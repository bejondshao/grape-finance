import asyncio
from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService

async def test_update_all_cci():
    mongo_service = MongoDBService()
    technical_service = TechnicalAnalysisService()
    stock_code = "sh.000001"
    
    # Get total records in stock_daily collection
    total_daily_records = await mongo_service.count_documents(f"stock_daily_{stock_code}", {})
    print(f"Total records in stock_daily_{stock_code}: {total_daily_records}")
    
    # Update all CCI indicators
    result = await technical_service.update_stock_cci(stock_code)
    print(f"Update result: {result}")
    
    # Get total records in technical collection after update
    total_technical_records = await mongo_service.count_documents(f"technical_{stock_code}", {})
    print(f"Total records in technical_{stock_code} after update: {total_technical_records}")
    
    # Check if the number of technical records matches expected (should be total_daily_records - 13)
    expected_technical_records = total_daily_records - 13  # CCI needs 14 days of data to calculate
    if total_technical_records >= expected_technical_records:
        print(f"✓ Update successful! Technical records ({total_technical_records}) match expected ({expected_technical_records} +)")
    else:
        print(f"✗ Update failed! Technical records ({total_technical_records}) are less than expected ({expected_technical_records})")

if __name__ == "__main__":
    asyncio.run(test_update_all_cci())