# 右侧交易策略实现指南

## 策略概述

右侧交易策略是一种趋势跟随策略，核心思想是在趋势确认后入场，追求趋势延续的收益。该策略避免预测市场底部，而是等待明确的上涨信号出现后才进行交易。

## 核心特点

- **趋势确认优先**：不抄底，等待趋势明确
- **多因子验证**：结合多个技术指标确认信号
- **严格风险控制**：设置止损和移动止损
- **资金管理**：控制单笔交易风险

## 技术指标组合

### 趋势确认指标
- **移动平均线**：MA20 > MA50 > MA200（多头排列）
- **MACD**：DIF线上穿信号线，柱状图为正
- **ADX**：>25表示强趋势

### 动量确认指标
- **RSI**：50-70区间（避免超买超卖）
- **成交量**：放量突破（>1.5倍平均量）
- **价格突破**：突破MA20或前期高点

## 入场条件

所有以下条件需同时满足：
1. MA20 > MA50 > MA200（多头排列）
2. 价格突破MA20
3. MACD DIF > 信号线且柱状图为正
4. ADX > 25（强趋势）
5. 成交量放大至1.5倍以上
6. RSI在50-70区间

## 出场条件

### 止损条件
- 跌破入场点下方8%
- 从最高点回撤10%

### 技术出场
- 跌破MA20
- MACD死叉

## 风险管理

### 资金管理
- 单笔交易风险不超过总资金2%
- 最多同时持有5只股票
- 保留5%现金作为缓冲

### 仓位计算
```
仓位大小 = 最大风险金额 / (入场价 - 止损价)
最大风险金额 = 总资金 × 2%
```

## 使用方法

### 1. 准备数据
```python
import pandas as pd

# 数据格式要求
data = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
}, index=pd.date_range(start='2020-01-01', periods=1000))
```

### 2. 创建策略
```python
from right_side_trading_strategy import RightSideTradingStrategy

strategy = RightSideTradingStrategy(
    initial_capital=100000,
    max_position_pct=0.02,
    max_positions=5
)
```

### 3. 生成信号
```python
signals = strategy.generate_signals(data, 'AAPL')
for signal in signals:
    print(f"{signal.timestamp}: {signal.action} {signal.symbol} at {signal.price}")
```

### 4. 回测策略
```python
from backtest_engine import BacktestEngine

engine = BacktestEngine(strategy)
data_dict = {'AAPL': data, 'MSFT': data2}
result = engine.run_backtest(data_dict, '2020-01-01', '2023-12-31')

print(f"总收益率: {result.total_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
print(f"胜率: {result.win_rate:.2%}")
```

### 5. 参数优化
```python
from backtest_engine import StrategyOptimizer

optimizer = StrategyOptimizer(RightSideTradingStrategy, data_dict)
param_grid = {
    'max_position_pct': [0.01, 0.02, 0.03],
    'max_positions': [3, 5, 7]
}

optimization_result = optimizer.optimize_parameters(
    param_grid, '2020-01-01', '2023-12-31', 'sharpe_ratio'
)
```

## 性能指标

### 主要指标
- **总收益率**：策略期间的总收益
- **年化收益率**：年化后的收益率
- **最大回撤**：最大的资金回撤幅度
- **夏普比率**：风险调整后的收益
- **胜率**：盈利交易占比
- **盈亏比**：总盈利/总亏损

### 可视化
```python
engine.plot_results(result, save_path='backtest_results.png')
```

## 注意事项

### 数据要求
- 至少200个交易日的数据
- 包含OHLCV数据
- 时间序列数据，建议日线

### 策略限制
- 适用于趋势性较强的市场
- 在震荡市中可能表现不佳
- 需要定期调整参数

### 风险提示
- 历史表现不代表未来收益
- 建议结合其他分析方法
- 严格执行止损策略

## 扩展优化

### 可调整参数
- 移动平均线周期
- MACD参数
- RSI周期和区间
- 成交量放大倍数
- 止损比例

### 增强功能
- 添加基本面筛选
- 市场环境识别
- 动态仓位管理
- 多时间框架分析

## 文件结构

```
grape-finance/
├── right_side_trading_strategy.py  # 主策略实现
├── backtest_engine.py              # 回测和优化引擎
├── README_right_side_trading.md    # 使用说明
└── data/                          # 数据文件目录
```

## 依赖包

```bash
pip install pandas numpy talib matplotlib
```

## 联系支持

如有问题或建议，请查看代码注释或联系开发团队。
