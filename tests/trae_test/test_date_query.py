import asyncio
from app.services.mongodb_service import MongoDBService

async def test_date_query():
    mongo_service = MongoDBService()
    
    # 测试股票代码和日期范围
    stock_code = "sh.600543"
    
    try:
        # 测试1：获取所有历史数据（默认返回前100条）
        print("测试1：获取所有历史数据")
        all_data = await mongo_service.get_stock_history(stock_code)
        print(f"共获取到 {len(all_data)} 条数据")
        if all_data:
            print(f"最新数据日期: {all_data[0]['date']}")
            print(f"最早数据日期: {all_data[-1]['date']}")
        
        # 测试2：获取指定日期范围的数据
        print("\n测试2：获取指定日期范围的数据")
        start_date = "2025-11-01 00:00:00"
        end_date = "2025-11-15 23:59:59"
        range_data = await mongo_service.get_stock_history(stock_code, start_date=start_date, end_date=end_date)
        print(f"{start_date} 到 {end_date} 共获取到 {len(range_data)} 条数据")
        for item in range_data:
            print(f"日期: {item['date']}, 收盘价: {item['close']}")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    
    # 注意：motor库的AsyncIOMotorClient.close()不是协程方法，无需await
    mongo_service.client.close()

if __name__ == "__main__":
    asyncio.run(test_date_query())