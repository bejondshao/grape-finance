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
        
        # 处理参数中的布尔值，确保从params中正确获取值
        parameters = params.get("parameters", {})
        
        # 构造策略对象，优先使用用户输入的值
        strategy = {
            "name": params.get("name"),
            "description": params.get("description"),
            "type": "right_side",
            "parameters": {
                "breakout_threshold": parameters.get("breakout_threshold"),
                "volume_threshold": parameters.get("volume_threshold"),
                "cci_threshold": parameters.get("cci_threshold"),
                "ma_periods": parameters.get("ma_periods"),
                # 正确处理布尔值，确保用户输入的值被正确存储
                "enable_price_breakout": parameters.get("enable_price_breakout"),
                "enable_volume_check": parameters.get("enable_volume_check"),
                "enable_cci_check": parameters.get("enable_cci_check"),
                "enable_ma_alignment": parameters.get("enable_ma_alignment")
            },
            "operation": params.get("operation"),
            "is_active": params.get("is_active"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # 清理参数，但保留用户明确设置的false值
        strategy["parameters"] = {k: v for k, v in strategy["parameters"].items() if v is not None}
        
        # 如果ma_periods是字符串，转换为数组
        if isinstance(strategy["parameters"].get("ma_periods"), str):
            ma_periods_str = strategy["parameters"]["ma_periods"]
            try:
                ma_periods = [int(p.strip()) for p in ma_periods_str.split(",") if p.strip()]
                strategy["parameters"]["ma_periods"] = ma_periods
            except ValueError:
                # 如果转换失败，使用默认值
                strategy["parameters"]["ma_periods"] = [5, 10, 20]
        
        # 为布尔参数设置默认值（仅在用户未提供时）
        bool_params = ["enable_price_breakout", "enable_volume_check", "enable_cci_check", "enable_ma_alignment"]
        for param in bool_params:
            if param not in strategy["parameters"]:
                strategy["parameters"][param] = True
        
        # 设置必填字段的默认值（仅当用户未提供时）
        if not strategy.get("name"):
            strategy["name"] = "右侧交易策略"
        if not strategy.get("operation"):
            strategy["operation"] = "关注"
        if strategy.get("is_active") is None:
            strategy["is_active"] = True
        
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
        # 获取所有股票和股票名称信息
        stocks = await mongo_service.find('stock_info', {}, {'code': 1, 'code_name': 1})
        
        # 创建股票代码到名称的映射
        stock_name_map = {stock['code']: stock.get('code_name', stock['code']) for stock in stocks}
        
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
                            # 从映射表中获取股票名称
                            stock_name = stock_name_map.get(stock_code, stock_code)
                            
                            # 通用策略使用当前日期作为匹配日期
                            meet_date = datetime.utcnow()
                            
                            # 通用策略不需要特定价格，设为0
                            price = 0
                            
                            # Add to stock collections
                            collection_item = {
                                'code': stock_code,
                                'name': stock_name,  # 添加股票名称
                                'strategy_id': str(strategy['_id']),
                                'strategy_name': strategy['name'],
                                'operation': strategy['operation'],
                                'price': price,  # 通用策略不需要特定价格
                                'share_amount': 0,
                                'meet_date': meet_date,
                                'added_date': datetime.utcnow()
                            }
                            
                            await mongo_service.insert_one('stock_collections', collection_item)
                            results.append({
                                'stock_code': stock_code,
                                'stock_name': stock_name,  # 添加股票名称
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
        
        # 获取所有股票和股票名称信息
        stocks = await mongo_service.find('stock_info', {}, {'code': 1, 'code_name': 1})
        
        # 创建股票代码到名称的映射
        stock_name_map = {stock['code']: stock.get('code_name', stock['code']) for stock in stocks}
        
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
                    
                    # 获取股票名称
                    stock_info = await mongo_service.find_one('stock_info', {'code': stock_code})
                    stock_name = stock_info.get('code_name', stock_code) if stock_info else stock_code
                    
                    # 为每个匹配的日期创建一个记录
                    for match_info in matching_dates:
                        # 添加到股票集合
                        collection_item = {
                            'code': stock_code,
                            'name': stock_name,  # 添加股票名称
                            'strategy_id': str(strategy['_id']),
                            'strategy_name': strategy['name'],
                            'operation': strategy['operation'],
                            'price': match_info.get('price'),
                            'share_amount': 0,
                            'meet_date': match_info.get('date'),
                            'added_date': datetime.utcnow()
                        }
                        
                        await mongo_service.insert_one('stock_collections', collection_item)
                    
                    results.append({
                        'stock_code': stock_code,
                        'stock_name': stock_name,  # 添加股票名称
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