import React, {useState, useEffect} from 'react'
import {
    Table,
    Button,
    Form,
    Input,
    Select,
    Space,
    message,
    Modal,
    InputNumber,
    DatePicker,
    Statistic,
    Card,
    Row,
    Col,
    Tag
} from 'antd'
import {PlusOutlined, EditOutlined, DeleteOutlined} from '@ant-design/icons'
import {tradingRecordService} from '../services/api'
import dayjs from 'dayjs'

const {Option} = Select
const {TextArea} = Input

const TradingRecords = () => {
    const [records, setRecords] = useState([])
    const [loading, setLoading] = useState(false)
    const [modalVisible, setModalVisible] = useState(false)
    const [editingRecord, setEditingRecord] = useState(null)
    const [profitData, setProfitData] = useState({})
    const [form] = Form.useForm()

    const columns = [
        {
            title: 'Date',
            dataIndex: 'date',
            key: 'date',
            width: 120,
            render: (date) => dayjs(date).format('YYYY-MM-DD'),
        },
        {
            title: 'Time',
            dataIndex: 'time',
            key: 'time',
            width: 100,
        },
        {
            title: 'Account',
            dataIndex: 'account',
            key: 'account',
            width: 120,
        },
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
            title: 'Type',
            dataIndex: 'type',
            key: 'type',
            width: 80,
            render: (type) => (
                <Tag color={type === 'buy' ? 'green' : 'red'}>
                    {type === 'buy' ? '买入' : '卖出'}
                </Tag>
            ),
        },
        {
            title: 'Price',
            dataIndex: 'price',
            key: 'price',
            width: 100,
            render: (price) => `¥${price}`,
        },
        {
            title: 'Amount',
            dataIndex: 'amount',
            key: 'amount',
            width: 100,
        },
        {
            title: 'Total',
            dataIndex: 'total_value',
            key: 'total_value',
            width: 120,
            render: (total) => total ? `¥${total}` : '-',
        },
        {
            title: 'Profit',
            dataIndex: 'profit',
            key: 'profit',
            width: 100,
            render: (profit) => (
                <Tag color={profit >= 0 ? 'green' : 'red'}>
                    {profit ? `¥${profit}` : '-'}
                </Tag>
            ),
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 100,
            render: (_, record) => (
                <Space>
                    <Button
                        size="small"
                        icon={<EditOutlined/>}
                        onClick={() => handleEdit(record)}
                    />
                    <Button
                        size="small"
                        danger
                        icon={<DeleteOutlined/>}
                        onClick={() => handleDelete(record._id)}
                    />
                </Space>
            ),
        },
    ]

    const fetchRecords = async () => {
        setLoading(true)
        try {
            const response = await tradingRecordService.getRecords()
            console.log('API Response:', response)
            console.log('Response records:', response.records)
            setRecords(response.records || {})
        } catch (error) {
            message.error('Failed to fetch trading records')
        } finally {
            setLoading(false)
        }
    }

    const fetchProfit = async () => {
        try {
            const response = await tradingRecordService.calculateProfit()
            setProfitData(response.records || {})
        } catch (error) {
            console.error('Failed to fetch profit data')
        }
    }

    useEffect(() => {
        fetchRecords()
        fetchProfit()
    }, [])

    const handleCreate = () => {
        setEditingRecord(null)
        form.resetFields()
        setModalVisible(true)
    }

    const handleEdit = (record) => {
        setEditingRecord(record)
        form.setFieldsValue({
            ...record,
            date: record.date ? dayjs(record.date) : null,
        })
        setModalVisible(true)
    }

    const handleDelete = async (id) => {
        try {
            await tradingRecordService.deleteRecord(id)
            message.success('Record deleted successfully')
            fetchRecords()
            fetchProfit()
        } catch (error) {
            message.error('Failed to delete record')
        }
    }

    const handleModalOk = async () => {
        try {
            const values = await form.validateFields()
            const formattedValues = {
                ...values,
                date: values.date ? values.date.format('YYYY-MM-DD') : null,
            }

            if (editingRecord) {
                await tradingRecordService.updateRecord(editingRecord._id, formattedValues)
                message.success('Record updated successfully')
            } else {
                await tradingRecordService.createRecord(formattedValues)
                message.success('Record created successfully')
            }

            setModalVisible(false)
            setEditingRecord(null)
            form.resetFields()
            fetchRecords()
            fetchProfit()
        } catch (error) {
            message.error('Failed to save record')
        }
    }

    const handleModalCancel = () => {
        setModalVisible(false)
        setEditingRecord(null)
        form.resetFields()
    }

    const calculateTotal = () => {
        const values = form.getFieldsValue()
        const price = values.price || 0
        const amount = values.amount || 0
        return price * amount
    }

    return (
        <div>
            <div style={{marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <h1>Trading Records</h1>
                <Button
                    type="primary"
                    icon={<PlusOutlined/>}
                    onClick={handleCreate}
                >
                    Add Record
                </Button>
            </div>

            <Row gutter={16} style={{marginBottom: 24}}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Total Profit"
                            value={profitData.total_profit || 0}
                            precision={2}
                            prefix="¥"
                            valueStyle={{color: (profitData.total_profit || 0) >= 0 ? '#3f8600' : '#cf1322'}}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Total Trades"
                            value={profitData.total_trades || 0}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Win Rate"
                            value={profitData.win_rate || 0}
                            precision={2}
                            suffix="%"
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Avg Profit per Trade"
                            value={profitData.avg_profit || 0}
                            precision={2}
                            prefix="¥"
                        />
                    </Card>
                </Col>
            </Row>

            <Table
                columns={columns}
                dataSource={records}
                rowKey="_id"
                loading={loading}
                scroll={{x: 1200}}
            />

            <Modal
                title={editingRecord ? 'Edit Trading Record' : 'Add Trading Record'}
                open={modalVisible}
                onOk={handleModalOk}
                onCancel={handleModalCancel}
                width={600}
            >
                <Form form={form} layout="vertical">
                    <Form.Item name="date" label="Date" rules={[{required: true}]}>
                        <DatePicker style={{width: '100%'}}/>
                    </Form.Item>

                    <Form.Item name="time" label="Time" rules={[{required: true}]}>
                        <Input placeholder="HH:MM"/>
                    </Form.Item>

                    <Form.Item name="account" label="Account" rules={[{required: true}]}>
                        <Input/>
                    </Form.Item>

                    <Form.Item name="code" label="Stock Code" rules={[{required: true}]}>
                        <Input/>
                    </Form.Item>

                    <Form.Item name="name" label="Stock Name">
                        <Input/>
                    </Form.Item>

                    <Form.Item name="type" label="Type" rules={[{required: true}]}>
                        <Select>
                            <Option value="buy">买入</Option>
                            <Option value="sell">卖出</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item name="price" label="Price" rules={[{required: true}]}>
                        <InputNumber
                            style={{width: '100%'}}
                            min={0}
                            step={0.01}
                            precision={2}
                        />
                    </Form.Item>

                    <Form.Item name="amount" label="Amount" rules={[{required: true}]}>
                        <InputNumber
                            style={{width: '100%'}}
                            min={0}
                        />
                    </Form.Item>

                    <Form.Item label="Total Value">
                        <Input value={calculateTotal()} disabled/>
                    </Form.Item>

                    <Form.Item name="reason" label="Reason">
                        <TextArea rows={3}/>
                    </Form.Item>

                    <Form.Item name="plan" label="Trading Plan">
                        <TextArea rows={3}/>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default TradingRecords
