const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');

/**
 * 模拟OCR识别函数 - 替代原Python OCR功能
 * @param {string} imagePath - 图片路径
 * @returns {Promise<string>} - 识别的文本结果
 */
const performOCR = async (imagePath) => {
  // 这里模拟OCR识别过程，实际项目中可以调用OCR API或使用第三方库如Tesseract.js
  logger.info(`执行OCR识别: ${imagePath}`);
  
  // 模拟处理延迟
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 模拟返回识别结果
  // 根据不同图片类型返回不同的模拟结果
  const ext = path.extname(imagePath).toLowerCase();
  
  let result = '';
  if (ext === '.png') {
    result = '物品: 女娲石\n数量: 100\n价格: 3.5';
  } else if (ext === '.jpg' || ext === '.jpeg') {
    result = '物品: 银两\n数量: 1000\n价格: 2.8';
  } else {
    result = '无法识别的图片格式';
  }
  
  logger.info(`OCR识别结果: ${result}`);
  return result;
};

/**
 * 处理图片上传和OCR识别
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.processImage = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: '没有上传图片' });
    }
    
    const imagePath = req.file.path;
    logger.info(`接收到图片上传: ${imagePath}`);
    
    // 执行OCR识别
    const recognizedText = await performOCR(imagePath);
    
    // 解析识别文本为结构化数据
    const lines = recognizedText.split('\n');
    const result = {};
    
    lines.forEach(line => {
      const [key, value] = line.split(':').map(item => item.trim());
      if (key && value) {
        result[key] = value;
      }
    });
    
    // 返回识别结果
    res.status(200).json({
      success: true,
      rawText: recognizedText,
      parsed: result,
      imageUrl: `/uploads/${path.basename(imagePath)}`
    });
  } catch (error) {
    logger.error(`OCR处理错误: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '图片处理失败',
      error: error.message
    });
  }
};

/**
 * 获取历史OCR记录（示例功能）
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getOcrHistory = async (req, res) => {
  try {
    // 这里可以实现从数据库或日志中获取历史OCR记录
    // 本示例返回模拟数据
    res.status(200).json({
      success: true,
      history: [
        {
          id: '1',
          date: '2023-11-22T10:30:00Z',
          imageUrl: '/uploads/sample1.jpg',
          result: '物品: 银两\n数量: 1000\n价格: 2.8'
        },
        {
          id: '2',
          date: '2023-11-21T14:15:00Z',
          imageUrl: '/uploads/sample2.png',
          result: '物品: 女娲石\n数量: 100\n价格: 3.5'
        }
      ]
    });
  } catch (error) {
    logger.error(`获取OCR历史记录错误: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取历史记录失败',
      error: error.message
    });
  }
}; 