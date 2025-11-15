from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging

from app.services.mongodb_service import MongoDBService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_configurations(
    category: Optional[str] = None,
    sub_category: Optional[str] = None
):
    """Get system configurations"""
    try:
        mongo_service = MongoDBService()
        
        query = {}
        if category:
            query['category'] = category
        if sub_category:
            query['sub_category'] = sub_category
        
        configs = await mongo_service.find('configuration', query, sort=[('category', 1), ('sub_category', 1), ('key', 1)])
        
        return {
            "configs": configs,
            "total": len(configs)
        }
    except Exception as e:
        logger.error(f"Error getting configurations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/")
async def create_configuration(config_create: Dict[str, Any]):
    """Create a new configuration value"""
    try:
        mongo_service = MongoDBService()
        
        category = config_create.get('category')
        sub_category = config_create.get('sub_category')
        key = config_create.get('key')
        value = config_create.get('value')
        description = config_create.get('description', '')
        
        if not all([category, sub_category, key, value]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        success = await mongo_service.set_config_value(category, sub_category, key, value, description)
        if success:
            return {"status": "success", "message": "Configuration created"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create configuration")
    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/")
async def update_configuration(config_update: Dict[str, Any]):
    """Update a configuration value"""
    try:
        mongo_service = MongoDBService()
        
        category = config_update.get('category')
        sub_category = config_update.get('sub_category')
        key = config_update.get('key')
        value = config_update.get('value')
        description = config_update.get('description', '')
        
        if not all([category, sub_category, key, value]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        success = await mongo_service.set_config_value(category, sub_category, key, value, description)
        if success:
            return {"status": "success", "message": "Configuration updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")