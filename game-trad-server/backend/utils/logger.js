// 自定义的日志系统 - 简单实现替代winston库版本
const fs = require('fs-extra');
const path = require('path');

// 确保日志目录存在
const logDir = process.env.LOG_DIR || './logs';
fs.ensureDirSync(logDir);

// 日志级别
const LOG_LEVELS = {
    ERROR: 'ERROR',
    WARN: 'WARN',
    INFO: 'INFO',
    DEBUG: 'DEBUG'
};

// 生成时间戳字符串
const getTimestamp = () => {
    return new Date().toISOString();
};

// 将日志写入文件
const writeToFile = (message, level) => {
    const timestamp = getTimestamp();
    const logEntry = `[${timestamp}] [${level}] ${message}\n`;
    
    // 将日志写入app.log
    const logFile = path.join(logDir, 'app.log');
    fs.appendFileSync(logFile, logEntry);
    
    // 错误日志也写入error.log
    if (level === LOG_LEVELS.ERROR) {
        const errorLogFile = path.join(logDir, 'error.log');
        fs.appendFileSync(errorLogFile, logEntry);
    }
};

// 日志系统对象
const logger = {
    error: (message) => {
        console.error(`ERROR: ${message}`);
        writeToFile(message, LOG_LEVELS.ERROR);
    },
    
    warn: (message) => {
        console.warn(`WARN: ${message}`);
        writeToFile(message, LOG_LEVELS.WARN);
    },
    
    info: (message) => {
        console.info(`INFO: ${message}`);
        writeToFile(message, LOG_LEVELS.INFO);
    },
    
    debug: (message) => {
        if (process.env.LOG_LEVEL === 'debug') {
            console.debug(`DEBUG: ${message}`);
            writeToFile(message, LOG_LEVELS.DEBUG);
        }
    },
    
    // 获取最近的日志
    getRecentLogs: async (limit = 100, logType = 'app') => {
        try {
            const logFile = path.join(logDir, `${logType}.log`);
            if (!fs.existsSync(logFile)) {
                return [];
            }
            
            const logs = fs.readFileSync(logFile, 'utf8')
                .split('\n')
                .filter(line => line.trim())
                .slice(-limit);
            
            return logs.map(log => {
                const match = log.match(/\[(.*?)\] \[(.*?)\] (.*)/);
                if (match) {
                    return {
                        timestamp: match[1],
                        level: match[2],
                        message: match[3]
                    };
                }
                return { raw: log };
            });
        } catch (error) {
            console.error(`获取日志失败: ${error.message}`);
            return [];
        }
    }
};

module.exports = logger; 