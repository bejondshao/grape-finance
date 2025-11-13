import asyncio
import datetime
from app.services.mongodb_service import MongoDBService

async def test_check_new_record():
    mongo_service = MongoDBService()
    stock_code = "sh.000001"
    collection_name = f"stock_daily_{stock_code}"
    
    # Step 1: Get latest daily record
    latest_daily = await mongo_service.find_one(collection_name, {}, sort=[("date", -1)])
    print(f"Latest daily record date: {latest_daily['date']}")
    
    # Step 2: Create new daily record (next day)
    new_date = latest_daily['date'] + datetime.timedelta(days=1)
    new_record = latest_daily.copy()
    new_record['date'] = new_date
    new_record['open'] = latest_daily['close']  # Set open to previous close
    new_record['high'] = latest_daily['close'] * 1.02  # 2% up
    new_record['low'] = latest_daily['close'] * 0.98  # 2% down
    new_record['close'] = (new_record['high'] + new_record['low']) / 2  # Average
    new_record['volume'] = latest_daily['volume'] * 1.1  # 10% more volume
    
    # Step 3: Insert new record - remove _id
    if '_id' in new_record:
        del new_record['_id']
    await mongo_service.insert_one(collection_name, new_record)
    
    # Step 4: Check if new record exists
    new_records = await mongo_service.find(collection_name, {"date": new_date})
    print(f"Found {len(new_records)} records for date {new_date}")
    for rec in new_records:
        print(f"  Record found: {rec['date']}")
    
    # Step 5: Test get_stock_history with start_date
    start_date = latest_daily['date'].strftime("%Y-%m-%d")
    print(f"\nTesting get_stock_history with start_date={start_date}")
    historical_data = await mongo_service.get_stock_history(
        stock_code=stock_code,
        start_date=start_date,
        end_date=None,
        limit=0,
        sort="asc"
    )
    print(f"Retrieved {len(historical_data)} records")
    latest_retrieved = historical_data[-1]
    print(f"Latest record from get_stock_history: {latest_retrieved['date']}")
    
    # Step 6: Test with converted date
    converted_date = start_date
    print(f"\nTesting with converted date: {converted_date}")
    historical_data2 = await mongo_service.get_stock_history(
        stock_code=stock_code,
        start_date=converted_date,
        end_date=None,
        limit=0,
        sort="asc"
    )
    print(f"Retrieved {len(historical_data2)} records")
    
    # Step 7: Clean up
    await mongo_service.delete_one(collection_name, {"date": new_date})
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_check_new_record())