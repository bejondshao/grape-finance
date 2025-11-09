import React, { useState, useEffect } from 'react'
import { Card, Button, Progress, Space, message, List, Tag, Statistic, Row, Col } from 'antd'
import { SyncOutlined } from '@ant-design/icons'
import { stockService } from '../services/api'

const DataFetch = () => {
  const [progress, setProgress] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const [fetchStatus, setFetchStatus] = useState('idle')
  const [currentStock, setCurrentStock] = useState('')
  const [failedStocks, setFailedStocks] = useState([])

  const fetchProgress = async () => {
    try {
      const response = await stockService.getFetchProgress()
      const data = response.data || {}

      setProgress(data.progress || 0)
      setIsRunning(data.is_running || false)
      setFetchStatus(data.status || 'idle')
      setCurrentStock(data.current_stock || '')
      setFailedStocks(data.failed_stocks || [])
    } catch (error) {
      console.error('Failed to fetch progress')
    }
  }

  useEffect(() => {
    const interval = setInterval(fetchProgress, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleTriggerFetch = async () => {
    try {
      await stockService.triggerFetch()
      message.success('Data fetch triggered successfully')
      setIsRunning(true)
    } catch (error) {
      message.error('Failed to trigger data fetch')
    }
  }

  const getStatusColor = (status) => {
    const colorMap = {
      'idle': 'default',
      'running': 'processing',
      'completed': 'success',
      'failed': 'error'
    }
    return colorMap[status] || 'default'
  }

  return (
    <div>
      <h1>Data Fetch Management</h1>

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Card title="Fetch Status">
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Statistic
                title="Current Status"
                value={fetchStatus}
                valueRender={value => (
                  <Tag color={getStatusColor(fetchStatus)}>{value}</Tag>
                )}
              />
              <Space>
                <Button
                  type="primary"
                  icon={<SyncOutlined />}
                  onClick={handleTriggerFetch}
                  disabled={isRunning}
                >
                  Trigger Fetch
                </Button>
              </Space>
            </div>

            <Progress percent={Math.round(progress)} status={isRunning ? 'active' : 'normal'} />

            {currentStock && (
              <div>
                <strong>Current Stock:</strong> {currentStock}
              </div>
            )}
          </Space>
        </Card>

        <Card title="Failed Stocks" style={{ minHeight: 300 }}>
          <List
            dataSource={failedStocks}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button type="link" size="small">Retry</Button>
                ]}
              >
                <List.Item.Meta
                  title={item.code}
                  description={`Error: ${item.error}`}
                />
                <div>{item.timestamp}</div>
              </List.Item>
            )}
            locale={{ emptyText: 'No failed stocks' }}
          />
        </Card>

        <Card title="Fetch Statistics">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic title="Total Stocks" value={4567} />
            </Col>
            <Col span={6}>
              <Statistic title="Updated Today" value={234} />
            </Col>
            <Col span={6}>
              <Statistic title="Failed Count" value={failedStocks.length} />
            </Col>
            <Col span={6}>
              <Statistic title="Success Rate" value={98.5} suffix="%" />
            </Col>
          </Row>
        </Card>
      </Space>
    </div>
  )
}

export default DataFetch
