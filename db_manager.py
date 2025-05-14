# 环境检测
try:
    import MySQLdb
except ImportError:
    raise RuntimeError("请先安装MySQLdb模块：pip install mysqlclient")
from MySQLdb import OperationalError, IntegrityError
from datetime import datetime
from decimal import Decimal
import sqlite3
import json

class DatabaseManager:
    def __init__(self, db_path='game_trading.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()  # sqlite建表
        # 检测MySQL连接有效性
        try:
            conn = self.get_connection()
            conn.close()
        except Exception as e:
            raise RuntimeError(f"MySQL连接失败: {e}")
        self._create_tables_mysql()  # MySQL建表

    def get_connection(self):
        try:
            return MySQLdb.connect(
                host="sql.didiba.uk",  # 新的远程服务器地址
                port=33306,            # 新的MySQL端口
                user="root",          # 数据库用户名
                passwd="Cenb1017!@",  # 数据库密码
                db="OcrTrade",        # 数据库名
                charset="utf8mb4",    # 字符集
                connect_timeout=10    # 连接超时时间
            )
        except MySQLdb.Error as e:
            print(f"MySQL连接错误: {e}")
            raise RuntimeError(f"无法连接到远程MySQL服务器(sql.didiba.uk): {e}")

    def close(self):
        pass  # 不再需要全局关闭

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return True
        except (OperationalError, IntegrityError, Exception) as e:
            return False
        finally:
            if cursor:
                cursor.close()
            conn.close()

    def fetch_all(self, query, params=None):
        conn = self.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            return results
        except (OperationalError, IntegrityError, Exception) as e:
            return []
        finally:
            if cursor:
                cursor.close()
            conn.close()

    def fetch_one(self, query, params=None):
        conn = self.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            return result
        except (OperationalError, IntegrityError, Exception) as e:
            return None
        finally:
            if cursor:
                cursor.close()
            conn.close()

    # 库存相关方法
    def save_inventory(self, item_data):
        query = """
            INSERT INTO inventory (
                item_name, quantity, avg_price, break_even_price,
                selling_price, profit, profit_rate, total_profit,
                inventory_value
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                quantity = VALUES(quantity),
                avg_price = VALUES(avg_price),
                break_even_price = VALUES(break_even_price),
                selling_price = VALUES(selling_price),
                profit = VALUES(profit),
                profit_rate = VALUES(profit_rate),
                total_profit = VALUES(total_profit),
                inventory_value = VALUES(inventory_value)
        """
        params = (
            item_data['item_name'],
            item_data['quantity'],
            item_data['avg_price'],
            item_data['break_even_price'],
            item_data['selling_price'],
            item_data['profit'],
            item_data['profit_rate'],
            item_data['total_profit'],
            item_data['inventory_value']
        )
        return self.execute_query(query, params)

    def get_inventory(self):
        query = "SELECT * FROM inventory"
        return self.fetch_all(query)

    # 入库记录相关方法
    def save_stock_in(self, stock_in_data):
        """保存入库记录"""
        try:
            # 数据验证
            if not isinstance(stock_in_data.get('quantity'), (int, float)) or stock_in_data.get('quantity', 0) <= 0:
                return False
                
            if not isinstance(stock_in_data.get('cost'), (int, float)) or stock_in_data.get('cost', 0) <= 0:
                return False
                
            if not isinstance(stock_in_data.get('avg_cost'), (int, float)) or stock_in_data.get('avg_cost', 0) <= 0:
                return False

            # 确保数值类型正确且为整数
            quantity = int(stock_in_data['quantity'])
            cost = int(stock_in_data['cost'])
            avg_cost = int(stock_in_data['avg_cost'])
            
            query = """
                INSERT INTO stock_in (
                    item_name, transaction_time, quantity,
                    cost, avg_cost, note
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (
                str(stock_in_data['item_name']),
                stock_in_data['transaction_time'],
                quantity,
                cost,
                avg_cost,
                str(stock_in_data.get('note', ''))
            )
            return self.execute_query(query, params)
            
        except Exception:
            return False

    def get_stock_in(self):
        query = "SELECT * FROM stock_in ORDER BY transaction_time DESC"
        return self.fetch_all(query)

    def delete_stock_in(self, item_name, transaction_time):
        query = "DELETE FROM stock_in WHERE item_name=%s AND transaction_time=%s"
        return self.execute_query(query, (item_name, transaction_time))

    # 出库记录相关方法
    def save_stock_out(self, stock_out_data):
        # 数据验证
        if not isinstance(stock_out_data.get('quantity'), (int, float)) or stock_out_data.get('quantity', 0) <= 0:
            return False
            
        if not isinstance(stock_out_data.get('unit_price'), (int, float)) or stock_out_data.get('unit_price', 0) <= 0:
            return False
            
        if not isinstance(stock_out_data.get('fee'), (int, float)) or stock_out_data.get('fee', 0) < 0:
            return False
            
        if not isinstance(stock_out_data.get('deposit', 0), (int, float)) or stock_out_data.get('deposit', 0) < 0:
            return False

        # 计算总金额
        quantity = float(stock_out_data['quantity'])
        unit_price = float(stock_out_data['unit_price'])
        fee = float(stock_out_data.get('fee', 0))
        deposit = float(stock_out_data.get('deposit', 0))
        total_amount = quantity * unit_price - fee + deposit

        query = """
            INSERT INTO stock_out (
                item_name, transaction_time, quantity,
                unit_price, fee, deposit, total_amount, note
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            stock_out_data['item_name'],
            stock_out_data['transaction_time'],
            quantity,
            unit_price,
            fee,
            deposit,
            total_amount,
            stock_out_data.get('note', '')
        )
        return self.execute_query(query, params)

    def get_stock_out(self):
        query = "SELECT * FROM stock_out ORDER BY transaction_time DESC"
        return self.fetch_all(query)

    def delete_stock_out(self, item_name, transaction_time):
        query = "DELETE FROM stock_out WHERE item_name=%s AND transaction_time=%s"
        return self.execute_query(query, (item_name, transaction_time))

    def add_stock_out(self, item_name, quantity, price, fee, deposit=0.00, note=''):
        """添加出库记录"""
        # 数据验证
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return False
            
        if not isinstance(price, (int, float)) or price <= 0:
            return False
            
        if not isinstance(fee, (int, float)) or fee < 0:
            return False
            
        if not isinstance(deposit, (int, float)) or deposit < 0:
            return False

        now = datetime.now()
        total_amount = float(quantity) * float(price) - float(fee) + float(deposit)
        
        # 获取当前库存总量和总金额
        inventory = self.fetch_one("SELECT quantity, avg_price FROM inventory WHERE item_name=%s", (item_name,))
        if not inventory:
            return False
        
        current_quantity, current_avg_price = inventory
        if current_quantity < quantity:
            return False
        
        # 计算新的库存数量和平均价格
        new_quantity = current_quantity - quantity
        new_avg_price = current_avg_price if new_quantity > 0 else 0
        
        # 更新库存
        if not self.execute_query(
            "UPDATE inventory SET quantity=%s, avg_price=%s WHERE item_name=%s",
            (new_quantity, new_avg_price, item_name)
        ):
            return False
        
        # 添加出库记录
        stock_out_data = {
            'item_name': item_name,
            'transaction_time': now,
            'quantity': quantity,
            'unit_price': price,
            'fee': fee,
            'deposit': deposit,
            'note': note
        }
        
        return self.save_stock_out(stock_out_data)

    # 交易监控相关方法
    def save_trade_monitor(self, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 检查是否已存在该物品
            cursor.execute("SELECT id FROM trade_monitor WHERE item_name=%s", (data['item_name'],))
            row = cursor.fetchone()
            if row:
                # 存在则只更新时间、数量、一口价
                cursor.execute(
                    "UPDATE trade_monitor SET monitor_time=%s, quantity=%s, market_price=%s WHERE item_name=%s",
                    (data['monitor_time'], data['quantity'], data['market_price'], data['item_name'])
                )
            else:
                # 不存在则插入新记录
                cursor.execute(
                    '''INSERT INTO trade_monitor (item_name, monitor_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (
                        data['item_name'],
                        data['monitor_time'],
                        data['quantity'],
                        data['market_price'],
                        data['target_price'],
                        data['planned_price'],
                        data['break_even_price'],
                        data['profit'],
                        data['profit_rate'],
                        data['strategy']
                    )
                )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_trade_monitor(self):
        query = '''
        SELECT * FROM trade_monitor ORDER BY monitor_time DESC
        '''
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            conn.close()

    def delete_trade_monitor(self, item_name, monitor_time):
        query = '''
        DELETE FROM trade_monitor WHERE item_name = %s AND monitor_time = %s
        '''
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (item_name, monitor_time))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    # 库存数量增减
    def increase_inventory(self, item_name, quantity, avg_price):
        query = """
            UPDATE inventory SET quantity=quantity+%s, avg_price=%s WHERE item_name=%s
        """
        return self.execute_query(query, (quantity, avg_price, item_name))

    def decrease_inventory(self, item_name, quantity):
        query = """
            UPDATE inventory SET quantity=quantity-%s WHERE item_name=%s AND quantity>=%s
        """
        return self.execute_query(query, (quantity, item_name, quantity))

    # 银两监控相关方法
    def save_silver_monitor(self, records):
        conn = self.get_connection()
        cursor = None
        try:
            for rec in records:
                query = """
                    INSERT INTO silver_monitor (server, series, price, ma_price, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                """
                params = (
                    rec['server'], rec['series'], rec['price'], rec['ma_price'], rec['timestamp']
                )
                cursor = conn.cursor()
                cursor.execute(query, params)
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            if cursor:
                cursor.close()
            conn.close()

    def get_silver_monitor(self, server=None, series=None, start_time=None, end_time=None):
        query = "SELECT server, series, price, ma_price, timestamp FROM silver_monitor WHERE 1=1"
        params = []
        if server:
            query += " AND server=%s"
            params.append(server)
        if series:
            query += " AND series=%s"
            params.append(series)
        if start_time:
            query += " AND timestamp>=%s"
            params.append(start_time)
        if end_time:
            query += " AND timestamp<=%s"
            params.append(end_time)
        query += " ORDER BY timestamp DESC"
        return self.fetch_all(query, tuple(params))

    def _create_tables(self):
        # 创建入库表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_in (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建出库表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_out (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建交易监控表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_monitor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            monitor_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            quantity INTEGER NOT NULL,
            market_price REAL NOT NULL,
            target_price REAL NOT NULL,
            planned_price REAL NOT NULL,
            break_even_price REAL NOT NULL,
            profit REAL NOT NULL,
            profit_rate REAL NOT NULL,
            strategy TEXT NOT NULL
        )
        ''')

        self.conn.commit()

    def _create_tables_mysql(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        table_sqls = [
            '''CREATE TABLE IF NOT EXISTS stock_in (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(128) NOT NULL,
                transaction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                quantity INT NOT NULL,
                cost DECIMAL(18,2) NOT NULL,
                avg_cost DECIMAL(18,2) NOT NULL,
                deposit DECIMAL(18,2) DEFAULT 0,
                note VARCHAR(255)
            )''',
            '''CREATE TABLE IF NOT EXISTS stock_out (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(128) NOT NULL,
                transaction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                quantity INT NOT NULL,
                unit_price DECIMAL(18,2) NOT NULL,
                fee DECIMAL(18,2) NOT NULL,
                deposit DECIMAL(18,2) DEFAULT 0,
                total_amount DECIMAL(18,2) NOT NULL,
                note VARCHAR(255)
            )''',
            '''CREATE TABLE IF NOT EXISTS trade_monitor (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(128) NOT NULL,
                monitor_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                quantity INT NOT NULL,
                market_price DECIMAL(18,2) NOT NULL,
                target_price DECIMAL(18,2) NOT NULL,
                planned_price DECIMAL(18,2) NOT NULL,
                break_even_price DECIMAL(18,2) NOT NULL,
                profit DECIMAL(18,2) NOT NULL,
                profit_rate DECIMAL(18,2) NOT NULL,
                strategy VARCHAR(255)
            )''',
            '''CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(128) NOT NULL,
                quantity INT NOT NULL,
                avg_price DECIMAL(18,2) NOT NULL,
                break_even_price DECIMAL(18,2) NOT NULL,
                selling_price DECIMAL(18,2) NOT NULL,
                profit DECIMAL(18,2) NOT NULL,
                profit_rate DECIMAL(18,2) NOT NULL,
                total_profit DECIMAL(18,2) NOT NULL,
                inventory_value DECIMAL(18,2) NOT NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS item_dict (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(128) NOT NULL UNIQUE,
                description TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS silver_monitor (
                id INT AUTO_INCREMENT PRIMARY KEY,
                server VARCHAR(50) NOT NULL,
                series VARCHAR(50) NOT NULL,
                price DECIMAL(18,2) NOT NULL,
                ma_price DECIMAL(18,2) NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS operation_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                operation_type VARCHAR(50) NOT NULL,
                tab_name VARCHAR(50) NOT NULL,
                operation_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                operation_data TEXT,
                reverted BOOLEAN DEFAULT FALSE,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )'''
        ]
        for sql in table_sqls:
            cursor.execute(sql)
        # 初始化item_dict表数据（如不存在）
        cursor.execute("SELECT COUNT(*) FROM item_dict")
        if cursor.fetchone()[0] == 0:
            init_items = [
                ("物品1", "默认物品1描述"),
                ("物品2", "默认物品2描述")
            ]
            cursor.executemany("INSERT INTO item_dict (item_name, description) VALUES (%s, %s)", init_items)
        conn.commit()
        cursor.close()
        conn.close()

    def get_operation_logs(self, tab_name=None, op_type=None, keyword=None, reverted=None, page=1, page_size=20):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = "SELECT id, operation_type, tab_name, operation_data, operation_time, reverted FROM operation_logs WHERE 1=1"
            params = []
            if tab_name:
                query += " AND tab_name LIKE %s"
                params.append(f"%{tab_name}%")
            if op_type:
                query += " AND operation_type LIKE %s"
                params.append(f"%{op_type}%")
            if keyword:
                query += " AND operation_data LIKE %s"
                params.append(f"%{keyword}%")
            if reverted is not None:
                query += " AND reverted=%s"
                params.append(reverted)
            query += " ORDER BY operation_time DESC LIMIT %s OFFSET %s"
            params.extend([page_size, (page-1)*page_size])
            cursor.execute(query, tuple(params))
            results = []
            for row in cursor.fetchall():
                id, operation_type, tab_name, operation_data, operation_time, reverted = row
                try:
                    operation_data = json.loads(operation_data)
                except Exception:
                    pass
                results.append({
                    'id': id,
                    '操作类型': operation_type,
                    '标签页': tab_name,
                    '操作时间': operation_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(operation_time, 'strftime') else str(operation_time),
                    '数据': operation_data,
                    '已回退': bool(reverted)
                })
            return results
        finally:
            cursor.close()
            conn.close()

    def count_operation_logs(self, tab_name=None, op_type=None, keyword=None, reverted=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = "SELECT COUNT(*) FROM operation_logs WHERE 1=1"
            params = []
            if tab_name:
                query += " AND tab_name LIKE %s"
                params.append(f"%{tab_name}%")
            if op_type:
                query += " AND operation_type LIKE %s"
                params.append(f"%{op_type}%")
            if keyword:
                query += " AND operation_data LIKE %s"
                params.append(f"%{keyword}%")
            if reverted is not None:
                query += " AND reverted=%s"
                params.append(reverted)
            cursor.execute(query, tuple(params))
            return cursor.fetchone()[0]
        except Exception:
            return 0
        finally:
            cursor.close()
            conn.close()

    def save_operation_log(self, op_type, tab_name, data=None, reverted=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO operation_logs (operation_type, tab_name, operation_data, reverted) VALUES (%s, %s, %s, %s)",
                (op_type, tab_name, json.dumps(data, ensure_ascii=False), int(bool(reverted)))
            )
            conn.commit()
            log_id = cursor.lastrowid
            return log_id
        except Exception:
            return None
        finally:
            cursor.close()
            conn.close()

    def update_operation_log_reverted(self, log_id, reverted=True):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE operation_logs SET reverted=%s WHERE id=%s",
                (int(bool(reverted)), log_id)
            )
            conn.commit()
        except Exception:
            pass
        finally:
            cursor.close()
            conn.close()

    def _load_operation_logs(self):
        """加载操作日志"""
        try:
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute("SELECT * FROM operation_logs ORDER BY operation_time DESC")
            logs = cursor.fetchall()
            cursor.close()
            return logs
        except Exception:
            return [] 