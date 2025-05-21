/**
 * 数据库迁移脚本 - 为stock_out表添加profit和profit_rate列
 * 解决"Unknown column 'profit' in 'field list'"错误
 */

const db = require('../utils/db');
const logger = require('../utils/logger');

async function migrate() {
  try {
    logger.info('开始执行数据库迁移: 添加profit和profit_rate列...');

    // 检查profit列是否已存在
    const checkColumnQuery = `
      SELECT COUNT(*) as count 
      FROM information_schema.COLUMNS 
      WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'stock_out' AND COLUMN_NAME = 'profit'
    `;
    const result = await db.fetchOne(checkColumnQuery, [db.dbConfig.database]);

    if (result && result.count > 0) {
      logger.info('profit列已存在，跳过迁移');
      return true;
    }

    // 添加profit列
    const addProfitColumnQuery = `
      ALTER TABLE stock_out
      ADD COLUMN profit DECIMAL(10, 2) DEFAULT 0.00 AFTER total_amount,
      ADD COLUMN profit_rate DECIMAL(10, 2) DEFAULT 0.00 AFTER profit
    `;
    
    await db.execute(addProfitColumnQuery);
    
    // 更新已有数据的profit和profit_rate值
    logger.info('正在更新已有数据的profit值...');
    
    // 获取所有出库记录
    const stockOutRecords = await db.fetchAll('SELECT * FROM stock_out');
    
    // 逐条记录更新profit
    let updatedCount = 0;
    for (const record of stockOutRecords) {
      // 获取对应的库存平均价格
      const inventoryQuery = "SELECT avg_price FROM inventory WHERE item_name = ?";
      const inventoryData = await db.fetchOne(inventoryQuery, [record.item_name]);
      
      if (inventoryData && inventoryData.avg_price) {
        const avgCost = Number(inventoryData.avg_price);
        const quantity = record.quantity;
        const totalRevenue = record.total_amount;
        
        // 计算利润 = 总收入 - (平均成本 × 数量)
        const profit = totalRevenue - (avgCost * quantity);
        
        // 计算利润率 = 利润 / 成本总额 * 100%
        const totalCost = avgCost * quantity;
        const profitRate = totalCost > 0 ? (profit / totalCost) * 100 : 0;
        
        // 更新记录
        const updateQuery = `
          UPDATE stock_out 
          SET profit = ?, profit_rate = ? 
          WHERE id = ?
        `;
        
        await db.execute(updateQuery, [profit, profitRate, record.id]);
        updatedCount++;
      }
    }
    
    logger.info(`迁移完成: 添加了profit和profit_rate列，并更新了${updatedCount}条记录`);
    return true;
  } catch (error) {
    logger.error(`迁移失败: ${error.message}`);
    return false;
  }
}

// 执行迁移
migrate().then(success => {
  if (success) {
    console.log('✓ 迁移成功: 添加了profit和profit_rate列');
    process.exit(0);
  } else {
    console.error('✗ 迁移失败');
    process.exit(1);
  }
}); 