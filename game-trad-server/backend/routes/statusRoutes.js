const express = require('express');
const { getStatus, healthCheck, getDashboardData } = require('../controllers/statusController');

const router = express.Router();

// 获取服务详细状态
router.get('/', getStatus);

// 健康检查
router.get('/health', healthCheck);

// 获取仪表盘数据
router.get('/dashboard', getDashboardData);

// 获取物品价格趋势
router.get('/item-price-trend/:itemName', async (req, res) => {
  try {
    const { itemName } = req.params;
    const { period = 'day' } = req.query;
    
    const dbHelper = require('../utils/dbHelper');
    const trendData = await dbHelper.getItemPriceTrend(itemName, period);
    
    res.status(200).json({
      success: true,
      itemName,
      period,
      data: trendData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取物品价格趋势失败',
      error: error.message
    });
  }
});

// 获取所有物品列表
router.get('/items', async (req, res) => {
  try {
    const dbHelper = require('../utils/dbHelper');
    const items = await dbHelper.getAllItems();
    
    res.status(200).json({
      success: true,
      count: items.length,
      items
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取物品列表失败',
      error: error.message
    });
  }
});

// 获取交易监控数据
router.get('/trade-monitor', async (req, res) => {
  try {
    const dbHelper = require('../utils/dbHelper');
    const items = await dbHelper.getTradeMonitorData();
    
    res.status(200).json({
      success: true,
      count: items.length,
      items
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取交易监控数据失败',
      error: error.message
    });
  }
});

// 添加或更新交易监控数据
router.post('/trade-monitor', async (req, res) => {
  try {
    const monitorData = req.body;
    const dbHelper = require('../utils/dbHelper');
    const result = await dbHelper.saveTradeMonitorData(monitorData);
    
    res.status(200).json({
      success: true,
      message: '交易监控数据已保存',
      itemId: result.id
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '保存交易监控数据失败',
      error: error.message
    });
  }
});

// 删除交易监控数据
router.delete('/trade-monitor/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const dbHelper = require('../utils/dbHelper');
    await dbHelper.deleteTradeMonitorData(id);
    
    res.status(200).json({
      success: true,
      message: '交易监控数据已删除'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '删除交易监控数据失败',
      error: error.message
    });
  }
});

module.exports = router; 