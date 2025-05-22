const mysql = require('mysql2/promise');
const logger = require('./logger');
const db = require('./db');
const fs = require('fs');
const path = require('path');

// 根据Python的db_manager.py创建相似配置
const DB_CONFIG = {
  host: 'sql.didiba.uk',
  port: 33306,
  user: 'root',
  password: 'Cenb1017!@',
  database: 'OcrTrade',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
};

// 创建连接池
const pool = mysql.createPool(DB_CONFIG);

// 历史价格点本地文件路径
const SILVER_7881_HISTORY_PATH = path.join(__dirname, '../temp/silver_7881_history.json');

// 测试数据库连接
const testConnection = async () => {
  try {
    const connection = await pool.getConnection();
    await connection.query('SELECT 1');
    connection.release();
    logger.info('数据库连接成功');
    return true;
  } catch (error) {
    logger.error(`数据库连接失败: ${error.message}`);
    return false;
  }
};

// 执行查询
const query = async (sql, params = []) => {
  try {
    const [results] = await pool.execute(sql, params);
    return results;
  } catch (error) {
    logger.error(`查询执行失败: ${error.message}`);
    throw error;
  }
};

// 获取总交易利润
const getTotalTradingProfit = async () => {
  try {
    // 获取总收入(使用total_amount代替profit)
    const totalProfitQuery = `
      SELECT SUM(total_amount) as totalProfit 
      FROM stock_out 
      WHERE transaction_time >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
    `;
    const totalProfitResult = await db.fetchOne(totalProfitQuery);
    const totalProfit = totalProfitResult?.totalProfit || 0;
    
    // 获取本月收入(使用total_amount代替profit)
    const currentMonthQuery = `
      SELECT SUM(total_amount) as monthProfit 
      FROM stock_out 
      WHERE transaction_time >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
    `;
    const currentMonthResult = await db.fetchOne(currentMonthQuery);
    const currentMonthProfit = currentMonthResult?.monthProfit || 0;
    
    // 获取上月收入(使用total_amount代替profit)
    const lastMonthQuery = `
      SELECT SUM(total_amount) as monthProfit 
      FROM stock_out 
      WHERE transaction_time >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01')
      AND transaction_time < DATE_FORMAT(CURDATE(), '%Y-%m-01')
    `;
    const lastMonthResult = await db.fetchOne(lastMonthQuery);
    const lastMonthProfit = lastMonthResult?.monthProfit || 0;
    
    // 计算月环比变化
    let monthOnMonthChange = 0;
    if (lastMonthProfit > 0) {
      monthOnMonthChange = ((currentMonthProfit - lastMonthProfit) / lastMonthProfit) * 100;
    }
    
    return {
      totalProfit,
      monthOnMonthChange: parseFloat(monthOnMonthChange.toFixed(2))
    };
  } catch (error) {
    logger.error(`获取总交易利润失败: ${error.message}`);
    return { totalProfit: 0, monthOnMonthChange: 0 };
  }
};

// 获取总库存价值
const getTotalInventoryValue = async () => {
  try {
    // 获取当前库存总价值
    const totalValueQuery = `
      SELECT SUM(inventory_value) as totalValue 
      FROM inventory 
      WHERE quantity > 0
    `;
    const totalValueResult = await db.fetchOne(totalValueQuery);
    const totalValue = totalValueResult?.totalValue || 0;
    
    // 模拟月环比变化（实际项目中应从历史数据计算）
    const monthOnMonthChange = Math.random() * 20 - 10; // -10% 到 +10% 的随机值
    
    return {
      totalValue,
      monthOnMonthChange: parseFloat(monthOnMonthChange.toFixed(2))
    };
  } catch (error) {
    logger.error(`获取总库存价值失败: ${error.message}`);
    return { totalValue: 0, monthOnMonthChange: 0 };
  }
};

// 获取库存详情数据
const getInventoryDetails = async (limit = 5) => {
  try {
    const query = `
      SELECT 
        item_name as item, 
        CONCAT(quantity) as quantity, 
        CONCAT(avg_price) as price, 
        CONCAT(inventory_value) as value,
        '0' as rate,
        '0%' as rateValue
      FROM inventory
      WHERE quantity > 0
      ORDER BY inventory_value DESC
      LIMIT ?
    `;
    
    const results = await db.fetchAll(query, [limit]);
    return results;
  } catch (error) {
    logger.error(`获取库存详情失败: ${error.message}`);
    return [];
  }
};

