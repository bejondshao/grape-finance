import sys
sys.path.insert(0, 'C:/Users/bejon/AppData/Local/Programs/Python/Python312/Lib/site-packages')

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from datetime import datetime
import asyncio
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.data_service import DataService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/strategies")
async def get_trading_strategies():
    """Get all trading strategies"""
    try:
        mongo_service = MongoDBService()
        strategies = await mongo_service.find('trading_strategies', {})
        # Convert ObjectId to string for JSON serialization
        for strategy in strategies:
            if '_id' in strategy and isinstance(strategy['_id'], ObjectId):
                strategy['_id'] = str(strategy['_id'])
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
            # Convert ObjectId to string for JSON serialization
            if '_id' in strategy and isinstance(strategy['_id'], ObjectId):
                strategy['_id'] = str(strategy['_id'])
            return {"status": "success", "message": "Strategy created", "strategy": strategy}
        else:
            raise HTTPException(status_code=500, detail="Failed to create strategy")
    except DuplicateKeyError as e:
        logger.error(f"Duplicate key error creating trading strategy: {str(e)}")
        raise HTTPException(status_code=400, detail="Strategy with this name already exists")
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

@router.post("/strategies/right_side")
async def create_right_side_strategy(params: Dict[str, Any] = None):
    """Create a right side trading strategy"""
    try:
        mongo_service = MongoDBService()
        
        # 默认参数
        if params is None:
            params = {}
            
        strategy = {
            "name": params.get("name", "右侧交易策略"),
            "description": params.get("description", "基于价格突破、成交量放大和技术指标确认的右侧交易策略"),
            "type": "right_side",
            "parameters": {
                "breakout_threshold": params.get("breakout_threshold", 0),
                "volume_threshold": params.get("volume_threshold", 1.5),
                "cci_threshold": params.get("cci_threshold", -100),
                "ma_periods": params.get("ma_periods", [5, 10, 20]),
                # 添加开关参数
                "enable_price_breakout": params.get("enable_price_breakout", True),
                "enable_volume_check": params.get("enable_volume_check", True),
                "enable_cci_check": params.get("enable_cci_check", True),
                "enable_ma_alignment": params.get("enable_ma_alignment", True)
            },
            "operation": params.get("operation", "关注"),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        success = await mongo_service.insert_one('trading_strategies', strategy)
        if success:
            # Convert ObjectId to string for JSON serialization
            if '_id' in strategy and isinstance(strategy['_id'], ObjectId):
                strategy['_id'] = str(strategy['_id'])
            return {"status": "success", "message": "右侧交易策略创建成功", "strategy": strategy}
        else:
            raise HTTPException(status_code=500, detail="Failed to create strategy")
    except DuplicateKeyError as e:
        logger.error(f"Duplicate key error creating right side trading strategy: {str(e)}")
        raise HTTPException(status_code=400, detail="策略名称已存在")
    except Exception as e:
        logger.error(f"Error creating right side trading strategy: {str(e)}")
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
            # 分批处理股票，每批20个并发执行
            batch_size = 20
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i+batch_size]
                
                # 为每只股票创建评估任务
                tasks = []
                for stock in batch:
                    stock_code = stock['code']
                    
                    # 根据策略类型调用不同的评估方法
                    if strategy.get('type') == 'right_side':
                        # 右侧交易策略
                        task = technical_service.evaluate_right_side_trading_strategy(
                            stock_code, strategy.get('parameters', {})
                        )
                    else:
                        # 通用策略评估
                        task = technical_service.evaluate_trading_strategy(stock_code, strategy)
                    
                    tasks.append((stock_code, task))
                
                # 并发执行当前批次的任务
                batch_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                
                # 处理当前批次的结果
                for (stock_code, _), result in zip(tasks, batch_results):
                    try:
                        if isinstance(result, Exception):
                            logger.error(f"Error evaluating strategy for {stock_code}: {str(result)}")
                            continue
                            
                        meets_conditions = result
                        
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
                    except Exception as e:
                        logger.error(f"Error processing result for {stock_code}: {str(e)}")
                        continue
        
        return {
            "status": "success",
            "message": f"Strategies evaluated, {len(results)} stocks added to collections",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error evaluating strategies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/evaluate/right_side")
async def evaluate_right_side_strategies():
    """专门评估右侧交易策略"""
    try:
        mongo_service = MongoDBService()
        technical_service = TechnicalAnalysisService()
        
        # 获取所有激活的右侧交易策略
        strategies = await mongo_service.find(
            'trading_strategies', 
            {'is_active': True, 'type': 'right_side'}
        )
        
        if not strategies:
            return {
                "status": "success",
                "message": "没有找到激活的右侧交易策略",
                "results": []
            }
        
        # 获取所有股票
        stocks = await mongo_service.find('stock_info', {}, {'code': 1})
        
        results = []
        for strategy in strategies:
            strategy_params = strategy.get('parameters', {})
            
            for stock in stocks:
                stock_code = stock['code']
                
                # 评估右侧交易策略
                evaluation_result = await technical_service.evaluate_right_side_trading_strategy(
                    stock_code, strategy_params
                )
                
                # 如果满足条件，添加到股票集合
                if evaluation_result and isinstance(evaluation_result, dict) and evaluation_result.get('matched'):
                    matching_dates = evaluation_result.get('matching_dates', [])
                    
                    # 为每个匹配的日期创建一个记录
                    for match_info in matching_dates:
                        # 添加到股票集合
                        collection_item = {
                            'code': stock_code,
                            'strategy_id': str(strategy['_id']),
                            'strategy_name': strategy['name'],
                            'operation': strategy['operation'],
                            'price': match_info.get('price', 0),
                            'share_amount': 0,
                            'meet_date': match_info.get('date'),
                            'added_date': datetime.utcnow()
                        }
                        
                        await mongo_service.insert_one('stock_collections', collection_item)
                    
                    results.append({
                        'stock_code': stock_code,
                        'strategy_name': strategy['name'],
                        'operation': strategy['operation'],
                        'matching_dates': matching_dates
                    })
        
        return {
            "status": "success",
            "message": f"右侧交易策略评估完成，{len(results)} 只股票满足条件",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error evaluating right side strategies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")