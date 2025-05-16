#!/usr/bin/env python
# 库存交易记录修复脚本 - 从库存数据反向生成入库和出库记录

import os
import sys
from datetime import datetime, timedelta
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.core.db_manager import DatabaseManager

def fix_inventory_and_transactions():
    """全面修复库存与交易记录"""
    print("开始全面修复库存和交易记录...")
    db = DatabaseManager()
    
    # 获取所有库存数据
    inventory_data = db.get_inventory()
    print(f"获取到 {len(inventory_data)} 条库存记录")
    
    if not inventory_data:
        print("没有找到库存数据，无法生成交易记录")
        return False
    
    # 检查入库和出库表是否为空
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM stock_in")
        stock_in_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stock_out")
        stock_out_count = cursor.fetchone()[0]
        
        if stock_in_count > 0 or stock_out_count > 0:
            answer = input("入库或出库表中已有数据，是否清空现有数据后继续？(y/n): ")
            if answer.lower() != 'y':
                print("操作已取消")
                return False
            
            # 清空入库和出库表
            cursor.execute("DELETE FROM stock_in")
            cursor.execute("DELETE FROM stock_out")
            conn.commit()
            print("已清空现有交易记录")
    finally:
        cursor.close()
        conn.close()
    
    # 为每条库存记录生成合适的入库和出库记录
    stock_in_count = 0
    stock_out_count = 0
    
    for item in inventory_data:
        try:
            # 解包库存记录数据
            item_id, item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value, *_ = item
            
            # 生成基础时间（30天前）
            base_time = datetime.now() - timedelta(days=30)
            
            # 1. 正库存：创建足够的入库记录
            if quantity > 0:
                # 计算入库总成本
                total_cost = float(avg_price) * float(quantity)
                
                # 生成入库时间（20-30天前）
                days_ago = random.randint(20, 30)
                transaction_time = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                # 添加入库记录
                db.save_stock_in({
                    'item_name': item_name,
                    'transaction_time': transaction_time,
                    'quantity': int(quantity),
                    'cost': int(total_cost),
                    'avg_cost': int(float(avg_price)),
                    'note': '数据修复自动生成'
                })
                stock_in_count += 1
                print(f"已为物品 {item_name} 生成入库记录，数量: {quantity}，均价: {avg_price}")
                
            # 2. 负库存：创建一条大量入库记录和足够的出库记录
            elif quantity < 0:
                abs_quantity = abs(quantity)
                # 模拟假设原有1000个入库，然后出库量比入库量多，导致负库存
                initial_quantity = 1000
                total_in_cost = int(float(avg_price) * initial_quantity)
                
                # 生成入库记录（25-30天前）
                in_days_ago = random.randint(25, 30)
                in_time = (datetime.now() - timedelta(days=in_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                db.save_stock_in({
                    'item_name': item_name,
                    'transaction_time': in_time,
                    'quantity': initial_quantity,
                    'cost': total_in_cost,
                    'avg_cost': int(float(avg_price)),
                    'note': '数据修复自动生成(负库存补偿)'
                })
                stock_in_count += 1
                
                # 生成出库记录（数量为入库量+负库存量，15-20天前）
                out_quantity = initial_quantity + abs_quantity
                out_days_ago = random.randint(15, 20)
                out_time = (datetime.now() - timedelta(days=out_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                unit_price = int(float(selling_price) if selling_price and float(selling_price) > 0 else float(avg_price) * 1.1)
                fee = int(out_quantity * unit_price * 0.05)  # 假设5%手续费
                total_amount = out_quantity * unit_price - fee
                
                db.save_stock_out({
                    'item_name': item_name,
                    'transaction_time': out_time,
                    'quantity': out_quantity,
                    'unit_price': unit_price,
                    'fee': fee,
                    'deposit': 0,
                    'total_amount': total_amount,
                    'note': '数据修复自动生成(负库存补偿)'
                })
                stock_out_count += 1
                
                print(f"已为负库存物品 {item_name} 生成配对交易记录，当前库存: {quantity}")
                
            # 3. 零库存：创建配对的入库和出库记录
            else:
                # 生成入库记录（25-30天前）
                initial_quantity = 1000  # 假设原来有1000个入库
                total_cost = int(float(avg_price) * initial_quantity)
                
                in_days_ago = random.randint(25, 30)
                in_time = (datetime.now() - timedelta(days=in_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                db.save_stock_in({
                    'item_name': item_name,
                    'transaction_time': in_time,
                    'quantity': initial_quantity,
                    'cost': total_cost,
                    'avg_cost': int(float(avg_price)),
                    'note': '数据修复自动生成(零库存)'
                })
                stock_in_count += 1
                
                # 生成出库记录（15-20天前）
                out_days_ago = random.randint(15, 20)
                out_time = (datetime.now() - timedelta(days=out_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                unit_price = int(float(selling_price) if selling_price and float(selling_price) > 0 else float(avg_price) * 1.1)
                fee = int(initial_quantity * unit_price * 0.05)  # 假设5%手续费
                total_amount = initial_quantity * unit_price - fee
                
                db.save_stock_out({
                    'item_name': item_name,
                    'transaction_time': out_time,
                    'quantity': initial_quantity,
                    'unit_price': unit_price,
                    'fee': fee,
                    'deposit': 0,
                    'total_amount': total_amount,
                    'note': '数据修复自动生成(零库存)'
                })
                stock_out_count += 1
                
                print(f"已为零库存物品 {item_name} 生成配对交易记录")
                
        except Exception as e:
            print(f"为物品 {item_name} 生成交易记录失败: {e}")
    
    print(f"库存与交易记录修复完成! 成功生成 {stock_in_count} 条入库记录, {stock_out_count} 条出库记录")
    
    # 最后更新库存表确保一致性
    print("更新库存表以确保数据一致性...")
    # 列出所有需要重建库存的物品
    try:
        stock_in_data = db.get_stock_in()
        items_set = set()
        for item in stock_in_data:
            _, item_name, *_ = item
            items_set.add(item_name)
        
        # 清空库存表，完全重建
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM inventory")
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        
        # 恢复inventory表，通过调用increase_inventory方法
        for item in inventory_data:
            if not any(item_name in str(row) for row in stock_in_data):
                continue  # 跳过不在入库记录中的物品
            
            # 获取每个物品的所有入库记录
            item_stock_ins = [record for record in stock_in_data if record[1] == item_name]
            
            for stock_in in item_stock_ins:
                _, item_name, _, quantity, cost, avg_cost, *_ = stock_in
                db.increase_inventory(item_name, quantity, avg_cost)
                
        print("库存表更新完成!")
    except Exception as e:
        print(f"重建库存数据时出错: {e}")
    
    return True

def main():
    print("===== 库存与交易记录全面修复工具 =====")
    print("此工具将根据当前库存数据，生成合理的入库和出库记录")
    print("适用于：库存数据不依赖于入库和出库记录计算的情况")
    print("注意：这将重建所有交易记录，使库存成为入库减去出库的结果")
    print()
    
    # 请求用户确认
    confirm = input("是否继续? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 执行修复
    if fix_inventory_and_transactions():
        print("全面修复完成! 请刷新应用程序查看结果。")
    else:
        print("修复失败!")

if __name__ == "__main__":
    main() 