import axios from 'axios';

const API_URL = '/api/stock-out';

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
      console.log('正在请求出库数据...');
      const response = await axios.get(API_URL);
      console.log('出库API响应:', response);
      
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
        
        // 记录每个项目的字段信息
        console.log(`项目 ${index} 字段:`, Object.keys(item));
        
        return item;
      }).filter(item => item !== null);
      
      console.log('经验证的出库数据:', validatedData);
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
      console.log('添加出库记录，数据:', stockOutData);
      const response = await axios.post(API_URL, stockOutData);
      console.log('添加出库记录响应:', response.data);
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
      const response = await axios.post(`${API_URL}/import`, { records });
      return response.data;
    } catch (error) {
      console.error('OCR导入出库记录失败:', error);
      throw error;
    }
  }
}; 