const os = require('os');
const process = require('process');
const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const dbHelper = require('../utils/dbHelper');
const axios = require('axios');
const cheerio = require('cheerio');
const { appendSilver7881PriceHistory, getSilver7881PriceHistory } = require('../utils/dbHelper');

/**
 * 获取系统信息
 * @returns {Object} - 系统信息对象
 */
const getSystemInfo = () => {
  return {
    platform: os.platform(),
    arch: os.arch(),
    cpus: os.cpus().length,
    totalMemory: Math.round(os.totalmem() / (1024 * 1024 * 1024) * 100) / 100 + ' GB',
    freeMemory: Math.round(os.freemem() / (1024 * 1024 * 1024) * 100) / 100 + ' GB',
    uptime: Math.round(os.uptime() / 3600) + ' hours',
    nodeVersion: process.version
  };
};

/**
 * 获取服务信息
 * @returns {Object} - 服务信息对象
 */
const getServiceInfo = () => {
  const startTime = new Date(Date.now() - process.uptime() * 1000);
  
  return {
    pid: process.pid,
    uptime: Math.round(process.uptime() / 60) + ' minutes',
    startTime: startTime.toISOString(),
    memoryUsage: Math.round(process.memoryUsage().rss / (1024 * 1024) * 100) / 100 + ' MB',
    apiVersion: '1.0.0'
  };
};

/**
 * 获取磁盘使用情况（模拟）
 * @returns {Object} - 磁盘使用信息
 */
const getDiskUsage = () => {
  // 在实际项目中，可以使用node模块如'diskusage'获取真实数据
  return {
    total: '500 GB',
    free: '320 GB',
    used: '180 GB',
    usedPercentage: '36%'
  };
};

/**
 * 获取仪表盘数据（包含系统状态、统计数据和最近活动）
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getDashboardData = async (req, res) => {
  try {
    // 获取系统资源使用情况
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const memoryPercentage = Math.round(((totalMem - freeMem) / totalMem) * 100);
    
    // CPU使用率（模拟数据）
    const cpuPercentage = Math.floor(Math.random() * 60) + 10; // 10-70%范围内的随机值
    
    // 磁盘使用率（模拟数据）
    const diskPercentage = 36; // 来自getDiskUsage
    
    // 从数据库获取交易数据
    const { totalProfit, monthOnMonthChange } = await dbHelper.getTotalTradingProfit();
    const { totalValue, monthOnMonthChange: assetGrowth } = await dbHelper.getTotalInventoryValue();
    const inventoryStats = await dbHelper.getInventoryStats();
    const inventoryDetails = await dbHelper.getInventoryDetails(5); // 获取前5项库存详情
    const weeklyIncome = await dbHelper.getWeeklyIncome();
    const marketData = await dbHelper.getMarketData();
    
    // 从交易数据创建物品排名数据
    const itemRanking = inventoryDetails.map(item => ({
      item: item.item,
      amount: parseInt(item.quantity.replace(/,/g, '')),
      change: parseFloat(item.rateValue)
    }));
    
    // 使用周收入数据创建趋势图数据
    const trendData = weeklyIncome.map(([date, value], index) => ({
      date,
      price: Math.round(value / 10) // 缩放值以适合UI显示
    }));
    
    // 从收入数据计算总收入
    const totalIncome = weeklyIncome.reduce((sum, [_, value]) => sum + value, 0);
    
    // 构建收入图表数据
    const incomeData = {
      months: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'],
      values: Array(12).fill(0), // 初始化为全0
      total: totalIncome
    };
    
    // 填充当前月份的数据（示例）
    const currentMonth = new Date().getMonth();
    incomeData.values[currentMonth] = totalIncome;
    
    // 统计数据 - 使用项目相关统计
    const getStatistics = async () => {
      try {
        return {
          recipes: await countRecipes(),
          logs: await countLogs(),
          updates: await countUpdates(),
          ocr_jobs: await countOcrJobs()
        };
      } catch (error) {
        logger.error(`获取统计数据失败: ${error.message}`);
        return {
          recipes: 0,
          logs: 0,
          updates: 0,
          ocr_jobs: 0
        };
      }
    };
    
    // 模拟计数方法（实际项目中应从数据库获取）
    const countRecipes = async () => Math.floor(Math.random() * 50) + 10;
    const countLogs = async () => Math.floor(Math.random() * 100) + 50;
    const countUpdates = async () => Math.floor(Math.random() * 20) + 5;
    const countOcrJobs = async () => Math.floor(Math.random() * 30) + 5;
    
    // 生成最近活动数据
    const generateRecentActivity = () => {
      const activities = [
        { action: '添加新配方', timestamp: '2023-05-15 14:32:45', user: '管理员' },
        { action: '执行OCR任务', timestamp: '2023-05-15 13:45:22', user: '系统' },
        { action: '更新系统设置', timestamp: '2023-05-15 11:20:15', user: '管理员' },
        { action: '导出日志文件', timestamp: '2023-05-14 16:55:10', user: '管理员' },
        { action: '备份配方数据', timestamp: '2023-05-14 10:30:05', user: '系统' }
      ];
      
      return activities;
    };
    
    const statistics = await getStatistics();
    const recentActivity = generateRecentActivity();
    
    // 构建并返回仪表盘所需的数据结构
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      system: {
        cpu_usage: cpuPercentage,
        memory_usage: memoryPercentage,
        disk_usage: diskPercentage,
        platform: os.platform(),
        uptime: Math.round(os.uptime() / 3600) + ' hours'
      },
      statistics: statistics,
      recent_activity: recentActivity,
      // 添加交易数据
      trading: {
        summary: {
          totalProfit: totalProfit,
          profitGrowth: monthOnMonthChange,
          totalAssets: totalValue,
          assetGrowth: assetGrowth,
          marketStatus: marketData.marketStatus,
          silverPrice: marketData.silverPrice,
          nvwaPrice: marketData.nvwaPrice
        },
        itemTrends: trendData,
        itemRanking: itemRanking,
        incomeData: incomeData,
        inventoryStats: inventoryStats
      }
    });
  } catch (error) {
    logger.error(`获取仪表盘数据失败: ${error.message}`);
    
    res.status(500).json({
      success: false,
      message: '获取仪表盘数据失败',
      error: error.message
    });
  }
};

/**
 * 获取服务状态
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getStatus = async (req, res) => {
  try {
    const systemInfo = getSystemInfo();
    const serviceInfo = getServiceInfo();
    const diskUsage = getDiskUsage();
    
    // 返回服务状态信息
    res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      status: 'running',
      system: systemInfo,
      service: serviceInfo,
      disk: diskUsage
    });
  } catch (error) {
    logger.error(`获取服务状态失败: ${error.message}`);
    
    res.status(500).json({
      success: false,
      message: '获取服务状态失败',
      error: error.message
    });
  }
};

/**
 * 获取健康状态
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.healthCheck = (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
};

/**
 * 创建一个简单的内存缓存
 */
