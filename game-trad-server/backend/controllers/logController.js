const logger = require('../utils/logger');
const db = require('../utils/db');

/**
 * 获取最近的日志
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getRecentLogs = async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 100;
    const logType = req.params.type || 'app';
    
    // 验证日志类型
    if (!['app', 'error', 'access'].includes(logType)) {
      return res.status(400).json({ 
        success: false, 
        message: '无效的日志类型，只支持 app、error 或 access' 
      });
    }
    
    const logs = await logger.getRecentLogs(limit, logType);
    res.status(200).json({
      success: true,
      count: logs.length,
      logs
    });
  } catch (error) {
    logger.error(`获取日志失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取日志失败',
      error: error.message
    });
  }
};

/**
 * 按日期获取日志
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getLogsByDate = async (req, res) => {
  try {
    const { date } = req.params;
    const logType = req.query.type || 'app';
    
    // 验证日期格式
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(date)) {
      return res.status(400).json({ 
        success: false, 
        message: '无效的日期格式，请使用YYYY-MM-DD格式' 
      });
    }
    
    // 验证日志类型
    if (!['app', 'error', 'access'].includes(logType)) {
      return res.status(400).json({ 
        success: false, 
        message: '无效的日志类型，只支持 app、error 或 access' 
      });
    }
    
    const logs = await logger.getLogsByDate(date, logType);
    res.status(200).json({
      success: true,
      date,
      type: logType,
      count: logs.length,
      logs
    });
  } catch (error) {
    logger.error(`获取日志失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取日志失败',
      error: error.message
    });
  }
};

/**
 * 添加一条日志（测试用）
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.addLog = async (req, res) => {
  try {
    const { level, message } = req.body;
    
    // 验证参数
    if (!level || !message) {
      return res.status(400).json({ 
        success: false, 
        message: '请提供日志级别和内容' 
      });
    }
    
    // 验证日志级别
    if (!['error', 'warn', 'info', 'debug'].includes(level.toLowerCase())) {
      return res.status(400).json({ 
        success: false, 
        message: '无效的日志级别，只支持 error、warn、info 或 debug' 
      });
    }
    
    // 记录日志
    logger[level.toLowerCase()](message);
    
    res.status(201).json({
      success: true,
      message: '日志添加成功',
      log: {
        level: level.toUpperCase(),
        message,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    logger.error(`添加日志失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '添加日志失败',
      error: error.message
    });
  }
};

/**
 * 获取操作日志
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getOperationLogs = async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 100;
    
    // 从数据库获取操作日志
    const query = `
      SELECT * FROM operation_logs 
      ORDER BY operation_time DESC 
      LIMIT ?
    `;
    
    const logs = await db.fetchAll(query, [limit]);
    
    // 解析操作数据
    const formattedLogs = logs.map(log => ({
      ...log,
      operation_data: log.operation_data ? JSON.parse(log.operation_data) : null
    }));
    
    res.status(200).json({
      success: true,
      count: formattedLogs.length,
      logs: formattedLogs
    });
  } catch (error) {
    logger.error(`获取操作日志失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取操作日志失败',
      error: error.message
    });
  }
}; 