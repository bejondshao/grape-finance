from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.services.data_service import DataService
from app.services.mongodb_service import MongoDBService
from app.routers import stocks, technical_analysis, trading_strategies, config, stock_collections, trading_records

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Grape Finance Application")
    
    # Initialize MongoDB indexes
    mongo_service = MongoDBService()
    await mongo_service.initialize_indexes()
    
    # Initialize configuration
    await mongo_service.initialize_configurations()
    
    # Start data service
    data_service = DataService()
    await data_service.startup_job()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Grape Finance Application")

app = FastAPI(
    title="Grape Finance API",
    description="Comprehensive stock analysis and trading system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(technical_analysis.router, prefix="/api/technical", tags=["technical-analysis"])
app.include_router(trading_strategies.router, prefix="/api/trading", tags=["trading-strategies"])
app.include_router(stock_collections.router, prefix="/api/collections", tags=["stock-collections"])
app.include_router(trading_records.router, prefix="/api/trading-records", tags=["trading-records"])
app.include_router(config.router, prefix="/api/config", tags=["configuration"])

@app.get("/")
async def root():
    return {"message": "Grape Finance API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
