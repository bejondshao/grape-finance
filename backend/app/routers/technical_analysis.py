from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis import TechnicalAnalysisService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/indicators")
async def get_technical_indicators(
    stock_code: str,
    indicator_type: str = Query(..., description="Technical indicator type (e.g., CCI)"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get technical indicators for a stock"""
    try:
        mongo_service = MongoDBService()
        collection_name = f"technical_{stock_code.replace('.', '_')}"
        
        query = {'code': stock_code}
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                query['date']['$gte'] = start_date
            if end_date:
                query['date']['$lte'] = end_date
        
        indicators = await mongo_service.find(
            collection_name,
            query,
            sort=[('date', -1)]
        )
        
        return {
            "stock_code": stock_code,
            "indicator_type": indicator_type,
            "indicators": indicators
        }
    except Exception as e:
        logger.error(f"Error getting technical indicators for {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/config")
async def create_technical_config(config: Dict[str, Any]):
    """Create technical analysis configuration"""
    try:
        mongo_service = MongoDBService()
        config['created_at'] = datetime.utcnow()
        
        success = await mongo_service.insert_one('technical_analysis_config', config)
        if success:
            return {"status": "success", "message": "Configuration created"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create configuration")
    except Exception as e:
        logger.error(f"Error creating technical config: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