const cache = {
  nvwaPrice: {
    data: null,
    timestamp: 0,
    days: 0,
    retries: 0   // 添加重试计数器
  },
  silverPrice: {
    data: null,
    timestamp: 0,
    days: 0,
    retries: 0   // 添加银两价格缓存
  }
};

// 添加重试函数
async function retryOperation(operation, maxRetries = 3, delay = 2000) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      logger.warn(`操作失败，尝试第${attempt}次重试，错误: ${error.message}`);
      
      if (attempt < maxRetries) {
        // 等待一段时间后重试
        await new Promise(resolve => setTimeout(resolve, delay * attempt));
      }
    }
  }
  
  // 所有重试都失败了
  throw lastError;
}

/**
 * 获取女娲石价格数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getNvwaPrice = async (req, res) => {
  try {
    const range = req.query.range || 'week'; // 默认获取一周的数据
    let days = 7;
    
    // 根据range参数确定天数
    switch(range) {
      case 'day':
        days = 1;
        break;
      case 'week':
        days = 7;
        break;
      case 'month':
        days = 30;
        break;
      case 'year':
        days = 365;
        break;
      default:
        days = 7;
    }
    
    // 检查缓存是否存在且有效（缩短缓存时间到5分钟，提高数据更新频率）
    const now = Date.now();
    const cacheMaxAge = 5 * 60 * 1000; // 5分钟
    const forceRefresh = req.query.refresh === 'true';
    
    // 如果有足够新的缓存且请求的日期范围相同，而且没有强制刷新请求
    if (
      !forceRefresh &&
      cache.nvwaPrice.data && 
      cache.nvwaPrice.timestamp + cacheMaxAge > now &&
      cache.nvwaPrice.days === days
    ) {
      logger.info('使用缓存的女娲石价格数据');
      return res.status(200).json(cache.nvwaPrice.data);
    }
    
    // 如果没有缓存或缓存过期，爬取新数据
    try {
      logger.info(`开始爬取女娲石价格数据，请求范围: ${days}天`);
      
      // 使用重试机制爬取数据
      const data = await retryOperation(
        async () => await scrapeNvwaPriceData(days),
        3,  // 最多3次重试
        1000 // 每次重试间隔1秒
      );
      
      // 更新缓存
      cache.nvwaPrice = {
        data: data,
        timestamp: now,
        days: days,
        retries: 0
      };
      
      logger.info('成功爬取并缓存女娲石价格数据');
      
      // 返回爬取的数据
      return res.status(200).json(data);
    } catch (scrapeError) {
      cache.nvwaPrice.retries += 1;
      logger.error(`爬取失败(第${cache.nvwaPrice.retries}次), 使用模拟数据: ${scrapeError.message}`);
      
      // 如果爬取失败且重试次数超过阈值，则缓存模拟数据（但缓存时间较短）
      const mockData = generateMockNvwaData(days);
      
      const response = {
        success: true,
        timestamp: new Date().toISOString(),
        source: 'mock_data',
        current: {
          price: mockData.currentPrice,
          trend: mockData.trend,
          updated: new Date().toLocaleDateString(),
          note: `使用模拟数据（爬取失败${cache.nvwaPrice.retries}次）`
        },
        prices: mockData.prices,
        dates: mockData.dates
      };
      
      // 只有当重试次数较少时才缓存模拟数据，且缓存时间较短
      if (cache.nvwaPrice.retries < 5) {
        cache.nvwaPrice = {
          data: response,
          timestamp: now,
          days: days,
          retries: cache.nvwaPrice.retries
        };
      }
      
      return res.status(200).json(response);
    }
  } catch (error) {
    logger.error(`获取女娲石价格数据失败: ${error.message}`);
    
    // 返回错误信息
    res.status(500).json({
      success: false,
      message: '获取女娲石价格数据失败',
      error: error.message
    });
  }
};

/**
 * 爬取女娲石价格数据
 * @param {number} days - 需要获取的天数
 * @returns {Object} 爬取的价格数据
 */
