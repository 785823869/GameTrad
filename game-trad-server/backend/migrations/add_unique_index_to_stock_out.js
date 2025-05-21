/**
 * 添加唯一索引到stock_out表，防止重复记录
 */

const mysql = require('mysql2/promise');
const config = require('../utils/db').loadDbConfig();

async function executeMigration() {
  console.log('开始执行迁移: 添加唯一索引到stock_out表');
  
  let connection;
  try {
    // 创建数据库连接
    connection = await mysql.createConnection({
      host: config.host,
      port: config.port,
      user: config.user,
      password: config.password,
      database: config.database
    });
    
    console.log('数据库连接成功');
    
    // 1. 首先清理可能的重复数据
    console.log('开始清理重复数据...');
    await cleanupDuplicateRecords(connection);
    
    // 2. 添加唯一索引
    console.log('添加唯一索引...');
    const createIndexQuery = `
      CREATE UNIQUE INDEX idx_stock_out_dedup 
      ON stock_out (
        item_name, 
        quantity, 
        unit_price, 
        DATE(transaction_time),
        HOUR(transaction_time),
        MINUTE(transaction_time)
      );
    `;
    
    await connection.execute(createIndexQuery);
    console.log('唯一索引添加成功');
    
    console.log('迁移完成');
  } catch (error) {
    console.error('迁移失败:', error.message);
    if (error.code === 'ER_DUP_KEYNAME') {
      console.log('索引已存在，无需创建');
    }
  } finally {
    if (connection) {
      await connection.end();
      console.log('数据库连接已关闭');
    }
  }
}

/**
 * 清理重复数据，只保留每组重复记录中的一条
 */
async function cleanupDuplicateRecords(connection) {
  try {
    // 1. 找出重复记录
    const findDuplicatesQuery = `
      SELECT item_name, quantity, unit_price, 
             DATE(transaction_time) as date,
             HOUR(transaction_time) as hour,
             MINUTE(transaction_time) as minute,
             COUNT(*) as count
      FROM stock_out
      GROUP BY item_name, quantity, unit_price, 
               DATE(transaction_time),
               HOUR(transaction_time),
               MINUTE(transaction_time)
      HAVING COUNT(*) > 1;
    `;
    
    const [duplicateGroups] = await connection.execute(findDuplicatesQuery);
    console.log(`发现 ${duplicateGroups.length} 组重复记录`);
    
    // 2. 对每组重复记录，除了保留最高手续费的记录外，删除其他记录
    for (const group of duplicateGroups) {
      const { item_name, quantity, unit_price, date, hour, minute } = group;
      
      // 找出该组中所有记录
      const findGroupRecordsQuery = `
        SELECT id, fee
        FROM stock_out
        WHERE item_name = ?
        AND quantity = ?
        AND unit_price = ?
        AND DATE(transaction_time) = ?
        AND HOUR(transaction_time) = ?
        AND MINUTE(transaction_time) = ?
        ORDER BY fee DESC;
      `;
      
      const [records] = await connection.execute(findGroupRecordsQuery, [
        item_name, quantity, unit_price, date, hour, minute
      ]);
      
      // 保留第一条记录(最高手续费)，删除其余记录
      if (records.length > 1) {
        const keepId = records[0].id;
        const deleteIds = records.slice(1).map(r => r.id);
        
        console.log(`组 ${item_name}/${quantity}/${unit_price}/${date} ${hour}:${minute} - 保留ID ${keepId}, 删除 ${deleteIds.length} 条记录`);
        
        // 删除多余记录
        if (deleteIds.length > 0) {
          const deleteQuery = `
            DELETE FROM stock_out
            WHERE id IN (?);
          `;
          
          await connection.execute(deleteQuery, [deleteIds]);
          console.log(`删除了 ${deleteIds.length} 条重复记录`);
        }
      }
    }
    
    console.log('重复数据清理完成');
  } catch (error) {
    console.error('清理重复数据失败:', error.message);
    throw error;
  }
}

// 执行迁移
executeMigration()
  .then(() => {
    console.log('迁移脚本执行完毕');
    process.exit(0);
  })
  .catch(err => {
    console.error('迁移脚本执行失败:', err);
    process.exit(1);
  }); 