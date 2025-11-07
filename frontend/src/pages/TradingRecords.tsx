import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Form, 
  Input, 
  Button, 
  Select, 
  DatePicker, 
  Space, 
  message, 
  Modal,
  Statistic,
  Row,
  Col,
  Tag
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined,
  CalculatorOutlined 
} from '@ant-design/icons';
import { tradingRecordAPI } from '../services/api';
import { TradingRecord } from '../types';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

const TradingRecords: React.FC = () => {
  const [form] = Form.useForm();
  const [records, setRecords] = useState<TradingRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<TradingRecord | null>(null);

  const columns = [
    {
      title: '账户',
      dataIndex: 'account',
      key: 'account',
      width: 100,
    },
    {
      title: '股票代码',
      dataIndex: 'code',
      key: 'code',
      width: 100,
    },
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
      width: 100,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: 'buy' | 'sell') => (
        <Tag color={type === 'buy' ? 'green' : 'red'}>
          {type === 'buy' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price: number) => price.toFixed(2),
    },
    {
      title: '数量',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
    },
    {
      title: '金额',
      key: 'total',
      width: 120,
      render: (_: any, record: TradingRecord) => (
        <span>{(record.price * record.amount).toFixed(2)}</span>
      ),
    },
    {
      title: '收益',
      dataIndex: 'profit',
      key: 'profit',
      width: 100,
      render: (profit: number) => {
        if (profit === undefined || profit === null) return '-';
        const color = profit >= 0 ? '#cf1322' : '#3f8600';
        return (
          <span style={{ color }}>
            {profit >= 0 ? '+' : ''}{profit.toFixed(2)}
          </span>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: TradingRecord) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />}
            onClick={() => editRecord(record)}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => deleteRecord(record._id!)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const loadRecords = async () => {
    setLoading(true);
    try {
      const response = await tradingRecordAPI.getRecords();
      setRecords(response.data.records);
    } catch (error) {
      message.error('加载交易记录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingRecord) {
        await tradingRecordAPI.updateRecord(editingRecord._id!, values);
        message.success('记录更新成功');
      } else {
        await tradingRecordAPI.createRecord(values);
        message.success('记录创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingRecord(null);
      loadRecords();
    } catch (error) {
      message.error(editingRecord ? '更新记录失败' : '创建记录失败');
    }
  };

  const editRecord = (record: TradingRecord) => {
    setEditingRecord(record);
    form.setFieldsValue({
      ...record,
      date: record.date ? dayjs(record.date) : null,
    });
    setModalVisible(true);
  };

  const deleteRecord = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条交易记录吗？',
      onOk: async () => {
        try {
          await tradingRecordAPI.deleteRecord(id);
          message.success('删除成功');
          loadRecords();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const calculateStats = () => {
    const totalProfit = records
      .filter(r => r.profit !== undefined && r.profit !== null)
      .reduce((sum, r) => sum + r.profit!, 0);
    
    const totalTrades = records.length;
    const winningTrades = records.filter(r => r.profit && r.profit > 0).length;
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;

    return { totalProfit, totalTrades, winRate };
  };

  useEffect(() => {
    loadRecords();
  }, []);

  const { totalProfit, totalTrades, winRate } = calculateStats();

  return (
    <div>
      <Card
        title="交易记录"
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            新建记录
          </Button>
        }
      >
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic 
                title="总交易次数" 
                value={totalTrades} 
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="总收益" 
                value={totalProfit} 
                precision={2}
                valueStyle={{ color: totalProfit >= 0 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="胜率" 
                value={winRate} 
                precision={1}
                suffix="%"
                valueStyle={{ color: winRate >= 50 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="盈利交易" 
                value={records.filter(r => r.profit && r.profit > 0).length}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={records}
          rowKey="_id"
          loading={loading}
          scroll={{ x: 1000 }}
        />
      </Card>

      <Modal
        title={editingRecord ? '编辑交易记录' : '新建交易记录'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingRecord(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="account"
                label="交易账户"
                rules={[{ required: true, message: '请输入交易账户' }]}
              >
                <Input placeholder="输入交易账户" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="code"
                label="股票代码"
                rules={[{ required: true, message: '请输入股票代码' }]}
              >
                <Input placeholder="例如：sh.600000" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="date"
                label="交易日期"
                rules={[{ required: true, message: '请选择交易日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="time"
                label="交易时间"
                rules={[{ required: true, message: '请输入交易时间' }]}
              >
                <Input placeholder="例如：09:30" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="type"
                label="交易类型"
                rules={[{ required: true, message: '请选择交易类型' }]}
              >
                <Select>
                  <Option value="buy">买入</Option>
                  <Option value="sell">卖出</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="price"
                label="价格"
                rules={[{ required: true, message: '请输入价格' }]}
              >
                <Input type="number" step="0.01" placeholder="交易价格" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="amount"
                label="数量"
                rules={[{ required: true, message: '请输入数量' }]}
              >
                <Input type="number" placeholder="交易数量" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="reason"
            label="交易原因"
            rules={[{ required: true, message: '请输入交易原因' }]}
          >
            <TextArea rows={3} placeholder="说明买入或卖出的原因" />
          </Form.Item>

          <Form.Item
            name="trading_plan"
            label="后续计划"
          >
            <TextArea rows={2} placeholder="后续的交易计划" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingRecord ? '更新记录' : '创建记录'}
              </Button>
              <Button onClick={() => {
                setModalVisible(false);
                setEditingRecord(null);
                form.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TradingRecords;