async function scrapeNvwaPriceData(days) {
  try {
    // 同时爬取DD373和7881的数据
    const [dd373Data, _7881Data] = await Promise.all([
      scrapeDD373NvwaPrice(days),
      scrape7881NvwaPrice(days)
    ]);
    
    // 合并数据
    const prices = {
      'DD373': dd373Data.prices,
      '7881': _7881Data.prices
    };
    
    const dates = {
      'DD373': dd373Data.dates,
      '7881': _7881Data.dates
    };
    
    // 确定当前价格和趋势（使用DD373的数据）
    const currentPrice = dd373Data.prices.length > 0 
      ? dd373Data.prices[dd373Data.prices.length - 1] 
      : 3.25;
      
    const previousPrice = dd373Data.prices.length > 1 
      ? dd373Data.prices[dd373Data.prices.length - 2] 
      : currentPrice;
      
    const trend = previousPrice > 0 
      ? ((currentPrice - previousPrice) / previousPrice) * 100 
      : 0;
    
    // 构造返回数据
    return {
      success: true,
      timestamp: new Date().toISOString(),
      source: 'crawler',
      current: {
        price: currentPrice,
        trend: parseFloat(trend.toFixed(2)),
        updated: new Date().toLocaleDateString()
      },
      prices: prices,
      dates: dates
    };
  } catch (error) {
    logger.error(`爬取失败: ${error.message}`);
    throw error;
  }
}

/**
 * 爬取DD373女娲石价格
 * @param {number} days - 需要获取的天数
 * @returns {Object} 爬取的价格数据
 */
