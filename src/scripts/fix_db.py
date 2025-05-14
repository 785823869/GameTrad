import mysql.connector
from mysql.connector import Error

def fix_database():
    try:
        # 连接MySQL
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456",
            database="game_trading"
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 重新创建出库记录表
            cursor.execute("DROP TABLE IF EXISTS stock_out")
            cursor.execute("""
                CREATE TABLE stock_out (
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
            
            connection.commit()
            print("数据库表修复成功！")
            
    except Error as e:
        print(f"错误: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL连接已关闭")

if __name__ == "__main__":
    fix_database() 