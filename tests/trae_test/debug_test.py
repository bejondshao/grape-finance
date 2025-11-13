import asyncio
import logging
from datetime import datetime, timedelta
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.mongodb_service import MongoDBService

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_test():
    try:
        # Initialize services
        mongo_service = MongoDBService()
        tech_service = TechnicalAnalysisService()
        tech_service.mongo_service = mongo_service
        await mongo_service.initialize_indexes()  # Ensure indexes are created

        stock_code = "sh.000001"
        logger.info("=== Debug Test Started ===")

        # Step 1: Check latest technical date
        latest_tech_date_str = await mongo_service.get_latest_technical_date(stock_code)
        logger.debug(f"Latest technical date for {stock_code}: {latest_tech_date_str}")

        # Step 2: Check what data is being retrieved for the update
        # Let's get today's date minus 1 day
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        logger.debug(f"Yesterday: {yesterday_str}")

        # Get stock history from the latest technical date to today
        historical_data = await mongo_service.get_stock_history(
            stock_code=stock_code,
            start_date=latest_tech_date_str,
            end_date=yesterday_str,
            limit=0,
            sort="asc"
        )
        logger.debug(f"Retrieved {len(historical_data)} historical records")

        # If there's data, check what the latest date is
        if historical_data:
            df = technical_service.pandas.DataFrame(historical_data)
            latest_date_in_data = df['date'].max()
            logger.debug(f"Latest date in historical data: {latest_date_in_data}")

            # Compare with latest technical date
            if latest_tech_date_str:
                latest_tech_date = datetime.strptime(latest_tech_date_str, "%Y-%m-%d %H:%M:%S")
                logger.debug(f"Latest tech date (datetime): {latest_tech_date}")
                logger.debug(f"Latest date in data > latest tech date: {latest_date_in_data > latest_tech_date}")

        logger.info("=== Debug Test Completed ===")
        return True

    except Exception as e:
        logger.error(f"Debug test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(debug_test())