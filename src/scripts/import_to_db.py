import pandas as pd
import os
from db_manager import DatabaseManager

def read_csv_auto_encoding(path):
    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='gbk')

def import_stock_in(csv_path):
    df = read_csv_auto_encoding(csv_path)
    db = DatabaseManager()
    for _, row in df.iterrows():
        note = row['备注'] if '备注' in row and pd.notna(row['备注']) else ''
        db.save_stock_in({
            'item_name': row['物品'],
            'transaction_time': row.get('当前时间', row.get('时间', '')),
            'quantity': int(row['入库数量']),
            'cost': int(float(row['入库花费'])) if pd.notna(row['入库花费']) else 0,
            'avg_cost': int(float(row['入库均价'])) if pd.notna(row['入库均价']) else 0,
            'note': note
        })
    print("入库数据导入完成！")

def import_stock_out(csv_path):
    df = read_csv_auto_encoding(csv_path)
    db = DatabaseManager()
    def safe_int(val):
        try:
            return int(float(val)) if pd.notna(val) else 0
        except Exception:
            return 0
    for _, row in df.iterrows():
        note = row['备注'] if '备注' in row and pd.notna(row['备注']) else ''
        db.save_stock_out({
            'item_name': row['物品'],
            'transaction_time': row.get('时间', row.get('当前时间', '')),
            'quantity': safe_int(row['数量']),
            'unit_price': safe_int(row['单价']),
            'fee': safe_int(row['手续费']),
            'deposit': 0,
            'total_amount': safe_int(row['总金额']),
            'note': note
        })
    print("出库数据导入完成！")

if __name__ == '__main__':
    data_dir = os.path.join("data", "import")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    import_stock_in(os.path.join(data_dir, 'stock_in.csv'))
    import_stock_out(os.path.join(data_dir, 'stock_out.csv')) 