/**
 * analyticsRoutes.js - 交易分析数据API路由
 */

const express = require('express');
const router = express.Router();
const analyticsController = require('../controllers/analyticsController');

// 获取交易分析汇总数据
router.get('/trade-analytics', analyticsController.getTradeAnalytics);

// 获取成交量数据
router.get('/volume', analyticsController.getVolumeData);

// 获取利润率排行数据
router.get('/profit-ranking', analyticsController.getProfitRanking);

// 获取滞销品数据
router.get('/slow-moving', analyticsController.getSlowMovingItems);

// 获取交易税统计数据
router.get('/tax-summary', analyticsController.getTradeTaxSummary);

module.exports = router; 