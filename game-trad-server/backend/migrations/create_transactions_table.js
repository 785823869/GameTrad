// Migration for creating transactions table
const mysql = require('mysql2/promise');
const path = require('path');
const fs = require('fs-extra');
const os = require('os');

// Load database config (copied from db.js)
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
                return config;
            } catch (e) {
                console.error(`加载数据库配置失败: ${e.message}`);
                return {
                    host: "sql.didiba.uk",
                    port: 33306,
                    user: "root",
                    password: "Cenb1017!@",
                    database: "OcrTrade",
                    charset: "utf8mb4",
                    connectTimeout: 10000
                };
            }
        } else {
            return {
                host: "sql.didiba.uk",
                port: 33306,
                user: "root",
                password: "Cenb1017!@",
                database: "OcrTrade",
                charset: "utf8mb4",
                connectTimeout: 10000
            };
        }
    } catch (e) {
        console.error(`数据库配置处理失败: ${e.message}`);
        return {
            host: "sql.didiba.uk",
            port: 33306,
            user: "root",
            password: "Cenb1017!@",
            database: "OcrTrade",
            charset: "utf8mb4",
            connectTimeout: 10000
        };
    }
};

// 创建transactions表
async function createTransactionsTable() {
    console.log('开始创建 transactions 表...');
    
    const dbConfig = loadDbConfig();
    
    try {
        // 创建数据库连接
        const connection = await mysql.createConnection({
            host: dbConfig.host,
            port: dbConfig.port,
            user: dbConfig.user,
            password: dbConfig.password,
            database: dbConfig.database,
            charset: dbConfig.charset,
            connectTimeout: dbConfig.connectTimeout
        });

        // 基于 API 使用和已有表结构，创建 transactions 表
        const createTableSQL = `
            CREATE TABLE IF NOT EXISTS transactions (
                id int NOT NULL AUTO_INCREMENT,
                transaction_type VARCHAR(50) NOT NULL,
                transaction_time DATETIME NOT NULL,
                item_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                fee DECIMAL(10,2) DEFAULT 0,
                platform VARCHAR(50) DEFAULT '',
                note TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                target_price DECIMAL(10,2) DEFAULT 0,
                planned_price DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        `;

        console.log('执行SQL:', createTableSQL);
        await connection.execute(createTableSQL);
        console.log('transactions 表创建成功!');

        // 添加索引
        const createIndexSQL = `
            CREATE INDEX idx_transaction_type ON transactions (transaction_type);
            CREATE INDEX idx_transaction_time ON transactions (transaction_time);
            CREATE INDEX idx_item_name ON transactions (item_name);
        `;
        
        console.log('添加索引:', createIndexSQL);
        await connection.execute(createIndexSQL);
        console.log('索引添加成功!');

        await connection.end();
        console.log('数据库连接已关闭');

        return true;
    } catch (error) {
        console.error('创建 transactions 表失败:', error);
        return false;
    }
}

// 执行迁移
createTransactionsTable()
    .then(result => {
        if (result) {
            console.log('迁移完成: transactions 表创建成功');
            process.exit(0);
        } else {
            console.error('迁移失败');
            process.exit(1);
        }
    })
    .catch(err => {
        console.error('迁移过程中发生错误:', err);
        process.exit(1);
    }); 