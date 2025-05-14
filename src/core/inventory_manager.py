from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict

class InventoryManager:
    def __init__(self):
        self.inventory = {}  # {item_name: {"quantity": int, "avg_price": float}}
        self.transactions = []  # 记录所有交易
        self.categories = {}  # {item_name: category}
        self.min_stock_levels = {}  # {item_name: min_quantity}
    
    def add_stock(self, item_name: str, quantity: int, price: float, date: datetime = None, source: str = None):
        """添加库存，使用移动加权平均法更新单价"""
        if date is None:
            date = datetime.now()
            
        if item_name not in self.inventory:
            self.inventory[item_name] = {"quantity": 0, "avg_price": 0.0}
        
        current = self.inventory[item_name]
        total_quantity = current["quantity"] + quantity
        total_value = (current["quantity"] * current["avg_price"]) + (quantity * price)
        
        # 更新库存
        self.inventory[item_name] = {
            "quantity": total_quantity,
            "avg_price": total_value / total_quantity if total_quantity > 0 else 0.0
        }
        
        # 记录交易
        self.transactions.append({
            "date": date,
            "item": item_name,
            "quantity": quantity,
            "price": price,
            "type": "in",
            "source": source
        })
    
    def remove_stock(self, item_name: str, quantity: int, price: float, date: datetime = None, destination: str = None):
        """移除库存"""
        if date is None:
            date = datetime.now()
            
        if item_name not in self.inventory or self.inventory[item_name]["quantity"] < quantity:
            raise ValueError(f"库存不足: {item_name}")
        
        current = self.inventory[item_name]
        current["quantity"] -= quantity
        
        # 记录交易
        self.transactions.append({
            "date": date,
            "item": item_name,
            "quantity": quantity,
            "price": price,
            "type": "out",
            "destination": destination
        })
    
    def set_category(self, item_name: str, category: str):
        """设置物品分类"""
        self.categories[item_name] = category
    
    def set_min_stock_level(self, item_name: str, min_quantity: int):
        """设置最低库存水平"""
        self.min_stock_levels[item_name] = min_quantity
    
    def get_inventory_value(self) -> float:
        """计算当前库存总价值"""
        return sum(
            item["quantity"] * item["avg_price"]
            for item in self.inventory.values()
        )
    
    def get_item_value(self, item_name: str) -> float:
        """获取指定物品的库存价值"""
        if item_name not in self.inventory:
            return 0.0
        item = self.inventory[item_name]
        return item["quantity"] * item["avg_price"]
    
    def get_transaction_history(self) -> List[Dict]:
        """获取交易历史记录"""
        return self.transactions
    
    def get_category_summary(self) -> Dict[str, Dict[str, float]]:
        """获取分类统计"""
        if not self.categories:
            return {}
        
        summary = defaultdict(lambda: {"quantity": 0, "value": 0.0})
        
        for item_name, category in self.categories.items():
            if item_name in self.inventory:
                item = self.inventory[item_name]
                summary[category]["quantity"] += item["quantity"]
                summary[category]["value"] += item["quantity"] * item["avg_price"]
        
        return dict(summary)
    
    def get_low_stock_items(self) -> List[Dict]:
        """获取低库存物品列表"""
        low_stock = []
        for item_name, min_quantity in self.min_stock_levels.items():
            if item_name in self.inventory:
                current_quantity = self.inventory[item_name]["quantity"]
                if current_quantity < min_quantity:
                    low_stock.append({
                        "item": item_name,
                        "current_quantity": current_quantity,
                        "min_quantity": min_quantity
                    })
        return low_stock
    
    def get_price_history(self, item_name: str, days: int = 30) -> List[Dict]:
        """获取物品价格历史"""
        if not self.transactions:
            return []
        
        # 筛选指定物品的交易记录
        item_transactions = [
            t for t in self.transactions 
            if t['item'] == item_name
        ]
        
        # 按日期分组计算平均价格
        price_by_date = defaultdict(list)
        for t in item_transactions:
            price_by_date[t['date'].date()].append(t['price'])
        
        # 计算每日平均价格
        price_history = [
            {
                'date': date,
                'price': sum(prices) / len(prices)
            }
            for date, prices in price_by_date.items()
        ]
        
        # 只返回指定天数内的记录
        cutoff_date = datetime.now().date() - timedelta(days=days)
        return [
            p for p in price_history 
            if p['date'] >= cutoff_date
        ]
    
    def save_state(self, filename: str):
        """保存当前状态到文件"""
        state = {
            "inventory": self.inventory,
            "transactions": self.transactions,
            "categories": self.categories,
            "min_stock_levels": self.min_stock_levels
        }
        with open(os.path.join('data', filename), 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)
    
    def load_state(self, filename: str):
        """从文件加载状态"""
        with open(os.path.join('data', filename), 'r', encoding='utf-8') as f:
            state = json.load(f)
            self.inventory = state["inventory"]
            self.transactions = state["transactions"]
            self.categories = state["categories"]
            self.min_stock_levels = state["min_stock_levels"]

# 使用示例
if __name__ == "__main__":
    manager = InventoryManager()
    
    # 设置分类和最低库存
    manager.set_category("铁剑", "武器")
    manager.set_min_stock_level("铁剑", 5)
    
    # 添加库存
    manager.add_stock("铁剑", 10, 100.0, source="制造")
    manager.add_stock("铁剑", 5, 110.0, source="购买")
    
    # 移除库存
    manager.remove_stock("铁剑", 3, 150.0, destination="玩家A")
    
    # 查看库存状态
    print(f"铁剑库存数量: {manager.inventory['铁剑']['quantity']}")
    print(f"铁剑平均单价: {manager.inventory['铁剑']['avg_price']:.2f}")
    print(f"库存总价值: {manager.get_inventory_value():.2f}")
    
    # 查看分类统计
    print("\n分类统计:")
    print(manager.get_category_summary())
    
    # 查看低库存物品
    print("\n低库存物品:")
    print(manager.get_low_stock_items())
    
    # 查看价格历史
    print("\n价格历史:")
    print(manager.get_price_history("铁剑"))
    
    # 保存状态
    manager.save_state("inventory_state.json")
    
    # 加载状态
    manager.load_state("inventory_state.json")
    
    # 查看加载后的库存状态
    print("\n加载后的库存状态:")
    print(f"铁剑库存数量: {manager.inventory['铁剑']['quantity']}")
    print(f"铁剑平均单价: {manager.inventory['铁剑']['avg_price']:.2f}")
    print(f"库存总价值: {manager.get_inventory_value():.2f}") 