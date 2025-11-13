import asyncio
import logging
logging.basicConfig(level=logging.INFO)

from app.services.technical_analysis_service import TechnicalAnalysisService

async def test_cci_update():
    service = TechnicalAnalysisService()
    result = await service.update_stock_cci('sh.600066')
    print(f"Update result: {result}")
    print(f"Updated count: {result.get('updated_count', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_cci_update())