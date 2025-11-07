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
  Switch,
  Modal,
  Tag
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined,
  PlayCircleOutlined 
} from '@ant-design/icons';
import { tradingAPI } from '../services/api';
import { TradingStrategy } from '../types';

const { Option } = Select;
const { TextArea } = Input;

const TradingStrategies: React.FC = () => {
  const [form] = Form.useForm();
  const [strategies, setStrategies] = useState<TradingStrategy[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<TradingStrategy | null>(null);

  const operationOptions = [
    { value: '关注', label: '关注' },
    { value: '密切关注', label: '密切关注' },
    { value: '建仓', label: '建仓' },
    { value: '加仓', label: '加仓' },
    { value: '减仓', label: '减仓' },
    { value: '持有', label: '持有' },
    { value: '清仓', label: '清仓' },
    { value: '清仓并关注', label: '清仓并关注' },
    { value: '清仓并密切关注', label: '清仓并密切关注' },
  ];

  const operatorOptions = [
    { value: '>', label: '大于' },
    { value: '>=', label: '大于等于' },
    { value: '<', label: '小于' },
    { value: '<=', label: '小于等于' },
    { value: '==', label: '等于' },
    { value: '!=', label: '不等于' },
  ];

  const columns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '条件数量',
      dataIndex: 'conditions',
      key: 'conditions',
      render: (conditions: any[]) => conditions.length,
    },
    {
      title: '操作',
      dataIndex: 'operation',
      key: 'operation',
      render: (operation: string) => (
        <Tag color="blue">{operation}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Switch checked={active} disabled />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: TradingStrategy) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />}
            onClick={() => editStrategy(record)}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            icon={<PlayCircleOutlined />}
            onClick={() => evaluateStrategy(record._id!)}
          >
            执行
          </Button>
          <Button 
            type="link" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => deleteStrategy(record._id!)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const loadStrategies = async () => {
    setLoading(true);
    try {
      const response = await tradingAPI.getStrategies();
      setStrategies(response.data);
    } catch (error) {
      message.error('加载交易策略失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingStrategy) {
        await tradingAPI.updateStrategy(editingStrategy._id!, values);
        message.success('策略更新成功');
      } else {
        await tradingAPI.createStrategy(values);
        message.success('策略创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingStrategy(null);
      loadStrategies();
    } catch (error) {
      message.error(editingStrategy ? '更新策略失败' : '创建策略失败');
    }
  };

  const editStrategy = (strategy: TradingStrategy) => {
    setEditingStrategy(strategy);
    form.setFieldsValue(strategy);
    setModalVisible(true);
  };

  const evaluateStrategy = async (strategyId: string) => {
    try {
      await tradingAPI.evaluateStrategies();
      message.success('策略执行完成，请查看股票收藏');
    } catch (error) {
      message.error('策略执行失败');
    }
  };

  const deleteStrategy = async (strategyId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个交易策略吗？',
      onOk: async () => {
        try {
          await tradingAPI.deleteStrategy(strategyId);
          message.success('删除成功');
          loadStrategies();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  useEffect(() => {
    loadStrategies();
  }, []);

  return (
    <div>
      <Card
        title="交易策略管理"
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            新建策略
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={strategies}
          rowKey="_id"
          loading={loading}
        />
      </Card>

      <Modal
        title={editingStrategy ? '编辑交易策略' : '新建交易策略'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingStrategy(null);
          form.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="策略名称"
            rules={[{ required: true, message: '请输入策略名称' }]}
          >
            <Input placeholder="输入策略名称" />
          </Form.Item>

          <Form.List name="conditions">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field, index) => (
                  <Space key={field.key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                    <Form.Item
                      {...field}
                      name={[field.name, 'days_ago']}
                      label={`条件 ${index + 1} - 天数`}
                      rules={[{ required: true, message: '请输入天数' }]}
                    >
                      <Input type="number" placeholder="0表示当天" />
                    </Form.Item>
                    <Form.Item
                      {...field}
                      name={[field.name, 'indicator']}
                      rules={[{ required: true, message: '选择指标' }]}
                    >
                      <Select placeholder="指标" style={{ width: 120 }}>
                        <Option value="CCI">CCI</Option>
                        <Option value="RSI">RSI</Option>
                        <Option value="close">收盘价</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item
                      {...field}
                      name={[field.name, 'operator']}
                      rules={[{ required: true, message: '选择运算符' }]}
                    >
                      <Select placeholder="运算符" style={{ width: 100 }}>
                        {operatorOptions.map(op => (
                          <Option key={op.value} value={op.value}>
                            {op.label}
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item
                      {...field}
                      name={[field.name, 'value']}
                      rules={[{ required: true, message: '输入值' }]}
                    >
                      <Input type="number" placeholder="数值" />
                    </Form.Item>
                    <Button type="link" danger onClick={() => remove(field.name)}>
                      删除
                    </Button>
                  </Space>
                ))}
                <Form.Item>
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    添加条件
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Form.Item
            name="operation"
            label="操作"
            rules={[{ required: true, message: '请选择操作' }]}
          >
            <Select placeholder="选择操作">
              {operationOptions.map(op => (
                <Option key={op.value} value={op.value}>
                  {op.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="is_active"
            label="状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingStrategy ? '更新策略' : '创建策略'}
              </Button>
              <Button onClick={() => {
                setModalVisible(false);
                setEditingStrategy(null);
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

export default TradingStrategies;
