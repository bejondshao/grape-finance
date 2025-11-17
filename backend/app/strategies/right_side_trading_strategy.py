import numpy as np
import pandas as pd
import talib
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    confidence: float
    timestamp: datetime
    reason: str

@dataclass
class Position:
    symbol: str
    entry_price: float
    quantity: int
    entry_date: datetime
    stop_loss: float
    take_profit: float

class RightSideTradingStrategy:
    def __init__(self, 
                 initial_capital: float = 100000,
                 max_position_pct: float = 0.02,
                 max_positions: int = 5):
        """
        右侧交易策略实现
        
        Args:
            initial_capital: 初始资金
            max_position_pct: 单笔交易最大风险比例
            max_positions: 最大持仓数量
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_pct = max_position_pct
        self.max_positions = max_positions
        self.positions: Dict[str, Position] = {}
        
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # 移动平均线
        df['MA20'] = talib.SMA(df['close'], timeperiod=20)
        df['MA50'] = talib.SMA(df['close'], timeperiod=50)
        df['MA200'] = talib.SMA(df['close'], timeperiod=200)
        
        # MACD
        df['MACD_DIF'], df['MACD_SIGNAL'], df['MACD_HIST'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        
        # ADX (趋势强度)
        df['ADX'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        
        # RSI
        df['RSI'] = talib.RSI(df['close'], timeperiod=14)
        
        # 成交量指标
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df
    
    def check_entry_conditions(self, df: pd.DataFrame, current_idx: int) -> bool:
        """检查入场条件"""
        if current_idx < 200:  # 确保有足够的历史数据
            logger.debug("检查入场条件 - 数据不足，索引小于200")
            return False
            
        current = df.iloc[current_idx]
        
        # 1. 数据有效性检查
        if any(pd.isna(current[col]) for col in ['MA20', 'MA50', 'MA200', 'MACD_DIF', 'MACD_SIGNAL', 'ADX', 'RSI']):
            logger.debug("检查入场条件 - 技术指标数据不完整")
            return False
        
        # 2. 趋势确认：MA多头排列（更严格的检查）
        ma_bullish = (current['MA20'] > current['MA50'] and 
                     current['MA50'] > current['MA200'] and
                     current['MA20'] > current['MA20'] * 1.01)  # MA20向上倾斜
        
        # 3. 价格突破MA20（增加更多确认）
        # 检查最近3日是否有突破行为
        breakout_days = 0
        for i in range(max(0, current_idx-3), current_idx):
            if df.iloc[i]['close'] > df.iloc[i]['MA20'] and i > 0 and df.iloc[i-1]['close'] <= df.iloc[i-1]['MA20']:
                breakout_days += 1
        
        price_breakout = (current['close'] > current['MA20'] and 
                         breakout_days >= 1)
        
        # 4. MACD确认（零轴上方更佳）
        macd_bullish = (current['MACD_DIF'] > current['MACD_SIGNAL'] and 
                       current['MACD_HIST'] > 0 and
                       current['MACD_DIF'] > 0)  # 零轴上方
        
        # 5. 趋势强度（ADX指标检查）
        strong_trend = current['ADX'] > 25
        
        # 6. 成交量确认（持续放量）
        volume_confirm = (current['volume_ratio'] > 1.5 and
                         df.iloc[current_idx-1]['volume_ratio'] > 1.2)
        
        # 7. RSI区间（避免极端值）
        rsi_range = 50 <= current['RSI'] <= 70
        
        # 8. 排除假突破：检查前期的震荡幅度
        recent_volatility_check = True
        if current_idx >= 20:
            recent_volatility = df.iloc[current_idx-20:current_idx]['close'].std() / df.iloc[current_idx-20:current_idx]['close'].mean()
            if recent_volatility > 0.03:  # 波动率过高可能产生假信号
                recent_volatility_check = False
        
        # 综合信号（至少满足5个条件）
        conditions = [ma_bullish, price_breakout, macd_bullish, strong_trend, volume_confirm, rsi_range, recent_volatility_check]
        satisfied_conditions = sum(conditions)
        
        logger.debug(f"入场条件检查:")
        logger.debug(f"  - MA多头排列: {ma_bullish} (MA20={current['MA20']:.2f}, MA50={current['MA50']:.2f}, MA200={current['MA200']:.2f})")
        logger.debug(f"  - 价格突破MA20: {price_breakout} (价格={current['close']:.2f}, MA20={current['MA20']:.2f})")
        logger.debug(f"  - MACD看涨: {macd_bullish} (DIF={current['MACD_DIF']:.4f}, SIGNAL={current['MACD_SIGNAL']:.4f})")
        logger.debug(f"  - 趋势强度: {strong_trend} (ADX={current['ADX']:.2f})")
        logger.debug(f"  - 成交量确认: {volume_confirm} (当前倍数={current['volume_ratio']:.2f}, 前一日={df.iloc[current_idx-1]['volume_ratio']:.2f})")
        logger.debug(f"  - RSI区间: {rsi_range} (RSI={current['RSI']:.2f})")
        logger.debug(f"  - 波动率检查: {recent_volatility_check}")
        logger.debug(f"  - 满足条件数: {satisfied_conditions}/7 (要求≥5)")
        
        return satisfied_conditions >= 5
    
    def check_exit_conditions(self, df: pd.DataFrame, current_idx: int, 
                            position: Position) -> Tuple[bool, str]:
        """检查出场条件"""
        current = df.iloc[current_idx]
        
        # 1. 止损检查
        stop_loss_triggered = current['close'] <= position.stop_loss
        if stop_loss_triggered:
            logger.debug(f"止损条件触发 - 当前价格: {current['close']:.2f}, 止损价: {position.stop_loss:.2f}")
            return True, "止损"
        
        # 2. 移动止损
        move_stop_loss_triggered = current['close'] < position.entry_price * 0.9  # 回撤10%
        if move_stop_loss_triggered:
            logger.debug(f"移动止损条件触发 - 当前价格: {current['close']:.2f}, 移动止损价: {position.entry_price * 0.9:.2f}")
            return True, "移动止损"
        
        # 3. 技术指标出场
        # 跌破MA20
        ma_exit = current['close'] < current['MA20']
        if ma_exit:
            logger.debug(f"跌破MA20出场 - 当前价格: {current['close']:.2f}, MA20: {current['MA20']:.2f}")
            return True, "跌破MA20"
        
        # MACD死叉
        macd_exit = current['MACD_DIF'] < current['MACD_SIGNAL']
        if macd_exit:
            logger.debug(f"MACD死叉出场 - DIF: {current['MACD_DIF']:.4f}, SIGNAL: {current['MACD_SIGNAL']:.4f}")
            return True, "MACD死叉"
        
        logger.debug(f"出场条件检查 - 无条件满足，继续持仓")
        return False, ""
    
    def calculate_position_size(self, price: float, stop_loss: float, symbol: str = None) -> int:
        """计算仓位大小（增强版）"""
        risk_per_share = abs(price - stop_loss)
        max_risk_amount = self.current_capital * self.max_position_pct
        
        if risk_per_share == 0:
            logger.debug("风险金额为0，无法计算仓位")
            return 0
        
        # 基础仓位计算
        position_size = int(max_risk_amount / risk_per_share)
        logger.debug(f"基础仓位计算 - 最大风险金额: {max_risk_amount:.2f}, 每股风险: {risk_per_share:.2f}, 基础仓位: {position_size}")
        
        # 确保不超过可用资金
        max_affordable = int(self.current_capital * 0.95 / price)
        logger.debug(f"最大可负担仓位: {max_affordable}")
        
        # 考虑已有持仓的影响
        if symbol and len(self.positions) > 0:
            # 如果已有持仓，考虑整体风险暴露
            total_risk = sum(
                abs(pos.entry_price - pos.stop_loss) * pos.quantity 
                for pos in self.positions.values()
            )
            
            # 确保总风险不超过预设比例
            max_total_risk = self.current_capital * 0.1  # 总风险不超过10%
            available_risk = max(0, max_total_risk - total_risk)
            
            # 计算基于可用风险的仓位
            risk_based_size = int(available_risk / risk_per_share)
            position_size = min(position_size, risk_based_size)
            logger.debug(f"已有持仓影响 - 总风险: {total_risk:.2f}, 可用风险: {available_risk:.2f}, 风险调整后仓位: {risk_based_size}")
        
        # 确保最小交易单位
        min_size = max(1, int(100 / price))  # 至少交易100元
        position_size = max(min_size, position_size)
        
        final_position_size = min(position_size, max_affordable)
        logger.debug(f"最终仓位大小: {final_position_size}")
        return final_position_size
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """生成交易信号"""
        logger.info(f"开始为股票 {symbol} 生成右侧交易信号")
        df = self.calculate_technical_indicators(data)
        signals = []
        
        logger.debug(f"数据总长度: {len(df)}")
        for i in range(200, len(df)):
            current_time = df.index[i]
            current_price = df.iloc[i]['close']
            logger.debug(f"\n检查数据点 {i} - 时间: {current_time}, 价格: {current_price:.2f}")
            
            # 检查是否有持仓
            if symbol in self.positions:
                position = self.positions[symbol]
                logger.debug(f"持有仓位 - 数量: {position.quantity}, 入场价: {position.entry_price:.2f}")
                should_exit, reason = self.check_exit_conditions(df, i, position)
                
                if should_exit:
                    logger.info(f"生成卖出信号 - 股票: {symbol}, 价格: {current_price:.2f}, 原因: {reason}")
                    signals.append(Signal(
                        symbol=symbol,
                        action='SELL',
                        price=current_price,
                        confidence=1.0,
                        timestamp=current_time,
                        reason=reason
                    ))
                    del self.positions[symbol]
            else:
                # 检查入场条件
                if len(self.positions) < self.max_positions:
                    logger.debug(f"检查入场条件 - 当前持仓数: {len(self.positions)}, 最大持仓数: {self.max_positions}")
                    if self.check_entry_conditions(df, i):
                        # 计算止损位
                        stop_loss = current_price * 0.92  # 8%止损
                        logger.debug(f"满足入场条件 - 止损价设置为: {stop_loss:.2f}")
                        
                        # 计算仓位大小
                        quantity = self.calculate_position_size(current_price, stop_loss, symbol)
                        logger.debug(f"计算仓位大小结果: {quantity}")
                        
                        if quantity > 0:
                            logger.info(f"生成买入信号 - 股票: {symbol}, 价格: {current_price:.2f}, 数量: {quantity}")
                            signals.append(Signal(
                                symbol=symbol,
                                action='BUY',
                                price=current_price,
                                confidence=0.8,
                                timestamp=current_time,
                                reason="右侧交易入场信号"
                            ))
                            
                            self.positions[symbol] = Position(
                                symbol=symbol,
                                entry_price=current_price,
                                quantity=quantity,
                                entry_date=current_time,
                                stop_loss=stop_loss,
                                take_profit=current_price * 1.2  # 20%止盈目标
                            )
        
        logger.info(f"信号生成完成 - 股票: {symbol}, 生成信号数: {len(signals)}")
        return signals
    
    def backtest(self, data_dict: Dict[str, pd.DataFrame], 
                 start_date: str, end_date: str) -> Dict:
        """回测策略"""
        results = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_return': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'trade_history': []
        }
        
        # 实现回测逻辑
        # ... (详细回测实现)
        
        return results

# 使用示例
if __name__ == "__main__":
    strategy = RightSideTradingStrategy(initial_capital=100000)
    
    # 示例数据结构
    # data = pd.DataFrame({
    #     'open': [...],
    #     'high': [...], 
    #     'low': [...],
    #     'close': [...],
    #     'volume': [...]
    # }, index=pd.date_range(start='2020-01-01', periods=1000))
    
    # signals = strategy.generate_signals(data, 'AAPL')
    # print(f"Generated {len(signals)} signals")