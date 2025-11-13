#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量删除MongoDB集合脚本

功能：删除所有以 'technical_sh_sh.' 或 'technical_sz_sz.' 开头的集合
注意：使用前请确保已备份重要数据！此操作不可逆！

使用说明：
1. 确保已安装Python和pymongo库：pip install pymongo
2. 可以通过环境变量配置MongoDB连接：
   - MONGO_URI: MongoDB连接字符串 (默认: mongodb://localhost:27017/)
   - MONGO_DB_NAME: 数据库名称 (默认: grape_finance)
3. 运行脚本：python delete_technical_collections.py
4. 脚本会显示找到的符合条件的集合，并要求确认后才执行删除

执行建议：
- 强烈建议在执行前备份MongoDB数据库
- 先在测试环境运行，确认脚本正常工作
- 仔细检查脚本显示的集合列表，确保没有误删重要数据
- 执行后验证是否所有目标集合已被删除
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


def connect_to_mongodb():
    """
    连接到MongoDB数据库
    尝试从环境变量获取连接信息，如果不存在则使用默认值
    """
    # 从环境变量获取MongoDB连接信息
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    db_name = os.environ.get('MONGO_DB_NAME', 'grape_finance')
    
    try:
        print(f"正在连接到MongoDB: {mongo_uri}")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # 验证连接
        client.server_info()
        db = client[db_name]
        print(f"成功连接到数据库: {db_name}")
        return db
    except ConnectionFailure as e:
        print(f"MongoDB连接失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"连接数据库时发生错误: {e}")
        sys.exit(1)


def delete_matching_collections(db):
    """
    删除所有匹配指定前缀的集合
    """
    # 定义要删除的集合前缀
    prefixes_to_delete = ['technical_sh_sh', 'technical_sz_sz', 'technical_sh_sz']
    
    try:
        # 获取所有集合列表
        collections = db.list_collection_names()
        print(f"数据库中共有 {len(collections)} 个集合")
        
        # 找出匹配的集合
        matching_collections = []
        for collection in collections:
            if any(collection.startswith(prefix) for prefix in prefixes_to_delete):
                matching_collections.append(collection)
        
        if not matching_collections:
            print("未找到需要删除的集合")
            return 0
        
        print(f"找到 {len(matching_collections)} 个符合条件的集合:")
        for i, collection in enumerate(matching_collections, 1):
            print(f"{i}. {collection}")
        
        # 确认删除
        confirm = input("\n确认要删除这些集合吗？(y/n): ")
        if confirm.lower() != 'y':
            print("操作已取消")
            return 0
        
        # 执行删除
        deleted_count = 0
        for collection in matching_collections:
            try:
                db.drop_collection(collection)
                deleted_count += 1
                print(f"已删除: {collection}")
            except Exception as e:
                print(f"删除集合 {collection} 时出错: {e}")
        
        print(f"\n删除操作完成，共删除 {deleted_count} 个集合")
        return deleted_count
        
    except Exception as e:
        print(f"操作过程中发生错误: {e}")
        return 0


def main():
    """
    主函数
    """
    print("="*60)
    print("MongoDB 集合批量删除工具")
    print("此工具将删除所有以 'technical_sh_sh.' 或 'technical_sz_sz.' 开头的集合")
    print("="*60)
    
    # 连接数据库
    db = connect_to_mongodb()
    
    # 删除匹配的集合
    delete_matching_collections(db)
    
    print("\n操作完成")


if __name__ == "__main__":
    main()