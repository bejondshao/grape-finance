import React, { useState, useEffect } from 'react'
import { Table, Button, Form, Input, Select, Space, message, Modal, InputNumber } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { technicalAnalysisService } from '../services/api'

const { Option } = Select

const TechnicalAnalysis = () => {
  const [indicators, setIndicators] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingIndicator, setEditingIndicator] = useState(null)
  const [form] = Form.useForm()

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 100,
    },
    {
      title: 'Parameters',
      dataIndex: 'parameters',
      key: 'parameters',
      width: 200,
      render: (parameters) => (
        <div>
          {parameters && typeof parameters === 'object' ? (
            Object.entries(parameters).map(([key, value]) => (
              <div key={key}>{key}: {value}</div>
            ))
          ) : (
            <div>-</div>
          )}
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
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (created_at) => created_at ? new Date(created_at).toLocaleDateString() : '-'
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

  const fetchIndicators = async () => {
    setLoading(true)
    try {
      const response = await technicalAnalysisService.getConfiguredIndicators()
      console.log('API Response:', response)
      // 确保响应数据是数组类型
      // API 返回的数据结构是 { data: [...] }，我们需要提取 data 字段
      const indicatorsData = Array.isArray(response) 
        ? response 
        : (response && Array.isArray(response.data) ? response.data : [])
      setIndicators(indicatorsData)
    } catch (error) {
      console.error('Failed to fetch indicators:', error)
      message.error('Failed to fetch indicators')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIndicators()
  }, [])

  const handleCreate = () => {
    setEditingIndicator(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (indicator) => {
    setEditingIndicator(indicator)
    form.setFieldsValue({
      ...indicator,
      parameters: indicator.parameters || {}
    })
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await technicalAnalysisService.deleteIndicator(id)
      message.success('Indicator deleted successfully')
      fetchIndicators()
    } catch (error) {
      console.error('Failed to delete indicator:', error)
      message.error('Failed to delete indicator: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()
      console.log('Form values:', values)

      if (editingIndicator) {
        // 更新指标配置
        await technicalAnalysisService.updateIndicator(editingIndicator._id, values)
        message.success('Indicator updated successfully')
      } else {
        // 创建新的指标配置
        await technicalAnalysisService.createIndicator(values)
        message.success('Indicator created successfully')
      }

      setModalVisible(false)
      setEditingIndicator(null)
      form.resetFields()
      fetchIndicators()
    } catch (error) {
      console.error('Failed to save indicator:', error)
      message.error('Failed to save indicator: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleModalCancel = () => {
    setModalVisible(false)
    setEditingIndicator(null)
    form.resetFields()
  }

  const renderParameterFields = (type) => {
    switch (type) {
      case 'CCI':
        return (
          <>
            <Form.Item name={['parameters', 'period']} label="Period" initialValue={14}>
              <InputNumber min={1} max={100} />
            </Form.Item>
            <Form.Item name={['parameters', 'scaling_constant']} label="Scaling Constant" initialValue={0.015}>
              <InputNumber step={0.001} min={0.001} max={1} />
            </Form.Item>
          </>
        )
      case 'RSI':
        return (
          <Form.Item name={['parameters', 'period']} label="Period" initialValue={14}>
            <InputNumber min={1} max={100} />
          </Form.Item>
        )
      case 'MACD':
        return (
          <>
            <Form.Item name={['parameters', 'fast_period']} label="Fast Period" initialValue={12}>
              <InputNumber min={1} max={100} />
            </Form.Item>
            <Form.Item name={['parameters', 'slow_period']} label="Slow Period" initialValue={26}>
              <InputNumber min={1} max={100} />
            </Form.Item>
            <Form.Item name={['parameters', 'signal_period']} label="Signal Period" initialValue={9}>
              <InputNumber min={1} max={100} />
            </Form.Item>
          </>
        )
      case 'BOLL':
        return (
          <>
            <Form.Item name={['parameters', 'period']} label="Period" initialValue={20}>
              <InputNumber min={1} max={100} />
            </Form.Item>
            <Form.Item name={['parameters', 'num_std']} label="Standard Deviations" initialValue={2}>
              <InputNumber min={1} max={5} step={0.5} />
            </Form.Item>
          </>
        )
      case 'KDJ':
        return (
          <Form.Item name={['parameters', 'period']} label="Period" initialValue={9}>
            <InputNumber min={1} max={100} />
          </Form.Item>
        )
      default:
        return null
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Technical Analysis</h1>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          Create Indicator
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={indicators}
        rowKey="_id"
        loading={loading}
        scroll={{ x: 800 }}
      />

      <Modal
        title={editingIndicator ? 'Edit Indicator' : 'Create Indicator'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. CCI, RSI, MACD" />
          </Form.Item>
          <Form.Item name="type" label="Type" rules={[{ required: true }]}>
            <Select placeholder="Select indicator type">
              <Option value="CCI">CCI</Option>
              <Option value="RSI">RSI</Option>
              <Option value="MACD">MACD</Option>
              <Option value="BOLL">Bollinger Bands</Option>
              <Option value="KDJ">KDJ</Option>
              <Option value="MA">Moving Average</Option>
            </Select>
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.type !== currentValues.type}
          >
            {({ getFieldValue }) => renderParameterFields(getFieldValue('type'))}
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={4} placeholder="Enter description for this indicator" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TechnicalAnalysis