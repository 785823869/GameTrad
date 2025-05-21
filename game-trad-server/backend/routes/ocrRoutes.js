const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs-extra');
const ocrController = require('../controllers/ocrController');
const { requireAuth } = require('../middleware/authMiddleware');

const router = express.Router();

/**
 * OCR相关路由
 * 与前端OCRService.js对应
 */

// 配置multer存储设置
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadDir = process.env.UPLOAD_DIR || './uploads';
    fs.ensureDirSync(uploadDir);
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    // 使用时间戳+原始文件名来保存文件
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, `ocr-${uniqueSuffix}${path.extname(file.originalname)}`);
  }
});

// 文件过滤器
const fileFilter = (req, file, cb) => {
  // 只接受特定的图片格式
  const allowedTypes = /jpeg|jpg|png|gif/;
  const mimetype = allowedTypes.test(file.mimetype);
  const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());

  if (mimetype && extname) {
    cb(null, true);
  } else {
    cb(new Error('只支持图片格式: jpeg, jpg, png, gif'), false);
  }
};

// 创建multer实例
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 5 * 1024 * 1024 // 限制为5MB
  },
  fileFilter: fileFilter
});

// 上传图片并进行OCR识别
router.post('/', upload.single('image'), ocrController.processImage);

// 获取OCR历史记录
router.get('/history', ocrController.getOcrHistory);

/**
 * @route   POST /api/ocr/recognize
 * @desc    识别图片中的文本并解析结构化数据
 * @access  Public
 */
router.post('/recognize', upload.single('image'), ocrController.recognize);

/**
 * @route   POST /api/ocr/extract-text
 * @desc    从图片中提取原始文本
 * @access  Public
 */
router.post('/extract-text', upload.single('image'), ocrController.extractText);

/**
 * @route   GET /api/ocr/rules/active
 * @desc    获取所有活跃的OCR规则
 * @access  Private
 */
router.get('/rules/active', requireAuth, ocrController.getActiveRules);

module.exports = router; 