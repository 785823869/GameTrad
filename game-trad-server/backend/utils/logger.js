// 自定义的日志系统 - 简单实现替代winston库版本
const fs = require('fs-extra');
const path = require('path');
const db = require('./db'); // 导入数据库连接器

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

// 确保数据库中有system_logs表
const ensureLogsTable = async () => {
    try {
        // 检查表是否存在
        const checkTableQuery = `
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = '${db.dbConfig.database}' 
            AND table_name = 'system_logs'
        `;
        
        const result = await db.fetchOne(checkTableQuery);
        
        if (!result || result.count === 0) {
            // 创建表
            const createTableQuery = `
                CREATE TABLE system_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    level VARCHAR(10) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(50) DEFAULT 'system'
                )
            `;
            
            await db.execute(createTableQuery);
            console.info('创建system_logs表成功');
        }
        return true;
    } catch (error) {
        console.error(`确保system_logs表存在失败: ${error.message}`);
        return false;
    }
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

// 将日志写入数据库
const writeToDatabase = async (message, level) => {
    try {
        // 确保日志表存在
        const tableExists = await ensureLogsTable();
        if (!tableExists) return;
        
        // 插入日志
        const query = `
            INSERT INTO system_logs (level, message)
            VALUES (?, ?)
        `;
        
        await db.execute(query, [level, message]);
    } catch (error) {
        console.error(`写入日志到数据库失败: ${error.message}`);
    }
};

// 日志系统对象
const logger = {
    error: (message) => {
        console.error(`ERROR: ${message}`);
        writeToFile(message, LOG_LEVELS.ERROR);
        writeToDatabase(message, LOG_LEVELS.ERROR);
    },
    
    warn: (message) => {
        console.warn(`WARN: ${message}`);
        writeToFile(message, LOG_LEVELS.WARN);
        writeToDatabase(message, LOG_LEVELS.WARN);
    },
    
    info: (message) => {
        console.info(`INFO: ${message}`);
        writeToFile(message, LOG_LEVELS.INFO);
        writeToDatabase(message, LOG_LEVELS.INFO);
    },
    
    debug: (message) => {
        if (process.env.LOG_LEVEL === 'debug') {
            console.debug(`DEBUG: ${message}`);
            writeToFile(message, LOG_LEVELS.DEBUG);
            writeToDatabase(message, LOG_LEVELS.DEBUG);
        }
    },
    
    // 获取最近的日志
    getRecentLogs: async (limit = 100, logType = 'app') => {
        try {
            // 优先从数据库获取日志
            if (logType === 'app' || logType === 'error') {
                try {
                    const tableExists = await ensureLogsTable();
                    if (tableExists) {
                        const query = logType === 'error' 
                            ? `SELECT * FROM system_logs WHERE level = 'ERROR' ORDER BY timestamp DESC LIMIT ?`
                            : `SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT ?`;
                        
                        const logs = await db.fetchAll(query, [limit]);
                        
                        if (logs && logs.length > 0) {
                            return logs.map(log => ({
                                timestamp: new Date(log.timestamp).toISOString(),
                                level: log.level,
                                message: log.message
                            }));
                        }
                    }
                } catch (dbError) {
                    console.error(`从数据库获取日志失败: ${dbError.message}`);
                }
            }
            
            // 如果从数据库获取失败，则从文件获取
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
    },
    
    // 按日期获取日志
    getLogsByDate: async (date, logType = 'app') => {
        try {
            // 从数据库获取指定日期的日志
            const tableExists = await ensureLogsTable();
            if (tableExists) {
                const query = logType === 'error'
                    ? `SELECT * FROM system_logs WHERE level = 'ERROR' AND DATE(timestamp) = ? ORDER BY timestamp DESC`
                    : `SELECT * FROM system_logs WHERE DATE(timestamp) = ? ORDER BY timestamp DESC`;
                
                const logs = await db.fetchAll(query, [date]);
                
                if (logs && logs.length > 0) {
                    return logs.map(log => ({
                        timestamp: new Date(log.timestamp).toISOString(),
                        level: log.level,
                        message: log.message
                    }));
                }
            }
            
            // 如果从数据库获取失败或没有结果，尝试从文件获取
            return [];
        } catch (error) {
            console.error(`获取日志失败: ${error.message}`);
            return [];
        }
    }
};

// 初始化日志表
ensureLogsTable().catch(err => console.error(`日志表初始化失败: ${err.message}`));

module.exports = logger; 