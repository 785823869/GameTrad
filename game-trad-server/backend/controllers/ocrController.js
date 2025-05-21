const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const multer = require('multer');
const logger = require('../utils/logger');

/**
 * 模拟OCR识别函数 - 替代原Python OCR功能
 * @param {string} imagePath - 图片路径
 * @returns {Promise<string>} - 识别的文本结果
 */
const performOCR = async (imagePath) => {
  // 使用真实OCR API替换模拟功能
  logger.info(`执行OCR识别: ${imagePath}`);

  try {
    // 读取图片文件
    const imageBuffer = fs.readFileSync(imagePath);
    
    // 转换为base64
    const base64Image = imageBuffer.toString('base64');
    
    // 构建OCR API请求 - 与ocr.py相同的API端点
    const ocrApiUrl = 'http://sql.didiba.uk:1224/api/ocr';
    const payload = {
      base64: base64Image,
      options: {
        'data.format': 'text'
      }
    };
    
    logger.info('发送OCR识别请求...');
    const response = await axios.post(ocrApiUrl, payload, {
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 20000 // 20秒超时
    });
    
    if (response.data && response.data.data) {
      const rawText = response.data.data;
      logger.info(`OCR识别结果: ${rawText}`);
      return rawText;
    } else {
      logger.warn('OCR API返回空数据');
      return '无法识别';
    }
  } catch (error) {
    logger.error(`OCR API请求失败: ${error.message}`);
    throw new Error(`OCR识别失败: ${error.message}`);
  }
};

/**
 * 解析OCR文本，提取有用的字段
 * 参考客户端的三种解析方法，增强识别能力
 * @param {string} text OCR识别的原始文本
 * @return {object} 结构化数据
 */
function parseOcrText(text) {
  logger.info('开始解析OCR文本...');
  
  // 依次尝试三种解析方法
  let result = parseOcrTextV3(text);
  if (result) {
    logger.info('使用V3方法成功解析OCR文本');
    return result;
  }
  
  result = parseOcrTextV2(text);
  if (result) {
    logger.info('使用V2方法成功解析OCR文本');
    return result;
  }
  
  result = parseOcrTextV1(text);
  if (result) {
    logger.info('使用V1方法成功解析OCR文本');
    return result;
  }
  
  // 如果所有解析方法都失败，返回默认值
  logger.warn('所有OCR解析方法均失败，返回默认值');
  return {
    item_name: text.split('\n')[0] || '未知物品',
    quantity: 0,
    price: 0,
  };
}

/**
 * 通用解析方法(V1)
 * @param {string} text OCR识别的原始文本
 * @return {object|null} 解析结果或null
 */
