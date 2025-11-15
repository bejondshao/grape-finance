import tushare as ts
import pandas as pd

# 设置TuShare的token
# 请替换为你的实际token
TOKEN = "your_token_here"
ts.set_token(TOKEN)

# 初始化pro接口
pro = ts.pro_api()

def test_stock_basic():
    """测试获取股票列表数据"""
    try:
        # 调用stock_basic接口获取股票基本信息
        df = pro.stock_basic(
            exchange='', 
            list_status='L'
        )
        
        print("股票基本信息获取成功!")
        print(f"总共获取到 {len(df)} 只股票")
        print("\n前10只股票信息:")
        print(df.head(10))
        
        # 保存到CSV文件
        df.to_csv('stock_basic.csv', index=False, encoding='utf-8-sig')
        print("\n数据已保存到 stock_basic.csv 文件")
        
        return df
    except Exception as e:
        print(f"获取股票基本信息时出错: {e}")
        return None

def test_stock_company_info():
    """测试获取上市公司基本信息"""
    try:
        # 一次性获取所有上市公司的详细信息
        company_df = pro.stock_company(**{
            "ts_code": "",
            "exchange": "",
            "status": "",
            "limit": "",
            "offset": ""
        })
        
        print("\n上市公司基本信息获取成功!")
        print(f"总共获取到 {len(company_df)} 家公司的详细信息")
        print("\n前5家公司的信息:")
        print(company_df.head())
        
        # 保存到CSV文件
        company_df.to_csv('stock_company_info.csv', index=False, encoding='utf-8-sig')
        print("\n数据已保存到 stock_company_info.csv 文件")
        
        return company_df
            
    except Exception as e:
        print(f"获取上市公司基本信息时出错: {e}")
        return None

def convert_ts_code(ts_code: str) -> str:
    """将TuShare ts_code格式(123456.SH)转换为标准格式(sh.123456)"""
    if '.' in ts_code:
        parts = ts_code.split('.')
        code = parts[0]
        market = parts[1].lower()
        return f"{market}.{code}"
    return ts_code

def test_combined_data():
    """测试组合数据：股票基本信息+转换后的code字段"""
    try:
        # 获取股票基本信息
        df = pro.stock_basic(exchange='', list_status='L')
        
        # 添加转换后的code列
        df['code'] = df['ts_code'].apply(convert_ts_code)
        
        print("组合数据获取成功!")
        print(f"总共获取到 {len(df)} 只股票")
        print("\n包含转换后code列的前10只股票信息:")
        print(df[['ts_code', 'code', 'name', 'symbol']].head(10))
        
        # 保存到CSV文件
        df.to_csv('combined_stock_data.csv', index=False, encoding='utf-8-sig')
        print("\n数据已保存到 combined_stock_data.csv 文件")
        
        return df
    except Exception as e:
        print(f"获取组合数据时出错: {e}")
        return None

if __name__ == "__main__":
    print("请将脚本中的 TOKEN 替换为你在 TuShare 官网申请的有效 token")
    print("可以从 https://tushare.pro/register?reg=123213 免费注册获取")