// 数据库管理模块
const mysql = require('mysql2/promise');
const path = require('path');
const fs = require('fs-extra');
const os = require('os');
const logger = require('./logger');

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
                logger.error(`加载数据库配置失败: ${e.message}`);
                // 如果加载失败，使用默认配置
                return defaultConfig;
            }
        } else {
            // 如果配置文件不存在，创建默认配置文件
            try {
                fs.writeFileSync(configFile, JSON.stringify(defaultConfig, null, 2));
            } catch (e) {
                logger.error(`创建默认数据库配置文件失败: ${e.message}`);
            }
            return defaultConfig;
        }
    } catch (e) {
        logger.error(`数据库配置处理失败: ${e.message}`);
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
        logger.error(`保存数据库配置失败: ${e.message}`);
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
    waitForConnections: true
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
            connectTimeout: config.connectTimeout
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
        logger.error(`查询执行失败: ${e.message}`);
        logger.error(`SQL: ${query}`);
        return [];
    }
};

// 执行查询并返回单个结果
const fetchOne = async (query, params = []) => {
    try {
        const [rows] = await pool.query(query, params);
        return rows.length > 0 ? rows[0] : null;
    } catch (e) {
        logger.error(`查询执行失败: ${e.message}`);
        logger.error(`SQL: ${query}`);
        return null;
    }
};

// 执行更新/插入/删除操作
const execute = async (query, params = []) => {
    try {
        const [result] = await pool.query(query, params);
        return true;
    } catch (e) {
        logger.error(`执行失败: ${e.message}`);
        logger.error(`SQL: ${query}`);
        return false;
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
        logger.error(`获取库存统计失败: ${e.message}`);
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
        logger.error(`记录操作日志失败: ${e.message}`);
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
        
        return true;
    } catch (e) {
        logger.error(`重新计算库存数据失败: ${e.message}`);
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
    const query = "DELETE FROM inventory WHERE id = ?";
    return await execute(query, [id]);
};

// 获取入库记录
const get_stock_in = async () => {
    const query = "SELECT * FROM stock_in ORDER BY transaction_time DESC";
    return await fetchAll(query);
};

// 删除入库记录
const delete_stock_in = async (item_name, transaction_time) => {
    const query = "DELETE FROM stock_in WHERE item_name=? AND transaction_time=?";
    return await execute(query, [item_name, transaction_time]);
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
        
        return await execute(query, params);
    } catch (error) {
        logger.error(`保存入库记录失败: ${error.message}`);
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
    const query = "DELETE FROM stock_out WHERE id = ?";
    return await execute(query, [id]);
};

// 保存出库记录
const save_stock_out = async (stock_out_data) => {
    try {
        // 数据验证
        if (!stock_out_data.item_name || 
            !stock_out_data.transaction_time || 
            !stock_out_data.quantity || 
            !stock_out_data.unit_price) {
            return false;
        }

        const query = `
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
        
        return await execute(query, params);
    } catch (error) {
        logger.error(`保存出库记录失败: ${error.message}`);
        return false;
    }
};

// 减少库存数量
const decrease_inventory = async (item_name, quantity) => {
    try {
        // 查询物品是否存在于库存中
        const checkQuery = "SELECT id, quantity FROM inventory WHERE item_name = ?";
        const item = await fetchOne(checkQuery, [item_name]);
        
        if (!item) {
            logger.warn(`物品 ${item_name} 不存在于库存中`);
            return false;
        }
        
        // 更新库存数量
        const updateQuery = "UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?";
        return await execute(updateQuery, [quantity, item_name]);
    } catch (error) {
        logger.error(`减少库存失败: ${error.message}`);
        return false;
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
    decrease_inventory
}; 