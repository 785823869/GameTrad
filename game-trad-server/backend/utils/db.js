// 数据库管理模块
const mysql = require('mysql2/promise');
const path = require('path');
const fs = require('fs-extra');
const os = require('os');
// 移除顶级导入，避免循环依赖
// const logger = require('./logger');

// 定义简单的日志函数用于db模块内部使用
const dbLogger = {
  error: (message) => {
    console.error(`DB ERROR: ${message}`);
    try {
      // 尝试将日志写入文件，但不要使用logger模块
      const logDir = process.env.LOG_DIR || './logs';
      
      // 确保日志目录存在
      fs.ensureDirSync(logDir);
      
      // 创建日志文件
      const timestamp = new Date().toISOString();
      const logEntry = `[${timestamp}] [ERROR] [DB] ${message}\n`;
      const logFile = path.join(logDir, 'db_errors.log');
      
      // 直接使用fs，不依赖其他模块
      fs.appendFileSync(logFile, logEntry);
    } catch (e) {
      // 如果写入文件失败，只记录控制台
      console.error(`DB ERROR: 无法写入日志文件: ${e.message}`);
    }
  },
  
  warn: (message) => {
    console.warn(`DB WARN: ${message}`);
    // 警告级别不写入文件，避免IO开销
  },
  
  info: (message) => {
    if (process.env.DB_DEBUG === 'true') {
      console.info(`DB INFO: ${message}`);
    }
  },
  
  debug: (message) => {
    if (process.env.DB_DEBUG === 'true') {
      console.debug(`DB DEBUG: ${message}`);
    }
  }
};

// 默认数据库配置(与Python版本保持一致)
const defaultConfig = {
    host: "sql.didiba.uk",
    port: 33306,
    user: "root",
    password: "Cenb1017!@",
    database: "OcrTrade",
    charset: "utf8mb4",
    connectTimeout: 10000
};

// 从配置文件加载数据库连接参数
const loadDbConfig = () => {
    try {
        // 创建配置目录
        const configDir = path.join(os.homedir(), ".gametrad");
        if (!fs.existsSync(configDir)) {
            fs.mkdirSync(configDir, { recursive: true });
        }

        // 配置文件路径
        const configFile = path.join(configDir, "db_config.json");

        // 如果配置文件存在，则加载配置
        if (fs.existsSync(configFile)) {
            try {
                const config = JSON.parse(fs.readFileSync(configFile, 'utf-8'));
                // 确保所有必要的配置项都存在
                for (const key in defaultConfig) {
                    if (!(key in config)) {
                        config[key] = defaultConfig[key];
                    }
                }
                // 确保端口和超时时间是整数
                try {
                    config.port = parseInt(config.port);
                } catch (e) {
                    config.port = defaultConfig.port;
                }

                try {
                    config.connectTimeout = parseInt(config.connectTimeout);
                } catch (e) {
                    config.connectTimeout = defaultConfig.connectTimeout;
                }
                return config;
            } catch (e) {
                dbLogger.error(`加载数据库配置失败: ${e.message}`);
                // 如果加载失败，使用默认配置
                return defaultConfig;
            }
        } else {
            // 如果配置文件不存在，创建默认配置文件
            try {
                fs.writeFileSync(configFile, JSON.stringify(defaultConfig, null, 2));
            } catch (e) {
                dbLogger.error(`创建默认数据库配置文件失败: ${e.message}`);
            }
            return defaultConfig;
        }
    } catch (e) {
        dbLogger.error(`数据库配置处理失败: ${e.message}`);
        return defaultConfig;
    }
};

// 保存数据库连接参数到配置文件
const saveDbConfig = (config) => {
    try {
        // 创建配置目录
        const configDir = path.join(os.homedir(), ".gametrad");
        if (!fs.existsSync(configDir)) {
            fs.mkdirSync(configDir, { recursive: true });
        }

        // 配置文件路径
        const configFile = path.join(configDir, "db_config.json");

        // 确保端口和超时时间是整数
        try {
            config.port = parseInt(config.port);
        } catch (e) {
            config.port = 33306; // 默认端口
        }

        try {
            config.connectTimeout = parseInt(config.connectTimeout);
        } catch (e) {
            config.connectTimeout = 10000; // 默认超时时间 (毫秒)
        }

        // 保存配置
        fs.writeFileSync(configFile, JSON.stringify(config, null, 2));
        return true;
    } catch (e) {
        dbLogger.error(`保存数据库配置失败: ${e.message}`);
        return false;
    }
};

// 加载配置
const dbConfig = loadDbConfig();

