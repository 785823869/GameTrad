const express = require('express');
const { 
  getStockOut, 
  addStockOut, 
  updateStockOut, 
  deleteStockOut,
  importStockOut
} = require('../controllers/stockOutController');

const router = express.Router();

// 获取所有出库记录
router.get('/', getStockOut);

// 添加出库记录
router.post('/', addStockOut);

// 更新出库记录
router.put('/:id', updateStockOut);

// 删除出库记录
router.delete('/:id', deleteStockOut);

// OCR导入出库记录
router.post('/import', importStockOut);

module.exports = router; 