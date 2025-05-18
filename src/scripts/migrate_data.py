import MySQLdb
from datetime import datetime
import sys
import os
import shutil
from tqdm import tqdm
import json
import subprocess
import shlex

class DataMigrator:
    def __init__(self):
        """初始化迁移器，但不创建连接"""
        # 创建备份目录
        self.backup_dir = os.path.join("data", "database_backups")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        self.local_conn = None
        self.remote_conn = None
        self.local_cursor = None
        self.remote_cursor = None

    def connect_databases(self, local_db, local_user, local_pass, remote_db, remote_ip, remote_user, remote_pass, remote_port=33306, local_host="localhost", local_port=3306):
        """连接到本地和远程数据库"""
        try:
            # 连接本地数据库
            self.local_conn = MySQLdb.connect(
                host=local_host,
                port=local_port,
                user=local_user,
                passwd=local_pass,
                db=local_db,
                charset="utf8mb4"
            )
            self.local_cursor = self.local_conn.cursor()
            print(f"源数据库连接成功 ({local_host}:{local_port})")
            
            # 尝试连接远程数据库
            try:
                self.remote_conn = MySQLdb.connect(
                    host=remote_ip,
                    port=remote_port,
                    user=remote_user,
                    passwd=remote_pass,
                    charset="utf8mb4"
                )
                self.remote_cursor = self.remote_conn.cursor()
                print(f"目标数据库连接成功 ({remote_ip}:{remote_port})")
                
                # 检查数据库是否存在，不存在则创建
                self.remote_cursor.execute(f"SHOW DATABASES LIKE '{remote_db}'")
                if not self.remote_cursor.fetchone():
                    print(f"远程数据库 {remote_db} 不存在，正在创建...")
                    self.remote_cursor.execute(f"CREATE DATABASE `{remote_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    self.remote_conn.commit()
                
                # 切换到指定数据库
                self.remote_conn.select_db(remote_db)
                print(f"成功切换到数据库: {remote_db}")
                
                return True
            except Exception as e:
                print(f"目标数据库连接或创建失败: {e}")
                raise
        except Exception as e:
            print(f"源数据库连接失败: {e}")
            raise

    def sync_table_structure(self, table_name):
        """同步表结构"""
        print(f"\n同步表 {table_name} 的结构...")
        
        # 获取本地表结构
        self.local_cursor.execute(f"SHOW CREATE TABLE {table_name}")
        local_create_table = self.local_cursor.fetchone()[1]
        
        # 检查远程表是否存在
        self.remote_cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not self.remote_cursor.fetchone():
            # 如果表不存在，直接创建
            print(f"远程数据库不存在表 {table_name}，正在创建...")
            self.remote_cursor.execute(local_create_table)
            self.remote_conn.commit()
            return True
            
        # 获取远程表结构
        self.remote_cursor.execute(f"SHOW CREATE TABLE {table_name}")
        remote_create_table = self.remote_cursor.fetchone()[1]
        
        # 如果表结构不同，先删除远程表再创建
        if local_create_table != remote_create_table:
            print(f"表 {table_name} 结构不一致，正在更新...")
            self.remote_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.remote_cursor.execute(local_create_table)
            self.remote_conn.commit()
            return True
            
        print(f"表 {table_name} 结构已同步")
        return True

    def backup_database(self, remote_ip, remote_user, remote_pass, remote_db, remote_port=33306, backup_dir=None):
        """备份远程数据库
        
        Args:
            remote_ip: 远程数据库IP
            remote_user: 远程数据库用户名
            remote_pass: 远程数据库密码
            remote_db: 远程数据库名
            remote_port: 远程数据库端口，默认33306
            backup_dir: 自定义备份目录，如果为None则使用默认目录
            
        Returns:
            str: 备份文件路径，如果备份失败则返回None
        """
        # 使用自定义备份目录或默认目录
        target_backup_dir = backup_dir if backup_dir else self.backup_dir
        
        # 确保备份目录存在
        if not os.path.exists(target_backup_dir):
            try:
                os.makedirs(target_backup_dir)
                print(f"创建备份目录: {target_backup_dir}")
            except Exception as e:
                print(f"创建备份目录失败: {e}")
                return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(target_backup_dir, f"backup_{remote_db}_{timestamp}.sql")
        
        print(f"\n开始备份远程数据库 {remote_db}...")
        try:
            # 构建mysqldump命令
            # 注意：在Windows中，不能使用shlex.quote处理密码，因为它会添加单引号，而Windows命令行不支持
            mysqldump_cmd = [
                "mysqldump",
                "-h", remote_ip,
                "-P", str(remote_port),
                "-u", remote_user,
                f"-p{remote_pass}",
                "--set-charset",
                "--routines",
                "--triggers",
                "--single-transaction",
                remote_db
            ]
            
            # 执行备份命令
            with open(backup_file, 'w', encoding='utf8') as f:
                process = subprocess.Popen(
                    mysqldump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                _, stderr = process.communicate()
                
                # 检查命令执行结果
                if process.returncode != 0:
                    print(f"mysqldump执行失败，错误码: {process.returncode}")
                    print(f"错误信息: {stderr}")
                    
                    # 检查是否是mysqldump命令不存在
                    if "不是内部或外部命令" in stderr or "command not found" in stderr:
                        print("mysqldump命令不可用，请确保MySQL客户端工具已安装并添加到PATH中")
                        print("将尝试使用纯Python方式备份...")
                        return self.backup_database_python(remote_ip, remote_user, remote_pass, remote_db, remote_port, backup_dir)
                    
                    return None
            
            # 验证备份文件
            if os.path.exists(backup_file):
                file_size = os.path.getsize(backup_file)
                if file_size == 0:
                    print(f"警告: 备份文件大小为0字节，备份可能失败")
                    print("将尝试使用纯Python方式备份...")
                    os.remove(backup_file)  # 删除空文件
                    return self.backup_database_python(remote_ip, remote_user, remote_pass, remote_db, remote_port, backup_dir)
                else:
                    print(f"数据库已备份到: {backup_file} (大小: {file_size/1024:.1f} KB)")
                    return backup_file
            else:
                print(f"备份失败: 无法创建备份文件")
                return None
                
        except Exception as e:
            print(f"备份失败: {e}")
            print("将尝试使用纯Python方式备份...")
            return self.backup_database_python(remote_ip, remote_user, remote_pass, remote_db, remote_port, backup_dir)

    def verify_data(self, table_name, local_rows, remote_rows):
        """验证数据完整性"""
        print(f"\n验证表 {table_name} 的数据完整性...")
        
        # 验证记录数
        if len(local_rows) != len(remote_rows):
            print(f"警告: 表 {table_name} 记录数不匹配")
            print(f"本地记录数: {len(local_rows)}")
            print(f"远程记录数: {len(remote_rows)}")
            return False
            
        # 验证数据内容
        for i, (local_row, remote_row) in enumerate(zip(local_rows, remote_rows)):
            if local_row != remote_row:
                print(f"警告: 表 {table_name} 第 {i+1} 行数据不匹配")
                print(f"本地数据: {local_row}")
                print(f"远程数据: {remote_row}")
                return False
                
        print(f"表 {table_name} 数据验证通过")
        return True

    def migrate_table(self, table_name):
        """迁移单个表的数据"""
        print(f"\n开始迁移表: {table_name}")
        
        # 先同步表结构
        if not self.sync_table_structure(table_name):
            print(f"同步表 {table_name} 结构失败，跳过迁移")
            return
        
        # 获取表结构
        self.local_cursor.execute(f"DESCRIBE {table_name}")
        columns = [column[0] for column in self.local_cursor.fetchall()]
        
        # 获取本地数据
        self.local_cursor.execute(f"SELECT * FROM {table_name}")
        local_rows = self.local_cursor.fetchall()
        
        if not local_rows:
            print(f"表 {table_name} 没有数据需要迁移")
            return
        
        # 先清空远程表中的数据
        self.remote_cursor.execute(f"TRUNCATE TABLE {table_name}")
        self.remote_conn.commit()
        print(f"已清空远程表 {table_name} 中的数据")
        
        # 构建插入语句
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # 迁移数据
        try:
            # 使用tqdm显示进度条
            for row in tqdm(local_rows, desc=f"迁移 {table_name}", unit="行"):
                self.remote_cursor.execute(insert_query, row)
            self.remote_conn.commit()
            
            # 验证数据
            self.remote_cursor.execute(f"SELECT * FROM {table_name}")
            remote_rows = self.remote_cursor.fetchall()
            if self.verify_data(table_name, local_rows, remote_rows):
                print(f"成功迁移并验证 {len(local_rows)} 条数据到表 {table_name}")
            else:
                print(f"警告: 表 {table_name} 数据验证未通过")
                
        except Exception as e:
            self.remote_conn.rollback()
            print(f"迁移表 {table_name} 时出错: {e}")
            raise

    def migrate_all_tables(self, local_db, local_user, local_pass, remote_db, remote_ip, remote_user, remote_pass, selected_tables=None, local_host="localhost", local_port=3306, remote_port=33306, backup_dir=None):
        """迁移所有选中的表"""
        print("开始数据迁移...")
        print(f"迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 连接数据库
        try:
            self.connect_databases(local_db, local_user, local_pass, remote_db, remote_ip, remote_user, remote_pass, remote_port=remote_port, local_host=local_host, local_port=local_port)
        except Exception as e:
            print(f"连接数据库失败，无法继续迁移: {e}")
            return False
        
        # 获取默认表列表
        if not selected_tables:
            selected_tables = [
                'stock_in',
                'stock_out',
                'trade_monitor',
                'inventory',
                'operation_logs',
                'item_dict',
                'silver_monitor'
            ]
        
        # 先备份远程数据库
        backup_file = self.backup_database(remote_ip, remote_user, remote_pass, remote_db, remote_port=remote_port, backup_dir=backup_dir)
        if not backup_file:
            print("警告: 备份失败，是否继续迁移？(y/n)")
            if input().lower() != 'y':
                print("迁移已取消")
                self.close_connections()
                return False
        
        migrated_tables = []
        try:
            # 使用tqdm显示总体进度
            for table in tqdm(selected_tables, desc="总体进度", unit="表"):
                self.migrate_table(table)
                migrated_tables.append(table)
            
            print("\n所有数据迁移完成！")
            
            # 保存迁移日志
            self.save_migration_log(migrated_tables)
            
            self.close_connections()
            return True
            
        except Exception as e:
            print(f"\n迁移过程中出错: {e}")
            self.close_connections()
            return False

    def save_migration_log(self, tables):
        """保存迁移日志"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.backup_dir, f"migration_log_{timestamp}.json")
        
        log_data = {
            "timestamp": timestamp,
            "tables": tables,
            "status": "success"
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"迁移日志已保存到: {log_file}")

    def close_connections(self):
        """关闭数据库连接"""
        if self.local_cursor:
        self.local_cursor.close()
        if self.remote_cursor:
        self.remote_cursor.close()
        if self.local_conn:
        self.local_conn.close()
        if self.remote_conn:
        self.remote_conn.close()
        print("已关闭所有数据库连接")

    def test_local_connection(self, db_name, user, passwd):
        """测试本地数据库连接"""
        try:
            conn = MySQLdb.connect(
                host="localhost",
                user=user,
                passwd=passwd,
                db=db_name,
                charset="utf8mb4"
            )
            conn.close()
            return True
        except Exception as e:
            print(f"本地数据库连接失败: {e}")
            return False

    def test_remote_connection(self, db_name, db_ip, user, passwd, port=33306):
        """测试远程数据库连接"""
        try:
            # 先尝试连接到MySQL服务器（不指定数据库）
            conn = MySQLdb.connect(
                host=db_ip,
                port=port,
                user=user,
                passwd=passwd,
                charset="utf8mb4",
                connect_timeout=5
            )
            
            # 检查数据库是否存在
            cursor = conn.cursor()
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
            database_exists = cursor.fetchone() is not None
            
            if not database_exists:
                print(f"数据库 {db_name} 不存在，将在迁移时自动创建")
            else:
                print(f"数据库 {db_name} 已存在")
                
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"远程数据库连接失败: {e}")
            return False

    def list_reports(self):
        """列出所有迁移报告"""
        reports = []
        if os.path.exists(self.backup_dir):
        for file in os.listdir(self.backup_dir):
                if file.endswith('.json'):
                    with open(os.path.join(self.backup_dir, file), 'r', encoding='utf-8') as f:
                try:
                            data = json.load(f)
                reports.append({
                                'file': file,
                                'timestamp': data.get('timestamp', ''),
                                'status': data.get('status', ''),
                                'tables': data.get('tables', [])
                            })
                        except json.JSONDecodeError:
                            pass
        return reports

    def restore_database(self, backup_file, db_ip, user, passwd, db_name, port=33306, backup_dir=None):
        """从备份文件恢复数据库
        
        Args:
            backup_file: 备份文件名
            db_ip: 数据库IP
            user: 数据库用户名
            passwd: 数据库密码
            db_name: 数据库名
            port: 数据库端口，默认33306
            backup_dir: 自定义备份目录，如果为None则使用默认目录
            
        Returns:
            bool: 恢复是否成功
        """
        # 使用自定义备份目录或默认目录
        target_backup_dir = backup_dir if backup_dir else self.backup_dir
        
        backup_path = os.path.join(target_backup_dir, backup_file)
        if not os.path.exists(backup_path):
            print(f"备份文件不存在: {backup_path}")
            return False
        
        try:
            # 确保数据库存在
            conn = MySQLdb.connect(
                host=db_ip,
                port=port,
                user=user,
                passwd=passwd,
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
            conn.commit()
            cursor.close()
            conn.close()
            
            # 执行恢复命令
            result = os.system(f"mysql -h {db_ip} -P {port} -u {user} -p{passwd} {db_name} < {backup_path}")
            if result == 0:
                print(f"数据库恢复成功: {backup_path} -> {db_name}")
            return True
            else:
                print(f"数据库恢复失败，错误代码: {result}")
                return False
        except Exception as e:
            print(f"恢复数据库时出错: {e}")
            return False

    def manual_backup(self, db_name, db_ip, user, passwd, port=33306, backup_dir=None):
        """手动备份数据库，不进行数据迁移
        
        Args:
            db_name: 数据库名
            db_ip: 数据库IP
            user: 数据库用户名
            passwd: 数据库密码
            port: 数据库端口，默认33306
            backup_dir: 自定义备份目录，如果为None则使用默认目录
            
        Returns:
            str: 备份文件路径，如果备份失败则返回None
        """
        try:
            # 尝试连接到数据库，确保数据库可访问
            try:
                conn = MySQLdb.connect(
                    host=db_ip,
                    port=port,
                    user=user,
                    passwd=passwd,
                    db=db_name,
                    charset="utf8mb4",
                    connect_timeout=5
                )
                conn.close()
                print(f"成功连接到数据库 {db_name}")
            except Exception as e:
                print(f"无法连接到数据库 {db_name}: {e}")
                # 提供更有用的错误信息
                if "Can't connect to MySQL server" in str(e):
                    print("可能原因: 无法连接到MySQL服务器，请检查网络连接和服务器状态。")
                elif "Access denied" in str(e):
                    print("可能原因: 访问被拒绝，请检查用户名和密码。")
                elif "Unknown database" in str(e):
                    print("可能原因: 数据库不存在，请先创建数据库。")
                return None
            
            # 执行备份
            backup_file = self.backup_database(db_ip, user, passwd, db_name, remote_port=port, backup_dir=backup_dir)
            
            # 验证备份文件
            if backup_file and os.path.exists(backup_file):
                file_size = os.path.getsize(backup_file)
                if file_size == 0:
                    print(f"警告: 备份文件大小为0字节，备份可能失败")
                    # 尝试使用纯Python方式备份
                    print("尝试使用纯Python方式备份...")
                    os.remove(backup_file)  # 删除空文件
                    return self.backup_database_python(db_ip, user, passwd, db_name, remote_port=port, backup_dir=backup_dir)
                
                # 检查文件内容
                try:
                    with open(backup_file, 'r', encoding='utf8') as f:
                        content = f.read(1000)  # 只读取前1000个字符进行检查
                        if not content or content.strip() == "":
                            print(f"警告: 备份文件内容为空，备份可能失败")
                            # 尝试使用纯Python方式备份
                            print("尝试使用纯Python方式备份...")
                            os.remove(backup_file)  # 删除空文件
                            return self.backup_database_python(db_ip, user, passwd, db_name, remote_port=port, backup_dir=backup_dir)
                except Exception as e:
                    print(f"检查备份文件内容时出错: {e}")
            
            return backup_file
        except Exception as e:
            print(f"备份数据库 {db_name} 失败: {e}")
            return None

    def backup_database_python(self, remote_ip, remote_user, remote_pass, remote_db, remote_port=33306, backup_dir=None):
        """使用纯Python方式备份数据库（不依赖mysqldump）
        
        Args:
            remote_ip: 远程数据库IP
            remote_user: 远程数据库用户名
            remote_pass: 远程数据库密码
            remote_db: 远程数据库名
            remote_port: 远程数据库端口，默认33306
            backup_dir: 自定义备份目录，如果为None则使用默认目录
            
        Returns:
            str: 备份文件路径，如果备份失败则返回None
        """
        # 使用自定义备份目录或默认目录
        target_backup_dir = backup_dir if backup_dir else self.backup_dir
        
        # 确保备份目录存在
        if not os.path.exists(target_backup_dir):
            try:
                os.makedirs(target_backup_dir)
                print(f"创建备份目录: {target_backup_dir}")
            except Exception as e:
                print(f"创建备份目录失败: {e}")
                return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(target_backup_dir, f"backup_{remote_db}_{timestamp}.sql")
        
        print(f"\n开始使用纯Python方式备份数据库 {remote_db}...")
        
        try:
            # 连接到数据库
            conn = MySQLdb.connect(
                host=remote_ip,
                port=remote_port,
                user=remote_user,
                passwd=remote_pass,
                db=remote_db,
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            
            # 打开备份文件
            with open(backup_file, 'w', encoding='utf8') as f:
                # 写入文件头
                f.write(f"-- MySQL dump by Python MySQLdb\n")
                f.write(f"-- Database: {remote_db}\n")
                f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("SET NAMES utf8mb4;\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
                
                # 获取所有表
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]
                
                if not tables:
                    print(f"警告: 数据库 {remote_db} 中没有表")
                    f.write(f"-- 警告: 数据库 {remote_db} 中没有表\n")
                
                # 备份每个表
                for table in tables:
                    print(f"备份表: {table}")
                    
                    # 获取表结构
                    cursor.execute(f"SHOW CREATE TABLE `{table}`")
                    create_table = cursor.fetchone()[1]
                    
                    f.write(f"\n-- Table structure for {table}\n")
                    f.write("DROP TABLE IF EXISTS `" + table + "`;\n")
                    f.write(create_table + ";\n\n")
                    
                    # 获取表数据
                    cursor.execute(f"SELECT * FROM `{table}`")
                    rows = cursor.fetchall()
                    
                    if rows:
                        f.write(f"-- Data for {table}\n")
                        f.write("LOCK TABLES `" + table + "` WRITE;\n")
                        
                        # 获取列名
                        cursor.execute(f"DESCRIBE `{table}`")
                        columns = [column[0] for column in cursor.fetchall()]
                        
                        # 构建INSERT语句
                        for row in rows:
                            values = []
                            for value in row:
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, (int, float)):
                                    values.append(str(value))
                                elif isinstance(value, bytes):
                                    values.append("X'" + value.hex() + "'")
                                else:
                                    values.append("'" + str(value).replace("'", "''") + "'")
                                    
                            f.write(f"INSERT INTO `{table}` VALUES ({', '.join(values)});\n")
                        
                        f.write("UNLOCK TABLES;\n\n")
                
                # 写入文件尾
                f.write("SET FOREIGN_KEY_CHECKS=1;\n")
            
            # 关闭连接
            cursor.close()
            conn.close()
            
            # 验证备份文件
            file_size = os.path.getsize(backup_file)
            if file_size == 0:
                print(f"警告: 备份文件大小为0字节，备份可能失败")
                os.remove(backup_file)  # 删除空文件
                return None
            else:
                print(f"数据库已备份到: {backup_file} (大小: {file_size/1024:.1f} KB)")
                return backup_file
                
        except Exception as e:
            print(f"纯Python方式备份失败: {e}")
            if os.path.exists(backup_file):
                os.remove(backup_file)  # 删除可能的部分备份文件
            return None

def main():
    """命令行入口函数"""
    migrator = DataMigrator()
    
    if len(sys.argv) < 2:
        print("用法: python migrate_data.py [command]")
        print("可用命令:")
        print("  test_local - 测试本地数据库连接")
        print("  test_remote - 测试远程数据库连接")
        print("  migrate - 迁移数据")
        print("  list_reports - 列出迁移报告")
        return
    
    command = sys.argv[1]
    
    if command == "test_local":
        migrator.test_local_connection("game_trading", "root", "123456")
    elif command == "test_remote":
        migrator.test_remote_connection("OcrTrade", "sql.didiba.uk", "root", "Cenb1017!@")
    elif command == "migrate":
        migrator.migrate_all_tables("game_trading", "root", "123456", "OcrTrade", "sql.didiba.uk", "root", "Cenb1017!@", selected_tables=None)
    elif command == "list_reports":
        reports = migrator.list_reports()
        for report in reports:
            print(f"{report['file']} - {report['timestamp']} - {report['status']}")
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main() 