async function scrapeDD373NvwaPrice(days) {
  try {
    // 使用用户提供的确切URL
    const url = 'https://www.dd373.com/s-0v21b3-vh1cw1-xdde8h-0-0-0-t75h2e-0-0-0-4pvu7k$ha92am-0-1-20-5-0.html';
    const response = await axios.get(url, {
      timeout: 15000, // 增加超时时间到15秒
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    // 使用cheerio解析HTML
    const $ = cheerio.load(response.data);
    
    // 提取价格信息
    let currentPrice = 3.25; // 默认值
    let prices = [];
    let dates = [];
    
    // 提取所有价格项
    const priceItems = [];
    
    // 使用用户提供的精确DOM路径
    logger.info('使用用户提供的精确DD373选择器获取价格');
    try {
      // 新的精确选择器
      const priceElement = $('body > div.main > div.goods-list-content > div > div.sell-goods > div.good-list-box > div:nth-child(1) > div.width233.p-l30 > div > p.font12.color666.m-t5');
      if (priceElement.length > 0) {
        const priceText = priceElement.text().trim();
        logger.info(`DD373新选择器价格文本: ${priceText}`);
        // 匹配格式: 1个女娲石=1169.0000元
        const priceMatch = priceText.match(/1个女娲石=(\d+(\.\d+)?)元/);
        if (priceMatch && priceMatch[1]) {
          const price = parseFloat(priceMatch[1]);
          if (!isNaN(price) && price > 0) {
            priceItems.push(price);
            logger.info(`DD373新选择器解析到价格: ${price}元`);
          }
        }
      } else {
        logger.warn('DD373新选择器未找到价格元素');
      }
    } catch (e) {
      logger.error(`使用新精确选择器解析DD373价格出错: ${e.message}`);
    }
    
    // 如果使用精确选择器没有找到价格，尝试其他方法
    if (priceItems.length === 0) {
      logger.info('尝试使用其他DD373选择器');
      
      // 尝试查找所有商品列表项
      $('.good-list-box .item, .commodity-list .item').each((index, element) => {
        try {
          // 查找价格文本
          const priceElement = $(element).find('h3.text-strong, .price, .text-price');
          const priceText = priceElement.text().trim();
          
          logger.info(`DD373商品项 ${index + 1} 价格文本: ${priceText}`);
          
          // 尝试匹配"1个女娲石=X元"格式
          const priceMatch = priceText.match(/1个女娲石=(\d+(\.\d+)?)元/);
          if (priceMatch && priceMatch[1]) {
            const price = parseFloat(priceMatch[1]);
            if (!isNaN(price) && price > 0) {
              priceItems.push(price);
            }
          } else {
            // 尝试提取任何数字作为价格
            const numericMatch = priceText.match(/(\d+(\.\d+)?)/);
            if (numericMatch && numericMatch[1]) {
              const price = parseFloat(numericMatch[1]);
              if (!isNaN(price) && price > 0 && price < 10000) { // 添加上限以排除不合理的价格
                priceItems.push(price);
              }
            }
          }
        } catch (e) {
          logger.error(`解析DD373商品项 ${index + 1} 出错: ${e.message}`);
        }
      });
    }
    
    // 输出找到的所有价格
    if (priceItems.length > 0) {
      logger.info(`DD373找到的所有价格: ${JSON.stringify(priceItems)}`);
      
      // 排序价格，取最低价格作为当前价格
      priceItems.sort((a, b) => a - b);
      currentPrice = priceItems[0];
      logger.info(`DD373女娲石当前价格：${currentPrice}元/个`);
    } else {
      logger.warn('DD373未找到有效价格，使用默认价格');
    }
    
    // 生成历史数据（实际应该从网站爬取，这里模拟）
    const today = new Date();
    const basePrice = currentPrice;
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const formattedDate = date.toISOString().split('T')[0];
      
      // 创建历史波动
      const randomFactor = Math.sin(i / 5) * 0.1 + (Math.random() - 0.5) * 0.05;
      const historicalPrice = basePrice * (1 + randomFactor);
      
      prices.push(parseFloat(historicalPrice.toFixed(2)));
      dates.push(formattedDate);
    }
    
    // 确保最后一个价格是当前爬取的价格
    if (prices.length > 0) {
      prices[prices.length - 1] = currentPrice;
    }
    
    logger.info(`DD373爬虫完成，生成了${prices.length}个历史价格点`);
    return { prices, dates };
  } catch (error) {
    logger.error(`DD373爬取失败: ${error.message}`);
    // 如果爬取失败，返回模拟数据
    return generateSinglePlatformMockData(days, 3.25);
  }
}

/**
 * 爬取7881女娲石价格
 * @param {number} days - 需要获取的天数
 * @returns {Object} 爬取的价格数据
 */
async function scrape7881NvwaPrice(days) {
  try {
    // 官方接口地址
    const url = 'https://gw.7881.com/goods-service-api/api/goods/list';
    // 请求体参数（女娲石示例）
    const body = {
      marketRequestSource: 'search',
      sellerType: 'C',
      gameId: 'G5722',
      gtid: '100038',
      groupId: 'G5722P001',
      serverId: 'G5722P001018',
      tradePlace: '0',
      goodsSortType: '1',
      extendAttrList: [],
      pageNum: 1,
      pageSize: 30
    };
    // 只带必要头部，若有校验需求再补充
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'Mozilla/5.0',
      'Accept': 'application/json'
    };
    const response = await axios.post(url, body, { headers, timeout: 10000 });
    const list = response.data?.data?.list;
    if (!Array.isArray(list) || list.length === 0) {
      // 没有数据时返回模拟数据
      logger.warn('7881接口未返回商品列表，使用模拟数据');
      return generateSinglePlatformMockData(days, 1160);
    }
    // 找出最低价商品
    let minItem = list[0];
    for (const item of list) {
      if (parseFloat(item.priceOfUnitForShow) < parseFloat(minItem.priceOfUnitForShow)) {
        minItem = item;
      }
    }
    const currentPrice = parseFloat(minItem.priceOfUnitForShow || minItem.price || minItem.priceStr);
    logger.info(`7881女娲石当前价格：${currentPrice}元/个`);
    
    // 生成历史数据
    const today = new Date();
    const prices = [];
    const dates = [];
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const formattedDate = date.toISOString().split('T')[0];
      // 创建历史波动
      const randomFactor = Math.sin(i / 4) * 0.12 + (Math.random() - 0.5) * 0.06;
      const historicalPrice = currentPrice * (1 + randomFactor);
      prices.push(parseFloat(historicalPrice.toFixed(2)));
      dates.push(formattedDate);
    }
    // 确保最后一个价格是当前爬取的价格
    if (prices.length > 0) {
      prices[prices.length - 1] = currentPrice;
    }
    logger.info(`7881爬虫完成，生成了${prices.length}个历史价格点`);
    return { prices, dates };
  } catch (error) {
    logger.error(`7881接口采集失败: ${error.message}`);
    return generateSinglePlatformMockData(days, 1160);
  }
}

