import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Pattern
import re

import motor.motor_asyncio
from bson import ObjectId
from pymongo import UpdateOne, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class MongoDBService:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            "mongodb://localhost:27017/grape_finance"
        )
        self.db = self.client.grape_finance

    async def initialize_indexes(self):
        try:
            # Stock info indexes
            await self.db.stock_info.create_index([("code", ASCENDING)], unique=True)
            await self.db.stock_info.create_index([("updateTime", DESCENDING)])

            # Configuration indexes
            await self.db.configuration.create_index([
                ("category", ASCENDING),
                ("sub_category", ASCENDING),
                ("key", ASCENDING)
            ], unique=True)

            # Trading strategy indexes
            await self.db.trading_strategies.create_index([("name", ASCENDING)], unique=True)
            await self.db.trading_strategies.create_index([("is_active", ASCENDING)])

            # Stock collection indexes
            await self.db.stock_collections.create_index([
                ("code", ASCENDING),
                ("strategy_id", ASCENDING),
                ("added_date", DESCENDING)
            ])

            # Failed requests indexes
            await self.db.failed_requests.create_index([("retry_count", ASCENDING)])
            await self.db.failed_requests.create_index([("last_attempt", DESCENDING)])

            # Trading records indexes
            await self.db.trading_records.create_index([("code", ASCENDING)])
            await self.db.trading_records.create_index([("date", DESCENDING)])

            logger.info("Database indexes initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database indexes: {str(e)}")

    async def initialize_configurations(self):
        default_configs = [
            {
                "category": "scheduler",
                "sub_category": "data_fetch",
                "key": "start_date",
                "value": "1990-12-19",
                "description": "Default start date for historical data fetching"
            },
            {
                "category": "scheduler",
                "sub_category": "data_fetch",
                "key": "sleep_timer",
                "value": "1",
                "description": "Sleep timer between BaoStock API calls in seconds"
            },
            {
                "category": "trading",
                "sub_category": "tax_fee",
                "key": "stamp_duty_rate",
                "value": "0.0005",
                "description": "Stamp duty tax rate for selling stocks (0.05%)"
            },
            {
                "category": "technical",
                "sub_category": "cci",
                "key": "default_period",
                "value": "14",
                "description": "Default CCI period"
            },
            {
                "category": "technical",
                "sub_category": "cci",
                "key": "default_constant",
                "value": "0.015",
                "description": "Default CCI scaling constant"
            }
        ]

        for config in default_configs:
            try:
                await self.db.configuration.update_one(
                    {
                        "category": config["category"],
                        "sub_category": config["sub_category"],
                        "key": config["key"]
                    },
                    {"$setOnInsert": config},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error initializing config {config['key']}: {str(e)}")

    def covert_objectid_to_string(self, documents: List[Dict[str, Any]]) -> list[dict[str, Any]] | None:
        if documents:
            for document in documents:
            # Convert ObjectId to string
                if '_id' in document and isinstance(document['_id'], ObjectId):
                    document['_id'] = str(document['_id'])
                    for key, value in document.items():
                        if isinstance(value, ObjectId):
                            document[key] = str(value)
            return None
        else:
            return documents

    def convert_string_to_objectid(self, query: dict) -> None:
        # Convert _id string to ObjectId if present in query
        if '_id' in query and isinstance(query['_id'], str):
            try:
                query['_id'] = ObjectId(query['_id'])
            except:
                pass  # If it's not a valid ObjectId string, leave as is

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> bool:
        try:
            document["created_at"] = datetime.utcnow()
            result = await self.db[collection].insert_one(document)
            return result.acknowledged
        except PyMongoError as e:
            logger.error(f"Error inserting document into {collection}: {str(e)}")
            return False

    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> bool:
        try:
            for doc in documents:
                doc["created_at"] = datetime.utcnow()
            result = await self.db[collection].insert_many(documents)
            return result.acknowledged
        except PyMongoError as e:
            logger.error(f"Error inserting documents into {collection}: {str(e)}")
            return False

    async def find(self, collection: str, query: Dict[str, Any] = None,
                   projection: Dict[str, Any] = None, limit: int = 0,
                   sort: List[tuple] = None) -> List[Dict[str, Any]]:
        try:
            cursor = self.db[collection].find(query or {}, projection or {})

            if sort:
                cursor = cursor.sort(sort)
            if limit > 0:
                cursor = cursor.limit(limit)

            documents = await cursor.to_list(length=None)
            self.covert_objectid_to_string(documents)
            return documents
        except PyMongoError as e:
            logger.error(f"Error finding documents in {collection}: {str(e)}")
            return []

    async def find_one(self, collection: str, query: Dict[str, Any],
                       sort: List[tuple] = None) -> Optional[Dict[str, Any]]:
        try:
            if sort:
                cursor = self.db[collection].find(query).sort(sort).limit(1)
                documents = await cursor.to_list(length=1)
                return documents[0] if documents else None
            else:
                document = await self.db[collection].find_one(query)
                return document
        except PyMongoError as e:
            logger.error(f"Error finding one document in {collection}: {str(e)}")
            return None

    async def update_one(self, collection: str, query: Dict[str, Any],
                         update: Dict[str, Any]) -> bool:
        try:
            if "$set" in update:
                update["$set"]["updated_at"] = datetime.utcnow()
            else:
                update["$set"] = {"updated_at": datetime.utcnow()}
            self.convert_string_to_objectid(query)
            result = await self.db[collection].update_one(query, update)
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating document in {collection}: {str(e)}")
            return False

    async def update_many(self, collection: str, query: Dict[str, Any],
                          update: Dict[str, Any]) -> int:
        try:
            if "$set" in update:
                update["$set"]["updated_at"] = datetime.utcnow()
            self.convert_string_to_objectid(query)
            result = await self.db[collection].update_many(query, update)
            return result.modified_count
        except PyMongoError as e:
            logger.error(f"Error updating documents in {collection}: {str(e)}")
            return 0

    async def bulk_write(self, collection: str, operations: List[UpdateOne]) -> bool:
        try:
            result = await self.db[collection].bulk_write(operations)
            return result.acknowledged
        except PyMongoError as e:
            logger.error(f"Error in bulk write operation for {collection}: {str(e)}")
            return False

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        try:
            self.convert_string_to_objectid(query)
            result = await self.db[collection].delete_one(query)
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting document from {collection}: {str(e)}")
            return False
    
    async def count_documents(self, collection: str, query: Dict[str, Any] = None) -> int:
        """统计集合中的文档数量"""
        try:
            # 检查集合是否存在
            if collection not in await self.db.list_collection_names():
                return 0
            
            # 转换ObjectId字符串
            if query:
                self.convert_string_to_objectid(query)
            
            # 执行计数
            count = await self.db[collection].count_documents(query or {})
            return count
        except PyMongoError as e:
            logger.error(f"Error counting documents in {collection}: {str(e)}")
            return 0

    async def get_config_value(self, category: str, sub_category: str, key: str,
                               default: Any = None) -> Any:
        try:
            config = await self.db.configuration.find_one({
                "category": category,
                "sub_category": sub_category,
                "key": key
            })
            return config.get("value", default) if config else default
        except PyMongoError as e:
            logger.error(f"Error getting config value {category}.{sub_category}.{key}: {str(e)}")
            return default

    async def set_config_value(self, category: str, sub_category: str, key: str,
                               value: Any, description: str = None) -> bool:
        try:
            update_data = {
                "category": category,
                "sub_category": sub_category,
                "key": key,
                "value": value,
                "updated_at": datetime.utcnow()
            }
            if description:
                update_data["description"] = description

            result = await self.db.configuration.update_one(
                {
                    "category": category,
                    "sub_category": sub_category,
                    "key": key
                },
                {"$set": update_data},
                upsert=True
            )
            return result.acknowledged
        except PyMongoError as e:
            logger.error(f"Error setting config value {category}.{sub_category}.{key}: {str(e)}")
            return False

    def get_collection_name(self, stock_code: str) -> str:

        return f"stock_daily_{stock_code}"

    def parse_collection_name(self, collection_name: str) -> Dict[str, str]:
        """解析表名，提取市场信息和股票代码"""
        pattern: Pattern = r"stock_daily_([a-z]{2})_(\d+)"
        match = re.match(pattern, collection_name)
        if match:
            return {
                "market": match.group(1),
                "code": match.group(2)
            }
        return {}

    async def get_stock_history(
            self,
            stock_code: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            limit: int = 100,
            skip: int = 0,
            sort: str = "desc",
            fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """获取单个股票的历史数据"""
        collection_name = self.get_collection_name(stock_code)

        # 跳过集合存在性检查，直接查询数据
        # 这样可以避免list_collection_names()无法正确识别包含.的集合名称的问题

        collection = self.db[collection_name]

        # 构建查询条件
        query = {}
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                # 将字符串日期转换为datetime类型
                if isinstance(start_date, str):
                    try:
                        # 尝试解析带时间的格式
                        query['date']['$gte'] = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # 解析不带时间的格式
                        query['date']['$gte'] = datetime.strptime(start_date, "%Y-%m-%d")
                else:
                    # 检查是否为Timestamp对象并转换为datetime
                    if hasattr(start_date, 'to_pydatetime'):
                        query['date']['$gte'] = start_date.to_pydatetime()
                    else:
                        query['date']['$gte'] = start_date
            if end_date:
                # 将字符串日期转换为datetime类型
                if isinstance(end_date, str):
                    try:
                        # 尝试解析带时间的格式
                        query['date']['$lte'] = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # 解析不带时间的格式
                        query['date']['$lte'] = datetime.strptime(end_date, "%Y-%m-%d")
                else:
                    # 检查是否为Timestamp对象并转换为datetime
                    if hasattr(end_date, 'to_pydatetime'):
                        query['date']['$lte'] = end_date.to_pydatetime()
                    else:
                        query['date']['$lte'] = end_date

        # 构建投影
        projection = None
        if fields:
            projection = {field: 1 for field in fields}
            projection['_id'] = 0  # 总是排除_id

        # 排序方向
        sort_direction = DESCENDING if sort == "desc" else ASCENDING

        try:
            # 执行查询
            cursor = collection.find(query, projection).sort('date', sort_direction).skip(skip).limit(limit)
            results = await cursor.to_list(length=None)

            # 移除内部字段
            for doc in results:
                doc.pop('_id', None)
                doc.pop('created_at', None)

            return results
        except PyMongoError as e:
            logger.error(f"Error fetching stock history for {stock_code}: {str(e)}")
            return []
    
    async def get_all_stocks(self) -> List[Dict[str, Any]]:
        """
        从stock_info集合获取所有股票列表
        
        Returns:
            List[Dict]: 包含股票基本信息的列表，每个元素包含code字段
        """
        try:
            # 检查stock_info集合是否存在
            if 'stock_info' not in await self.db.list_collection_names():
                logger.warning("Collection stock_info does not exist")
                return []
            
            # 投影只获取code字段
            projection = {"code": 1, "_id": 0}
            
            # 查询所有股票信息
            stocks = await self.db.stock_info.find({}, projection).to_list(length=None)
            
            return stocks
        except PyMongoError as e:
            logger.error(f"Error fetching all stocks from stock_info: {str(e)}")
            return []
    
    def get_technical_collection_name(self, stock_code: str) -> str:
        """
        根据股票代码生成技术分析集合名称
        
        Args:
            stock_code: 股票代码
        
        Returns:
            str: 技术分析集合名称 (格式: technical_xx.123456)
        """
        # Normalize to lowercase for consistent case handling with stored codes
        # 注意：永远不要使用replace('.', '_')处理股票代码
        stock_code = stock_code.lower()
        return f"technical_{stock_code}"
    
    async def ensure_technical_collection_exists(self, stock_code: str) -> bool:
        """
        确保技术分析集合存在，如果不存在则创建
        
        Args:
            stock_code: 股票代码
            
        Returns:
            bool: 操作是否成功
        """
        try:
            collection_name = self.get_technical_collection_name(stock_code)
            
            # 检查集合是否存在
            if collection_name not in await self.db.list_collection_names():
                # 创建新集合
                await self.db.create_collection(collection_name)
                # 添加日期索引
                await self.db[collection_name].create_index([("date", ASCENDING)], unique=True)
                logger.info(f"Created technical analysis collection: {collection_name}")
            
            return True
        except PyMongoError as e:
            logger.error(f"Error ensuring technical collection for {stock_code}: {str(e)}")
            return False
    
    async def get_latest_technical_date(self, stock_code: str) -> Optional[str]:
        """
        获取股票技术分析集合中的最新日期
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Optional[str]: 最新日期字符串，如果集合不存在或为空则返回None
        """
        try:
            collection_name = self.get_technical_collection_name(stock_code)
            logger.debug(f"Getting latest technical date for {stock_code}, collection: {collection_name}")
            
            # 查询最新的日期
            latest = await self.db[collection_name].find_one(
                {}, 
                projection={"date": 1, "_id": 0}, 
                sort=[("date", DESCENDING)]
            )
            
            if latest:
                date_str = latest.get("date").strftime("%Y-%m-%d %H:%M:%S") if latest.get("date") else None
                logger.debug(f"Latest technical date for {stock_code}: {date_str}")
                return date_str
            logger.debug(f"No latest technical date found for {stock_code}")
            return None
        except PyMongoError as e:
            logger.error(f"Error getting latest technical date for {stock_code}: {str(e)}")
            return None
    
    async def get_latest_complete_technical_date(self, stock_code: str) -> Optional[str]:
        """
        获取股票技术分析集合中的最新完整数据日期（所有指标都存在的日期）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Optional[str]: 最新完整数据日期字符串，如果集合不存在或为空则返回None
        """
        try:
            collection_name = self.get_technical_collection_name(stock_code)
            logger.debug(f"Getting latest complete technical date for {stock_code}, collection: {collection_name}")
            
            # 查询最新的日期，确保所有技术指标都存在
            query = {
                "cci": {"$exists": True, "$ne": None},
                "rsi": {"$exists": True, "$ne": None},
                "macd_line": {"$exists": True, "$ne": None},
                "macd_signal": {"$exists": True, "$ne": None},
                "macd_histogram": {"$exists": True, "$ne": None},
                "kdj_k": {"$exists": True, "$ne": None},
                "kdj_d": {"$exists": True, "$ne": None},
                "kdj_j": {"$exists": True, "$ne": None},
                "bb_upper": {"$exists": True, "$ne": None},
                "bb_middle": {"$exists": True, "$ne": None},
                "bb_lower": {"$exists": True, "$ne": None}
            }
            
            latest = await self.db[collection_name].find_one(
                query,
                projection={"date": 1, "_id": 0}, 
                sort=[("date", DESCENDING)]
            )
            
            if latest:
                date_str = latest.get("date").strftime("%Y-%m-%d %H:%M:%S") if latest.get("date") else None
                logger.debug(f"Latest complete technical date for {stock_code}: {date_str}")
                return date_str
            logger.debug(f"No latest complete technical date found for {stock_code}")
            return None
        except PyMongoError as e:
            logger.error(f"Error getting latest complete technical date for {stock_code}: {str(e)}")
            return None