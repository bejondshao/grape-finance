import asyncio
from app.services.mongodb_service import MongoDBService

async def check_date_field_type():
    mongo_service = MongoDBService()
    
    # 选择一个股票代码进行测试
    stock_code = "sh.600543"
    collection_name = f"stock_daily_{stock_code}"
    
    try:
        # 获取第一条记录
        first_doc = await mongo_service.find_one(collection_name, {})
        if first_doc:
            print(f"第一条记录: {first_doc}")
            print(f"日期字段类型: {type(first_doc.get('date'))}")
            print(f"日期值: {first_doc.get('date')}")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        # 关闭MongoDB连接
        await mongo_service.client.close()

if __name__ == "__main__":
    asyncio.run(check_date_field_type())