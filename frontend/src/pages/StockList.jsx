import React, {useEffect, useState} from 'react'
import {Button, DatePicker, Input, message, Select, Space, Table, Tag} from 'antd'
import {SyncOutlined} from '@ant-design/icons'
import {stockService} from '../services/api'
import dayjs from 'dayjs'

const {Search} = Input
const {Option} = Select
const {RangePicker} = DatePicker

const StockList = () => {
    const [stocks, setStocks] = useState([])
    const [loading, setLoading] = useState(false)
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 20,
        total: 0,
    })
    const [filters, setFilters] = useState({})

    const columns = [
        {
            title: 'Code',
            dataIndex: 'code',
            key: 'code',
            width: 120,
        },
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            width: 150,
        },
        {
            title: 'Industry',
            dataIndex: 'industry',
            key: 'industry',
            width: 120,
        },
        {
            title: 'Latest Price',
            dataIndex: 'close',
            key: 'close',
            width: 100,
            render: (value) => value ? `¥${value}` : '-',
        },
        {
            title: 'Change %',
            dataIndex: 'change_percent',
            key: 'change_percent',
            width: 100,
            render: (value) => {
                if (!value) return '-'
                const color = value >= 0 ? 'green' : 'red'
                return <Tag color={color}>{value}%</Tag>
            },
        },
        {
            title: 'Volume',
            dataIndex: 'volume',
            key: 'volume',
            width: 120,
            render: (value) => value ? (value / 10000).toFixed(2) + '万' : '-',
        },
        {
            title: 'Last Updated',
            dataIndex: 'date',
            key: 'date',
            width: 120,
            render: (value) => value ? dayjs(value).format('YYYY-MM-DD') : '-',
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 120,
            render: (_, record) => (
                <Space>
                    <Button size="small">View</Button>
                    <Button size="small" type="primary">Add</Button>
                </Space>
            ),
        },
    ]

    const fetchStocks = async (params = {}) => {
        setLoading(true)
        try {
            const response = await stockService.getStocks({
                page: pagination.current,
                pageSize: pagination.pageSize,
                ...filters,
                ...params,
            })
            setStocks(response.stocks || [])
            setPagination(prev => ({
                ...prev,
                total: response.total || 0,
            }))
        } catch (error) {
            message.error('Failed to fetch stocks')
        } finally {
            setLoading(false)
        }
    }

    const getStockHistory = async (params = {}) => {
        setLoading(true)
        try {
            const response = await stockService.getStockHistory({
                page: pagination.current,
                pageSize: pagination.pageSize,
                ...filters,
                ...params,
            })
            setStocks(response.data || [])
            setPagination(prev => ({
                ...prev,
                total: response.total || 0,
            }))
        } catch (error) {
            message.error('Failed to fetch stocks')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchStocks()
    }, [pagination.current, pagination.pageSize])

    const handleTableChange = (newPagination) => {
        setPagination(newPagination)
    }

    const handleSearch = (value) => {
        setFilters(prev => ({...prev, search: value}))
        getStockHistory({search: value})
    }

    const handleIndustryChange = (value) => {
        setFilters(prev => ({...prev, industry: value}))
        fetchStocks({industry: value})
    }

    const handleDateChange = (dates) => {
        if (dates) {
            setFilters(prev => ({
                ...prev,
                start_date: dates[0].format('YYYY-MM-DD'),
                end_date: dates[1].format('YYYY-MM-DD'),
            }))
            fetchStocks({
                start_date: dates[0].format('YYYY-MM-DD'),
                end_date: dates[1].format('YYYY-MM-DD'),
            })
        } else {
            const newFilters = {...filters}
            delete newFilters.start_date
            delete newFilters.end_date
            setFilters(newFilters)
            fetchStocks(newFilters)
        }
    }

    const handleTriggerFetch = async () => {
        try {
            await stockService.triggerFetch()
            message.success('Data fetch triggered successfully')
        } catch (error) {
            message.error('Failed to trigger data fetch')
        }
    }

    return (
        <div>
            <div style={{marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <h1>Stock List</h1>
                <Button
                    type="primary"
                    icon={<SyncOutlined/>}
                    onClick={handleTriggerFetch}
                >
                    Trigger Fetch
                </Button>
            </div>

            <div style={{marginBottom: 16}}>
                <Space>
                    <Search
                        placeholder="Search by code or name"
                        onSearch={handleSearch}
                        style={{width: 300}}
                    />
                    <Select
                        placeholder="Select Industry"
                        style={{width: 200}}
                        onChange={handleIndustryChange}
                        allowClear
                    >
                        <Option value="technology">Technology</Option>
                        <Option value="finance">Finance</Option>
                        <Option value="healthcare">Healthcare</Option>
                        <Option value="energy">Energy</Option>
                    </Select>
                    <RangePicker onChange={handleDateChange}/>
                </Space>
            </div>

            <Table
                columns={columns}
                dataSource={stocks}
                rowKey="code"
                loading={loading}
                pagination={pagination}
                onChange={handleTableChange}
                scroll={{x: 800}}
            />
        </div>
    )
}

export default StockList
