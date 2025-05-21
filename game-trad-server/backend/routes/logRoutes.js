const express = require('express');
const { getRecentLogs, getLogsByDate, addLog, getOperationLogs } = require('../controllers/logController');

const router = express.Router();

// 获取最近的日志
router.get('/:type?', getRecentLogs);

// 按日期获取日志
router.get('/date/:date', getLogsByDate);

// 获取操作日志
router.get('/operations', getOperationLogs);

// 添加一条日志（测试用）
router.post('/', addLog);

module.exports = router; 