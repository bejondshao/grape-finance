from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging
import json
from bson import ObjectId
from datetime import datetime, timedelta

from app.services.data_service import DataService
from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService

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
    elif code.startswith('3') or code.startswith('0') or code.startswith('1'):
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
        collection_name = mongo_service.get_collection_name(code)
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
    limit: int = Query(3000, description="返回数据条数"),
    fields: Optional[str] = Query(None, description="返回字段，逗号分隔")
):
    logger.info(f"{code}")

    """Get daily data for a specific stock"""
    try:
        mongo_service = MongoDBService()
        if code.isdigit():
            code = get_market_and_code(code)

        collection_name = mongo_service.get_collection_name(code)
        query = {'code': code}
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                # Convert start_date string to datetime object
                query['date']['$gte'] = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                # Convert end_date string to datetime object and include the entire day
                end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_date_dt = end_date_dt.replace(hour=23, minute=59, second=59)
                query['date']['$lte'] = end_date_dt
        
        # Handle field projection
        projection = None
        if fields:
            field_list = fields.split(',')
            projection = {field.strip(): 1 for field in field_list}
            projection['_id'] = 0  # Exclude _id by default

        data = await mongo_service.find(
            collection_name,
            query,
            projection=projection,
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

@router.get("/{code}/integrated-data")
async def get_stock_integrated_data(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(3000, description="返回数据条数"),
    fields: Optional[str] = Query(None, description="返回字段，逗号分隔")
):
    """获取整合的股票数据，包括日线数据和技术指标"""
    try:
        mongo_service = MongoDBService()
        technical_service = TechnicalAnalysisService()
        
        if code.isdigit():
            code = get_market_and_code(code)

        # 获取股票基本信息
        stock_info = await mongo_service.find_one('stock_info', {'code': code})
        stock_name = stock_info.get('code_name', '') if stock_info else ''

        # 获取股票日线数据
        collection_name = mongo_service.get_collection_name(code)
        query = {'code': code}
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                query['date']['$gte'] = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_date_dt = end_date_dt.replace(hour=23, minute=59, second=59)
                query['date']['$lte'] = end_date_dt

        # 处理字段投影
        projection = None
        if fields:
            field_list = fields.split(',')
            projection = {field.strip(): 1 for field in field_list}
            projection['_id'] = 0  # Exclude _id by default

        # 获取日线数据
        daily_data = await mongo_service.find(
            collection_name,
            query,
            projection=projection,
            sort=[('date', -1)],
            limit=limit
        )

        # 获取技术指标数据
        technical_collection_name = f"technical_{code}"
        technical_query = {'code': code}
        if start_date or end_date:
            technical_query['date'] = {}
            if start_date:
                technical_query['date']['$gte'] = start_date
            if end_date:
                technical_query['date']['$lte'] = end_date

        technical_data = await mongo_service.find(
            technical_collection_name,
            technical_query,
            sort=[('date', -1)]
        )

        # 整合数据
        # 创建技术指标映射
        technical_map = {}
        for item in technical_data:
            if 'date' in item:
                if isinstance(item['date'], str):
                    # 使用日期字符串作为键
                    date_key = item['date'].split('T')[0]
                elif isinstance(item['date'], datetime):
                    # 使用日期对象作为键
                    date_key = item['date'].strftime('%Y-%m-%d')
                else:
                    continue
                    
                technical_map[date_key] = item

        # 合并数据
        integrated_data = []
        for daily_item in daily_data:
            if 'date' in daily_item:
                if isinstance(daily_item['date'], datetime):
                    date_key = daily_item['date'].strftime('%Y-%m-%d')
                elif isinstance(daily_item['date'], str):
                    date_key = daily_item['date'].split('T')[0]
                else:
                    integrated_data.append(daily_item)
                    continue
                
                # 获取对应的技术指标数据
                technical_item = technical_map.get(date_key, {})
                
                # 合并数据，确保技术指标字段也被包含
                integrated_item = {**daily_item}
                if 'cci' in technical_item:
                    integrated_item['cci'] = technical_item['cci']
                
                integrated_data.append(integrated_item)

        return {
            "code": code,
            "name": stock_name,
            "data": integrated_data,
            "total": len(integrated_data)
        }
    except Exception as e:
        logger.error(f"Error getting integrated data for {code}: {str(e)}")
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