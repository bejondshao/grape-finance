import pandas as pd
import numpy as np
import asyncio
from app.services.technical_analysis_service import TechnicalAnalysisService

def create_test_data():
    """创建用于测试的股票数据"""
    # 创建一个简单的测试数据集
    dates = pd.date_range(start='2025-01-01', periods=20)
    # 创建一个具有明显趋势的数据，便于验证CCI计算
    base_price = 100
    high = [base_price + i*0.5 + np.random.random()*5 for i in range(20)]
    low = [base_price + i*0.5 - np.random.random()*5 for i in range(20)]
    close = [(h + l) / 2 + (np.random.random() - 0.5) * 2 for h, l in zip(high, low)]
    
    return pd.DataFrame({
        'date': dates,
        'high': high,
        'low': low,
        'close': close
    })

async def test_cci_calculation():
    """测试CCI计算逻辑"""
    print("开始测试CCI计算逻辑...")
    
    # 创建测试数据
    test_df = create_test_data()
    print("测试数据创建完成")
    print(test_df.head())
    
    # 初始化服务
    service = TechnicalAnalysisService()
    
    # 测试不同周期的CCI计算
    periods = [7, 14, 21]
    
    for period in periods:
        print(f"\n测试周期 {period} 的CCI计算：")
        try:
            # 计算CCI
            cci_result = await service.calculate_cci(test_df, period=period)
            
            # 验证结果
            print(f"计算结果长度: {len(cci_result)}")
            print(f"非NaN值数量: {cci_result.notna().sum()}")
            print(f"结果索引类型: {type(cci_result.index)}")
            print(f"是否与输入索引匹配: {all(cci_result.index == test_df.index)}")
            
            # 打印部分结果
            print("\n部分CCI结果:")
            valid_results = cci_result.dropna()
            if len(valid_results) > 0:
                print(valid_results.head())
            else:
                print("没有有效的CCI计算结果")
                
        except Exception as e:
            print(f"计算周期 {period} 的CCI时出错: {e}")
    
    # 测试边界情况
    print("\n测试边界情况：")
    
    # 测试数据不足的情况
    short_df = test_df.iloc[:5].copy()
    try:
        cci_short = await service.calculate_cci(short_df, period=10)
        print(f"数据不足时的结果: {cci_short.isna().all()}")
    except Exception as e:
        print(f"数据不足测试时出错: {e}")
    
    # 测试MAD为零的情况（所有价格相同）
    flat_df = pd.DataFrame({
        'date': pd.date_range(start='2025-01-01', periods=14),
        'high': [100] * 14,
        'low': [100] * 14,
        'close': [100] * 14
    })
    try:
        cci_flat = await service.calculate_cci(flat_df, period=5)
        print(f"价格不变时的结果: {cci_flat.isna().all()}")
    except Exception as e:
        print(f"价格不变测试时出错: {e}")
    
    print("\nCCI计算逻辑测试完成")

if __name__ == "__main__":
    asyncio.run(test_cci_calculation())