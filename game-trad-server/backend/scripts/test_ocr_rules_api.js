/**
 * OCR规则API测试脚本
 * 用于验证OCR规则API是否正常工作以及数据库表是否已创建
 */
const axios = require('axios');
const mysql = require('mysql2/promise');
const path = require('path');
const fs = require('fs-extra');
const os = require('os');

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

// API 基础URL
const API_BASE_URL = 'http://localhost:5000/api';

/**
 * 检查数据库表是否存在
 */
async function checkDatabaseTables() {
  console.log('检查数据库表...');
  
  try {
    // 加载数据库配置
    const dbConfig = loadDbConfig();
    console.log('使用数据库配置:', {
      host: dbConfig.host,
      port: dbConfig.port,
      user: dbConfig.user,
      database: dbConfig.database
    });

    // 创建数据库连接
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
    
    // 检查入库规则表
    const [stockInResult] = await connection.execute(`
      SELECT TABLE_NAME 
      FROM information_schema.TABLES 
      WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'ocr_rules_stock_in'
    `, [dbConfig.database]);
    
    // 检查出库规则表
    const [stockOutResult] = await connection.execute(`
      SELECT TABLE_NAME 
      FROM information_schema.TABLES 
      WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'ocr_rules_stock_out'
    `, [dbConfig.database]);
    
    // 检查监控规则表
    const [monitorResult] = await connection.execute(`
      SELECT TABLE_NAME 
      FROM information_schema.TABLES 
      WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'ocr_rules_monitor'
    `, [dbConfig.database]);
    
    console.log('入库规则表存在:', stockInResult.length > 0);
    console.log('出库规则表存在:', stockOutResult.length > 0);
    console.log('监控规则表存在:', monitorResult.length > 0);
    
    // 如果表不存在，尝试导入setup_ocr_rules.js脚本
    if (stockInResult.length === 0 || stockOutResult.length === 0 || monitorResult.length === 0) {
      console.log('表不完整，请运行setup_ocr_rules.js脚本创建表和预设规则');
    }
    
    // 查询规则数量
    if (stockInResult.length > 0) {
      const [stockInCount] = await connection.execute('SELECT COUNT(*) as count FROM ocr_rules_stock_in');
      console.log('入库规则数量:', stockInCount[0].count);
    }
    
    if (stockOutResult.length > 0) {
      const [stockOutCount] = await connection.execute('SELECT COUNT(*) as count FROM ocr_rules_stock_out');
      console.log('出库规则数量:', stockOutCount[0].count);
    }
    
    if (monitorResult.length > 0) {
      const [monitorCount] = await connection.execute('SELECT COUNT(*) as count FROM ocr_rules_monitor');
      console.log('监控规则数量:', monitorCount[0].count);
    }
    
    // 关闭数据库连接
    await connection.end();
    return stockInResult.length > 0 && stockOutResult.length > 0 && monitorResult.length > 0;
  } catch (error) {
    console.error('检查数据库表失败:', error.message);
    return false;
  }
}

/**
 * 测试OCR规则API
 */
async function testOcrRulesApi() {
  console.log('\n测试OCR规则API...');
  
  // 定义测试规则
  const testRule = {
    name: 'API测试规则',
    description: '用于测试API的规则',
    is_active: true,
    patterns: [
      { field: 'item_name', regex: 'test_item_(.+)', group: 1, default_value: '' },
      { field: 'quantity', regex: 'test_qty_(\\d+)', group: 1, default_value: '0' }
    ]
  };
  
  try {
    // 测试入库规则API
    console.log('\n测试入库规则API:');
    await testRuleApiForType('stock-in', testRule);
    
    // 测试出库规则API
    console.log('\n测试出库规则API:');
    await testRuleApiForType('stock-out', testRule);
    
    // 测试监控规则API
    console.log('\n测试监控规则API:');
    await testRuleApiForType('monitor', testRule);
    
  } catch (error) {
    console.error('API测试失败:', error.message);
  }
}

/**
 * 测试指定类型的规则API
 * @param {string} type - 规则类型(stock-in, stock-out, monitor)
 * @param {object} testRule - 测试规则对象
 */
async function testRuleApiForType(type, testRule) {
  try {
    // 1. 测试获取规则列表
    console.log(`尝试获取${type}规则列表...`);
    const listResponse = await axios.get(`${API_BASE_URL}/ocr-rules/${type}`);
    console.log('获取规则列表状态码:', listResponse.status);
    console.log('规则数量:', listResponse.data.data ? listResponse.data.data.length : 0);
    
    // 2. 测试添加规则
    console.log(`\n尝试添加${type}测试规则...`);
    const addResponse = await axios.post(`${API_BASE_URL}/ocr-rules/${type}`, testRule);
    console.log('添加规则状态码:', addResponse.status);
    
    if (addResponse.data && addResponse.data.success) {
      const ruleId = addResponse.data.data.id;
      console.log(`规则ID: ${ruleId}`);
      
      // 3. 测试获取单个规则
      console.log(`\n尝试获取${type}规则${ruleId}...`);
      const getResponse = await axios.get(`${API_BASE_URL}/ocr-rules/${type}/${ruleId}`);
      console.log('获取单个规则状态码:', getResponse.status);
      
      // 4. 测试更新规则
      console.log(`\n尝试更新${type}规则${ruleId}...`);
      const updatedRule = {
        ...testRule,
        name: 'API测试规则(已更新)',
        description: '测试更新API'
      };
      const updateResponse = await axios.put(`${API_BASE_URL}/ocr-rules/${type}/${ruleId}`, updatedRule);
      console.log('更新规则状态码:', updateResponse.status);
      
      // 5. 测试删除规则
      console.log(`\n尝试删除${type}规则${ruleId}...`);
      const deleteResponse = await axios.delete(`${API_BASE_URL}/ocr-rules/${type}/${ruleId}`);
      console.log('删除规则状态码:', deleteResponse.status);
    }
  } catch (error) {
    console.error(`测试${type}规则API失败:`, error.message);
    if (error.response) {
      console.error('错误状态:', error.response.status);
      console.error('错误数据:', error.response.data);
    }
  }
}

/**
 * 主函数
 */
async function main() {
  try {
    console.log('开始测试OCR规则功能...\n');
    
    // 检查数据库表
    const tablesExist = await checkDatabaseTables();
    
    if (tablesExist) {
      console.log('\n数据库表检查通过! 继续API测试...');
      await testOcrRulesApi();
    } else {
      console.log('\n数据库表检查失败! 请确认表是否正确创建。');
      console.log('您可以尝试手动运行setup_ocr_rules.js脚本创建表。');
    }
    
    console.log('\n测试完成!');
  } catch (error) {
    console.error('测试过程中出错:', error);
  }
}

// 执行主函数
main(); 