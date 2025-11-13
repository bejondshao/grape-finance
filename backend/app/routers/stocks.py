from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging
import json
from bson import ObjectId
from datetime import datetime, timedelta

from app.services.data_service import DataService
from app.services.mongodb_service import MongoDBService

router = APIRouter()
logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)

def get_market_prefix(code):
    """根据股票代码确定市场前缀"""
    if code.startswith('6') or code.startswith('8'):
        return 'sh'
    elif code.startswith('3') or code.startswith('0'):
        return 'sz'
    elif code.startswith('4') or code.startswith('9'):
        return 'bj'
    else:
        return 'sh'  # 默认上海

def get_market_and_code(code):
    return get_market_prefix(code) + "." + code

@router.get("/")
async def get_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    code: Optional[str] = "sh.000300",
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
        collection_name = f"stock_daily_{code}"
        stocks = await mongo_service.find(
            collection_name,
            query,
            sort=[('code', 1)],
            #skip=skip,
            limit=limit
        )
        
        total = len(await mongo_service.find(collection_name, query))
        
        return {
            "stocks": stocks,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting stocks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{code}/daily")
async def get_stock_daily_data(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(3000, description="返回数据条数")
):
    logger.info(f"{code}")

    """Get daily data for a specific stock"""
    try:
        mongo_service = MongoDBService()
        if code.isdigit():
            code = get_market_and_code(code)

        collection_name = f"stock_daily_{code}"
        query = {'code': code}
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                query['date']['$gte'] = start_date
            if end_date:
                # 包含结束日期当天的数据
                end_date = end_date.replace(hour=23, minute=59, second=59)
                query['date']['$lte'] = end_date
        
        data = await mongo_service.find(
            collection_name,
            query,
            sort=[('date', -1)],
            limit=limit
        )
        
        return {
            "code": code,
            "data": data,
            "total": len(data)
        }
    except Exception as e:
        logger.error(f"Error getting daily data for {code}: {str(e)}")
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
