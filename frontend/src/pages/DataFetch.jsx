import React, { useState, useEffect } from 'react'
import { Card, Button, Progress, Space, message, List, Tag, Statistic, Row, Col, Input, DatePicker } from 'antd'
import { SyncOutlined } from '@ant-design/icons'
import { stockService, technicalAnalysisService } from '../services/api'

const { RangePicker } = DatePicker

const DataFetch = () => {
  const [progress, setProgress] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const [fetchStatus, setFetchStatus] = useState('idle')
  const [currentStock, setCurrentStock] = useState('')
  const [failedStocks, setFailedStocks] = useState([])
  // CCI更新相关状态
  const [stockCode, setStockCode] = useState('')
  const [dateRange, setDateRange] = useState([])
  const [isCciUpdating, setIsCciUpdating] = useState(false)
  const [cciUpdateResult, setCciUpdateResult] = useState(null)
  // 批量更新所有股票CCI相关状态
  const [isBatchCciUpdating, setIsBatchCciUpdating] = useState(false)
  const [batchCciResult, setBatchCciResult] = useState(null)

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

  const handleUpdateCci = async () => {
    if (!stockCode) {
      message.error('Please enter stock code')
      return
    }

    try {
      setIsCciUpdating(true)
      setCciUpdateResult(null)
      
      const params = {
        code: stockCode
      }
      
      // 添加日期范围参数（如果选择了）
      if (dateRange.length === 2) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }

      const response = await stockService.updateStockCci(params)
      setCciUpdateResult(response.data)
      message.success(`CCI updated successfully. Updated records: ${response.data.updated_count}`)
    } catch (error) {
      message.error(`Failed to update CCI: ${error.response?.data?.detail || 'Unknown error'}`)
    } finally {
      setIsCciUpdating(false)
    }
  }

  const handleUpdateAllStocksCci = async () => {
    try {
      setIsBatchCciUpdating(true)
      setBatchCciResult(null)
      
      message.info('开始批量更新所有股票的CCI指标，请耐心等待...')
      
      // 调用批量更新API
      const response = await technicalAnalysisService.updateAllStocksCci()
      setBatchCciResult(response.data || response)
      
      if (response.success || response.data?.success) {
        message.success(`批量更新完成！成功: ${response.data?.results?.success_count || 0}, 失败: ${response.data?.results?.failed_count || 0}`)
      } else {
        message.error(`批量更新失败: ${response.message || 'Unknown error'}`)
      }
    } catch (error) {
      message.error(`Failed to update all stocks CCI: ${error.response?.data?.detail || 'Unknown error'}`)
    } finally {
      setIsBatchCciUpdating(false)
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

        <Card title="Update Stock CCI">
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Space>
              <span>Stock Code:</span>
              <Input 
                placeholder="Enter stock code (e.g., 600000)" 
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                style={{ width: 200 }}
              />
              <span>Date Range (optional):</span>
              <RangePicker 
                onChange={(dates) => setDateRange(dates || [])}
                style={{ width: 300 }}
              />
              <Button
                type="primary"
                icon={<SyncOutlined />}
                onClick={handleUpdateCci}
                disabled={isCciUpdating}
                loading={isCciUpdating}
              >
                Update CCI
              </Button>
            </Space>
            
            {cciUpdateResult && (
              <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f0f9ff', borderRadius: 4 }}>
                <h4>Update Results:</h4>
                <p>Stock: {cciUpdateResult.code}</p>
                <p>Updated Records: {cciUpdateResult.updated_count}</p>
                <p>Process Time: {cciUpdateResult.process_time_ms} ms</p>
                {cciUpdateResult.message && <p>Message: {cciUpdateResult.message}</p>}
              </div>
            )}
          </Space>
        </Card>
        
        <Card title="Batch Update All Stocks CCI">
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Space>
              <p style={{ marginRight: '16px' }}>一键更新所有股票的CCI指标，自动从各股票最新CCI日期更新到今日</p>
              <Button
                type="primary"
                danger
                icon={<SyncOutlined />}
                onClick={handleUpdateAllStocksCci}
                disabled={isBatchCciUpdating}
                loading={isBatchCciUpdating}
              >
                一键更新所有股票CCI
              </Button>
            </Space>
            
            {batchCciResult && (
              <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f0f9ff', borderRadius: 4 }}>
                <h4>Batch Update Results:</h4>
                <p>Total Stocks: {batchCciResult.results?.total_count || 0}</p>
                <p>Successfully Updated: {batchCciResult.results?.success_count || 0}</p>
                <p>Failed to Update: {batchCciResult.results?.failed_count || 0}</p>
                {batchCciResult.message && <p>Message: {batchCciResult.message}</p>}
                
                {batchCciResult.results?.failed_stocks && batchCciResult.results.failed_stocks.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <h5 style={{ color: '#ff4d4f' }}>Failed Stocks:</h5>
                    <List
                      dataSource={batchCciResult.results.failed_stocks}
                      renderItem={(item) => (
                        <List.Item>
                          <List.Item.Meta
                            title={item.code}
                            description={`Error: ${item.error}`}
                          />
                        </List.Item>
                      )}
                    />
                  </div>
                )}
              </div>
            )}
          </Space>
        </Card>
      </Space>
    </div>
  )
}

export default DataFetch
