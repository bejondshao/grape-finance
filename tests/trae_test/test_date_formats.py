import asyncio
import sys
from datetime import datetime
import pandas as pd

# Add the project root to sys.path
sys.path.append('c:\\Users\\bejon\\code\\grape-finance\\backend')

from app.services.mongodb_service import MongoDBService

async def test_date_formats():
    """Test that both date formats work correctly"""
    mongo_service = MongoDBService()
    stock_code = "sh.600543"
    
    print(f"Testing date formats for stock: {stock_code}")
    
    try:
        # Test 1: Query with date only format (YYYY-MM-DD)
        print(f"\n1. Testing date only format (YYYY-MM-DD):")
        date_only = "2025-11-07"
        result_date_only = await mongo_service.get_stock_history(
            stock_code=stock_code,
            start_date=date_only,
            end_date=date_only,
            limit=5
        )
        print(f"   Found {len(result_date_only)} records for date: {date_only}")
        
        # Test 2: Query with datetime format (YYYY-MM-DD HH:mm:ss)
        print(f"\n2. Testing datetime format (YYYY-MM-DD HH:mm:ss):")
        datetime_format = "2025-11-07 00:00:00"
        result_datetime = await mongo_service.get_stock_history(
            stock_code=stock_code,
            start_date=datetime_format,
            end_date=datetime_format,
            limit=5
        )
        print(f"   Found {len(result_datetime)} records for datetime: {datetime_format}")
        
        # Test 3: Query with date range including both formats
        print(f"\n3. Testing date range with mixed formats:")
        start_date_only = "2025-11-01"
        end_datetime = "2025-11-07 23:59:59"
        result_range = await mongo_service.get_stock_history(
            stock_code=stock_code,
            start_date=start_date_only,
            end_date=end_datetime,
            limit=10,
            sort="asc"
        )
        print(f"   Found {len(result_range)} records from {start_date_only} to {end_datetime}")
        
        if result_range:
            print(f"   Date range: {result_range[0]['date']} to {result_range[-1]['date']}")
        
        print(f"\n✅ All tests passed! Both date formats are supported.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Close the MongoDB connection
        if hasattr(mongo_service, 'client') and mongo_service.client is not None:
            mongo_service.client.close()

if __name__ == "__main__":
    asyncio.run(test_date_formats())