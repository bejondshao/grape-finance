import React, { useState, useEffect } from 'react'
import { Table, Button, Form, Input, Select, Space, message, Modal, InputNumber } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { configurationService } from '../services/api'

const { Option } = Select
const { TextArea } = Input

const Configuration = () => {
  const [configs, setConfigs] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState(null)
  const [form] = Form.useForm()

  const columns = [
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: 120,
    },
    {
      title: 'Sub Category',
      dataIndex: 'sub_category',
      key: 'sub_category',
      width: 120,
    },
    {
      title: 'Key',
      dataIndex: 'key',
      key: 'key',
      width: 150,
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      width: 200,
      render: (value) => (
        <div style={{ wordBreak: 'break-all' }}>
          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
        </div>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: 200,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Button 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Button 
            size="small" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record._id)}
          />
        </Space>
      ),
    },
  ]

  const fetchConfigs = async () => {
    setLoading(true)
    try {
      // 现在API拦截器会自动处理响应数据，直接使用返回结果
      const response = await configurationService.getConfigs()
      // API 返回的数据结构是 { configs: [...], total: ... }
      // 我们需要提取 configs 字段
      const configsData = response && response.configs && Array.isArray(response.configs) 
        ? response.configs 
        : []
      setConfigs(configsData)
    } catch (error) {
      console.error('Failed to fetch configurations:', error)
      message.error('Failed to fetch configurations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [])

  const handleCreate = () => {
    setEditingConfig(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (config) => {
    setEditingConfig(config)
    form.setFieldsValue(config)
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      // Configuration items don't have an ID in the current implementation
      // We would need to identify them by category, sub_category, and key
      message.warning('Delete functionality not implemented yet');
      // await configurationService.deleteConfig(id)
      // message.success('Configuration deleted successfully')
      // fetchConfigs()
    } catch (error) {
      console.error('Failed to delete configuration:', error)
      message.error('Failed to delete configuration: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()

      if (editingConfig) {
        await configurationService.updateConfig(values)
        message.success('Configuration updated successfully')
      } else {
        await configurationService.createConfig(values)
        message.success('Configuration created successfully')
      }

      setModalVisible(false)
      setEditingConfig(null)
      form.resetFields()
      fetchConfigs()
    } catch (error) {
      console.error('Failed to save configuration:', error)
      message.error('Failed to save configuration: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleModalCancel = () => {
    setModalVisible(false)
    setEditingConfig(null)
    form.resetFields()
  }

  const categories = [
    'scheduler',
    'trading',
    'technical_analysis',
    'data_fetch',
    'system'
  ]

  const subCategories = [
    'general',
    'tax_fee',
    'indicators',
    'baostock',
    'performance'
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>System Configuration</h1>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          Add Configuration
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={configs}
        rowKey="_id"
        loading={loading}
        scroll={{ x: 1000 }}
      />

      <Modal
        title={editingConfig ? 'Edit Configuration' : 'Add Configuration'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="category" label="Category" rules={[{ required: true }]}>
            <Select>
              {categories.map(cat => (
                <Option key={cat} value={cat}>
                  {cat}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="sub_category" label="Sub Category" rules={[{ required: true }]}>
            <Select>
              {subCategories.map(subCat => (
                <Option key={subCat} value={subCat}>
                  {subCat}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="key" label="Key" rules={[{ required: true }]}>
            <Input />
          </Form.Item>

          <Form.Item name="value" label="Value" rules={[{ required: true }]}>
            <Input />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Configuration