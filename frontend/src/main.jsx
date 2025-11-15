import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider, App as AntApp } from 'antd'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// 修复样式表问题
const fixStylesheetIssue = () => {
  // 确保DOM已经加载
  if (typeof document !== 'undefined') {
    // 检查是否已存在样式元素
    if (!document.getElementById('grape-finance-fix')) {
      // 创建一个空的样式元素
      const style = document.createElement('style');
      style.id = 'grape-finance-fix';
      style.type = 'text/css';
      
      // 添加到head中
      document.head.appendChild(style);
    }
  }
};

// 应用修复
fixStylesheetIssue();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#722ed1',
        },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>
)