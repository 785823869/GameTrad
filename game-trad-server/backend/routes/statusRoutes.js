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

module.exports = router; 