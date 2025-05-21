// 自定义的日志系统 - 简单实现替代winston库版本
const fs = require('fs-extra');
const path = require('path');
// 移除全局导入，避免循环依赖
// const db = require('./db');

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

// 日志级别权重
const LOG_LEVEL_WEIGHTS = {
    ERROR: 0,
    WARN: 1,
    INFO: 2,
    DEBUG: 3
};

// 获取当前日志级别，默认为WARN（通过环境变量控制）
const CURRENT_LOG_LEVEL = (process.env.LOG_LEVEL || 'WARN').toUpperCase();

// 检查是否应该记录某个级别的日志
const shouldLog = (level) => {
    const currentLevelWeight = LOG_LEVEL_WEIGHTS[CURRENT_LOG_LEVEL] || 1; // 默认为WARN
    const targetLevelWeight = LOG_LEVEL_WEIGHTS[level] || 3; // 默认为DEBUG
    return targetLevelWeight <= currentLevelWeight;
};

// 生成时间戳字符串
const getTimestamp = () => {
    return new Date().toISOString();
};

// 确保数据库中有system_logs表
const ensureLogsTable = async () => {
    try {
        // 延迟导入db模块，避免循环依赖
        const db = require('./db');
        
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
const writeToFile = (message, level, traceId) => {
    const timestamp = getTimestamp();
    const logEntry = `[${timestamp}] [${level}] ${traceId ? `[${traceId}] ` : ''} ${message}\n`;
    
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
const writeToDatabase = async (message, level, traceId) => {
    // 只记录ERROR和WARN级别的日志到数据库，除非明确要求记录所有级别
    if (level !== LOG_LEVELS.ERROR && level !== LOG_LEVELS.WARN && process.env.LOG_ALL_TO_DB !== 'true') {
        return;
    }
    
    try {
        // 延迟导入db模块，避免循环依赖
        const db = require('./db');
        
        // 确保日志表存在
        const tableExists = await ensureLogsTable();
        if (!tableExists) return;
        
        // 插入日志
        const query = `
            INSERT INTO system_logs (level, message, source)
            VALUES (?, ?, ?)
        `;
        
        await db.execute(query, [level, message, traceId || 'system']);
    } catch (error) {
        console.error(`写入日志到数据库失败: ${error.message}`);
    }
};

// 生成唯一的日志跟踪ID
const generateTraceId = () => {
    return `trace-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
};

// 当前活动的跟踪ID (使用异步本地存储模拟)
let activeTraceId = null;

// 日志系统对象
const logger = {
    error: (message) => {
        const tracePrefix = activeTraceId ? `[${activeTraceId}] ` : '';
        console.error(`ERROR: ${tracePrefix}${message}`);
        writeToFile(message, LOG_LEVELS.ERROR, activeTraceId);
        writeToDatabase(message, LOG_LEVELS.ERROR, activeTraceId);
    },
    
    warn: (message) => {
        const tracePrefix = activeTraceId ? `[${activeTraceId}] ` : '';
        console.warn(`WARN: ${tracePrefix}${message}`);
        writeToFile(message, LOG_LEVELS.WARN, activeTraceId);
        writeToDatabase(message, LOG_LEVELS.WARN, activeTraceId);
    },
    
    info: (message) => {
        // 检查是否应该记录INFO级别的日志
        if (!shouldLog(LOG_LEVELS.INFO)) {
            // 始终写入文件，但不输出到控制台
            writeToFile(message, LOG_LEVELS.INFO, activeTraceId);
            return;
        }
        
        const tracePrefix = activeTraceId ? `[${activeTraceId}] ` : '';
        console.info(`INFO: ${tracePrefix}${message}`);
        writeToFile(message, LOG_LEVELS.INFO, activeTraceId);
        writeToDatabase(message, LOG_LEVELS.INFO, activeTraceId);
    },
    
    debug: (message) => {
        // 检查是否应该记录DEBUG级别的日志
        if (!shouldLog(LOG_LEVELS.DEBUG)) {
            // 始终写入文件，但不输出到控制台
            writeToFile(message, LOG_LEVELS.DEBUG, activeTraceId);
            return;
        }
        
        const tracePrefix = activeTraceId ? `[${activeTraceId}] ` : '';
        console.debug(`DEBUG: ${tracePrefix}${message}`);
        writeToFile(message, LOG_LEVELS.DEBUG, activeTraceId);
        writeToDatabase(message, LOG_LEVELS.DEBUG, activeTraceId);
    },
    
    // 开始请求跟踪
    startRequest: (req) => {
        const requestId = Math.random().toString(36).substring(2, 15);
        const method = req.method || 'UNKNOWN';
        const url = req.url || 'UNKNOWN';
        const startTime = Date.now();
        const traceId = generateTraceId();
        
        // 设置当前活动的跟踪ID
        activeTraceId = traceId;
        
        // 只在DEBUG级别输出开始请求日志
        if (shouldLog(LOG_LEVELS.DEBUG)) {
            console.info(`[${requestId}][${traceId}] START ${method} ${url}`);
        }
        
        writeToFile(`开始请求: [${requestId}] ${method} ${url}`, LOG_LEVELS.INFO, traceId);
        
        return {
            requestId,
            traceId,
            method, 
            url,
            startTime,
            finish: () => {
                const duration = Date.now() - startTime;
                
                // 只在DEBUG级别输出完成请求日志
                if (shouldLog(LOG_LEVELS.DEBUG)) {
                    console.info(`[${requestId}][${traceId}] FINISH ${method} ${url} - ${duration}ms`);
                }
                
                writeToFile(`完成请求: [${requestId}] ${method} ${url} - ${duration}ms`, LOG_LEVELS.INFO, traceId);
                
                // 清除当前活动的跟踪ID
                if (activeTraceId === traceId) {
                    activeTraceId = null;
                }
            },
            log: (level, message) => {
                const logMessage = `[${requestId}][${traceId}] ${message}`;
                
                // 临时设置当前活动的跟踪ID
                const prevTraceId = activeTraceId;
                activeTraceId = traceId;
                
                logger[level.toLowerCase()](logMessage);
                
                // 恢复之前的跟踪ID
                activeTraceId = prevTraceId;
            }
        };
    },

    // 设置当前跟踪ID
    setTraceId: (traceId) => {
        activeTraceId = traceId;
        return activeTraceId;
    },
    
    // 获取当前跟踪ID
    getTraceId: () => {
        return activeTraceId;
    },
    
    // 清除当前跟踪ID
    clearTraceId: () => {
        activeTraceId = null;
    },
    
    // 获取当前日志级别
    getLogLevel: () => {
        return CURRENT_LOG_LEVEL;
    },
    
    // 获取最近的日志
    getRecentLogs: async (limit = 100, logType = 'app') => {
        try {
            console.log(`尝试获取${logType}类型的最近${limit}条日志`);
            
            // 确保limit是有效数字
            if (isNaN(parseInt(limit))) {
                console.warn(`无效的limit参数: ${limit}，使用默认值100`);
                limit = 100;
            }
            
            // 验证日志类型
            if (!['app', 'error', 'access'].includes(logType)) {
                console.warn(`无效的日志类型: ${logType}，使用默认值'app'`);
                logType = 'app';
            }
            
            // 存储日志结果的数组
            let resultLogs = [];
            
            // 优先从数据库获取日志
            if (logType === 'app' || logType === 'error') {
                try {
                    // 延迟导入db模块，避免循环依赖
                    const db = require('./db');
                    
                    const tableExists = await ensureLogsTable();
                    if (tableExists) {
                        const query = logType === 'error' 
                            ? `SELECT * FROM system_logs WHERE level = 'ERROR' ORDER BY timestamp DESC LIMIT ?`
                            : `SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT ?`;
                        
                        console.log(`执行SQL查询: ${query}`);
                        const logs = await db.fetchAll(query, [limit]);
                        
                        // 确保logs是数组
                        if (Array.isArray(logs) && logs.length > 0) {
                            resultLogs = logs.map(log => ({
                                timestamp: new Date(log.timestamp).toISOString(),
                                level: log.level,
                                message: log.message
                            }));
                            console.log(`从数据库获取到${resultLogs.length}条日志`);
                            return resultLogs;
                        } else {
                            console.log('数据库查询未返回日志记录或结果不是数组，尝试从文件获取');
                        }
                    }
                } catch (error) {
                    console.error(`从数据库获取日志失败: ${error.message}`);
                }
            }
            
            // 如果从数据库获取失败，尝试从文件获取
            const logFilePath = path.join(logDir, logType === 'error' ? 'error.log' : 'app.log');
            
            if (fs.existsSync(logFilePath)) {
                const fileContent = fs.readFileSync(logFilePath, 'utf8');
                const logLines = fileContent.split('\n').filter(line => line.trim());
                
                // 获取最近的日志行
                const recentLines = logLines.reverse().slice(0, limit);
                
                resultLogs = recentLines.map(line => {
                    // 解析日志行
                    const timestampMatch = line.match(/\[(.*?)\]/);
                    const levelMatch = line.match(/\[(ERROR|WARN|INFO|DEBUG)\]/);
                    
                    return {
                        timestamp: timestampMatch ? timestampMatch[1] : new Date().toISOString(),
                        level: levelMatch ? levelMatch[1] : 'INFO',
                        message: line.replace(/\[.*?\]\s*/g, '').trim()
                    };
                });
                
                console.log(`从文件获取到${resultLogs.length}条日志`);
            }
            
            return resultLogs;
        } catch (error) {
            console.error(`获取日志失败: ${error.message}`);
            return [];
        }
    }
};

module.exports = logger; 