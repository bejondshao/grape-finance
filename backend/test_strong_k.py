import asyncio
import pandas as pd
from app.services.mongodb_service import MongoDBService
from app.strategies.strong_k_breakout_strategy import StrongKBreakoutStrategy

async def test():
    # 获取数据
    mongo = MongoDBService()
    # 限制数据量以加快测试速度
    historical_data = await mongo.find('stock_daily_sh.600000', {}, limit=50)
    
    if not historical_data:
        print("No data found")
        return
    
    print(f"Found {len(historical_data)} data points")
    
    # 转换数据格式
    df = pd.DataFrame(historical_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    print(f"Dataframe shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # 创建策略实例并执行
    strategy = StrongKBreakoutStrategy(
        initial_capital=100000,
        max_position_pct=0.03,
        max_positions=3
    )
    
    try:
        signals = strategy.generate_signals(df, "sh.600000")
        print(f"Generated {len(signals)} signals")
        
        # 尝试转换信号
        signals_dict = []
        for signal in signals:
            signals_dict.append({
                "symbol": signal.symbol,
                "action": signal.action,
                "price": signal.price,
                "stop_loss": signal.stop_loss,
                "target_price": signal.target_price,
                "timestamp": signal.timestamp.isoformat() if hasattr(signal.timestamp, 'isoformat') else str(signal.timestamp),
                "confidence": signal.confidence,
                "stage": signal.stage,
                "reason": signal.reason
            })
        
        print(f"Converted {len(signals_dict)} signals to dict")
        if signals_dict:
            print("First signal:", signals_dict[0])
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

asyncio.run(test())