#!/usr/bin/env python
# 库存修复脚本 - 从入库记录重新计算库存数据

from src.core.db_manager import DatabaseManager
import json

def fix_inventory():
    print("开始修复库存数据...")
    db = DatabaseManager()
    
    # 清空现有inventory表数据
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE inventory")
        conn.commit()
        print("已清空库存表")
    except Exception as e:
        print(f"清空库存表失败: {e}")
        return
    finally:
        cursor.close()
        conn.close()
    
    # 获取所有入库数据
    stock_in_data = db.get_stock_in()
    print(f"获取到 {len(stock_in_data)} 条入库记录")
    
    # 获取所有出库数据
    stock_out_data = db.get_stock_out()
    print(f"获取到 {len(stock_out_data)} 条出库记录")
    
    # 计算库存情况
    inventory = {}
    
    # 处理入库数据
    for record in stock_in_data:
        try:
            _, item_name, _, quantity, cost, avg_cost, *_ = record
            if item_name not in inventory:
                inventory[item_name] = {
                    'in_qty': 0, 
                    'in_amount': 0, 
                    'out_qty': 0, 
                    'out_amount': 0
                }
            
            inventory[item_name]['in_qty'] += int(quantity)
            inventory[item_name]['in_amount'] += float(cost)
        except Exception as e:
            print(f"处理入库记录时出错: {e}")
            continue
    
    # 处理出库数据
    for record in stock_out_data:
        try:
            _, item_name, _, quantity, unit_price, fee, deposit, total_amount, *_ = record
            if item_name not in inventory:
                inventory[item_name] = {
                    'in_qty': 0, 
                    'in_amount': 0, 
                    'out_qty': 0, 
                    'out_amount': 0
                }
            
            inventory[item_name]['out_qty'] += int(quantity)
            inventory[item_name]['out_amount'] += float(total_amount)
        except Exception as e:
            print(f"处理出库记录时出错: {e}")
            continue
    
    # 插入库存数据
    success_count = 0
    error_count = 0
    
    for item_name, data in inventory.items():
        try:
            # 计算库存数量
            remain_qty = data['in_qty'] - data['out_qty']
            
            # 计算均价
            avg_price = data['in_amount'] / data['in_qty'] if data['in_qty'] > 0 else 0
            
            # 计算出库均价
            out_avg = data['out_amount'] / data['out_qty'] if data['out_qty'] > 0 else 0
            
            # 计算利润和利润率
            profit = (out_avg - avg_price) * data['out_qty'] if data['out_qty'] > 0 else 0
            profit_rate = ((out_avg - avg_price) / avg_price * 100) if avg_price > 0 and data['out_qty'] > 0 else 0
            
            # 计算库存价值
            inventory_value = remain_qty * avg_price if remain_qty > 0 else 0
            
            # 构建库存数据
            inventory_record = {
                'item_name': item_name,
                'quantity': remain_qty,
                'avg_price': avg_price,
                'break_even_price': avg_price,  # 保本价等于入库均价
                'selling_price': out_avg if out_avg > 0 else avg_price,  # 如果未出库，就用入库均价
                'profit': profit,
                'profit_rate': profit_rate,
                'total_profit': profit,  # 成交利润等于利润
                'inventory_value': inventory_value
            }
            
            # 保存库存记录
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO inventory (
                        item_name, quantity, avg_price, break_even_price, 
                        selling_price, profit, profit_rate, total_profit, inventory_value
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item_name, remain_qty, avg_price, avg_price,
                    out_avg if out_avg > 0 else avg_price, profit, profit_rate, profit, inventory_value
                ))
                conn.commit()
                success_count += 1
                print(f"物品 '{item_name}' 库存修复成功: {remain_qty} 个, 均价 {avg_price:.2f}")
            except Exception as e:
                error_count += 1
                print(f"物品 '{item_name}' 库存保存失败: {e}")
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            error_count += 1
            print(f"处理物品 '{item_name}' 库存时出错: {e}")
    
    # 输出结果
    print(f"\n库存修复完成!")
    print(f"成功: {success_count} 个物品")
    print(f"失败: {error_count} 个物品")
    print(f"库存记录总数: {success_count}")
    
if __name__ == "__main__":
    fix_inventory() 