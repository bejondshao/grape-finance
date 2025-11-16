import sys
sys.path.insert(0, 'C:/Users/bejon/AppData/Local/Programs/Python/Python312/Lib/site-packages')

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from bson import ObjectId

from app.services.mongodb_service import MongoDBService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_stock_collections(
    code: Optional[str] = None,
    strategy: Optional[str] = None,
    operation: Optional[str] = None
):
    """Get stock collections with filtering"""
    try:
        mongo_service = MongoDBService()
        
        query = {}
        if code:
            query['code'] = {'$regex': code, '$options': 'i'}
        if strategy:
            query['strategy_name'] = {'$regex': strategy, '$options': 'i'}
        if operation:
            query['operation'] = operation
        
        collections = await mongo_service.find(
            'stock_collections',
            query,
            sort=[('added_date', -1)]
        )
        
        return {
            "status": "success",
            "data": collections,
            "total": len(collections)
        }
    except Exception as e:
        logger.error(f"Error getting stock collections: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/")
async def add_to_collection(collection_item: Dict[str, Any]):
    """Add a stock to collections"""
    try:
        mongo_service = MongoDBService()
        
        success = await mongo_service.insert_one('stock_collections', collection_item)
        if success:
            return {"status": "success", "message": "Stock added to collection"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add to collection")
    except Exception as e:
        logger.error(f"Error adding to collection: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{collection_id}")
async def remove_from_collection(collection_id: str):
    """Remove a stock from collections"""
    try:
        mongo_service = MongoDBService()
        
        success = await mongo_service.delete_one('stock_collections', {'_id': collection_id})
        if success:
            return {"status": "success", "message": "Stock removed from collection"}
        else:
            raise HTTPException(status_code=404, detail="Collection item not found")
    except Exception as e:
        logger.error(f"Error removing from collection: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{collection_id}")
async def update_collection(collection_id: str, updates: Dict[str, Any]):
    """Update a collection item"""
    try:
        mongo_service = MongoDBService()
        
        success = await mongo_service.update_one(
            'stock_collections',
            {'_id': collection_id},
            {'$set': updates}
        )
        if success:
            return {"status": "success", "message": "Collection updated"}
        else:
            raise HTTPException(status_code=404, detail="Collection item not found")
    except Exception as e:
        logger.error(f"Error updating collection: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/")
async def clear_all_collections():
    """Clear all stock collections"""
    try:
        mongo_service = MongoDBService()
        
        # 删除所有收藏项
        result = await mongo_service.db.stock_collections.delete_many({})
        
        return {
            "status": "success", 
            "message": f"Successfully cleared {result.deleted_count} items from collection"
        }
    except Exception as e:
        logger.error(f"Error clearing all collections: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")