import pandas as pd
import os
import sys
from datetime import datetime
import shutil
import subprocess

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.core.db_manager import DatabaseManager

def read_csv_auto_encoding(path):
    """尝试使用不同的编码读取CSV文件"""
    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            return pd.read_csv(path, encoding='gbk')
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding='utf-8-sig')

def backup_database():
    """备份数据库"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database_backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    
    try:
        # 使用与DatabaseManager.get_connection相同的配置
        host = "sql.didiba.uk"
        port = 33306
        user = "root"
        password = "Cenb1017!@"
        database = "OcrTrade"
        
        # 使用subprocess.Popen代替os.system以获得更好的错误处理
        mysqldump_cmd = [
            "mysqldump",
            "-h", host,
            "-P", str(port),
            "-u", user,
            f"-p{password}",
            "--set-charset",
            "--routines",
            "--triggers",
            "--single-transaction",
            database
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
                    return backup_database_python()
                
                return False
        
        # 验证备份文件
        if os.path.exists(backup_file):
            file_size = os.path.getsize(backup_file)
            if file_size == 0:
                print(f"警告: 备份文件大小为0字节，备份可能失败")
                os.remove(backup_file)  # 删除空文件
                print("将尝试使用纯Python方式备份...")
                return backup_database_python()
            else:
                print(f"数据库已备份到: {backup_file} (大小: {file_size/1024:.1f} KB)")
                return True
        else:
            print(f"备份失败: 无法创建备份文件")
            return False
            
    except Exception as e:
        print(f"备份数据库失败: {e}")
        print("将尝试使用纯Python方式备份...")
        return backup_database_python()
    finally:
        conn.close()

def backup_database_python():
    """使用纯Python方式备份数据库（不依赖mysqldump）"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database_backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
    
    print(f"\n开始使用纯Python方式备份数据库...")
    
    try:
        # 获取数据库连接
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 打开备份文件
        with open(backup_file, 'w', encoding='utf8') as f:
            # 写入文件头
            f.write(f"-- MySQL dump by Python MySQLdb\n")
            f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("SET NAMES utf8mb4;\n")
            f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
            
            # 获取所有表
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            if not tables:
                print(f"警告: 数据库中没有表")
                f.write(f"-- 警告: 数据库中没有表\n")
            
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
        
        # 验证备份文件
        file_size = os.path.getsize(backup_file)
        if file_size == 0:
            print(f"警告: 备份文件大小为0字节，备份可能失败")
            os.remove(backup_file)  # 删除空文件
            return False
        else:
            print(f"数据库已备份到: {backup_file} (大小: {file_size/1024:.1f} KB)")
            return True
            
    except Exception as e:
        print(f"纯Python方式备份失败: {e}")
        if os.path.exists(backup_file):
            os.remove(backup_file)  # 删除可能的部分备份文件
        return False
    finally:
        cursor.close()
        conn.close()

