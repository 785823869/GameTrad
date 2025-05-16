#!/usr/bin/env python
# 清空所有数据脚本

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.core.db_manager import DatabaseManager

def clear_all_data():
    """清空所有交易和库存数据"""
    print("开始清空所有数据...")
    db = DatabaseManager()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # 清空库存表和交易记录表
        tables = ['inventory', 'stock_in', 'stock_out']
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            print(f"已清空{table}表")
        
        conn.commit()
        print("所有数据已清空!")
        return True
    except Exception as e:
        conn.rollback()
        print(f"清空数据失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    print("===== 清空所有数据工具 =====")
    print("此工具将清空所有库存和交易记录")
    print("警告: 此操作不可恢复!")
    print()
    
    # 请求用户确认
    confirm = input("是否继续清空所有数据? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 再次确认
    confirm_again = input("此操作将删除所有数据且不可恢复，再次确认? (yes/no): ")
    if confirm_again.lower() != 'yes':
        print("操作已取消")
        return
    
    # 执行清空
    if clear_all_data():
        print("数据清空完成! 请重启应用程序。")
    else:
        print("清空数据失败!")

if __name__ == "__main__":
    main() 