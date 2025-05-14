import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.recipe_parser import RecipeParser
from src.core.inventory_manager import InventoryManager
from src.core.trade_analyzer import TradeAnalyzer
from datetime import datetime, timedelta

def main():
    print("=== 游戏交易系统测试 ===\n")
    
    # 1. 初始化系统组件
    print("1. 初始化系统组件...")
    inventory_manager = InventoryManager()
    recipe_parser = RecipeParser()
    trade_analyzer = TradeAnalyzer(inventory_manager, recipe_parser)
    
    # 2. 设置配方和材料价格
    print("\n2. 设置配方和材料价格...")
    recipe_parser.add_recipe("铁剑", {"iron": 3, "wood": 1}, processing_fee=10.0)
    recipe_parser.add_recipe("iron", {"iron_ore": 2, "coal": 1}, processing_fee=5.0)
    
    recipe_parser.set_material_price("iron_ore", 10.0)
    recipe_parser.set_material_price("coal", 5.0)
    recipe_parser.set_material_price("wood", 8.0)
    
    # 3. 设置物品分类和库存预警
    print("\n3. 设置物品分类和库存预警...")
    inventory_manager.set_category("铁剑", "武器")
    inventory_manager.set_min_stock_level("铁剑", 5)
    
    # 4. 模拟交易记录
    print("\n4. 模拟交易记录...")
    # 添加库存
    inventory_manager.add_stock("铁剑", 10, 100.0, source="制造")
    inventory_manager.add_stock("铁剑", 5, 110.0, source="购买")
    
    # 模拟一些交易
    inventory_manager.remove_stock("铁剑", 3, 150.0, destination="玩家A")
    inventory_manager.remove_stock("铁剑", 2, 160.0, destination="玩家B")
    
    # 5. 显示当前库存状态
    print("\n5. 当前库存状态:")
    for item, data in inventory_manager.inventory.items():
        print(f"{item}: 数量={data['quantity']}, 平均单价={data['avg_price']:.2f}")
    
    # 6. 显示分类统计
    print("\n6. 分类统计:")
    category_summary = inventory_manager.get_category_summary()
    print(category_summary)
    
    # 7. 显示低库存预警
    print("\n7. 低库存预警:")
    low_stock = inventory_manager.get_low_stock_items()
    if low_stock:
        for item in low_stock:
            print(f"- {item}")
    else:
        print("没有低库存物品")
    
    # 8. 显示滞销品列表
    print("\n8. 滞销品列表:")
    slow_moving = trade_analyzer.get_slow_moving_items()
    if slow_moving:
        for item in slow_moving:
            print(f"- {item}")
    else:
        print("没有滞销品")
    
    # 9. 显示利润率排行榜
    print("\n9. 利润率排行榜:")
    profit_ranking = trade_analyzer.get_profit_ranking()
    for item in profit_ranking:
        print(f"- {item['item']}: 利润率={item['profit_rate']:.2f}%")
    
    # 10. 显示交易税统计
    print("\n10. 交易税统计:")
    tax_summary = trade_analyzer.get_trade_tax_summary()
    for item in tax_summary:
        print(f"- {item['item']}: 数量={item['quantity']}, 税额={item['tax_amount']:.2f}")
    
    # 11. 显示制造利润分析
    print("\n11. 制造利润分析:")
    manufacturing_profit = trade_analyzer.get_manufacturing_profit_analysis()
    for item in manufacturing_profit:
        print(f"- {item['item']}: 利润率={item['profit_rate']:.2f}%")
    
    # 12. 保存系统状态
    print("\n12. 保存系统状态...")
    inventory_manager.save_state("inventory_state.json")
    recipe_parser.save_recipes(os.path.join("data", "recipes.json"))
    print("系统状态已保存")

if __name__ == "__main__":
    main() 