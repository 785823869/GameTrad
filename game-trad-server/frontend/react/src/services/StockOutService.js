import axios from 'axios';

const API_URL = '/api/stock-out';
// 控制是否输出详细日志
const DEBUG = false; 

/**
 * 出库管理相关API服务
 */
export default {
  /**
   * 获取所有出库记录
   * @returns {Promise} - 返回出库记录列表
   */
  getAll: async () => {
    try {
      if (DEBUG) console.log('正在请求出库数据...');
      const response = await axios.get(API_URL);
      if (DEBUG) console.log('出库API响应:', response);
      
      if (!response.data) {
        console.error('API响应中没有data字段');
        return [];
      }
      
      // 检查响应数据是否为数组
      if (!Array.isArray(response.data)) {
        console.error('API返回的数据不是数组格式:', response.data);
        return [];
      }
      
      // 确保每项数据都包含必要的字段
      const validatedData = response.data.map((item, index) => {
        // 检查是否是有效的对象
        if (!item || typeof item !== 'object') {
          console.error(`第${index}项数据无效:`, item);
          return null;
        }
        
        // 只在DEBUG模式下记录每个项目的字段信息
        if (DEBUG) console.log(`项目 ${index} 字段:`, Object.keys(item));
        
        return item;
      }).filter(item => item !== null);
      
      if (DEBUG) console.log('经验证的出库数据:', validatedData);
      return validatedData;
    } catch (error) {
      console.error('获取出库记录失败:', error);
      // 检查详细的错误信息
      if (error.response) {
        // 服务器响应了错误状态码
        console.error('错误状态码:', error.response.status);
        console.error('错误数据:', error.response.data);
      } else if (error.request) {
        // 请求已发送但未收到响应
        console.error('未收到响应:', error.request);
      } else {
        // 发送请求时出现错误
        console.error('请求错误:', error.message);
      }
      throw error;
    }
  },

  /**
   * 添加出库记录
   * @param {Object} stockOutData - 出库记录数据
   * @returns {Promise} - 返回添加结果
   */
  add: async (stockOutData) => {
    try {
      if (DEBUG) console.log('添加出库记录，数据:', stockOutData);
      const response = await axios.post(API_URL, stockOutData);
      if (DEBUG) console.log('添加出库记录响应:', response.data);
      return response.data;
    } catch (error) {
      console.error('添加出库记录失败:', error);
      if (error.response) {
        console.error('服务器响应:', error.response.data);
      }
      throw error;
    }
  },

  /**
   * 更新出库记录
   * @param {number} id - 记录ID
   * @param {Object} stockOutData - 更新的出库记录数据
   * @returns {Promise} - 返回更新结果
   */
  update: async (id, stockOutData) => {
    try {
      const response = await axios.put(`${API_URL}/${id}`, stockOutData);
      return response.data;
    } catch (error) {
      console.error('更新出库记录失败:', error);
      throw error;
    }
  },

  /**
   * 删除出库记录
   * @param {number} id - 记录ID
   * @returns {Promise} - 返回删除结果
   */
  delete: async (id) => {
    try {
      const response = await axios.delete(`${API_URL}/${id}`);
      return response.data;
    } catch (error) {
      console.error('删除出库记录失败:', error);
      throw error;
    }
  },

  /**
   * OCR识别导入
   * @param {Array} records - OCR识别结果记录
   * @returns {Promise} - 返回导入结果
   */
  importOcr: async (records) => {
    try {
      if (DEBUG) console.log('开始OCR导入，数据:', records);
      
      // 确保records是数组
      if (!Array.isArray(records)) {
        console.error('OCR导入失败: records不是数组');
        return { success: false, message: 'OCR数据格式不正确' };
      }
      
      // 数据预处理和验证
      const validRecords = records.filter(record => {
        // 验证记录的必要字段
        const isValid = record && 
                        record.item_name && 
                        (record.quantity !== undefined) && 
                        (record.unit_price !== undefined);
        
        if (!isValid && DEBUG) {
          console.warn('跳过无效OCR记录:', record);
        }
        
        return isValid;
      }).map(record => {
        // 确保数值字段为数字类型
        return {
          ...record,
          item_name: String(record.item_name).trim(),
          quantity: Number(record.quantity),
          unit_price: Number(record.unit_price),
          fee: Number(record.fee || 0),
          // 确保有交易时间，使用本地时间而非UTC时间
          transaction_time: record.transaction_time || 
                           (() => {
                             const now = new Date();
                             const year = now.getFullYear();
                             const month = String(now.getMonth() + 1).padStart(2, '0');
                             const day = String(now.getDate()).padStart(2, '0');
                             const hours = String(now.getHours()).padStart(2, '0');
                             const minutes = String(now.getMinutes()).padStart(2, '0');
                             const seconds = String(now.getSeconds()).padStart(2, '0');
                             return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
                           })(),
          note: record.note || '通过OCR导入'
        };
      });
      
      if (validRecords.length === 0) {
        console.warn('OCR导入失败: 没有有效记录');
        return { success: false, message: '没有有效的OCR数据' };
      }
      
      // 记录请求详情日志
      if (DEBUG) {
        console.log('发送OCR导入请求，有效记录数:', validRecords.length);
        console.log('请求数据示例:', validRecords[0]);
        console.log('请求端点:', `${API_URL}/import`);
      }
      
      // 发送请求
      const startTime = Date.now();
      const response = await axios.post(`${API_URL}/import`, validRecords);
      const endTime = Date.now();
      
      if (DEBUG) {
        console.log(`OCR导入响应耗时: ${endTime - startTime}ms`);
        console.log('OCR导入响应状态:', response.status);
        console.log('OCR导入响应数据:', response.data);
      }
      
      return response.data;
    } catch (error) {
      console.error('OCR导入出库记录失败:', error);
      
      // 详细记录错误信息
      if (error.response) {
        console.error('服务器响应状态码:', error.response.status);
        console.error('服务器响应数据:', error.response.data);
        
        // 返回服务器提供的错误信息
        return { 
          success: false, 
          message: error.response.data?.message || '服务器返回错误',
          error: error.response.data
        };
      } else if (error.request) {
        console.error('未收到服务器响应:', error.request);
        return { success: false, message: '服务器未响应请求' };
      } else {
        console.error('请求配置错误:', error.message);
        return { success: false, message: `请求错误: ${error.message}` };
      }
    }
  }
}; 