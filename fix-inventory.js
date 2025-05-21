const mysql = require('mysql2/promise');

async function main() {
  let conn = null;
  try {
    // 连接数据库
    conn = await mysql.createConnection({
      host: "sql.didiba.uk",
      port: 33306,
      user: "root",
      password: "Cenb1017!@",
      database: "OcrTrade",
      charset: "utf8mb4"
    });
    console.log("数据库连接成功");
    
    // 查询灵之精火的库存
    const [rows] = await conn.query(`SELECT * FROM inventory WHERE item_name = ?`, ["灵之精火"]);
    
    if (rows.length === 0) {
      console.log("物品\"灵之精火\"不存在于库存中，准备添加...");
      
      // 插入灵之精火到库存表
      const insertQuery = `
        INSERT INTO inventory (
          item_name, quantity, avg_price, avg_cost, inventory_value, 
          last_transaction_time, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
      `;
      
      const now = new Date().toISOString();
      const params = [
        "灵之精火",    // 物品名称
        100,           // 数量
        500,           // 平均价格
        450,           // 平均成本
        45000,         // 库存价值
        now,           // 最后交易时间
        "系统自动添加" // 备注
      ];
      
      const [result] = await conn.query(insertQuery, params);
      console.log(`成功添加灵之精火到库存，影响行数: ${result.affectedRows}`);
    } else {
      console.log("灵之精火库存情况:", rows[0]);
      
      // 检查库存是否为零
      if (rows[0].quantity <= 0) {
        console.log("灵之精火库存不足，准备更新库存...");
        
        // 更新库存为100
        const updateQuery = `UPDATE inventory SET quantity = ? WHERE item_name = ?`;
        const [updateResult] = await conn.query(updateQuery, [100, "灵之精火"]);
        
        console.log(`成功更新灵之精火库存，影响行数: ${updateResult.affectedRows}`);
      } else {
        console.log("灵之精火库存充足，无需更新");
      }
    }
  } catch (err) {
    console.error("执行出错:", err.message);
  } finally {
    if (conn) {
      await conn.end();
      console.log("数据库连接已关闭");
    }
  }
}

main(); 