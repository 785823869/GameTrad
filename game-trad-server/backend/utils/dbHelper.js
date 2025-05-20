const mysql = require('mysql2/promise');
const logger = require('./logger');

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
    // 获取入库数据
    const stockInQuery = 'SELECT item_name, quantity, cost FROM stock_in';
    const stockInResults = await query(stockInQuery);
    
    // 获取出库数据
    const stockOutQuery = 'SELECT item_name, quantity, unit_price, fee FROM stock_out';
    const stockOutResults = await query(stockOutQuery);
    
    // 计算每种物品的库存和价值
    const inventoryDict = {};
    
    // 统计入库
    for (const row of stockInResults) {
      const { item_name, quantity, cost } = row;
      const qty = parseFloat(quantity);
      const costValue = parseFloat(cost);
      
      if (!inventoryDict[item_name]) {
        inventoryDict[item_name] = {
          in_qty: 0, in_amount: 0, out_qty: 0, out_amount: 0
        };
      }
      
      inventoryDict[item_name].in_qty += qty;
      inventoryDict[item_name].in_amount += costValue;
    }
    
    // 统计出库
    for (const row of stockOutResults) {
      const { item_name, quantity, unit_price, fee } = row;
      const qty = parseFloat(quantity);
      const price = parseFloat(unit_price);
      const feeValue = parseFloat(fee || 0);
      const amount = price * qty - feeValue;
      
      if (!inventoryDict[item_name]) {
        inventoryDict[item_name] = {
          in_qty: 0, in_amount: 0, out_qty: 0, out_amount: 0
        };
      }
      
      inventoryDict[item_name].out_qty += qty;
      inventoryDict[item_name].out_amount += amount;
    }
    
    // 计算总成交利润额
    let totalProfit = 0.0;
    for (const item in inventoryDict) {
      const data = inventoryDict[item];
      
      // 只计算有出库记录的物品
      if (data.out_qty <= 0) continue;
      
      // 计算入库均价
      const inAvg = data.in_qty > 0 ? data.in_amount / data.in_qty : 0;
      
      // 计算出库均价
      const outAvg = data.out_qty > 0 ? data.out_amount / data.out_qty : 0;
      
      // 计算成交利润额
      const profit = data.out_qty > 0 ? (outAvg - inAvg) * data.out_qty : 0;
      totalProfit += profit;
    }
    
    // 计算月环比数据
    // 在现实应用中，应该存储历史数据并计算真实的月环比
    // 这里返回一个固定值作为示例
    const monthOnMonthChange = 15.0;
    
    return { totalProfit, monthOnMonthChange };
  } catch (error) {
    logger.error(`获取总交易利润失败: ${error.message}`);
    return { totalProfit: 0, monthOnMonthChange: 0 };
  }
};

// 获取总库存价值
const getTotalInventoryValue = async () => {
  try {
    // 获取入库数据
    const stockInQuery = 'SELECT item_name, quantity, cost FROM stock_in';
    const stockInResults = await query(stockInQuery);
    
    // 获取出库数据
    const stockOutQuery = 'SELECT item_name, quantity FROM stock_out';
    const stockOutResults = await query(stockOutQuery);
    
    // 计算每种物品的库存和价值
    const inventoryDict = {};
    
    // 统计入库
    for (const row of stockInResults) {
      const { item_name, quantity, cost } = row;
      const qty = parseFloat(quantity);
      const costValue = parseFloat(cost);
      
      if (!inventoryDict[item_name]) {
        inventoryDict[item_name] = {
          in_qty: 0, in_amount: 0, out_qty: 0
        };
      }
      
      inventoryDict[item_name].in_qty += qty;
      inventoryDict[item_name].in_amount += costValue;
    }
    
    // 统计出库
    for (const row of stockOutResults) {
      const { item_name, quantity } = row;
      const qty = parseFloat(quantity);
      
      if (!inventoryDict[item_name]) {
        inventoryDict[item_name] = {
          in_qty: 0, in_amount: 0, out_qty: 0
        };
      }
      
      inventoryDict[item_name].out_qty += qty;
    }
    
    // 计算总库存价值
    let totalValue = 0.0;
    for (const item in inventoryDict) {
      const data = inventoryDict[item];
      const remainQty = data.in_qty - data.out_qty;
      
      if (remainQty <= 0) continue;
      
      const inAvg = data.in_qty > 0 ? data.in_amount / data.in_qty : 0;
      const value = remainQty * inAvg;
      totalValue += value;
    }
    
    // 计算月环比数据（示例固定值）
    const monthOnMonthChange = 33.0;
    
    return { totalValue, monthOnMonthChange };
  } catch (error) {
    logger.error(`获取总库存价值失败: ${error.message}`);
    return { totalValue: 0, monthOnMonthChange: 0 };
  }
};