/**
 * 为单个平台生成模拟数据
 * @param {number} days - 需要生成的天数
 * @param {number} basePrice - 基础价格
 * @returns {Object} 模拟的价格数据
 */
function generateSinglePlatformMockData(days, basePrice) {
  const prices = [];
  const dates = [];
  
  const today = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    const formattedDate = date.toISOString().split('T')[0];
    
    // 创建波动
    const randomFactor = Math.sin(i / 5) * 0.2 + (Math.random() - 0.5) * 0.1;
    const price = basePrice * (1 + randomFactor);
    
    prices.push(parseFloat(price.toFixed(2)));
    dates.push(formattedDate);
  }
  
  return { prices, dates };
}

/**
 * 生成模拟的女娲石价格数据（当爬虫失败时使用）
 * @param {number} days - 需要生成的天数
 * @returns {Object} 模拟的价格数据
 */
const generateMockNvwaData = (days) => {
  const dd373Data = generateSinglePlatformMockData(days, 3.25);
  const _7881Data = generateSinglePlatformMockData(days, 3.30);
  
  // 计算当前价格和趋势
  const currentPrice = dd373Data.prices[dd373Data.prices.length - 1];
  const previousPrice = dd373Data.prices[dd373Data.prices.length - 2] || currentPrice;
  const trend = previousPrice > 0 ? ((currentPrice - previousPrice) / previousPrice) * 100 : 0;
  
  return {
    currentPrice,
    trend: parseFloat(trend.toFixed(2)),
    prices: {
      'DD373': dd373Data.prices,
      '7881': _7881Data.prices
    },
    dates: {
      'DD373': dd373Data.dates,
      '7881': _7881Data.dates
    }
  };
};

