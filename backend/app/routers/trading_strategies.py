from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from datetime import datetime

from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.data_service import DataService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/strategies")
async def get_trading_strategies():
    """Get all trading strategies"""
    try:
        mongo_service = MongoDBService()
        strategies = await mongo_service.find('trading_strategies', {})
        return strategies
    except Exception as e:
        logger.error(f"Error getting trading strategies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/strategies")
async def create_trading_strategy(strategy: Dict[str, Any]):
    """Create a new trading strategy"""
    try:
        mongo_service = MongoDBService()
        strategy['created_at'] = datetime.utcnow()
        
        success = await mongo_service.insert_one('trading_strategies', strategy)
        if success:
            return {"status": "success", "message": "Strategy created"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create strategy")
    except Exception as e:
        logger.error(f"Error creating trading strategy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/strategies/{strategy_id}")
async def update_trading_strategy(strategy_id: str, strategy: Dict[str, Any]):
    """Update a trading strategy"""
    try:
        mongo_service = MongoDBService()
        strategy['updated_at'] = datetime.utcnow()
        
        success = await mongo_service.update_one(
            'trading_strategies',
            {'_id': strategy_id},
            {'$set': strategy}
        )
        if success:
            return {"status": "success", "message": "Strategy updated"}
        else:
            raise HTTPException(status_code=404, detail="Strategy not found")
    except Exception as e:
        logger.error(f"Error updating trading strategy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/strategies/{strategy_id}")
async def delete_trading_strategy(strategy_id: str):
    """Delete a trading strategy"""
    try:
        mongo_service = MongoDBService()
        success = await mongo_service.delete_one('trading_strategies', {'_id': strategy_id})
        if success:
            return {"status": "success", "message": "Strategy deleted"}
        else:
            raise HTTPException(status_code=404, detail="Strategy not found")
    except Exception as e:
        logger.error(f"Error deleting trading strategy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/evaluate")
async def evaluate_strategies():
    """Evaluate all active trading strategies"""
    try:
        mongo_service = MongoDBService()
        technical_service = TechnicalAnalysisService()
        
        # Get all active strategies
        strategies = await mongo_service.find('trading_strategies', {'is_active': True})
        stocks = await mongo_service.find('stock_info', {}, {'code': 1})
        
        results = []
        for strategy in strategies:
            for stock in stocks:
                stock_code = stock['code']
                meets_conditions = await technical_service.evaluate_trading_strategy(stock_code, strategy)
                
                if meets_conditions:
                    # Add to stock collections
                    collection_item = {
                        'code': stock_code,
                        'strategy_id': str(strategy['_id']),
                        'strategy_name': strategy['name'],
                        'operation': strategy['operation'],
                        'price': 0,  # This should be the current price
                        'share_amount': 0,
                        'meet_date': datetime.utcnow(),
                        'added_date': datetime.utcnow()
                    }
                    
                    await mongo_service.insert_one('stock_collections', collection_item)
                    results.append({
                        'stock_code': stock_code,
                        'strategy_name': strategy['name'],
                        'operation': strategy['operation']
                    })
        
        return {
            "status": "success",
            "message": f"Strategies evaluated, {len(results)} stocks added to collections",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error evaluating strategies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
