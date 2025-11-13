from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.services.mongodb_service import MongoDBService
from app.services.technical_analysis_service import TechnicalAnalysisService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/indicators")
async def get_technical_indicators(
    stock_code: str,
    indicator_type: Optional[str] = Query(None, description="Technical indicator type (e.g., CCI)"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get technical indicators for a stock"""
    try:
        mongo_service = MongoDBService()
        collection_name = f"technical_{stock_code}"
        
        query = {'code': stock_code}
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                query['date']['$gte'] = start_date
            if end_date:
                query['date']['$lte'] = end_date
        
        indicators = await mongo_service.find(
            collection_name,
            query,
            sort=[('date', -1)]
        )
        
        return {
            "stock_code": stock_code,
            "indicator_type": indicator_type,
            "indicators": indicators
        }
    except Exception as e:
        logger.error(f"Error getting technical indicators for {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/config")
async def create_technical_config(config: Dict[str, Any]):
    """Create technical analysis configuration"""
    try:
        mongo_service = MongoDBService()
        config['created_at'] = datetime.utcnow()
        
        success = await mongo_service.insert_one('technical_analysis_config', config)
        if success:
            return {"status": "success", "message": "Configuration created"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create configuration")
    except Exception as e:
        logger.error(f"Error creating technical config: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/update-cci")
async def update_stock_cci_endpoint(
    stock_code: str = Query(..., description="股票代码"),
    start_date: Optional[str] = Query(None, description="开始日期，格式: YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式: YYYY-MM-DD")
):
    """手动更新指定股票的CCI指标值"""
    try:
        # 验证股票代码
        if not stock_code or not isinstance(stock_code, str):
            raise HTTPException(status_code=400, detail="无效的股票代码")
        
        # 验证日期格式
        date_range = None
        if start_date or end_date:
            date_range = {}
            if start_date:
                try:
                    # 验证日期格式
                    datetime.strptime(start_date, '%Y-%m-%d')
                    date_range['start_date'] = start_date
                except ValueError:
                    raise HTTPException(status_code=400, detail="开始日期格式无效，请使用YYYY-MM-DD格式")
            if end_date:
                try:
                    # 验证日期格式
                    datetime.strptime(end_date, '%Y-%m-%d')
                    date_range['end_date'] = end_date
                except ValueError:
                    raise HTTPException(status_code=400, detail="结束日期格式无效，请使用YYYY-MM-DD格式")
        
        # 调用服务层方法更新CCI
        technical_service = TechnicalAnalysisService()
        result = await technical_service.update_stock_cci(stock_code, date_range)
        
        if result.get('success'):
            return {
                "status": "success",
                "message": result.get('message'),
                "updated_count": result.get('updated_count')
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message'))
            
    except HTTPException:
        raise  # 重新抛出已定义的HTTP异常
    except Exception as e:
        logger.error(f"更新股票 {stock_code} 的CCI指标时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


@router.post("/update-all-cci")
async def update_all_stocks_cci_endpoint():
    """
    一键更新所有股票的CCI值
    
    对于每个股票，从technical_xx_123456集合中查询最新的CCI日期，然后更新从该日期到今日的CCI值
    """
    try:
        logger.info("接收到批量更新所有股票CCI值的请求")
        
        # 调用服务层方法
        technical_service = TechnicalAnalysisService()
        result = await technical_service.update_all_stocks_cci()
        
        # 记录操作日志
        logger.info(f"批量更新所有股票CCI值请求完成，结果: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"批量更新所有股票CCI值请求处理错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")
