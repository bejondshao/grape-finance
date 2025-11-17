#!/usr/bin/env python3
"""
测试策略API功能
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_api_connection():
    """测试API连接"""
    try:
        response = requests.get(f"{BASE_URL}/trading-strategies/strategies")
        print(f"API连接测试: {response.status_code}")
        if response.status_code == 200:
            print("API连接成功")
            return True
        else:
            print(f"API连接失败: {response.text}")
            return False
    except Exception as e:
        print(f"API连接异常: {e}")
        return False

def test_filter_stocks():
    """测试股票筛选API"""
    try:
        response = requests.get(f"{BASE_URL}/trading-strategies/stocks/filter")
        print(f"股票筛选测试: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {data.get('count', 0)} 只股票")
            return True
        else:
            print(f"股票筛选失败: {response.text}")
            return False
    except Exception as e:
        print(f"股票筛选异常: {e}")
        return False

def test_manual_execute():
    """测试手动执行策略API"""
    try:
        params = {
            "strategy_type": "right_side",
            "stock_codes": [],  # 空列表表示执行所有股票
            "parameters": {
                "initial_capital": 100000,
                "max_position_pct": 0.02,
                "max_positions": 5
            }
        }
        response = requests.post(f"{BASE_URL}/trading-strategies/execute/manual", json=params)
        print(f"手动执行策略测试: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"执行结果: 处理了 {data.get('total_stocks', 0)} 只股票")
            print(f"成功数量: {len([r for r in data.get('results', []) if r.get('status') == 'success'])}")
            return True
        else:
            print(f"手动执行策略失败: {response.text}")
            return False
    except Exception as e:
        print(f"手动执行策略异常: {e}")
        return False

if __name__ == "__main__":
    print("开始测试策略API...")
    print("=" * 50)
    
    # 测试API连接
    if not test_api_connection():
        print("API连接失败，请检查后端服务是否启动")
        exit(1)
    
    print()
    
    # 测试股票筛选
    test_filter_stocks()
    print()
    
    # 测试手动执行策略
    test_manual_execute()
    print()
    
    print("=" * 50)
    print("测试完成")
