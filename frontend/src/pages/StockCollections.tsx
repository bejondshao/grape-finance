import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Input, 
  Button, 
  Space, 
  Tag, 
  message, 
  Statistic,
  Row,
  Col,
  Select,
  Progress
} from 'antd';
import { 
  SearchOutlined, 
  DeleteOutlined,
  LineChartOutlined,
  CalculatorOutlined 
} from '@ant-design/icons';
import { collectionAPI } from '../services/api';
import { StockCollection } from '../types';

const { Search } = Input;
const { Option } = Select;

const StockCollections: React.FC = () => {
  const [collections, setCollections] = useState<StockCollection[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    code: '',
    strategy: '',
    operation: '',
  });

  const columns = [
    {
      title: '股票代码',
      dataIndex: 'code',
      key: 'code',
      width: 100,
    },
    {
      title: '股票名称',
      dataIndex: 'code_name',
      key: 'code_name',
      width: 120,
      render: (name: string, record: StockCollection) => (
        <Space>
          <span>{name}</span>
          <Button 
            type="link" 
            icon={<LineChartOutlined />}
            size="small"
          >
            图表
          </Button>
        </Space>
      ),
    },
    {
      title: '策略',
      dataIndex: 'strategy_name',
      key: 'strategy_name',
      width: 150,
    },
    {
      title: '操作类型',
      dataIndex: 'operation',
      key: 'operation',
      width: 120,
      render: (operation: string) => {
        const colorMap: { [key: string]: string } = {
          '建仓': 'green',
          '加仓': 'blue',
          '减仓': 'orange',
          '清仓': 'red',
          '关注': 'purple',
          '持有': 'cyan',
        };
        return <Tag color={colorMap[operation] || 'default'}>{operation}</Tag>;
      },
    },
    {
      title: '触发价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price: number) => price.toFixed(2),
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 100,
      render: (price: number) => price ? price.toFixed(2) : '-',
    },
    {
      title: '收益',
      dataIndex: 'income',
      key: 'income',
      width: 100,
      render: (income: number) => {
        if (income === undefined || income === null) return '-';
        const color = income >= 0 ? '#cf1322' : '#3f8600';
        const icon = income >= 0 ? '↑' : '↓';
        return (
          <span style={{ color }}>
            {icon} {Math.abs(income).toFixed(2)}%
          </span>
        );
      },
    },
    {
      title: '触发日期',
      dataIndex: 'meet_date',
      key: 'meet_date',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '添加日期',
      dataIndex: 'added_date',
      key: 'added_date',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: StockCollection) => (
        <Space>
          <Button 
            type="link" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => removeFromCollection(record._id!)}
          >
            移除
          </Button>
        </Space>
      ),
    },
  ];

  const loadCollections = async () => {
    setLoading(true);
    try {
      const response = await collectionAPI.getCollections(filters);
      setCollections(response.data.collections);
    } catch (error) {
      message.error('加载收藏股票失败');
    } finally {
      setLoading(false);
    }
  };

  const removeFromCollection = async (id: string) => {
    try {
      await collectionAPI.removeFromCollection(id);
      message.success('移除成功');
      loadCollections();
    } catch (error) {
      message.error('移除失败');
    }
  };

  const calculateTotalIncome = () => {
    const validIncomes = collections
      .filter(c => c.income !== undefined && c.income !== null)
      .map(c => c.income!);
    
    if (validIncomes.length === 0) return 0;
    return validIncomes.reduce((sum, income) => sum + income, 0) / validIncomes.length;
  };

  useEffect(() => {
    loadCollections();
  }, [filters]);

  const totalIncome = calculateTotalIncome();

  return (
    <div>
      <Card>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Input
              placeholder="股票代码"
              value={filters.code}
              onChange={(e) => setFilters({ ...filters, code: e.target.value })}
            />
          </Col>
          <Col span={6}>
            <Input
              placeholder="策略名称"
              value={filters.strategy}
              onChange={(e) => setFilters({ ...filters, strategy: e.target.value })}
            />
          </Col>
          <Col span={6}>
            <Select
              placeholder="操作类型"
              style={{ width: '100%' }}
              value={filters.operation}
              onChange={(value) => setFilters({ ...filters, operation: value })}
              allowClear
            >
              <Option value="建仓">建仓</Option>
              <Option value="加仓">加仓</Option>
              <Option value="减仓">减仓</Option>
              <Option value="清仓">清仓</Option>
              <Option value="关注">关注</Option>
              <Option value="持有">持有</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Space>
              <Button 
                type="primary" 
                icon={<SearchOutlined />}
                onClick={loadCollections}
              >
                搜索
              </Button>
              <Button 
                icon={<CalculatorOutlined />}
                onClick={loadCollections}
              >
                计算收益
              </Button>
            </Space>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic 
                title="总股票数" 
                value={collections.length} 
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="平均收益" 
                value={totalIncome} 
                precision={2}
                suffix="%"
                valueStyle={{ color: totalIncome >= 0 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="盈利股票" 
                value={collections.filter(c => c.income && c.income > 0).length}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="亏损股票" 
                value={collections.filter(c => c.income && c.income < 0).length}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={collections}
          rowKey="_id"
          loading={loading}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  );
};

export default StockCollections;
