import React, { useState, useEffect } from 'react'
import { Card, Button, Progress, Space, message, List, Tag, Statistic, Row, Col } from 'antd'
import { SyncOutlined, StopOutlined } from '@ant-design/icons'
import { stockService, technicalAnalysisService } from '../services/api'

const DataFetch = () => {
  const [progress, setProgress] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const [fetchStatus, setFetchStatus] = useState('idle')
  const [currentStock, setCurrentStock] = useState('')
  const [failedStocks, setFailedStocks] = useState([])
  // 批量更新所有股票指标相关状态
  const [isBatchIndicatorsUpdating, setIsBatchIndicatorsUpdating] = useState(false)
  const [batchIndicatorsResult, setBatchIndicatorsResult] = useState(null)
  // 重新计算所有股票指标相关状态
  const [isRecomputeIndicatorsUpdating, setIsRecomputeIndicatorsUpdating] = useState(false)
  const [recomputeIndicatorsResult, setRecomputeIndicatorsResult] = useState(null)

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

  const handleStopFetch = async () => {
    try {
      await stockService.stopDataFetch()
      message.success('Data fetch stop command sent successfully')
      setIsRunning(false)
    } catch (error) {
      message.error('Failed to stop data fetch')
    }
  }

  const handleUpdateAllStocksIndicators = async () => {
    try {
      setIsBatchIndicatorsUpdating(true)
      setBatchIndicatorsResult(null)
      
      message.info('开始批量更新所有股票的所有技术指标，请耐心等待...')
      
      // 调用批量更新API
      const response = await technicalAnalysisService.updateAllStocksIndicators()
      setBatchIndicatorsResult(response.data || response)
      
      if (response.success || response.data?.success) {
        message.success(`批量更新完成！成功: ${response.data?.results?.success_count || 0}, 失败: ${response.data?.results?.failed_count || 0}`)
      } else {
        message.error(`批量更新失败: ${response.message || 'Unknown error'}`)
      }
    } catch (error) {
      message.error(`Failed to update all stocks indicators: ${error.response?.data?.detail || 'Unknown error'}`)
    } finally {
      setIsBatchIndicatorsUpdating(false)
    }
  }

  const handleRecomputeAllStocksIndicators = async () => {
    try {
      setIsRecomputeIndicatorsUpdating(true)
      setRecomputeIndicatorsResult(null)
      
      message.info('开始重新计算所有股票的所有技术指标，请耐心等待...')
      
      // 调用重新计算API
      const response = await technicalAnalysisService.recomputeAllStocksIndicators()
      setRecomputeIndicatorsResult(response.data || response)
      
      if (response.success || response.data?.success) {
        message.success(`重新计算完成！成功: ${response.data?.results?.success_count || 0}, 失败: ${response.data?.results?.failed_count || 0}`)
      } else {
        message.error(`重新计算失败: ${response.message || 'Unknown error'}`)
      }
    } catch (error) {
      message.error(`Failed to recompute all stocks indicators: ${error.response?.data?.detail || 'Unknown error'}`)
    } finally {
      setIsRecomputeIndicatorsUpdating(false)
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
                <Button
                  type="primary"
                  danger
                  icon={<StopOutlined />}
                  onClick={handleStopFetch}
                  disabled={!isRunning}
                >
                  Stop Fetch
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

        <Card title="Batch Update All Stocks Indicators">
          <Space direction="vertical" style={{ width: '100%' }}>
            <p>一键更新所有股票的所有技术指标值</p>
            <Button 
              type="primary" 
              onClick={handleUpdateAllStocksIndicators}
              loading={isBatchIndicatorsUpdating}
            >
              Update All Stocks Indicators
            </Button>
            
            {batchIndicatorsResult && (
              <div style={{ marginTop: 16 }}>
                <strong>批量更新结果:</strong>
                <div>总股票数: {batchIndicatorsResult.results?.total_count}</div>
                <div>成功: {batchIndicatorsResult.results?.success_count}</div>
                <div>失败: {batchIndicatorsResult.results?.failed_count}</div>
              </div>
            )}
          </Space>
        </Card>

        <Card title="Recompute All Stocks Indicators">
          <Space direction="vertical" style={{ width: '100%' }}>
            <p>重新计算所有股票的所有技术指标值（从头开始计算，不考虑最新日期）</p>
            <Button 
              type="primary" 
              danger
              onClick={handleRecomputeAllStocksIndicators}
              loading={isRecomputeIndicatorsUpdating}
            >
              Recompute All Stocks Indicators
            </Button>
            
            {recomputeIndicatorsResult && (
              <div style={{ marginTop: 16 }}>
                <strong>重新计算结果:</strong>
                <div>总股票数: {recomputeIndicatorsResult.results?.total_count}</div>
                <div>成功: {recomputeIndicatorsResult.results?.success_count}</div>
                <div>失败: {recomputeIndicatorsResult.results?.failed_count}</div>
              </div>
            )}
          </Space>
        </Card>
      </Space>
    </div>
  )
}

export default DataFetch