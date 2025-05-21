const express = require('express');
const { 
  getInventory, 
  recalculateInventory, 
  exportInventory, 
  deleteInventoryItem,
  getZeroInventoryItems
} = require('../controllers/inventoryController');

const router = express.Router();

// 获取所有库存数据
router.get('/', getInventory);

// 重新计算库存
router.post('/recalculate', recalculateInventory);

// 导出库存数据
router.get('/export', exportInventory);

// 获取零库存或负库存物品
router.get('/zero', getZeroInventoryItems);

// 删除库存项
router.delete('/:id', deleteInventoryItem);

module.exports = router; 