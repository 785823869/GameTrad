/**
 * analyticsHelper.js - 交易分析工具函数
 * 参考Python的trade_analyzer.py实现
 */

const db = require('./db');
const logger = require('./logger');

/**
 * 按指定周期统计成交量
 * @param {string} period - 统计周期: 'day'=日, 'week'=周, 'month'=月
 * @param {number} limit - 返回记录数量限制
 * @returns {Promise<Array>} 成交量统计数据
 */
const getVolumeByPeriod = async (period = 'day', limit = 30) => {
  try {
    let groupFormat;
    switch(period) {
      case 'week':
        groupFormat = '%Y-%u'; // 年-周
        break;
      case 'month':
        groupFormat = '%Y-%m'; // 年-月
        break;
      default:
        groupFormat = '%Y-%m-%d'; // 年-月-日
    }

    const query = `
      SELECT 
        DATE_FORMAT(transaction_time, '${groupFormat}') as period,
        item_name,
        SUM(quantity) as total_quantity
      FROM stock_out
      WHERE transaction_time >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
      GROUP BY period, item_name
      ORDER BY period DESC, total_quantity DESC
      LIMIT ?
    `;
    
    const results = await db.fetchAll(query, [limit]);
    
    // 转换为易于前端使用的格式
    const formattedResults = [];
    results.forEach(row => {
      formattedResults.push({
        date: row.period,
        item: row.item_name,
        quantity: parseInt(row.total_quantity)
      });
    });
    
    return formattedResults;
  } catch (error) {
    logger.error(`获取成交量统计失败: ${error.message}`);
    return [];
  }
};

/**
 * 计算利润率排行榜
 * @param {number} topN - 返回排名前N项
 * @returns {Promise<Array>} 利润率排行数据
 */
const getProfitRanking = async (topN = 10) => {
  try {
    // 直接从库存表获取所有物品信息（包括利润率）
    // 使用与库存表完全一致的数据，避免计算差异
    const inventoryQuery = `SELECT item_name, quantity, avg_price, break_even_price, 
                           selling_price, profit, profit_rate, total_profit, inventory_value 
                           FROM inventory`;
    const inventoryItems = await db.fetchAll(inventoryQuery);
    
    // 创建物品到库存信息的映射
    const inventoryMap = {};
    inventoryItems.forEach(item => {
      inventoryMap[item.item_name] = {
        quantity: parseInt(item.quantity) || 0,
        avg_price: parseFloat(item.avg_price) || 0,
        profit: parseFloat(item.profit) || 0,
        profit_rate: parseFloat(item.profit_rate) || 0
      };
    });
    
    // 获取出库数据（仅用于计算销售总额和数量）
    const outQuery = `
      SELECT 
        item_name,
        SUM(quantity) as total_quantity,
        SUM(total_amount) as total_sales
      FROM stock_out
      WHERE transaction_time >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
      GROUP BY item_name
    `;
    const outItems = await db.fetchAll(outQuery);
    
    // 整合数据并优先使用库存表中的利润率
    const profitRanking = outItems.map(item => {
      const itemName = item.item_name;
      const totalQuantity = parseInt(item.total_quantity) || 0;
      const totalSales = parseFloat(item.total_sales) || 0;
      
      // 获取库存表中的数据
      const inventoryData = inventoryMap[itemName] || {
        quantity: 0,
        avg_price: 0,
        profit: 0,
        profit_rate: 0
      };
      
      // 确保使用库存表的利润率
      const profitRate = inventoryData.profit_rate;
      
      // 计算销售的利润（使用库存数据中的利润计算）
      const profit = totalQuantity * inventoryData.profit || 0;
      
      return {
        item: itemName,
        avg_cost: Number(inventoryData.avg_price.toFixed(2)),
        total_quantity: totalQuantity,
        total_sales: Number(totalSales.toFixed(2)),
        profit: Number(profit.toFixed(2)),
        profit_rate: Number(profitRate)
      };
    });
    
    // 过滤无效数据并按利润率排序
    const validProfitRanking = profitRanking
      .filter(item => {
        // 过滤掉无效或异常数据
        if (!item.item) return false;
        if (isNaN(item.profit_rate)) return false;
        return true;
      })
      .sort((a, b) => b.profit_rate - a.profit_rate);
      
    // 返回前N项或所有项
    return validProfitRanking.slice(0, Math.min(validProfitRanking.length, topN || 10));
  } catch (error) {
    logger.error(`计算利润率排行榜失败: ${error.message}`);
    return [];
  }
};