function parseOcrTextV1(text) {
  if (!text || !text.trim()) {
    return null;
  }
  
  // 默认提取结果
  const result = {
    item_name: '',
    quantity: 0,
    price: 0,
    unit_price: 0,
    fee: 0,
    total_amount: 0
  };
  
  try {
    // 分行处理文本
    const lines = text.split('\n').map(line => line.trim()).filter(Boolean);
    
    // 扩展关键字匹配范围，参考客户端实现
    const itemKeywords = ['品名', '物品', '物品名称', '道具', '道具名称', '商品', '商品名称'];
    const quantityKeywords = ['数量', '个数', '件数', '数目', '出售数量', '出库数量'];
    const priceKeywords = ['单价', '价格', '单价格', '出售价格', '出售单价', '出库价格', '出库单价', '每个价格'];
    const feeKeywords = ['手续费', '费用', '交易费', '平台费', '服务费', '税费'];
    
    // 提取物品名称 (通常是第一行或包含关键词的行)
    let foundItemName = false;
    
    for (const line of lines) {
      // 检查是否包含物品关键词
      if (!foundItemName && itemKeywords.some(keyword => line.includes(keyword))) {
        // 尝试找到冒号后的内容
        const match = line.match(/[：:]+\s*(.+)$/) || 
                     line.match(new RegExp(`(${itemKeywords.join('|')})[^：:]*[：:]*\\s*(.+)$`));
        
        if (match) {
          result.item_name = match[match.length - 1].trim();
          foundItemName = true;
        }
      }
      
      // 检查是否包含数量关键词
      if (quantityKeywords.some(keyword => line.includes(keyword))) {
        const match = line.match(/[：:]+\s*([\d,]+)/) ||
                     line.match(new RegExp(`(${quantityKeywords.join('|')})[^：:]*[：:]*\\s*(\\d+)`));
        
        if (match) {
          const qtyStr = match[match.length - 1].replace(/,/g, '');
          result.quantity = parseInt(qtyStr, 10);
        }
      }
      
      // 检查是否包含价格关键词
      if (priceKeywords.some(keyword => line.includes(keyword))) {
        const match = line.match(/[：:]+\s*([\d,.]+)/) ||
                     line.match(new RegExp(`(${priceKeywords.join('|')})[^：:]*[：:]*\\s*([\\d,.]+)`));
        
        if (match) {
          const priceStr = match[match.length - 1].replace(/,/g, '');
          result.price = parseFloat(priceStr);
          result.unit_price = parseFloat(priceStr);
        }
      }
      
      // 检查是否包含手续费关键词
      if (feeKeywords.some(keyword => line.includes(keyword))) {
        const match = line.match(/[：:]+\s*([\d,.]+)/) ||
                     line.match(new RegExp(`(${feeKeywords.join('|')})[^：:]*[：:]*\\s*([\\d,.]+)`));
        
        if (match) {
          const feeStr = match[match.length - 1].replace(/,/g, '');
          result.fee = parseFloat(feeStr);
        }
      }
    }
    
    // 提取物品名称（如果上面没找到）
    if (!result.item_name && lines.length > 0) {
      result.item_name = lines[0].trim().replace(/[:：].*$/, '').trim();
    }
    
    // 如果没有找到有效值，提取可能的数字作为价格和数量
    if (result.quantity === 0 || result.price === 0) {
      // 提取所有数字
      const numbers = [];
      const numberMatches = text.match(/\d+(\.\d+)?/g);
      
      if (numberMatches) {
        numberMatches.forEach(num => {
          numbers.push(parseFloat(num));
        });
        
        // 按大小排序
        numbers.sort((a, b) => a - b);
        
        // 如果没有数量，取最小的整数
        if (result.quantity === 0 && numbers.length > 0) {
          for (const num of numbers) {
            if (Number.isInteger(num) && num > 0 && num < 1000) {
              result.quantity = num;
              break;
            }
          }
          if (result.quantity === 0 && numbers.length > 0) {
            result.quantity = Math.round(numbers[0]);
          }
        }
        
        // 如果没有价格，取剩余数字中较大的一个
        if (result.price === 0 && numbers.length > 0) {
          // 过滤掉已用作数量的数字
          const remainingNumbers = numbers.filter(n => n !== result.quantity);
          if (remainingNumbers.length > 0) {
            // 取中间值或较大值作为价格
            const index = Math.min(Math.floor(remainingNumbers.length / 2), remainingNumbers.length - 1);
            result.price = remainingNumbers[index];
            result.unit_price = result.price;
          }
        }
      }
    }
    
    // 计算总金额
    if (result.quantity > 0 && result.unit_price > 0) {
      result.total_amount = result.quantity * result.unit_price - result.fee;
    }
    
    // 确保物品名称不为空
    if (!result.item_name) {
      return null;
    }
    
    // 验证必要字段是否存在
    if (result.quantity > 0 && (result.price > 0 || result.unit_price > 0)) {
      return result;
    }
  } catch (error) {
    logger.error('解析OCR文本V1出错:', error);
  }
  
  return null;
}

