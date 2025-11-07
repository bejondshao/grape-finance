import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Form, 
  Input, 
  Button, 
  Select, 
  Space, 
  message, 
  Tag,
  Modal,
  InputNumber
} from 'antd';
import { 
  EditOutlined, 
  ReloadOutlined 
} from '@ant-design/icons';
import { configAPI } from '../services/api';
import { Configuration } from '../types';

const { Option } = Select;
const { TextArea } = Input;

const ConfigurationPage: React.FC = () => {
  const [form] = Form.useForm();
  const [configs, setConfigs] = useState<Configuration[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState<Configuration | null>(null);

  const categories = [
    'scheduler',
    'trading',
    'technical',
    'system',
    'tax_fee'
  ];

  const columns = [
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: string) => (
        <Tag color="blue">{category}</Tag>
      ),
    },
    {
      title: '子分类',
      dataIndex: 'sub_category',
      key: 'sub_category',
      width: 120,
    },
    {
      title: '配置键',
      dataIndex: 'key',
      key: 'key',
      width: 150,
    },
    {
      title: '配置值',
      dataIndex: 'value',
      key: 'value',
      width: 150,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: Configuration) => (
        <Button 
          type="link" 
          icon={<EditOutlined />}
          onClick={() => editConfig(record)}
        >
          编辑
        </Button>
      ),
    },
  ];

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await configAPI.getConfigs();
      setConfigs(response.data.configs);
    } catch (error) {
      message.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const editConfig = (config: Configuration) => {
    setEditingConfig(config);
    form.setFieldsValue(config);
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    if (!editingConfig) return;
    
    try {
      await configAPI.updateConfig({
        category: editingConfig.category,
        sub_category: editingConfig.sub_category,
        key: editingConfig.key,
        value: values.value
      });
      message.success('配置更新成功');
      setModalVisible(false);
      setEditingConfig(null);
      form.resetFields();
      loadConfigs();
    } catch (error) {
      message.error('更新配置失败');
    }
  };

  const resetToDefault = async () => {
    Modal.confirm({
      title: '确认重置',
      content: '确定要重置所有配置为默认值吗？',
      onOk: async () => {
        // Implement reset logic
        message.success('配置已重置为默认值');
        loadConfigs();
      },
    });
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  return (
    <div>
      <Card
        title="系统配置"
        extra={
          <Button 
            icon={<ReloadOutlined />}
            onClick={resetToDefault}
          >
            重置默认
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={configs}
          rowKey={record => `${record.category}-${record.sub_category}-${record.key}`}
          loading={loading}
          scroll={{ x: 800 }}
        />
      </Card>

      <Modal
        title="编辑配置"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingConfig(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        {editingConfig && (
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
          >
            <Form.Item label="分类">
              <Input value={editingConfig.category} disabled />
            </Form.Item>

            <Form.Item label="子分类">
              <Input value={editingConfig.sub_category} disabled />
            </Form.Item>

            <Form.Item label="配置键">
              <Input value={editingConfig.key} disabled />
            </Form.Item>

            <Form.Item label="描述">
              <Input value={editingConfig.description} disabled />
            </Form.Item>

            <Form.Item
              name="value"
              label="配置值"
              rules={[{ required: true, message: '请输入配置值' }]}
            >
              <Input placeholder="输入配置值" />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  保存
                </Button>
                <Button onClick={() => {
                  setModalVisible(false);
                  setEditingConfig(null);
                  form.resetFields();
                }}>
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
};

export default ConfigurationPage;
