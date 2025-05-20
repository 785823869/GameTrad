const os = require('os');
const process = require('process');
const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const dbHelper = require('../utils/dbHelper');

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