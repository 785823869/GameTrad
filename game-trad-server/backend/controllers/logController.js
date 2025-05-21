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
      logger.warn(`请求了无效的日志类型: ${logType}`);
      return res.status(400).json({ 
        success: false, 
        message: '无效的日志类型，只支持 app、error 或 access' 
      });
    }
    
    logger.info(`正在获取${logType}类型的最近${limit}条日志`);
    
    try {
      const logs = await logger.getRecentLogs(limit, logType);
      
      // 确保logs是数组
      if (!Array.isArray(logs)) {
        logger.error(`getRecentLogs返回非数组结果: ${typeof logs}`);
        return res.status(500).json({
          success: false,
          message: '获取日志失败，返回格式错误',
          error: 'logs is not iterable'
        });
      }
      
      logger.info(`成功获取${logs.length}条日志`);
      
      res.status(200).json({
        success: true,
        count: logs.length,
        logs
      });
    } catch (logError) {
      logger.error(`从logger获取日志失败: ${logError.message}`);
      res.status(500).json({
        success: false,
        message: '获取日志失败',
        error: logError.message
      });
    }
  } catch (error) {
    logger.error(`getRecentLogs控制器错误: ${error.message}`);
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
      logger.warn(`请求了无效的日期格式: ${date}`);
      return res.status(400).json({ 
        success: false, 
        message: '无效的日期格式，请使用YYYY-MM-DD格式' 
      });
    }
    
    // 验证日志类型
    if (!['app', 'error', 'access'].includes(logType)) {
      logger.warn(`请求了无效的日志类型: ${logType}`);
      return res.status(400).json({ 
        success: false, 
        message: '无效的日志类型，只支持 app、error 或 access' 
      });
    }
    
    logger.info(`正在获取${date}日期的${logType}类型日志`);
    
    try {
      const logs = await logger.getLogsByDate(date, logType);
      
      // 确保logs是数组
      if (!Array.isArray(logs)) {
        logger.error(`getLogsByDate返回非数组结果: ${typeof logs}`);
        return res.status(500).json({
          success: false,
          message: '获取日志失败，返回格式错误',
          error: 'logs is not iterable'
        });
      }
      
      logger.info(`成功获取${logs.length}条日志`);
      
      res.status(200).json({
        success: true,
        date,
        type: logType,
        count: logs.length,
        logs
      });
    } catch (logError) {
      logger.error(`按日期从logger获取日志失败: ${logError.message}`);
      res.status(500).json({
        success: false,
        message: '获取日志失败',
        error: logError.message
      });
    }
  } catch (error) {
    logger.error(`getLogsByDate控制器错误: ${error.message}`);
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
    
    // 检查logger模块中的方法是否存在并是函数类型
    const logMethod = level.toLowerCase();
    if (typeof logger[logMethod] !== 'function') {
      return res.status(500).json({
        success: false,
        message: `记录日志失败：logger.${logMethod}不是一个函数`
      });
    }
    
    // 记录日志
    logger[logMethod](message);
    
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
    console.error(`添加日志失败: ${error.message}`);
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
    logger.info(`正在获取最近${limit}条操作日志`);
    
    try {
      // 从数据库获取操作日志
      const query = `
        SELECT * FROM operation_logs 
        ORDER BY operation_time DESC 
        LIMIT ?
      `;
      
      const logs = await db.fetchAll(query, [limit]);
      
      // 确保logs是数组
      if (!Array.isArray(logs)) {
        logger.error(`从数据库获取操作日志失败: 返回的不是数组`);
        return res.status(500).json({
          success: false,
          message: '获取操作日志失败，返回格式错误',
          error: 'logs is not iterable'
        });
      }
      
      logger.info(`成功获取${logs.length}条操作日志`);
      
      // 解析操作数据
      const formattedLogs = [];
      for (let i = 0; i < logs.length; i++) {
        try {
          const log = logs[i];
          const parsedData = log.operation_data ? JSON.parse(log.operation_data) : null;
          formattedLogs.push({
            ...log,
            operation_data: parsedData
          });
        } catch (parseError) {
          logger.warn(`解析操作日志数据失败，跳过此条日志: ${parseError.message}`);
          formattedLogs.push({
            ...logs[i],
            operation_data: null,
            parse_error: '解析JSON数据失败'
          });
        }
      }
      
      res.status(200).json({
        success: true,
        count: formattedLogs.length,
        logs: formattedLogs
      });
    } catch (dbError) {
      logger.error(`从数据库获取操作日志失败: ${dbError.message}`);
      res.status(500).json({
        success: false,
        message: '获取操作日志失败',
        error: dbError.message
      });
    }
  } catch (error) {
    logger.error(`getOperationLogs控制器错误: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取操作日志失败',
      error: error.message
    });
  }
}; 