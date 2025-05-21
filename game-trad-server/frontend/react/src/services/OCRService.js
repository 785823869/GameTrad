import axios from 'axios';

// 简易日志对象，用于前端日志记录
const logger = {
  error: (message) => console.error(`OCRService ERROR: ${message}`),
  warn: (message) => console.warn(`OCRService WARN: ${message}`),
  info: (message) => console.info(`OCRService INFO: ${message}`)
};

/**
 * OCR服务类，提供OCR识别相关API调用
 */
class OCRService {
  /**
   * OCR图片识别
   * @param {File|Blob} image 要识别的图片文件
   * @returns {Promise} OCR识别结果
   */
  static async recognizeImage(image) {
    try {
      const formData = new FormData();
      formData.append('image', image);

      const response = await axios.post('/api/ocr/recognize', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data && response.data.success) {
        // 处理响应结果，确保前端字段名与StockOut.js组件兼容
        const ocrData = response.data.data || {};
        
        // 增加数据验证宽容度 - 尝试更灵活地提取和解析字段
        let itemName = ocrData.item_name || '';
        let quantity = 0;
        let unitPrice = 0;
        let fee = 0;
        let totalAmount = 0;
        
        // 尝试解析数量
        if (ocrData.quantity !== undefined) {
          quantity = parseInt(ocrData.quantity) || 0;
        } else if (typeof ocrData.count === 'string' || typeof ocrData.count === 'number') {
          quantity = parseInt(ocrData.count) || 0;
        }
        
        // 尝试解析单价
        if (ocrData.unit_price !== undefined) {
          unitPrice = parseFloat(ocrData.unit_price) || 0;
        } else if (ocrData.price !== undefined) {
          unitPrice = parseFloat(ocrData.price) || 0;
        }
        
        // 尝试解析手续费
        if (ocrData.fee !== undefined) {
          fee = parseFloat(ocrData.fee) || 0;
        }
        
        // 尝试解析总金额，或计算总金额
        if (ocrData.total_amount !== undefined) {
          totalAmount = parseFloat(ocrData.total_amount) || 0;
        } else if (ocrData.total !== undefined) {
          totalAmount = parseFloat(ocrData.total) || 0;
        } else if (quantity && unitPrice) {
          // 如果有数量和单价，可以计算总金额
          totalAmount = quantity * unitPrice - fee;
        }
        
        // 如果数据过于无效（没有物品名或数量为0），尝试从rawText中提取
        if (!itemName || quantity <= 0) {
          console.warn('OCR识别数据不完整，尝试从原始文本提取');
          // 这里可以添加更多的数据修复逻辑
        }
        
        // 标准化数据字段
        const result = {
          item_name: itemName,
          quantity: quantity,
          unit_price: unitPrice,
          fee: fee,
          total_amount: totalAmount,
          note: ocrData.note || ''
        };
        
        console.log('OCR识别结果:', result);
        
        // 只在确实有识别到有效物品名称和数量时才返回成功
        if (result.item_name && result.quantity > 0) {
          return {
            success: true,
            data: result,
            rawText: response.data.rawText || ''
          };
        } else {
          console.warn('OCR识别结果无效:', result);
          return {
            success: false,
            message: '未识别到有效的物品数据',
            rawText: response.data.rawText || ''
          };
        }
      }
      
      return response.data;
    } catch (error) {
      console.error('OCR识别请求失败:', error);
      throw error;
    }
  }

  /**
   * OCR批量图片识别
   * @param {Array<File|Blob>} images 要识别的图片文件数组
   * @returns {Promise} OCR识别结果数组
   */
  static async recognizeImages(images) {
    try {
      const results = [];
      
      // 串行处理每张图片，避免服务器过载
      for (const image of images) {
        const result = await this.recognizeImage(image);
        if (result.success && result.data) {
          results.push(result.data);
        }
      }
      
      return { 
        success: true, 
        data: results 
      };
    } catch (error) {
      console.error('OCR批量识别请求失败:', error);
      throw error;
    }
  }

