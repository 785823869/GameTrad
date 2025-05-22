// Server.js

const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const path = require('path');
const fs = require('fs-extra');
const dotenv = require('dotenv');
const http = require('http');
const socketIo = require('socket.io');

// 加载环境变量配置
dotenv.config();

// --> ADDING LOGS HERE <--
console.log('[DEBUG] Current NODE_ENV:', process.env.NODE_ENV);
const staticPath = path.join(__dirname, '../frontend/react/build');
console.log('[DEBUG] Expected static files path:', staticPath);
fs.pathExists(staticPath, (err, exists) => {
  console.log('[DEBUG] Static path exists on server?:', exists, '(Error check:', err, ')');
  if (exists) {
    fs.pathExists(path.join(staticPath, 'index.html'), (err2, indexExists) => {
      console.log('[DEBUG] index.html exists in static path?:', indexExists, '(Error check:', err2, ')');
    });
  }
});
// --> END OF ADDED LOGS <--

// 设置时区为中国标准时间(UTC+8)
process.env.TZ = 'Asia/Shanghai';

// 确保目录存在
const uploadDir = process.env.UPLOAD_DIR || './uploads';
const logDir = process.env.LOG_DIR || './logs';
fs.ensureDirSync(uploadDir);
fs.ensureDirSync(logDir);

// 初始化日志系统
const logger = require('./utils/logger');

// 导入请求跟踪中间件
const requestTracker = require('./utils/requestTracker');

// 创建Express实例
const app = express();
const PORT = process.env.PORT || 5000;

// 创建HTTP服务器并添加Socket.IO支持
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// 将Socket.IO实例添加到app对象，以便在控制器中使用
app.set('io', io);

// Socket.IO连接处理
io.on('connection', (socket) => {
  logger.info(`新Socket连接建立: ${socket.id}`);
  
  socket.on('disconnect', () => {
    logger.info(`Socket连接断开: ${socket.id}`);
  });
});

// 中间件
app.use(cors());

// 添加请求跟踪中间件
app.use(requestTracker);

// 解析JSON请求体
app.use(express.json({
  verify: (req, res, buf) => {
    try {
      JSON.parse(buf);
    } catch (e) {
      logger.error(`无效的JSON请求体: ${e.message}`);
      res.status(400).json({ 
        success: false, 
        message: '无效的JSON格式' 
      });
      throw new Error('无效的JSON格式');
    }
  }
}));

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
const ocrRuleRoutes = require('./routes/ocrRuleRoutes');
const inventoryRoutes = require('./routes/inventoryRoutes');
const stockInRoutes = require('./routes/stockInRoutes');
const stockOutRoutes = require('./routes/stockOutRoutes');
const transactionRoutes = require('./routes/transactionRoutes');
const backupRoutes = require('./routes/backupRoutes');
const emailConfigRoutes = require('./routes/emailConfigRoutes');
const analyticsRoutes = require('./routes/analyticsRoutes');

// 使用路由
app.use('/api/status', statusRoutes);
app.use('/api/update', updateRoutes);
app.use('/api/recipes', recipeRoutes);
app.use('/api/logs', logRoutes);
app.use('/api/ocr', ocrRoutes);
app.use('/api/ocr-rules', ocrRuleRoutes);
app.use('/api/backup', backupRoutes);
app.use('/api/settings', emailConfigRoutes);
app.use('/api/analytics', analyticsRoutes);

// 库存相关路由 - 减少过多的日志输出
// 只在DEBUG日志级别时记录详细信息
app.use('/api/inventory', inventoryRoutes);
app.use('/api/stock-in', stockInRoutes);
app.use('/api/stock-out', stockOutRoutes);
app.use('/api/transactions', transactionRoutes);

// 在生产环境中提供React静态文件
if (process.env.NODE_ENV === 'production') {
    app.use(express.static(path.join(__dirname, '../frontend/react/build')));
    
    app.get('*', (req, res) => {
        res.sendFile(path.join(__dirname, '../frontend/react/build', 'index.html'));
    });
}

// 错误中间件
app.use((err, req, res, next) => {
    logger.error(`Express错误: ${err.message}`);
    logger.error(`错误堆栈: ${err.stack}`);
    
    res.status(err.status || 500).json({
        success: false,
        message: err.message,
        stack: process.env.NODE_ENV === 'production' ? '🥞' : err.stack
    });
});

// 启动服务器
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    logger.info(`服务器启动成功，监听端口 ${PORT}`);
});