/**
 * 特定格式解析方法(V2) - 针对"已成功售出灵之精火（66）。售出单价：1388银两：手续费：4581银两："格式
 * @param {string} text OCR识别的原始文本
 * @return {object|null} 解析结果或null
 */
function parseOcrTextV2(text) {
  if (!text || !text.trim()) {
    return null;
  }
  
  try {
    // 提取物品名称和数量
    const itemMatch = text.match(/已成功售出([^（(]+)[（(](\d+)[）)]/);
    if (!itemMatch) {
      return null;
    }
    
    const itemName = itemMatch[1].trim();
    const quantity = parseInt(itemMatch[2], 10);
    
    // 提取单价
    const priceMatch = text.match(/售出单价[：:]\s*(\d+)银两/);
    const unitPrice = priceMatch ? parseInt(priceMatch[1], 10) : 0;
    
    // 提取手续费 - 手续费可以为空
    const feeMatch = text.match(/手续费[：:]\s*(\d+)银两/);
    const fee = feeMatch ? parseInt(feeMatch[1], 10) : 0;
    
    if (itemName && quantity > 0 && unitPrice > 0) {
      // 计算总金额
      const totalAmount = quantity * unitPrice - fee;
      
      return {
        item_name: itemName,
        quantity: quantity,
        price: unitPrice,
        unit_price: unitPrice,
        fee: fee,
        total_amount: totalAmount,
        note: ''  // 添加空备注字段
      };
    }
  } catch (error) {
    logger.error('解析OCR文本V2出错:', error);
  }
  
  return null;
}

/**
 * 最新格式解析方法(V3) - 针对"已成功售出60诛仙古玉，请在附件中领取已计算相关费用后的收益。 136116"格式
 * @param {string} text OCR识别的原始文本
 * @return {object|null} 解析结果或null
 */
function parseOcrTextV3(text) {
  if (!text || !text.trim()) {
    return null;
  }
  
  try {
    // 提取物品名称和数量
    // 模式: 已成功售出[数量][物品名]，请在附件中领取...
    const itemMatch = text.match(/已成功售出(\d+)([^，,。]+)[，,。]/);
    if (!itemMatch) {
      return null;
    }
    
    const quantity = parseInt(itemMatch[1], 10);
    const itemName = itemMatch[2].trim();
    
    // 提取总金额 - 通常是文本末尾的数字
    const amountMatch = text.match(/(\d+)\s*$/);
    const totalAmount = amountMatch ? parseInt(amountMatch[1], 10) : 0;
    
    if (itemName && quantity > 0 && totalAmount > 0) {
      // 计算单价（总金额除以数量）
      const unitPrice = totalAmount / quantity;
      
      return {
        item_name: itemName,
        quantity: quantity,
        price: unitPrice,
        unit_price: unitPrice,
        fee: 0,  // 手续费默认为0
        total_amount: totalAmount,
        note: ''  // 备注默认为空
      };
    }
  } catch (error) {
    logger.error('解析OCR文本V3出错:', error);
  }
  
  return null;
}

/**
 * OCR控制器
 */
const ocrController = {
  /**
   * 处理图片上传和OCR识别 (旧API保持兼容)
   * @param {Object} req - 请求对象
   * @param {Object} res - 响应对象
   */
  processImage: async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ message: '没有上传图片' });
      }
      
      const imagePath = req.file.path;
      logger.info(`接收到图片上传: ${imagePath}`);
      
      // 执行OCR识别
      const recognizedText = await performOCR(imagePath);
      
      // 解析识别文本为结构化数据
      const extractedData = parseOcrText(recognizedText);
      
      // 返回识别结果
      res.status(200).json({
        success: true,
        rawText: recognizedText,
        parsed: extractedData,
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
  },
  
  /**
   * 获取历史OCR记录（示例功能）
   * @param {Object} req - 请求对象
   * @param {Object} res - 响应对象
   */
  getOcrHistory: async (req, res) => {
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
  },
  
  /**
   * 识别图片中的文本
   * POST /api/ocr/recognize
   */
  recognize: async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ 
          success: false, 
          message: '未提供图片文件' 
        });
      }

      try {
        // 读取上传的文件
        const imagePath = req.file.path;
        
        // 执行OCR识别
        const rawText = await performOCR(imagePath);
        
        logger.info(`OCR原始文本: ${rawText.substring(0, 100)}${rawText.length > 100 ? '...' : ''}`);
        
        // 使用增强的解析方法
        const extractedData = parseOcrText(rawText);
        
        logger.info(`OCR解析结果: ${JSON.stringify(extractedData)}`);
        
        // 检查是否成功解析出有效结果
        if (!extractedData || 
            (extractedData.item_name === '未知物品' && extractedData.quantity === 0)) {
          return res.status(400).json({
            success: false,
            message: '无法识别出有效的出库记录数据',
            rawText: rawText
          });
        }
        
        // 确保有物品名称和数量
        if (!extractedData.item_name || !extractedData.quantity) {
          const defaultItemName = rawText.split('\n')[0] || '未识别物品';
          
          // 补充默认值
          if (!extractedData.item_name) extractedData.item_name = defaultItemName;
          if (!extractedData.quantity) extractedData.quantity = 1;
          
          logger.warn(`OCR结果不完整，已添加默认值: ${JSON.stringify(extractedData)}`);
        }
        
        // 确保至少有价格信息
        if (!extractedData.price && !extractedData.unit_price && !extractedData.total_amount) {
          return res.status(400).json({
            success: false,
            message: '无法识别价格相关信息',
            rawText: rawText,
            partialData: extractedData
          });
        }
        
        // 计算和补充字段
        if (!extractedData.unit_price && extractedData.price) {
          extractedData.unit_price = extractedData.price;
        }
        
        if (!extractedData.fee) {
          extractedData.fee = 0;
        }
        
        if (!extractedData.total_amount && extractedData.quantity && extractedData.unit_price) {
          extractedData.total_amount = extractedData.quantity * extractedData.unit_price - extractedData.fee;
        }
        
        if (!extractedData.note) {
          extractedData.note = '';
        }
        
        logger.info('OCR识别成功');
        
        return res.json({
          success: true,
          message: 'OCR识别成功',
          data: extractedData,
          rawText: rawText
        });
      } catch (error) {
        logger.error('OCR处理错误:', error);
        
        // 删除临时文件
        if (req.file && req.file.path) {
          try {
            fs.unlinkSync(req.file.path);
          } catch (unlinkError) {
            logger.error(`删除临时文件失败: ${unlinkError.message}`);
          }
        }
        
        return res.status(500).json({
          success: false,
          message: '处理OCR请求时出错: ' + error.message
        });
      }
    } catch (error) {
      logger.error('OCR控制器错误:', error);
      return res.status(500).json({
        success: false,
        message: '服务器错误: ' + error.message
      });
    }
  },
  
  /**
   * 提取图片中的文本
   * POST /api/ocr/extract-text
   */
  extractText: async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ 
          success: false, 
          message: '未提供图片文件' 
        });
      }

      try {
        // 读取上传的文件
        const imagePath = req.file.path;
        
        // 执行OCR识别
        const rawText = await performOCR(imagePath);
        
        logger.info('OCR文本提取成功');
        
        return res.json({
          success: true,
          message: 'OCR文本提取成功',
          text: rawText
        });
      } catch (error) {
        logger.error('OCR处理错误:', error);
        return res.status(500).json({
          success: false,
          message: '处理OCR请求时出错: ' + error.message
        });
      }
    } catch (error) {
      logger.error('OCR控制器错误:', error);
      return res.status(500).json({
        success: false,
        message: '服务器错误: ' + error.message
      });
    }
  }
};

module.exports = ocrController; 