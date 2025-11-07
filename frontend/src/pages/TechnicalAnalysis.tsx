import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Select, 
  Table, 
  message, 
  Space,
  Row,
  Col,
  Divider,
  Typography
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { technicalAPI } from '../services/api';
import { TechnicalIndicator } from '../types';

const { Option } = Select;
const { Title } = Typography;

const TechnicalAnalysis: React.FC = () => {
  const [form] = Form.useForm();
  const [indicators, setIndicators] = useState<TechnicalIndicator[]>([]);
  const [loading, setLoading] = useState(false);

  const indicatorOptions = [
    { value: 'CCI', label: 'CCI (商品通道指数)' },
    { value: 'RSI', label: 'RSI (相对强弱指数)' },
    { value: 'MACD', label: 'MACD (指数平滑移动平均线)' },
    { value: 'BOLL', label: 'BOLL (布林带)' },
    { value: 'KDJ', label: 'KDJ (随机指标)' },
  ];

  const columns = [
    {
      title: '指标名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '参数',
      dataIndex: 'parameters',
      key: 'parameters',
      render: (params: any) => JSON.stringify(params),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <span style={{ color: status === 'active' ? 'green' : 'red' }}>
          {status === 'active' ? '启用' : '禁用'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" onClick={() => editIndicator(record)}>
            编辑
          </Button>
          <Button type="link" danger onClick={() => deleteIndicator(record._id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const loadIndicators = async () => {
    setLoading(true);
    try {
      // This would come from your API
      const mockData = [
        {
          _id: '1',
          name: 'CCI',
          description: '商品通道指数',
          parameters: { period: 14, constant: 0.015 },
          status: 'active',
        },
      ];
      setIndicators(mockData);
    } catch (error) {
      message.error('加载技术指标失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      await technicalAPI.createConfig(values);
      message.success('技术指标配置保存成功');
      form.resetFields();
      loadIndicators();
    } catch (error) {
      message.error('保存配置失败');
    }
  };

  const editIndicator = (indicator: any) => {
    form.setFieldsValue(indicator);
  };

  const deleteIndicator = async (id: string) => {
    try {
      // await technicalAPI.deleteConfig(id);
      message.success('删除成功');
      loadIndicators();
    } catch (error) {
      message.error('删除失败');
    }
  };

  useEffect(() => {
    loadIndicators();
  }, []);

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="配置技术指标">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
            >
              <Form.Item
                name="name"
                label="指标名称"
                rules={[{ required: true, message: '请输入指标名称' }]}
              >
                <Select placeholder="选择技术指标">
                  {indicatorOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="description"
                label="指标描述"
                rules={[{ required: true, message: '请输入指标描述' }]}
              >
                <Input.TextArea rows={2} placeholder="描述该技术指标的用途" />
              </Form.Item>

              <Title level={5}>参数配置</Title>
              
              <Form.Item
                name={['parameters', 'period']}
                label="周期"
                rules={[{ required: true, message: '请输入周期参数' }]}
              >
                <Input type="number" placeholder="例如：14" />
              </Form.Item>

              <Form.Item
                name={['parameters', 'constant']}
                label="缩放常数"
                rules={[{ required: true, message: '请输入缩放常数' }]}
              >
                <Input type="number" step="0.001" placeholder="例如：0.015" />
              </Form.Item>

              <Form.Item
                name="status"
                label="状态"
                initialValue="active"
              >
                <Select>
                  <Option value="active">启用</Option>
                  <Option value="inactive">禁用</Option>
                </Select>
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
                  保存配置
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="已配置的技术指标">
            <Table
              columns={columns}
              dataSource={indicators}
              rowKey="_id"
              loading={loading}
              pagination={false}
            />
          </Card>
        </Col>
      </Row>

      <Divider />

      <Card title="CCI指标说明">
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Card size="small" title="超买区域">
              <p>CCI &gt; +100：考虑卖出</p>
              <p>价格可能过高，存在回调风险</p>
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small" title="正常区域">
              <p>CCI介于 -100 到 +100 之间</p>
              <p>价格在正常范围内波动</p>
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small" title="超卖区域">
              <p>CCI &lt; -100：考虑买入</p>
              <p>价格可能过低，存在反弹机会</p>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default TechnicalAnalysis;