// 获取库存详情数据
const getInventoryDetails = async (limit = 7) => {
  try {
    // 获取入库数据
    const stockInQuery = 'SELECT item_name, quantity, cost FROM stock_in';
    const stockInResults = await query(stockInQuery);
    
    // 获取出库数据
    const stockOutQuery = 'SELECT item_name, quantity, unit_price, fee FROM stock_out';
    const stockOutResults = await query(stockOutQuery);
    
    // 计算每种物品的库存和价值
    const inventoryDict = {};
    
    // 统计入库
    for (const row of stockInResults) {
      const { item_name, quantity, cost } = row;
      const qty = parseFloat(quantity);
      const costValue = parseFloat(cost);
      
      if (!inventoryDict[item_name]) {
        inventoryDict[item_name] = {
          in_qty: 0, in_amount: 0, out_qty: 0, out_amount: 0
        };
      }
      
      inventoryDict[item_name].in_qty += qty;
      inventoryDict[item_name].in_amount += costValue;
    }
    
    // 统计出库
    for (const row of stockOutResults) {
      const { item_name, quantity, unit_price, fee } = row;
      const qty = parseFloat(quantity);
      const price = parseFloat(unit_price);
      const feeValue = parseFloat(fee || 0);
      const amount = price * qty - feeValue;
      
      if (!inventoryDict[item_name]) {
        inventoryDict[item_name] = {
          in_qty: 0, in_amount: 0, out_qty: 0, out_amount: 0
        };
      }
      
      inventoryDict[item_name].out_qty += qty;
      inventoryDict[item_name].out_amount += amount;
    }
    
    // 计算库存数量和利润率
    const result = [];
    for (const item in inventoryDict) {
      const data = inventoryDict[item];
      const remainQty = data.in_qty - data.out_qty;
      
      // 计算平均入库成本和平均出库价格
      const inAvg = data.in_qty > 0 ? data.in_amount / data.in_qty : 0;
      const outAvg = data.out_qty > 0 ? data.out_amount / data.out_qty : 0;
      
      // 计算利润率
      let profitRate = 0;
      if (inAvg > 0 && outAvg > 0) {
        profitRate = (outAvg - inAvg) / inAvg * 100;
      }
      
      // 格式化数据
      const formattedQty = Math.abs(remainQty) < 1000 
        ? Math.round(remainQty).toString() 
        : Math.round(remainQty).toLocaleString();
      
      const formattedRate = `${profitRate >= 0 ? '+' : ''}${profitRate.toFixed(1)}%`;
      
      result.push({
        item,
        quantity: formattedQty,
        profitRate: formattedRate,
        rateValue: profitRate
      });
    }
    
    // 首先按库存是否为正排序，然后按库存数量从高到低排序
    result.sort((a, b) => {
      const aQty = parseInt(a.quantity.replace(/,/g, ''));
      const bQty = parseInt(b.quantity.replace(/,/g, ''));
      
      // 先按是否为正排序
      if ((aQty > 0 && bQty <= 0) || (aQty <= 0 && bQty > 0)) {
        return aQty > 0 ? -1 : 1;
      }
      
      // 然后按绝对数量从高到低排序
      return Math.abs(bQty) - Math.abs(aQty);
    });
    
    // 取前N项
    return result.slice(0, limit);
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

// 获取收入情况数据
const getWeeklyIncome = async () => {
  try {
    const now = new Date();
    const result = [];
    
    // 查找当前周的周三
    const wednesday = new Date(now);
    const dayOfWeek = wednesday.getDay();
    const daysToWednesday = (3 - dayOfWeek + 7) % 7;
    wednesday.setDate(wednesday.getDate() + daysToWednesday);
    wednesday.setHours(8, 0, 0, 0);
    
    // 生成最近10周的日期
    const weeks = [];
    for (let i = 0; i < 10; i++) {
      const startDate = new Date(wednesday);
      startDate.setDate(startDate.getDate() - (i * 7));
      weeks.push({
        startDate,
        endDate: i === 0 ? now : new Date(startDate.getTime() + 7 * 24 * 60 * 60 * 1000)
      });
    }
    
    // 按从早到晚排序
    weeks.sort((a, b) => a.startDate - b.startDate);
    
    // 获取出库数据
    const stockInQuery = 'SELECT item_name, AVG(avg_cost) as avg_cost FROM stock_in GROUP BY item_name';
    const stockOutQuery = 'SELECT item_name, quantity, unit_price, fee, transaction_time FROM stock_out';
    
    const inPrices = {};
    const stockInResults = await query(stockInQuery);
    for (const row of stockInResults) {
      inPrices[row.item_name] = parseFloat(row.avg_cost || 0);
    }
    
    const stockOutResults = await query(stockOutQuery);
    
    // 计算每周收入
    for (const week of weeks) {
      let income = 0;
      
      for (const row of stockOutResults) {
        const transactionTime = new Date(row.transaction_time);
        if (transactionTime >= week.startDate && transactionTime <= week.endDate) {
          const itemName = row.item_name;
          const quantity = parseFloat(row.quantity);
          const unitPrice = parseFloat(row.unit_price);
          const fee = parseFloat(row.fee || 0);
          
          // 查找入库均价（成本）
          const inPrice = inPrices[itemName] || 0;
          
          // 计算此次交易的收入 = (出库单价 - 入库均价) * 数量 - 手续费
          const transactionIncome = (unitPrice - inPrice) * quantity - fee;
          income += transactionIncome;
        }
      }
      
      // 格式化日期
      const dateLabel = `${week.startDate.getMonth() + 1}/${week.startDate.getDate()}`;
      result.push([dateLabel, income]);
    }
    
    return result;
  } catch (error) {
    logger.error(`获取收入情况数据失败: ${error.message}`);
    return [];
  }
};

// 获取所有物品
const getAllItems = async () => {
  try {
    const query = 'SELECT DISTINCT item_name FROM inventory ORDER BY item_name';
    const results = await pool.query(query);
    return results[0].map(row => row.item_name);
  } catch (error) {
    logger.error(`获取所有物品失败: ${error.message}`);
    return [];
  }
};

// 获取行情数据
const getMarketData = async () => {
  try {
    // 获取最新银两价格
    const silverQuery = 'SELECT price FROM silver_price ORDER BY update_time DESC LIMIT 1';
    const silverResult = await query(silverQuery);
    const silverPrice = silverResult.length > 0 ? `¥${parseFloat(silverResult[0].price).toFixed(2)}/万` : 'N/A';
    
    // 获取最新女娲石价格
    const nvwaQuery = 'SELECT price FROM nvwa_price ORDER BY update_time DESC LIMIT 1';
    const nvwaResult = await query(nvwaQuery);
    const nvwaPrice = nvwaResult.length > 0 ? `¥${parseFloat(nvwaResult[0].price).toFixed(2)}/个` : 'N/A';
    
    return { 
      silverPrice, 
      nvwaPrice,
      marketStatus: '盘中行情，趋势上涨' // 示例固定文本
    };
  } catch (error) {
    logger.error(`获取行情数据失败: ${error.message}`);
    return { silverPrice: 'N/A', nvwaPrice: 'N/A', marketStatus: '数据获取失败' };
  }
};

// 获取总库存统计
const getInventoryStats = async () => {
  try {
    const statsQuery = 'SELECT COUNT(*), SUM(quantity), SUM(inventory_value) FROM inventory WHERE quantity > 0';
    const lowStockQuery = 'SELECT COUNT(*) FROM inventory WHERE quantity > 0 AND quantity < 30';
    
    const statsResult = await query(statsQuery);
    const lowStockResult = await query(lowStockQuery);
    
    const itemCount = statsResult[0]['COUNT(*)'] || 0;
    const totalQuantity = statsResult[0]['SUM(quantity)'] || 0;
    const totalValue = statsResult[0]['SUM(inventory_value)'] || 0;
    const lowStockCount = lowStockResult[0]['COUNT(*)'] || 0;
    
    return {
      itemCount,
      totalQuantity,
      totalValue,
      lowStockCount
    };
  } catch (error) {
    logger.error(`获取库存统计失败: ${error.message}`);
    return { itemCount: 0, totalQuantity: 0, totalValue: 0, lowStockCount: 0 };
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
  getWeeklyIncome,
  getAllItems,
  getMarketData,
  getInventoryStats
}; 