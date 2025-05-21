import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import removeHorizontalScrollbars from './RemoveScrollbars';
import './index.css';

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