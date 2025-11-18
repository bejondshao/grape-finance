from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class StrategyParameter(BaseModel):
    """策略参数基类"""
    pass


class RightSideStrategyParameter(StrategyParameter):
    """右侧交易策略参数"""
    breakout_threshold: Optional[float] = None
    volume_threshold: Optional[float] = None
    cci_threshold: Optional[float] = None
    ma_periods: Optional[List[int]] = None
    enable_price_breakout: Optional[bool] = None
    enable_volume_check: Optional[bool] = None
    enable_cci_check: Optional[bool] = None
    enable_ma_alignment: Optional[bool] = None


class StrongKStrategyParameter(StrategyParameter):
    """强K突破策略参数"""
    initial_capital: Optional[float] = None
    max_position_pct: Optional[float] = None
    max_positions: Optional[int] = None


class BottomReversalStrategyParameter(StrategyParameter):
    """底部反转策略参数"""
    initial_capital: Optional[float] = None
    max_position_pct: Optional[float] = None
    max_positions: Optional[int] = None


class TradingStrategyBase(BaseModel):
    """交易策略基础模型"""
    name: str
    description: Optional[str] = None
    type: str
    parameters: Dict[str, Any] = {}
    operation: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TradingStrategyCreate(BaseModel):
    """创建交易策略请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    operation: Optional[str] = None
    is_active: Optional[bool] = None


class TradingStrategyUpdate(BaseModel):
    """更新交易策略请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    operation: Optional[str] = None
    is_active: Optional[bool] = None


class Signal(BaseModel):
    """交易信号模型"""
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    confidence: float
    timestamp: datetime
    reason: str
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    stage: Optional[str] = None


class Position(BaseModel):
    """持仓信息模型"""
    symbol: str
    entry_price: float
    quantity: int
    entry_date: datetime
    stop_loss: float
    take_profit: float