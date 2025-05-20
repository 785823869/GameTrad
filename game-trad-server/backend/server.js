// Server.js

const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const path = require('path');
const fs = require('fs-extra');
const dotenv = require('dotenv');

// 加载环境变量配置
dotenv.config();

// 确保目录存在
const uploadDir = process.env.UPLOAD_DIR || './uploads';
const logDir = process.env.LOG_DIR || './logs';
fs.ensureDirSync(uploadDir);
fs.ensureDirSync(logDir);

// 初始化日志系统
const logger = require('./utils/logger');

// 创建Express实例
const app = express();
const PORT = process.env.PORT || 5000;

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));

// 静态文件
app.use(express.static(path.join(__dirname, '../public')));
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// API路由
app.get('/api', (req, res) => {
    res.json({ message: 'GameTrad API 服务运行中' });
});

// 健康检查
app.get('/api/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString()
    });
});

// 导入路由
const statusRoutes = require('./routes/statusRoutes');
const updateRoutes = require('./routes/updateRoutes');
const recipeRoutes = require('./routes/recipeRoutes');
const logRoutes = require('./routes/logRoutes');
const ocrRoutes = require('./routes/ocrRoutes');

// 使用路由
app.use('/api/status', statusRoutes);
app.use('/api/update', updateRoutes);
app.use('/api/recipes', recipeRoutes);
app.use('/api/logs', logRoutes);
app.use('/api/ocr', ocrRoutes);

// 在生产环境中提供React静态文件
if (process.env.NODE_ENV === 'production') {
    app.use(express.static(path.join(__dirname, '../frontend/react/build')));
    
    app.get('*', (req, res) => {
        res.sendFile(path.join(__dirname, '../frontend/react/build', 'index.html'));
    });
}

// 错误中间件
app.use((err, req, res, next) => {
    console.error(`Error: ${err.message}`);
    res.status(err.status || 500).json({
        message: err.message,
        stack: process.env.NODE_ENV === 'production' ? '🥞' : err.stack
    });
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
}); 