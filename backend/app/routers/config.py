from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging

from app.services.mongodb_service import MongoDBService
from app.models.config import Configuration, ConfigurationCreate, ConfigurationUpdate, SchedulerTimingConfig

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=Dict[str, Any])
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

@router.post("/", response_model=Dict[str, Any])
async def create_configuration(config_create: ConfigurationCreate):
    """Create a new configuration value"""
    try:
        mongo_service = MongoDBService()
        
        success = await mongo_service.set_config_value(
            config_create.category, 
            config_create.sub_category, 
            config_create.key, 
            config_create.value, 
            config_create.description
        )
        if success:
            return {"status": "success", "message": "Configuration created"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create configuration")
    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/", response_model=Dict[str, Any])
async def update_configuration(config_update: ConfigurationUpdate):
    """Update a configuration value"""
    try:
        mongo_service = MongoDBService()
        
        success = await mongo_service.set_config_value(
            config_update.category, 
            config_update.sub_category, 
            config_update.key, 
            config_update.value, 
            config_update.description
        )
        if success:
            return {"status": "success", "message": "Configuration updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/scheduler/timing", response_model=Dict[str, Any])
async def update_scheduler_timing(config: SchedulerTimingConfig):
    """Update scheduler timing configurations"""
    try:
        mongo_service = MongoDBService()
        
        # Update stock list fetch cron expression
        if config.stock_list_fetch_cron:
            await mongo_service.set_config_value(
                "scheduler", 
                "timing", 
                "stock_list_fetch_cron", 
                config.stock_list_fetch_cron,
                "Cron expression for stock list fetching"
            )
        
        # Update stock history fetch cron expression
        if config.stock_history_fetch_cron:
            await mongo_service.set_config_value(
                "scheduler", 
                "timing", 
                "stock_history_fetch_cron", 
                config.stock_history_fetch_cron,
                "Cron expression for stock history fetching"
            )
            
        return {"status": "success", "message": "Scheduler timing updated"}
    except Exception as e:
        logger.error(f"Error updating scheduler timing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")