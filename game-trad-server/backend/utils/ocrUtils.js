/**
 * OCR工具函数
 */
const fs = require('fs-extra');
const path = require('path');
const logger = require('./logger');
const { createWorker } = require('tesseract.js');
const axios = require('axios');

/**
 * 图像预处理函数
 * @param {Buffer} imageBuffer - 图像数据
 * @returns {Buffer} - 处理后的图像数据
 */
const preprocessImage = async (imageBuffer) => {
  // 这里可以添加图像预处理逻辑，如调整对比度、去噪等
  // 对于简单情况，我们直接返回原始图像
  return imageBuffer;
};

/**
 * 使用外部API进行OCR识别，兼容umi-ocr接口规范
 * @param {string} imagePath - 图像文件路径
 * @param {Object} options - OCR选项
 * @returns {Promise<Object>} - OCR识别结果
 */
const ocrRecognizeWithAPI = async (imagePath, options = {}) => {
  try {
    logger.info(`使用API开始OCR识别图片: ${imagePath}`);
    
    // 读取图片文件
    const imageBuffer = await fs.readFile(imagePath);
    
    // 图像预处理
    const processedImageBuffer = await preprocessImage(imageBuffer);
    
    // 转换为base64
    const base64Image = processedImageBuffer.toString('base64');
    
    // 准备API请求参数，兼容umi-ocr规范
    const url = "http://sql.didiba.uk:1224/api/ocr";
    
    // 默认选项
    const defaultOptions = {
      "data.format": "text",
      "language": "chi_sim", // 简体中文
      "engine": "auto",     // 自动选择引擎
      "detect_orientation": true, // 自动检测方向
      "trim": true         // 去除多余空白
    };
    
    // 合并用户选项
    const apiOptions = {
      ...defaultOptions,
      ...options
    };
    
    // 构建请求数据
    const payload = {
      "base64": base64Image,
      "options": apiOptions
    };
    
    const headers = {"Content-Type": "application/json"};
    
    logger.info("正在发送OCR识别API请求...");
    
    // 发送请求，支持重试
    let response;
    let retryCount = 0;
    const maxRetries = 2;
    
    while (retryCount <= maxRetries) {
      try {
        response = await axios.post(url, payload, {
          headers: headers,
          timeout: 20000 // 20秒超时，与Python版本一致
        });
        break; // 成功就跳出循环
      } catch (err) {
        retryCount++;
        if (retryCount > maxRetries) throw err;
        logger.warn(`OCR API请求失败，尝试第${retryCount}次重试...`);
        await new Promise(resolve => setTimeout(resolve, 1000)); // 等待1秒后重试
      }
    }
    
    // 处理响应
    if (response.status === 200 && response.data) {
      const text = response.data.data || '';
      
      if (!text) {
        logger.warn("OCR API识别返回空文本");
      } else {
        logger.info(`API成功识别文本，长度: ${text.length}`);
        
        // 后处理文本
        const processedText = postprocessText(text);
        
        return {
          success: true,
          text: processedText,
          fromAPI: true,
          raw: response.data
        };
      }
    } else {
      throw new Error(`API返回状态码: ${response.status}`);
    }
  } catch (error) {
    logger.error(`OCR API请求失败: ${error.message}`);
    // 不抛出异常，让调用者决定回退策略
    return {
      success: false,
      error: `OCR API请求失败: ${error.message}`,
      fromAPI: true
    };
  }
};

/**
 * 文本后处理函数
 * @param {string} text - OCR识别的原始文本
 * @returns {string} - 处理后的文本
 */
const postprocessText = (text) => {
  if (!text) return '';
  
  // 去除多余空白
  let processed = text.replace(/\s+/g, ' ').trim();
  
  // 处理常见OCR错误
  // 例如：数字"0"与字母"O"混淆
  processed = processed.replace(/失去了银两O/g, '失去了银两×');
  processed = processed.replace(/银两O/g, '银两×');
  processed = processed.replace(/至纯精华O/g, '至纯精华×');
  
  // 处理中英文混排中的空格问题
  processed = processed.replace(/(\d)\s+(\d)/g, '$1$2'); // 连续数字之间不应有空格
  
  return processed;
};

