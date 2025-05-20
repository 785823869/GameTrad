const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs-extra');
const { processImage, getOcrHistory } = require('../controllers/ocrController');

const router = express.Router();

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
router.post('/', upload.single('image'), processImage);

// 获取OCR历史记录
router.get('/history', getOcrHistory);

module.exports = router; 