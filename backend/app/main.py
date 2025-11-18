import os
import logging
import sys
import datetime
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.services.data_service import DataService
from app.services.mongodb_service import MongoDBService
from app.routers import stocks, technical_analysis, trading_strategies, config, stock_collections, trading_records
from app.config.settings import Settings

# 在任何其他导入之前配置日志系统
# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

# 配置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console handler - 使用UTF-8编码
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 创建带日期的文件名，格式为 grape_finance-YYYY-MM-DD.log
current_date = datetime.datetime.now().strftime('%Y-%m-%d')
log_filename = os.path.join(log_dir, f"grape_finance-{current_date}.log")

# File handler with UTF-8 encoding
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

# 获取logger
logger = logging.getLogger(__name__)
logger.info("日志系统初始化完成")

# 确保所有子模块使用相同的日志配置
logging.getLogger('app').setLevel(logging.INFO)
logging.getLogger('app.strategies').setLevel(logging.INFO)
logging.getLogger('app.routers').setLevel(logging.INFO)
logging.getLogger('app.services').setLevel(logging.INFO)

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.app_name} Application - Version {settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"MongoDB URL: {settings.mongodb_url}")

    # Initialize MongoDB indexes
    mongo_service = MongoDBService()
    await mongo_service.initialize_indexes()

    # Initialize configuration
    await mongo_service.initialize_configurations()
    
    # Initialize default scheduler timing configurations
    await _initialize_scheduler_configs(mongo_service)

    # Start data service if scheduler is enabled
    if settings.scheduler_enabled:
        data_service = DataService()
        await data_service.startup_job()
    else:
        logger.info("Scheduler is disabled - manual data fetch required")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name} Application")


async def _initialize_scheduler_configs(mongo_service: MongoDBService):
    """Initialize default scheduler timing configurations"""
    # Set default stock list fetch cron expression
    await mongo_service.set_config_value(
        "scheduler",
        "timing", 
        "stock_list_fetch_cron",
        settings.stock_list_fetch_cron,
        "Cron expression for stock list fetching (minute hour day month day_of_week)"
    )
    
    # Set default stock history fetch cron expression
    await mongo_service.set_config_value(
        "scheduler",
        "timing",
        "stock_history_fetch_cron", 
        settings.stock_history_fetch_cron,
        "Cron expression for stock history fetching (minute hour day month day_of_week)"
    )


app = FastAPI(
    title=settings.app_name,
    description="Comprehensive stock analysis and trading system",
    version=settings.app_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=settings.cors_origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(technical_analysis.router, prefix="/api/technical", tags=["technical-analysis"])
app.include_router(trading_strategies.router, prefix="/api/trading-strategies", tags=["trading-strategies"])
app.include_router(stock_collections.router, prefix="/api/collections", tags=["stock-collections"])
app.include_router(trading_records.router, prefix="/api/trading-records", tags=["trading-records"])
app.include_router(config.router, prefix="/api/config", tags=["configuration"])


@app.get("/")
async def root():
    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/config")
async def get_config():
    """Get current application configuration (without sensitive data)"""
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "app_env": settings.app_env,
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "scheduler_enabled": settings.scheduler_enabled,
        # "cors_origins": settings.cors_origins
        "cors_origins": ["*"]
    }