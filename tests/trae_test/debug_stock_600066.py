import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.mongodb_service import MongoDBService

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_stock_600066():
    try:
        # Initialize services
        mongo_service = MongoDBService()
        tech_service = TechnicalAnalysisService()

        stock_code = "sh.600066"
        logger.info(f"=== Debugging {stock_code} ===")

        # Step 1: Check the latest technical date
        latest_tech_date = await mongo_service.get_latest_technical_date(stock_code)
        logger.debug(f"Latest technical date: {latest_tech_date}")
        latest_tech_datetime = datetime.strptime(latest_tech_date, "%Y-%m-%d %H:%M:%S") if latest_tech_date else datetime.min

        # Step 2: Get all technical records count
        tech_collection = f"technical_{stock_code}"
        total_tech_records = await mongo_service.count_documents(tech_collection, {})
        logger.debug(f"Total technical records: {total_tech_records}")

        # Step 3: Get the full date range for the stock's history
        daily_collection = f"stock_daily_{stock_code}"
        all_daily_records = await mongo_service.get_stock_history(stock_code=stock_code, limit=0, sort="asc")
        logger.debug(f"Total daily records: {len(all_daily_records)}")

        if all_daily_records:
            df = pd.DataFrame(all_daily_records)
            df['date'] = pd.to_datetime(df['date'])
            earliest_date = df['date'].min()
            latest_date = df['date'].max()
            logger.debug(f"Daily records date range: {earliest_date} to {latest_date}")

            # Step 4: Check what would be processed in an update
            # Get historical data from the latest technical date to the latest available date
            historical_data = await mongo_service.get_stock_history(
                stock_code=stock_code,
                start_date=latest_tech_date,
                end_date=latest_date.strftime("%Y-%m-%d"),
                limit=0,
                sort="asc"
            )
            logger.debug(f"Historical data for update: {len(historical_data)} records")

            # Step 5: If there's data, check how many are new
            if historical_data:
                df_new = pd.DataFrame(historical_data)
                df_new['date'] = pd.to_datetime(df_new['date'])
                new_records = df_new[df_new['date'] > latest_tech_datetime]
                logger.debug(f"New records to process: {len(new_records)}")

        logger.info(f"=== Debugging {stock_code} completed ===")
        return True

    except Exception as e:
        logger.error(f"Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(debug_stock_600066())