// 创建连接池
const pool = mysql.createPool({
    host: dbConfig.host,
    port: dbConfig.port,
    user: dbConfig.user,
    password: dbConfig.password,
    database: dbConfig.database,
    charset: dbConfig.charset,
    connectionLimit: 10,
    connectTimeout: dbConfig.connectTimeout,
    waitForConnections: true,
    timezone: '+08:00' // 添加时区设置为东八区(北京时间)
});

// 测试数据库连接
const testConnection = async (config) => {
    try {
        const conn = await mysql.createConnection({
            host: config.host,
            port: config.port,
            user: config.user,
            password: config.password,
            database: config.database,
            charset: config.charset,
            connectTimeout: config.connectTimeout,
            timezone: '+08:00' // 添加时区设置为东八区(北京时间)
        });

        const [rows] = await conn.query('SELECT VERSION()');
        await conn.end();
        return { success: true, message: `连接成功！MySQL版本: ${rows[0]['VERSION()']}` };
    } catch (e) {
        return { success: false, message: `连接失败: ${e.message}` };
    }
};

// 执行查询并返回所有结果
const fetchAll = async (query, params = []) => {
    try {
        const [rows] = await pool.query(query, params);
        return rows;
    } catch (e) {
        dbLogger.error(`查询执行失败: ${e.message}`);
        dbLogger.error(`SQL: ${query}`);
        return [];
    }
};

// 执行查询并返回单个结果
const fetchOne = async (query, params = []) => {
    try {
        const [rows] = await pool.query(query, params);
        return rows[0];
    } catch (e) {
        dbLogger.error(`查询执行失败: ${e.message}`);
        dbLogger.error(`SQL: ${query}`);
        return null;
    }
};

// 执行SQL语句（增删改）
const execute = async (query, params = []) => {
    try {
        // 记录SQL执行信息（但不记录完整参数以防敏感信息泄露）
        dbLogger.debug(`执行SQL: ${query.replace(/\s+/g, ' ').trim()}`);
        dbLogger.debug(`参数数量: ${params.length}`);
        
        // 执行SQL
        const [result] = await pool.query(query, params);
        
        // 记录执行结果
        if (result) {
            if (result.affectedRows !== undefined) {
                dbLogger.debug(`SQL执行成功: 影响 ${result.affectedRows} 行`);
                if (result.insertId) {
                    dbLogger.debug(`插入ID: ${result.insertId}`);
                }
            }
            return result;
        } else {
            dbLogger.warn(`SQL执行未返回结果: ${query.substring(0, 100)}`);
        return false;
        }
    } catch (error) {
        // 处理特定的SQL错误
        if (error.code === 'ER_NO_REFERENCED_ROW_2') {
            dbLogger.error('外键约束错误: 引用的记录不存在');
        } else if (error.code === 'ER_DUP_ENTRY') {
            dbLogger.error('重复键错误: 记录已存在');
        }
        throw error; // 继续抛出错误以便上层处理
    }
};

// 获取库存统计数据
const getInventoryStats = async () => {
    try {
        // 获取基本库存统计
        const statsQuery = "SELECT COUNT(*) as itemCount, SUM(quantity) as totalQuantity, SUM(inventory_value) as totalValue FROM inventory WHERE quantity > 0";
        const stats = await fetchOne(statsQuery);
        
        // 获取低库存物品数量（库存小于30的物品）
        const lowStockQuery = "SELECT COUNT(*) as lowStockCount FROM inventory WHERE quantity > 0 AND quantity < 30";
        const lowStock = await fetchOne(lowStockQuery);
        
        // 获取零库存或负库存物品数量
        const zeroStockQuery = "SELECT COUNT(*) as zeroStockCount FROM inventory WHERE quantity <= 0";
        const zeroStock = await fetchOne(zeroStockQuery);
        
        return {
            itemCount: stats?.itemCount || 0,
            totalQuantity: stats?.totalQuantity || 0, 
            totalValue: stats?.totalValue || 0,
            lowStockCount: lowStock?.lowStockCount || 0,
            zeroStockCount: zeroStock?.zeroStockCount || 0
        };
    } catch (e) {
        dbLogger.error(`获取库存统计失败: ${e.message}`);
        return {
            itemCount: 0,
            totalQuantity: 0,
            totalValue: 0,
            lowStockCount: 0,
            zeroStockCount: 0
        };
    }
};

// 获取零库存或负库存的物品
const getZeroInventoryItems = async () => {
    const query = "SELECT id, item_name, quantity FROM inventory WHERE quantity <= 0 ORDER BY quantity ASC";
    return await fetchAll(query);
};

