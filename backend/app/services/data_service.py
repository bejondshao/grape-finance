import asyncio
import logging
import pandas as pd
import baostock as bs
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import apscheduler.schedulers.asyncio
from apscheduler.triggers.cron import CronTrigger
import time
from pymongo import UpdateOne

from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis import TechnicalAnalysisService

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
                # Fetch stock list
                await self.fetch_stock_list()
                
                # Schedule regular data updates
                await self._setup_scheduler()
            else:
                logger.error("Failed to login to BaoStock, scheduler not started")
    
    async def _login_baostock(self) -> bool:
        """Login to BaoStock system"""
        try:
            lg = bs.login()
            if lg.error_code == '0':
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
        # Schedule stock list update every day at 18:00
        self.scheduler.add_job(
            self.fetch_stock_list,
            trigger=CronTrigger(hour=18, minute=0),
            id='fetch_stock_list'
        )
        
        # Schedule daily data update every day at 19:00  
        self.scheduler.add_job(
            self.fetch_all_stock_daily_data,
            trigger=CronTrigger(hour=19, minute=0),
            id='fetch_daily_data'
        )
        
        self.scheduler.start()
        logger.info("Data scheduler started")
    
    async def fetch_stock_list(self, date: str = None) -> bool:
        """Fetch all stock list and save to database"""
        if self.is_fetching:
            logger.info("Stock list fetch already in progress")
            return False
            
        self.is_fetching = True
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
                
            logger.info(f"Fetching stock list for date: {date}")
            
            # Fetch stock data from BaoStock
            rs = bs.query_all_stock(date)
            if rs.error_code != '0':
                logger.error(f"Error fetching stock list: {rs.error_msg}")
                await self._record_failed_request("query_all_stock", {"date": date}, rs.error_msg)
                return False
            
            stock_list = []
            while (rs.error_code == '0') & rs.next():
                stock_list.append(rs.get_row_data())
            
            if not stock_list:
                logger.warning("No stock data received")
                return False
            
            # Convert to DataFrame for better handling
            df = pd.DataFrame(stock_list, columns=rs.fields)
            logger.info(f"Received {len(df)} stocks, DataFrame structure: {df.shape}, columns: {df.columns.tolist()}")
            
            # Transform data
            operations = []
            for _, row in df.iterrows():
                stock_doc = {
                    'code': row['code'],
                    'code_name': row['code_name'],
                    'tradeStatus': row.get('tradeStatus', ''),
                    'ipoDate': row.get('ipoDate', ''),
                    'outDate': row.get('outDate', ''),
                    'type': row.get('type', ''),
                    'updateTime': datetime.utcnow()
                }
                
                operations.append(
                    UpdateOne(
                        {'code': stock_doc['code']},
                        {'$set': stock_doc},
                        upsert=True
                    )
                )
            
            # Bulk write to database
            if operations:
                success = await self.mongo_service.bulk_write('stock_info', operations)
                if success:
                    logger.info(f"Successfully updated {len(operations)} stocks in database")
                    # Remove any successful requests from failed_requests table
                    await self.mongo_service.delete_one('failed_requests', {
                        'api_name': 'query_all_stock',
                        'parameters.date': date
                    })
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
        if self.is_fetching:
            logger.info("Daily data fetch already in progress")
            return
            
        self.is_fetching = True
        try:
            # Get all stock codes
            stocks = await self.mongo_service.find('stock_info', {}, {'code': 1})
            if not stocks:
                logger.warning("No stocks found in database")
                return
            
            sleep_timer = float(await self.mongo_service.get_config_value(
                'scheduler', 'data_fetch', 'sleep_timer', 1
            ))
            
            successful_fetches = 0
            total_stocks = len(stocks)
            
            for i, stock in enumerate(stocks):
                stock_code = stock['code']
                logger.info(f"Processing stock {i+1}/{total_stocks}: {stock_code}")
                
                success = await self.fetch_stock_daily_data(stock_code)
                if success:
                    successful_fetches += 1
                
                # Sleep to avoid overwhelming the API
                if sleep_timer > 0 and i < total_stocks - 1:
                    await asyncio.sleep(sleep_timer)
            
            logger.info(f"Daily data fetch completed. Successful: {successful_fetches}/{total_stocks}")
            
            if successful_fetches > 0:
                # Update start_date configuration to today
                today = datetime.now().strftime("%Y-%m-%d")
                await self.mongo_service.set_config_value(
                    'scheduler', 'data_fetch', 'start_date', today,
                    'Last successful data fetch date'
                )
                
        except Exception as e:
            logger.error(f"Error in fetch_all_stock_daily_data: {str(e)}")
        finally:
            self.is_fetching = False
    
    async def fetch_stock_daily_data(self, stock_code: str) -> bool:
        """Fetch daily K-line data for a specific stock"""
        try:
            # Get the last date from existing data
            last_date = await self._get_last_date_for_stock(stock_code)
            start_date = last_date or "1990-12-19"
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Fetching daily data for {stock_code} from {start_date} to {end_date}")
            
            # Fetch data from BaoStock
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2"  # Backward adjustment
            )
            
            if rs.error_code != '0':
                logger.error(f"Error fetching data for {stock_code}: {rs.error_msg}")
                await self._record_failed_request(
                    "query_history_k_data_plus", 
                    {"code": stock_code, "start_date": start_date, "end_date": end_date},
                    rs.error_msg
                )
                return False
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                logger.info(f"No new data for {stock_code}")
                return True
            
            # Convert to DataFrame
            df = pd.DataFrame(data_list, columns=rs.fields)
            logger.debug(f"DataFrame structure for {stock_code}: {df.shape}, columns: {df.columns.tolist()}")
            
            # Process and save data
            collection_name = f"stock_daily_{stock_code.replace('.', '_')}"
            operations = []
            
            for _, row in df.iterrows():
                # Convert date string to datetime
                try:
                    if 'date' in df.columns:
                        trade_date = datetime.strptime(row['date'], '%Y-%m-%d')
                    else:
                        # Try to find date column automatically
                        date_col = None
                        for col in df.columns:
                            if 'date' in col.lower():
                                date_col = col
                                break
                        if date_col:
                            trade_date = datetime.strptime(row[date_col], '%Y-%m-%d')
                        else:
                            logger.warning(f"No date column found for {stock_code}, using current date")
                            trade_date = datetime.utcnow()
                except Exception as e:
                    logger.warning(f"Error parsing date for {stock_code}: {str(e)}, using current date")
                    trade_date = datetime.utcnow()
                
                doc = {
                    'code': stock_code,
                    'date': trade_date,
                    'open': float(row['open']) if row['open'] else 0,
                    'high': float(row['high']) if row['high'] else 0,
                    'low': float(row['low']) if row['low'] else 0,
                    'close': float(row['close']) if row['close'] else 0,
                    'preclose': float(row['preclose']) if row['preclose'] else 0,
                    'volume': float(row['volume']) if row['volume'] else 0,
                    'amount': float(row['amount']) if row['amount'] else 0,
                    'adjustflag': row.get('adjustflag', ''),
                    'turn': float(row['turn']) if row['turn'] else 0,
                    'tradestatus': int(row['tradestatus']) if row['tradestatus'] else 0,
                    'pctChg': float(row['pctChg']) if row['pctChg'] else 0,
                    'peTTM': float(row['peTTM']) if row['peTTM'] else 0,
                    'pbMRQ': float(row['pbMRQ']) if row['pbMRQ'] else 0,
                    'psTTM': float(row['psTTM']) if row['psTTM'] else 0,
                    'pcfNcfTTM': float(row['pcfNcfTTM']) if row['pcfNcfTTM'] else 0,
                    'isST': int(row['isST']) if row['isST'] else 0,
                    'updated_at': datetime.utcnow()
                }
                
                operations.append(
                    UpdateOne(
                        {'code': stock_code, 'date': trade_date},
                        {'$set': doc},
                        upsert=True
                    )
                )
            
            if operations:
                success = await self.mongo_service.bulk_write(collection_name, operations)
                if success:
                    logger.info(f"Successfully updated {len(operations)} daily records for {stock_code}")
                    # Remove from failed requests if successful
                    await self.mongo_service.delete_one('failed_requests', {
                        'api_name': 'query_history_k_data_plus',
                        'parameters.code': stock_code
                    })
                    
                    # Calculate technical indicators
                    await self.technical_service.calculate_technical_indicators(stock_code, df)
                    
                    return True
                else:
                    logger.error(f"Failed to update daily records for {stock_code}")
                    return False
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error fetching daily data for {stock_code}: {str(e)}")
            await self._record_failed_request(
                "query_history_k_data_plus",
                {"code": stock_code, "start_date": start_date, "end_date": end_date},
                str(e)
            )
            return False
    
    async def _get_last_date_for_stock(self, stock_code: str) -> Optional[str]:
        """Get the last date for a stock from its daily data collection"""
        try:
            collection_name = f"stock_daily_{stock_code.replace('.', '_')}"
            last_record = await self.mongo_service.find_one(
                collection_name,
                {},
                sort=[('date', -1)]
            )
            
            if last_record and 'date' in last_record:
                if isinstance(last_record['date'], datetime):
                    return last_record['date'].strftime('%Y-%m-%d')
                else:
                    return last_record['date']
            return None
        except Exception as e:
            logger.error(f"Error getting last date for {stock_code}: {str(e)}")
            return None
    
    async def _record_failed_request(self, api_name: str, parameters: Dict[str, Any], error_msg: str):
        """Record failed API requests for manual retry"""
        try:
            failed_request = {
                'api_name': api_name,
                'parameters': parameters,
                'error_message': error_msg,
                'retry_count': 0,
                'last_attempt': datetime.utcnow(),
                'created_at': datetime.utcnow()
            }
            
            await self.mongo_service.insert_one('failed_requests', failed_request)
            logger.info(f"Recorded failed request for {api_name}")
        except Exception as e:
            logger.error(f"Error recording failed request: {str(e)}")
    
    async def trigger_immediate_fetch(self):
        """Manually trigger immediate data fetch"""
        if self.is_fetching:
            return {"status": "error", "message": "Data fetch already in progress"}
        
        # Run in background to avoid blocking
        asyncio.create_task(self.fetch_all_stock_daily_data())
        return {"status": "success", "message": "Data fetch started"}
