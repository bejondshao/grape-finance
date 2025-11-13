#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MongoDB集合名称重命名脚本

功能：
1. 将所有 "technical_xx_123456" 格式的集合重命名为 "technical_xx.123456"
2. 将所有 "stock_daily_xx_123456" 格式的集合重命名为 "stock_daily_xx.123456"

使用说明：
1. 确保已安装Python和pymongo库：pip install pymongo
2. 可以通过环境变量配置MongoDB连接：
   - MONGO_URI: MongoDB连接字符串 (默认: mongodb://localhost:27017/)
   - MONGO_DB_NAME: 数据库名称 (默认: grape_finance)
3. 运行脚本：python rename_collections.py
4. 脚本会显示找到的符合条件的集合及其新名称，并要求确认后才执行重命名

注意：
- 使用前请确保已备份数据库！
- 脚本仅处理符合 "technical_xx_123456" 和 "stock_daily_xx_123456" 格式的集合
- "xx" 代表2个字母的前缀（如sh、sz）
- "123456" 代表6位或更多位的数字代码
"""

import os
import sys
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure


def connect_to_mongodb():
    """连接到MongoDB数据库"""
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    db_name = os.environ.get('MONGO_DB_NAME', 'grape_finance')
    
    try:
        print(f"正在连接到MongoDB: {mongo_uri}")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # 验证连接
        db = client[db_name]
        print(f"成功连接到数据库: {db_name}")
        return db
    except ConnectionFailure as e:
        print(f"MongoDB连接失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"连接数据库时发生错误: {e}")
        sys.exit(1)


def get_collections_to_rename(db):
    """找出所有需要重命名的集合"""
    collections = db.list_collection_names()
    collections_to_rename = []
    
    # 定义正则表达式模式
    technical_pattern = re.compile(r'^technical_([a-z]{2})_(\d{6,})$')
    stock_daily_pattern = re.compile(r'^stock_daily_([a-z]{2})_(\d{6,})$')
    
    for collection in collections:
        # 检查是否匹配technical模式
        tech_match = technical_pattern.match(collection)
        if tech_match:
            new_name = f"technical_{tech_match.group(1)}.{tech_match.group(2)}"
            collections_to_rename.append((collection, new_name))
            continue
            
        # 检查是否匹配stock_daily模式
        stock_match = stock_daily_pattern.match(collection)
        if stock_match:
            new_name = f"stock_daily_{stock_match.group(1)}.{stock_match.group(2)}"
            collections_to_rename.append((collection, new_name))
    
    return collections_to_rename


def rename_collections(db, collections_to_rename):
    """执行重命名操作"""
    renamed_count = 0
    failed_count = 0
    
    for old_name, new_name in collections_to_rename:
        try:
            db[old_name].rename(new_name)
            renamed_count += 1
            print(f"已重命名: {old_name} -> {new_name}")
        except OperationFailure as e:
            failed_count += 1
            print(f"重命名失败 {old_name} -> {new_name}: {e}")
        except Exception as e:
            failed_count += 1
            print(f"重命名时发生错误 {old_name} -> {new_name}: {e}")
    
    return renamed_count, failed_count


def main():
    """主函数"""
    print("="*70)
    print("MongoDB集合名称重命名工具")
    print("="*70)
    print("功能：将集合名称从 underscore 格式转换为 dot 格式")
    print("- technical_xx_123456 -> technical_xx.123456")
    print("- stock_daily_xx_123456 -> stock_daily_xx.123456")
    print("="*70)
    
    # 连接数据库
    db = connect_to_mongodb()
    
    # 找出需要重命名的集合
    collections_to_rename = get_collections_to_rename(db)
    
    if not collections_to_rename:
        print("未找到需要重命名的集合")
        sys.exit(0)
    
    print(f"找到 {len(collections_to_rename)} 个符合条件的集合:")
    print("-" * 50)
    for old_name, new_name in collections_to_rename:
        print(f"  {old_name} -> {new_name}")
    print("-" * 50)
    
    # 确认操作
    confirm = input("\n确认要执行这些重命名操作吗？(y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        sys.exit(0)
    
    # 执行重命名
    print("\n正在执行重命名操作...")
    renamed_count, failed_count = rename_collections(db, collections_to_rename)
    
    # 打印结果
    print("\n" + "="*70)
    print(f"重命名完成！")
    print(f"成功重命名: {renamed_count} 个集合")
    print(f"重命名失败: {failed_count} 个集合")
    print("="*70)


if __name__ == "__main__":
    main()