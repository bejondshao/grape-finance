import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """交易信号"""
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    confidence: float
    timestamp: datetime
    reason: str

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    entry_price: float
    quantity: int
    entry_date: datetime
    stop_loss: float
    take_profit: float

class BottomReversalStrategy:
    """底部反转策略 - 仅基于量价关系发现触底后缓慢反弹并在特定日期放量的股票"""
    
    def __init__(self, 
                 initial_capital: float = 100000,
                 max_position_pct: float = 0.03,
                 max_positions: int = 5):
        """
        底部反转策略初始化
        
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
        
    def identify_bottom_zone(self, df: pd.DataFrame, current_idx: int) -> bool:
        """识别底部区域 - 仅基于量价关系"""
        if current_idx < 60:
            return False
            
        current = df.iloc[current_idx]
        recent_30 = df.iloc[current_idx-30:current_idx]
        recent_60 = df.iloc[current_idx-60:current_idx]
        
        # 1. 当前价格处于近期低位
        low_price_position = current['close'] < recent_30['close'].quantile(0.3)
        
        # 2. 前期有明显下跌
        price_decline_60d = recent_60['close'].max() / current['close'] > 1.15   # 60天内最大跌幅超过15%
        
        # 3. 成交量特征
        # 前期成交量萎缩（最近30天）
        volume_low = recent_30['volume'].mean() < recent_60['volume'].mean() * 0.7  # 成交量萎缩至前期的70%以下
        
        # 当前成交量开始放大
        volume_recovery = current['volume'] > recent_30['volume'].mean() * 1.5     # 当前成交量超过平均1.5倍
        
        # 记录详细日志
        logger.debug(f"底部区域识别:")
        logger.debug(f"  - 价格位置: {current['close']:.2f} (近期低位: {low_price_position})")
        logger.debug(f"  - 60天最大跌幅: {recent_60['close'].max() / current['close']:.2%} (>15%: {price_decline_60d})")
        logger.debug(f"  - 成交量萎缩: {recent_30['volume'].mean():.0f} < {recent_60['volume'].mean() * 0.7:.0f} ({volume_low})")
        logger.debug(f"  - 成交量恢复: {current['volume']:.0f} > {recent_30['volume'].mean() * 1.5:.0f} ({volume_recovery})")
        
        return (low_price_position and 
                price_decline_60d and 
                volume_low and 
                volume_recovery)
    
    def identify_reversal_signal(self, df: pd.DataFrame, current_idx: int) -> bool:
        """识别反转信号 - 仅基于量价关系"""
        if current_idx < 20:
            return False
            
        current = df.iloc[current_idx]
        prev_5 = df.iloc[current_idx-5:current_idx]
        
        # 1. 价格上涨趋势（连续上涨）
        consecutive_up_days = 0
        for i in range(len(prev_5)-1, -1, -1):
            if prev_5.iloc[i]['close'] > prev_5.iloc[i]['open']:
                consecutive_up_days += 1
            else:
                break
        
        rising_trend = consecutive_up_days >= 3  # 连续3天阳线
        
        # 2. 成交量配合（放量上涨）
        volume_ma_10 = df.iloc[max(0, current_idx-10):current_idx]['volume'].mean()
        high_volume = current['volume'] > volume_ma_10 * 2.0  # 成交量超过10日均量2倍
        
        # 3. 价格涨幅确认
        price_change_5d = (current['close'] / prev_5['close'].iloc[0]) - 1  # 5天累计涨幅
        significant_gain = price_change_5d > 0.05  # 5天累计上涨超过5%
        
        # 记录详细日志
        logger.debug(f"反转信号识别:")
        logger.debug(f"  - 连续上涨天数: {consecutive_up_days} (>=3: {rising_trend})")
        logger.debug(f"  - 成交量放大: {current['volume']:.0f} > {volume_ma_10 * 2.0:.0f} ({high_volume})")
        logger.debug(f"  - 5天累计涨幅: {price_change_5d:.2%} (>5%: {significant_gain})")
        
        return rising_trend and high_volume and significant_gain
    
    def check_entry_conditions(self, df: pd.DataFrame, current_idx: int) -> bool:
        """检查入场条件 - 仅基于量价关系"""
        if current_idx < 60:
            logger.debug("检查入场条件 - 数据不足，索引小于60")
            return False
            
        # 检查是否处于底部区域
        in_bottom_zone = self.identify_bottom_zone(df, current_idx)
        if not in_bottom_zone:
            logger.debug("检查入场条件 - 不在底部区域")
            return False
            
        # 检查是否有反转信号
        reversal_signal = self.identify_reversal_signal(df, current_idx)
        if not reversal_signal:
            logger.debug("检查入场条件 - 无反转信号")
            return False
            
        current = df.iloc[current_idx]
        
        # 综合条件判断
        # 1. 底部区域确认
        # 2. 反转信号确认
        # 3. 成交量确认（放量）
        volume_confirm = current['volume'] > df.iloc[max(0, current_idx-20):current_idx]['volume'].mean() * 1.8
        
        logger.debug(f"入场条件检查:")
        logger.debug(f"  - 底部区域: {in_bottom_zone}")
        logger.debug(f"  - 反转信号: {reversal_signal}")
        logger.debug(f"  - 成交量确认: {volume_confirm}")
        
        return in_bottom_zone and reversal_signal and volume_confirm
    
    def check_exit_conditions(self, df: pd.DataFrame, current_idx: int, 
                            position: Position) -> Tuple[bool, str]:
        """检查出场条件 - 仅基于量价关系"""
        current = df.iloc[current_idx]
        
        # 1. 止损检查（8%止损）
        stop_loss_triggered = current['close'] <= position.stop_loss
        if stop_loss_triggered:
            logger.debug(f"止损条件触发 - 当前价格: {current['close']:.2f}, 止损价: {position.stop_loss:.2f}")
            return True, "止损"
        
        # 2. 回撤止损（从最高价回撤10%）
        highest_price_since_entry = df.iloc[position.entry_date:current_idx+1]['high'].max()
        drawdown_stop_triggered = current['close'] <= highest_price_since_entry * 0.9
        if drawdown_stop_triggered:
            logger.debug(f"回撤止损条件触发 - 当前价格: {current['close']:.2f}, 回撤止损价: {highest_price_since_entry * 0.9:.2f}")
            return True, "回撤止损"
        
        # 3. 放量下跌出场
        volume_ma_10 = df.iloc[max(0, current_idx-10):current_idx]['volume'].mean()
        heavy_volume_down = (current['close'] < current['open'] and 
                           current['volume'] > volume_ma_10 * 2.0)
        if heavy_volume_down:
            logger.debug(f"放量下跌出场 - 当前价格: {current['close']:.2f}, 开盘价: {current['open']:.2f}, 成交量: {current['volume']:.0f}")
            return True, "放量下跌"
        
        logger.debug(f"出场条件检查 - 无条件满足，继续持仓")
        return False, ""
    
    def calculate_position_size(self, price: float, stop_loss: float, symbol: str = None) -> int:
        """计算仓位大小"""
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
            max_total_risk = self.current_capital * 0.15  # 总风险不超过15%
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
        """生成交易信号 - 仅基于量价关系"""
        logger.info(f"开始为股票 {symbol} 生成底部反转信号（仅基于量价关系）")
        signals = []
        
        logger.debug(f"数据总长度: {len(data)}")
        for i in range(60, len(data)):
            current_time = data.index[i]
            current_price = data.iloc[i]['close']
            logger.debug(f"\n检查数据点 {i} - 时间: {current_time}, 价格: {current_price:.2f}")
            
            # 检查是否有持仓
            if symbol in self.positions:
                position = self.positions[symbol]
                logger.debug(f"持有仓位 - 数量: {position.quantity}, 入场价: {position.entry_price:.2f}")
                should_exit, reason = self.check_exit_conditions(data, i, position)
                
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
                    if self.check_entry_conditions(data, i):
                        # 计算止损位（底部价格的8%止损）
                        stop_loss = current_price * 0.92
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
                                confidence=0.85,
                                timestamp=current_time,
                                reason="底部反转入场信号（仅量价关系）"
                            ))
                            
                            self.positions[symbol] = Position(
                                symbol=symbol,
                                entry_price=current_price,
                                quantity=quantity,
                                entry_date=i,  # 使用索引作为入场日期
                                stop_loss=stop_loss,
                                take_profit=current_price * 1.3  # 30%止盈目标
                            )
        
        logger.info(f"信号生成完成 - 股票: {symbol}, 生成信号数: {len(signals)}")
        return signals

# 使用示例
if __name__ == "__main__":
    strategy = BottomReversalStrategy(initial_capital=100000)
    
    # 示例数据结构
    # data = pd.DataFrame({
    #     'open': [...],
    #     'high': [...], 
    #     'low': [...],
    #     'close': [...],
    #     'volume': [...]
    # }, index=pd.date_range(start='2020-01-01', periods=1000))
    
    # signals = strategy.generate_signals(data, '600969')
    # print(f"Generated {len(signals)} signals")