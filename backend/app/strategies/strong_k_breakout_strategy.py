import numpy as np
import pandas as pd
import talib
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class MarketSignal:
    """市场信号数据类"""
    signal_type: str  # 'bottom_support', 'left_peak', 'volume_first', 'strong_k', 'buy', 'sell'
    price: float
    volume: float
    timestamp: datetime
    confidence: float
    description: str

@dataclass
class StrongKSignal:
    """强K信号数据类"""
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    stop_loss: float
    target_price: float
    timestamp: datetime
    confidence: float
    stage: str  # 当前所处阶段
    reason: str

class StrongKBreakoutStrategy:
    """强K突围模式策略实现"""
    
    def __init__(self, 
                 initial_capital: float = 100000,
                 max_position_pct: float = 0.03,
                 max_positions: int = 3):
        """
        强K突围策略初始化
        
        Args:
            initial_capital: 初始资金
            max_position_pct: 单笔交易最大风险比例
            max_positions: 最大持仓数量
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_pct = max_position_pct
        self.max_positions = max_positions
        self.positions: Dict[str, Dict] = {}
        
        # 策略状态跟踪
        self.market_stages: Dict[str, str] = {}  # 'bottom', 'accumulation', 'left_peak', 'volume_first', 'strong_k', 'rally'
        self.left_peaks: Dict[str, Dict] = {}  # 记录左峰信息
        self.volume_first_signals: Dict[str, Dict] = {}  # 记录量在价先信号
        
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        try:
            # 基础移动平均线
            df['MA5'] = talib.SMA(df['close'], timeperiod=5)
            df['MA10'] = talib.SMA(df['close'], timeperiod=10)
            df['MA20'] = talib.SMA(df['close'], timeperiod=20)
            df['MA60'] = talib.SMA(df['close'], timeperiod=60)
            
            # 成交量指标
            df['volume_ma5'] = df['volume'].rolling(window=5).mean()
            df['volume_ma10'] = df['volume'].rolling(window=10).mean()
            df['volume_ma20'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma20']
            
            # RSI
            df['RSI'] = talib.RSI(df['close'], timeperiod=14)
            
            # MACD
            df['MACD_DIF'], df['MACD_SIGNAL'], df['MACD_HIST'] = talib.MACD(
                df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
            
            # 布林带
            df['BB_UPPER'], df['BB_MIDDLE'], df['BB_LOWER'] = talib.BBANDS(
                df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
            
            # 价格位置指标
            df['price_position'] = (df['close'] - df['low'].rolling(20).min()) / \
                                  (df['high'].rolling(20).max() - df['low'].rolling(20).min())
            
            # K线形态
            df['body_size'] = abs(df['close'] - df['open']) / df['open']
            df['upper_shadow'] = df['high'] - df[['close', 'open']].max(axis=1)
            df['lower_shadow'] = df[['close', 'open']].min(axis=1) - df['low']
            # 避免除零错误
            df['shadow_ratio'] = np.where(df['body_size'] != 0, (df['upper_shadow'] + df['lower_shadow']) / df['body_size'], 0)
        except Exception as e:
            print(f"Error calculating technical indicators: {str(e)}")
            raise e
        
        return df
    
    def identify_bottom_support(self, df: pd.DataFrame, current_idx: int) -> Optional[MarketSignal]:
        """识别底部资金承接信号"""
        if current_idx < 30:
            print("底部资金承接信号检查 - 数据不足，索引小于30")
            return None
            
        current = df.iloc[current_idx]
        prev_5 = df.iloc[current_idx-5:current_idx]
        prev_20 = df.iloc[current_idx-20:current_idx]
        
        # 1. 长期下跌判断
        price_decline = (df.iloc[current_idx-20]['close'] - current['close']) / df.iloc[current_idx-20]['close']
        price_decline_condition = price_decline >= 0.15  # 下跌幅度至少15%（稍微宽松一些）
        
        # 2. 恐慌性长阴识别（最近5日内）
        panic_long_shadow = False
        panic_candle_details = []
        for i in range(len(prev_5)):
            candle = prev_5.iloc[i]
            body_size_check = candle['body_size'] > 0.03  # 实体较大
            bearish_check = candle['close'] < candle['open']  # 阴线
            lower_shadow_check = candle['lower_shadow'] > candle['body_size'] * 0.3  # 稍微宽松的长下影要求
            
            panic_candle_details.append({
                'index': current_idx-5+i,
                'body_size': candle['body_size'],
                'body_size_check': body_size_check,
                'bearish_check': bearish_check,
                'lower_shadow_ratio': candle['lower_shadow'] / candle['body_size'] if candle['body_size'] > 0 else 0,
                'lower_shadow_check': lower_shadow_check
            })
            
            if body_size_check and bearish_check and lower_shadow_check:
                panic_long_shadow = True
                break
        
        # 3. 资金承接信号（带长下影的阳线）
        bullish_candle = current['close'] > current['open']  # 阳线
        long_lower_shadow = current['lower_shadow'] > current['body_size'] * 0.3  # 稍微宽松的长下影要求
        high_volume = current['volume_ratio'] > 1.0  # 稍微宽松的放量要求
        oversold = current['RSI'] < 35  # 稍微宽松的超卖区域
        support_signal = bullish_candle and long_lower_shadow and high_volume and oversold
        
        # 记录详细日志
        print(f"底部资金承接信号检查:")
        print(f"  - 价格下跌幅度: {price_decline:.2%} (要求≥15%: {price_decline_condition})")
        print(f"  - 恐慌长阴详情:")
        for detail in panic_candle_details:
            print(f"    [{detail['index']}] 实体:{detail['body_size']:.4f}(>{0.03}:{detail['body_size_check']}) "
                  f"阴线:{detail['bearish_check']} 下影比:{detail['lower_shadow_ratio']:.2f}(>0.3:{detail['lower_shadow_check']})")
        print(f"  - 资金承接信号详情:")
        print(f"    阳线: {bullish_candle}, 长下影: {long_lower_shadow}, 放量: {high_volume}({current['volume_ratio']:.2f}>1.0), "
              f"超卖: {oversold}({current['RSI']:.1f}<35)")
        print(f"  - 最终结果: {'符合' if (price_decline_condition and panic_long_shadow and support_signal) else '不符合'}")
        
        if price_decline_condition and panic_long_shadow and support_signal:
            return MarketSignal(
                signal_type='bottom_support',
                price=current['close'],
                volume=current['volume'],
                timestamp=df.index[current_idx],
                confidence=0.7,
                description="底部资金承接信号：恐慌长阴后的长下影阳线"
            )
        
        return None
    
    def identify_accumulation_stage(self, df: pd.DataFrame, current_idx: int) -> bool:
        """识别主力吸筹阶段"""
        if current_idx < 20:
            print("主力吸筹阶段检查 - 数据不足，索引小于20")
            return False
            
        current = df.iloc[current_idx]
        recent_10 = df.iloc[current_idx-10:current_idx]
        
        # 小连阳拉升特征
        consecutive_rising_days = 0
        rising_details = []
        for i in range(len(recent_10)):
            candle = recent_10.iloc[i]
            is_rising = candle['close'] > candle['open']
            if is_rising:
                consecutive_rising_days += 1
            else:
                consecutive_rising_days = 0
                
            rising_details.append({
                'index': current_idx-10+i,
                'close': candle['close'],
                'open': candle['open'],
                'is_rising': is_rising,
                'consecutive_count': consecutive_rising_days
            })
        
        # 量能无大幅异动
        max_volume_ratio = recent_10['volume_ratio'].max()
        volume_stable = max_volume_ratio < 2.5  # 稍微宽松的量能要求
        
        # 记录详细日志
        print(f"主力吸筹阶段检查:")
        print(f"  - 连续阳线详情:")
        for detail in rising_details:
            print(f"    [{detail['index']}] 收盘:{detail['close']:.2f} 开盘:{detail['open']:.2f} "
                  f"上涨:{detail['is_rising']} 连续计数:{detail['consecutive_count']}")
        print(f"  - 量能情况: 最大成交量倍数={max_volume_ratio:.2f} (要求<2.5: {volume_stable})")
        print(f"  - 最终结果: {'符合' if (consecutive_rising_days >= 3 and volume_stable) else '不符合'} "  # 降低连续阳线要求
              f"(连续阳线天数: {consecutive_rising_days}≥3)")
        
        return consecutive_rising_days >= 3 and volume_stable  # 降低连续阳线要求
    
    def identify_left_peak(self, df: pd.DataFrame, current_idx: int, symbol: str) -> Optional[MarketSignal]:
        """识别左峰形成"""
        if current_idx < 30:
            print("左峰形成检查 - 数据不足，索引小于30")
            return None
            
        current = df.iloc[current_idx]
        recent_20 = df.iloc[current_idx-20:current_idx]
        
        # 寻找阶段性高点
        peak_idx = recent_20['high'].idxmax()
        peak_data = df.loc[peak_idx]
        
        # 检查是否为有效左峰
        peak_position = df.index.get_loc(peak_idx)
        
        # 左峰后出现回调
        after_peak = df.iloc[peak_position+1:current_idx+1]
        if len(after_peak) < 3:  # 降低数据要求
            print(f"左峰形成检查 - 峰后数据不足: {len(after_peak)} < 3")
            return None
            
        max_decline = (peak_data['high'] - after_peak['low'].min()) / peak_data['high']
        decline_condition = max_decline > 0.08  # 降低回调要求到8%
        
        # 记录详细日志
        print(f"左峰形成检查:")
        print(f"  - 左峰信息: 价格={peak_data['high']:.2f}, 位置={peak_idx}")
        print(f"  - 回调信息: 最低价格={after_peak['low'].min():.2f}, 回调幅度={max_decline:.2%} (要求>8%: {decline_condition})")
        print(f"  - 最终结果: {'符合' if decline_condition else '不符合'}")
        
        if decline_condition:
            left_peak_info = {
                'price': peak_data['high'],
                'volume': peak_data['volume'],
                'date': peak_idx,
                'decline_pct': max_decline
            }
            
            self.left_peaks[symbol] = left_peak_info
            
            return MarketSignal(
                signal_type='left_peak',
                price=peak_data['high'],
                volume=peak_data['volume'],
                timestamp=peak_idx,
                confidence=0.8,
                description=f"左峰形成：高点{peak_data['high']:.2f}，回调{max_decline:.2%}"
            )
        
        return None
    
    def identify_volume_first_signal(self, df: pd.DataFrame, current_idx: int, symbol: str) -> Optional[MarketSignal]:
        """识别量在价先前置条件"""
        if symbol not in self.left_peaks or current_idx < 10:
            print(f"量在价先检查 - 缺少左峰信息: {symbol in self.left_peaks}, 数据索引: {current_idx}")
            return None
            
        current = df.iloc[current_idx]
        left_peak = self.left_peaks[symbol]
        
        # 1. 放量长阳线
        high_volume_condition = current['volume_ratio'] > 1.5  # 降低倍量要求到1.5倍
        bullish_candle_condition = current['close'] > current['open']  # 阳线
        large_body_condition = current['body_size'] > 0.015  # 稍微降低实体要求
        volume_breakout = high_volume_condition and bullish_candle_condition and large_body_condition
        
        # 2. 价格未突破左峰，但量能突破
        price_below_peak = current['close'] < left_peak['price']
        volume_above_peak = current['volume'] > left_peak['volume']
        
        # 记录详细日志
        print(f"量在价先检查:")
        print(f"  - 成交量倍数: {current['volume_ratio']:.2f} (要求>1.5: {high_volume_condition})")
        print(f"  - 阳线条件: 收盘={current['close']:.2f} > 开盘={current['open']:.2f} ({bullish_candle_condition})")
        print(f"  - 实体大小: {current['body_size']:.2%} (要求>1.5%: {large_body_condition})")
        print(f"  - 价格条件: 当前价格={current['close']:.2f} < 左峰价格={left_peak['price']:.2f} ({price_below_peak})")
        print(f"  - 量能条件: 当前成交量={current['volume']:.0f} > 左峰成交量={left_peak['volume']:.0f} ({volume_above_peak})")
        print(f"  - 最终结果: {'符合' if (volume_breakout and price_below_peak and volume_above_peak) else '不符合'}")
        
        if volume_breakout and price_below_peak and volume_above_peak:
            volume_first_info = {
                'price': current['close'],
                'volume': current['volume'],
                'date': df.index[current_idx],
                'left_peak_price': left_peak['price']
            }
            
            self.volume_first_signals[symbol] = volume_first_info
            
            return MarketSignal(
                signal_type='volume_first',
                price=current['close'],
                volume=current['volume'],
                timestamp=df.index[current_idx],
                confidence=0.85,
                description="量在价先：量能突破左峰但价格未突破"
            )
        
        return None
    
    def identify_strong_k_signal(self, df: pd.DataFrame, current_idx: int, symbol: str) -> Optional[StrongKSignal]:
        """识别强K信号（右侧交易起点）"""
        if (symbol not in self.left_peaks or 
            symbol not in self.volume_first_signals or 
            current_idx < 5):
            print(f"强K信号检查 - 缺少必要条件: 左峰={symbol in self.left_peaks}, 量在价先={symbol in self.volume_first_signals}, 索引={current_idx}")
            return None
            
        current = df.iloc[current_idx]
        left_peak = self.left_peaks[symbol]
        volume_first = self.volume_first_signals[symbol]
        
        # 1. 倍量甚至天量阳线
        volume_multiplier = current['volume'] / df['volume_ma20'].iloc[current_idx]
        strong_volume = volume_multiplier >= 1.5  # 降低倍量要求到1.5倍
        
        # 2. 价格突破左峰高点
        price_breakout = current['close'] > left_peak['price']
        
        # 3. 突破试盘高点（如果有）
        test_high = volume_first['left_peak_price'] * 0.95  # 降低试盘高点要求
        price_strong_breakout = current['close'] > test_high
        
        # 4. 技术确认
        ma_support = current['close'] > current['MA20']
        macd_confirm = current['MACD_DIF'] > current['MACD_SIGNAL']
        
        # 记录详细日志
        print(f"强K信号检查:")
        print(f"  - 成交量倍数: {volume_multiplier:.2f} (要求≥1.5: {strong_volume})")
        print(f"  - 价格突破左峰: {price_breakout} (当前价格: {current['close']:.2f}, 左峰: {left_peak['price']:.2f})")
        print(f"  - 突破试盘高点: {price_strong_breakout} (试盘高点: {test_high:.2f})")
        print(f"  - 均线支撑: {ma_support} (收盘价: {current['close']:.2f} > MA20: {current['MA20']:.2f})")
        print(f"  - MACD确认: {macd_confirm} (DIF: {current['MACD_DIF']:.4f} > SIGNAL: {current['MACD_SIGNAL']:.4f})")
        print(f"  - 最终结果: {'符合' if (strong_volume and price_breakout and price_strong_breakout and ma_support) else '不符合'}")
        
        # 不再要求MACD确认，降低要求
        if (strong_volume and price_breakout and price_strong_breakout and ma_support):
            
            # 计算止损位（强K底部）
            stop_loss = current['low']
            
            # 计算目标位（基于强K幅度）
            k_amplitude = (current['close'] - current['open']) / current['open']
            target_price = current['close'] * (1 + k_amplitude * 3)  # 3倍强K幅度
            
            print(f"生成强K信号 - 止损: {stop_loss:.2f}, 目标价: {target_price:.2f}, K线幅度: {k_amplitude:.2%}")
            
            return StrongKSignal(
                symbol=symbol,
                action='BUY',
                price=current['close'],
                stop_loss=stop_loss,
                target_price=target_price,
                timestamp=df.index[current_idx],
                confidence=0.9,
                stage='strong_k',
                reason=f"强K突破：{volume_multiplier:.1f}倍量突破左峰{left_peak['price']:.2f}"
            )
        
        return None
    
    def check_exit_conditions(self, df: pd.DataFrame, current_idx: int, 
                            position: Dict) -> Tuple[bool, str]:
        """检查出场条件"""
        current = df.iloc[current_idx]
        
        # 1. 止损检查
        if current['close'] <= position['stop_loss']:
            return True, "强K止损"
        
        # 2. 移动止损（保护利润）
        if 'highest_price' in position:
            drawdown = (position['highest_price'] - current['close']) / position['highest_price']
            if drawdown > 0.15:  # 回撤15%
                return True, "移动止损"
        
        # 3. 目标位到达
        if current['close'] >= position['target_price']:
            return True, "目标止盈"
        
        # 4. 技术指标走弱
        if (current['close'] < current['MA20'] or 
            current['MACD_DIF'] < current['MACD_SIGNAL']):
            return True, "技术走弱"
        
        return False, ""
    
    def calculate_position_size(self, price: float, stop_loss: float, symbol: str = None) -> int:
        """计算仓位大小"""
        risk_per_share = abs(price - stop_loss)
        max_risk_amount = self.current_capital * self.max_position_pct
        
        if risk_per_share == 0:
            return 0
        
        # 基础仓位计算
        position_size = int(max_risk_amount / risk_per_share)
        
        # 确保不超过可用资金
        max_affordable = int(self.current_capital * 0.95 / price)
        position_size = min(position_size, max_affordable)
        
        # 考虑已有持仓的风险
        if symbol and len(self.positions) > 0:
            total_risk = sum(
                abs(pos['entry_price'] - pos['stop_loss']) * pos['quantity'] 
                for pos in self.positions.values()
            )
            
            max_total_risk = self.current_capital * 0.15  # 总风险不超过15%
            available_risk = max(0, max_total_risk - total_risk)
            
            risk_based_size = int(available_risk / risk_per_share)
            position_size = min(position_size, risk_based_size)
        
        # 强K信号可以适当增加仓位
        if symbol in self.market_stages and self.market_stages[symbol] == 'strong_k':
            position_size = int(position_size * 1.2)  # 增加20%仓位
        
        # 确保最小交易单位
        min_size = max(1, int(100 / price))
        position_size = max(min_size, position_size)
        
        return position_size
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[StrongKSignal]:
        """生成交易信号"""
        try:
            print(f"开始为股票 {symbol} 生成强K信号")
            
            # 限制数据长度以提高性能
            if len(data) > 100:
                df = self.calculate_technical_indicators(data.tail(100))
                print(f"使用最近100条数据进行分析")
            else:
                df = self.calculate_technical_indicators(data)
                print(f"使用全部 {len(data)} 条数据进行分析")
                
            signals = []
            
            # 初始化股票状态
            if symbol not in self.market_stages:
                self.market_stages[symbol] = 'watching'
                print(f"初始化股票 {symbol} 状态为 watching")
            
            # 检查所有数据点而不是只检查最近的
            # 从索引30开始（确保有足够的历史数据）
            start_idx = 30
            end_idx = len(df) - 1
            print(f"开始检查索引 {start_idx} 到 {end_idx} 的数据点")
            
            # 为每个股票重新初始化状态，以便检查多个信号点
            self.market_stages[symbol] = 'watching'
            if symbol in self.left_peaks:
                del self.left_peaks[symbol]
            if symbol in self.volume_first_signals:
                del self.volume_first_signals[symbol]
            if symbol in self.positions:
                del self.positions[symbol]
            
            for i in range(start_idx, len(df)):
                current_time = df.index[i]
                current_price = df.iloc[i]['close']
                print(f"\n检查数据点 {i} - 时间: {current_time}, 价格: {current_price:.2f}")
                
                # 更新市场阶段
                self.update_market_stage(df, i, symbol)
                
                # 检查是否有持仓
                if symbol in self.positions:
                    position = self.positions[symbol]
                    print(f"持有仓位 - 数量: {position['quantity']}, 入场价: {position['entry_price']:.2f}")
                    
                    # 更新最高价
                    if current_price > position.get('highest_price', position['entry_price']):
                        position['highest_price'] = current_price
                        print(f"更新最高价至: {current_price:.2f}")
                    
                    # 检查出场条件
                    should_exit, reason = self.check_exit_conditions(df, i, position)
                    print(f"出场条件检查 - 需要出场: {should_exit}, 原因: {reason}")
                    
                    if should_exit:
                        signals.append(StrongKSignal(
                            symbol=symbol,
                            action='SELL',
                            price=current_price,
                            stop_loss=position['stop_loss'],
                            target_price=position['target_price'],
                            timestamp=current_time,
                            confidence=1.0,
                            stage=self.market_stages[symbol],
                            reason=reason
                        ))
                        print(f"生成卖出信号 - 原因: {reason}")
                        
                        del self.positions[symbol]
                        self.market_stages[symbol] = 'watching'
                        # 重置相关状态以便寻找下一个机会
                        if symbol in self.left_peaks:
                            del self.left_peaks[symbol]
                        if symbol in self.volume_first_signals:
                            del self.volume_first_signals[symbol]
                else:
                    # 检查强K买入信号
                    if len(self.positions) < self.max_positions:
                        print(f"检查强K买入信号 - 当前持仓数: {len(self.positions)}, 最大持仓数: {self.max_positions}")
                        strong_k_signal = self.identify_strong_k_signal(df, i, symbol)
                        
                        if strong_k_signal:
                            # 计算仓位大小
                            quantity = self.calculate_position_size(
                                strong_k_signal.price, 
                                strong_k_signal.stop_loss, 
                                symbol
                            )
                            print(f"计算仓位大小 - 数量: {quantity}")
                            
                            if quantity > 0:
                                signals.append(strong_k_signal)
                                print(f"生成买入信号 - 价格: {strong_k_signal.price:.2f}, 止损: {strong_k_signal.stop_loss:.2f}")
                                
                                self.positions[symbol] = {
                                    'quantity': quantity,
                                    'entry_price': strong_k_signal.price,
                                    'stop_loss': strong_k_signal.stop_loss,
                                    'target_price': strong_k_signal.target_price,
                                    'entry_date': strong_k_signal.timestamp,
                                    'highest_price': strong_k_signal.price
                                }
                                
                                self.market_stages[symbol] = 'rally'
                                print(f"建立仓位并进入rally阶段")
                                
                                # 在生成买入信号后重置状态以寻找下一个机会
                                # 注意：这里我们不重置状态，因为可能还有上涨空间
            
            print(f"信号生成完成 - 股票: {symbol}, 生成信号数: {len(signals)}")
            return signals
        except Exception as e:
            print(f"Error generating signals for {symbol}: {str(e)}")
            raise e
    
    def update_market_stage(self, df: pd.DataFrame, current_idx: int, symbol: str):
        """更新市场阶段"""
        current_stage = self.market_stages.get(symbol, 'watching')
        print(f"更新市场阶段 - 股票: {symbol}, 当前阶段: {current_stage}")
        
        # 底部承接信号
        print(f"检查底部承接信号 - 当前阶段: {current_stage}")
        bottom_signal = self.identify_bottom_support(df, current_idx)
        if bottom_signal and current_stage == 'watching':
            self.market_stages[symbol] = 'bottom'
            print(f"进入底部阶段 - 股票: {symbol}")
            # 重置其他状态
            if symbol in self.left_peaks:
                del self.left_peaks[symbol]
            if symbol in self.volume_first_signals:
                del self.volume_first_signals[symbol]
            return
        
        # 吸筹阶段
        if current_stage == 'bottom':
            print(f"检查吸筹阶段 - 当前阶段: {current_stage}")
            accumulation_condition = self.identify_accumulation_stage(df, current_idx)
            if accumulation_condition:
                self.market_stages[symbol] = 'accumulation'
                print(f"进入吸筹阶段 - 股票: {symbol}")
        
        # 左峰形成
        print(f"检查左峰形成 - 当前阶段: {current_stage}")
        left_peak_signal = self.identify_left_peak(df, current_idx, symbol)
        if left_peak_signal and current_stage in ['accumulation', 'bottom']:
            self.market_stages[symbol] = 'left_peak'
            print(f"进入左峰阶段 - 股票: {symbol}")
        
        # 量在价先
        print(f"检查量在价先 - 当前阶段: {current_stage}")
        volume_first_signal = self.identify_volume_first_signal(df, current_idx, symbol)
        if volume_first_signal and current_stage == 'left_peak':
            self.market_stages[symbol] = 'volume_first'
            print(f"进入量在价先阶段 - 股票: {symbol}")
        
        # 强K突破后进入拉升阶段
        if current_stage == 'volume_first':
            print(f"检查强K信号 - 当前阶段: {current_stage}")
            strong_k = self.identify_strong_k_signal(df, current_idx, symbol)
            if strong_k:
                self.market_stages[symbol] = 'strong_k'
                print(f"进入强K阶段 - 股票: {symbol}")
        
        # 如果当前没有任何信号且不是在观察阶段，重置状态
        # 这样可以重新开始寻找机会
        if (not bottom_signal and not left_peak_signal and not volume_first_signal and 
            current_stage != 'watching' and current_stage != 'rally'):
            print(f"重置状态为观察阶段 - 股票: {symbol}")
            self.market_stages[symbol] = 'watching'
            if symbol in self.left_peaks:
                del self.left_peaks[symbol]
            if symbol in self.volume_first_signals:
                del self.volume_first_signals[symbol]
    
    def get_market_analysis(self, data: pd.DataFrame, symbol: str) -> Dict:
        """获取市场分析结果"""
        df = self.calculate_technical_indicators(data)
        analysis = {
            'current_stage': self.market_stages.get(symbol, 'watching'),
            'signals': [],
            'left_peak': self.left_peaks.get(symbol),
            'volume_first': self.volume_first_signals.get(symbol),
            'technical_summary': {}
        }
        
        # 技术面总结
        current = df.iloc[-1]
        analysis['technical_summary'] = {
            'price': current['close'],
            'volume_ratio': current['volume_ratio'],
            'RSI': current['RSI'],
            'MACD_signal': 'bullish' if current['MACD_DIF'] > current['MACD_SIGNAL'] else 'bearish',
            'MA_trend': 'up' if current['close'] > current['MA20'] else 'down'
        }
        
        return analysis

# 使用示例
if __name__ == "__main__":
    strategy = StrongKBreakoutStrategy(initial_capital=100000)
    
    # 示例数据结构
    # data = pd.DataFrame({
    #     'open': [...],
    #     'high': [...], 
    #     'low': [...],
    #     'close': [...],
    #     'volume': [...]
    # }, index=pd.date_range(start='2020-01-01', periods=1000))
    
    # signals = strategy.generate_signals(data, 'AAPL')
    # analysis = strategy.get_market_analysis(data, 'AAPL')
    
    # print(f"生成 {len(signals)} 个信号")
    # print(f"当前阶段: {analysis['current_stage']}")
    # print(f"技术总结: {analysis['technical_summary']}")