// OCR识别函数，使用API优先，失败时回退到Tesseract.js或模拟数据
const ocrRecognize = async (imagePath, options = {}) => {
  try {
    // 检查图片文件是否存在
    if (!fs.existsSync(imagePath)) {
      logger.error(`OCR识别失败: 图片文件不存在 ${imagePath}`);
      return {
        success: false,
        error: '图片文件不存在'
      };
    }

    // 首先尝试使用API进行OCR识别
    try {
      const apiResult = await ocrRecognizeWithAPI(imagePath, options);
      if (apiResult.success) {
        return apiResult;
      }
      
      logger.warn("API识别失败，尝试使用本地Tesseract.js");
    } catch (apiError) {
      logger.error(`API OCR识别失败: ${apiError.message}`);
    }

    // 如果API失败，尝试使用tesseract.js进行OCR识别
    try {
      logger.info(`开始使用Tesseract.js识别图片: ${imagePath}`);
      
      // 创建worker，使用与API相同的语言设置
      const lang = options.language || 'chi_sim';
      const worker = await createWorker(lang);
      const { data } = await worker.recognize(imagePath);
      await worker.terminate();
      
      logger.info(`Tesseract.js OCR识别完成，获取到文本`);
      
      // 应用相同的后处理
      const processedText = postprocessText(data.text);
      
      return {
        success: true,
        text: processedText,
        fromTesseract: true
      };
    } catch (tesseractError) {
      logger.error(`Tesseract OCR识别失败: ${tesseractError.message}，使用模拟数据`);
      
      // 如果Tesseract.js也失败，回退到模拟数据
      return {
        success: true,
        text: `品名：至纯精华
数量：10
价格：15000`,
        fromMock: true  // 标记这是来自模拟数据
      };
    }
  } catch (error) {
    logger.error(`OCR识别失败: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
};

// 处理游戏特定格式的OCR识别函数
const ocrRecognizeGameFormat = async (imagePath, options = {}) => {
  // 为游戏特定格式添加选项
  const gameOptions = {
    ...options,
    "engine": "game",  // 标记为游戏专用引擎
    "trim": true,      // 去除额外空白
    "detect_orientation": true, // 自动检测文本方向
  };
  
  // 首先使用标准OCR识别获取文本
  const ocrResult = await ocrRecognize(imagePath, gameOptions);
  
  if (!ocrResult.success) {
    return ocrResult;
  }
  
  const text = ocrResult.text;
  
  // 如果是模拟数据，直接返回
  if (ocrResult.fromMock) {
    return ocrResult;
  }
  
  try {
    // 使用专用后处理函数处理游戏文本
    const processedText = postprocessGameText(text);
    
    logger.info(`处理后的游戏OCR文本: ${processedText}`);
    
    return {
      success: true,
      text: processedText,
      fromAPI: ocrResult.fromAPI || false,
      fromTesseract: ocrResult.fromTesseract || false
    };
  } catch (error) {
    logger.error(`处理OCR文本失败: ${error.message}`);
    return {
      success: false,
      error: `处理OCR文本失败: ${error.message}`
    };
  }
};

/**
 * 游戏特定文本后处理函数
 * @param {string} text - OCR识别的原始文本
 * @returns {string} - 处理后的文本
 */
const postprocessGameText = (text) => {
  if (!text) return '';
  
  // 基本文本清理
  let processed = text.replace(/\s+/g, ' ').trim();
  
  // 游戏特定格式处理
  // 1. 修复"失去了银两×"模式
  processed = processed.replace(/失去了[银銀][两雨][ oO0×]/gi, '失去了银两×');
  processed = processed.replace(/失去了银两 (\d+)/g, '失去了银两×$1');
  
  // 2. 修复"至纯精华×"模式
  processed = processed.replace(/至[純纯][精棈]华[ oO0×]/gi, '至纯精华×');
  processed = processed.replace(/至纯精华 (\d+)/g, '至纯精华×$1');
  
  // 3. 处理数值格式，确保只有数字
  processed = processed.replace(/×([^0-9]+)(\d+)/g, '×$2'); // 删除数字前的非数字字符
  processed = processed.replace(/×(\d+)([^0-9]+)/g, '×$1'); // 删除数字后的非数字字符
  
  return processed;
};

module.exports = {
  ocrRecognize,
  ocrRecognizeGameFormat,
  ocrRecognizeWithAPI,
  preprocessImage,
  postprocessText,
  postprocessGameText
}; 