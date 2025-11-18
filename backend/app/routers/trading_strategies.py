import sys
sys.path.insert(0, 'C:/Users/bejon/AppData/Local/Programs/Python/Python312/Lib/site-packages')

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import logging
from datetime import datetime
import asyncio
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.data_service import DataService
from app.strategies.right_side_trading_strategy import RightSideTradingStrategy
from app.strategies.strong_k_breakout_strategy import StrongKBreakoutStrategy
from app.strategies.bottom_reversal_strategy import BottomReversalStrategy
from app.models.trading_strategy import (
    TradingStrategyBase, 
    TradingStrategyCreate, 
    TradingStrategyUpdate,
    Signal
)

router = APIRouter()
logger = logging.getLogger(__name__)

# 添加一个全局变量来控制策略执行
strategy_execution_in_progress = False
strategy_execution_cancelled = False
strategy_execution_task = None

# 添加一个字典来存储执行任务的结果
strategy_execution_results = {}

@router.get("/strategies", response_model=List[TradingStrategyBase])
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

@router.post("/strategies", response_model=Dict[str, Any])
async def create_trading_strategy(strategy: TradingStrategyCreate):
    """Create a new trading strategy"""
    try:
        logger.info(f"创建新的交易策略: {strategy}")
        mongo_service = MongoDBService()
        
        # Convert Pydantic model to dict
        strategy_dict = strategy.dict(exclude_unset=True)
        strategy_dict['created_at'] = datetime.utcnow()
        
        success = await mongo_service.insert_one('trading_strategies', strategy_dict)
        if success:
            # Convert ObjectId to string for JSON serialization
            if '_id' in strategy_dict and isinstance(strategy_dict['_id'], ObjectId):
                strategy_dict['_id'] = str(strategy_dict['_id'])
            logger.info(f"策略创建成功: {strategy_dict.get('name', 'Unknown')}")
            return {"status": "success", "message": "Strategy created", "strategy": strategy_dict}
        else:
            logger.error("策略创建失败: 数据库插入失败")
            raise HTTPException(status_code=500, detail="Failed to create strategy")
    except DuplicateKeyError as e:
        logger.error(f"重复键错误创建交易策略: {str(e)}")
        raise HTTPException(status_code=400, detail="Strategy with this name already exists")
    except Exception as e:
        logger.error(f"创建交易策略时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/strategies/{strategy_id}")
async def update_trading_strategy(strategy_id: str, strategy: Dict[str, Any]):
    """Update a trading strategy"""
    try:
        logger.info(f"更新交易策略 {strategy_id}: {strategy}")
        mongo_service = MongoDBService()
        strategy['updated_at'] = datetime.utcnow()
        
        success = await mongo_service.update_one(
            'trading_strategies',
            {'_id': strategy_id},
            {'$set': strategy}
        )
        if success:
            logger.info(f"策略更新成功: {strategy_id}")
            return {"status": "success", "message": "Strategy updated"}
        else:
            logger.error(f"策略更新失败: 未找到策略 {strategy_id}")
            raise HTTPException(status_code=404, detail="Strategy not found")
    except Exception as e:
        logger.error(f"更新交易策略时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/strategies/{strategy_id}")
async def delete_trading_strategy(strategy_id: str):
    """Delete a trading strategy"""
    try:
        logger.info(f"删除交易策略: {strategy_id}")
        mongo_service = MongoDBService()
        success = await mongo_service.delete_one('trading_strategies', {'_id': strategy_id})
        if success:
            logger.info(f"策略删除成功: {strategy_id}")
            return {"status": "success", "message": "Strategy deleted"}
        else:
            logger.error(f"策略删除失败: 未找到策略 {strategy_id}")
            raise HTTPException(status_code=404, detail="Strategy not found")
    except Exception as e:
        logger.error(f"删除交易策略时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/strategies/right_side")
