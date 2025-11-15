import logging
import pandas as pd
import numpy as np
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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

    async def calculate_cci(self, df: pd.DataFrame, stock_code: str = None, period: int = 14, constant: float = 0.015) -> pd.Series:
        """Calculate Commodity Channel Index
        
        Args:
            df: 包含high, low, close列的DataFrame
            stock_code: 股票代码，当数据不足时用于从数据库获取历史数据
            period: CCI计算周期，默认为14
            constant: 缩放常数，默认为0.015
            
        Returns:
            包含CCI值的Series，索引与输入DataFrame匹配
        """
        try:
            # 参数验证
            if not isinstance(df, pd.DataFrame):
                raise TypeError("Input must be a pandas DataFrame")
            
            if period < 1:
                raise ValueError("Period must be at least 1")
            
            if constant <= 0:
                raise ValueError("Constant must be positive")
            
            # 检查必需列
            required_columns = ['high', 'low', 'close']
            for col in required_columns:
                if col not in df.columns:
                    raise KeyError(f"Required column '{col}' not found in DataFrame")
            
            # 创建DataFrame副本以避免修改原始数据
            df_copy = df.copy()
            logger.info(f"calculate_cci received {len(df_copy)} records with columns: {list(df_copy.columns)}")
            
            # 转换列为数值类型，错误转换为NaN
            for col in required_columns:
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
            
            # 记录转换后的非数值行数量
            non_numeric_rows = df_copy[df_copy[required_columns].isna().any(axis=1)]
            if len(non_numeric_rows) > 0:
                logger.warning(f"Found {len(non_numeric_rows)} rows with non-numeric price data")
            
            # 初始化结果Series，确保索引与原始DataFrame匹配
            result = pd.Series([np.nan] * len(df), index=df.index)
            
            # 检查数据是否足够计算
            logger.info(f"Current data size after cleaning: {len(df_copy)}, required: {period}")
            if len(df_copy) < period:
                # 如果提供了股票代码，尝试从数据库获取历史数据补充
                if stock_code:
                    try:
                        logger.info(f"Attempting to fetch additional historical data for {stock_code}")
                        
                        # 计算需要补充的数据量
                        additional_data_needed = period - len(df_copy) + 1  # 多获取一些确保足够
                        
                        # 获取补充的历史数据
                        # 假设df中的数据是按日期排序的，我们需要获取更早的数据
                        if not df.empty and 'date' in df.columns:
                            # 获取df中最早的日期作为结束日期，往前获取数据
                            earliest_date = df['date'].min()
                            if isinstance(earliest_date, datetime):
                                end_date_str = earliest_date.strftime('%Y-%m-%d')
                            else:
                                end_date_str = str(earliest_date)
                            
                            # 从数据库获取历史数据，需要比period多一些以确保有足够的数据
                            historical_data = await self.mongo_service.get_stock_history(
                                stock_code=stock_code,
                                end_date=end_date_str,
                                limit=additional_data_needed * 2,  # 获取更多数据以确保有足够的数据
                                sort="desc"  # 降序排列，最新的数据在前
                            )
                        else:
                            # 如果df中没有日期信息，直接获取最近的数据
                            historical_data = await self.mongo_service.get_stock_history(
                                stock_code=stock_code,
                                limit=additional_data_needed * 2,
                                sort="desc"
                            )
                        
                        if historical_data:
                            logger.info(f"Retrieved {len(historical_data)} additional records from database")
                            
                            # 将历史数据转换为DataFrame
                            historical_df = pd.DataFrame(historical_data)
                            
                            # 确保数据列名正确
                            required_columns = ['high', 'low', 'close', 'date']
                            if all(col in historical_df.columns for col in required_columns):
                                # 合并数据并按日期排序
                                combined_df = pd.concat([historical_df, df_copy], ignore_index=True)
                                # 确保日期唯一，保留最新记录
                                if 'date' in combined_df.columns:
                                    combined_df['date'] = pd.to_datetime(combined_df['date'])
                                    combined_df = combined_df.sort_values('date', ascending=True)
                                    combined_df = combined_df.drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)
                                df_copy = combined_df
                                logger.info(f"Combined data has {len(df_copy)} records")
                            else:
                                logger.warning(f"Historical data missing required columns: {required_columns}")
                        else:
                            logger.warning(f"No historical data found for {stock_code}")
                    except Exception as e:
                        logger.error(f"Error fetching historical data for {stock_code}: {str(e)}")
                
                # 如果仍然数据不足，返回全NaN结果
                if len(df_copy) < period:
                    logger.warning(f"Still not enough data points after fetching historical data. Required: {period}, Available: {len(df_copy)}")
                    return result
            
            # 找出数据有效的行
            valid_data_mask = df_copy[required_columns].notna().all(axis=1)
            
            if not valid_data_mask.any():
                logger.warning("No valid data points found for CCI calculation")
                return result
            
            # 计算典型价格 (TP)
            tp = (df_copy['high'] + df_copy['low'] + df_copy['close']) / 3
            
            # 计算TP的简单移动平均线 (SMA)
            sma = tp.rolling(window=period).mean()
            
            # 计算平均绝对偏差 (MAD)，使用更高效的方式
            # 先计算每个点相对于均值的绝对偏差，然后使用rolling窗口平均
            mad = tp.rolling(window=period).apply(
                lambda x: np.fabs(x - x.mean()).mean(), raw=True  # 使用raw=True提高性能
            )
            
            # 计算CCI，处理以下情况：
            # 1. MAD为零或接近零
            # 2. 数据点不足
            # 3. 中间计算出现NaN
            valid_cci_mask = (mad > 1e-10) & valid_data_mask  # 使用小阈值避免除零错误
            
            # Create a temporary Series to hold CCI values for the entire combined dataframe
            temp_cci = pd.Series(np.nan, index=df_copy.index)
            
            if valid_cci_mask.any():
                # 只在有效位置计算CCI
                temp_cci[valid_cci_mask] = (tp[valid_cci_mask] - sma[valid_cci_mask]) / (constant * mad[valid_cci_mask])
                
                # Create a date-to-CCI mapping
                if 'date' in df_copy.columns and 'date' in df.columns:
                    df_copy['date'] = pd.to_datetime(df_copy['date'])
                    df['date'] = pd.to_datetime(df['date'])
                    date_cci_map = pd.Series(temp_cci.values, index=df_copy['date'])
                    
                    # Remove duplicate indices, keeping the last value for each date
                    date_cci_map = date_cci_map[~date_cci_map.index.duplicated(keep='last')]
                    
                    # Map the CCI values back to the original input dataframe's dates
                    result = df['date'].map(date_cci_map)
                else:
                    # 如果没有日期列，直接返回计算结果的后部分（对应原始df的长度）
                    if len(temp_cci) >= len(result):
                        result = temp_cci.iloc[-len(result):].reset_index(drop=True)
                
                # 记录计算结果统计信息以便调试
                valid_result_count = result.notna().sum()
                logger.debug(f"Calculated CCI for {valid_result_count}/{len(df)} data points")
            else:
                logger.warning("No valid CCI values could be calculated")
            
            return result
        except Exception as e:
            logger.error(f"Error calculating CCI: {str(e)}")
            # 出错时返回全NaN序列
            if isinstance(df, pd.DataFrame):
                return pd.Series([np.nan] * len(df), index=df.index)
            else:
                return pd.Series([np.nan])

    async def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (RSI)
        
        Args:
            df: DataFrame containing close column
            period: RSI calculation period, default 14
            
        Returns:
            Series containing RSI values, index matches input DataFrame
        """
        try:
            # Validate inputs
            if not isinstance(df, pd.DataFrame):
                raise TypeError("Input must be a pandas DataFrame")
            if 'close' not in df.columns:
                raise KeyError("Close column not found")
            if period < 1:
                raise ValueError("Period must be at least 1")
            
            # Convert close to numeric
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            # Calculate price changes
            delta = df['close'].diff()
            delta = delta[1:]  # Drop first NaN
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate exponential moving averages
            avg_gain = gains.ewm(span=period, adjust=False).mean()
            avg_loss = losses.ewm(span=period, adjust=False).mean()
            
            # Calculate RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Pad with NaNs to match original length
            rsi_series = pd.Series(np.nan, index=df.index)
            rsi_series.iloc[1:] = rsi
            
            return rsi_series
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series([np.nan] * len(df))

    async def calculate_macd(self, df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        """Calculate Moving Average Convergence Divergence (MACD)
        
        Args:
            df: DataFrame containing close column
            fast_period: Fast EMA period, default 12
            slow_period: Slow EMA period, default 26
            signal_period: Signal EMA period, default 9
            
        Returns:
            DataFrame containing MACD line, signal line, and histogram
        """
        try:
            # Validate inputs
            if not isinstance(df, pd.DataFrame):
                raise TypeError("Input must be a pandas DataFrame")
            if 'close' not in df.columns:
                raise KeyError("Close column not found")
            
            # Convert close to numeric
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            # Calculate EMAs
            ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
            ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            
            # Calculate histogram
            macd_histogram = macd_line - signal_line
            
            return pd.DataFrame({
                'macd_line': macd_line,
                'signal_line': signal_line,
                'macd_histogram': macd_histogram
            }, index=df.index)
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return pd.DataFrame({
                'macd_line': [np.nan] * len(df),
                'signal_line': [np.nan] * len(df),
                'macd_histogram': [np.nan] * len(df)
            }, index=df.index)

    async def calculate_kdj(self, df: pd.DataFrame, period: int = 9, slow_k_period: int = 3, slow_d_period: int = 3) -> pd.DataFrame:
        """Calculate KDJ indicator
        
        Args:
            df: DataFrame containing high, low, close columns
            period: KDJ calculation period, default 9
            slow_k_period: Slow K period, default 3
            slow_d_period: Slow D period, default 3
            
        Returns:
            DataFrame containing K, D, J values
        """
        try:
            # Validate inputs
            if not isinstance(df, pd.DataFrame):
                raise TypeError("Input must be a pandas DataFrame")
            for col in ['high', 'low', 'close']:
                if col not in df.columns:
                    raise KeyError(f"{col} column not found")
            
            # Convert columns to numeric
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            # Calculate highest high and lowest low
            df['highest_high'] = df['high'].rolling(window=period).max()
            df['lowest_low'] = df['low'].rolling(window=period).min()
            
            # Calculate RSV
            rsv = (df['close'] - df['lowest_low']) / (df['highest_high'] - df['lowest_low']) * 100
            
            # Calculate KDJ
            df['kdj_k'] = rsv.ewm(com=slow_k_period-1, adjust=False).mean()
            df['kdj_d'] = df['kdj_k'].ewm(com=slow_d_period-1, adjust=False).mean()
            df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
            
            return pd.DataFrame({
                'kdj_k': df['kdj_k'],
                'kdj_d': df['kdj_d'],
                'kdj_j': df['kdj_j']
            }, index=df.index)
        except Exception as e:
            logger.error(f"Error calculating KDJ: {str(e)}")
            return pd.DataFrame({
                'kdj_k': [np.nan] * len(df),
                'kdj_d': [np.nan] * len(df),
                'kdj_j': [np.nan] * len(df)
            }, index=df.index)

    async def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, num_std: int = 2) -> pd.DataFrame:
        """Calculate Bollinger Bands
        
        Args:
            df: DataFrame containing close column
            period: Moving average period, default 20
            num_std: Number of standard deviations, default 2
            
        Returns:
            DataFrame containing upper, middle, lower bands
        """
        try:
            # Validate inputs
            if not isinstance(df, pd.DataFrame):
                raise TypeError("Input must be a pandas DataFrame")
            if 'close' not in df.columns:
                raise KeyError("Close column not found")
            
            # Convert close to numeric
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            # Calculate moving average
            ma = df['close'].rolling(window=period).mean()
            
            # Calculate standard deviation
            std = df['close'].rolling(window=period).std()
            
            # Calculate Bollinger Bands
            upper = ma + (num_std * std)
            lower = ma - (num_std * std)
            
            return pd.DataFrame({
                'bb_upper': upper,
                'bb_middle': ma,
                'bb_lower': lower
            }, index=df.index)
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return pd.DataFrame({
                'bb_upper': [np.nan] * len(df),
                'bb_middle': [np.nan] * len(df),
                'bb_lower': [np.nan] * len(df)
            }, index=df.index)

    async def calculate_technical_indicators(self, stock_code: str, df: pd.DataFrame) -> int:
        """Calculate all technical indicators for a stock and return the number of updated records"""
        try:
            # Get stock properties for dynamic parameters
            stock_info = await self.mongo_service.find_one('stock_info', {'code': stock_code})
            cci_period, cci_constant = await self._get_cci_parameters(stock_info)
            
            # Calculate indicators
            df_sorted = df.sort_values('date')
            cci_values = await self.calculate_cci(df_sorted, stock_code, cci_period, cci_constant)
            rsi_values = await self.calculate_rsi(df_sorted, period=14)
            macd_values = await self.calculate_macd(df_sorted)
            kdj_values = await self.calculate_kdj(df_sorted)
            bb_values = await self.calculate_bollinger_bands(df_sorted)
            
            # Save technical indicators
            collection_name = self.mongo_service.get_technical_collection_name(stock_code)
            operations = []
            
            # Get the latest technical analysis date to avoid re-updating existing records
            latest_tech_date_str = await self.mongo_service.get_latest_technical_date(stock_code)
            latest_tech_date = datetime.strptime(latest_tech_date_str, "%Y-%m-%d %H:%M:%S") if latest_tech_date_str else datetime.min
            
            for i, (idx, row) in enumerate(df_sorted.iterrows()):
                if not pd.isna(cci_values.iloc[i]):
                    # Ensure current_date is a datetime object for comparison
                    if isinstance(row['date'], pd.Timestamp):
                        current_date = row['date'].to_pydatetime()
                    elif isinstance(row['date'], datetime):
                        current_date = row['date']
                    elif isinstance(row['date'], str):
                        current_date = datetime.strptime(row['date'], '%Y-%m-%d')
                    else:
                        current_date = row['date']
                    
                    # Only update records that are after the latest technical analysis date
                    if current_date > latest_tech_date:
                        tech_doc = {
                            'code': stock_code,
                            'date': current_date,
                            'cci': float(cci_values.iloc[i]),
                            'cci_period': cci_period,
                            'cci_constant': cci_constant,
                            'rsi': float(rsi_values.iloc[i]) if not pd.isna(rsi_values.iloc[i]) else None,
                            'macd_line': float(macd_values['macd_line'].iloc[i]) if not pd.isna(macd_values['macd_line'].iloc[i]) else None,
                            'macd_signal': float(macd_values['signal_line'].iloc[i]) if not pd.isna(macd_values['signal_line'].iloc[i]) else None,
                            'macd_histogram': float(macd_values['macd_histogram'].iloc[i]) if not pd.isna(macd_values['macd_histogram'].iloc[i]) else None,
                            'kdj_k': float(kdj_values['kdj_k'].iloc[i]) if not pd.isna(kdj_values['kdj_k'].iloc[i]) else None,
                            'kdj_d': float(kdj_values['kdj_d'].iloc[i]) if not pd.isna(kdj_values['kdj_d'].iloc[i]) else None,
                            'kdj_j': float(kdj_values['kdj_j'].iloc[i]) if not pd.isna(kdj_values['kdj_j'].iloc[i]) else None,
                            'bb_upper': float(bb_values['bb_upper'].iloc[i]) if not pd.isna(bb_values['bb_upper'].iloc[i]) else None,
                            'bb_middle': float(bb_values['bb_middle'].iloc[i]) if not pd.isna(bb_values['bb_middle'].iloc[i]) else None,
                            'bb_lower': float(bb_values['bb_lower'].iloc[i]) if not pd.isna(bb_values['bb_lower'].iloc[i]) else None,
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
                logger.info(f"Calculated technical indicators for {stock_code}, updated {len(operations)} new records")
                return len(operations)
            return 0
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {stock_code}: {str(e)}")
            raise  # 重新抛出异常以便调用者能够捕获并处理
    
    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """统计集合中的文档数量"""
        try:
            # 检查集合是否存在
            collection_names = await self.mongo_service.get_collection_names()
            if collection_name not in collection_names:
                return 0
            
            # 执行计数查询
            count = await self.mongo_service.db[collection_name].count_documents(query)
            return count
        except Exception as e:
            logger.error(f"Error counting documents in {collection_name}: {str(e)}")
            return 0
            
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

    async def update_stock_cci(self, stock_code: str, date_range: Dict[str, str] = None) -> Dict[str, Any]:
        """手动更新指定股票的CCI指标值
        
        Args:
            stock_code: 股票代码
            date_range: 日期范围，格式为 {'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}，不提供则更新所有数据
            
        Returns:
            包含更新结果的字典
        """
        try:
            # Convert to lowercase for consistent case handling
            stock_code = stock_code.lower()
            
            logger.info(f"开始更新股票 {stock_code} 的CCI指标")
            
            # Determine CCI period based on stock market type
            cci_period = 20 if stock_code.startswith("bj.") else 14
            
            # 从数据库获取股票的日线数据
            # 获取历史数据，需要比计算周期多一些数据来确保计算准确性
            start_date = date_range.get('start_date') if date_range else None
            end_date = date_range.get('end_date') if date_range else None
            
            # If no date range provided, only update new data after the last technical analysis
            if not date_range:
                logger.debug(f"Checking latest tech date for {stock_code}")
                latest_tech_date = await self.mongo_service.get_latest_technical_date(stock_code)
                logger.debug(f"Latest tech date for {stock_code}: {latest_tech_date}")
                if latest_tech_date:
                    # Convert to datetime object
                    latest_tech_datetime = datetime.strptime(latest_tech_date, "%Y-%m-%d %H:%M:%S")
                    # Subtract (period - 1) days to ensure enough data for CCI calculation
                    start_date = (latest_tech_datetime - timedelta(days=cci_period - 1)).strftime("%Y-%m-%d")
                    logger.debug(f"Calculated start_date: {start_date}")
            
            historical_data = await self.mongo_service.get_stock_history(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                limit=0,  # 获取所有历史数据
                sort="asc"  # 升序排列，便于计算
            )
            
            if not historical_data:
                return {"success": False, "message": f"未找到股票 {stock_code} 的历史数据"}
            
            # 将历史数据转换为DataFrame
            df = pd.DataFrame(historical_data)
            
            # 确保数据按日期排序
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 调用现有的计算方法
            updated_count = await self.calculate_technical_indicators(stock_code, df)
            
            # 验证更新结果
            collection_name = self.mongo_service.get_technical_collection_name(stock_code)
            total_records = await self.mongo_service.count_documents(
                collection_name,
                {'code': stock_code}
            )
            
            logger.info(f"股票 {stock_code} 的CCI指标更新完成，共 {total_records} 条记录")
            return {
                "success": True,
                "message": f"股票 {stock_code} 的CCI指标更新成功",
                "updated_count": updated_count
            }
            
        except Exception as e:
            logger.error(f"更新股票 {stock_code} 的CCI指标时出错: {str(e)}")
            return {
                "success": False,
                "message": f"更新失败: {str(e)}"
            }

    async def update_stock_indicators(self, stock_code: str, date_range: Dict[str, str] = None) -> Dict[str, Any]:
        """手动更新指定股票的所有技术指标值
        
        Args:
            stock_code: 股票代码
            date_range: 日期范围，格式为 {'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}，不提供则更新所有数据
            
        Returns:
            包含更新结果的字典
        """
        try:
            # Convert to lowercase for consistent case handling
            stock_code = stock_code.lower()
            
            logger.info(f"开始更新股票 {stock_code} 的所有技术指标")
            
            # 从数据库获取股票的日线数据
            # 获取历史数据，需要比计算周期多一些数据来确保计算准确性
            start_date = date_range.get('start_date') if date_range else None
            end_date = date_range.get('end_date') if date_range else None
            
            # If no date range provided, only update new data after the last technical analysis
            if not date_range:
                logger.debug(f"Checking latest tech date for {stock_code}")
                latest_tech_date = await self.mongo_service.get_latest_technical_date(stock_code)
                logger.debug(f"Latest tech date for {stock_code}: {latest_tech_date}")
                if latest_tech_date:
                    # Convert to datetime object
                    latest_tech_datetime = datetime.strptime(latest_tech_date, "%Y-%m-%d %H:%M:%S")
                    # Subtract (period - 1) days to ensure enough data for indicator calculation (using max period)
                    start_date = (latest_tech_datetime - timedelta(days=20)).strftime("%Y-%m-%d")
                    logger.debug(f"Calculated start_date: {start_date}")
            
            historical_data = await self.mongo_service.get_stock_history(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                limit=0,  # 获取所有历史数据
                sort="asc"  # 升序排列，便于计算
            )
            
            if not historical_data:
                return {"success": False, "message": f"未找到股票 {stock_code} 的历史数据"}
            
            # 将历史数据转换为DataFrame
            df = pd.DataFrame(historical_data)
            
            # 确保数据按日期排序
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 调用现有的计算方法
            updated_count = await self.calculate_technical_indicators(stock_code, df)
            
            # 验证更新结果
            collection_name = self.mongo_service.get_technical_collection_name(stock_code)
            total_records = await self.mongo_service.count_documents(
                collection_name,
                {'code': stock_code}
            )
            
            logger.info(f"股票 {stock_code} 的所有技术指标更新完成，共 {total_records} 条记录")
            return {
                "success": True,
                "message": f"股票 {stock_code} 的所有技术指标更新成功",
                "updated_count": updated_count
            }
            
        except Exception as e:
            logger.error(f"更新股票 {stock_code} 的所有技术指标时出错: {str(e)}")
            return {
                "success": False,
                "message": f"更新失败: {str(e)}"
            }
    
    async def update_all_stocks_cci(self) -> Dict[str, Any]:
        """一键更新所有股票的CCI指标值
        
        从stock_info集合获取所有股票列表，对每个股票：
        1. 检查technical_xx_123456集合是否存在，不存在则创建
        2. 查询最新CCI日期
        3. 更新从该日期到今日的CCI值
        
        Returns:
            包含更新结果的字典，包含成功和失败的统计信息
        """
        try:
            logger.info("开始批量更新所有股票的CCI指标")
            
            # 从stock_info集合获取所有股票列表
            stocks = await self.mongo_service.get_all_stocks()
            
            if not stocks:
                logger.warning("未从stock_info集合获取到股票数据")
                return {
                    "success": False,
                    "message": "未从stock_info集合获取到股票数据"
                }
            
            results = {
                'success_count': 0,
                'failed_count': 0,
                'total_count': len(stocks),
                'success_stocks': [],
                'failed_stocks': []
            }
            
            # 处理每个股票
            for stock in stocks:
                try:
                    # 获取股票代码
                    stock_code = stock.get('code', '')
                    if not stock_code:
                        logger.warning("跳过无效的股票数据（缺少code字段）")
                        continue
                    
                    logger.info(f"开始处理股票: {stock_code}")
                    
                    # 确保技术分析集合存在，如果不存在则创建
                    collection_ensured = await self.mongo_service.ensure_technical_collection_exists(stock_code)
                    if not collection_ensured:
                        logger.error(f"无法创建或访问股票 {stock_code} 的技术分析集合")
                        results['failed_count'] += 1
                        results['failed_stocks'].append({
                            'code': stock_code,
                            'error': '无法创建或访问技术分析集合'
                        })
                        continue
                    
                    # 获取该股票的最新技术分析日期
                    latest_tech_date = await self.mongo_service.get_latest_technical_date(stock_code)
                    
                    # 确定起始日期
                    if latest_tech_date:
                        start_date = latest_tech_date
                        logger.info(f"股票 {stock_code} 的最新CCI日期为 {start_date}")
                    else:
                        start_date = None  # 如果没有数据，则从最早的数据开始
                        logger.info(f"股票 {stock_code} 没有找到已有的CCI数据，将更新全部数据")
                    
                    # 构建日期范围参数
                    date_range = {
                        'start_date': start_date.strftime('%Y-%m-%d 00:00:00') if isinstance(start_date, datetime) else start_date,
                        'end_date': datetime.now().strftime('%Y-%m-%d 23:59:59')
                    }
                    
                    # 更新该股票的CCI值
                    result = await self.update_stock_cci(stock_code, date_range)
                    
                    if result.get('success'):
                        results['success_count'] += 1
                        results['success_stocks'].append({
                            'code': stock_code,
                            'updated_count': result.get('updated_count', 0)
                        })
                        logger.info(f"成功更新股票 {stock_code} 的CCI指标，更新了 {result.get('updated_count', 0)} 条记录")
                    else:
                        results['failed_count'] += 1
                        results['failed_stocks'].append({
                            'code': stock_code,
                            'error': result.get('message', 'Unknown error')
                        })
                        logger.warning(f"更新股票 {stock_code} 的CCI指标失败: {result.get('message')}")
                    
                except Exception as e:
                    stock_code = stock.get('code', 'Unknown')
                    logger.error(f"处理股票 {stock_code} 时出错: {str(e)}")
                    results['failed_count'] += 1
                    results['failed_stocks'].append({
                        'code': stock_code,
                        'error': str(e)
                    })
                    
            logger.info(f"批量更新所有股票的CCI指标完成，成功: {results['success_count']}, 失败: {results['failed_count']}, 总计: {results['total_count']}")
            return {
                "success": True,
                "message": f"批量更新完成，成功 {results['success_count']} 只股票，失败 {results['failed_count']} 只股票，总计 {results['total_count']} 只股票",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"批量更新所有股票的CCI指标时出错: {str(e)}")
            return {
                "success": False,
                "message": f"批量更新失败: {str(e)}"
            }

    async def update_all_stocks_indicators(self) -> Dict[str, Any]:
        """一键更新所有股票的所有技术指标值
        
        从stock_info集合获取所有股票列表，对每个股票：
        1. 检查technical_xx_123456集合是否存在，不存在则创建
        2. 查询最新技术指标日期
        3. 更新从该日期到今日的所有技术指标值
        
        Returns:
            包含更新结果的字典，包含成功和失败的统计信息
        """
        try:
            logger.info("开始批量更新所有股票的所有技术指标")
            
            # 从stock_info集合获取所有股票列表
            stocks = await self.mongo_service.get_all_stocks()
            
            if not stocks:
                logger.warning("未从stock_info集合获取到股票数据")
                return {
                    "success": False,
                    "message": "未从stock_info集合获取到股票数据"
                }
            
            results = {
                'success_count': 0,
                'failed_count': 0,
                'total_count': len(stocks),
                'success_stocks': [],
                'failed_stocks': []
            }
            
            # 分批处理股票，避免创建过多并发连接
            batch_size = 20  # 每批处理的股票数量
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i+batch_size]
                tasks = []
                
                # 为每个股票创建处理任务
                for stock in batch:
                    # 获取股票代码
                    stock_code = stock.get('code', '')
                    if not stock_code:
                        logger.warning("跳过无效的股票数据（缺少code字段）")
                        results['failed_count'] += 1
                        results['failed_stocks'].append({
                            'code': 'Unknown',
                            'error': '缺少code字段'
                        })
                        continue
                    
                    # 创建处理任务
                    task = asyncio.create_task(self._process_stock_for_update(stock_code))
                    tasks.append((stock_code, task))
                
                # 并行执行当前批次的任务
                for stock_code, task in tasks:
                    try:
                        result = await task
                        if result.get('success'):
                            results['success_count'] += 1
                            results['success_stocks'].append({
                                'code': stock_code,
                                'updated_count': result.get('updated_count', 0)
                            })
                            logger.info(f"成功更新股票 {stock_code} 的所有技术指标，更新了 {result.get('updated_count', 0)} 条记录")
                        else:
                            results['failed_count'] += 1
                            results['failed_stocks'].append({
                                'code': stock_code,
                                'error': result.get('message', 'Unknown error')
                            })
                            logger.warning(f"更新股票 {stock_code} 的所有技术指标失败: {result.get('message')}")
                    except Exception as e:
                        logger.error(f"处理股票 {stock_code} 时出错: {str(e)}")
                        results['failed_count'] += 1
                        results['failed_stocks'].append({
                            'code': stock_code,
                            'error': str(e)
                        })
                
                logger.info(f"已完成第 {i//batch_size + 1} 批股票处理，当前成功: {results['success_count']}, 失败: {results['failed_count']}")
                    
            logger.info(f"批量更新所有股票的所有技术指标完成，成功: {results['success_count']}, 失败: {results['failed_count']}, 总计: {results['total_count']}")
            return {
                "success": True,
                "message": f"批量更新完成，成功 {results['success_count']} 只股票，失败 {results['failed_count']} 只股票，总计 {results['total_count']} 只股票",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"批量更新所有股票的所有技术指标时出错: {str(e)}")
            return {
                "success": False,
                "message": f"批量更新失败: {str(e)}"
            }
    
    async def _process_stock_for_update(self, stock_code: str) -> Dict[str, Any]:
        """处理单个股票的更新操作"""
        try:
            logger.info(f"开始处理股票: {stock_code}")
            
            # 确保技术分析集合存在，如果不存在则创建
            collection_ensured = await self.mongo_service.ensure_technical_collection_exists(stock_code)
            if not collection_ensured:
                logger.error(f"无法创建或访问股票 {stock_code} 的技术分析集合")
                return {
                    "success": False,
                    "message": "无法创建或访问技术分析集合"
                }
            
            # 获取该股票的最新技术分析日期
            latest_tech_date = await self.mongo_service.get_latest_technical_date(stock_code)
            
            # 确定起始日期
            if latest_tech_date:
                start_date = latest_tech_date
                logger.info(f"股票 {stock_code} 的最新技术指标日期为 {start_date}")
            else:
                start_date = None  # 如果没有数据，则从最早的数据开始
                logger.info(f"股票 {stock_code} 没有找到已有的技术指标数据，将更新全部数据")
            
            # 构建日期范围参数
            date_range = {
                'start_date': start_date.strftime('%Y-%m-%d 00:00:00') if isinstance(start_date, datetime) else start_date,
                'end_date': datetime.now().strftime('%Y-%m-%d 23:59:59')
            }
            
            # 更新该股票的所有技术指标值
            result = await self.update_stock_indicators(stock_code, date_range)
            return result
            
        except Exception as e:
            logger.error(f"处理股票 {stock_code} 更新时出错: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

    async def evaluate_trading_strategy(self, stock_code: str, strategy: Dict[str, Any]) -> bool:
        """Evaluate if a stock meets trading strategy conditions"""
        try:
            # Get latest technical data
            collection_name = f"technical_{stock_code}"
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

    async def evaluate_right_side_trading_strategy(self, stock_code: str, params: Dict[str, Any] = None) -> bool:
        """Evaluate if a stock meets right side trading strategy conditions
        
        右侧交易策略是一种趋势跟踪策略，核心思想是在股价确认上涨趋势后买入，
        或在确认下跌趋势后卖出。这种策略追求的是顺势而为，减少逆势操作带来的风险。
        
        右侧交易策略条件：
        1. 价格突破关键阻力位（如前期高点、均线等）
        2. 成交量放大确认突破有效性
        3. 技术指标确认趋势方向（如CCI从-100以下向上突破）
        4. 可选：MA多头排列等确认趋势
        
        Args:
            stock_code: 股票代码
            params: 策略参数，包括：
                - breakout_threshold: 突破阈值，默认为0（表示突破前高）
                - volume_threshold: 成交量放大倍数，默认为1.5
                - cci_threshold: CCI阈值，默认为-100（CCI从-100以下向上突破）
                - ma_periods: 均线周期列表，默认为[5, 10, 20]
                
        Returns:
            bool: 是否满足右侧交易策略条件
        """
        try:
            if params is None:
                params = {}
            
            # 获取参数，默认值
            breakout_threshold = params.get('breakout_threshold', 0)  # 突破阈值
            volume_threshold = params.get('volume_threshold', 1.5)    # 成交量放大倍数
            cci_threshold = params.get('cci_threshold', -100)         # CCI阈值
            ma_periods = params.get('ma_periods', [5, 10, 20])        # 均线周期
            
            # 获取股票历史数据（包括价格、成交量等）
            historical_data = await self.mongo_service.get_stock_history(
                stock_code=stock_code,
                limit=30,  # 获取最近30天的数据
                sort="desc"
            )
            
            if not historical_data or len(historical_data) < max(ma_periods) + 2:
                return False
            
            # 转换为DataFrame并按日期排序
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # 计算均线
            for period in ma_periods:
                df[f'ma{period}'] = df['close'].rolling(window=period).mean()
            
            # 计算平均成交量（用于比较最近的成交量）
            avg_volume = df['volume'].rolling(window=10).mean()
            
            # 获取最新数据点
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # 条件1: 价格突破（收盘价突破前高或均线）
            price_breakout = False
            if breakout_threshold == 0:
                # 突破前高
                price_breakout = latest['close'] > df['high'].iloc[-6:-1].max() if len(df) >= 6 else False
            else:
                # 突破指定价格
                price_breakout = latest['close'] > breakout_threshold
            
            # 条件2: 成交量放大
            volume_amplified = latest['volume'] > (avg_volume.iloc[-1] * volume_threshold)
            
            # 条件3: CCI指标确认（从阈值以下向上突破）
            # 获取技术指标数据
            tech_collection = f"technical_{stock_code}"
            tech_data = await self.mongo_service.find(
                tech_collection,
                {'code': stock_code},
                sort=[('date', -1)],
                limit=2
            )
            
            cci_condition = False
            if len(tech_data) >= 2:
                current_cci = tech_data[0].get('cci', 0)
                previous_cci = tech_data[1].get('cci', 0)
                
                # CCI从阈值以下向上突破
                cci_condition = (previous_cci <= cci_threshold) and (current_cci > cci_threshold)
            
            # 条件4: 均线多头排列（可选）
            ma_alignment = True
            if len(ma_periods) >= 2:
                # 短期均线 > 长期均线
                ma_values = [latest[f'ma{period}'] for period in ma_periods if f'ma{period}' in latest and not pd.isna(latest[f'ma{period}'])]
                if len(ma_values) >= 2:
                    # 检查是否为递减序列（从短期到长期）
                    ma_alignment = all(ma_values[i] >= ma_values[i+1] for i in range(len(ma_values)-1))
            
            # 综合判断
            right_side_condition = price_breakout and volume_amplified and cci_condition and ma_alignment
            
            logger.info(f"Right side strategy for {stock_code}: "
                       f"price_breakout={price_breakout}, "
                       f"volume_amplified={volume_amplified}, "
                       f"cci_condition={cci_condition}, "
                       f"ma_alignment={ma_alignment}, "
                       f"result={right_side_condition}")
            
            return right_side_condition
            
        except Exception as e:
            logger.error(f"Error evaluating right side trading strategy for {stock_code}: {str(e)}")
            return False

    async def recompute_all_stocks_indicators(self) -> Dict[str, Any]:
        """重新计算所有股票的所有技术指标值（从头开始计算，不考虑最新日期）
        
        从stock_info集合获取所有股票列表，对每个股票：
        1. 检查technical_xx_123456集合是否存在，不存在则创建
        2. 删除所有现有技术指标数据
        3. 重新计算所有历史数据的技术指标值
        
        Returns:
            包含更新结果的字典，包含成功和失败的统计信息
        """
        try:
            logger.info("开始重新计算所有股票的所有技术指标")
            
            # 从stock_info集合获取所有股票列表
            stocks = await self.mongo_service.get_all_stocks()
            
            if not stocks:
                logger.warning("未从stock_info集合获取到股票数据")
                return {
                    "success": False,
                    "message": "未从stock_info集合获取到股票数据"
                }
            
            results = {
                'success_count': 0,
                'failed_count': 0,
                'total_count': len(stocks),
                'success_stocks': [],
                'failed_stocks': []
            }
            
            # 分批处理股票，避免创建过多并发连接
            batch_size = 20  # 每批处理的股票数量
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i+batch_size]
                tasks = []
                
                # 为每个股票创建处理任务
                for stock in batch:
                    # 获取股票代码
                    stock_code = stock.get('code', '')
                    if not stock_code:
                        logger.warning("跳过无效的股票数据（缺少code字段）")
                        results['failed_count'] += 1
                        results['failed_stocks'].append({
                            'code': 'Unknown',
                            'error': '缺少code字段'
                        })
                        continue
                    
                    # 创建处理任务
                    task = asyncio.create_task(self._process_stock_for_recompute(stock_code))
                    tasks.append((stock_code, task))
                
                # 并行执行当前批次的任务
                for stock_code, task in tasks:
                    try:
                        result = await task
                        if result.get('success'):
                            results['success_count'] += 1
                            results['success_stocks'].append({
                                'code': stock_code,
                                'updated_count': result.get('updated_count', 0)
                            })
                            logger.info(f"成功重新计算股票 {stock_code} 的所有技术指标，更新了 {result.get('updated_count', 0)} 条记录")
                        else:
                            results['failed_count'] += 1
                            results['failed_stocks'].append({
                                'code': stock_code,
                                'error': result.get('message', 'Unknown error')
                            })
                            logger.warning(f"重新计算股票 {stock_code} 的所有技术指标失败: {result.get('message')}")
                    except Exception as e:
                        logger.error(f"处理股票 {stock_code} 时出错: {str(e)}")
                        results['failed_count'] += 1
                        results['failed_stocks'].append({
                            'code': stock_code,
                            'error': str(e)
                        })
                
                logger.info(f"已完成第 {i//batch_size + 1} 批股票处理，当前成功: {results['success_count']}, 失败: {results['failed_count']}")
                    
            logger.info(f"重新计算所有股票的所有技术指标完成，成功: {results['success_count']}, 失败: {results['failed_count']}, 总计: {results['total_count']}")
            return {
                "success": True,
                "message": f"重新计算完成，成功 {results['success_count']} 只股票，失败 {results['failed_count']} 只股票，总计 {results['total_count']} 只股票",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"重新计算所有股票的所有技术指标时出错: {str(e)}")
            return {
                "success": False,
                "message": f"重新计算失败: {str(e)}"
            }
    
    async def _process_stock_for_recompute(self, stock_code: str) -> Dict[str, Any]:
        """处理单个股票的重新计算操作"""
        try:
            logger.info(f"开始处理股票: {stock_code}")
            
            # 确保技术分析集合存在，如果不存在则创建
            collection_ensured = await self.mongo_service.ensure_technical_collection_exists(stock_code)
            if not collection_ensured:
                logger.error(f"无法创建或访问股票 {stock_code} 的技术分析集合")
                return {
                    "success": False,
                    "message": "无法创建或访问技术分析集合"
                }
            
            # 删除该股票的所有现有技术指标数据
            tech_collection_name = self.mongo_service.get_technical_collection_name(stock_code)
            await self.mongo_service.db[tech_collection_name].delete_many({'code': stock_code})
            logger.info(f"已删除股票 {stock_code} 的所有现有技术指标数据")
            
            # 重新计算该股票的所有技术指标值（不提供日期范围，计算所有数据）
            result = await self.update_stock_indicators(stock_code)
            return result
            
        except Exception as e:
            logger.error(f"处理股票 {stock_code} 重新计算时出错: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

