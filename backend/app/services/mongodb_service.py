import motor.motor_asyncio
from pymongo import UpdateOne, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

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
            return documents
        except PyMongoError as e:
            logger.error(f"Error finding documents in {collection}: {str(e)}")
            return []
    
    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
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
            result = await self.db[collection].delete_one(query)
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting document from {collection}: {str(e)}")
            return False
    
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
