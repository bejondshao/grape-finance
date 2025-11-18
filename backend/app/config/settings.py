from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "Grape Finance"
    app_version: str = "1.0.0"
    app_env: str = "development"

    # Database
    mongodb_url: str = "mongodb://localhost:27017/grape_finance"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # CORS
    cors_origins: str = "http://localhost:3000"

    # BaoStock
    baostock_username: str = ""
    baostock_password: str = ""

    # Scheduler
    scheduler_enabled: bool = True
    data_fetch_start_date: str = "1990-12-19"
    sleep_timer: float = 1.0
    
    # Scheduler times for different tasks
    stock_list_fetch_cron: str = "00 20 * * 1"  # Every Monday at 20:00
    stock_history_fetch_cron: str = "04 20 * * *"  # Every day at 20:32

    # Trading
    stamp_duty_rate: float = 0.0005
    trading_fee_rate: float = 0.0003

    # Technical Analysis
    cci_default_period: int = 14
    cci_default_constant: float = 0.015

    # Logging
    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()