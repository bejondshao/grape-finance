import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
from strong_k_breakout_strategy import StrongKBreakoutStrategy, StrongKSignal

@dataclass
class StrongKBacktestResult:
    """强K策略回测结果"""
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    avg_holding_days: float
    strong_k_success_rate: float
    stage_distribution: Dict[str, int]
    equity_curve: pd.Series
    trade_history: List[Dict]

class StrongKBacktestEngine:
    """强K突围策略专用回测引擎"""
    
    def __init__(self, strategy: StrongKBreakoutStrategy):
        self.strategy = strategy
        self.reset()
    
    def reset(self):
        """重置回测状态"""
        self.capital = self.strategy.initial_capital
        self.positions = {}
        self.equity_curve = []
        self.trade_history = []
        self.stage_signals = []  # 记录各阶段信号
        self.current_date = None
    
    def execute_trade(self, signal: StrongKSignal) -> Dict:
        """执行交易"""
        trade_result = {
            'date': signal.timestamp,
            'symbol': signal.symbol,
            'action': signal.action,
            'price': signal.price,
            'quantity': 0,
            'pnl': 0,
            'commission': 0,
            'stage': signal.stage,
            'reason': signal.reason,
            'confidence': signal.confidence,
            'stop_loss': signal.stop_loss,
            'target_price': signal.target_price,
            'holding_days': 0
        }
        
        if signal.action == 'BUY':
            # 计算可买数量
            available_capital = self.capital * 0.95
            quantity = int(available_capital / signal.price)
            
            if quantity > 0:
                commission = quantity * signal.price * 0.001
                total_cost = quantity * signal.price + commission
                
                if total_cost <= self.capital:
                    self.positions[signal.symbol] = {
                        'quantity': quantity,
                        'entry_price': signal.price,
                        'entry_date': signal.timestamp,
                        'stop_loss': signal.stop_loss,
                        'target_price': signal.target_price,
                        'stage': signal.stage,
                        'highest_price': signal.price
                    }
                    self.capital -= total_cost
                    
                    trade_result.update({
                        'quantity': quantity,
                        'commission': commission
                    })
                    
                    # 记录阶段信号
                    self.stage_signals.append({
                        'date': signal.timestamp,
                        'symbol': signal.symbol,
                        'stage': signal.stage,
                        'action': 'BUY',
                        'price': signal.price,
                        'reason': signal.reason
                    })
        
        elif signal.action == 'SELL' and signal.symbol in self.positions:
            position = self.positions[signal.symbol]
            quantity = position['quantity']
            
            commission = quantity * signal.price * 0.001
            proceeds = quantity * signal.price - commission
            
            pnl = (signal.price - position['entry_price']) * quantity - commission
            holding_days = (signal.timestamp - position['entry_date']).days
            
            self.capital += proceeds
            
            trade_result.update({
                'quantity': quantity,
                'pnl': pnl,
                'commission': commission,
                'holding_days': holding_days
            })
            
            # 记录阶段信号
            self.stage_signals.append({
                'date': signal.timestamp,
                'symbol': signal.symbol,
                'stage': position['stage'],
                'action': 'SELL',
                'price': signal.price,
                'reason': signal.reason,
                'pnl': pnl,
                'holding_days': holding_days
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
                    start_date: str, end_date: str) -> StrongKBacktestResult:
        """运行强K策略回测"""
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
    
    def calculate_results(self) -> StrongKBacktestResult:
        """计算强K策略回测结果"""
        if not self.equity_curve:
            return StrongKBacktestResult(0, 0, 0, 0, 0, 0, 0, 0, 0, {}, pd.Series(), [])
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('date', inplace=True)
        equity_series = equity_df['value']
        
        # 基本收益指标
        total_return = (equity_series.iloc[-1] - self.strategy.initial_capital) / self.strategy.initial_capital
        
        # 年化收益率
        days = (equity_series.index[-1] - equity_series.index[0]).days
        if days > 0:
            annualized_return = (equity_series.iloc[-1] / self.strategy.initial_capital) ** (365 / days) - 1
        else:
            annualized_return = 0
        
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
        avg_holding_days = np.mean([t['holding_days'] for t in self.trade_history if t['holding_days'] > 0]) if self.trade_history else 0
        
        # 强K成功率
        strong_k_trades = [t for t in self.trade_history if t['stage'] == 'strong_k']
        strong_k_wins = [t for t in strong_k_trades if t['pnl'] > 0]
        strong_k_success_rate = len(strong_k_wins) / len(strong_k_trades) if strong_k_trades else 0
        
        # 阶段分布统计
        stage_distribution = {}
        for signal in self.stage_signals:
            stage = signal['stage']
            if stage not in stage_distribution:
                stage_distribution[stage] = 0
            stage_distribution[stage] += 1
        
        return StrongKBacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(self.trade_history),
            avg_trade_return=avg_trade_return,
            avg_holding_days=avg_holding_days,
            strong_k_success_rate=strong_k_success_rate,
            stage_distribution=stage_distribution,
            equity_curve=equity_series,
            trade_history=self.trade_history
        )
    
    def plot_results(self, result: StrongKBacktestResult, save_path: str = None):
        """绘制强K策略回测结果"""
        fig, axes = plt.subplots(3, 2, figsize=(16, 12))
        
        # 资金曲线
        axes[0, 0].plot(result.equity_curve.index, result.equity_curve.values, linewidth=2)
        axes[0, 0].set_title('强K突围策略 - 资金曲线', fontsize=14, fontweight='bold')
        axes[0, 0].set_ylabel('组合价值')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 回撤曲线
        rolling_max = result.equity_curve.expanding().max()
        drawdown = (result.equity_curve - rolling_max) / rolling_max
        axes[0, 1].fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
        axes[0, 1].set_title('最大回撤分析', fontsize=14, fontweight='bold')
        axes[0, 1].set_ylabel('回撤比例')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 阶段分布饼图
        if result.stage_distribution:
            stages = list(result.stage_distribution.keys())
            counts = list(result.stage_distribution.values())
            axes[1, 0].pie(counts, labels=stages, autopct='%1.1f%%', startangle=90)
            axes[1, 0].set_title('信号阶段分布', fontsize=14, fontweight='bold')
        
        # 交易收益分布
        if result.trade_history:
            returns = [t['pnl'] for t in result.trade_history]
            axes[1, 1].hist(returns, bins=20, alpha=0.7, color='blue', edgecolor='black')
            axes[1, 1].set_title('单笔交易收益分布', fontsize=14, fontweight='bold')
            axes[1, 1].set_xlabel('收益金额')
            axes[1, 1].set_ylabel('交易次数')
            axes[1, 1].grid(True, alpha=0.3)
        
        # 持仓天数分布
        if result.trade_history:
            holding_days = [t['holding_days'] for t in result.trade_history if t['holding_days'] > 0]
            axes[2, 0].hist(holding_days, bins=15, alpha=0.7, color='green', edgecolor='black')
            axes[2, 0].set_title('持仓天数分布', fontsize=14, fontweight='bold')
            axes[2, 0].set_xlabel('持仓天数')
            axes[2, 0].set_ylabel('交易次数')
            axes[2, 0].grid(True, alpha=0.3)
        
        # 关键指标展示
        stats_text = f"""
        📊 核心业绩指标
        ─────────────────
        总收益率: {result.total_return:.2%}
        年化收益率: {result.annualized_return:.2%}
        最大回撤: {result.max_drawdown:.2%}
        夏普比率: {result.sharpe_ratio:.2f}
        
        🎯 交易统计
        ─────────────────
        总交易次数: {result.total_trades}
        胜率: {result.win_rate:.2%}
        盈亏比: {result.profit_factor:.2f}
        平均持仓天数: {result.avg_holding_days:.1f}
        
        ⚡ 强K策略特色
        ─────────────────
        强K成功率: {result.strong_k_success_rate:.2%}
        平均单笔收益: {result.avg_trade_return:.2f}
        """
        
        axes[2, 1].text(0.05, 0.95, stats_text, fontsize=11, verticalalignment='top',
                       fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        axes[2, 1].set_title('策略业绩总览', fontsize=14, fontweight='bold')
        axes[2, 1].axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
    
    def analyze_stage_performance(self) -> Dict:
        """分析各阶段表现"""
        stage_analysis = {}
        
        for stage in ['bottom', 'accumulation', 'left_peak', 'volume_first', 'strong_k', 'rally']:
            stage_trades = [t for t in self.trade_history if t['stage'] == stage]
            
            if stage_trades:
                winning_trades = [t for t in stage_trades if t['pnl'] > 0]
                stage_analysis[stage] = {
                    'trade_count': len(stage_trades),
                    'win_rate': len(winning_trades) / len(stage_trades),
                    'avg_return': np.mean([t['pnl'] for t in stage_trades]),
                    'avg_holding_days': np.mean([t['holding_days'] for t in stage_trades if t['holding_days'] > 0])
                }
            else:
                stage_analysis[stage] = {
                    'trade_count': 0,
                    'win_rate': 0,
                    'avg_return': 0,
                    'avg_holding_days': 0
                }
        
        return stage_analysis

class StrongKStrategyOptimizer:
    """强K策略优化器"""
    
    def __init__(self, strategy_class, data_dict: Dict[str, pd.DataFrame]):
        self.strategy_class = strategy_class
        self.data_dict = data_dict
    
    def optimize_parameters(self, param_grid: Dict[str, List], 
                          start_date: str, end_date: str,
                          metric: str = 'sharpe_ratio') -> Dict:
        """优化强K策略参数"""
        best_params = None
        best_score = -float('inf')
        results = []
        
        from itertools import product
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        for combination in product(*param_values):
            params = dict(zip(param_names, combination))
            
            # 创建策略实例
            strategy = self.strategy_class(**params)
            
            # 运行回测
            engine = StrongKBacktestEngine(strategy)
            result = engine.run_backtest(self.data_dict, start_date, end_date)
            
            # 记录结果
            score = getattr(result, metric)
            results.append({
                'params': params,
                'score': score,
                'result': result,
                'strong_k_success_rate': result.strong_k_success_rate
            })
            
            # 更新最佳参数（强K成功率权重更高）
            combined_score = score * 0.7 + result.strong_k_success_rate * 0.3
            if combined_score > best_score:
                best_score = combined_score
                best_params = params
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'all_results': results
        }

# 使用示例
if __name__ == "__main__":
    # 创建强K策略
    strategy = StrongKBreakoutStrategy(initial_capital=100000)
    
    # 创建回测引擎
    engine = StrongKBacktestEngine(strategy)
    
    # 示例：需要提供实际数据
    # data_dict = {
    #     'AAPL': pd.DataFrame(...),
    #     'MSFT': pd.DataFrame(...)
    # }
    
    # 运行回测
    # result = engine.run_backtest(data_dict, '2020-01-01', '2023-12-31')
    # engine.plot_results(result, save_path='strong_k_backtest.png')
    
    # 阶段分析
    # stage_analysis = engine.analyze_stage_performance()
    # print("各阶段表现分析:", stage_analysis)
    
    # 参数优化
    # optimizer = StrongKStrategyOptimizer(StrongKBreakoutStrategy, data_dict)
    # param_grid = {
    #     'max_position_pct': [0.02, 0.03, 0.04],
    #     'max_positions': [2, 3, 4]
    # }
    # optimization_result = optimizer.optimize_parameters(param_grid, '2020-01-01', '2023-12-31')
