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
          {Object.entries(parameters || {}).map(([key, value]) => (
            <div key={key}>{key}: {value}</div>
          ))}
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
      const response = await technicalAnalysisService.getIndicators()
      setIndicators(response.data || [])
    } catch (error) {
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
      message.error('Failed to delete indicator')
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()

      if (editingIndicator) {
        await technicalAnalysisService.updateIndicator(editingIndicator._id, values)
        message.success('Indicator updated successfully')
      } else {
        await technicalAnalysisService.createIndicator(values)
        message.success('Indicator created successfully')
      }

      setModalVisible(false)
      setEditingIndicator(null)
      form.resetFields()
      fetchIndicators()
    } catch (error) {
      message.error('Failed to save indicator')
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
            <Input />
          </Form.Item>
          <Form.Item name="type" label="Type" rules={[{ required: true }]}>
            <Select>
              <Option value="CCI">CCI</Option>
              <Option value="RSI">RSI</Option>
              <Option value="MACD">MACD</Option>
              <Option value="BOLL">Bollinger Bands</Option>
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
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TechnicalAnalysis
