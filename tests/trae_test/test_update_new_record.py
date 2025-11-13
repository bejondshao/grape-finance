import asyncio
import datetime
import argparse
from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService

async def test_update_new_record(stock_code="sh.000001"):
    mongo_service = MongoDBService()
    technical_service = TechnicalAnalysisService()
    
    print("=== Testing Update with New Daily Record ===")
    
    # Step 1: Get latest daily record
    collection_name = f"stock_daily_{stock_code}"
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
    
    print(f"Created new daily record for: {new_date}")
    
    # Step 3: Insert new record - remove _id
    if '_id' in new_record:
        del new_record['_id']
    await mongo_service.insert_one(collection_name, new_record)
    
    # Step 4: Get total technical records before update
    total_before = await mongo_service.count_documents(f"technical_{stock_code}", {})
    print(f"Total technical records before update: {total_before}")
    
    # Step 5: Update CCI (should process new records)
    result = await technical_service.update_stock_cci(stock_code)
    print(f"Update result: {result}")
    
    # Step 6: Get total technical records after update
    total_after = await mongo_service.count_documents(f"technical_{stock_code}", {})
    print(f"Total technical records after update: {total_after}")
    
    # Step 7: Clean up (remove test record)
    await mongo_service.delete_one(collection_name, {"date": new_date})
    await mongo_service.delete_one(f"technical_{stock_code}", {"date": new_date})
    
    # Step 8: Verify results
    if total_after == total_before + 1:
        print("✓ New record correctly updated!")
    elif total_after > total_before:
        print(f"✓ {total_after - total_before} new records updated (may include recalculated values)")
    else:
        print(f"✗ No new records updated. Something went wrong!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test CCI update for a specific stock")
    parser.add_argument("--stock_code", type=str, default="sh.000001", help="Stock code to test (default: sh.000001)")
    args = parser.parse_args()
    asyncio.run(test_update_new_record(args.stock_code))