/**
 * analyticsController.js - 交易分析数据API控制器
 */

const analyticsHelper = require('../utils/analyticsHelper');
const logger = require('../utils/logger');

/**
 * 获取交易分析数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getTradeAnalytics = async (req, res) => {
  try {
    // 提取查询参数
    const period = req.query.period || 'day'; // 'day', 'week', 'month'
    const days = parseInt(req.query.days) || 30;
    const taxRate = parseFloat(req.query.tax_rate) || 0.05;
    const topN = parseInt(req.query.top_n) || 10;
    
    // 获取分析数据
    const volumeData = await analyticsHelper.getVolumeByPeriod(period);
    const profitRanking = await analyticsHelper.getProfitRanking(topN);
    const slowMovingItems = await analyticsHelper.getSlowMovingItems(days);
    const taxSummary = await analyticsHelper.getTradeTaxSummary(taxRate);
    
    // 返回分析结果
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      data: {
        volume_data: volumeData,
        profit_ranking: profitRanking,
        slow_moving_items: slowMovingItems,
        tax_summary: taxSummary
      }
    });
  } catch (error) {
    logger.error(`获取交易分析数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取交易分析数据失败',
      error: error.message
    });
  }
};

/**
 * 获取成交量数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getVolumeData = async (req, res) => {
  try {
    const period = req.query.period || 'day'; // 'day', 'week', 'month'
    const limit = parseInt(req.query.limit) || 30;
    
    const volumeData = await analyticsHelper.getVolumeByPeriod(period, limit);
    
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      data: volumeData
    });
  } catch (error) {
    logger.error(`获取成交量数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取成交量数据失败',
      error: error.message
    });
  }
};

/**
 * 获取利润率排行数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getProfitRanking = async (req, res) => {
  try {
    const topN = parseInt(req.query.top_n) || 10;
    
    const profitRanking = await analyticsHelper.getProfitRanking(topN);
    
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      data: profitRanking
    });
  } catch (error) {
    logger.error(`获取利润率排行数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取利润率排行数据失败',
      error: error.message
    });
  }
};

/**
 * 获取滞销品数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getSlowMovingItems = async (req, res) => {
  try {
    const days = parseInt(req.query.days) || 30;
    
    const slowMovingItems = await analyticsHelper.getSlowMovingItems(days);
    
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      data: slowMovingItems
    });
  } catch (error) {
    logger.error(`获取滞销品数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取滞销品数据失败',
      error: error.message
    });
  }
};

/**
 * 获取交易税统计数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getTradeTaxSummary = async (req, res) => {
  try {
    const taxRate = parseFloat(req.query.tax_rate) || 0.05;
    
    const taxSummary = await analyticsHelper.getTradeTaxSummary(taxRate);
    
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      data: taxSummary
    });
  } catch (error) {
    logger.error(`获取交易税统计数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取交易税统计数据失败',
      error: error.message
    });
  }
}; 