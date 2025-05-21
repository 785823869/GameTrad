/**
 * OCR规则初始化脚本
 * 用于设置预定义的OCR识别规则
 */
const mysql = require('mysql2/promise');
const path = require('path');
const fs = require('fs-extra');
const os = require('os');
const logger = require('../utils/logger');

// 默认数据库配置(与db.js保持一致)
const defaultConfig = {
  host: "sql.didiba.uk",
  port: 33306,
  user: "root",
  password: "Cenb1017!@",
  database: "OcrTrade",
  charset: "utf8mb4",
  connectTimeout: 10000,
  timezone: '+08:00'  // 添加时区设置为东八区(北京时间)
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

// 创建数据库连接
async function createConnection() {
  try {
    // 从配置文件加载数据库配置
    const dbConfig = loadDbConfig();

    console.log('使用数据库配置:', {
      host: dbConfig.host,
      port: dbConfig.port,
      user: dbConfig.user,
      database: dbConfig.database
    });

    const connection = await mysql.createConnection({
      host: dbConfig.host,
      port: dbConfig.port,
      user: dbConfig.user,
      password: dbConfig.password,
      database: dbConfig.database,
      charset: dbConfig.charset,
      connectTimeout: dbConfig.connectTimeout,
      timezone: dbConfig.timezone
    });
    
    return connection;
  } catch (error) {
    console.error('创建数据库连接失败:', error.message);
    throw error;
  }
}

/**
 * 确保OCR规则表存在
 */
async function ensureTablesExist(connection) {
  try {
    // 检查并创建入库规则表
    await connection.execute(`
      CREATE TABLE IF NOT EXISTS ocr_rules_stock_in (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        patterns JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      )
    `);

    // 检查并创建出库规则表
    await connection.execute(`
      CREATE TABLE IF NOT EXISTS ocr_rules_stock_out (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        patterns JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      )
    `);

    // 检查并创建监控规则表
    await connection.execute(`
      CREATE TABLE IF NOT EXISTS ocr_rules_monitor (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        patterns JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      )
    `);

    logger.info('OCR规则表创建成功');
    console.log('OCR规则表创建成功');
  } catch (error) {
    logger.error('创建OCR规则表失败:', error);
    console.error('创建OCR规则表失败:', error.message);
    throw error;
  }
}

/**
 * 插入预定义的OCR规则
 */
async function insertPredefinedRules(connection) {
  try {
    // 清空现有规则
    await connection.execute('TRUNCATE TABLE ocr_rules_stock_in');
    await connection.execute('TRUNCATE TABLE ocr_rules_stock_out');
    await connection.execute('TRUNCATE TABLE ocr_rules_monitor');

    // 插入入库规则
    await insertStockInRules(connection);
    
    // 插入出库规则
    await insertStockOutRules(connection);

    logger.info('预定义OCR规则添加完成');
    console.log('预定义OCR规则添加完成');
  } catch (error) {
    logger.error('添加预定义OCR规则失败:', error);
    console.error('添加预定义OCR规则失败:', error.message);
    throw error;
  }
}

/**
 * 插入入库规则
 */
async function insertStockInRules(connection) {
  // 入库规则1：通用格式（基于品名、数量、价格）
  const stockInRule1 = {
    name: '通用入库识别规则',
    description: '识别包含品名/物品、数量、价格/金额/花费等信息的文本',
    is_active: true,
    patterns: [
      { field: 'item_name', regex: '[品名|物品|道具]+[^：:]*[：:]*\\s*(.+)$', group: 1, default_value: '' },
      { field: 'quantity', regex: '[数量|个数|件数]+[^：:]*[：:]*\\s*(\\d+)', group: 1, default_value: '0' },
      { field: 'unit_price', regex: '[价格|金额|花费]+[^：:]*[：:]*\\s*(\\d+)', group: 1, default_value: '0' }
    ]
  };

  // 入库规则2：精确格式（基于"获得了物品×数量"和"花费了银两×金额"）
  const stockInRule2 = {
    name: '精确入库识别规则',
    description: '识别"获得了[物品]×[数量]"和"失去了银两×[金额]"格式的文本',
    is_active: true,
    patterns: [
      { field: 'item_name', regex: '获得了(.+?)×', group: 1, default_value: '' },
      { field: 'quantity', regex: '×(\\d+)', group: 1, default_value: '0' },
      { field: 'unit_price', regex: '失去了银两×(\\d+)', group: 1, default_value: '0' }
    ]
  };

  // 入库规则3：游戏特定格式 - 至纯精华（针对多个银两消费和至纯精华获取的场景）
  const stockInRule3 = {
    name: '游戏特定入库识别规则',
    description: '识别游戏中多个"失去了银两×金额"和"至纯精华×数量"的特定格式',
    is_active: true,
    patterns: [
      // 固定物品名称为"至纯精华"
      { field: 'item_name', regex: '.+', group: 0, default_value: '至纯精华' },
      
      // 匹配物品数量模式 - 优化正则表达式以匹配所有出现的模式
      { field: 'quantity_1', regex: '至纯精华\\s*×\\s*(\\d+)', group: 1, default_value: '0' },
      { field: 'quantity_2', regex: '获得了\\s*至纯精华\\s*×\\s*(\\d+)', group: 1, default_value: '0' },
      { field: 'quantity_3', regex: '至纯精华\\s*(\\d+)', group: 1, default_value: '0' },
      { field: 'quantity_4', regex: '获得了\\s*至纯精华\\s*(\\d+)', group: 1, default_value: '0' },
      
      // 匹配花费银两模式 - 优化正则表达式以匹配所有出现的模式
      { field: 'cost_1', regex: '失去了\\s*银两\\s*×\\s*(\\d+)', group: 1, default_value: '0' },
      { field: 'cost_2', regex: '银两\\s*×\\s*(\\d+)', group: 1, default_value: '0' },
      { field: 'cost_3', regex: '失去了\\s*(\\d+)\\s*银两', group: 1, default_value: '0' },
      { field: 'cost_4', regex: '花费\\s*(\\d+)\\s*银两', group: 1, default_value: '0' },
      { field: 'cost_5', regex: '花费了\\s*(\\d+)\\s*银两', group: 1, default_value: '0' }
    ]
  };

  // 插入入库规则
  await connection.execute(
    'INSERT INTO ocr_rules_stock_in (name, description, is_active, patterns) VALUES (?, ?, ?, ?)',
    [stockInRule1.name, stockInRule1.description, stockInRule1.is_active, JSON.stringify(stockInRule1.patterns)]
  );
  
  await connection.execute(
    'INSERT INTO ocr_rules_stock_in (name, description, is_active, patterns) VALUES (?, ?, ?, ?)',
    [stockInRule2.name, stockInRule2.description, stockInRule2.is_active, JSON.stringify(stockInRule2.patterns)]
  );
  
  // 插入游戏特定格式规则
  await connection.execute(
    'INSERT INTO ocr_rules_stock_in (name, description, is_active, patterns) VALUES (?, ?, ?, ?)',
    [stockInRule3.name, stockInRule3.description, stockInRule3.is_active, JSON.stringify(stockInRule3.patterns)]
  );
  
  logger.info('入库规则添加完成');
  console.log('入库规则添加完成');
}

/**
 * 插入出库规则
 */
async function insertStockOutRules(connection) {
  // 出库规则1：通用格式（基于品名、数量、单价、手续费）
  const stockOutRule1 = {
    name: '通用出库识别规则',
    description: '识别包含品名/物品名称、数量/个数、单价/价格、手续费等信息的文本',
    is_active: true,
    patterns: [
      { field: 'item_name', regex: '[品名|物品名称|道具]+[^：:]*[：:]*\\s*(.+)$', group: 1, default_value: '' },
      { field: 'quantity', regex: '[数量|个数|件数]+[^：:]*[：:]*\\s*(\\d+)', group: 1, default_value: '0' },
      { field: 'unit_price', regex: '[单价|价格]+[^：:]*[：:]*\\s*(\\d+)', group: 1, default_value: '0' },
      { field: 'fee', regex: '[手续费|费用]+[^：:]*[：:]*\\s*(\\d+)', group: 1, default_value: '0' }
    ]
  };

  // 出库规则2：V2格式（已成功售出物品(数量)。售出单价：银两 手续费：银两）
  const stockOutRule2 = {
    name: '售出确认识别规则',
    description: '识别"已成功售出[物品]（[数量]）。售出单价：[金额]银两 手续费：[金额]银两"格式的文本',
    is_active: true,
    patterns: [
      { field: 'item_name', regex: '已成功售出([^（(]+)[（(]', group: 1, default_value: '' },
      { field: 'quantity', regex: '[（(](\\d+)[）)]', group: 1, default_value: '0' },
      { field: 'unit_price', regex: '售出单价[：:]\\s*(\\d+)银两', group: 1, default_value: '0' },
      { field: 'fee', regex: '手续费[：:]\\s*(\\d+)银两', group: 1, default_value: '0' }
    ]
  };

  // 出库规则3：V3格式（已成功售出[数量][物品名]，请在附件中领取...）
  const stockOutRule3 = {
    name: '售出通知识别规则',
    description: '识别"已成功售出[数量][物品名]，请在附件中领取..."格式的文本',
    is_active: true,
    patterns: [
      { field: 'quantity', regex: '已成功售出(\\d+)', group: 1, default_value: '0' },
      { field: 'item_name', regex: '已成功售出\\d+([^，,。]+)[，,。]', group: 1, default_value: '' },
      { field: 'total_amount', regex: '(\\d+)\\s*$', group: 1, default_value: '0' }
    ]
  };

  // 插入出库规则
  await connection.execute(
    'INSERT INTO ocr_rules_stock_out (name, description, is_active, patterns) VALUES (?, ?, ?, ?)',
    [stockOutRule1.name, stockOutRule1.description, stockOutRule1.is_active, JSON.stringify(stockOutRule1.patterns)]
  );
  
  await connection.execute(
    'INSERT INTO ocr_rules_stock_out (name, description, is_active, patterns) VALUES (?, ?, ?, ?)',
    [stockOutRule2.name, stockOutRule2.description, stockOutRule2.is_active, JSON.stringify(stockOutRule2.patterns)]
  );
  
  await connection.execute(
    'INSERT INTO ocr_rules_stock_out (name, description, is_active, patterns) VALUES (?, ?, ?, ?)',
    [stockOutRule3.name, stockOutRule3.description, stockOutRule3.is_active, JSON.stringify(stockOutRule3.patterns)]
  );
  
  logger.info('出库规则添加完成');
  console.log('出库规则添加完成');
}

/**
 * 主函数
 */
async function main() {
  let connection;
  try {
    console.log('开始设置OCR规则...');
    connection = await createConnection();
    
    await ensureTablesExist(connection);
    await insertPredefinedRules(connection);
    
    console.log('OCR规则设置完成！');
    process.exit(0);
  } catch (error) {
    console.error('设置OCR规则失败:', error);
    process.exit(1);
  } finally {
    if (connection) {
      await connection.end();
    }
  }
}

// 执行主函数
main(); 