def clear_stock_data():
    """清空库存相关表"""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 清空库存相关表
        tables = ['stock_in', 'stock_out']
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()
        print("已清空原有库存数据")
        return True
    except Exception as e:
        print(f"清空数据失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def import_stock_in(df, progress_callback=None):
    """导入入库数据"""
    try:
        db_manager = DatabaseManager()
        
        # 检查必要的列是否存在
        required_columns = ['物品', '入库数量', '入库花费', '入库均价']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"CSV文件缺少必要的列: {', '.join(missing_columns)}")
            return False
        
        # 导入数据
        success_count = 0
        error_count = 0
        
        for idx, (_, row) in enumerate(df.iterrows()):
            try:
                # 如果提供了回调函数，调用它更新进度
                if progress_callback:
                    progress_callback(idx + 1)
                    
                note = row['备注'] if '备注' in row and pd.notna(row['备注']) else ''
                transaction_time = row.get('当前时间', row.get('时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
                # 处理可能的日期格式问题
                if isinstance(transaction_time, str):
                    try:
                        # 尝试解析日期格式
                        transaction_time = pd.to_datetime(transaction_time)
                    except:
                        # 如果解析失败，使用当前时间
                        transaction_time = datetime.now()
                
                db_manager.save_stock_in({
                    'item_name': str(row['物品']),
                    'transaction_time': transaction_time,
                    'quantity': int(float(row['入库数量'])) if pd.notna(row['入库数量']) else 0,
                    'cost': int(float(row['入库花费'])) if pd.notna(row['入库花费']) else 0,
                    'avg_cost': int(float(row['入库均价'])) if pd.notna(row['入库均价']) else 0,
                    'note': note
                })
                success_count += 1
            except Exception as e:
                print(f"导入入库记录失败: {e}, 行: {row.to_dict()}")
                error_count += 1
        
        print(f"入库数据导入完成！成功: {success_count}, 失败: {error_count}")
        return True
    except Exception as e:
        print(f"导入入库数据失败: {e}")
        return False

def import_stock_out(df, progress_callback=None):
    """导入出库数据"""
    try:
        db_manager = DatabaseManager()
        
        # 检查必要的列是否存在
        required_columns = ['物品', '出库数量', '出库单价', '手续费']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"CSV文件缺少必要的列: {', '.join(missing_columns)}")
            return False
        
        # 导入数据
        success_count = 0
        error_count = 0
        
        def safe_int(val):
            try:
                return int(float(val)) if pd.notna(val) else 0
            except Exception:
                return 0
        
        for idx, (_, row) in enumerate(df.iterrows()):
            try:
                # 如果提供了回调函数，调用它更新进度
                if progress_callback:
                    progress_callback(idx + 1)
                
                note = row['备注'] if '备注' in row and pd.notna(row['备注']) else ''
                transaction_time = row.get('时间', row.get('当前时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
                # 处理可能的日期格式问题
                if isinstance(transaction_time, str):
                    try:
                        # 尝试解析日期格式
                        transaction_time = pd.to_datetime(transaction_time)
                    except:
                        # 如果解析失败，使用当前时间
                        transaction_time = datetime.now()
                
                # 计算总金额
                quantity = safe_int(row['出库数量'])
                unit_price = safe_int(row['出库单价'])
                fee = safe_int(row['手续费'])
                deposit = safe_int(row.get('押金', 0))
                total_amount = quantity * unit_price - fee + deposit
                
                # 如果CSV中有总金额列，则使用该值
                if '总金额' in row and pd.notna(row['总金额']):
                    total_amount = safe_int(row['总金额'])
                
                db_manager.save_stock_out({
                    'item_name': str(row['物品']),
                    'transaction_time': transaction_time,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'fee': fee,
                    'deposit': deposit,
                    'total_amount': total_amount,
                    'note': note
                })
                success_count += 1
            except Exception as e:
                print(f"导入出库记录失败: {e}, 行: {row.to_dict()}")
                error_count += 1
        
        print(f"出库数据导入完成！成功: {success_count}, 失败: {error_count}")
        return True
    except Exception as e:
        print(f"导入出库数据失败: {e}")
        return False

def main():
    """主函数"""
    # 默认文件路径
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'import')
    stock_in_path = os.path.join(data_dir, 'stock_in.csv')
    stock_out_path = os.path.join(data_dir, 'stock_out.csv')
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        stock_in_path = sys.argv[1]
    if len(sys.argv) > 2:
        stock_out_path = sys.argv[2]
    
    # 确保目录存在
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 检查文件是否存在
    if not os.path.exists(stock_in_path) and not os.path.exists(stock_out_path):
        print(f"错误: 入库文件 '{stock_in_path}' 和出库文件 '{stock_out_path}' 都不存在！")
        print(f"请将入库数据CSV文件命名为'stock_in.csv'，出库数据CSV文件命名为'stock_out.csv'，")
        print(f"并放置在 '{data_dir}' 目录下，或者通过命令行参数指定文件路径。")
        return False
    
    # 询问用户确认
    print("警告: 此操作将清空当前所有库存数据，并导入新数据。")
    confirm = input("是否继续? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return False
    
    # 备份数据库
    print("正在备份数据库...")
    if not backup_database():
        print("数据库备份失败，操作已取消")
        return False
    
    # 清空库存数据
    print("正在清空原有库存数据...")
    if not clear_stock_data():
        print("清空数据失败，操作已取消")
        return False
    
    # 导入数据
    success = True
    if os.path.exists(stock_in_path):
        print(f"正在导入入库数据: {stock_in_path}")
        df = read_csv_auto_encoding(stock_in_path)
        if df is None or df.empty:
            print(f"无法读取入库文件或文件为空: {stock_in_path}")
            success = False
        else:
            if not import_stock_in(df):
                success = False
    
    if os.path.exists(stock_out_path):
        print(f"正在导入出库数据: {stock_out_path}")
        df = read_csv_auto_encoding(stock_out_path)
        if df is None or df.empty:
            print(f"无法读取出库文件或文件为空: {stock_out_path}")
            success = False
        else:
            if not import_stock_out(df):
                success = False
    
    if success:
        print("数据导入完成！")
    else:
        print("数据导入过程中出现错误，请检查日志。")
    
    return success

if __name__ == '__main__':
    main() 