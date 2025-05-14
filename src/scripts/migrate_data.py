import MySQLdb
from datetime import datetime
import sys
import os
import shutil
from tqdm import tqdm
import json

class DataMigrator:
    def __init__(self):
        # 本地数据库连接
        self.local_conn = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="123456",
            db="game_trading",
            charset="utf8mb4"
        )
        
        # 远程数据库连接
        self.remote_conn = MySQLdb.connect(
            host="szxz.llwdz.top",
            port=33306,
            user="root",
            passwd="123456",
            db="OcrTrade",
            charset="utf8mb4"
        )
        
        self.local_cursor = self.local_conn.cursor()
        self.remote_cursor = self.remote_conn.cursor()
        
        # 创建备份目录
        self.backup_dir = os.path.join("data", "database_backups")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

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

    def backup_database(self):
        """备份远程数据库"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.sql")
        
        print("\n开始备份远程数据库...")
        try:
            # 使用mysqldump命令备份
            os.system(f"mysqldump -h 192.168.3.22 -u root -p123456 OcrTrade > {backup_file}")
            print(f"数据库已备份到: {backup_file}")
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False

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

    def migrate_all_tables(self, local_db, local_user, local_pass, remote_db, remote_ip, remote_user, remote_pass):
        # 连接本地数据库
        self.local_conn = MySQLdb.connect(
            host="localhost",
            user=local_user,
            passwd=local_pass,
            db=local_db,
            charset="utf8mb4"
        )
        self.local_cursor = self.local_conn.cursor()
        # 连接远程数据库
        self.remote_conn = MySQLdb.connect(
            host=remote_ip,
            user=remote_user,
            passwd=remote_pass,
            db=remote_db,
            charset="utf8mb4"
        )
        self.remote_cursor = self.remote_conn.cursor()
        
        print("开始数据迁移...")
        print(f"迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 先备份远程数据库
        if not self.backup_database():
            print("警告: 备份失败，是否继续迁移？(y/n)")
            if input().lower() != 'y':
                print("迁移已取消")
                return
        
        try:
            # 使用tqdm显示总体进度
            tables = [
                'stock_in',
                'stock_out',
                'trade_monitor',
                'inventory',
                'operation_logs',
                'item_dict',
                'silver_monitor'
            ]
            for table in tqdm(tables, desc="总体进度", unit="表"):
                self.migrate_table(table)
            print("\n所有数据迁移完成！")
            
            # 保存迁移日志
            self.save_migration_log(tables)
            
        except Exception as e:
            print(f"\n迁移过程中出错: {e}")
        finally:
            self.close_connections()

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
        self.local_cursor.close()
        self.remote_cursor.close()
        self.local_conn.close()
        self.remote_conn.close()

    def test_local_connection(self, db_name, user, passwd):
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
        try:
            conn = MySQLdb.connect(
                host=db_ip,
                port=port,
                user=user,
                passwd=passwd,
                db=db_name,
                charset="utf8mb4"
            )
            conn.close()
            return True
        except Exception as e:
            print(f"远程数据库连接失败: {e}")
            return False

    def list_reports(self):
        """列出所有迁移报告文件"""
        reports = []
        if not hasattr(self, 'backup_dir'):
            self.backup_dir = "database_backups"
        if not os.path.exists(self.backup_dir):
            return reports
        for file in os.listdir(self.backup_dir):
            if file.startswith("migration_report_") and file.endswith(".html"):
                file_path = os.path.join(self.backup_dir, file)
                try:
                    time = datetime.strptime(file[16:-5], "%Y%m%d_%H%M%S")
                except Exception:
                    time = datetime.fromtimestamp(os.path.getmtime(file_path))
                reports.append({
                    "file": file,
                    "path": file_path,
                    "time": time
                })
        return sorted(reports, key=lambda x: x["time"], reverse=True)

    def restore_database(self, backup_file, db_ip, user, passwd, db_name):
        """从备份文件恢复数据库"""
        backup_path = os.path.join(self.backup_dir, backup_file)
        if not os.path.exists(backup_path):
            print(f"错误: 备份文件 {backup_path} 不存在")
            return False
        
        print(f"\n开始从 {backup_path} 恢复数据库...")
        try:
            os.system(f"mysql -h {db_ip} -u {user} -p{passwd} {db_name} < {backup_path}")
            print("数据库恢复完成")
            return True
        except Exception as e:
            print(f"恢复失败: {e}")
            return False

def main():
    print("=== 数据迁移工具 ===")
    print("此工具将把本地MySQL数据库(game_trading)的数据迁移到远程服务器(192.168.3.22:OcrTrade)")
    
    try:
        migrator = DataMigrator()
        migrator.migrate_all_tables("game_trading", "root", "123456", "OcrTrade", "192.168.3.22", "root", "123456")
    except Exception as e:
        print(f"迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 