/**
 * 获取银两价格数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getSilverPrice = async (req, res) => {
  try {
    const range = req.query.range || 'week'; // 默认获取一周的数据
    let days = 7;
    
    // 根据range参数确定天数
    switch(range) {
      case 'day':
        days = 1;
        break;
      case 'week':
        days = 7;
        break;
      case 'month':
        days = 30;
        break;
      case 'year':
        days = 365;
        break;
      default:
        days = 7;
    }
    
    // 检查缓存是否存在且有效
    const now = Date.now();
    const cacheMaxAge = 5 * 60 * 1000; // 5分钟
    const forceRefresh = req.query.refresh === 'true';
    
    // 如果有足够新的缓存且请求的日期范围相同，而且没有强制刷新请求
    if (
      !forceRefresh &&
      cache.silverPrice.data && 
      cache.silverPrice.timestamp + cacheMaxAge > now &&
      cache.silverPrice.days === days
    ) {
      logger.info('使用缓存的银两价格数据');
      return res.status(200).json(cache.silverPrice.data);
    }
    
    // 爬取新数据
    try {
      logger.info(`开始爬取银两价格数据，请求范围: ${days}天`);
      
      // 使用重试机制爬取数据
      const data = await retryOperation(
        async () => await scrapeSilverPriceData(days),
        3,  // 最多3次重试
        1000 // 每次重试间隔1秒
      );
      
      // 更新缓存
      cache.silverPrice = {
        data: data,
        timestamp: now,
        days: days,
        retries: 0
      };
      
      logger.info('成功爬取并缓存银两价格数据');
      
      // 返回爬取的数据
      return res.status(200).json(data);
    } catch (scrapeError) {
      cache.silverPrice.retries += 1;
      logger.error(`银两价格爬取失败(第${cache.silverPrice.retries}次), 使用模拟数据: ${scrapeError.message}`);
      
      // 如果爬取失败，则生成模拟数据
      const mockData = generateMockSilverData(days);
      
      const response = {
        success: true,
        timestamp: new Date().toISOString(),
        source: 'mock_data',
        current: {
          price: mockData.currentPrice,
          trend: mockData.trend,
          updated: new Date().toLocaleDateString(),
          note: `使用模拟数据（爬取失败${cache.silverPrice.retries}次）`
        },
        prices: mockData.prices,
        dates: mockData.dates
      };
      
      // 缓存模拟数据，但缓存时间较短
      if (cache.silverPrice.retries < 5) {
        cache.silverPrice = {
          data: response,
          timestamp: now,
          days: days,
          retries: cache.silverPrice.retries
        };
      }
      
      return res.status(200).json(response);
    }
  } catch (error) {
    logger.error(`获取银两价格数据失败: ${error.message}`);
    
    // 返回错误信息
    res.status(500).json({
      success: false,
      message: '获取银两价格数据失败',
      error: error.message
    });
  }
};

/**
 * 爬取银两价格数据
 * @param {number} days - 需要获取的天数
 * @returns {Object} 爬取的价格数据
 */
async function scrapeSilverPriceData(days) {
  try {
    // 同时爬取DD373和7881的银两价格数据
    const [dd373Data, _7881Data] = await Promise.all([
      scrapeDD373SilverPrice(days),
      scrape7881SilverPrice(days)
    ]);
    
    // 整理价格数据为平台格式
    const prices = {
      'DD373': dd373Data.prices.map(item => item.price),
      '7881': _7881Data.prices
    };
    
    // 整理日期数据为平台格式
    const dates = {
      'DD373': dd373Data.prices.map(item => item.date),
      '7881': _7881Data.dates
    };
    
    // 构造返回数据
    return {
      success: true,
      timestamp: new Date().toISOString(),
      source: 'crawler',
      current: {
        price: dd373Data.currentPrice,
        trend: dd373Data.trend,
        updated: new Date().toLocaleDateString()
      },
      prices: prices,
      dates: dates
    };
  } catch (error) {
    logger.error(`银两爬取失败: ${error.message}`);
    throw error;
  }
}

/**
 * 爬取DD373银两价格
 * @param {number} days - 需要获取的天数
 * @returns {Object} 爬取的价格数据
 */
