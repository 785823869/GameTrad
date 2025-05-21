const mysql = require('mysql2/promise');

// 创建数据库连接
const createConnection = async () => {
    try {
        const connection = await mysql.createConnection({
            host: "sql.didiba.uk",
            port: 33306,
            user: "root",
            password: "Cenb1017!@",
            database: "OcrTrade",
            charset: "utf8mb4"
        });
        console.log("数据库连接成功");
        return connection;
    } catch (err) {
        console.error("数据库连接失败:", err.message);
        throw err;
    }
};

// 查询表结构
const showTableStructure = async (conn, tableName) => {
    try {
        const [rows] = await conn.query(`DESCRIBE ${tableName}`);
        console.log(`\n===== ${tableName} 表结构 =====`);
        console.log(rows);
        return rows;
    } catch (err) {
        console.error(`获取表 ${tableName} 结构失败:`, err.message);
        return null;
    }
};

// 尝试插入测试数据
const insertTestRecord = async (conn) => {
    try {
        const testData = {
            item_name: "测试物品",
            transaction_time: new Date().toISOString(),
            quantity: 10,
            unit_price: 100,
            fee: 50,
            total_amount: 950,
            note: "测试数据"
        };

        console.log("\n===== 尝试插入测试数据 =====");
        console.log(testData);

        const query = `
            INSERT INTO stock_out (
                item_name, transaction_time, quantity,
                unit_price, fee, total_amount, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `;
        
        const params = [
            testData.item_name,
            testData.transaction_time,
            testData.quantity,
            testData.unit_price,
            testData.fee,
            testData.total_amount,
            testData.note
        ];

        const [result] = await conn.query(query, params);
        console.log("插入成功，影响行数:", result.affectedRows);
        console.log("插入ID:", result.insertId);
        return true;
    } catch (err) {
        console.error("插入测试数据失败:", err.message);
        if (err.sqlState) {
            console.error("SQL状态码:", err.sqlState);
            console.error("SQL错误码:", err.errno);
            console.error("SQL消息:", err.sqlMessage);
        }
        return false;
    }
};

// 查询最近的记录
const getRecentRecords = async (conn, tableName, limit = 5) => {
    try {
        const [rows] = await conn.query(`SELECT * FROM ${tableName} ORDER BY id DESC LIMIT ?`, [limit]);
        console.log(`\n===== ${tableName} 最近 ${limit} 条记录 =====`);
        console.log(rows);
        return rows;
    } catch (err) {
        console.error(`获取 ${tableName} 记录失败:`, err.message);
        return null;
    }
};

// 主函数
(async () => {
    let conn = null;
    try {
        conn = await createConnection();
        await showTableStructure(conn, 'stock_out');
        await insertTestRecord(conn);
        await getRecentRecords(conn, 'stock_out');
    } catch (err) {
        console.error("执行出错:", err.message);
    } finally {
        if (conn) {
            await conn.end();
            console.log("\n数据库连接已关闭");
        }
    }
})(); 