// 获取物品价格趋势
const getItemPriceTrend = async (itemName, period = 'day') => {
  try {
    if (!itemName) {
      return [];
    }
    
    // 获取入库数据
    const stockInQuery = 'SELECT transaction_time, avg_cost FROM stock_in WHERE item_name = ? ORDER BY transaction_time';
    const stockInResults = await query(stockInQuery, [itemName]);
    
    // 获取出库数据
    const stockOutQuery = 'SELECT transaction_time, unit_price FROM stock_out WHERE item_name = ? ORDER BY transaction_time';
    const stockOutResults = await query(stockOutQuery, [itemName]);
    
    // 处理入库数据
    const inPrices = stockInResults.map(row => ({
      date: new Date(row.transaction_time),
      price: parseFloat(row.avg_cost)
    }));
    
    // 处理出库数据
    const outPrices = stockOutResults.map(row => ({
      date: new Date(row.transaction_time),
      price: parseFloat(row.unit_price)
    }));
    
    // 合并并排序数据
    const allPrices = [...inPrices, ...outPrices].sort((a, b) => a.date - b.date);
    
    // 如果没有数据，返回空数组
    if (allPrices.length === 0) {
      return [];
    }
    
    // 根据周期格式化日期
    allPrices.forEach(item => {
      if (period === 'day') {
        item.dateLabel = item.date.toISOString().split('T')[0];
      } else if (period === 'week') {
        const date = new Date(item.date);
        date.setDate(date.getDate() - date.getDay());
        item.dateLabel = `W${Math.ceil(date.getDate() / 7)}`;
      } else if (period === 'month') {
        item.dateLabel = `${item.date.getFullYear()}-${(item.date.getMonth() + 1).toString().padStart(2, '0')}`;
      }
    });
    
    return allPrices;
  } catch (error) {
    logger.error(`获取物品价格趋势失败: ${error.message}`);
    return [];
  }
};

// 获取交易监控数据
const getTradeMonitorData = async () => {
  try {
    const query = `
      SELECT 
        id,
        item_name,
        monitor_time,
        quantity,
        market_price,
        target_price,
        planned_price,
        break_even_price,
        profit,
        profit_rate,
        strategy
      FROM trade_monitor
      ORDER BY monitor_time DESC
    `;
    
    const results = await db.fetchAll(query);
    return results.map(item => ({
      id: item.id,
      item_name: item.item_name,
      monitor_time: item.monitor_time,
      quantity: parseInt(item.quantity) || 0,
      market_price: parseFloat(item.market_price) || 0,
      target_price: parseFloat(item.target_price) || 0,
      planned_price: parseFloat(item.planned_price) || 0,
      break_even_price: parseFloat(item.break_even_price) || 0,
      profit: parseFloat(item.profit) || 0,
      profit_rate: parseFloat(item.profit_rate) || 0,
      strategy: item.strategy || ''
    }));
  } catch (error) {
    logger.error(`获取交易监控数据失败: ${error.message}`);
    return [];
  }
};

