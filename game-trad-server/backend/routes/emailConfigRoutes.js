const express = require('express');
const router = express.Router();
const emailConfigController = require('../controllers/emailConfigController');

// 获取邮件配置
router.get('/email-config', emailConfigController.getEmailConfig);

// 保存邮件配置
router.post('/email-config', emailConfigController.saveEmailConfig);

// 测试邮件配置
router.post('/email-test', emailConfigController.testEmailConfig);

module.exports = router; 