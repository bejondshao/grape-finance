import React from 'react';
import { Layout, Menu, theme, Typography } from 'antd';
import { 
  StockOutlined, 
  LineChartOutlined, 
  StrategyOutlined, 
  FolderOutlined,
  SettingOutlined,
  HistoryOutlined 
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const menuItems = [
    {
      key: '/stocks',
      icon: <StockOutlined />,
      label: '股票列表',
    },
    {
      key: '/technical',
      icon: <LineChartOutlined />,
      label: '技术分析',
    },
    {
      key: '/strategies',
      icon: <StrategyOutlined />,
      label: '交易策略',
    },
    {
      key: '/collections',
      icon: <FolderOutlined />,
      label: '股票收藏',
    },
    {
      key: '/records',
      icon: <HistoryOutlined />,
      label: '交易记录',
    },
    {
      key: '/config',
      icon: <SettingOutlined />,
      label: '系统配置',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" collapsible>
        <div style={{ 
          height: 32, 
          margin: 16, 
          background: 'rgba(255, 255, 255, 0.2)', 
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Title level={4} style={{ color: 'white', margin: 0, fontSize: 16 }}>
            Grape Finance
          </Title>
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: 0, 
          background: colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          paddingLeft: 24
        }}>
          <Title level={3} style={{ margin: 0 }}>
            {menuItems.find(item => item.key === location.pathname)?.label || 'Grape Finance'}
          </Title>
        </Header>
        <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
          <div
            style={{
              padding: 24,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
              minHeight: 360,
            }}
          >
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
