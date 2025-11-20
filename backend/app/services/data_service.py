import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import aiohttp
import apscheduler.schedulers.asyncio
import baostock as bs
import tushare as ts
import pandas as pd
from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService
from apscheduler.triggers.cron import CronTrigger
from pandas import to_datetime
from pymongo import UpdateOne

logger = logging.getLogger(__name__)


class DataService:
    def __init__(self):
        self.mongo_service = MongoDBService()
        self.technical_service = TechnicalAnalysisService()
        self.scheduler = apscheduler.schedulers.asyncio.AsyncIOScheduler()
        self.startup_job_run = False
        self.is_fetching = False

    async def startup_job(self):
        """Run initial data fetch on startup"""
        if not self.startup_job_run:
            logger.info("Running startup data fetch job")
            self.startup_job_run = True

            # Login to BaoStock
            if await self._login_baostock():
                # Schedule regular data updates
                await self._setup_scheduler()
            else:
                logger.error("Failed to login to BaoStock, scheduler not started")

    async def _login_baostock(self) -> bool:
        """Login to BaoStock system"""
        try:
            lg = bs.login()
            if lg.error_code == "0":
                logger.info("BaoStock login successful")
                return True
            else:
                logger.error(f"BaoStock login failed: {lg.error_msg}")
                return False
        except Exception as e:
            logger.error(f"Error logging into BaoStock: {str(e)}")
            return False

    async def _setup_scheduler(self):
        """Setup scheduled jobs"""
        # Get scheduler times from configuration or use defaults
        stock_list_cron = await self.mongo_service.get_config_value(
            "scheduler", "timing", "stock_list_fetch_cron", "00 20 * * 1"
        )
        
        stock_history_cron = await self.mongo_service.get_config_value(
            "scheduler", "timing", "stock_history_fetch_cron", "04 20 * * *"
        )
        
        # Parse cron expressions
        try:
            stock_list_trigger = self._parse_cron_expression(stock_list_cron)
            stock_history_trigger = self._parse_cron_expression(stock_history_cron)
        except Exception as e:
            logger.error(f"Error parsing cron expressions: {str(e)}")
            # Use default triggers
            stock_list_trigger = CronTrigger(hour=20, minute=30)
            stock_history_trigger = CronTrigger(hour=20, minute=32)
        
        # Schedule stock list update
        self.scheduler.add_job(
            self.fetch_stock_list,
            trigger=stock_list_trigger,
            id="fetch_stock_list",
        )

        # Schedule daily data update
        self.scheduler.add_job(
            self.fetch_all_stock_daily_data,
            trigger=stock_history_trigger,
            id="fetch_daily_data",
        )

        self.scheduler.start()
        logger.info(f"Data scheduler started with stock list cron: {stock_list_cron}, history cron: {stock_history_cron}")

    def _parse_cron_expression(self, cron_expr: str) -> CronTrigger:
        """Parse cron expression string into CronTrigger"""
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")
        
        minute, hour, day, month, day_of_week = parts
        return CronTrigger(
            minute=minute if minute != '*' else None,
            hour=hour if hour != '*' else None,
            day=day if day != '*' else None,
            month=month if month != '*' else None,
            day_of_week=day_of_week if day_of_week != '*' else None
        )

    def _convert_ts_code(self, ts_code: str) -> str:
        """Convert TuShare ts_code format (123456.SH) to standard format (sh.123456)"""
        if "." in ts_code:
            parts = ts_code.split(".")
            code = parts[0]
            market = parts[1].lower()
            return f"{market}.{code}"
        return ts_code

    async def fetch_stock_list_from_tushare(self) -> Optional[tuple]:
        """Fetch stock list from TuShare"""
        try:
            # Get TuShare token from configuration
            token = await self.mongo_service.get_config_value(
                "system", "general", "tushare_token"
            )
            if not token:
                logger.warning("TuShare token not found in configuration")
                return None

            # Set TuShare token
            ts.set_token(token)
            pro = ts.pro_api()

            # Fetch stock basic info
            df = pro.stock_basic(
                exchange="",
                list_status="L"
            )
            
            # Also fetch company detailed info for ALL stocks at once
            try:
                company_df = pro.stock_company(**{
                    "ts_code": "",
                    "exchange": "",
                    "status": "",
                    "limit": "",
                    "offset": ""
                })
                logger.info(f"Successfully fetched company info for {len(company_df)} stocks from TuShare")
            except Exception as e:
                logger.warning(f"Error fetching company info from TuShare: {str(e)}")
                company_df = None
            
            logger.info(f"Successfully fetched {len(df)} stocks from TuShare")
            return df, company_df
        except Exception as e:
            logger.error(f"Error fetching stock list from TuShare: {str(e)}")
            return None

    def fetch_latest_stock_list(self, date: str = None) -> bool | tuple[list[Any], Any]:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        # Fetch stock data from BaoStock
        stock_list = []
        times = 0
        while not stock_list and times < 30:
            rs = bs.query_all_stock(date)
            if rs.error_code != "0":
                logger.error(f"Error fetching stock list: {rs.error_msg}")
                self._record_failed_request(
                    "query_all_stock", {"date": date}, rs.error_msg
                )
                return False

            while (rs.error_code == "0") & rs.next():
                stock_list.append(rs.get_row_data())

            if not stock_list:
                logger.warning(
                    "No stock data received, probably due to date is not trading date. Trying the previous one"
                )
                date = (to_datetime(date) - timedelta(days=1)).strftime("%Y-%m-%d")
                times += 1

        return stock_list, rs

    async def fetch_stock_list(self, date: str = None) -> bool:
        """Fetch all stock list and save to database"""
        if self.is_fetching:
            logger.info("Stock list fetch already in progress")
            return False

        self.is_fetching = True
        try:
            # First try to fetch from TuShare
            tushare_result = await self.fetch_stock_list_from_tushare()

            company_operations = []
            if tushare_result:
                # Process TuShare data
                df, company_df = tushare_result
                logger.info(f"Using TuShare data with {len(df)} stocks")

                # Transform data to match existing format
                operations = []
                for _, row in df.iterrows():
                    # Convert ts_code to standard format
                    code = self._convert_ts_code(row["ts_code"])
                    
                    # Filter out Beijing Stock Exchange (bj) stocks
                    # because BaoStock does not provide data for Beijing Stock Exchange
                    if code.startswith("bj."):
                        continue

                    stock_doc = {
                        "code": code,
                        "ts_code": row.get("ts_code", ""),
                        "symbol": row.get("symbol", ""),
                        "code_name": row["name"],
                        "name": row["name"],
                        "area": row.get("area", ""),
                        "industry": row.get("industry", ""),
                        "fullname": row.get("fullname", ""),
                        "enname": row.get("enname", ""),
                        "cnspell": row.get("cnspell", ""),
                        "market": row.get("market", ""),
                        "exchange": row.get("exchange", ""),
                        "curr_type": row.get("curr_type", ""),
                        "list_status": row.get("list_status", ""),
                        "list_date": row.get("list_date", ""),
                        "delist_date": row.get("delist_date", ""),
                        "is_hs": row.get("is_hs", ""),
                        "act_name": row.get("act_name", ""),
                        "act_ent_type": row.get("act_ent_type", ""),
                        "updateTime": datetime.utcnow(),
                    }

                    operations.append(
                        UpdateOne(
                            {"code": stock_doc["code"]},
                            {"$set": stock_doc},
                            upsert=True,
                        )
                    )
                    
                    # Prepare company info document if available
                    if company_df is not None:
                        # Find company info for this stock
                        company_rows = company_df[company_df['ts_code'] == row['ts_code']]
                        if not company_rows.empty:
                            company_row = company_rows.iloc[0]
                            company_doc = company_row.to_dict()
                            # Add converted code
                            company_doc['code'] = code
                            company_doc['updated_at'] = datetime.utcnow()
                            
                            company_operations.append(
                                UpdateOne(
                                    {"ts_code": company_doc["ts_code"]},
                                    {"$set": company_doc},
                                    upsert=True,
                                )
                            )

            else:
                # Fallback to BaoStock if TuShare fails
                logger.info("Falling back to BaoStock for stock list")
                stock_list, rs = self.fetch_latest_stock_list()
                # Convert to DataFrame for better handling
                df = pd.DataFrame(stock_list, columns=rs.fields)
                logger.info(
                    f"Received {len(df)} stocks from BaoStock, DataFrame structure: {df.shape}, columns: {df.columns.tolist()}"
                )

                # Transform data
                operations = []
                for _, row in df.iterrows():
                    stock_doc = {
                        "code": row["code"],
                        "code_name": row["code_name"],
                        "tradeStatus": row.get("tradeStatus", ""),
                        "updateTime": datetime.utcnow(),
                    }

                    operations.append(
                        UpdateOne(
                            {"code": stock_doc["code"]},
                            {"$set": stock_doc},
                            upsert=True,
                        )
                    )

            # Bulk write to database
            if operations:
                success = await self.mongo_service.bulk_write("stock_info", operations)
                if success:
                    logger.info(
                        f"Successfully updated {len(operations)} stocks in database"
                    )
                    # Remove any successful requests from failed_requests table
                    await self.mongo_service.delete_one(
                        "failed_requests",
                        {"api_name": "query_all_stock", "parameters.date": date},
                    )
                    
                    # Also save company info if available
                    if company_operations:
                        company_success = await self.mongo_service.bulk_write("stock_basic_info", company_operations)
                        if company_success:
                            logger.info(f"Successfully updated {len(company_operations)} company records in database")
                        else:
                            logger.error("Failed to update company info in database")
                    
                    return True
                else:
                    logger.error("Failed to update stocks in database")
                    return False
            else:
                logger.warning("No operations to perform")
                return False

        except Exception as e:
            logger.error(f"Error in fetch_stock_list: {str(e)}")
            await self._record_failed_request("query_all_stock", {"date": date}, str(e))
            return False
        finally:
            self.is_fetching = False

    async def fetch_all_stock_daily_data(self):
        """Fetch daily data for all stocks"""
        # Login to BaoStock
        login_success = await self._login_baostock()
        if not login_success:
            logger.error("Failed to login to BaoStock, cannot fetch stock data")
            return

        if self.is_fetching:
            logger.info("Daily data fetch already in progress")
            return

        self.is_fetching = True
        try:
            # Get all stock codes, excluding Beijing Stock Exchange (bj) stocks
            # because BaoStock does not provide data for Beijing Stock Exchange
            stocks = await self.mongo_service.find(
                "stock_info", 
                {"code": {"$not": {"$regex": "^bj\\."}}}, 
                {"code": 1}
            )
            if not stocks:
                logger.warning("No stocks found in database")
                return

            # Process stocks in batches for better performance
            # More concurrent requests for data fetching (30), fewer for processing (3)
            fetch_semaphore = asyncio.Semaphore(30)  # Increased threads for data fetching
            process_semaphore = asyncio.Semaphore(3)  # Reduced threads for processing
            
            async def fetch_with_semaphores(stock_code):
                # First semaphore for fetching data from BaoStock
                async with fetch_semaphore:
                    result = await self.fetch_stock_daily_data_without_processing(stock_code)
                    
                # Second semaphore for processing data (saving to DB and calculating indicators)
                if result and result[0]:  # if fetch was successful
                    async with process_semaphore:
                        stock_code, df = result[1]  # Fixed unpacking - result is (bool, (stock_code, df))
                        await self.process_stock_data(stock_code, df)
                
                return result[0] if result else False
            
            # Process stocks in larger batches
            batch_size = 100  # Increased batch size
            successful_fetches = 0
            total_stocks = len(stocks)
            
            for i in range(0, total_stocks, batch_size):
                batch = stocks[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(total_stocks-1)//batch_size + 1} with {len(batch)} stocks")
                
                tasks = [fetch_with_semaphores(stock["code"]) for stock in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                batch_successes = sum(1 for result in results if result is True and result is not Exception)
                successful_fetches += batch_successes
                
                logger.info(f"Completed batch {i//batch_size + 1}, successful: {batch_successes}/{len(batch)}")

            logger.info(
                f"Daily data fetch completed. Successful: {successful_fetches}/{total_stocks}"
            )

            if successful_fetches > 0:
                # Update start_date configuration to today
                today = datetime.now().strftime("%Y-%m-%d")
                await self.mongo_service.set_config_value(
                    "scheduler",
                    "data_fetch",
                    "start_date",
                    today,
                    "Last successful data fetch date",
                )

        except Exception as e:
            logger.error(f"Error in fetch_all_stock_daily_data: {str(e)}")
        finally:
            self.is_fetching = False

    async def fetch_stock_daily_data_without_processing(self, stock_code: str) -> tuple:
        """Fetch daily K-line data for a specific stock without processing"""
        try:
            # Get the last date from existing data
            last_date = await self._get_last_date_for_stock(stock_code)
            start_date = last_date or "1990-12-19"

            end_date = datetime.now().strftime("%Y-%m-%d")

            logger.info(
                f"Fetching daily data for {stock_code} from {start_date} to {end_date}"
            )

            # Fetch data from BaoStock
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2",  # Backward adjustment
            )

            if rs.error_code != "0":
                logger.error(f"Error fetching data for {stock_code}: {rs.error_msg}")
                await self._record_failed_request(
                    "query_history_k_data_plus",
                    {
                        "code": stock_code,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                    rs.error_msg,
                )
                return None

            data_list = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                logger.info(f"No new data for {stock_code}")
                return (False, None)

            # Convert to DataFrame
            df = pd.DataFrame(data_list, columns=rs.fields)
            logger.debug(
                f"DataFrame structure for {stock_code}: {df.shape}, columns: {df.columns.tolist()}"
            )
            
            return (True, (stock_code, df))

        except Exception as e:
            logger.error(f"Error fetching daily data for {stock_code}: {str(e)}")
            await self._record_failed_request(
                "query_history_k_data_plus",
                {"code": stock_code, "start_date": start_date, "end_date": end_date},
                str(e),
            )
            return None

    async def process_stock_data(self, stock_code: str, df: pd.DataFrame) -> bool:
        """Process stock data: save to database and calculate technical indicators"""
        try:
            # Process and save data
            collection_name = self.mongo_service.get_collection_name(stock_code)
            operations = []

            for _, row in df.iterrows():
                # Convert date string to datetime
                try:
                    if "date" in df.columns:
                        trade_date = datetime.strptime(row["date"], "%Y-%m-%d")
                    else:
                        # Try to find date column automatically
                        date_col = None
                        for col in df.columns:
                            if "date" in col.lower():
                                date_col = col
                                break
                        if date_col:
                            trade_date = datetime.strptime(row[date_col], "%Y-%m-%d")
                        else:
                            logger.warning(
                                f"No date column found for {stock_code}, using current date"
                            )
                            trade_date = datetime.utcnow()
                except Exception as e:
                    logger.warning(
                        f"Error parsing date for {stock_code}: {str(e)}, using current date"
                    )
                    trade_date = datetime.utcnow()

                doc = {
                    "code": stock_code,
                    "date": trade_date,
                    "open": float(row["open"]) if row["open"] else 0,
                    "high": float(row["high"]) if row["high"] else 0,
                    "low": float(row["low"]) if row["low"] else 0,
                    "close": float(row["close"]) if row["close"] else 0,
                    "preclose": float(row["preclose"]) if row["preclose"] else 0,
                    "volume": float(row["volume"]) if row["volume"] else 0,
                    "amount": float(row["amount"]) if row["amount"] else 0,
                    "adjustflag": row.get("adjustflag", ""),
                    "turn": float(row["turn"]) if row["turn"] else 0,
                    "tradestatus": int(row["tradestatus"]) if row["tradestatus"] else 0,
                    "pctChg": float(row["pctChg"]) if row["pctChg"] else 0,
                    "peTTM": float(row["peTTM"]) if row["peTTM"] else 0,
                    "pbMRQ": float(row["pbMRQ"]) if row["pbMRQ"] else 0,
                    "psTTM": float(row["psTTM"]) if row["psTTM"] else 0,
                    "pcfNcfTTM": float(row["pcfNcfTTM"]) if row["pcfNcfTTM"] else 0,
                    "isST": int(row["isST"]) if row["isST"] else 0,
                    "updated_at": datetime.utcnow(),
                }

                operations.append(
                    UpdateOne(
                        {"code": stock_code, "date": trade_date},
                        {"$set": doc},
                        upsert=True,
                    )
                )

            if operations:
                success = await self.mongo_service.bulk_write(
                    collection_name, operations
                )
                if success:
                    logger.info(
                        f"Successfully updated {len(operations)} daily records for {stock_code}"
                    )
                    # Remove from failed requests if successful
                    await self.mongo_service.delete_one(
                        "failed_requests",
                        {
                            "api_name": "query_history_k_data_plus",
                            "parameters.code": stock_code,
                        },
                    )

                    # Calculate technical indicators
                    await self.technical_service.calculate_technical_indicators(
                        stock_code, df
                    )

                    return True
                else:
                    logger.error(f"Failed to update daily records for {stock_code}")
                    return False
            else:
                return True

        except Exception as e:
            logger.error(f"Error processing data for {stock_code}: {str(e)}")
            return False

    async def fetch_stock_daily_data(self, stock_code: str) -> bool:
        """Fetch daily K-line data for a specific stock"""
        # First fetch the data
        result = await self.fetch_stock_daily_data_without_processing(stock_code)
        if not result:
            return False
            
        success, data = result
        if not success:
            return False
            
        # Then process it
        stock_code, df = data
        return await self.process_stock_data(stock_code, df)

    async def _get_last_date_for_stock(self, stock_code: str) -> Optional[str]:
        """Get the last date for a stock from its daily data collection"""
        try:
            collection_name = f"stock_daily_{stock_code}"
            last_record = await self.mongo_service.find_one(
                collection_name, {}, sort=[("date", -1)]
            )

            if last_record and "date" in last_record:
                if isinstance(last_record["date"], datetime):
                    return last_record["date"].strftime("%Y-%m-%d")
                else:
                    return last_record["date"]
            return None
        except Exception as e:
            logger.error(f"Error getting last date for {stock_code}: {str(e)}")
            return None

    async def _record_failed_request(
        self, api_name: str, parameters: Dict[str, Any], error_msg: str
    ):
        """Record failed API requests for manual retry"""
        try:
            failed_request = {
                "api_name": api_name,
                "parameters": parameters,
                "error_message": error_msg,
                "retry_count": 0,
                "last_attempt": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }

            await self.mongo_service.insert_one("failed_requests", failed_request)
            logger.info(f"Recorded failed request for {api_name}")
        except Exception as e:
            logger.error(f"Error recording failed request: {str(e)}")

    async def trigger_immediate_fetch(self):
        """Manually trigger immediate data fetch"""
        if self.is_fetching:
            return {"status": "error", "message": "Data fetch already in progress"}

        # Run in background to avoid blocking
        task = asyncio.create_task(self.fetch_all_stock_daily_data())
        
        # Add a callback to handle task exceptions
        def handle_task_result(task):
            try:
                exception = task.exception()
                if exception:
                    logger.error(f"Error in data fetch task: {str(exception)}")
            except asyncio.CancelledError:
                logger.info("Data fetch task was cancelled")
        
        task.add_done_callback(handle_task_result)
        return {"status": "success", "message": "Data fetch started"}
