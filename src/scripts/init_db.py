import mysql.connector
from mysql.connector import Error

def create_database():
    try:
        # 连接MySQL
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456"
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS game_trading")
            cursor.execute("USE game_trading")
            
            # 创建库存表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_name VARCHAR(100) NOT NULL,
                    quantity INT NOT NULL DEFAULT 0,
                    avg_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    break_even_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    selling_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    profit DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    profit_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                    total_profit DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    inventory_value DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # 创建入库记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_in (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_name VARCHAR(100) NOT NULL,
                    transaction_time DATETIME NOT NULL,
                    quantity INT NOT NULL,
                    cost DECIMAL(10,2) NOT NULL,
                    avg_cost DECIMAL(10,2) NOT NULL,
                    deposit DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建出库记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_out (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_name VARCHAR(100) NOT NULL,
                    transaction_time DATETIME NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(10,2) NOT NULL,
                    fee DECIMAL(10,2) NOT NULL,
                    deposit DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    total_amount DECIMAL(10,2) NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建交易监控表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_monitor (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_name VARCHAR(100) NOT NULL,
                    monitor_time DATETIME NOT NULL,
                    quantity INT NOT NULL,
                    market_price DECIMAL(10,2) NOT NULL,
                    target_price DECIMAL(10,2) NOT NULL,
                    planned_price DECIMAL(10,2) NOT NULL,
                    break_even_price DECIMAL(10,2) NOT NULL,
                    profit DECIMAL(10,2) NOT NULL,
                    profit_rate DECIMAL(5,2) NOT NULL,
                    strategy TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建银两监控表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS silver_monitor (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    server VARCHAR(32),
                    series VARCHAR(16),
                    price DECIMAL(10,4),
                    ma_price DECIMAL(10,4),
                    timestamp DATETIME,
                    UNIQUE KEY uniq_silver (server, series, timestamp)
                )
            """)
            
            connection.commit()
            print("数据库和表创建成功！")
            
    except Error as e:
        print(f"错误: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL连接已关闭")

if __name__ == "__main__":
    create_database() 