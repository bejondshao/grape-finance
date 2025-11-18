from pydantic import BaseModel
from typing import Optional, Dict, Any


class Configuration(BaseModel):
    """系统配置模型"""
    category: str
    sub_category: str
    key: str
    value: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConfigurationCreate(BaseModel):
    """创建配置请求模型"""
    category: str
    sub_category: str
    key: str
    value: str
    description: Optional[str] = None


class ConfigurationUpdate(BaseModel):
    """更新配置请求模型"""
    category: str
    sub_category: str
    key: str
    value: str
    description: Optional[str] = None


class SchedulerTimingConfig(BaseModel):
    """调度器时间配置模型"""
    stock_list_fetch_cron: Optional[str] = None
    stock_history_fetch_cron: Optional[str] = None