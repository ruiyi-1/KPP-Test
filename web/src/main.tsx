import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary'
import { initAnalytics, trackPageView } from './utils/analytics'
import './i18n/config'
import 'antd-mobile/es/global'

// 初始化统计
initAnalytics()

// 跟踪初始页面访问
trackPageView(window.location.pathname, 'KPP Test')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
