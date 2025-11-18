from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class StockInfo(BaseModel):
    """股票基本信息模型"""
    code: str
    ts_code: Optional[str] = None
    symbol: Optional[str] = None
    code_name: Optional[str] = None
    name: Optional[str] = None
    area: Optional[str] = None
    industry: Optional[str] = None
    fullname: Optional[str] = None
    enname: Optional[str] = None
    cnspell: Optional[str] = None
    market: Optional[str] = None
    exchange: Optional[str] = None
    curr_type: Optional[str] = None
    list_status: Optional[str] = None
    list_date: Optional[str] = None
    delist_date: Optional[str] = None
    is_hs: Optional[str] = None
    act_name: Optional[str] = None
    act_ent_type: Optional[str] = None
    updateTime: Optional[datetime] = None


class StockDailyData(BaseModel):
    """股票日线数据模型"""
    code: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    preclose: float
    volume: float
    amount: float
    adjustflag: Optional[str] = None
    turn: Optional[float] = None
    tradestatus: Optional[int] = None
    pctChg: Optional[float] = None
    peTTM: Optional[float] = None
    pbMRQ: Optional[float] = None
    psTTM: Optional[float] = None
    pcfNcfTTM: Optional[float] = None
    isST: Optional[int] = None
    updated_at: Optional[datetime] = None


class TechnicalIndicator(BaseModel):
    """技术指标数据模型"""
    code: str
    date: datetime
    cci: Optional[float] = None
    cci_period: Optional[int] = None
    cci_constant: Optional[float] = None
    rsi: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    kdj_k: Optional[float] = None
    kdj_d: Optional[float] = None
    kdj_j: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    updated_at: Optional[datetime] = None


class StockCollection(BaseModel):
    """股票集合模型"""
    code: str
    name: Optional[str] = None
    strategy_id: str
    strategy_name: str
    operation: str
    price: float
    share_amount: int
    meet_date: datetime
    added_date: datetime


class TradingRecord(BaseModel):
    """交易记录模型"""
    code: str
    name: Optional[str] = None
    date: datetime
    action: str  # 'BUY', 'SELL'
    price: float
    volume: int
    amount: float
    fee: float
    profit: Optional[float] = None
    created_at: Optional[datetime] = None