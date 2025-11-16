#!/usr/bin/env python3
"""
右侧交易策略演示脚本

这个脚本展示了如何使用右侧交易策略进行回测和优化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from right_side_trading_strategy import RightSideTradingStrategy
from backtest_engine import BacktestEngine, StrategyOptimizer

def generate_sample_data(symbol: str, start_date: str, end_date: str, initial_price: float = 100) -> pd.DataFrame:
    """
    生成示例股票数据用于演示
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        initial_price: 初始价格
        
    Returns:
        pd.DataFrame: 包含OHLCV数据的DataFrame
    """
    # 生成日期范围
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(date_range)
    
    # 生成随机价格数据（模拟真实股票波动）
    np.random.seed(42)  # 固定随机种子保证结果可重现
    
    # 生成收益率序列（几何布朗运动）
    returns = np.random.normal(0.0005, 0.02, n_days)  # 平均收益0.05%，标准差2%
    
    # 计算价格序列
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # 添加一些趋势性（模拟牛市或熊市）
    trend = np.linspace(0, 0.3, n_days)  # 30%的趋势
    prices = prices * (1 + trend)
    
    # 生成OHLC数据
    data = []
    for i in range(n_days):
        base_price = prices[i]
        open_price = base_price * (1 + np.random.normal(0, 0.01))
        high_price = max(open_price, base_price) * (1 + abs(np.random.normal(0, 0.02)))
        low_price = min(open_price, base_price) * (1 - abs(np.random.normal(0, 0.02)))
        close_price = base_price
        
        # 成交量（与价格波动相关）
        volatility = abs(high_price - low_price) / base_price
        volume = int(1000000 * (1 + volatility * 10 + np.random.normal(0, 0.5)))
        
        data.append({
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=date_range)
    return df

def run_basic_backtest():
    """运行基础回测演示"""
    print("=== 右侧交易策略基础回测演示 ===")
    
    # 生成示例数据
    data = generate_sample_data('AAPL', '2020-01-01', '2023-12-31', 100)
    
    # 创建策略
    strategy = RightSideTradingStrategy(
        initial_capital=100000,
        max_position_pct=0.02,
        max_positions=5
    )
    
    # 生成交易信号
    signals = strategy.generate_signals(data, 'AAPL')
    print(f"生成 {len(signals)} 个交易信号")
    
    # 显示前几个信号
    for i, signal in enumerate(signals[:5]):
        print(f"信号 {i+1}: {signal.timestamp.date()} {signal.action} {signal.symbol} "
              f"@ {signal.price:.2f} ({signal.reason})")
    
    return strategy, data, signals

def run_advanced_backtest():
    """运行高级回测（多股票）"""
    print("\n=== 多股票组合回测演示 ===")
    
    # 生成多支股票数据
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    data_dict = {}
    
    for i, symbol in enumerate(symbols):
        # 为每支股票设置不同的初始价格和波动率
        initial_price = 100 + i * 50
        data_dict[symbol] = generate_sample_data(symbol, '2020-01-01', '2023-12-31', initial_price)
    
    # 创建策略和回测引擎
    strategy = RightSideTradingStrategy(initial_capital=100000)
    engine = BacktestEngine(strategy)
    
    # 运行回测
    result = engine.run_backtest(data_dict, '2020-01-01', '2023-12-31')
    
    # 显示回测结果
    print(f"回测结果:")
    print(f"总收益率: {result.total_return:.2%}")
    print(f"年化收益率: {result.annualized_return:.2%}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"胜率: {result.win_rate:.2%}")
    print(f"总交易次数: {result.total_trades}")
    
    # 绘制结果
    engine.plot_results(result, 'backtest_results.png')
    print("回测图表已保存为 'backtest_results.png'")
    
    return result

def run_parameter_optimization():
    """运行参数优化"""
    print("\n=== 策略参数优化演示 ===")
    
    # 生成示例数据
    symbols = ['AAPL', 'MSFT']
    data_dict = {}
    
    for symbol in symbols:
        data_dict[symbol] = generate_sample_data(symbol, '2020-01-01', '2023-12-31', 100)
    
    # 创建优化器
    optimizer = StrategyOptimizer(RightSideTradingStrategy, data_dict)
    
    # 定义参数网格
    param_grid = {
        'max_position_pct': [0.01, 0.02, 0.03],
        'max_positions': [3, 5, 7]
    }
    
    # 运行优化
    optimization_result = optimizer.optimize_parameters(
        param_grid, '2020-01-01', '2023-12-31', 'sharpe_ratio'
    )
    
    # 显示优化结果
    print(f"最佳参数: {optimization_result['best_params']}")
    print(f"最佳夏普比率: {optimization_result['best_score']:.2f}")
    
    # 显示所有参数组合结果
    print("\n所有参数组合表现:")
    for i, result in enumerate(optimization_result['all_results']):
        print(f"组合 {i+1}: {result['params']} -> 夏普比率: {result['score']:.2f}")
    
    return optimization_result

def analyze_strategy_performance():
    """分析策略性能特征"""
    print("\n=== 策略性能分析 ===")
    
    # 运行回测获取数据
    result = run_advanced_backtest()
    
    # 分析交易统计
    if result.trade_history:
        winning_trades = [t for t in result.trade_history if t['pnl'] > 0]
        losing_trades = [t for t in result.trade_history if t['pnl'] < 0]
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        print(f"平均盈利: {avg_win:.2f}")
        print(f"平均亏损: {avg_loss:.2f}")
        print(f"盈亏比: {abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "盈亏比: ∞")
        
        # 分析持仓时间
        if len(result.trade_history) >= 2:
            # 这里可以添加持仓时间分析
            print("持仓时间分析功能待完善")
    
    return result

def strategy_insights():
    """提供策略洞察"""
    print("\n=== 右侧交易策略核心洞察 ===")
    
    insights = [
        "🎯 趋势确认是核心：右侧交易的核心是等待趋势明确，而不是预测底部",
        "📊 多指标验证：结合MA、MACD、ADX、RSI、成交量等多个指标进行交叉验证",
        "⚖️ 严格风险管理：8%止损+10%移动止损，单笔风险不超过总资金2%",
        "📈 适合趋势性市场：在单边上涨或下跌市中表现较好，震荡市中可能不佳",
        "🔄 需要定期优化：参数需要根据市场环境调整，建议每季度重新优化",
        "📉 避免过度交易：严格的入场条件确保每笔交易都有充分理由",
        "💰 仓位控制：考虑整体风险暴露，确保不超过总风险限制",
        "📋 交易纪律：严格执行止损和出场条件，避免情绪化交易"
    ]
    
    for insight in insights:
        print(insight)

def main():
    """主函数"""
    print("右侧交易策略完整演示")
    print("=" * 50)
    
    try:
        # 运行基础回测
        strategy, data, signals = run_basic_backtest()
        
        # 运行高级回测
        result = run_advanced_backtest()
        
        # 运行参数优化
        optimization_result = run_parameter_optimization()
        
        # 分析策略性能
        performance_result = analyze_strategy_performance()
        
        # 提供策略洞察
        strategy_insights()
        
        print("\n" + "=" * 50)
        print("演示完成！建议在实际使用前：")
        print("1. 使用真实市场数据进行回测")
        print("2. 根据具体股票特性调整参数")
        print("3. 结合基本面分析进行选股")
        print("4. 定期监控和优化策略")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        print("请确保已安装必要的依赖包: pandas, numpy, matplotlib, talib")

if __name__ == "__main__":
    main()