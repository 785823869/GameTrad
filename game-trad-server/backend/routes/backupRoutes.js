const express = require('express');
const router = express.Router();
const backupController = require('../controllers/backupController');

// 获取备份列表
router.get('/list', backupController.getBackupList);

// 获取备份设置
router.get('/settings', backupController.getBackupSettings);

// 保存备份设置
router.post('/settings', backupController.saveBackupSettings);

// 创建新备份
router.post('/create', backupController.createBackup);

// 恢复备份
router.post('/restore', backupController.restoreBackup);

// 删除备份
router.delete('/delete/:filename', backupController.deleteBackup);

// 下载备份
router.get('/download/:filename', backupController.downloadBackup);

// 清理旧备份
router.post('/cleanup', backupController.cleanupOldBackups);

module.exports = router; 