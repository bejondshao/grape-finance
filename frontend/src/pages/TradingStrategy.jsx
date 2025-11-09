import React, { useState, useEffect } from 'react'
import { Table, Button, Form, Input, Select, Space, message, Modal, InputNumber, Switch } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { tradingStrategyService, technicalAnalysisService } from '../services/api'

const { Option } = Select
const { TextArea } = Input

const TradingStrategy = () => {
  const [strategies, setStrategies] = useState([])
  const [indicators, setIndicators] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingStrategy, setEditingStrategy] = useState(null)
  const [form] = Form.useForm()

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: 200,
    },
    {
      title: 'Conditions',
      dataIndex: 'conditions',
      key: 'conditions',
      width: 300,
      render: (conditions) => (
        <div>
          {conditions?.map((condition, index) => (
            <div key={index}>
              {condition.indicator} {condition.operator} {condition.value}
            </div>
          ))}
        </div>
      ),
    },
    {
      title: 'Operation',
      dataIndex: 'operation',
      key: 'operation',
      width: 100,
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive) => (
        <Switch checked={isActive} disabled />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button 
            size="small" 
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecute(record._id)}
          >
            Run
          </Button>
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

  const fetchStrategies = async () => {
    setLoading(true)
    try {
      const response = await tradingStrategyService.getStrategies()
      setStrategies(response.data || [])
    } catch (error) {
      message.error('Failed to fetch strategies')
    } finally {
      setLoading(false)
    }
  }

  const fetchIndicators = async () => {
    try {
      const response = await technicalAnalysisService.getIndicators()
      setIndicators(response.data || [])
    } catch (error) {
      message.error('Failed to fetch indicators')
    }
  }

  useEffect(() => {
    fetchStrategies()
    fetchIndicators()
  }, [])

  const handleCreate = () => {
    setEditingStrategy(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (strategy) => {
    setEditingStrategy(strategy)
    form.setFieldsValue(strategy)
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await tradingStrategyService.deleteStrategy(id)
      message.success('Strategy deleted successfully')
      fetchStrategies()
    } catch (error) {
      message.error('Failed to delete strategy')
    }
  }

  const handleExecute = async (id) => {
    try {
      await tradingStrategyService.executeStrategy(id)
      message.success('Strategy executed successfully')
    } catch (error) {
      message.error('Failed to execute strategy')
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()

      if (editingStrategy) {
        await tradingStrategyService.updateStrategy(editingStrategy._id, values)
        message.success('Strategy updated successfully')
      } else {
        await tradingStrategyService.createStrategy(values)
        message.success('Strategy created successfully')
      }

      setModalVisible(false)
      setEditingStrategy(null)
      form.resetFields()
      fetchStrategies()
    } catch (error) {
      message.error('Failed to save strategy')
    }
  }

  const handleModalCancel = () => {
    setModalVisible(false)
    setEditingStrategy(null)
    form.resetFields()
  }

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
  ]

  const operatorOptions = [
    { value: '>', label: '大于' },
    { value: '>=', label: '大于等于' },
    { value: '<', label: '小于' },
    { value: '<=', label: '小于等于' },
    { value: '==', label: '等于' },
    { value: '!=', label: '不等于' },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Trading Strategy</h1>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          Create Strategy
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={strategies}
        rowKey="_id"
        loading={loading}
        scroll={{ x: 1000 }}
      />

      <Modal
        title={editingStrategy ? 'Edit Strategy' : 'Create Strategy'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={800}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Strategy Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={3} />
          </Form.Item>

          <Form.List name="conditions">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field, index) => (
                  <Space key={field.key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                    <Form.Item
                      {...field}
                      name={[field.name, 'indicator']}
                      label={index === 0 ? 'Indicator' : ''}
                      rules={[{ required: true }]}
                    >
                      <Select placeholder="Select Indicator" style={{ width: 150 }}>
                        {indicators.map(indicator => (
                          <Option key={indicator._id} value={indicator.name}>
                            {indicator.name}
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>

                    <Form.Item
                      {...field}
                      name={[field.name, 'operator']}
                      label={index === 0 ? 'Operator' : ''}
                      rules={[{ required: true }]}
                    >
                      <Select placeholder="Operator" style={{ width: 120 }}>
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
                      label={index === 0 ? 'Value' : ''}
                      rules={[{ required: true }]}
                    >
                      <InputNumber placeholder="Value" />
                    </Form.Item>

                    <Button type="dashed" onClick={() => remove(field.name)}>
                      Remove
                    </Button>
                  </Space>
                ))}

                <Form.Item>
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    Add Condition
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Form.Item name="operation" label="Operation" rules={[{ required: true }]}>
            <Select>
              {operationOptions.map(op => (
                <Option key={op.value} value={op.value}>
                  {op.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="is_active" label="Active" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TradingStrategy
