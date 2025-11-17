#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强K突围策略回测示例
演示如何使用强K策略进行回测分析
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

from strong_k_breakout_strategy import StrongKBreakoutStrategy
from strong_k_backtest_engine import StrongKBacktestEngine, StrongKStrategyOptimizer


def generate_sample_data(symbol='AAPL', days=1000):
    """
    生成示例数据（如果没有真实数据源）
    """
    print(f"为 {symbol} 生成 {days} 天的示例数据...")
    
    # 创建日期范围
    dates = pd.date_range(start='2020-01-01', periods=days, freq='D')
    
    # 生成价格数据（模拟真实市场波动）
    np.random.seed(42)
    
    # 初始价格
    initial_price = 100.0
    prices = [initial_price]
    
    for i in range(1, days):
        # 添加趋势和随机波动
        trend = 0.0002  # 小幅上升趋势
        volatility = 0.02  # 2%日波动率
        
        # 随机游走 + 趋势
        daily_return = np.random.normal(trend, volatility)
        new_price = prices[-1] * (1 + daily_return)
        prices.append(max(new_price, 1.0))  # 确保价格为正
    
    # 生成OHLCV数据
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 模拟开高低收
        volatility_factor = 0.01 + np.random.random() * 0.02
        
        high = close * (1 + volatility_factor)
        low = close * (1 - volatility_factor)
        
        if i == 0:
            open_price = close
        else:
            # 开盘价接近前一日收盘价
            open_price = data[-1]['close'] * (1 + np.random.normal(0, 0.005))
        
        # 确保价格关系合理
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # 生成成交量（与价格波动相关）
        base_volume = 1000000
        volume_variation = abs(daily_return) if 'daily_return' in locals() else 0.01
        volume = int(base_volume * (1 + volume_variation * 10) * (0.5 + np.random.random()))
        
        data.append({
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    return df


def download_real_data(symbols=['AAPL', 'MSFT', 'GOOGL'], period='2y'):
    """
    下载真实股票数据（需要yfinance包）
    """
    print(f"下载真实数据: {symbols}")
    
    try:
        data_dict = {}
        for symbol in symbols:
            print(f"下载 {symbol} 数据...")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            
            # 重命名列以匹配策略要求
            df.columns = [col.lower() for col in df.columns]
            
            # 确保有必要的列
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if all(col in df.columns for col in required_cols):
                data_dict[symbol] = df[required_cols]
                print(f"✅ {symbol} 数据下载成功: {len(df)} 天")
            else:
                print(f"❌ {symbol} 数据格式不正确")
        
        return data_dict
        
    except Exception as e:
        print(f"❌ 下载真实数据失败: {e}")
        print("将使用示例数据进行演示...")
        return None


def run_basic_backtest():
    """
    运行基础回测示例
    """
    print("=" * 60)
    print("强K突围策略基础回测示例")
    print("=" * 60)
    
    # 1. 创建策略实例
    strategy = StrongKBreakoutStrategy(
        initial_capital=100000,
        max_position_pct=0.03,  # 单笔风险3%
        max_positions=3
    )
    
    # 2. 准备数据
    print("\n📊 准备数据...")
    
    # 尝试下载真实数据，失败则使用示例数据
    real_data = download_real_data(['AAPL', 'MSFT'], period='2y')
    
    if real_data:
        data_dict = real_data
    else:
        # 使用示例数据
        data_dict = {
            'AAPL': generate_sample_data('AAPL', 500),
            'MSFT': generate_sample_data('MSFT', 500)
        }
    
    # 3. 创建回测引擎
    print("\n🚀 创建回测引擎...")
    engine = StrongKBacktestEngine(strategy)
    
    # 4. 运行回测
    print("\n⏳ 运行回测...")
    start_date = data_dict['AAPL'].index[0].strftime('%Y-%m-%d')
    end_date = data_dict['AAPL'].index[-1].strftime('%Y-%m-%d')
    
    result = engine.run_backtest(data_dict, start_date, end_date)
    
    # 5. 显示结果
    print("\n📈 回测结果:")
    print("-" * 40)
    print(f"初始资金: ¥{result.initial_capital:,.0f}")
    print(f"最终资金: ¥{result.final_capital:,.0f}")
    print(f"总收益率: {result.total_return:.2%}")
    print(f"年化收益率: {result.annualized_return:.2%}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"胜率: {result.win_rate:.2%}")
    print(f"盈亏比: {result.profit_factor:.2f}")
    print(f"交易次数: {result.total_trades}")
    print(f"强K成功率: {result.strong_k_success_rate:.2%}")
    
    # 6. 阶段分析
    print("\n🎯 阶段分析:")
    stage_analysis = engine.analyze_stage_performance()
    for stage, stats in stage_analysis.items():
        if stats['count'] > 0:
            print(f"  {stage}: {stats['count']}次, "
                  f"胜率: {stats['win_rate']:.1%}, "
                  f"平均收益: {stats['avg_return']:.1%}")
    
    # 7. 生成图表
    print("\n📊 生成分析图表...")
    try:
        engine.plot_results(result, save_path='strong_k_backtest_results.png')
        print("✅ 图表已保存为: strong_k_backtest_results.png")
    except Exception as e:
        print(f"❌ 图表生成失败: {e}")
        print("请确保matplotlib正确安装")
    
    return result


def run_parameter_optimization():
    """
    运行参数优化示例
    """
    print("\n" + "=" * 60)
    print("强K突围策略参数优化示例")
    print("=" * 60)
    
    # 准备数据
    data_dict = {
        'AAPL': generate_sample_data('AAPL', 300),
        'MSFT': generate_sample_data('MSFT', 300)
    }
    
    # 定义参数网格
    param_grid = {
        'max_position_pct': [0.02, 0.03, 0.04],
        'max_positions': [2, 3, 4]
    }
    
    print(f"参数网格: {param_grid}")
    
    # 创建优化器
    optimizer = StrongKStrategyOptimizer(StrongKBreakoutStrategy, data_dict)
    
    # 运行优化
    print("\n⏳ 运行参数优化...")
    optimization_result = optimizer.optimize_parameters(
        param_grid, 
        start_date=data_dict['AAPL'].index[0].strftime('%Y-%m-%d'),
        end_date=data_dict['AAPL'].index[-1].strftime('%Y-%m-%d'),
        optimization_target='sharpe_ratio'
    )
    
    # 显示优化结果
    print("\n🎯 优化结果:")
    print("-" * 40)
    print(f"最佳参数: {optimization_result['best_params']}")
    print(f"最佳得分: {optimization_result['best_score']:.4f}")
    
    # 显示所有结果
    print("\n📋 所有参数组合结果:")
    for params, result in optimization_result['all_results']:
        print(f"  {params}: 夏普比率={result['sharpe_ratio']:.3f}, "
              f"强K成功率={result['strong_k_success_rate']:.1%}")
    
    return optimization_result


def analyze_single_symbol():
    """
    分析单个股票的强K信号
    """
    print("\n" + "=" * 60)
    print("单个股票强K信号分析示例")
    print("=" * 60)
    
    # 创建策略
    strategy = StrongKBreakoutStrategy(initial_capital=100000)
    
    # 生成数据
    data = generate_sample_data('DEMO', 800)
    
    # 生成信号
    print("\n🔍 分析强K信号...")
    signals = strategy.generate_signals(data, 'DEMO')
    
    # 统计信号
    buy_signals = [s for s in signals if s.action == 'BUY']
    sell_signals = [s for s in signals if s.action == 'SELL']
    
    print(f"总信号数: {len(signals)}")
    print(f"买入信号: {len(buy_signals)}")
    print(f"卖出信号: {len(sell_signals)}")
    
    # 显示最近的信号
    print("\n📅 最近信号:")
    for signal in signals[-10:]:
        print(f"{signal.timestamp.strftime('%Y-%m-%d')}: "
              f"{signal.action} {signal.symbol} "
              f"@{signal.price:.2f} "
              f"[{signal.stage}] {signal.reason}")
    
    # 获取市场分析
    print("\n📊 市场分析:")
    analysis = strategy.get_market_analysis(data, 'DEMO')
    print(f"当前阶段: {analysis['current_stage']}")
    print(f"左峰信息: {analysis['left_peak']}")
    print(f"量在价先: {analysis['volume_first']}")
    print(f"技术面: {analysis['technical_summary']}")
    
    return signals, analysis


def main():
    """
    主函数 - 运行所有示例
    """
    print("🚀 强K突围策略回测系统")
    print("=" * 60)
    
    try:
        # 1. 基础回测
        result = run_basic_backtest()
        
        # 2. 参数优化
        optimization = run_parameter_optimization()
        
        # 3. 单股分析
        signals, analysis = analyze_single_symbol()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        print("请检查依赖包是否正确安装:")
        print("pip install pandas numpy yfinance matplotlib")


if __name__ == "__main__":
    main()
