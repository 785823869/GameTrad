from src.core.db_manager import DatabaseManager
from datetime import datetime

def fix_inventory():
    """根据入库和出库记录重新计算并更新库存表"""
    print("开始修复库存数据...")
    db = DatabaseManager()
    
    # 先清空库存表
    db.execute_query("DELETE FROM inventory")
    print("已清空库存表")
    
    # 获取所有入库和出库数据
    stock_in_data = db.get_stock_in()
    stock_out_data = db.get_stock_out()
    
    print(f"获取到 {len(stock_in_data)} 条入库记录")
    print(f"获取到 {len(stock_out_data)} 条出库记录")
    
    # 计算每个物品的库存数量和平均价格
    inventory = {}
    
    # 处理入库记录
    for row in stock_in_data:
        try:
            _, item_name, _, qty, cost, avg_cost, *_ = row
            qty = int(qty)
            cost = float(cost)
            avg_cost = float(avg_cost)
            
            if item_name not in inventory:
                inventory[item_name] = {
                    'quantity': 0, 
                    'total_cost': 0.0,
                    'in_qty': 0,
                    'in_cost': 0.0,
                    'out_qty': 0,
                    'out_amount': 0.0
                }
            
            inventory[item_name]['quantity'] += qty
            inventory[item_name]['total_cost'] += cost
            inventory[item_name]['in_qty'] += qty
            inventory[item_name]['in_cost'] += cost
        except Exception as e:
            print(f"处理入库记录错误: {e}")
            continue
    
    # 处理出库记录
    for row in stock_out_data:
        try:
            _, item_name, _, qty, unit_price, fee, deposit, total_amount, *_ = row
            qty = int(qty)
            unit_price = float(unit_price)
            fee = float(fee)
            total_amount = float(total_amount)
            
            if item_name not in inventory:
                inventory[item_name] = {
                    'quantity': 0, 
                    'total_cost': 0.0,
                    'in_qty': 0,
                    'in_cost': 0.0,
                    'out_qty': 0,
                    'out_amount': 0.0
                }
            
            inventory[item_name]['quantity'] -= qty
            inventory[item_name]['out_qty'] += qty
            inventory[item_name]['out_amount'] += (unit_price * qty - fee)
        except Exception as e:
            print(f"处理出库记录错误: {e}")
            continue
    
    # 更新库存表
    success_count = 0
    fail_count = 0
    
    for item_name, data in inventory.items():
        try:
            # 计算均价
            avg_price = data['total_cost'] / data['in_qty'] if data['in_qty'] > 0 else 0
            out_avg = data['out_amount'] / data['out_qty'] if data['out_qty'] > 0 else 0
            
            # 计算利润相关数据
            profit = (out_avg - avg_price) * data['out_qty'] if data['out_qty'] > 0 else 0
            profit_rate = ((out_avg - avg_price) / avg_price * 100) if avg_price > 0 and data['out_qty'] > 0 else 0
            total_profit = profit  # 累计利润等于单项利润
            inventory_value = data['quantity'] * avg_price if data['quantity'] > 0 else 0
            
            # 保存到库存表
            item_data = {
                'item_name': item_name,
                'quantity': data['quantity'],
                'avg_price': avg_price,
                'break_even_price': avg_price,  # 简单起见，保本价等于平均成本
                'selling_price': out_avg if out_avg > 0 else avg_price,  # 如果有出库价则使用，否则使用入库均价
                'profit': profit,
                'profit_rate': profit_rate,
                'total_profit': total_profit,
                'inventory_value': inventory_value
            }
            
            db.save_inventory(item_data)
            
            print(f"物品 '{item_name}' 库存修复成功: {data['quantity']} 个, 均价 {avg_price:.2f}")
            success_count += 1
        except Exception as e:
            print(f"物品 '{item_name}' 库存修复失败: {e}")
            fail_count += 1
    
    print("\n库存修复完成!")
    print(f"成功: {success_count} 个物品")
    print(f"失败: {fail_count} 个物品")
    
    # 再次检查库存表
    inventory_count = db.fetch_one("SELECT COUNT(*) FROM inventory")[0]
    print(f"库存记录总数: {inventory_count}")

if __name__ == "__main__":
    fix_inventory() 