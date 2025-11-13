import asyncio
import sys
import pandas as pd
from datetime import datetime

# 将项目根目录添加到sys.path中
sys.path.append('c:\\Users\\bejon\\code\\grape-finance\\backend')

from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService

async def test_date_functions():
    """测试与日期相关的功能"""
    mongo_service = MongoDBService()
    ta_service = TechnicalAnalysisService()
    
    stock_code = "sh.600543"
    
    print(f"测试股票代码: {stock_code}")
    
    try:
        # 测试1: 检查get_latest_technical_date是否返回字符串
        latest_date = await mongo_service.get_latest_technical_date(stock_code)
        print(f"\n1. get_latest_technical_date返回值: {latest_date}")
        print(f"   类型: {type(latest_date)}")
        
        if latest_date:
            assert isinstance(latest_date, str), f"latest_date应该是字符串类型，但实际是{type(latest_date)}"
            print("   ✅ 测试通过: 返回的是字符串类型的日期")
        
        # 测试2: 测试get_stock_history的日期范围查询
        print(f"\n2. 测试get_stock_history日期范围查询...")
        end_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_data = await mongo_service.get_stock_history(
            stock_code=stock_code,
            end_date=end_date_str,
            limit=5,
            sort="desc"
        )
        print(f"   获取到{len(history_data)}条历史数据")
        
        if history_data:
            first_date = history_data[0].get("date")
            print(f"   最新一条数据的日期: {first_date}")
            print(f"   类型: {type(first_date)}")
            
        # 测试3: 测试calculate_cci是否能正常工作
        print(f"\n3. 测试calculate_cci...")
        
        # 先获取一些历史数据
        historical_data = await mongo_service.get_stock_history(
            stock_code=stock_code,
            limit=20,
            sort="asc"
        )
        
        if historical_data:
            df = pd.DataFrame(historical_data)
            result = await ta_service.calculate_cci(df, period=14)
            print(f"   计算结果类型: {type(result)}")
            
            if isinstance(result, pd.Series):
                print(f"   计算得到{len(result)}个CCI值")
                print(f"   第一个CCI值: {result.iloc[0]}")
                print(f"   最后一个CCI值: {result.iloc[-1]}")
                print(f"   ✅ 测试通过: CCI计算成功")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 手动关闭MongoDB连接
        if hasattr(mongo_service, 'client') and mongo_service.client is not None:
            mongo_service.client.close()

if __name__ == "__main__":
    asyncio.run(test_date_functions())