async def create_right_side_strategy(params: Dict[str, Any] = None):
    """Create a right side trading strategy"""
    try:
        logger.info(f"创建右侧交易策略，参数: {params}")
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
            # 检查是否已存在默认名称，如果存在则添加时间戳
            default_name = "右侧交易策略"
            existing_strategy = await mongo_service.find_one('trading_strategies', {'name': default_name})
            if existing_strategy:
                import time
                strategy["name"] = f"{default_name}_{int(time.time())}"
            else:
                strategy["name"] = default_name
        if not strategy.get("operation"):
            strategy["operation"] = "关注"
        if strategy.get("is_active") is None:
            strategy["is_active"] = True
        
        success = await mongo_service.insert_one('trading_strategies', strategy)
        if success:
            # Convert ObjectId to string for JSON serialization
            if '_id' in strategy and isinstance(strategy['_id'], ObjectId):
                strategy['_id'] = str(strategy['_id'])
            logger.info(f"右侧交易策略创建成功: {strategy['name']}")
            return {"status": "success", "message": "右侧交易策略创建成功", "strategy": strategy}
        else:
            logger.error("右侧交易策略创建失败: 数据库插入失败")
            raise HTTPException(status_code=500, detail="Failed to create strategy")
    except DuplicateKeyError as e:
        logger.error(f"重复键错误创建右侧交易策略: {str(e)}")
        raise HTTPException(status_code=400, detail="策略名称已存在")
    except Exception as e:
        logger.error(f"创建右侧交易策略时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/strategies/strong_k")
