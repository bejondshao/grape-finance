import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Select, Space, Tag, message, Modal, Form } from 'antd'
import { SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { stockCollectionService, tradingStrategyService } from '../services/api'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select

const StockCollection = () => {
  const [collection, setCollection] = useState([])
  const [strategies, setStrategies] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [form] = Form.useForm()

  const columns = [
    {
      title: 'Code',
      dataIndex: 'code',
      key: 'code',
      width: 100,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: 'Strategy',
      dataIndex: 'strategy_name',
      key: 'strategy_name',
      width: 150,
    },
    {
      title: 'Operation',
      dataIndex: 'operation',
      key: 'operation',
      width: 100,
      render: (operation) => {
        const colorMap = {
          'buy': 'green',
          'sell': 'red',
          'hold': 'blue',
          'watch': 'orange'
        }
        return <Tag color={colorMap[operation]}>{operation}</Tag>
      },
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price) => price ? `¥${price}` : '-',
    },
    {
      title: 'Shares',
      dataIndex: 'share_amount',
      key: 'share_amount',
      width: 100,
    },
    {
      title: 'Income',
      dataIndex: 'income',
      key: 'income',
      width: 100,
      render: (income) => {
        const color = income >= 0 ? 'green' : 'red'
        return <Tag color={color}>{income ? `¥${income}` : '-'}</Tag>
      },
    },
    {
      title: 'Signal Date',
      dataIndex: 'signal_date',
      key: 'signal_date',
      width: 120,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: 'Added Date',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
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

  const fetchCollection = async () => {
    setLoading(true)
    try {
      const response = await stockCollectionService.getCollection()
      setCollection(response.data || [])
    } catch (error) {
      message.error('Failed to fetch stock collection')
    } finally {
      setLoading(false)
    }
  }

  const fetchStrategies = async () => {
    try {
      const response = await tradingStrategyService.getStrategies()
      setStrategies(response.data || [])
    } catch (error) {
      message.error('Failed to fetch strategies')
    }
  }

  useEffect(() => {
    fetchCollection()
    fetchStrategies()
  }, [])

  const handleEdit = (record) => {
    setEditingRecord(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await stockCollectionService.removeFromCollection(id)
      message.success('Record deleted successfully')
      fetchCollection()
    } catch (error) {
      message.error('Failed to delete record')
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()
      if (editingRecord) {
        await stockCollectionService.updateCollection(editingRecord._id, values)
        message.success('Record updated successfully')
      }
      setModalVisible(false)
      setEditingRecord(null)
      form.resetFields()
      fetchCollection()
    } catch (error) {
      message.error('Failed to update record')
    }
  }

  const handleModalCancel = () => {
    setModalVisible(false)
    setEditingRecord(null)
    form.resetFields()
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Stock Collection</h1>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="Search by code or name"
            style={{ width: 300 }}
          />
          <Select placeholder="Filter by operation" style={{ width: 150 }} allowClear>
            <Option value="buy">Buy</Option>
            <Option value="sell">Sell</Option>
            <Option value="hold">Hold</Option>
            <Option value="watch">Watch</Option>
          </Select>
          <Select placeholder="Filter by strategy" style={{ width: 200 }} allowClear>
            {strategies.map(strategy => (
              <Option key={strategy._id} value={strategy._id}>
                {strategy.name}
              </Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={collection}
        rowKey="_id"
        loading={loading}
        scroll={{ x: 1000 }}
      />

      <Modal
        title="Edit Collection Record"
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="operation" label="Operation" rules={[{ required: true }]}>
            <Select>
              <Option value="buy">Buy</Option>
              <Option value="sell">Sell</Option>
              <Option value="hold">Hold</Option>
              <Option value="watch">Watch</Option>
            </Select>
          </Form.Item>
          <Form.Item name="price" label="Price">
            <Input type="number" />
          </Form.Item>
          <Form.Item name="share_amount" label="Share Amount">
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default StockCollection
