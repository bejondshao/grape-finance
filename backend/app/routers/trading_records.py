from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.services.mongodb_service import MongoDBService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_trading_records(
    account: Optional[str] = None,
    code: Optional[str] = None,
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get trading records with filtering"""
    try:
        mongo_service = MongoDBService()
        
        query = {}
        if account:
            query['account'] = {'$regex': account, '$options': 'i'}
        if code:
            query['code'] = {'$regex': code, '$options': 'i'}
        if type:
            query['type'] = type
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                query['date']['$gte'] = start_date
            if end_date:
                query['date']['$lte'] = end_date
        
        records = await mongo_service.find(
            'trading_records',
            query,
            sort=[('date', -1), ('time', -1)]
        )
        
        return {
            "records": records,
            "total": len(records)
        }
    except Exception as e:
        logger.error(f"Error getting trading records: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/")
async def create_trading_record(record: Dict[str, Any]):
    """Create a new trading record"""
    try:
        mongo_service = MongoDBService()
        record['created_at'] = datetime.utcnow()
        
        success = await mongo_service.insert_one('trading_records', record)
        if success:
            return {"status": "success", "message": "Trading record created"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create trading record")
    except Exception as e:
        logger.error(f"Error creating trading record: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{record_id}")
async def update_trading_record(record_id: str, record: Dict[str, Any]):
    """Update a trading record"""
    try:
        mongo_service = MongoDBService()
        record['updated_at'] = datetime.utcnow()
        
        success = await mongo_service.update_one(
            'trading_records',
            {'_id': record_id},
            {'$set': record}
        )
        if success:
            return {"status": "success", "message": "Trading record updated"}
        else:
            raise HTTPException(status_code=404, detail="Trading record not found")
    except Exception as e:
        logger.error(f"Error updating trading record: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{record_id}")
async def delete_trading_record(record_id: str):
    """Delete a trading record"""
    try:
        mongo_service = MongoDBService()
        success = await mongo_service.delete_one('trading_records', {'_id': record_id})
        if success:
            return {"status": "success", "message": "Trading record deleted"}
        else:
            raise HTTPException(status_code=404, detail="Trading record not found")
    except Exception as e:
        logger.error(f"Error deleting trading record: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