/**
 * 获取滞销品列表
 * @param {number} days - 指定多少天没交易算滞销品
 * @returns {Promise<Array>} 滞销品列表
 */
const getSlowMovingItems = async (days = 30) => {
  try {
    // 查询库存中的物品
    const inventoryQuery = `SELECT item_name, quantity FROM inventory WHERE quantity > 0`;
    const inventoryItems = await db.fetchAll(inventoryQuery);
    
    // 查询最近有过交易的物品
    const recentSalesQuery = `
      SELECT DISTINCT item_name
      FROM stock_out
      WHERE transaction_time >= DATE_SUB(NOW(), INTERVAL ? DAY)
    `;
    const recentSalesItems = await db.fetchAll(recentSalesQuery, [days]);
    
    // 创建最近交易物品集合
    const recentSalesSet = new Set();
    recentSalesItems.forEach(item => {
      recentSalesSet.add(item.item_name);
    });
    
    // 找出存在于库存但最近没有交易的物品
    const slowMovingItems = inventoryItems.filter(item => {
      return !recentSalesSet.has(item.item_name);
    }).map(item => ({
      item: item.item_name,
      quantity: parseInt(item.quantity),
      days_inactive: days
    }));
    
    return slowMovingItems;
  } catch (error) {
    logger.error(`获取滞销品列表失败: ${error.message}`);
    return [];
  }
};

/**
 * 计算交易税统计
 * @param {number} taxRate - 交易税率(小数)
 * @returns {Promise<Array>} 交易税统计数据
 */
const getTradeTaxSummary = async (taxRate = 0.05) => {
  try {
    const query = `
      SELECT 
        item_name,
        SUM(quantity) as total_quantity,
        AVG(unit_price) as avg_price,
        SUM(total_amount) as total_sales
      FROM stock_out
      WHERE transaction_time >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
      GROUP BY item_name
      ORDER BY total_sales DESC
    `;
    
    const results = await db.fetchAll(query);
    
    // 计算每个物品的交易税
    return results.map(item => {
      const taxAmount = parseFloat(item.total_sales) * taxRate;
      
      return {
        item: item.item_name,
        quantity: parseInt(item.total_quantity) || 0,
        price: parseFloat(item.avg_price) || 0,
        tax_amount: taxAmount
      };
    });
  } catch (error) {
    logger.error(`计算交易税统计失败: ${error.message}`);
    return [];
  }
};

/**
 * 获取综合交易分析数据
 * @returns {Promise<Object>} 交易分析数据
 */
const getTradeAnalytics = async () => {
  try {
    const volumeData = await getVolumeByPeriod('day');
    const profitRanking = await getProfitRanking();
    const slowMovingItems = await getSlowMovingItems();
    const taxSummary = await getTradeTaxSummary();

    return {
      volume_data: volumeData,
      profit_ranking: profitRanking,
      slow_moving_items: slowMovingItems,
      tax_summary: taxSummary
    };
  } catch (error) {
    logger.error(`获取交易分析数据失败: ${error.message}`);
    return {
      volume_data: [],
      profit_ranking: [],
      slow_moving_items: [],
      tax_summary: []
    };
  }
};

module.exports = {
  getVolumeByPeriod,
  getProfitRanking,
  getSlowMovingItems,
  getTradeTaxSummary,
  getTradeAnalytics
}; 