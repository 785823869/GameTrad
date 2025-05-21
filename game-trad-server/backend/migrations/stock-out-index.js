/**
 * 库存出库表迁移脚本 - 添加唯一索引防止重复记录
 * 
 * 该脚本执行两个主要操作：
 * 1. 清理已存在的重复数据，保留最新添加的记录
 * 2. 添加唯一索引，防止未来出现重复数据
 * 
 * 运行方式: node migrations/stock-out-index.js
 */

const mysql = require('mysql2/promise');
const path = require('path');
const fs = require('fs');
const os = require('os');

// 从db.js复制加载数据库配置的函数，避免依赖问题
const loadDbConfig = () => {
  try {
    // 默认数据库配置
    const defaultConfig = {
      host: "sql.didiba.uk",
      port: 33306,
      user: "root",
      password: "Cenb1017!@",
      database: "OcrTrade",
      charset: "utf8mb4",
      connectTimeout: 10000
    };

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
        console.error(`加载数据库配置失败: ${e.message}`);
        // 如果加载失败，使用默认配置
        return defaultConfig;
      }
    } else {
      // 如果配置文件不存在，创建默认配置文件
      try {
        fs.writeFileSync(configFile, JSON.stringify(defaultConfig, null, 2));
      } catch (e) {
        console.error(`创建默认数据库配置文件失败: ${e.message}`);
      }
      return defaultConfig;
    }
  } catch (e) {
    console.error(`数据库配置处理失败: ${e.message}`);
    return defaultConfig;
  }
};

// 日志格式化
const log = {
  info: (msg) => console.log(`[INFO] ${msg}`),
  warn: (msg) => console.warn(`[WARN] ${msg}`),
  error: (msg) => console.error(`[ERROR] ${msg}`),
  success: (msg) => console.log(`[SUCCESS] ${msg}`)
};

async function findDuplicateRecords(connection) {
  log.info('开始查找重复记录...');
  
  // 查找重复记录：同一物品、同一数量、同一单价、同一交易日期（精确到分钟）
  const [duplicates] = await connection.query(`
    SELECT 
      item_name, 
      quantity, 
      unit_price, 
      DATE_FORMAT(transaction_time, '%Y-%m-%d %H:%i') as trx_time,
      COUNT(*) as count,
      GROUP_CONCAT(id ORDER BY id DESC) as ids
    FROM 
      stock_out
    GROUP BY 
      item_name, 
      quantity, 
      unit_price,
      DATE_FORMAT(transaction_time, '%Y-%m-%d %H:%i')
    HAVING 
      COUNT(*) > 1
  `);
  
  return duplicates;
}

async function reportDuplicateRecords(connection, duplicates) {
  if (duplicates.length === 0) {
    log.info('没有发现重复记录');
    return 0;
  }
  
  log.warn(`发现 ${duplicates.length} 组重复记录，但不会删除它们：`);
  
  // 只报告重复记录，不删除
  for (const dup of duplicates) {
    const ids = dup.ids.split(',');
    log.warn(`组 "${dup.item_name} (${dup.quantity}x${dup.unit_price})" 有 ${ids.length} 条重复记录，ID: ${dup.ids}`);
  }
  
  return duplicates.length;
}

async function addUniqueIndex(connection) {
  log.info('开始添加唯一索引...');
  
  try {
    // 检查索引是否已存在
    const [indexes] = await connection.query(`
      SHOW INDEX FROM stock_out WHERE Key_name = 'uk_stock_out_item_qty_price_time';
    `);
    
    if (indexes.length > 0) {
      log.warn('唯一索引已经存在，跳过创建');
      return false;
    }
    
    // 添加唯一索引
    await connection.query(`
      ALTER TABLE stock_out 
      ADD CONSTRAINT uk_stock_out_item_qty_price_time 
      UNIQUE (item_name, quantity, unit_price, transaction_time);
    `);
    
    log.success('唯一索引创建成功');
    return true;
  } catch (error) {
    if (error.code === 'ER_DUP_ENTRY') {
      log.error('创建唯一索引失败：存在重复数据！如需添加索引，请先移除重复数据');
      return false;
    }
    throw error;
  }
}

async function runMigration() {
  let connection;
  
  try {
    log.info('开始数据库迁移 - 库存出库表添加唯一索引(不删除重复数据)');
    
    // 加载数据库配置
    const dbConfig = loadDbConfig();
    
    // 创建数据库连接
    connection = await mysql.createConnection({
      host: dbConfig.host,
      port: dbConfig.port,
      user: dbConfig.user,
      password: dbConfig.password,
      database: dbConfig.database,
      charset: dbConfig.charset || 'utf8mb4',
      connectTimeout: dbConfig.connectTimeout || 10000
    });
    
    // 开始事务
    await connection.beginTransaction();
    
    // 1. 查找并报告重复记录，但不删除
    const duplicates = await findDuplicateRecords(connection);
    const dupCount = await reportDuplicateRecords(connection, duplicates);
    
    if (dupCount > 0) {
      log.warn('存在重复数据！添加唯一索引可能会失败，请手动处理重复数据后再添加索引');
      log.warn('你可以运行原始版本的脚本来清理重复数据');
    }
    
    // 2. 添加唯一索引
    const indexCreated = await addUniqueIndex(connection);
    
    // 提交事务
    await connection.commit();
    
    if (indexCreated) {
      log.success('唯一索引创建成功，将防止未来出现重复记录');
    } else if (dupCount > 0) {
      log.error('由于存在重复数据，无法添加唯一索引。请先处理重复数据');
    }
    
    log.success('迁移完成！');
    
  } catch (error) {
    if (connection) {
      await connection.rollback();
    }
    log.error(`迁移失败: ${error.message}`);
    console.error(error);
  } finally {
    if (connection) {
      await connection.end();
    }
  }
}

// 执行迁移
runMigration(); 