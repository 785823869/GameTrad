import axios from 'axios';

const API_URL = '/api/ocr-rules';

/**
 * OCR规则管理相关API服务
 */
export default {
  /**
   * 获取所有OCR规则
   * @param {string} type - 规则类型 (stock-in, stock-out, monitor)
   * @returns {Promise} - 返回规则列表
   */
  getAllRules: async (type) => {
    try {
      const response = await axios.get(`${API_URL}/${type}`);
      return response.data;
    } catch (error) {
      console.error(`获取${type}规则失败:`, error);
      throw error;
    }
  },

  /**
   * 获取单个规则
   * @param {string} type - 规则类型 (stock-in, stock-out, monitor)
   * @param {number} id - 规则ID
   * @returns {Promise} - 返回规则详情
   */
  getRule: async (type, id) => {
    try {
      const response = await axios.get(`${API_URL}/${type}/${id}`);
      return response.data;
    } catch (error) {
      console.error(`获取规则详情失败:`, error);
      throw error;
    }
  },

  /**
   * 添加新规则
   * @param {string} type - 规则类型 (stock-in, stock-out, monitor)
   * @param {Object} rule - 规则数据
   * @returns {Promise} - 返回添加结果
   */
  addRule: async (type, rule) => {
    try {
      const response = await axios.post(`${API_URL}/${type}`, rule);
      return response.data;
    } catch (error) {
      console.error(`添加规则失败:`, error);
      throw error;
    }
  },

  /**
   * 更新规则
   * @param {string} type - 规则类型 (stock-in, stock-out, monitor)
   * @param {number} id - 规则ID
   * @param {Object} rule - 规则数据
   * @returns {Promise} - 返回更新结果
   */
  updateRule: async (type, id, rule) => {
    try {
      const response = await axios.put(`${API_URL}/${type}/${id}`, rule);
      return response.data;
    } catch (error) {
      console.error(`更新规则失败:`, error);
      throw error;
    }
  },

  /**
   * 删除规则
   * @param {string} type - 规则类型 (stock-in, stock-out, monitor)
   * @param {number} id - 规则ID
   * @returns {Promise} - 返回删除结果
   */
  deleteRule: async (type, id) => {
    try {
      const response = await axios.delete(`${API_URL}/${type}/${id}`);
      return response.data;
    } catch (error) {
      console.error(`删除规则失败:`, error);
      throw error;
    }
  },

  /**
   * 测试OCR规则
   * @param {string} type - 规则类型 (stock-in, stock-out, monitor)
   * @param {Object} rule - 规则数据
   * @param {File} image - 测试图片
   * @returns {Promise} - 返回测试结果
   */
  testRule: async (type, rule, image) => {
    try {
      const formData = new FormData();
      formData.append('image', image);
      formData.append('rule', JSON.stringify(rule));
      
      const response = await axios.post(`${API_URL}/${type}/test`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response.data;
    } catch (error) {
      console.error(`测试规则失败:`, error);
      throw error;
    }
  }
}; 