import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo import UpdateOne

from app.services.mongodb_service import MongoDBService

logger = logging.getLogger(__name__)

class TechnicalAnalysisService:
    def __init__(self):
        self.mongo_service = MongoDBService()
    
    # async def calculate_cci(self, df: pd.DataFrame, period: int = 14, constant: float = 0.015) -> pd.Series:
    #     """Calculate Commodity Channel Index"""
    #     try:
    #         tp = (df['high'] + df['low'] + df['close']) / 3
    #         sma = tp.rolling(window=period).mean()
    #         mad = tp.rolling(window=period).apply(
    #             lambda x: np.abs(x - x.mean()).mean(), raw=False
    #         )
    #         cci = (tp - sma) / (constant * mad)
    #         return cci
    #     except Exception as e:
    #         logger.error(f"Error calculating CCI: {str(e)}")
    #         return pd.Series([np.nan] * len(df))

    async def calculate_cci(self, df: pd.DataFrame, period: int = 14, constant: float = 0.015) -> pd.Series:
        """Calculate Commodity Channel Index"""
        try:
            # Convert columns to numeric, coercing errors to NaN
            df.copy()
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')

            # Drop rows with NaN values that would break the calculation
            df = df.dropna(subset=['high', 'low', 'close'])

            if len(df) < period:
                return pd.Series([np.nan] * len(df))

            tp = (df['high'] + df['low'] + df['close']) / 3
            sma = tp.rolling(window=period).mean()
            mad = tp.rolling(window=period).apply(
                lambda x: np.abs(x - x.mean()).mean(), raw=False
            )
            cci = (tp - sma) / (constant * mad)
            return cci
        except Exception as e:
            logger.error(f"Error calculating CCI: {str(e)}")
            return pd.Series([np.nan] * len(df))

    async def calculate_technical_indicators(self, stock_code: str, df: pd.DataFrame):
        """Calculate all technical indicators for a stock"""
        try:
            # Get stock properties for dynamic parameters
            stock_info = await self.mongo_service.find_one('stock_info', {'code': stock_code})
            cci_period, cci_constant = await self._get_cci_parameters(stock_info)
            
            # Calculate CCI
            df_sorted = df.sort_values('date')
            cci_values = await self.calculate_cci(df_sorted, cci_period, cci_constant)
            
            # Save technical indicators
            collection_name = f"technical_{stock_code.replace('.', '_')}"
            operations = []
            
            for i, (idx, row) in enumerate(df_sorted.iterrows()):
                if i >= cci_period - 1 and not pd.isna(cci_values.iloc[i]):
                    tech_doc = {
                        'code': stock_code,
                        'date': row['date'] if isinstance(row['date'], datetime) else datetime.strptime(row['date'], '%Y-%m-%d'),
                        'cci': float(cci_values.iloc[i]),
                        'cci_period': cci_period,
                        'cci_constant': cci_constant,
                        'updated_at': datetime.utcnow()
                    }
                    
                    operations.append(
                        UpdateOne(
                            {'code': stock_code, 'date': tech_doc['date']},
                            {'$set': tech_doc},
                            upsert=True
                        )
                    )
            
            if operations:
                await self.mongo_service.bulk_write(collection_name, operations)
                logger.info(f"Calculated technical indicators for {stock_code}")
                
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {stock_code}: {str(e)}")
    
    async def _get_cci_parameters(self, stock_info: Dict[str, Any]) -> tuple:
        """Get CCI parameters based on stock properties"""
        # Default values
        period = 14
        constant = 0.015
        
        if stock_info:
            # Example: Adjust parameters based on stock type or industry
            stock_type = stock_info.get('type', '')
            if 'ST' in stock_info.get('code_name', ''):
                period = 20
                constant = 0.02
            elif stock_type == '1':  # Shanghai main board
                period = 14
                constant = 0.015
            elif stock_type == '2':  # Shenzhen main board
                period = 14
                constant = 0.015
        
        return period, constant

    async def evaluate_trading_strategy(self, stock_code: str, strategy: Dict[str, Any]) -> bool:
        """Evaluate if a stock meets trading strategy conditions"""
        try:
            # Get latest technical data
            collection_name = f"technical_{stock_code.replace('.', '_')}"
            tech_data = await self.mongo_service.find(
                collection_name,
                {'code': stock_code},
                sort=[('date', -1)],
                limit=2
            )
            
            if len(tech_data) < 2:
                return False
            
            current_data = tech_data[0]
            previous_data = tech_data[1]
            
            # Check strategy conditions
            conditions_met = True
            for condition in strategy.get('conditions', []):
                indicator = condition.get('indicator')
                operator = condition.get('operator')
                value = condition.get('value')
                days_ago = condition.get('days_ago', 0)
                
                if days_ago == 0:
                    data_point = current_data
                else:
                    data_point = previous_data
                
                if indicator == 'CCI':
                    cci_value = data_point.get('cci', 0)
                    if operator == '>' and not (cci_value > value):
                        conditions_met = False
                    elif operator == '>=' and not (cci_value >= value):
                        conditions_met = False
                    elif operator == '<' and not (cci_value < value):
                        conditions_met = False
                    elif operator == '<=' and not (cci_value <= value):
                        conditions_met = False
                    elif operator == '==' and not (cci_value == value):
                        conditions_met = False
                    elif operator == '!=' and not (cci_value != value):
                        conditions_met = False
            
            return conditions_met
            
        except Exception as e:
            logger.error(f"Error evaluating trading strategy for {stock_code}: {str(e)}")
            return False
