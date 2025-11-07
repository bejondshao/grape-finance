from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging

from app.services.data_service import DataService
from app.services.mongodb_service import MongoDBService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    code: Optional[str] = None,
    name: Optional[str] = None,
    type: Optional[str] = None
):
    """Get stock list with filtering"""
    try:
        mongo_service = MongoDBService()
        
        query = {}
        if code:
            query['code'] = {'$regex': code, '$options': 'i'}
        if name:
            query['code_name'] = {'$regex': name, '$options': 'i'}
        if type:
            query['type'] = type
        
        stocks = await mongo_service.find(
            'stock_info',
            query,
            sort=[('code', 1)],
            skip=skip,
            limit=limit
        )
        
        total = len(await mongo_service.find('stock_info', query))
        
        return {
            "stocks": stocks,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting stocks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{stock_code}/daily")
async def get_stock_daily_data(
    stock_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get daily data for a specific stock"""
    try:
        mongo_service = MongoDBService()
        collection_name = f"stock_daily_{stock_code.replace('.', '_')}"
        
        query = {'code': stock_code}
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                query['date']['$gte'] = start_date
            if end_date:
                query['date']['$lte'] = end_date
        
        data = await mongo_service.find(
            collection_name,
            query,
            sort=[('date', -1)],
            skip=skip,
            limit=limit
        )
        
        return {
            "stock_code": stock_code,
            "data": data,
            "total": len(data)
        }
    except Exception as e:
        logger.error(f"Error getting daily data for {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/trigger-fetch")
async def trigger_data_fetch():
    """Manually trigger data fetch"""
    try:
        data_service = DataService()
        result = await data_service.trigger_immediate_fetch()
        return result
    except Exception as e:
        logger.error(f"Error triggering data fetch: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
