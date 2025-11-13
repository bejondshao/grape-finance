import asyncio
import datetime
import logging
logging.basicConfig(level=logging.INFO)

from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService

async def test_new_record():
    mongo_service = MongoDBService()
    ta_service = TechnicalAnalysisService()
    
    # Get current date in ISO format
    today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    today_iso = datetime.datetime.now(datetime.UTC)
    
    # Create a new test record for sh.600066
    new_record = {
        "code": "sh.600066",
        "date": today,
        "open": 10.50,
        "close": 10.80,
        "high": 10.90,
        "low": 10.40,
        "volume": 12345678,
        "amount": 133333333.00,
        "pctChg": 2.86,
        "preclose": 10.50,
        "turn": 0.32,
        "pbMRQ": 1.80,
        "peTTM": 15.50,
        "psTTM": 1.20,
        "pcfNcfTTM": 8.90,
        "adjustflag": 2,
        "tradestatus": 1,
        "isST": 0,
        "updated_at": datetime.datetime.now(datetime.UTC)
    }
    
    # Insert the new record
    collection_name = mongo_service.get_collection_name("sh.600066")
    await mongo_service.insert_one(collection_name, new_record)
    
    print(f"Inserted new record for sh.600066 on date: {new_record['date']}")
    
    # Check latest technical date
    latest_tech_date = await mongo_service.get_latest_technical_date("sh.600066")
    print(f"Latest technical date: {latest_tech_date}")
    
    # Get historical data to verify new record is present
    historical_data = await mongo_service.get_stock_history(
        stock_code="sh.600066", 
        limit=10, 
        sort="desc"
    )
    print(f"Latest 10 historical records dates: {[record['date'] for record in historical_data]}")
    
    # Update CCI with debug logs
    print("\n=== Updating CCI ===")
    result = await ta_service.update_stock_cci("sh.600066")
    print(f"CCI update result: {result}")
    print(f"Updated count: {result.get('updated_count', 'N/A')}")
    
    # Check the new record in technical collection
    tech_collection_name = mongo_service.get_technical_collection_name("sh.600066")
    print(f"Technical collection name: {tech_collection_name}")
    
    # Try different date formats to find the record
    tech_record = await mongo_service.find_one(tech_collection_name, {
        "code": "sh.600066"
    }, sort=[("date", -1)])
    if tech_record:
        print(f"Latest technical record: {tech_record}")
    
    # Check all CCI records count
    cci_count = await mongo_service.count_documents(tech_collection_name, {
        "code": "sh.600066"
    })
    print(f"Total CCI records for sh.600066: {cci_count}")
    
    # Clean up - delete the new record
    await mongo_service.delete_one(collection_name, {
        "code": "sh.600066",
        "date": new_record['date']
    })
    
    print("Cleanup complete")

if __name__ == "__main__":
    asyncio.run(test_new_record())