  /**
   * 导入OCR结果到库存
   * @param {string} type 导入类型，'in'表示入库，'out'表示出库
   * @param {Array} data OCR识别结果数据
   * @param {string} requestId 可选的请求跟踪ID
   * @returns {Promise} 导入结果
   */
  static async importOCRResults(type, data, requestId = null) {
    try {
      // 启用调试模式
      const DEBUG = true;
      
      // 如果没有传入requestId，生成一个唯一ID
      if (!requestId) {
        requestId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
      }
      
      // 防止重复导入 - 使用RequestID检查
      if (window._lastOCRImportRequestId === requestId) {
        console.warn(`OCRService: 检测到重复请求，拒绝处理，请求ID: ${requestId}`);
        return { 
          success: false, 
          message: '检测到重复请求，已拒绝处理', 
          _duplicateRequest: true 
        };
      }
      
      // 存储当前请求ID
      window._lastOCRImportRequestId = requestId;
      
      if (DEBUG) {
        console.log(`OCRService: 开始导入数据，类型: ${type}, 请求ID: ${requestId}`);
        console.log(`OCRService: 数据类型: ${typeof data}`);
        console.log(`OCRService: 是否为数组: ${Array.isArray(data)}`);
        console.log(`OCRService: 数据长度: ${Array.isArray(data) ? data.length : 0}`);
        if (Array.isArray(data) && data.length > 0) {
          console.log(`OCRService: 首条数据: ${JSON.stringify(data[0])}`);
        }
      }
      
      // 验证数据
      if (!Array.isArray(data)) {
        console.error('OCRService: 导入失败 - 数据不是数组');
        return { success: false, message: '数据格式错误，应为数组' };
      }
      
      if (data.length === 0) {
        console.warn('OCRService: 导入失败 - 数据为空数组');
        return { success: false, message: '没有数据可导入' };
      }
      
      // 数据预处理 - 确保手续费一致处理
      const processedData = data.map(item => {
        // 确保所有必要字段都存在
        const processed = { ...item };
        
        // 保留请求ID（如果有）
        if (item._requestId) {
          processed._requestId = item._requestId;
        } else if (requestId) {
          processed._requestId = requestId;
        }
        
        // 确保item_name是字符串
        if (processed.item_name !== undefined) {
          processed.item_name = String(processed.item_name).trim();
        } else {
          console.warn('OCRService: 警告 - 记录缺少item_name字段');
          processed.item_name = '未知物品';
        }
        
        // 确保数值字段为数字类型
        if (processed.quantity !== undefined) {
          processed.quantity = Number(processed.quantity);
          if (isNaN(processed.quantity)) {
            console.warn(`OCRService: 警告 - quantity字段值无效: ${item.quantity}`);
            processed.quantity = 0;
          }
        }
        
        if (processed.unit_price !== undefined) {
          processed.unit_price = Number(processed.unit_price);
          if (isNaN(processed.unit_price)) {
            console.warn(`OCRService: 警告 - unit_price字段值无效: ${item.unit_price}`);
            processed.unit_price = 0;
          }
        } else if (processed.price !== undefined) {
          // 兼容使用price字段
          processed.unit_price = Number(processed.price);
          if (isNaN(processed.unit_price)) {
            console.warn(`OCRService: 警告 - price字段值无效: ${item.price}`);
            processed.unit_price = 0;
          }
        }
        
        // 确保手续费被正确处理 
        if (processed.fee !== undefined) {
          processed.fee = Number(processed.fee);
          if (isNaN(processed.fee)) {
            console.warn(`OCRService: 警告 - fee字段值无效: ${item.fee}, 设置为0`);
            processed.fee = 0;
          }
        } else {
          processed.fee = 0; // 默认手续费为0
          console.info(`OCRService: 记录没有手续费字段，设置为0`);
        }
        
        // 确保有交易时间
        if (!processed.transaction_time) {
          // 创建MySQL兼容格式的当前时间 (YYYY-MM-DD HH:MM:SS)，使用本地时间
          const now = new Date();
          const year = now.getFullYear();
          const month = String(now.getMonth() + 1).padStart(2, '0');
          const day = String(now.getDate()).padStart(2, '0');
          const hours = String(now.getHours()).padStart(2, '0');
          const minutes = String(now.getMinutes()).padStart(2, '0');
          const seconds = String(now.getSeconds()).padStart(2, '0');
          processed.transaction_time = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        } else if (processed.transaction_time.includes('T')) {
          // 如果已有ISO格式的时间，转换为MySQL格式
          processed.transaction_time = processed.transaction_time.replace('T', ' ').replace(/\.\d+Z$/, '');
        }
        
        // 添加备注
        if (!processed.note) {
          processed.note = '通过OCR导入';
        }
        
        // 根据导入类型添加额外字段
        if (type === 'in') {
          // 入库记录需要有单价和总价
          processed.avg_cost = processed.unit_price;
          processed.cost = processed.quantity * processed.unit_price;
        } else if (type === 'out') {
          // 出库记录需要有总金额 - 确保正确计算（数量 * 单价 - 手续费）
          processed.total_amount = (processed.quantity * processed.unit_price) - processed.fee;
          
          // 记录计算金额，便于调试
          console.info(`OCRService: 计算总金额: ${processed.quantity} * ${processed.unit_price} - ${processed.fee} = ${processed.total_amount}`);
        } else if (type === 'monitor') {
          // 监控记录调整
          processed.market_price = processed.unit_price;
          if (!processed.target_price) processed.target_price = 0;
          if (!processed.planned_price) processed.planned_price = 0;
          if (!processed.strategy) processed.strategy = '';
        }
        
        if (DEBUG) {
          console.log(`OCRService: 数据预处理结果:`, processed);
        }
        
        return processed;
      }).filter(item => {
        // 过滤掉无效的数据
        const isValid = item.item_name && 
                      item.quantity !== undefined && 
                      item.unit_price !== undefined;
                       
        if (!isValid) {
          console.warn(`OCRService: 过滤掉无效数据: ${JSON.stringify(item)}`);
        }
        
        return isValid;
      });
      
      if (processedData.length === 0) {
        console.warn('OCRService: 所有数据都无效');
        return { success: false, message: '所有数据格式无效，无法导入' };
      }
      
      // 确定API端点
      let endpoint = '';
      if (type === 'in') {
        endpoint = '/api/stock-in/import';
      } else if (type === 'out') {
        endpoint = '/api/stock-out/import';
      } else if (type === 'monitor') {
        endpoint = '/api/monitor/import';
      } else {
        console.error(`OCRService: 导入失败 - 未知的导入类型: ${type}`);
        return { success: false, message: `未知的导入类型: ${type}` };
      }
      
      console.log(`OCRService: 使用端点: ${endpoint}, 请求ID: ${requestId}`);
      console.log(`OCRService: 即将发送数据: ${JSON.stringify(processedData).substring(0, 150)}...`);
      
      // 添加请求计时
      const startTime = Date.now();
      
      // 发送请求，添加请求ID到header中以便追踪
      const response = await axios.post(endpoint, processedData, {
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId
        },
        timeout: 15000 // 增加超时时间为15秒
      });
      
      const endTime = Date.now();
      console.log(`OCRService: 请求耗时 ${endTime - startTime}ms, 请求ID: ${requestId}`);
      
      if (DEBUG) {
        console.log(`OCRService: 收到响应状态: ${response.status}, 请求ID: ${requestId}`);
        console.log(`OCRService: 响应数据: ${JSON.stringify(response.data)}`);
      }
      
      // 检查响应中的错误信息
      if (response.data && response.data.results && response.data.results.errors && response.data.results.errors.length > 0) {
        console.warn(`OCRService: API返回了错误信息 (请求ID: ${requestId}):`, response.data.results.errors);
      }
      
      // 添加请求ID到响应中，便于前端追踪
      if (response.data) {
        response.data._requestId = requestId;
      }
      
      return response.data;
    } catch (error) {
      console.error(`OCRService: 导入OCR结果失败 (请求ID: ${requestId}):`, error);
      
      // 记录更详细的错误信息
      if (error.response) {
        console.error('OCRService: 服务器响应错误:');
        console.error(`状态码: ${error.response.status}`);
        console.error(`响应数据: ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        console.error('OCRService: 请求已发送但未收到响应');
        console.error(`请求详情: ${JSON.stringify(error.request)}`);
      } else {
        console.error(`OCRService: 请求配置错误: ${error.message}`);
      }
      
      // 重新抛出错误以便上层处理
      throw error;
    }
  }
  
  /**
   * 从图片中提取文本
   * @param {File|Blob} image 要识别的图片文件
   * @returns {Promise} 提取的文本
   */
  static async extractText(image) {
    try {
      const formData = new FormData();
      formData.append('image', image);
      
      const response = await axios.post('/api/ocr/extract-text', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response.data;
    } catch (error) {
      console.error('文本提取请求失败:', error);
      throw error;
    }
  }
}

export default OCRService; 