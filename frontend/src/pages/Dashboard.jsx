import React from 'react'
import { Card, Row, Col, Statistic, Progress } from 'antd'
import { StockOutlined, RiseOutlined, FallOutlined, HeartOutlined } from '@ant-design/icons'

const Dashboard = () => {
  return (
    <div>
      <h1>Dashboard</h1>
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Stocks"
              value={4567}
              prefix={<StockOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="In Collection"
              value={23}
              prefix={<HeartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Today's Gainers"
              value={45}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Today's Losers"
              value={32}
              prefix={<FallOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="Data Sync Status" bordered={false}>
            <Progress percent={75} status="active" />
            <div style={{ marginTop: 16 }}>
              <p>Last Sync: 2024-01-15 14:30</p>
              <p>Next Sync: 2024-01-15 15:30</p>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Recent Activities" bordered={false}>
            <p>• Stock 000001.SZ updated</p>
            <p>• New trading signal detected</p>
            <p>• Data fetch completed</p>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
