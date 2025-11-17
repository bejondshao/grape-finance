import asyncio
from app.services.mongodb_service import MongoDBService

async def test():
    mongo = MongoDBService()
    data = await mongo.find('stock_daily_sh.600000', {}, limit=5)
    if data:
        print("Sample data:")
        print(data[0])
        print("\nKeys:")
        print(list(data[0].keys()))
    else:
        print("No data found")

asyncio.run(test())