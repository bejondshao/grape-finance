import asyncio
from app.services.mongodb_service import MongoDBService

async def test():
    service = MongoDBService()
    
    # 检查股票数据
    count = await service.count_documents('stock_daily_sh.600000')
    print(f'Stock data count: {count}')
    
    # 检查股票信息
    info = await service.find_one('stock_info', {'code': 'sh.600000'})
    print(f'Stock info: {info}')
    
    # 检查技术指标数据
    tech_count = await service.count_documents('technical_sh.600000')
    print(f'Technical data count: {tech_count}')

asyncio.run(test())