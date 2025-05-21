/**
 * LogConfig.js - 全局日志配置
 * 提供统一的日志控制功能，可通过localStorage切换调试模式
 */

// 日志级别常量
export const LogLevels = {
  ERROR: 'error',
  WARN: 'warn',
  INFO: 'info',
  DEBUG: 'debug'
};

// 从localStorage获取当前日志级别，默认为'error'
const getLogLevel = () => {
  try {
    const savedLevel = localStorage.getItem('gametrad_log_level');
    return savedLevel && Object.values(LogLevels).includes(savedLevel) 
      ? savedLevel 
      : LogLevels.ERROR;
  } catch (e) {
    // 如果localStorage不可用，使用默认值
    return LogLevels.ERROR;
  }
};

// 设置日志级别
export const setLogLevel = (level) => {
  if (!Object.values(LogLevels).includes(level)) {
    console.warn(`无效的日志级别: ${level}，使用 WARN`);
    level = LogLevels.WARN;
  }
  try {
    localStorage.setItem('gametrad_log_level', level);
  } catch (e) {
    console.error('无法保存日志级别到localStorage', e);
  }
};

// 日志级别权重
const LOG_LEVEL_WEIGHTS = {
  [LogLevels.ERROR]: 1,
  [LogLevels.WARN]: 2,
  [LogLevels.INFO]: 3,
  [LogLevels.DEBUG]: 4
};

// 当前日志级别
let currentLevel = getLogLevel();

// 检查给定级别是否应该记录
const shouldLog = (level) => {
  const currentWeight = LOG_LEVEL_WEIGHTS[currentLevel] || 2; // 默认为WARN
  const targetWeight = LOG_LEVEL_WEIGHTS[level] || 4; // 默认为DEBUG
  return targetWeight <= currentWeight;
};

// 日志工具对象
const logger = {
  error: (message, ...args) => {
    console.error(message, ...args);
  },
  
  warn: (message, ...args) => {
    console.warn(message, ...args);
  },
  
  info: (message, ...args) => {
    if (shouldLog(LogLevels.INFO)) {
      console.info(message, ...args);
    }
  },
  
  debug: (message, ...args) => {
    if (shouldLog(LogLevels.DEBUG)) {
      console.debug(message, ...args);
    }
  },
  
  // 获取当前日志级别
  getLevel: () => currentLevel,
  
  // 设置当前日志级别
  setLevel: (level) => {
    setLogLevel(level);
    currentLevel = getLogLevel();
    return currentLevel;
  },
  
  // 启用调试模式
  enableDebug: () => {
    setLogLevel(LogLevels.DEBUG);
    currentLevel = LogLevels.DEBUG;
    console.log('已启用调试日志');
  },
  
  // 禁用调试模式（设为WARN级别）
  disableDebug: () => {
    setLogLevel(LogLevels.WARN);
    currentLevel = LogLevels.WARN;
    console.log('已禁用调试日志');
  },
  
  // 切换调试模式
  toggleDebug: () => {
    if (currentLevel === LogLevels.DEBUG) {
      logger.disableDebug();
      return false;
    } else {
      logger.enableDebug();
      return true;
    }
  }
};

export default logger; 