// 获取最近交易
const getRecentTransactions = async (limit = 5) => {
    const query = "SELECT * FROM stock_out ORDER BY transaction_time DESC LIMIT ?";
    return await fetchAll(query, [limit]);
};

// 记录操作日志
const logOperation = async (tabName, opType, data = null, reverted = false) => {
    try {
        const query = "INSERT INTO operation_logs (operation_type, tab_name, operation_data, reverted) VALUES (?, ?, ?, ?)";
        const params = [
            opType, 
            tabName, 
            data ? JSON.stringify(data) : null, 
            reverted ? 1 : 0
        ];
        
        const [result] = await pool.query(query, params);
        return result.insertId;
    } catch (e) {
        dbLogger.error(`记录操作日志失败: ${e.message}`);
        return null;
    }
};

// 获取所有库存数据
const getAllInventory = async () => {
    const query = `
        SELECT 
            id,
            item_name,
            quantity,
            avg_price,
            break_even_price,
            selling_price,
            profit,
            profit_rate,
            total_profit,
            inventory_value
        FROM 
            inventory
        ORDER BY 
            item_name ASC
    `;
    return await fetchAll(query);
};

// 重新计算库存数据
const recalculateInventory = async () => {
    try {
        // 这里模拟Python客户端的重新计算功能
        // 实际应用中，应该根据交易记录重新计算库存数据
        
        // 1. 更新保本均价
        await execute(`
            UPDATE inventory 
            SET break_even_price = avg_price * 1.05
            WHERE break_even_price IS NULL OR break_even_price = 0
        `);
        
        // 2. 更新利润和利润率
        await execute(`
            UPDATE inventory 
            SET 
                profit = selling_price - break_even_price,
                profit_rate = CASE 
                    WHEN break_even_price > 0 
                    THEN ((selling_price - break_even_price) / break_even_price) * 100
                    ELSE 0 
                END
            WHERE 
                selling_price > 0 AND break_even_price > 0
        `);
        
        // 3. 更新库存价值
        await execute(`
            UPDATE inventory 
            SET inventory_value = quantity * avg_price
            WHERE quantity > 0
        `);
        
        // 4. 更新成交利润
        await execute(`
            UPDATE inventory 
            SET total_profit = profit * quantity
            WHERE profit IS NOT NULL AND quantity > 0
        `);
        
        // 记录操作日志
        await logOperation(
            'inventory',
            'recalculate',
            {
                action: 'full_recalculation',
                fields_updated: ['break_even_price', 'profit', 'profit_rate', 'inventory_value', 'total_profit']
            }
        );
        
        return true;
    } catch (e) {
        dbLogger.error(`重新计算库存数据失败: ${e.message}`);
        return false;
    }
};

// 检查库存项目是否存在
const checkInventoryItemExists = async (id) => {
    const query = "SELECT COUNT(*) as count FROM inventory WHERE id = ?";
    const result = await fetchOne(query, [id]);
    return result && result.count > 0;
};

// 删除库存项目
const deleteInventoryItem = async (id) => {
    try {
        // 先获取要删除的记录以便记录日志
        const record = await fetchOne(
            "SELECT * FROM inventory WHERE id = ?",
            [id]
        );
        
    const query = "DELETE FROM inventory WHERE id = ?";
        const result = await execute(query, [id]);
        
        // 记录操作日志
        if (result && result.affectedRows > 0) {
            await logOperation(
                'inventory',
                'delete',
                record || { id }
            );
        }
        
        return result;
    } catch (error) {
        dbLogger.error(`删除库存项目失败: ${error.message}`);
        return false;
    }
};

// 获取入库记录
const get_stock_in = async () => {
    const query = "SELECT * FROM stock_in ORDER BY transaction_time DESC";
    return await fetchAll(query);
};

// 删除入库记录
const delete_stock_in = async (item_name, transaction_time) => {
    try {
        // 先获取要删除的记录以便记录日志
        const record = await fetchOne(
            "SELECT * FROM stock_in WHERE item_name=? AND transaction_time=?",
            [item_name, transaction_time]
        );
        
    const query = "DELETE FROM stock_in WHERE item_name=? AND transaction_time=?";
        const result = await execute(query, [item_name, transaction_time]);
        
        // 记录操作日志
        if (result && result.affectedRows > 0) {
            await logOperation(
                'stock_in',
                'delete',
                record || { item_name, transaction_time }
            );
        }
        
        return result;
    } catch (error) {
        dbLogger.error(`删除入库记录失败: ${error.message}`);
        return false;
    }
};

