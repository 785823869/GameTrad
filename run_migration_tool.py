#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动数据迁移工具
"""
import sys
import os
import traceback

# 添加src目录到路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.path}")

def main():
    try:
        # 确保所需模块已安装
        print("检查必要模块...")
        
        try:
            import MySQLdb
            print("✓ MySQLdb模块已安装")
        except ImportError as e:
            print(f"✗ MySQLdb模块未安装: {e}")
            print("  请执行: pip install mysqlclient")
            return 1
            
        try:
            from PyQt5.QtWidgets import QApplication
            print("✓ PyQt5模块已安装")
        except ImportError as e:
            print(f"✗ PyQt5模块未安装: {e}")
            print("  请执行: pip install pyqt5")
            return 1
            
        try:
            import tqdm
            print("✓ tqdm模块已安装")
        except ImportError as e:
            print(f"✗ tqdm模块未安装: {e}")
            print("  请执行: pip install tqdm")
            return 1
        
        # 检查迁移工具文件是否存在
        migrate_gui_path = os.path.join(current_dir, "src", "scripts", "migrate_data_gui.py")
        if os.path.exists(migrate_gui_path):
            print(f"✓ 找到迁移工具文件: {migrate_gui_path}")
        else:
            print(f"✗ 未找到迁移工具文件: {migrate_gui_path}")
            return 1
            
        # 导入迁移工具
        print("导入迁移工具模块...")
        try:
            # 直接导入模块
            sys.path.append(os.path.join(current_dir, "src", "scripts"))
            from migrate_data_gui import MigrationGUI, main as run_migration_tool
            print("✓ 成功导入迁移工具模块")
        except ImportError as e:
            print(f"✗ 导入迁移工具模块失败: {e}")
            traceback.print_exc()
            return 1
        
        # 运行迁移工具
        print("启动数据迁移工具...")
        run_migration_tool()
        return 0
        
    except Exception as e:
        print(f"启动失败: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 