// 保存交易监控数据
const saveTradeMonitorData = async (data) => {
  try {
    // 验证必要字段
    if (!data.item_name) {
      throw new Error('物品名称不能为空');
    }
    
    // 设置默认值
    const monitorTime = data.monitor_time || new Date();
    const quantity = parseInt(data.quantity) || 0;
    const marketPrice = parseFloat(data.market_price) || 0;
    const targetPrice = parseFloat(data.target_price) || 0;
    const plannedPrice = parseFloat(data.planned_price) || 0;
    
    // 计算派生字段
    const breakEvenPrice = targetPrice > 0 ? targetPrice * 1.03 : 0;
    const profit = (plannedPrice - targetPrice) * quantity;
    const profitRate = targetPrice > 0 ? ((plannedPrice - targetPrice) / targetPrice) * 100 : 0;
    
    // 检查是否存在该物品的记录
    const existingItemQuery = `
      SELECT id FROM trade_monitor WHERE item_name = ?
    `;
    const existingItem = await db.fetchOne(existingItemQuery, [data.item_name]);
    
    let result;
    
    if (existingItem) {
      // 更新现有记录
      const updateQuery = `
        UPDATE trade_monitor SET
          monitor_time = ?,
          quantity = ?,
          market_price = ?,
          target_price = ?,
          planned_price = ?,
          break_even_price = ?,
          profit = ?,
          profit_rate = ?,
          strategy = ?
        WHERE id = ?
      `;
      
      await db.execute(updateQuery, [
        monitorTime,
        quantity,
        marketPrice,
        targetPrice,
        plannedPrice,
        breakEvenPrice,
        profit,
        profitRate,
        data.strategy || '',
        existingItem.id
      ]);
      
      result = { id: existingItem.id, updated: true };
    } else {
      // 插入新记录
      const insertQuery = `
        INSERT INTO trade_monitor (
          item_name,
          monitor_time,
          quantity,
          market_price,
          target_price,
          planned_price,
          break_even_price,
          profit,
          profit_rate,
          strategy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;
      
      const insertResult = await db.execute(insertQuery, [
        data.item_name,
        monitorTime,
        quantity,
        marketPrice,
        targetPrice,
        plannedPrice,
        breakEvenPrice,
        profit,
        profitRate,
        data.strategy || ''
      ]);
      
      result = { id: insertResult.insertId, updated: false };
    }
    
    return result;
  } catch (error) {
    logger.error(`保存交易监控数据失败: ${error.message}`);
    throw error;
  }
};

// 删除交易监控数据
const deleteTradeMonitorData = async (id) => {
  try {
    const query = 'DELETE FROM trade_monitor WHERE id = ?';
    await db.execute(query, [id]);
    return true;
  } catch (error) {
    logger.error(`删除交易监控数据失败: ${error.message}`);
    throw error;
  }
};

// 获取每周收入
const getWeeklyIncome = async () => {
  try {
    const query = `
      SELECT 
        DATE_FORMAT(transaction_time, '%Y-%m-%d') as date,
        SUM(total_amount) as daily_profit
      FROM stock_out
      WHERE transaction_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
      GROUP BY DATE_FORMAT(transaction_time, '%Y-%m-%d')
      ORDER BY date ASC
    `;
    
    const results = await db.fetchAll(query);
    
    // 将结果转换为[日期, 收入]格式的数组
    return results.map(row => [row.date, parseFloat(row.daily_profit || 0)]);
  } catch (error) {
    logger.error(`获取周收入数据失败: ${error.message}`);
    // 返回过去7天的模拟数据
    const weeklyData = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const formattedDate = date.toISOString().split('T')[0];
      weeklyData.push([formattedDate, Math.floor(Math.random() * 1000) + 500]);
    }
    
    return weeklyData;
  }
};

// 获取所有物品
const getAllItems = async () => {
  try {
    const query = `SELECT DISTINCT item_name FROM inventory ORDER BY item_name ASC`;
    const results = await db.fetchAll(query);
    return results.map(row => row.item_name);
  } catch (error) {
    logger.error(`获取物品列表失败: ${error.message}`);
    return [];
  }
};

// 获取行情数据
const getMarketData = async () => {
  try {
    // 这里可以从数据库或外部API获取市场数据
    // 目前使用模拟数据
    return {
      marketStatus: '活跃',
      silverPrice: '¥ 6.75/克',
      nvwaPrice: '¥ 3.25/个'
    };
  } catch (error) {
    logger.error(`获取市场数据失败: ${error.message}`);
    return {
      marketStatus: '未知',
      silverPrice: '未知',
      nvwaPrice: '未知'
    };
  }
};

// 获取总库存统计
const getInventoryStats = async () => {
  try {
    return await db.getInventoryStats();
  } catch (error) {
    logger.error(`获取库存统计失败: ${error.message}`);
    return {
      itemCount: 0,
      totalQuantity: 0,
      totalValue: 0,
      lowStockCount: 0
    };
  }
};

// 追加一条价格记录 { timestamp, price }
const appendSilver7881PriceHistory = async (price) => {
  try {
    const now = Date.now();
    let history = [];
    if (fs.existsSync(SILVER_7881_HISTORY_PATH)) {
      const raw = fs.readFileSync(SILVER_7881_HISTORY_PATH, 'utf-8');
      history = JSON.parse(raw);
    }
    history.push({ timestamp: now, price });
    fs.writeFileSync(SILVER_7881_HISTORY_PATH, JSON.stringify(history, null, 2), 'utf-8');
    return true;
  } catch (e) {
    logger.error('写入银两历史价格失败: ' + e.message);
    return false;
  }
};

// 查询指定时间范围内的历史价格点
const getSilver7881PriceHistory = async (fromTimestamp, toTimestamp) => {
  try {
    if (!fs.existsSync(SILVER_7881_HISTORY_PATH)) return [];
    const raw = fs.readFileSync(SILVER_7881_HISTORY_PATH, 'utf-8');
    const history = JSON.parse(raw);
    return history.filter(item => item.timestamp >= fromTimestamp && item.timestamp <= toTimestamp);
  } catch (e) {
    logger.error('读取银两历史价格失败: ' + e.message);
    return [];
  }
};

// 初始化模块
testConnection();

module.exports = {
  query,
  getTotalTradingProfit,
  getTotalInventoryValue,
  getInventoryDetails,
  getItemPriceTrend,
  getTradeMonitorData,
  saveTradeMonitorData,
  deleteTradeMonitorData,
  getWeeklyIncome,
  getAllItems,
  getMarketData,
  getInventoryStats,
  appendSilver7881PriceHistory,
  getSilver7881PriceHistory
}; 