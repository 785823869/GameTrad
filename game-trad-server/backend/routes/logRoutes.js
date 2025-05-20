const express = require('express');
const { getRecentLogs, getLogsByDate, addLog } = require('../controllers/logController');

const router = express.Router();

// 获取最近的日志
router.get('/', getRecentLogs);

// 按日期获取日志
router.get('/date/:date', getLogsByDate);

// 添加一条日志（测试用）
router.post('/', addLog);

module.exports = router; 