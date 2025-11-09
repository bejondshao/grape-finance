from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.services.data_service import DataService
from app.services.mongodb_service import MongoDBService
from app.routers import stocks, technical_analysis, trading_strategies, config, stock_collections, trading_records
from app.config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

    # Start data service if scheduler is enabled
    if settings.scheduler_enabled:
        data_service = DataService()
        await data_service.startup_job()
    else:
        logger.info("Scheduler is disabled - manual data fetch required")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name} Application")


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