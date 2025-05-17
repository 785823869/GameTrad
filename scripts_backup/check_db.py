from src.core.db_manager import DatabaseManager

db = DatabaseManager()

print('库存表数据：')
result = db.fetch_all('SELECT * FROM inventory')
print(result)

print('\n入库表数据：')
result = db.fetch_all('SELECT * FROM stock_in LIMIT 5')
print(result)

print('\n出库表数据：')
result = db.fetch_all('SELECT * FROM stock_out LIMIT 5')
print(result) 