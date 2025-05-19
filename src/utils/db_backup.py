import os
import time
import shutil
import datetime
import logging
import threading
import subprocess
from pathlib import Path
import MySQLdb
from src.utils.email_sender import QQEmailSender
from src.core.db_manager import DatabaseManager

class DatabaseBackup:
    """数据库备份工具"""
    
    def __init__(self, backup_dir=None):
        """初始化备份工具
        
        Args:
            backup_dir: 备份文件存储目录，默认为项目根目录下的database_backups
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        
        # 设置备份目录
        if backup_dir is None:
            self.backup_dir = os.path.join(os.getcwd(), "database_backups")
        else:
            self.backup_dir = backup_dir
            
        # 确保备份目录存在
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            self.logger.info(f"已创建备份目录: {self.backup_dir}")
    
    def backup_database(self, send_email=True):
        """备份数据库
        
        Args:
            send_email: 是否发送邮件通知
            
        Returns:
            tuple: (成功标志, 消息, 备份文件路径)
        """
        start_time = time.time()
        self.logger.info("开始备份数据库...")
        
        # 获取数据库配置
        db_config = self.db_manager.config
        
        # 生成备份文件名，使用当前时间
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # 首先尝试使用mysqldump命令备份
            cmd = [
                "mysqldump",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--user={db_config['user']}",
                f"--password={db_config['passwd']}",
                "--hex-blob",
                "--single-transaction",
                "--set-charset",
                "--triggers",
                "--routines",
                "--events",
                db_config['db']
            ]
            
            # 执行备份命令并将输出重定向到文件
            with open(backup_path, 'w', encoding='utf-8') as f:
                self.logger.info("尝试使用mysqldump命令备份")
                try:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, timeout=60)
                    if result.returncode == 0:
                        self.logger.info("mysqldump备份成功")
                    else:
                        raise Exception(f"mysqldump执行失败: {result.stderr}")
                except FileNotFoundError:
                    self.logger.warning("系统找不到mysqldump命令，将使用纯Python方式备份")
                    # 删除空文件，重新创建
                    f.close()
                    os.remove(backup_path)
                    # 使用Python方式备份
                    return self._backup_database_using_python(backup_path, send_email)
                except Exception as e:
                    self.logger.warning(f"mysqldump执行异常: {str(e)}")
                    # 删除可能的不完整文件
                    f.close()
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    # 使用Python方式备份
                    return self._backup_database_using_python(backup_path, send_email)
            
            # 验证备份文件是否存在且大小大于0
            if not os.path.exists(backup_path) or os.path.getsize(backup_path) == 0:
                self.logger.warning("备份文件创建失败或为空，将使用纯Python方式备份")
                # 使用Python方式备份
                return self._backup_database_using_python(backup_path, send_email)
            
            # 计算文件大小
            file_size_bytes = os.path.getsize(backup_path)
            file_size = self._format_size(file_size_bytes)
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            
            success_msg = f"数据库备份成功! 耗时: {elapsed_time:.2f}秒, 大小: {file_size}"
            self.logger.info(success_msg)
            
            # 发送邮件通知
            if send_email:
                self._send_backup_notification(backup_filename, backup_path, file_size_bytes)
            
            return True, success_msg, backup_path
            
        except Exception as e:
            error_msg = f"备份数据库时发生错误: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.logger.info("尝试使用纯Python方式备份")
            # 尝试使用Python方式备份
            return self._backup_database_using_python(backup_path, send_email)
    
    def _backup_database_using_python(self, backup_path, send_email=True):
        """使用纯Python方式备份数据库
        
        Args:
            backup_path: 备份文件路径
            send_email: 是否发送邮件通知
            
        Returns:
            tuple: (成功标志, 消息, 备份文件路径)
        """
        start_time = time.time()
        self.logger.info("开始使用纯Python方式备份数据库...")
        
        # 获取数据库配置
        db_config = self.db_manager.config
        
        try:
            # 连接数据库
            conn = MySQLdb.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['user'],
                passwd=db_config['passwd'],
                db=db_config['db'],
                charset=db_config['charset']
            )
            
            cursor = conn.cursor()
            
            # 打开文件用于写入SQL
            with open(backup_path, 'w', encoding='utf-8') as f:
                # 写入文件头
                f.write(f"-- GameTrad 数据库备份\n")
                f.write(f"-- 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- 数据库: {db_config['db']}\n\n")
                
                f.write("SET FOREIGN_KEY_CHECKS=0;\n")
                f.write("SET SQL_MODE = \"NO_AUTO_VALUE_ON_ZERO\";\n")
                f.write("SET AUTOCOMMIT = 0;\n")
                f.write("START TRANSACTION;\n")
                f.write(f"SET time_zone = \"+00:00\";\n\n")
                
                # 获取所有表
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                # 处理每个表
                for table_row in tables:
                    table_name = table_row[0]
                    self.logger.info(f"正在备份表: {table_name}")
                    
                    # 获取创建表的语句
                    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                    create_table = cursor.fetchone()[1]
                    f.write(f"\n--\n-- 表结构 `{table_name}`\n--\n\n")
                    f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                    f.write(f"{create_table};\n\n")
                    
                    # 获取表数据
                    cursor.execute(f"SELECT * FROM `{table_name}`")
                    rows = cursor.fetchall()
                    
                    if rows:
                        f.write(f"--\n-- 转存表中的数据 `{table_name}`\n--\n\n")
                        
                        # 获取列名
                        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
                        columns = [column[0] for column in cursor.fetchall()]
                        columns_str = ", ".join(f"`{column}`" for column in columns)
                        
                        # 分批写入INSERT语句，每次最多1000行
                        batch_size = 1000
                        total_rows = len(rows)
                        
                        for i in range(0, total_rows, batch_size):
                            batch = rows[i:i+batch_size]
                            values_list = []
                            
                            for row in batch:
                                values = []
                                for value in row:
                                    if value is None:
                                        values.append("NULL")
                                    elif isinstance(value, (int, float)):
                                        values.append(str(value))
                                    elif isinstance(value, datetime.datetime):
                                        values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
                                    elif isinstance(value, datetime.date):
                                        values.append(f"'{value.strftime('%Y-%m-%d')}'")
                                    elif isinstance(value, bytes):
                                        hex_value = value.hex()
                                        values.append(f"x'{hex_value}'")
                                    else:
                                        # 处理字符串，转义单引号
                                        escaped_value = str(value).replace("'", "''")
                                        values.append(f"'{escaped_value}'")
                                
                                values_str = ", ".join(values)
                                values_list.append(f"({values_str})")
                            
                            # 写入INSERT语句
                            values_block = ",\n".join(values_list)
                            f.write(f"INSERT INTO `{table_name}` ({columns_str}) VALUES\n{values_block};\n\n")
                
                f.write("SET FOREIGN_KEY_CHECKS=1;\n")
                f.write("COMMIT;\n")
            
            # 关闭数据库连接
            cursor.close()
            conn.close()
            
            # 验证备份文件
            if not os.path.exists(backup_path) or os.path.getsize(backup_path) == 0:
                error_msg = "备份文件创建失败或为空"
                self.logger.error(error_msg)
                return False, error_msg, None
            
            # 计算文件大小
            file_size_bytes = os.path.getsize(backup_path)
            file_size = self._format_size(file_size_bytes)
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            
            success_msg = f"数据库备份成功(Python方式)! 耗时: {elapsed_time:.2f}秒, 大小: {file_size}"
            self.logger.info(success_msg)
            
            # 提取文件名
            backup_filename = os.path.basename(backup_path)
            
            # 发送邮件通知
            if send_email:
                self._send_backup_notification(backup_filename, backup_path, file_size_bytes)
            
            return True, success_msg, backup_path
            
        except Exception as e:
            error_msg = f"使用Python方式备份数据库时发生错误: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            # 删除可能存在的不完整备份文件
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except:
                    pass
                
            return False, error_msg, None
    
    def restore_database(self, backup_file):
        """从备份文件恢复数据库
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            tuple: (成功标志, 消息)
        """
        self.logger.info(f"开始从备份文件恢复数据库: {backup_file}")
        
        if not os.path.exists(backup_file):
            error_msg = f"备份文件不存在: {backup_file}"
            self.logger.error(error_msg)
            return False, error_msg
        
        # 获取数据库配置
        db_config = self.db_manager.config
        
        try:
            # 首先尝试使用mysql命令恢复
            cmd = [
                "mysql",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--user={db_config['user']}",
                f"--password={db_config['passwd']}",
                db_config['db']
            ]
            
            # 从文件读取SQL并通过管道传递给mysql命令
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True, timeout=60)
                    
                if result.returncode == 0:
                    success_msg = "数据库恢复成功!"
                    self.logger.info(success_msg)
                    return True, success_msg
                else:
                    error_msg = f"恢复失败: {result.stderr}"
                    self.logger.error(error_msg)
                    # 如果mysql命令失败，尝试使用纯Python方式恢复
                    self.logger.info("尝试使用纯Python方式恢复数据库")
                    return self._restore_database_using_python(backup_file)
            except FileNotFoundError:
                self.logger.warning("系统找不到mysql命令，将使用纯Python方式恢复")
                return self._restore_database_using_python(backup_file)
            except Exception as e:
                self.logger.error(f"使用mysql命令恢复失败: {str(e)}", exc_info=True)
                self.logger.info("尝试使用纯Python方式恢复数据库")
                return self._restore_database_using_python(backup_file)
            
        except Exception as e:
            error_msg = f"恢复数据库时发生错误: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def _restore_database_using_python(self, backup_file):
        """使用纯Python方式恢复数据库
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            tuple: (成功标志, 消息)
        """
        self.logger.info(f"开始使用纯Python方式恢复数据库: {backup_file}")
        
        # 获取数据库配置
        db_config = self.db_manager.config
        
        try:
            # 连接数据库
            conn = MySQLdb.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['user'],
                passwd=db_config['passwd'],
                db=db_config['db'],
                charset=db_config['charset']
            )
            
            cursor = conn.cursor()
            
            # 读取SQL文件内容
            with open(backup_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句（按分号分割，但跳过字符串中的分号）
            statements = []
            current_statement = ""
            in_string = False
            escape_char = False
            
            for char in sql_content:
                if escape_char:
                    current_statement += char
                    escape_char = False
                elif char == '\\':
                    current_statement += char
                    escape_char = True
                elif char == "'" and not in_string:
                    current_statement += char
                    in_string = True
                elif char == "'" and in_string:
                    current_statement += char
                    in_string = False
                elif char == ';' and not in_string:
                    current_statement += char
                    statements.append(current_statement.strip())
                    current_statement = ""
                else:
                    current_statement += char
            
            if current_statement.strip():
                statements.append(current_statement.strip())
            
            # 执行SQL语句
            for statement in statements:
                if statement and not statement.startswith('--'):
                    cursor.execute(statement)
            
            # 提交事务
            conn.commit()
            
            # 关闭连接
            cursor.close()
            conn.close()
            
            success_msg = "数据库恢复成功(Python方式)!"
            self.logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"使用Python方式恢复数据库时发生错误: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def list_backups(self):
        """列出所有备份文件
        
        Returns:
            list: 备份文件信息列表，每项包含(文件名, 备份时间, 文件大小, 文件路径)
        """
        backups = []
        
        try:
            # 确保目录存在
            if not os.path.exists(self.backup_dir):
                return []
                
            # 遍历备份目录
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("backup_") and filename.endswith(".sql"):
                    file_path = os.path.join(self.backup_dir, filename)
                    # 获取文件大小
                    size_bytes = os.path.getsize(file_path)
                    size_str = self._format_size(size_bytes)
                    
                    # 从文件名解析备份时间
                    try:
                        time_part = filename.replace("backup_", "").replace(".sql", "")
                        backup_time = datetime.datetime.strptime(time_part, '%Y%m%d_%H%M%S')
                        time_str = backup_time.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        time_str = "未知时间"
                    
                    backups.append({
                        "filename": filename,
                        "time": time_str,
                        "size": size_str,
                        "size_bytes": size_bytes,
                        "path": file_path
                    })
            
            # 按时间排序，最新的在前
            backups.sort(key=lambda x: x["filename"], reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"列出备份文件时发生错误: {e}", exc_info=True)
            return []
    
    def delete_backup(self, backup_file):
        """删除备份文件
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            tuple: (成功标志, 消息)
        """
        if not os.path.exists(backup_file):
            return False, "备份文件不存在"
            
        try:
            os.remove(backup_file)
            return True, f"已删除备份文件: {os.path.basename(backup_file)}"
        except Exception as e:
            error_msg = f"删除备份文件失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def auto_delete_old_backups(self, keep_days=30):
        """自动删除过旧的备份文件
        
        Args:
            keep_days: 保留天数，默认30天
            
        Returns:
            tuple: (删除文件数, 删除文件列表)
        """
        deleted_count = 0
        deleted_files = []
        
        try:
            # 获取所有备份文件
            backups = self.list_backups()
            
            # 计算截止日期
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
            
            for backup in backups:
                try:
                    # 解析备份文件的时间
                    filename = backup["filename"]
                    time_part = filename.replace("backup_", "").replace(".sql", "")
                    file_time = datetime.datetime.strptime(time_part, '%Y%m%d_%H%M%S')
                    
                    # 如果文件时间早于截止日期，则删除
                    if file_time < cutoff_date:
                        file_path = backup["path"]
                        success, _ = self.delete_backup(file_path)
                        if success:
                            deleted_count += 1
                            deleted_files.append(filename)
                except Exception as e:
                    self.logger.error(f"处理备份文件时出错: {str(e)}", exc_info=True)
                    continue
            
            return deleted_count, deleted_files
            
        except Exception as e:
            self.logger.error(f"自动删除旧备份文件时出错: {str(e)}", exc_info=True)
            return 0, []
    
    def _format_size(self, size_bytes):
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
    
    def _send_backup_notification(self, filename, filepath, size_bytes):
        """发送备份完成通知邮件
        
        Args:
            filename: 备份文件名
            filepath: 备份文件路径
            size_bytes: 文件大小(字节)
        """
        try:
            # 导入邮件发送器
            email_sender = QQEmailSender()
            
            # 如果邮件功能未启用，直接返回
            if not email_sender.config["enabled"]:
                self.logger.info("邮件功能未启用，跳过发送备份通知")
                return
            
            # 准备邮件内容
            context = {
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "filename": filename,
                "path": filepath,
                "size": self._format_size(size_bytes)
            }
            
            # 发送模板邮件
            email_sender.send_template_email(
                template_name="backup_success",
                context=context
            )
            
            self.logger.info(f"已发送备份完成通知邮件")
            
        except Exception as e:
            self.logger.error(f"发送备份通知邮件失败: {str(e)}", exc_info=True)

def backup_database_and_notify():
    """执行备份操作并发送通知（可用于定时任务）"""
    backup_tool = DatabaseBackup()
    success, message, backup_path = backup_tool.backup_database(send_email=True)
    if success:
        backup_tool.auto_delete_old_backups(keep_days=30)
    return success, message, backup_path 