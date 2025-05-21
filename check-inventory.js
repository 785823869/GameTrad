const mysql = require("mysql2/promise");

async function main() {
  let conn = null;
  try {
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
      console.log("物品\"灵之精火\"不存在于库存中");
    } else {
      console.log("灵之精火库存情况:", rows[0]);
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