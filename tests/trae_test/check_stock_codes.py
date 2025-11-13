import asyncio
from app.services.mongodb_service import MongoDBService

async def check_stock_codes():
    service = MongoDBService()
    codes = await service.db.stock_info.distinct('code')
    print('Sample stock codes:', codes[:10] if codes else 'No codes found')
    print('Are all codes lowercase?', all(code.lower() == code for code in codes))
    print('Are all codes uppercase?', all(code.upper() == code for code in codes))
    print('Stock code format example:', codes[0] if codes else 'No example available')

if __name__ == "__main__":
    asyncio.run(check_stock_codes())