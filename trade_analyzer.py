from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from recipe_parser import RecipeParser

class TradeAnalyzer:
    def __init__(self, inventory_manager, recipe_parser: RecipeParser = None):
        self.inventory_manager = inventory_manager
        self.recipe_parser = recipe_parser
    
    def get_volume_by_period(self, period: str = 'D') -> List[Dict]:
        """
        按指定周期统计成交量
        period: 'D'=日, 'W'=周, 'M'=月
        """
        transactions = self.inventory_manager.get_transaction_history()
        if not transactions:
            return []
        
        # 只统计出库交易
        out_transactions = [
            t for t in transactions 
            if t['type'] == 'out'
        ]
        
        # 按周期分组统计
        volume_by_period = defaultdict(lambda: defaultdict(int))
        for t in out_transactions:
            date = t['date']
            if period == 'D':
                key = date.date()
            elif period == 'W':
                key = date.date() - timedelta(days=date.weekday())
            else:  # 'M'
                key = date.date().replace(day=1)
            
            volume_by_period[key][t['item']] += t['quantity']
        
        # 转换为列表格式
        result = []
        for date, items in volume_by_period.items():
            for item, quantity in items.items():
                result.append({
                    'date': date,
                    'item': item,
                    'quantity': quantity
                })
        
        return sorted(result, key=lambda x: x['date'])
    
    def get_profit_ranking(self, top_n: int = 10) -> List[Dict]:
        """计算利润率排行榜"""
        transactions = self.inventory_manager.get_transaction_history()
        if not transactions:
            return []
        
        # 计算每个物品的利润
        profits = defaultdict(lambda: {
            'total_sales': 0.0,
            'cost': 0.0,
            'profit': 0.0,
            'profit_rate': 0.0
        })
        
        for item in set(t['item'] for t in transactions):
            item_transactions = [t for t in transactions if t['item'] == item]
            
            # 计算销售总额
            sales = sum(
                t['quantity'] * t['price']
                for t in item_transactions
                if t['type'] == 'out'
            )
            
            # 计算成本
            inventory = self.inventory_manager.inventory.get(item, {'avg_price': 0})
            cost = sum(
                t['quantity'] * inventory['avg_price']
                for t in item_transactions
                if t['type'] == 'out'
            )
            
            # 计算利润
            profit = sales - cost
            profit_rate = (profit / cost * 100) if cost > 0 else 0
            
            profits[item].update({
                'item': item,
                'total_sales': sales,
                'cost': cost,
                'profit': profit,
                'profit_rate': profit_rate
            })
        
        # 转换为列表并排序
        result = list(profits.values())
        return sorted(result, key=lambda x: x['profit_rate'], reverse=True)[:top_n]
    
    def get_slow_moving_items(self, days: int = 30) -> List[str]:
        """获取滞销品列表"""
        transactions = self.inventory_manager.get_transaction_history()
        if not transactions:
            return []
        
        # 获取最近一次交易时间
        last_trade = defaultdict(lambda: datetime.min)
        for t in transactions:
            if t['date'] > last_trade[t['item']]:
                last_trade[t['item']] = t['date']
        
        # 找出超过指定天数没有交易的商品
        cutoff_date = datetime.now() - timedelta(days=days)
        slow_moving = [
            item for item, last_date in last_trade.items()
            if last_date < cutoff_date and item in self.inventory_manager.inventory
        ]
        
        return slow_moving
    
    def get_trade_tax_summary(self, tax_rate: float = 0.05) -> List[Dict]:
        """计算交易税统计"""
        transactions = self.inventory_manager.get_transaction_history()
        if not transactions:
            return []
        
        # 只统计出库交易
        out_transactions = [
            t for t in transactions 
            if t['type'] == 'out'
        ]
        
        # 按物品分组统计
        tax_by_item = defaultdict(lambda: {
            'quantity': 0,
            'price_sum': 0.0,
            'price_count': 0,
            'tax_amount': 0.0
        })
        
        for t in out_transactions:
            item = t['item']
            tax_by_item[item]['quantity'] += t['quantity']
            tax_by_item[item]['price_sum'] += t['price']
            tax_by_item[item]['price_count'] += 1
            tax_by_item[item]['tax_amount'] += t['quantity'] * t['price'] * tax_rate
        
        # 计算平均价格并转换为列表
        result = []
        for item, data in tax_by_item.items():
            result.append({
                'item': item,
                'quantity': data['quantity'],
                'price': data['price_sum'] / data['price_count'],
                'tax_amount': data['tax_amount']
            })
        
        return result
    
    def get_manufacturing_profit_analysis(self) -> List[Dict]:
        """分析制造利润"""
        if not self.recipe_parser:
            raise ValueError("需要提供RecipeParser实例")
        
        transactions = self.inventory_manager.get_transaction_history()
        if not transactions:
            return []
        
        # 只统计出库交易
        out_transactions = [
            t for t in transactions 
            if t['type'] == 'out'
        ]
        
        # 计算每个物品的制造利润
        profits = []
        for item in set(t['item'] for t in out_transactions):
            if item not in self.recipe_parser.recipes:
                continue
            
            item_transactions = [t for t in out_transactions if t['item'] == item]
            
            # 计算销售总额
            total_sales = sum(t['quantity'] * t['price'] for t in item_transactions)
            
            # 计算制造成本
            total_quantity = sum(t['quantity'] for t in item_transactions)
            _, total_cost = self.recipe_parser.calculate_cost(item, total_quantity)
            
            # 计算利润
            profit = total_sales - total_cost
            profit_rate = (profit / total_cost * 100) if total_cost > 0 else 0
            
            profits.append({
                'item': item,
                'total_sales': total_sales,
                'manufacturing_cost': total_cost,
                'profit': profit,
                'profit_rate': profit_rate
            })
        
        return sorted(profits, key=lambda x: x['profit_rate'], reverse=True)

# 使用示例
if __name__ == "__main__":
    from inventory_manager import InventoryManager
    from recipe_parser import RecipeParser
    
    # 创建库存管理器和配方解析器
    manager = InventoryManager()
    parser = RecipeParser()
    
    # 添加配方
    parser.add_recipe("铁剑", {"iron": 3, "wood": 1}, processing_fee=10.0)
    parser.add_recipe("iron", {"iron_ore": 2, "coal": 1}, processing_fee=5.0)
    
    # 设置材料价格
    parser.set_material_price("iron_ore", 10.0)
    parser.set_material_price("coal", 5.0)
    parser.set_material_price("wood", 8.0)
    
    # 添加一些测试数据
    manager.add_stock("铁剑", 10, 100.0, source="制造")
    manager.add_stock("铁剑", 5, 110.0, source="购买")
    manager.remove_stock("铁剑", 3, 150.0, destination="玩家A")
    
    # 创建分析器
    analyzer = TradeAnalyzer(manager, parser)
    
    # 获取日成交量统计
    daily_volume = analyzer.get_volume_by_period('D')
    print("\n日成交量统计:")
    print(daily_volume)
    
    # 获取利润率排行榜
    profit_ranking = analyzer.get_profit_ranking()
    print("\n利润率排行榜:")
    print(profit_ranking)
    
    # 获取滞销品列表
    slow_moving = analyzer.get_slow_moving_items()
    print("\n滞销品列表:")
    print(slow_moving)
    
    # 获取交易税统计
    tax_summary = analyzer.get_trade_tax_summary()
    print("\n交易税统计:")
    print(tax_summary)
    
    # 获取制造利润分析
    manufacturing_profit = analyzer.get_manufacturing_profit_analysis()
    print("\n制造利润分析:")
    print(manufacturing_profit) 