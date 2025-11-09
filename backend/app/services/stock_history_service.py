from pymongo import MongoClient, ASCENDING, DESCENDING
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import asyncio
import re


class StockHistoryService:
    def __init__(self, db_uri: str, db_name: str):
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]

    def get_collection_name(self, stock_code: str) -> str:
        """根据股票代码生成表名"""
        # 解析股票代码中的市场信息
        if stock_code.startswith('6') or stock_code.startswith('8'):
            market = 'sh'  # 上海
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            market = 'sz'  # 深圳
        elif stock_code.startswith('9') or stock_code.startswith('4'):
            market = 'bj'  # 北京
        else:
            market = 'sh'  # 其他

        return f"stock_daily_{market}_{stock_code}"

    def parse_collection_name(self, collection_name: str) -> Dict[str, str]:
        """解析表名，提取市场信息和股票代码"""
        pattern = r"stock_daily_([a-z]{2})_(\d+)"
        match = re.match(pattern, collection_name)
        if match:
            return {
                "market": match.group(1),
                "code": match.group(2)
            }
        return {}

    async def get_all_stock_collections(self) -> List[Dict]:
        """获取所有股票数据表的信息"""
        collections = self.db.list_collection_names()
        stock_collections = []

        for coll_name in collections:
            if coll_name.startswith("stock_daily_"):
                info = self.parse_collection_name(coll_name)
                if info:
                    stock_collections.append({
                        "collection_name": coll_name,
                        "market": info["market"],
                        "code": info["code"],
                        "full_code": f"{info['market'].upper()}{info['code']}"
                    })

        return stock_collections

    async def save_stock_data(self, stock_code: str, data: List[Dict]):
        """保存股票历史数据到对应表"""
        collection_name = self.get_collection_name(stock_code)
        collection = self.db[collection_name]

        # 添加时间戳和索引
        for record in data:
            record['created_at'] = datetime.now()
            record['date_str'] = record['date']  # 保持日期字符串格式

        # 创建索引
        await collection.create_index([("date", ASCENDING)], unique=True)
        await collection.create_index([("code", ASCENDING)])

        # 批量插入或更新
        for record in data:
            await collection.update_one(
                {"date": record["date"]},
                {"$set": record},
                upsert=True
            )

        return len(data)

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

        # 检查集合是否存在
        if collection_name not in await self.db.list_collection_names():
            return []

        collection = self.db[collection_name]

        # 构建查询条件
        query = {}
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                query['date']['$gte'] = start_date
            if end_date:
                query['date']['$lte'] = end_date

        # 构建投影
        projection = None
        if fields:
            projection = {field: 1 for field in fields}
            projection['_id'] = 0  # 总是排除_id

        # 排序方向
        sort_direction = DESCENDING if sort == "desc" else ASCENDING

        # 执行查询
        cursor = collection.find(query, projection).sort('date', sort_direction).skip(skip).limit(limit)

        results = list(cursor)

        # 移除内部字段
        for doc in results:
            doc.pop('_id', None)
            doc.pop('created_at', None)

        return results

    async def search_stocks_by_market(
            self,
            market: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            limit_per_stock: int = 10
    ) -> Dict[str, List[Dict]]:
        """按市场搜索股票数据"""
        collections = await self.get_all_stock_collections()
        market_collections = [c for c in collections if c["market"] == market.lower()]

        tasks = []
        stock_codes = []

        for coll_info in market_collections:
            task = self.get_stock_history(
                stock_code=coll_info["code"],
                start_date=start_date,
                end_date=end_date,
                limit=limit_per_stock
            )
            tasks.append(task)
            stock_codes.append(coll_info["full_code"])

        # 并发执行所有查询
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 组织结果
        response = {}
        for code, result in zip(stock_codes, results):
            if isinstance(result, Exception):
                response[code] = {"error": str(result)}
            else:
                response[code] = result

        return response

    async def search_stocks_by_codes(
            self,
            stock_codes: List[str],
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            limit_per_stock: int = 50
    ) -> Dict[str, List[Dict]]:
        """按股票代码列表搜索"""
        tasks = []
        processed_codes = []

        for code in stock_codes:
            # 处理带市场前缀的代码 (如 SH600123) 或纯数字代码
            if code[:2].isalpha() and code[2:].isdigit():
                # 格式: SH600123 -> 提取 600123
                pure_code = code[2:]
            else:
                pure_code = code

            task = self.get_stock_history(
                stock_code=pure_code,
                start_date=start_date,
                end_date=end_date,
                limit=limit_per_stock
            )
            tasks.append(task)
            processed_codes.append(code)

        # 并发执行所有查询
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 组织结果
        response = {}
        for code, result in zip(processed_codes, results):
            if isinstance(result, Exception):
                response[code] = {"error": str(result)}
            elif not result:
                response[code] = {"error": "未找到数据"}
            else:
                response[code] = result

        return response

    async def get_stock_info(self, stock_code: str) -> Dict:
        """获取股票基本信息"""
        collection_name = self.get_collection_name(stock_code)

        if collection_name not in await self.db.list_collection_names():
            return {"error": "股票不存在"}

        collection = self.db[collection_name]

        # 获取最新数据
        latest = await collection.find_one({}, sort=[('date', DESCENDING)])
        # 获取最早数据
        earliest = await collection.find_one({}, sort=[('date', ASCENDING)])
        # 获取数据总数
        total_count = await collection.count_documents({})

        info = self.parse_collection_name(collection_name)

        return {
            "code": stock_code,
            "market": info.get("market", "").upper(),
            "full_code": f"{info.get('market', '').upper()}{stock_code}",
            "data_range": {
                "start_date": earliest["date"] if earliest else None,
                "end_date": latest["date"] if latest else None
            },
            "total_records": total_count,
            "latest_data": {
                "date": latest["date"] if latest else None,
                "close": latest["close"] if latest else None
            } if latest else None
        }