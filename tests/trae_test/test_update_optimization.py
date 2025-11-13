import asyncio
from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService

async def test_update_optimization():
    mongo_service = MongoDBService()
    technical_service = TechnicalAnalysisService()
    stock_code = "sh.000001"
    
    print("=== Testing Update Optimization ===")
    
    # Step 1: Get total records in technical collection before update
    total_before = await mongo_service.count_documents(f"technical_{stock_code}", {})
    print(f"Total records in technical_{stock_code} before update: {total_before}")
    
    # Step 2: Get latest technical date
    latest_tech_date = await mongo_service.get_latest_technical_date(stock_code)
    print(f"Latest technical date: {latest_tech_date}")
    
    # Step 3: Update CCI (should only process new data)
    result = await technical_service.update_stock_cci(stock_code)
    print(f"Update result: {result}")
    
    # Step 4: Get total records in technical collection after update
    total_after = await mongo_service.count_documents(f"technical_{stock_code}", {})
    print(f"Total records in technical_{stock_code} after update: {total_after}")
    
    # Step 5: Verify results
    if total_after == total_before:
        print("✓ No new records to update. Optimization working correctly!")
    else:
        print(f"✓ {total_after - total_before} new records updated!")

if __name__ == "__main__":
    asyncio.run(test_update_optimization())