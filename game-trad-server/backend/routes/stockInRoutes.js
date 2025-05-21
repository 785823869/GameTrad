const express = require('express');
const { 
  getStockIn, 
  addStockIn, 
  updateStockIn, 
  deleteStockIn,
  importStockIn
} = require('../controllers/stockInController');

const router = express.Router();

// 获取所有入库记录
router.get('/', getStockIn);

// 添加入库记录
router.post('/', addStockIn);

// 更新入库记录
router.put('/:id', updateStockIn);

// 删除入库记录
router.delete('/:id', deleteStockIn);

// OCR导入入库记录
router.post('/import', importStockIn);

module.exports = router; 