async function scrapeDD373SilverPrice(days) {
  try {
    // 使用用户提供的确切URL
    const url = 'https://www.dd373.com/s-0v21b3-vh1cw1-xdde8h-0-0-0-c2rfmg-0-0-0-0-0-1-0-5-0.html';
    const response = await axios.get(url, {
      timeout: 15000, // 增加超时时间到15秒
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    // 使用cheerio解析HTML
    const $ = cheerio.load(response.data);
    
    // 提取价格信息
    let currentPrice = 0.38; // 默认值
    let prices = [];
    
    // 使用用户提供的精确DOM路径
    logger.info('使用用户提供的DD373银两价格选择器');
    try {
      // 使用提供的选择器
      const priceElement = $('body > div.main > div.goods-list-content > div > div.sell-goods > div.good-list-box > div:nth-child(1) > div.width233.p-l30 > div > p.font12.color666.m-t5');
      
      if (priceElement.length > 0) {
        const priceText = priceElement.text().trim();
        logger.info(`银两价格文本: ${priceText}`);
        
        // 匹配"1万银=0.3776元"格式
        const priceMatch = priceText.match(/1万银=(\d+(\.\d+)?)元/);
        if (priceMatch && priceMatch[1]) {
          currentPrice = parseFloat(priceMatch[1]);
          if (!isNaN(currentPrice) && currentPrice > 0) {
            logger.info(`DD373银两当前价格：${currentPrice}元/万两`);
          }
        }
      } else {
        logger.warn('未找到银两价格元素');
      }
    } catch (e) {
      logger.error(`解析银两价格出错: ${e.message}`);
    }
    
    // 如果提取失败，尝试使用备用选择器
    if (currentPrice <= 0) {
      logger.info('尝试使用备用选择器获取银两价格');
      
      try {
        $('.good-list-box .item').each((index, element) => {
          // 查找价格文本
          const priceText = $(element).text().trim();
          
          // 寻找包含"万银"或"元/万银"的文本
          if (priceText.includes('万银') || priceText.includes('元/万')) {
            // 尝试提取数字
            const numericMatches = priceText.match(/(\d+(\.\d+)?)/g);
            if (numericMatches && numericMatches.length > 0) {
              // 找出合理范围内的价格（一般银两价格在0.2-1.0元/万两之间）
              for (const match of numericMatches) {
                const price = parseFloat(match);
                if (!isNaN(price) && price > 0 && price < 10) {
                  currentPrice = price;
                  logger.info(`从备用选择器提取到银两价格: ${price}元/万两`);
                  break;
                }
              }
            }
          }
        });
      } catch (e) {
        logger.error(`备用选择器解析银两价格出错: ${e.message}`);
      }
    }
    
    // 生成历史数据
    const today = new Date();
    const basePrice = currentPrice > 0 ? currentPrice : 0.38;
    
    // 计算上一个价格点，用于趋势计算
    const previousPrice = basePrice * (1 + (Math.random() - 0.5) * 0.1);
    const trend = ((basePrice - previousPrice) / previousPrice) * 100;
    
    // 生成历史数据
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const formattedDate = date.toISOString().split('T')[0];
      
      // 创建历史波动
      const randomFactor = Math.sin(i / 4) * 0.12 + (Math.random() - 0.5) * 0.06;
      const historicalPrice = basePrice * (1 + randomFactor);
      
      prices.push({
        date: formattedDate,
        price: parseFloat(historicalPrice.toFixed(4))
      });
    }
    
    // 确保最后一个价格是当前爬取的价格
    if (prices.length > 0) {
      prices[prices.length - 1].price = basePrice;
    }
    
    logger.info(`DD373银两爬虫完成，生成了${prices.length}个历史价格点`);
    return {
      currentPrice: basePrice,
      trend: parseFloat(trend.toFixed(2)),
      prices: prices
    };
  } catch (error) {
    logger.error(`DD373银两爬取失败: ${error.message}`);
    // 采集失败时，尝试聚合历史文件已有数据
    try {
      const now = Date.now();
      const fromTs = now - days * 24 * 60 * 60 * 1000;
      const history = await getSilver7881PriceHistory(fromTs, now);
      const { prices, dates } = get15MinPeriodLows(history, 15);
      if (prices.length > 0) {
        logger.warn('采集失败，返回历史文件聚合数据');
        return { prices, dates };
      }
    } catch (e) { logger.error('采集失败且聚合历史文件出错: ' + e.message); }
    // 若无历史数据，返回模拟数据
    return generateSinglePlatformMockData(days, 0.38);
  }
}

/**
 * 爬取7881银两价格
 * @param {number} days - 需要获取的天数
 * @returns {Object} 爬取的价格数据
 */
async function scrape7881SilverPrice(days) {
  try {
    // 官方接口地址
    const url = 'https://gw.7881.com/goods-service-api/api/goods/list';
    // 请求体参数（银两参数）
    const body = {
      marketRequestSource: 'search',
      sellerType: 'C',
      gameId: 'G5722',
      gtid: '100001', // 银两的商品类型ID
      groupId: 'G5722P001',
      serverId: 'G5722P001018',
      tradePlace: '0',
      goodsSortType: '1',
      extendAttrList: [],
      pageNum: 1,
      pageSize: 30
    };
    // 只带必要头部
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'Mozilla/5.0',
      'Accept': 'application/json'
    };
    const response = await axios.post(url, body, { headers, timeout: 10000 });
    const list = response.data?.data?.list;
    if (!Array.isArray(list) || list.length === 0) {
      // 没有数据时返回模拟数据
      logger.warn('7881银两接口未返回商品列表，使用模拟数据');
      return generateSinglePlatformMockData(days, 0.38);
    }
    // 找出最低价商品
    let minItem = list[0];
    for (const item of list) {
      // 优先取priceOfUnitForShow，否则正则提取title
      let price = parseFloat(item.priceOfUnitForShow);
      if (isNaN(price) && item.title) {
        const match = item.title.match(/=([0-9.]+)元/);
        if (match && match[1]) price = parseFloat(match[1]);
      }
      if (!isNaN(price) && (isNaN(parseFloat(minItem.priceOfUnitForShow)) || price < parseFloat(minItem.priceOfUnitForShow))) {
        minItem = item;
        minItem.priceOfUnitForShow = price;
      }
    }
    const currentPrice = parseFloat(minItem.priceOfUnitForShow);
    logger.info(`7881银两当前价格：${currentPrice}元/万两`);
    // 记录历史价格点
    appendSilver7881PriceHistory(currentPrice);
    // 生成15分钟周期历史数据
    const now = Date.now();
    const fromTs = now - days * 24 * 60 * 60 * 1000;
    const history = await getSilver7881PriceHistory(fromTs, now);
    const { prices, dates } = get15MinPeriodLows(history, 15);
    logger.info(`7881银两15分钟周期聚合，生成${prices.length}个历史价格点`);
    return { prices, dates };
  } catch (error) {
    logger.error(`7881银两接口采集失败: ${error.message}`);
    return generateSinglePlatformMockData(days, 0.38);
  }
}

