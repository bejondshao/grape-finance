import React, { useState } from 'react'
import {
  Layout,
  Menu,
  Button,
  theme,
  Avatar,
  Dropdown,
  Space
} from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  StockOutlined,
  PayCircleOutlined,
  HeartOutlined,
  LineChartOutlined,
  TransactionOutlined,
  SettingOutlined,
  SyncOutlined,
  UserOutlined,
  SearchOutlined
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content } = Layout

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const {
    token: { colorBgContainer },
  } = theme.useToken()

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/stocks',
      icon: <StockOutlined />,
      label: 'Stock List',
    },
    {
      key: '/collection',
      icon: <HeartOutlined />,
      label: 'Stock Collection',
    },
    {
      key: '/technical-analysis',
      icon: <LineChartOutlined />,
      label: 'Technical Analysis',
    },
    {
      key: '/stock-view',
      icon: <SearchOutlined />,
      label: 'Stock View',
    },
    {
      key: '/trading-strategy',
      icon: <PayCircleOutlined />,
      label: 'Trading Strategy',
    },
    {
      key: '/trading-records',
      icon: <TransactionOutlined />,
      label: 'Trading Records',
    },
    {
      key: '/data-fetch',
      icon: <SyncOutlined />,
      label: 'Data Fetch',
    },
    {
      key: '/configuration',
      icon: <SettingOutlined />,
      label: 'Configuration',
    },
  ]

  const userMenuItems = [
    {
      key: '1',
      label: 'Profile',
    },
    {
      key: '2',
      label: 'Settings',
    },
    {
      type: 'divider',
    },
    {
      key: '3',
      label: 'Logout',
    },
  ]

  return (
    <Layout className="layout-container">
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div className="demo-logo-vertical" style={{ 
          height: 32, 
          margin: 16, 
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold'
        }}>
          {collapsed ? 'GF' : 'Grape Finance'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: 0, 
          background: colorBgContainer,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingRight: 24
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: '16px',
              width: 64,
              height: 64,
            }}
          />
          <Space>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ 
          margin: '24px 16px', 
          padding: 24, 
          minHeight: 280,
          background: colorBgContainer,
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
