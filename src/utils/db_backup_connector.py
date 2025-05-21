#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库备份连接器
用于通过命令行参数调用数据库备份模块
"""

import os
import sys
import json
import logging
import shutil
import datetime
from pathlib import Path

# 确保当前目录在Python路径中，用于导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# 导入备份模块
from src.utils.db_backup import DatabaseBackup, backup_database_and_notify

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 简单文件备份 - 不依赖MySQL工具，只拷贝数据库文件
def file_backup():
    """
    创建数据库文件的直接备份
    适用于SQLite或直接使用文件的数据库
    
    Returns:
        dict: 包含操作结果的字典
    """
    try:
        # 确定数据库文件位置 (假设是SQLite数据库，位于项目根目录)
        db_dir = root_dir
        db_file = os.path.join(db_dir, "gametrad.db")
        
        # 检查数据库文件是否存在
        if not os.path.exists(db_file):
            return {
                "success": False,
                "message": f"找不到数据库文件: {db_file}"
            }
        
        # 创建备份目录
        backup_dir = os.path.join(root_dir, "database_backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 生成备份文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_file)
        
        # 复制数据库文件
        shutil.copy2(db_file, backup_path)
        
        # 计算文件大小
        size_bytes = os.path.getsize(backup_path)
        size_str = format_size(size_bytes)
        
        return {
            "success": True,
            "message": f"数据库文件备份成功，大小: {size_str}",
            "backup_path": backup_path
        }
    except Exception as e:
        logger.exception("文件备份失败")
        return {
            "success": False,
            "message": f"备份失败: {str(e)}"
        }

# 文件恢复功能
def file_restore(backup_file):
    """
    从备份文件恢复数据库
    
    Args:
        backup_file: 备份文件路径
        
    Returns:
        dict: 包含操作结果的字典
    """
    try:
        # 检查备份文件是否存在
        if not os.path.exists(backup_file):
            return {
                "success": False,
                "message": f"找不到备份文件: {backup_file}"
            }
        
        # 确定数据库文件位置
        db_dir = root_dir
        db_file = os.path.join(db_dir, "gametrad.db")
        
        # 如果当前数据库文件存在，先创建一个临时备份
        temp_backup = None
        if os.path.exists(db_file):
            temp_backup = f"{db_file}.temp_backup"
            shutil.copy2(db_file, temp_backup)
        
        try:
            # 复制备份文件到数据库位置
            shutil.copy2(backup_file, db_file)
            
            # 恢复成功后，删除临时备份
            if temp_backup and os.path.exists(temp_backup):
                os.remove(temp_backup)
                
            return {
                "success": True,
                "message": "数据库文件恢复成功"
            }
        except Exception as e:
            # 如果恢复失败，并且有临时备份，则恢复原始文件
            if temp_backup and os.path.exists(temp_backup):
                shutil.copy2(temp_backup, db_file)
                os.remove(temp_backup)
                
            raise e
    except Exception as e:
        logger.exception("文件恢复失败")
        return {
            "success": False,
            "message": f"恢复失败: {str(e)}"
        }

# 格式化文件大小
def format_size(size_bytes):
    """格式化文件大小
    
    Args:
        size_bytes: 文件大小(字节)
        
    Returns:
        str: 格式化后的大小字符串
    """
    # 转换为KB, MB, GB等更可读的格式
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def main():
    """主函数，处理命令行参数并执行相应操作"""
    
    # 创建备份实例
    backup_tool = DatabaseBackup()
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python db_backup_connector.py [命令] [参数...]")
        print("可用命令:")
        print("  backup         - 执行数据库备份")
        print("  file_backup    - 执行数据库文件备份(仅复制文件，不使用SQL导出)")
        print("  restore <文件名> - 从指定备份文件恢复数据库")
        print("  file_restore <文件名> - 从指定备份文件恢复数据库(直接文件恢复)")
        print("  list_backups    - 列出所有备份文件")
        print("  cleanup <天数>  - 清理指定天数之前的备份")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        # 执行标准SQL备份
        if command == "backup":
            success, message, backup_path = backup_tool.backup_database(send_email=True)
            result = {
                "success": success,
                "message": message,
                "backup_path": backup_path if backup_path else ""
            }
            print(json.dumps(result))
        
        # 执行文件备份
        elif command == "file_backup":
            result = file_backup()
            print(json.dumps(result))
        
        # 标准SQL恢复
        elif command == "restore" and len(sys.argv) >= 3:
            filename = sys.argv[2]
            backup_dir = os.path.join(os.getcwd(), "database_backups")
            backup_path = os.path.join(backup_dir, filename)
            
            success, message = backup_tool.restore_database(backup_path)
            result = {
                "success": success,
                "message": message
            }
            print(json.dumps(result))
        
        # 文件恢复
        elif command == "file_restore" and len(sys.argv) >= 3:
            filename = sys.argv[2]
            backup_dir = os.path.join(os.getcwd(), "database_backups")
            backup_path = os.path.join(backup_dir, filename)
            
            result = file_restore(backup_path)
            print(json.dumps(result))
        
        # 列出备份
        elif command == "list_backups":
            backups = backup_tool.list_backups()
            
            # 转换为JSON可序列化格式
            formatted_backups = []
            for backup in backups:
                formatted_backups.append({
                    "filename": backup["filename"],
                    "created_at": backup["time"],
                    "size": backup["size_bytes"],
                    "size_formatted": backup["size"],
                    "path": backup["path"]
                })
            
            print(json.dumps(formatted_backups))
        
        # 清理旧备份
        elif command == "cleanup" and len(sys.argv) >= 3:
            keep_days = int(sys.argv[2])
            deleted_count, deleted_files = backup_tool.auto_delete_old_backups(keep_days)
            result = {
                "deleted_count": deleted_count,
                "deleted_files": deleted_files
            }
            print(json.dumps(result))
        
        else:
            print(json.dumps({
                "success": False,
                "message": "无效的命令或参数不足"
            }))
    
    except Exception as e:
        logger.exception("执行备份命令时出错")
        print(json.dumps({
            "success": False,
            "message": f"错误: {str(e)}"
        }))

if __name__ == "__main__":
    main() 