// 保存入库记录
const save_stock_in = async (stock_in_data) => {
    try {
        // 数据验证
        if (!stock_in_data.item_name || 
            !stock_in_data.transaction_time || 
            !stock_in_data.quantity || 
            !stock_in_data.cost || 
            !stock_in_data.avg_cost) {
            return false;
        }

        const query = `
            INSERT INTO stock_in (
                item_name, transaction_time, quantity,
                cost, avg_cost, note
            ) VALUES (?, ?, ?, ?, ?, ?)
        `;
        
        const params = [
            stock_in_data.item_name,
            stock_in_data.transaction_time,
            stock_in_data.quantity,
            stock_in_data.cost,
            stock_in_data.avg_cost,
            stock_in_data.note || ''
        ];
        
        const result = await execute(query, params);
        
        // 记录操作日志
        if (result) {
            await logOperation(
                'stock_in',
                'insert',
                {
                    item_name: stock_in_data.item_name,
                    quantity: stock_in_data.quantity,
                    cost: stock_in_data.cost,
                    avg_cost: stock_in_data.avg_cost,
                    transaction_time: stock_in_data.transaction_time
                }
            );
        }
        
        return result;
    } catch (error) {
        dbLogger.error(`保存入库记录失败: ${error.message}`);
        return false;
    }
};

// 获取出库记录
const get_stock_out = async () => {
    const query = "SELECT * FROM stock_out ORDER BY transaction_time DESC";
    return await fetchAll(query);
};

// 删除出库记录
const delete_stock_out = async (id) => {
    try {
        // 先获取要删除的记录以便记录日志
        const record = await fetchOne(
            "SELECT * FROM stock_out WHERE id = ?",
            [id]
        );
        
    const query = "DELETE FROM stock_out WHERE id = ?";
        const result = await execute(query, [id]);
        
        // 记录操作日志
        if (result && result.affectedRows > 0) {
            await logOperation(
                'stock_out',
                'delete',
                record || { id }
            );
        }
        
        return result;
    } catch (error) {
        dbLogger.error(`删除出库记录失败: ${error.message}`);
        return false;
    }
};

