import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from src.scripts.migrate_data import DataMigrator
    print("成功导入DataMigrator模块")
except Exception as e:
    print(f"导入失败: {e}") 