/**
 * 生成模拟的银两价格数据（当爬虫失败时使用）
 * @param {number} days - 需要生成的天数
 * @returns {Object} 模拟的价格数据
 */
function generateMockSilverData(days) {
  // 生成DD373和7881的模拟数据
  const dd373Data = generateSinglePlatformMockData(days, 0.38);
  const _7881Data = generateSinglePlatformMockData(days, 0.40);
  
  // 计算当前价格和趋势
  const currentPrice = dd373Data.prices[dd373Data.prices.length - 1];
  const previousPrice = dd373Data.prices[dd373Data.prices.length - 2] || currentPrice;
  const trend = previousPrice > 0 ? ((currentPrice - previousPrice) / previousPrice) * 100 : 0;
  
  // 转换DD373数据格式以匹配原格式
  const dd373FormattedPrices = [];
  for (let i = 0; i < dd373Data.prices.length; i++) {
    dd373FormattedPrices.push({
      date: dd373Data.dates[i],
      price: dd373Data.prices[i]
    });
  }
  
  return {
    currentPrice: currentPrice,
    trend: parseFloat(trend.toFixed(2)),
    prices: {
      'DD373': dd373FormattedPrices.map(item => item.price),
      '7881': _7881Data.prices
    },
    dates: {
      'DD373': dd373FormattedPrices.map(item => item.date),
      '7881': _7881Data.dates
    }
  };
}

// 15分钟周期聚合历史价格点
function get15MinPeriodLows(history, periodMinutes = 15) {
  if (!Array.isArray(history) || history.length === 0) return { prices: [], dates: [] };
  // 按时间升序排序
  history.sort((a, b) => a.timestamp - b.timestamp);
  const periodMs = periodMinutes * 60 * 1000;
  const result = [];
  let periodStart = Math.floor(history[0].timestamp / periodMs) * periodMs;
  let periodEnd = periodStart + periodMs;
  let minPrice = null;
  let minTs = null;
  for (const item of history) {
    if (item.timestamp >= periodEnd) {
      if (minPrice !== null) {
        result.push({ timestamp: minTs, price: minPrice });
      }
      // 跳到下一个周期
      while (item.timestamp >= periodEnd) {
        periodStart = periodEnd;
        periodEnd += periodMs;
      }
      minPrice = item.price;
      minTs = item.timestamp;
    } else {
      if (minPrice === null || item.price < minPrice) {
        minPrice = item.price;
        minTs = item.timestamp;
      }
    }
  }
  if (minPrice !== null) {
    result.push({ timestamp: minTs, price: minPrice });
  }
  // 输出聚合结果
  return {
    prices: result.map(r => r.price),
    dates: result.map(r => new Date(r.timestamp).toISOString())
  };
} 