// 保存出库记录
const save_stock_out = async (stock_out_data) => {
    // 获取数据库连接用于事务
    let conn = null;
    try {
        // 开始记录更详细的操作日志
        dbLogger.info(`save_stock_out - 开始保存出库记录: ${JSON.stringify(stock_out_data)}`);
        
        // 数据验证详细检查
        const validationErrors = [];
        
        // 检查物品名称
        if (!stock_out_data.item_name) {
            validationErrors.push('缺少物品名称');
        } else if (typeof stock_out_data.item_name !== 'string') {
            validationErrors.push(`物品名称类型错误: ${typeof stock_out_data.item_name}`);
        }
        
        // 检查交易时间
        if (!stock_out_data.transaction_time) {
            validationErrors.push('缺少交易时间');
            // 自动添加当前时间作为交易时间
            const now = new Date();
            stock_out_data.transaction_time = now.toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');
            dbLogger.info(`使用默认日期格式: ${stock_out_data.transaction_time}`);
        } else {
            // 确保交易时间格式符合MySQL要求
            if (stock_out_data.transaction_time.includes('T')) {
                stock_out_data.transaction_time = stock_out_data.transaction_time.replace('T', ' ').replace(/\.\d+Z$/, '');
                dbLogger.info(`已转换日期格式: ${stock_out_data.transaction_time}`);
            }
        }
        
        // 检查数量并转换为数字
        try {
            if (stock_out_data.quantity === undefined || stock_out_data.quantity === null) {
                validationErrors.push('缺少数量');
            } else {
                const quantity = parseFloat(stock_out_data.quantity);
                if (isNaN(quantity)) {
                    validationErrors.push(`数量不是有效数字: ${stock_out_data.quantity}`);
                } else if (quantity <= 0) {
                    validationErrors.push(`数量必须大于0: ${quantity}`);
                } else {
                    // 确保保存为数字类型
                    stock_out_data.quantity = quantity;
                }
            }
        } catch (e) {
            validationErrors.push(`数量解析错误: ${e.message}`);
        }
        
        // 检查单价并转换为数字
        try {
            if (stock_out_data.unit_price === undefined || stock_out_data.unit_price === null) {
                validationErrors.push('缺少单价');
            } else {
                const unitPrice = parseFloat(stock_out_data.unit_price);
                if (isNaN(unitPrice)) {
                    validationErrors.push(`单价不是有效数字: ${stock_out_data.unit_price}`);
                } else if (unitPrice < 0) {
                    validationErrors.push(`单价不能为负: ${unitPrice}`);
                } else {
                    // 确保保存为数字类型
                    stock_out_data.unit_price = unitPrice;
                }
            }
        } catch (e) {
            validationErrors.push(`单价解析错误: ${e.message}`);
        }
        
        // 检查手续费并转换为数字
        try {
            if (stock_out_data.fee === undefined || stock_out_data.fee === null) {
                stock_out_data.fee = 0;
                dbLogger.info('自动将手续费设为0');
            } else {
                const fee = parseFloat(stock_out_data.fee);
                if (isNaN(fee)) {
                    validationErrors.push(`手续费不是有效数字: ${stock_out_data.fee}`);
                } else if (fee < 0) {
                    validationErrors.push(`手续费不能为负: ${fee}`);
                } else {
                    // 确保保存为数字类型
                    stock_out_data.fee = fee;
                }
            }
        } catch (e) {
            validationErrors.push(`手续费解析错误: ${e.message}`);
        }
        
        // 检查总金额并转换为数字
        try {
            // 如果总金额未提供，计算总金额 = 数量 * 单价 - 手续费
            if (stock_out_data.total_amount === undefined || stock_out_data.total_amount === null) {
                if (!validationErrors.includes('缺少数量') && !validationErrors.includes('缺少单价')) {
                    stock_out_data.total_amount = stock_out_data.quantity * stock_out_data.unit_price - stock_out_data.fee;
                    dbLogger.info(`自动计算总金额: ${stock_out_data.total_amount}`);
                }
            } else {
                const totalAmount = parseFloat(stock_out_data.total_amount);
                if (isNaN(totalAmount)) {
                    validationErrors.push(`总金额不是有效数字: ${stock_out_data.total_amount}`);
                } else {
                    // 确保保存为数字类型
                    stock_out_data.total_amount = totalAmount;
                }
            }
        } catch (e) {
            validationErrors.push(`总金额解析错误: ${e.message}`);
        }

        if (validationErrors.length > 0) {
            dbLogger.error(`保存出库记录验证失败: ${validationErrors.join(', ')}`);
            dbLogger.error(`无效的出库记录数据: ${JSON.stringify(stock_out_data)}`);
            return false;
        }

        // 检查物品是否存在于库存中
        const checkItemQuery = "SELECT id, item_name, quantity FROM inventory WHERE item_name = ?";
        const itemInInventory = await fetchOne(checkItemQuery, [stock_out_data.item_name]);
        
        // 如果物品不在库存中，自动创建该物品的库存记录
        if (!itemInInventory) {
            dbLogger.info(`物品不存在于库存中，将自动创建: ${stock_out_data.item_name}`);
            
            // 创建新物品库存记录的SQL
            const createItemQuery = `
                INSERT INTO inventory (
                    item_name, quantity, avg_price, break_even_price, 
                    selling_price, profit, profit_rate, total_profit, inventory_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;
            
            // 初始化库存为0，其他值也为0
            await execute(createItemQuery, [
                stock_out_data.item_name, 0, 0, 0, 0, 0, 0, 0, 0
            ]);
            
            dbLogger.info(`已创建物品库存记录: ${stock_out_data.item_name}`);
            
            // 记录创建库存项的操作日志
            await logOperation(
                'inventory',
                'create',
                {
                    item_name: stock_out_data.item_name,
                    quantity: 0,
                    created_from: 'stock_out'
                }
            );
        }
        
        // 不再检查库存充足性，允许库存为负数
        // Python版本也没有进行此检查

        // 确保交易时间格式符合MySQL要求
        if (stock_out_data.transaction_time && typeof stock_out_data.transaction_time === 'string') {
            // 检查是否是ISO格式并转换
            if (stock_out_data.transaction_time.includes('T')) {
                stock_out_data.transaction_time = stock_out_data.transaction_time.replace('T', ' ').replace(/\.\d+Z$/, '');
                dbLogger.info(`转换日期格式为MySQL格式: ${stock_out_data.transaction_time}`);
            }
        } else {
            // 如果没有提供时间或格式不正确，使用当前时间
            const now = new Date();
            stock_out_data.transaction_time = now.toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');
            dbLogger.info(`使用当前日期(MySQL格式): ${stock_out_data.transaction_time}`);
        }

        // 记录数据保存前的状态
        dbLogger.info(`准备保存出库记录: 物品=${stock_out_data.item_name}, ` +
                   `数量=${stock_out_data.quantity}, 单价=${stock_out_data.unit_price}`);

        // 获取连接用于事务
        conn = await pool.getConnection();
        
        // 开始事务
        await conn.beginTransaction();
        dbLogger.info(`开始数据库事务`);

        // 1. 插入出库记录
        const insertQuery = `
            INSERT INTO stock_out (
                item_name, transaction_time, quantity,
                unit_price, fee, total_amount, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `;
        
        const params = [
            stock_out_data.item_name,
            stock_out_data.transaction_time,
            stock_out_data.quantity,
            stock_out_data.unit_price,
            stock_out_data.fee || 0,
            stock_out_data.total_amount || 0,
            stock_out_data.note || ''
        ];
        
        // 执行SQL并记录结果
        dbLogger.info(`执行SQL插入: ${insertQuery.replace(/\s+/g, ' ').trim()}`);
        dbLogger.info(`参数: ${JSON.stringify(params)}`);
        
        const [insertResult] = await conn.query(insertQuery, params);
        dbLogger.info(`出库记录插入结果: ${JSON.stringify(insertResult)}`);
        
        // 2. 更新库存
        const updateQuery = "UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?";
        const [updateResult] = await conn.query(updateQuery, [stock_out_data.quantity, stock_out_data.item_name]);
        dbLogger.info(`库存更新结果: ${JSON.stringify(updateResult)}`);
        
        // 如果两个操作都成功，提交事务
        await conn.commit();
        dbLogger.info(`事务提交成功，出库记录ID=${insertResult.insertId}`);
        
        // 记录操作日志
        await logOperation(
            'stock_out',
            'insert',
            {
                id: insertResult.insertId,
                item_name: stock_out_data.item_name,
                quantity: stock_out_data.quantity,
                unit_price: stock_out_data.unit_price,
                fee: stock_out_data.fee,
                total_amount: stock_out_data.total_amount,
                transaction_time: stock_out_data.transaction_time
            }
        );
        
        return insertResult;
    } catch (error) {
        // 如果发生错误，回滚事务
        if (conn) {
            try {
                await conn.rollback();
                dbLogger.info('事务已回滚');
            } catch (rollbackError) {
                dbLogger.error(`事务回滚失败: ${rollbackError.message}`);
            }
        }
        
        // 处理特定的数据库错误
        if (error.code) {
            switch (error.code) {
                case 'ER_NO_REFERENCED_ROW_2':
                    dbLogger.error('外键约束错误: 引用的物品不存在');
                    break;
                case 'ER_DUP_ENTRY':
                    dbLogger.error('重复键错误: 记录已存在');
                    break;
                case 'ER_BAD_NULL_ERROR':
                    dbLogger.error('NULL值错误: 必填字段为空');
                    break;
                case 'ER_DATA_TOO_LONG':
                    dbLogger.error('数据过长错误: 超出字段长度限制');
                    break;
                default:
                    dbLogger.error(`数据库错误: ${error.code} - ${error.sqlMessage || error.message}`);
            }
        }
        
        dbLogger.error(`错误详情: ${error.stack || '无堆栈信息'}`);
        dbLogger.error(`出库数据: ${JSON.stringify(stock_out_data)}`);
        return false;
    } finally {
        // 释放连接
        if (conn) {
            try {
                conn.release();
                dbLogger.info('数据库连接已释放');
            } catch (releaseError) {
                dbLogger.error(`释放连接失败: ${releaseError.message}`);
            }
        }
    }
};

// 减少库存数量
const decrease_inventory = async (item_name, quantity) => {
    const dbLogger = require('./logger');
    
    // 参数验证
    if (!item_name) {
        dbLogger.error('减少库存失败: 物品名称为空');
        return false;
    }
    
    if (!quantity || isNaN(Number(quantity)) || Number(quantity) <= 0) {
        dbLogger.error(`减少库存失败: 无效的数量 "${quantity}"`);
        return false;
    }
    
    // 确保数量是数字
    const numericQuantity = Number(quantity);
    
    let conn = null;
    try {
        conn = await pool.getConnection();
        
        // 查询物品是否存在于库存中，并获取当前库存信息
        const checkQuery = "SELECT id, item_name, quantity, avg_price FROM inventory WHERE item_name = ?";
        const [rows] = await conn.query(checkQuery, [item_name]);
        
        if (!rows || rows.length === 0) {
            dbLogger.warn(`物品 "${item_name}" 不存在于库存中`);
            
            // 尝试在库存中创建物品记录
            try {
                dbLogger.info(`尝试创建物品 "${item_name}" 的库存记录`);
                
                const insertQuery = `
                    INSERT INTO inventory (
                        item_name, quantity, avg_price, break_even_price, 
                        selling_price, profit, profit_rate, total_profit, inventory_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                `;
                
                const [insertResult] = await conn.query(insertQuery, [
                    item_name,
                    -numericQuantity, // 初始库存设为负数，表示欠库存
                    0, // 初始均价
                    0, // 保本价
                    0, // 售价
                    0, // 利润
                    0, // 利润率
                    0, // 总利润
                    0  // 库存价值
                ]);
                
                if (insertResult && insertResult.affectedRows > 0) {
                    dbLogger.info(`成功创建物品 "${item_name}" 的库存记录，初始库存为-${numericQuantity}`);
                    
                    // 记录创建物品操作日志
                    await logOperation(
                        'inventory',
                        'create',
                        {
                            item_name: item_name,
                            initial_quantity: -numericQuantity,
                            created_from: 'decrease_inventory'
                        }
                    );
                    
                    return true;
                } else {
                    dbLogger.error(`创建物品 "${item_name}" 的库存记录失败`);
                    return false;
                }
            } catch (insertError) {
                dbLogger.error(`创建物品库存记录失败: ${insertError.message}`);
            return false;
            }
        }
        
        const currentInventory = rows[0];
        dbLogger.info(`物品 "${item_name}" 当前库存: ${currentInventory.quantity}, 出库数量: ${numericQuantity}`);
        
        // 更新库存数量
        const updateQuery = "UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?";
        const [updateResult] = await conn.query(updateQuery, [numericQuantity, item_name]);
        
        if (updateResult && updateResult.affectedRows > 0) {
            const newQuantity = currentInventory.quantity - numericQuantity;
            
            // 检查是否导致库存为负
            if (newQuantity < 0) {
                dbLogger.warn(`物品 "${item_name}" 库存变为负数: ${newQuantity}`);
            }
            
            dbLogger.info(`成功减少物品 "${item_name}" 库存: ${currentInventory.quantity} -> ${newQuantity}`);
            
            // 记录操作日志
            await logOperation(
                'inventory',
                'decrease',
                {
                    item_name: item_name,
                    original_quantity: currentInventory.quantity,
                    decrease_amount: numericQuantity,
                    new_quantity: newQuantity
                }
            );
            
            return true;
        } else {
            dbLogger.error(`更新物品 "${item_name}" 库存失败，未影响任何行`);
            return false;
        }
    } catch (error) {
        dbLogger.error(`减少库存失败: ${error.message}`);
        dbLogger.error(`错误详情: ${error.stack || '无堆栈信息'}`);
        return false;
    } finally {
        // 释放连接
        if (conn) {
            try {
                conn.release();
            } catch (releaseError) {
                dbLogger.error(`释放数据库连接失败: ${releaseError.message}`);
            }
        }
    }
};

// 获取交易记录
const get_transactions = async (type = null, limit = 100, offset = 0) => {
    try {
        let query;
        let params = [];
        
        if (type) {
            query = "SELECT * FROM transactions WHERE transaction_type = ? ORDER BY transaction_time DESC LIMIT ? OFFSET ?";
            params = [type, limit, offset];
        } else {
            query = "SELECT * FROM transactions ORDER BY transaction_time DESC LIMIT ? OFFSET ?";
            params = [limit, offset];
        }
        
        return await fetchAll(query, params);
    } catch (error) {
        dbLogger.error(`获取交易记录失败: ${error.message}`);
        return [];
    }
};

// 获取交易记录统计
const get_transaction_stats = async () => {
    try {
        // 获取交易类型统计
        const typeStatsQuery = "SELECT transaction_type, COUNT(*) as count FROM transactions GROUP BY transaction_type";
        const typeStats = await fetchAll(typeStatsQuery);
        
        // 获取最近7天交易数量
        const recentStatsQuery = `
            SELECT DATE(transaction_time) as date, COUNT(*) as count 
            FROM transactions 
            WHERE transaction_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(transaction_time)
            ORDER BY date
        `;
        const recentStats = await fetchAll(recentStatsQuery);
        
        // 获取交易总金额
        const totalAmountQuery = "SELECT SUM(total_amount) as total FROM transactions";
        const totalAmount = await fetchOne(totalAmountQuery);
        
        return {
            typeStats,
            recentStats,
            totalAmount: totalAmount?.total || 0
        };
    } catch (error) {
        dbLogger.error(`获取交易统计失败: ${error.message}`);
        return {
            typeStats: [],
            recentStats: [],
            totalAmount: 0
        };
    }
};

// 保存交易记录
const save_transaction = async (transactionData) => {
    try {
        // 数据验证
        if (!transactionData.transaction_type || 
            !transactionData.item_name || 
            !transactionData.transaction_time || 
            transactionData.quantity === undefined || 
            transactionData.price === undefined) {
            dbLogger.error(`保存交易记录验证失败: 缺少必要字段`);
            return false;
        }
        
        // 将ISO格式的时间转换为MySQL格式
        let transaction_time = transactionData.transaction_time;
        if (typeof transaction_time === 'string' && transaction_time.includes('T')) {
            transaction_time = transaction_time.replace('T', ' ').replace(/\.\d+Z$/, '');
        }
        
        const query = `
            INSERT INTO transactions (
                transaction_type, transaction_time, item_name,
                quantity, price, total_amount, fee, platform, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `;
        
        const params = [
            transactionData.transaction_type,
            transaction_time,
            transactionData.item_name,
            transactionData.quantity,
            transactionData.price,
            transactionData.total_amount || (transactionData.quantity * transactionData.price - (transactionData.fee || 0)),
            transactionData.fee || 0,
            transactionData.platform || '',
            transactionData.note || ''
        ];
        
        const result = await execute(query, params);
        
        // 记录操作日志
        if (result) {
            await logOperation(
                'transactions',
                'insert',
                {
                    transaction_type: transactionData.transaction_type,
                    item_name: transactionData.item_name,
                    quantity: transactionData.quantity,
                    price: transactionData.price,
                    transaction_time: transaction_time
                }
            );
        }
        
        return result;
    } catch (error) {
        dbLogger.error(`保存交易记录失败: ${error.message}`);
        return false;
    }
};

// 删除交易记录
const delete_transaction = async (id) => {
    try {
        // 先获取要删除的记录以便记录日志
        const record = await fetchOne(
            "SELECT * FROM transactions WHERE id = ?",
            [id]
        );
        
        const query = "DELETE FROM transactions WHERE id = ?";
        const result = await execute(query, [id]);
        
        // 记录操作日志
        if (result && result.affectedRows > 0) {
            await logOperation(
                'transactions',
                'delete',
                record || { id }
            );
        }
        
        return result;
    } catch (error) {
        dbLogger.error(`删除交易记录失败: ${error.message}`);
        return false;
    }
};

// 更新交易记录
const update_transaction = async (id, transactionData) => {
    try {
        // 数据验证
        if (!id || !transactionData) {
            return false;
        }
        
        // 先获取原始记录以便记录日志
        const originalRecord = await fetchOne(
            "SELECT * FROM transactions WHERE id = ?",
            [id]
        );
        
        const query = `
            UPDATE transactions SET
                transaction_type = ?,
                item_name = ?,
                quantity = ?,
                price = ?,
                total_amount = ?,
                fee = ?,
                platform = ?,
                note = ?
            WHERE id = ?
        `;
        
        const params = [
            transactionData.transaction_type,
            transactionData.item_name,
            transactionData.quantity,
            transactionData.price,
            transactionData.total_amount,
            transactionData.fee || 0,
            transactionData.platform || '',
            transactionData.note || '',
            id
        ];
        
        const result = await execute(query, params);
        
        // 记录操作日志
        if (result && result.affectedRows > 0) {
            await logOperation(
                'transactions',
                'update',
                {
                    id: id,
                    original: originalRecord,
                    updated: transactionData
                }
            );
        }
        
        return result;
    } catch (error) {
        dbLogger.error(`更新交易记录失败: ${error.message}`);
        return false;
    }
};

// 获取数据库连接
const getConnection = async () => {
    try {
        return await pool.getConnection();
    } catch (e) {
        dbLogger.error(`获取数据库连接失败: ${e.message}`);
        throw e; // 重新抛出错误，让调用者处理
    }
};

// 导出模块
module.exports = {
    pool,
    dbConfig,
    testConnection,
    saveDbConfig,
    fetchAll,
    fetchOne,
    execute,
    getInventoryStats,
    getZeroInventoryItems,
    getRecentTransactions,
    logOperation,
    getAllInventory,
    recalculateInventory,
    checkInventoryItemExists,
    deleteInventoryItem,
    get_stock_in,
    delete_stock_in,
    save_stock_in,
    get_stock_out,
    delete_stock_out,
    save_stock_out,
    decrease_inventory,
    get_transactions,
    get_transaction_stats,
    save_transaction,
    delete_transaction,
    update_transaction,
    getConnection
}; 