async def create_strong_k_strategy(params: Dict[str, Any] = None):
    """Create a strong K breakout strategy"""
    try:
        logger.info(f"创建强K突破策略，参数: {params}")
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
            "type": "strong_k",
            "parameters": {
                "initial_capital": parameters.get("initial_capital"),
                "max_position_pct": parameters.get("max_position_pct"),
                "max_positions": parameters.get("max_positions")
            },
            "operation": params.get("operation"),
            "is_active": params.get("is_active"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # 清理参数，但保留用户明确设置的false值
        strategy["parameters"] = {k: v for k, v in strategy["parameters"].items() if v is not None}
        
        # 设置必填字段的默认值（仅当用户未提供时）
        if not strategy.get("name"):
            # 检查是否已存在默认名称，如果存在则添加时间戳
            default_name = "强K突破策略"
            existing_strategy = await mongo_service.find_one('trading_strategies', {'name': default_name})
            if existing_strategy:
                import time
                strategy["name"] = f"{default_name}_{int(time.time())}"
            else:
                strategy["name"] = default_name
        if not strategy.get("operation"):
            strategy["operation"] = "关注"
        if strategy.get("is_active") is None:
            strategy["is_active"] = True
        
        success = await mongo_service.insert_one('trading_strategies', strategy)
        if success:
            # Convert ObjectId to string for JSON serialization
            if '_id' in strategy and isinstance(strategy['_id'], ObjectId):
                strategy['_id'] = str(strategy['_id'])
            return {"status": "success", "message": "强K突破策略创建成功", "strategy": strategy}
        else:
            raise HTTPException(status_code=500, detail="Failed to create strategy")
    except DuplicateKeyError as e:
        logger.error(f"Duplicate key error creating strong K trading strategy: {str(e)}")
        raise HTTPException(status_code=400, detail="策略名称已存在")
    except Exception as e:
        logger.error(f"Error creating strong K trading strategy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/strategies/bottom_reversal")
async def create_bottom_reversal_strategy(params: Dict[str, Any] = None):
    """Create a bottom reversal trading strategy"""
    try:
        logger.info(f"创建底部反转策略，参数: {params}")
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
            "type": "bottom_reversal",
            "parameters": {
                "initial_capital": parameters.get("initial_capital"),
                "max_position_pct": parameters.get("max_position_pct"),
                "max_positions": parameters.get("max_positions")
            },
            "operation": params.get("operation"),
            "is_active": params.get("is_active"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # 清理参数，但保留用户明确设置的false值
        strategy["parameters"] = {k: v for k, v in strategy["parameters"].items() if v is not None}
        
        # 设置必填字段的默认值（仅当用户未提供时）
        if not strategy.get("name"):
            # 检查是否已存在默认名称，如果存在则添加时间戳
            default_name = "底部反转策略"
            existing_strategy = await mongo_service.find_one('trading_strategies', {'name': default_name})
            if existing_strategy:
                import time
                strategy["name"] = f"{default_name}_{int(time.time())}"
            else:
                strategy["name"] = default_name
        if not strategy.get("operation"):
            strategy["operation"] = "关注"
        if strategy.get("is_active") is None:
            strategy["is_active"] = True
        
        success = await mongo_service.insert_one('trading_strategies', strategy)
        if success:
            # Convert ObjectId to string for JSON serialization
            if '_id' in strategy and isinstance(strategy['_id'], ObjectId):
                strategy['_id'] = str(strategy['_id'])
            return {"status": "success", "message": "底部反转策略创建成功", "strategy": strategy}
        else:
            raise HTTPException(status_code=500, detail="Failed to create strategy")
    except DuplicateKeyError as e:
        logger.error(f"Duplicate key error creating bottom reversal trading strategy: {str(e)}")
        raise HTTPException(status_code=400, detail="策略名称已存在")
    except Exception as e:
        logger.error(f"Error creating bottom reversal trading strategy: {str(e)}")
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
            strategy_params = strategy.get('parameters', {})
            # 获取执行范围参数，默认为30天
            days_range = strategy_params.get('days_range', 30)
            
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
                            stock_code, strategy_params
                        )
                    elif strategy.get('type') == 'strong_k':
                        # 强K策略使用手动执行方式进行评估
                        continue  # 暂时不支持在评估接口中执行强K策略
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
                            
                            # 检查是否是右侧交易策略的详细结果
                            if isinstance(meets_conditions, dict) and meets_conditions.get('matched'):
                                # 右侧交易策略返回详细匹配信息
                                matching_dates = meets_conditions.get('matching_dates', [])
                                
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
                            else:
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
            # 获取执行范围参数，默认为30天
            days_range = strategy_params.get('days_range', 30)
            
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
            "message": f"右侧交易策略评估完成，{len(results)} 只股票满足条件",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error evaluating right side strategies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/execute/manual")
async def manual_execute_strategy(params: Dict[str, Any]):
    """手动执行策略"""
    global strategy_execution_in_progress, strategy_execution_cancelled, strategy_execution_task
    
    try:
        # 设置执行状态
        strategy_execution_in_progress = True
        strategy_execution_cancelled = False
        
        strategy_type = params.get("strategy_type")  # "right_side" 或 "strong_k"
        stock_codes = params.get("stock_codes", [])  # 用户选择的股票代码列表
        days_range = params.get("days_range", 30)  # 执行范围（天数）
        strategy_params = params.get("parameters", {})  # 策略参数
        
        # 如果没有提供days_range参数，但参数中有，则使用参数中的值
        if "days_range" in strategy_params:
            days_range = strategy_params["days_range"]
        
        # 立即返回响应，不等待执行完成
        execution_id = str(datetime.now().timestamp())
        logger.info(f"启动策略执行任务，执行ID: {execution_id}，策略类型: {strategy_type}")
        
        # 在后台运行策略执行任务
        strategy_execution_task = asyncio.create_task(
            _execute_strategy_background(
                execution_id, strategy_type, stock_codes, days_range, strategy_params
            )
        )
        
        return {
            "status": "started",
            "message": "策略执行任务已启动",
            "execution_id": execution_id
        }
        
    except Exception as e:
        # 重置执行状态
        strategy_execution_in_progress = False
        strategy_execution_cancelled = False
        logger.error(f"启动策略执行任务时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _execute_strategy_background(execution_id: str, strategy_type: str, stock_codes: List[str], 
                                     days_range: int, strategy_params: Dict[str, Any]):
    """在后台执行策略的异步函数"""
    global strategy_execution_in_progress, strategy_execution_cancelled, strategy_execution_results
    
    try:
        mongo_service = MongoDBService()
        technical_service = TechnicalAnalysisService()
        
        if not stock_codes:
            # 如果没有指定股票，获取所有股票
            stocks = await mongo_service.find('stock_info', {}, {'code': 1, 'code_name': 1})
            stock_codes = [stock['code'] for stock in stocks]
        else:
            # 如果指定了股票，获取这些股票的详细信息
            stocks = await mongo_service.find('stock_info', {'code': {'$in': stock_codes}}, {'code': 1, 'code_name': 1})
        
        results = []
        
        if strategy_type == "right_side":
            # 执行右侧交易策略
            logger.info(f"开始执行右侧交易策略，执行ID: {execution_id}，股票数量: {len(stock_codes)}, 执行范围: {days_range}天")
            for stock_code in stock_codes:
                # 检查是否需要取消执行
                if strategy_execution_cancelled:
                    logger.info(f"策略执行已被取消，执行ID: {execution_id}")
                    break
                    
                try:
                    logger.info(f"处理股票 {stock_code}，执行ID: {execution_id}")
                    # 获取股票历史数据
                    collection_name = mongo_service.get_collection_name(stock_code)
                    historical_data = await mongo_service.find(
                        collection_name, 
                        {'code': stock_code},
                        sort=[('date', -1)],
                        limit=days_range  # 使用用户指定的天数范围
                    )
                    
                    if historical_data:
                        logger.info(f"获取到股票 {stock_code} 的 {len(historical_data)} 条历史数据，执行ID: {execution_id}")
                        # 创建策略实例并执行
                        strategy = RightSideTradingStrategy(
                            initial_capital=strategy_params.get("initial_capital", 100000),
                            max_position_pct=strategy_params.get("max_position_pct", 0.02),
                            max_positions=strategy_params.get("max_positions", 5)
                        )
                        
                        # 转换数据格式
                        import pandas as pd
                        df = pd.DataFrame(historical_data)
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.sort_values('date')
                        
                        # 执行策略
                        signals = strategy.generate_signals(df, stock_code)
                        logger.info(f"股票 {stock_code} 生成 {len(signals)} 个信号，执行ID: {execution_id}")
                        
                        # 转换信号为字典格式
                        signals_dict = []
                        for signal in signals:
                            signal_dict = {
                                "symbol": signal.symbol,
                                "action": signal.action,
                                "price": signal.price,
                                "confidence": signal.confidence,
                                "timestamp": signal.timestamp.isoformat() if hasattr(signal.timestamp, 'isoformat') else str(signal.timestamp),
                                "reason": signal.reason
                            }
                            signals_dict.append(signal_dict)
                        
                        if signals_dict:
                            logger.info(f"股票 {stock_code} 生成 {len(signals_dict)} 个有效信号，执行ID: {execution_id}")
                            results.append({
                                "stock_code": stock_code,
                                "signals": signals_dict,
                                "status": "success"
                            })
                        else:
                            logger.info(f"股票 {stock_code} 未生成有效信号，执行ID: {execution_id}")
                            results.append({
                                "stock_code": stock_code,
                                "signals": [],
                                "status": "no_signals"
                            })
                    else:
                        logger.warning(f"股票 {stock_code} 无历史数据，执行ID: {execution_id}")
                        results.append({
                            "stock_code": stock_code,
                            "signals": [],
                            "status": "no_data"
                        })
                        
                except Exception as e:
                    logger.error(f"执行右侧交易策略时发生错误，股票: {stock_code}, 错误: {str(e)}, 执行ID: {execution_id}", exc_info=True)
                    results.append({
                        "stock_code": stock_code,
                        "signals": [],
                        "status": "error",
                        "error": str(e)
                    })
                    
        elif strategy_type == "strong_k":
            # 执行强K策略
            logger.info(f"开始执行强K策略，执行ID: {execution_id}，股票数量: {len(stock_codes)}, 执行范围: {days_range}天")
            for stock_code in stock_codes:
                # 检查是否需要取消执行
                if strategy_execution_cancelled:
                    logger.info(f"策略执行已被取消，执行ID: {execution_id}")
                    break
                    
                try:
                    logger.info(f"处理股票 {stock_code}，执行ID: {execution_id}")
                    # 获取股票历史数据
                    collection_name = mongo_service.get_collection_name(stock_code)
                    historical_data = await mongo_service.find(
                        collection_name, 
                        {'code': stock_code},
                        sort=[('date', -1)],
                        limit=days_range  # 使用用户指定的天数范围
                    )
                    
                    if historical_data:
                        try:
                            logger.info(f"获取到股票 {stock_code} 的 {len(historical_data)} 条历史数据，执行ID: {execution_id}")
                            # 创建策略实例并执行
                            strategy = StrongKBreakoutStrategy(
                                initial_capital=strategy_params.get("initial_capital", 100000),
                                max_position_pct=strategy_params.get("max_position_pct", 0.03),
                                max_positions=strategy_params.get("max_positions", 3)
                            )
                            
                            # 转换数据格式
                            import pandas as pd
                            df = pd.DataFrame(historical_data)
                            df['date'] = pd.to_datetime(df['date'])
                            df = df.sort_values('date')
                            
                            logger.info(f"数据形状: {df.shape}，执行ID: {execution_id}")
                            
                            # 执行策略
                            signals = strategy.generate_signals(df, stock_code)
                            logger.info(f"股票 {stock_code} 生成 {len(signals)} 个信号，执行ID: {execution_id}")
                            
                            # 转换信号为字典格式
                            signals_dict = []
                            try:
                                for signal in signals:
                                    signal_dict = {
                                        "symbol": signal.symbol,
                                        "action": signal.action,
                                        "price": signal.price,
                                        "stop_loss": getattr(signal, 'stop_loss', None),
                                        "target_price": getattr(signal, 'target_price', None),
                                        "timestamp": signal.timestamp.isoformat() if hasattr(signal.timestamp, 'isoformat') else str(signal.timestamp),
                                        "confidence": signal.confidence,
                                        "stage": getattr(signal, 'stage', None),
                                        "reason": signal.reason
                                    }
                                    signals_dict.append(signal_dict)
                            except Exception as e:
                                logger.error(f"转换信号为字典时发生错误，股票: {stock_code}, 错误: {str(e)}, 执行ID: {execution_id}")
                                raise e
                            
                            if signals_dict:
                                logger.info(f"股票 {stock_code} 生成 {len(signals_dict)} 个有效信号，执行ID: {execution_id}")
                                results.append({
                                    "stock_code": stock_code,
                                    "signals": signals_dict,
                                    "status": "success"
                                })
                            else:
                                logger.info(f"股票 {stock_code} 未生成有效信号，执行ID: {execution_id}")
                                results.append({
                                    "stock_code": stock_code,
                                    "signals": [],
                                    "status": "no_signals"
                                })
                        except Exception as e:
                            logger.error(f"生成信号时发生错误，股票: {stock_code}, 错误: {str(e)}, 执行ID: {execution_id}", exc_info=True)
                            raise e
                    else:
                        logger.warning(f"股票 {stock_code} 无历史数据，执行ID: {execution_id}")
                        results.append({
                            "stock_code": stock_code,
                            "signals": [],
                            "status": "no_data"
                        })
                        
                except Exception as e:
                    logger.error(f"执行强K策略时发生错误，股票: {stock_code}, 错误: {str(e)}, 执行ID: {execution_id}", exc_info=True)
                    results.append({
                        "stock_code": stock_code,
                        "signals": [],
                        "status": "error",
                        "error": str(e)
                    })
        
        elif strategy_type == "bottom_reversal":
            # 执行底部反转策略
            logger.info(f"开始执行底部反转策略，执行ID: {execution_id}，股票数量: {len(stock_codes)}, 执行范围: {days_range}天")
            for stock_code in stock_codes:
                # 检查是否需要取消执行
                if strategy_execution_cancelled:
                    logger.info(f"策略执行已被取消，执行ID: {execution_id}")
                    break
                    
                try:
                    logger.info(f"处理股票 {stock_code}，执行ID: {execution_id}")
                    # 获取股票历史数据
                    collection_name = mongo_service.get_collection_name(stock_code)
                    historical_data = await mongo_service.find(
                        collection_name, 
                        {'code': stock_code},
                        sort=[('date', -1)],
                        limit=days_range  # 使用用户指定的天数范围
                    )
                    
                    if historical_data:
                        try:
                            logger.info(f"获取到股票 {stock_code} 的 {len(historical_data)} 条历史数据，执行ID: {execution_id}")
                            # 创建策略实例并执行
                            strategy = BottomReversalStrategy(
                                initial_capital=strategy_params.get("initial_capital", 100000),
                                max_position_pct=strategy_params.get("max_position_pct", 0.03),
                                max_positions=strategy_params.get("max_positions", 5)
                            )
                            
                            # 转换数据格式
                            import pandas as pd
                            df = pd.DataFrame(historical_data)
                            df['date'] = pd.to_datetime(df['date'])
                            df = df.sort_values('date')
                            
                            logger.info(f"数据形状: {df.shape}，执行ID: {execution_id}")
                            
                            # 执行策略
                            signals = strategy.generate_signals(df, stock_code)
                            logger.info(f"股票 {stock_code} 生成 {len(signals)} 个信号，执行ID: {execution_id}")
                            
                            # 转换信号为字典格式
                            signals_dict = []
                            try:
                                for signal in signals:
                                    signal_dict = {
                                        "symbol": signal.symbol,
                                        "action": signal.action,
                                        "price": signal.price,
                                        "stop_loss": getattr(signal, 'stop_loss', None),
                                        "target_price": getattr(signal, 'target_price', None),
                                        "timestamp": signal.timestamp.isoformat() if hasattr(signal.timestamp, 'isoformat') else str(signal.timestamp),
                                        "confidence": signal.confidence,
                                        "reason": signal.reason
                                    }
                                    signals_dict.append(signal_dict)
                            except Exception as e:
                                logger.error(f"转换信号为字典时发生错误，股票: {stock_code}, 错误: {str(e)}, 执行ID: {execution_id}")
                                raise e
                            
                            if signals_dict:
                                logger.info(f"股票 {stock_code} 生成 {len(signals_dict)} 个有效信号，执行ID: {execution_id}")
                                results.append({
                                    "stock_code": stock_code,
                                    "signals": signals_dict,
                                    "status": "success"
                                })
                            else:
                                logger.info(f"股票 {stock_code} 未生成有效信号，执行ID: {execution_id}")
                                results.append({
                                    "stock_code": stock_code,
                                    "signals": [],
                                    "status": "no_signals"
                                })
                        except Exception as e:
                            logger.error(f"生成信号时发生错误，股票: {stock_code}, 错误: {str(e)}, 执行ID: {execution_id}", exc_info=True)
                            raise e
                    else:
                        logger.warning(f"股票 {stock_code} 无历史数据，执行ID: {execution_id}")
                        results.append({
                            "stock_code": stock_code,
                            "signals": [],
                            "status": "no_data"
                        })
                        
                except Exception as e:
                    logger.error(f"执行底部反转策略时发生错误，股票: {stock_code}, 错误: {str(e)}, 执行ID: {execution_id}", exc_info=True)
                    results.append({
                        "stock_code": stock_code,
                        "signals": [],
                        "status": "error",
                        "error": str(e)
                    })
        # 重置执行状态
        strategy_execution_in_progress = False
        strategy_execution_cancelled = False
        
        message = f"手动执行{strategy_type}策略完成"
        if strategy_execution_cancelled:
            message = f"手动执行{strategy_type}策略已取消"
            
        logger.info(f"策略执行完成: {message}, 执行ID: {execution_id}, 总股票数: {len(stock_codes)}, 结果数: {len(results)}")
        
        # 存储执行结果
        strategy_execution_results[execution_id] = {
            "status": "success",
            "message": message,
            "total_stocks": len(stock_codes),
            "results": results,
            "cancelled": strategy_execution_cancelled,
            "completed_at": datetime.utcnow()
        }
        
    except Exception as e:
        # 重置执行状态
        strategy_execution_in_progress = False
        strategy_execution_cancelled = False
        logger.error(f"后台策略执行任务发生错误: {str(e)}, 执行ID: {execution_id}")
        
        # 存储错误结果
        strategy_execution_results[execution_id] = {
            "status": "error",
            "message": f"策略执行过程中发生错误: {str(e)}",
            "total_stocks": 0,
            "results": [],
            "cancelled": strategy_execution_cancelled,
            "completed_at": datetime.utcnow()
        }

@router.get("/execute/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """获取策略执行状态"""
    global strategy_execution_results
    
    # 检查执行是否完成
    if execution_id in strategy_execution_results:
        result = strategy_execution_results[execution_id]
        # 清理已完成的结果（可选）
        # del strategy_execution_results[execution_id]
        return {
            "status": "completed",
            "result": result
        }
    elif strategy_execution_in_progress:
        return {
            "status": "running",
            "message": "策略执行中"
        }
    else:
        return {
            "status": "not_found",
            "message": "未找到执行任务"
        }

@router.post("/execute/stop")
async def stop_strategy_execution():
    """停止策略执行"""
    global strategy_execution_in_progress, strategy_execution_cancelled
    
    if strategy_execution_in_progress:
        strategy_execution_cancelled = True
        return {"status": "success", "message": "策略执行停止命令已发送"}
    else:
        return {"status": "success", "message": "当前没有正在执行的策略"}

@router.get("/stocks/filter")
async def filter_stocks(
    min_price: float = Query(None, description="最低价格"),
    max_price: float = Query(None, description="最高价格"),
    min_volume: int = Query(None, description="最小成交量"),
    market: str = Query(None, description="市场类型：sh, sz, bj"),
    industry: str = Query(None, description="行业")
):
    """筛选股票"""
    try:
        mongo_service = MongoDBService()
        
        # 构建筛选条件
        filter_conditions = {}
        
        if min_price is not None or max_price is not None:
            filter_conditions['current_price'] = {}
            if min_price is not None:
                filter_conditions['current_price']['$gte'] = min_price
            if max_price is not None:
                filter_conditions['current_price']['$lte'] = max_price
                
        if min_volume is not None:
            filter_conditions['volume'] = {'$gte': min_volume}
            
        if market:
            filter_conditions['market'] = market
            
        if industry:
            filter_conditions['industry'] = {'$regex': industry, '$options': 'i'}
        
        # 获取筛选后的股票
        stocks = await mongo_service.find('stock_info', filter_conditions)
        
        # 转换ObjectId
        for stock in stocks:
            if '_id' in stock and isinstance(stock['_id'], ObjectId):
                stock['_id'] = str(stock['_id'])
        
        return {
            "status": "success",
            "count": len(stocks),
            "stocks": stocks
        }
        
    except Exception as e:
        logger.error(f"Error filtering stocks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")