import pandas as pd
import os
import sys
from datetime import datetime
import shutil

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
        
        # 使用mysqldump进行备份
        cmd = f'mysqldump -h {host} -P {port} -u {user}'
        if password:
            cmd += f' -p{password}'
        cmd += f' {database} > "{backup_file}"'
        
        os.system(cmd)
        print(f"数据库已备份到: {backup_file}")
        return True
    except Exception as e:
        print(f"备份数据库失败: {e}")
        return False
    finally:
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

def import_stock_in(csv_path):
    """导入入库数据"""
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return False
    
    try:
        df = read_csv_auto_encoding(csv_path)
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
        
        for _, row in df.iterrows():
            try:
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

def import_stock_out(csv_path):
    """导入出库数据"""
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return False
    
    try:
        df = read_csv_auto_encoding(csv_path)
        db_manager = DatabaseManager()
        
        # 检查必要的列是否存在
        required_columns = ['物品', '数量', '单价', '手续费']
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
        
        for _, row in df.iterrows():
            try:
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
                quantity = safe_int(row['数量'])
                unit_price = safe_int(row['单价'])
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
        if not import_stock_in(stock_in_path):
            success = False
    
    if os.path.exists(stock_out_path):
        print(f"正在导入出库数据: {stock_out_path}")
        if not import_stock_out(stock_out_path):
            success = False
    
    if success:
        print("数据导入完成！")
    else:
        print("数据导入过程中出现错误，请检查日志。")
    
    return success

if __name__ == '__main__':
    main() 