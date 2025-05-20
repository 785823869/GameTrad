const express = require('express');
const { 
  checkUpdate, 
  downloadUpdate, 
  installUpdate, 
  getStatus 
} = require('../controllers/updateController');

const router = express.Router();

// 检查更新
router.post('/check', checkUpdate);

// 下载更新
router.post('/download', downloadUpdate);

// 安装更新
router.post('/install', installUpdate);

// 获取更新状态
router.get('/status', getStatus);

module.exports = router; 