import React from 'react';
import { Form, Select, Spin, Button } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { stockService } from '../../services/api';

const StockSearch = ({ form, loading, searchResults, searchLoading, handleSearch, handleSelect, handleQuery }) => {
  return (
    <Form form={form} onFinish={handleQuery} layout="inline">
      <Form.Item name="stockCode" label="股票代码" rules={[{ required: true, message: '请输入股票代码' }]}>
        <Select
          showSearch
          placeholder="输入6位数字或拼音缩写搜索股票"
          style={{ width: 300 }}
          onSearch={handleSearch}
          onSelect={handleSelect}
          loading={searchLoading}
          optionFilterProp="children"
          filterOption={false}
          notFoundContent={searchLoading ? <Spin size="small" /> : null}
          allowClear
          onKeyDown={(e) => {
            // 当用户按下回车键时，如果输入的是6位数字，直接查询
            if (e.key === 'Enter') {
              const value = e.target.value;
              if (/^\d{6}$/.test(value)) {
                e.preventDefault();
                handleQuery({ stockCode: value });
              }
            }
          }}
        >
          {searchResults.map(stock => (
            <Select.Option key={stock.code} value={stock.code}>
              {stock.code} - {stock.code_name}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={loading}>
          查询
        </Button>
      </Form.Item>
    </Form>
  );
};

export default StockSearch;