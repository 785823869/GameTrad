from typing import Dict, List, Tuple
from collections import defaultdict
import json
import os

class RecipeParser:
    def __init__(self):
        self.recipes = {}  # {item_name: {"materials": Dict[str, int], "processing_fee": float}}
        self.material_prices = {}
    
    def add_recipe(self, item_name: str, recipe: Dict[str, int], processing_fee: float = 0.0):
        """添加或更新配方
        Args:
            item_name: 物品名称
            recipe: 材料配方 {"material": quantity}
            processing_fee: 加工费用
        """
        self.recipes[item_name] = {
            "materials": recipe,
            "processing_fee": processing_fee
        }
    
    def set_material_price(self, material: str, price: float):
        """设置材料单价"""
        self.material_prices[material] = price
    
    def calculate_materials(self, item_name: str, quantity: int = 1) -> Dict[str, int]:
        """计算制造指定物品所需的所有材料"""
        if item_name not in self.recipes:
            return {item_name: quantity}
        
        materials = defaultdict(int)
        recipe = self.recipes[item_name]["materials"]
        
        for material, amount in recipe.items():
            if material in self.recipes:  # 如果材料也需要制造
                sub_materials = self.calculate_materials(material, amount * quantity)
                for sub_material, sub_amount in sub_materials.items():
                    materials[sub_material] += sub_amount
            else:  # 基础材料
                materials[material] += amount * quantity
        
        return dict(materials)
    
    def calculate_cost(self, item_name: str, quantity: int = 1) -> Tuple[Dict[str, int], float]:
        """计算制造指定物品所需的所有材料和总成本"""
        materials = self.calculate_materials(item_name, quantity)
        total_cost = 0.0
        
        # 计算材料成本
        for material, amount in materials.items():
            if material in self.material_prices:
                total_cost += self.material_prices[material] * amount
            else:
                print(f"Warning: Price not set for material {material}")
        
        # 添加加工费用
        if item_name in self.recipes:
            total_cost += self.recipes[item_name]["processing_fee"] * quantity
        
        return materials, total_cost
    
    def get_recipe_tree(self, item_name: str) -> Dict:
        """获取配方的树形结构"""
        if item_name not in self.recipes:
            return {"name": item_name, "type": "material"}
        
        recipe = self.recipes[item_name]
        tree = {
            "name": item_name,
            "type": "recipe",
            "processing_fee": recipe["processing_fee"],
            "materials": []
        }
        
        for material, amount in recipe["materials"].items():
            if material in self.recipes:
                sub_tree = self.get_recipe_tree(material)
                sub_tree["amount"] = amount
                tree["materials"].append(sub_tree)
            else:
                tree["materials"].append({
                    "name": material,
                    "type": "material",
                    "amount": amount
                })
        
        return tree
    
    def save_recipes(self, filename: str):
        """保存配方到文件"""
        with open(os.path.join('data', filename), 'w', encoding='utf-8') as f:
            json.dump(self.recipes, f, ensure_ascii=False, indent=2)
    
    def load_recipes(self, filename: str):
        """从文件加载配方"""
        with open(os.path.join('data', filename), 'r', encoding='utf-8') as f:
            self.recipes = json.load(f)

# 使用示例
if __name__ == "__main__":
    parser = RecipeParser()
    
    # 添加配方
    parser.add_recipe("铁剑", {"iron": 3, "wood": 1}, processing_fee=10.0)
    parser.add_recipe("iron", {"iron_ore": 2, "coal": 1}, processing_fee=5.0)
    
    # 设置材料价格
    parser.set_material_price("iron_ore", 10.0)
    parser.set_material_price("coal", 5.0)
    parser.set_material_price("wood", 8.0)
    
    # 计算制造一把铁剑所需的材料和成本
    materials, cost = parser.calculate_cost("铁剑")
    print(f"制造铁剑所需材料: {materials}")
    print(f"预估成本: {cost}")
    
    # 获取配方树
    recipe_tree = parser.get_recipe_tree("铁剑")
    print("\n配方树结构:")
    print(json.dumps(recipe_tree, ensure_ascii=False, indent=2)) 