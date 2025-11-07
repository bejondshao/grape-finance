import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Input, 
  Button, 
  Space, 
  Tag, 
  message, 
  Spin,
  Select,
  Row,
  Col,
  Statistic,
  Progress
} from 'antd';
import { 
  SearchOutlined, 
  ReloadOutlined, 
  DownloadOutlined,
  LineChartOutlined 
} from '@ant-design/icons';
import { stockAPI } from '../services/api';
import { Stock } from '../types';

const { Search } = Input;
const { Option } = Select;

const Stocks: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });
  const [filters, setFilters] = useState({
    code: '',
    name: '',
    type: '',
  });

  const columns = [
    {
      title: '股票代码',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: '股票名称',
      dataIndex: 'code_name',
      key: 'code_name',
      width: 150,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => {
        const typeMap: { [key: string]: { color: string; text: string } } = {
          '1': { color: 'blue', text: '上证' },
          '2': { color: 'green', text: '深证' },
          '3': { color: 'orange', text: '创业板' },
        };
        const info = typeMap[type] || { color: 'default', text: type };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '交易状态',
      dataIndex: 'tradeStatus',
      key: 'tradeStatus',
      width: 100,
      render: (status: string) => (
        <Tag color={status === '1' ? 'green' : 'red'}>
          {status === '1' ? '交易' : '停牌'}
        </Tag>
      ),
    },
    {
      title: '上市日期',
      dataIndex: 'ipoDate',
      key: 'ipoDate',
      width: 120,
    },
    {
      title: '更新时间',
      dataIndex: 'updateTime',
      key: 'updateTime',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: Stock) => (
        <Space size="small">
          <Button 
            type="link" 
            icon={<LineChartOutlined />}
            onClick={() => viewStockDetails(record)}
          >
            详情
          </Button>
          <Button 
            type="link" 
            onClick={() => fetchStockData(record.code)}
          >
            更新数据
          </Button>
        </Space>
      ),
    },
  ];

  const loadStocks = async (page = 1, pageSize = 50) => {
    setLoading(true);
    try {
      const response = await stockAPI.getStocks({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...filters,
      });
      setStocks(response.data.stocks);
      setPagination({
        current: page,
        pageSize,
        total: response.data.total,
      });
    } catch (error) {
      message.error('加载股票列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (values: any) => {
    setFilters(values);
    loadStocks(1, pagination.pageSize);
  };

  const handleTableChange = (newPagination: any) => {
    loadStocks(newPagination.current, newPagination.pageSize);
  };

  const triggerDataFetch = async () => {
    setFetching(true);
    try {
      const response = await stockAPI.triggerDataFetch();
      message.success(response.data.message);
      // Poll for progress (you might want to implement WebSocket for real progress)
      setTimeout(() => {
        loadStocks();
        setFetching(false);
      }, 5000);
    } catch (error) {
      message.error('触发数据更新失败');
      setFetching(false);
    }
  };

  const fetchStockData = async (code: string) => {
    try {
      await stockAPI.getStockDailyData(code);
      message.success(`开始更新 ${code} 的数据`);
    } catch (error) {
      message.error(`更新 ${code} 数据失败`);
    }
  };

  const viewStockDetails = (stock: Stock) => {
    // Navigate to stock detail page or show modal
    message.info(`查看 ${stock.code_name} 的详细信息`);
  };

  useEffect(() => {
    loadStocks();
  }, []);

  return (
    <div>
      <Card>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Input
              placeholder="股票代码"
              value={filters.code}
              onChange={(e) => setFilters({ ...filters, code: e.target.value })}
              onPressEnter={() => handleSearch(filters)}
            />
          </Col>
          <Col span={6}>
            <Input
              placeholder="股票名称"
              value={filters.name}
              onChange={(e) => setFilters({ ...filters, name: e.target.value })}
              onPressEnter={() => handleSearch(filters)}
            />
          </Col>
          <Col span={6}>
            <Select
              placeholder="股票类型"
              style={{ width: '100%' }}
              value={filters.type}
              onChange={(value) => setFilters({ ...filters, type: value })}
              allowClear
            >
              <Option value="1">上证</Option>
              <Option value="2">深证</Option>
              <Option value="3">创业板</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Space>
              <Button 
                type="primary" 
                icon={<SearchOutlined />}
                onClick={() => handleSearch(filters)}
              >
                搜索
              </Button>
              <Button 
                icon={<ReloadOutlined />}
                onClick={() => {
                  setFilters({ code: '', name: '', type: '' });
                  loadStocks(1, pagination.pageSize);
                }}
              >
                重置
              </Button>
            </Space>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Card>
              <Statistic title="股票总数" value={pagination.total} />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic title="上证股票" 
                value={stocks.filter(s => s.type === '1').length} 
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Statistic title="数据状态" value="实时" />
                <Button 
                  type="primary" 
                  icon={<DownloadOutlined />}
                  loading={fetching}
                  onClick={triggerDataFetch}
                >
                  立即更新
                </Button>
              </div>
              {fetching && (
                <Progress percent={50} status="active" style={{ marginTop: 8 }} />
              )}
            </Card>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={stocks}
          rowKey="code"
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );
};

export default Stocks;
