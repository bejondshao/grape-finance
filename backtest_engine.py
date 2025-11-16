import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
from right_side_trading_strategy import RightSideTradingStrategy, Signal, Position

@dataclass
class BacktestResult:
    """回测结果数据类"""
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    equity_curve: pd.Series
    trade_history: List[Dict]

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, strategy: RightSideTradingStrategy):
        self.strategy = strategy
        self.reset()
    
    def reset(self):
        """重置回测状态"""
        self.capital = self.strategy.initial_capital
        self.positions = {}
        self.equity_curve = []
        self.trade_history = []
        self.current_date = None
    
    def execute_trade(self, signal: Signal) -> Dict:
        """执行交易"""
        trade_result = {
            'date': signal.timestamp,
            'symbol': signal.symbol,
            'action': signal.action,
            'price': signal.price,
            'quantity': 0,
            'pnl': 0,
            'commission': 0,
            'reason': signal.reason
        }
        
        if signal.action == 'BUY':
            # 计算可买数量
            available_capital = self.capital * 0.95  # 留5%作为缓冲
            quantity = int(available_capital / signal.price)
            
            if quantity > 0:
                commission = quantity * signal.price * 0.001  # 0.1%手续费
                total_cost = quantity * signal.price + commission
                
                if total_cost <= self.capital:
                    self.positions[signal.symbol] = {
                        'quantity': quantity,
                        'entry_price': signal.price,
                        'entry_date': signal.timestamp
                    }
                    self.capital -= total_cost
                    
                    trade_result.update({
                        'quantity': quantity,
                        'commission': commission
                    })
        
        elif signal.action == 'SELL' and signal.symbol in self.positions:
            position = self.positions[signal.symbol]
            quantity = position['quantity']
            
            commission = quantity * signal.price * 0.001
            proceeds = quantity * signal.price - commission
            
            pnl = (signal.price - position['entry_price']) * quantity - commission
            self.capital += proceeds
            
            trade_result.update({
                'quantity': quantity,
                'pnl': pnl,
                'commission': commission
            })
            
            del self.positions[signal.symbol]
        
        return trade_result
    
    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """计算当前组合价值"""
        total_value = self.capital
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total_value += position['quantity'] * current_prices[symbol]
        
        return total_value
    
    def run_backtest(self, data_dict: Dict[str, pd.DataFrame], 
                    start_date: str, end_date: str) -> BacktestResult:
        """运行回测"""
        self.reset()
        
        # 生成所有交易信号
        all_signals = []
        for symbol, data in data_dict.items():
            signals = self.strategy.generate_signals(data, symbol)
            all_signals.extend(signals)
        
        # 按时间排序信号
        all_signals.sort(key=lambda x: x.timestamp)
        
        # 过滤时间范围
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        filtered_signals = [s for s in all_signals 
                          if start_dt <= s.timestamp <= end_dt]
        
        # 执行回测
        for signal in filtered_signals:
            self.current_date = signal.timestamp
            
            # 执行交易
            trade_result = self.execute_trade(signal)
            if trade_result['quantity'] > 0:
                self.trade_history.append(trade_result)
            
            # 记录组合价值
            current_prices = {symbol: data.loc[data.index <= signal.timestamp]['close'].iloc[-1] 
                            for symbol, data in data_dict.items() 
                            if len(data.loc[data.index <= signal.timestamp]) > 0}
            
            portfolio_value = self.calculate_portfolio_value(current_prices)
            self.equity_curve.append({
                'date': signal.timestamp,
                'value': portfolio_value
            })
        
        # 计算回测结果
        return self.calculate_results()
    
    def calculate_results(self) -> BacktestResult:
        """计算回测结果"""
        if not self.equity_curve:
            return BacktestResult(0, 0, 0, 0, 0, 0, 0, 0, pd.Series(), [])
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('date', inplace=True)
        equity_series = equity_df['value']
        
        # 基本收益指标
        total_return = (equity_series.iloc[-1] - self.strategy.initial_capital) / self.strategy.initial_capital
        
        # 年化收益率
        days = (equity_series.index[-1] - equity_series.index[0]).days
        annualized_return = (equity_series.iloc[-1] / self.strategy.initial_capital) ** (365 / days) - 1
        
        # 最大回撤
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 夏普比率
        returns = equity_series.pct_change().dropna()
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 交易统计
        winning_trades = [t for t in self.trade_history if t['pnl'] > 0]
        losing_trades = [t for t in self.trade_history if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / len(self.trade_history) if self.trade_history else 0
        
        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        avg_trade_return = np.mean([t['pnl'] for t in self.trade_history]) if self.trade_history else 0
        
        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(self.trade_history),
            avg_trade_return=avg_trade_return,
            equity_curve=equity_series,
            trade_history=self.trade_history
        )
    
    def plot_results(self, result: BacktestResult, save_path: str = None):
        """绘制回测结果"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 资金曲线
        axes[0, 0].plot(result.equity_curve.index, result.equity_curve.values)
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Portfolio Value')
        axes[0, 0].grid(True)
        
        # 回撤曲线
        rolling_max = result.equity_curve.expanding().max()
        drawdown = (result.equity_curve - rolling_max) / rolling_max
        axes[0, 1].fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
        axes[0, 1].set_title('Drawdown')
        axes[0, 1].set_ylabel('Drawdown %')
        axes[0, 1].grid(True)
        
        # 每月收益
        monthly_returns = result.equity_curve.resample('M').last().pct_change().dropna()
        axes[1, 0].bar(monthly_returns.index, monthly_returns.values)
        axes[1, 0].set_title('Monthly Returns')
        axes[1, 0].set_ylabel('Return %')
        axes[1, 0].grid(True)
        
        # 交易统计
        stats_text = f"""
        Total Return: {result.total_return:.2%}
        Annualized Return: {result.annualized_return:.2%}
        Max Drawdown: {result.max_drawdown:.2%}
        Sharpe Ratio: {result.sharpe_ratio:.2f}
        Win Rate: {result.win_rate:.2%}
        Profit Factor: {result.profit_factor:.2f}
        Total Trades: {result.total_trades}
        Avg Trade Return: {result.avg_trade_return:.2f}
        """
        axes[1, 1].text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center')
        axes[1, 1].set_title('Performance Statistics')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

class StrategyOptimizer:
    """策略优化器"""
    
    def __init__(self, strategy_class, data_dict: Dict[str, pd.DataFrame]):
        self.strategy_class = strategy_class
        self.data_dict = data_dict
    
    def optimize_parameters(self, param_grid: Dict[str, List], 
                          start_date: str, end_date: str,
                          metric: str = 'sharpe_ratio') -> Dict:
        """优化策略参数"""
        best_params = None
        best_score = -float('inf')
        results = []
        
        # 生成所有参数组合
        from itertools import product
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        for combination in product(*param_values):
            params = dict(zip(param_names, combination))
            
            # 创建策略实例
            strategy = self.strategy_class(**params)
            
            # 运行回测
            engine = BacktestEngine(strategy)
            result = engine.run_backtest(self.data_dict, start_date, end_date)
            
            # 记录结果
            score = getattr(result, metric)
            results.append({
                'params': params,
                'score': score,
                'result': result
            })
            
            # 更新最佳参数
            if score > best_score:
                best_score = score
                best_params = params
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'all_results': results
        }

# 使用示例
if __name__ == "__main__":
    # 创建策略
    strategy = RightSideTradingStrategy(initial_capital=100000)
    
    # 创建回测引擎
    engine = BacktestEngine(strategy)
    
    # 示例：需要提供实际数据
    # data_dict = {
    #     'AAPL': pd.DataFrame(...),
    #     'MSFT': pd.DataFrame(...)
    # }
    
    # 运行回测
    # result = engine.run_backtest(data_dict, '2020-01-01', '2023-12-31')
    # engine.plot_results(result)
    
    # 参数优化
    # optimizer = StrategyOptimizer(RightSideTradingStrategy, data_dict)
    # param_grid = {
    #     'max_position_pct': [0.01, 0.02, 0.03],
    #     'max_positions': [3, 5, 7]
    # }
    # optimization_result = optimizer.optimize_parameters(param_grid, '2020-01-01', '2023-12-31')
