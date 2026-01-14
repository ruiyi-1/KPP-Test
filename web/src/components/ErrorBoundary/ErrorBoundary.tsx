import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button, NavBar } from 'antd-mobile';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * 错误边界组件 - 捕获子组件树中的JavaScript错误
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 可以在这里记录错误到错误报告服务
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <NavBar back={null}>错误</NavBar>
          <div style={{ marginTop: '40px' }}>
            <h2>出现了一些问题</h2>
            <p style={{ color: '#666', marginTop: '16px' }}>
              应用程序遇到了一个错误。请刷新页面重试。
            </p>
            {import.meta.env.DEV && this.state.error && (
              <details style={{ marginTop: '20px', textAlign: 'left' }}>
                <summary style={{ cursor: 'pointer', color: '#1890ff' }}>
                  错误详情（开发模式）
                </summary>
                <pre
                  style={{
                    marginTop: '10px',
                    padding: '10px',
                    background: '#f5f5f5',
                    borderRadius: '4px',
                    overflow: 'auto',
                    fontSize: '12px',
                  }}
                >
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            <Button
              color="primary"
              style={{ marginTop: '24px' }}
              onClick={this.handleReset}
            >
              重试
            </Button>
            <Button
              color="primary"
              fill="outline"
              style={{ marginTop: '12px' }}
              onClick={() => window.location.reload()}
            >
              刷新页面
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
