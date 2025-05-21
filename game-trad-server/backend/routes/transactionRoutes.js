const express = require('express');
const { 
  getTransactions, 
  addTransaction, 
  updateTransaction, 
  deleteTransaction,
  importTransactions
} = require('../controllers/transactionController');

const router = express.Router();

// 获取所有交易记录
router.get('/', getTransactions);

// 添加交易记录
router.post('/', addTransaction);

// 更新交易记录
router.put('/:id', updateTransaction);

// 删除交易记录
router.delete('/:id', deleteTransaction);

// OCR导入交易记录
router.post('/import', importTransactions);

module.exports = router; 