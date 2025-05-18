#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据迁移工具启动
"""
import os
import sys
import subprocess

# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from src.utils.path_resolver import get_script_path

def test_migration_tool_launch():
    """测试数据迁移工具启动"""
    print("测试数据迁移工具启动...")
    
    # 获取迁移工具脚本路径
    migration_script_path = get_script_path("scripts/migrate_data_gui.py")
    
    # 检查脚本是否存在
    if not os.path.exists(migration_script_path):
        print(f"错误: 找不到数据迁移工具: {migration_script_path}")
        return False
    
    print(f"找到数据迁移工具: {migration_script_path}")
    
    try:
        # 启动迁移工具
        print(f"尝试启动: {sys.executable} {migration_script_path}")
        subprocess.Popen([sys.executable, migration_script_path])
        print("数据迁移工具已启动")
        return True
    except Exception as e:
        print(f"启动数据迁移工具失败: {e}")
        return False

if __name__ == "__main__":
    success = test_migration_tool_launch()
    print(f"测试结果: {'成功' if success else '失败'}")
    
    # 保持脚本运行，直到用户输入
    input("按Enter键退出...") 