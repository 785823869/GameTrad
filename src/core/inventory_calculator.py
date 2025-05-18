#!/usr/bin/env python
# 库存计算模块 - 提供库存数据计算功能

from src.core.db_manager import DatabaseManager

def calculate_inventory(db_manager=None, update_db=True, silent=False):
    """
    计算库存数据，可选择是否更新数据库
    
    Args:
        db_manager: 数据库管理器实例，如果为None则创建新实例
        update_db: 是否更新数据库中的库存表
        silent: 是否静默执行（不打印日志）
    
    Returns:
        计算后的库存数据字典
    """
    if not db_manager:
        db_manager = DatabaseManager()
    
    if not silent:
        print("开始计算库存数据...")
    
    # 如果需要更新数据库，先清空现有库存表
    if update_db:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("TRUNCATE TABLE inventory")
            conn.commit()
            if not silent:
                print("已清空库存表")
        except Exception as e:
            if not silent:
                print(f"清空库存表失败: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    # 获取所有入库数据
    stock_in_data = db_manager.get_stock_in()
    if not silent:
        print(f"获取到 {len(stock_in_data)} 条入库记录")
    
    # 获取所有出库数据
    stock_out_data = db_manager.get_stock_out()
    if not silent:
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
            if not silent:
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
            if not silent:
                print(f"处理出库记录时出错: {e}")
            continue
    
    # 计算最终库存数据
    result_inventory = {}
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
            
            # 保存结果
            result_inventory[item_name] = inventory_record
            
            # 如果需要更新数据库，保存库存记录
            if update_db:
                conn = db_manager.get_connection()
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
                    if not silent:
                        print(f"物品 '{item_name}' 库存计算成功: {remain_qty} 个, 均价 {avg_price:.2f}")
                except Exception as e:
                    error_count += 1
                    if not silent:
                        print(f"物品 '{item_name}' 库存保存失败: {e}")
                finally:
                    cursor.close()
                    conn.close()
                
        except Exception as e:
            error_count += 1
            if not silent:
                print(f"处理物品 '{item_name}' 库存时出错: {e}")
    
    # 输出结果
    if not silent:
        print(f"\n库存计算完成!")
        print(f"成功: {success_count} 个物品")
        print(f"失败: {error_count} 个物品")
        print(f"库存记录总数: {success_count}")
    
    return result_inventory

if __name__ == "__main__":
    # 如果直接运行此模块，则执行库存计算并更新数据库
    calculate_inventory(update_db=True, silent=False) 