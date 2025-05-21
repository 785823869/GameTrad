import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import removeHorizontalScrollbars from './RemoveScrollbars';
import './index.css';
import disableConsole from './utils/disableConsole';
import logger from './utils/LogConfig';

// 在生产环境中禁用多余的控制台日志
disableConsole();

// 设置日志级别为ERROR，减少不必要的日志输出
logger.setLevel(logger.LogLevels?.ERROR || 'error');

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// 等待DOM完全加载后执行滚动条修复
window.addEventListener('load', () => {
  setTimeout(removeHorizontalScrollbars, 500);
}); 