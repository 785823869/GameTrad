import json
import mysql.connector
from datetime import datetime

def restore_logs():
    try:
        # 连接数据库
        conn = mysql.connector.connect(
            host='sql.didiba.uk',
            port=33306,
            user='root',
            password='Cenb1017!@',
            database='OcrTrade'
        )
        cursor = conn.cursor()
        
        # 读取JSON文件
        with open('operation_logs.json', 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        print(f'从JSON文件中读取到 {len(logs)} 条记录')
        
        # 先清空表
        cursor.execute('TRUNCATE TABLE operation_logs')
        print('已清空操作日志表')
        
        success, fail = 0, 0
        for i, log in enumerate(logs, 1):
            try:
                # 自动兼容操作时间格式
                try:
                    operation_time = datetime.strptime(log['操作时间'], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    # 兼容带毫秒或其他格式
                    operation_time = datetime.fromisoformat(log['操作时间'].replace('T', ' ').split('.')[0])
                # 自动兼容数据字段为None、list、dict
                data_field = log.get('数据', None)
                try:
                    data_json = json.dumps(data_field, ensure_ascii=False)
                except Exception:
                    data_json = 'null'
                cursor.execute(
                    'INSERT INTO operation_logs (operation_type, tab_name, operation_time, operation_data, reverted) VALUES (%s, %s, %s, %s, %s)',
                    (
                        log.get('操作类型', ''),
                        log.get('标签页', ''),
                        operation_time,
                        data_json,
                        int(bool(log.get('已回退', False)))
                    )
                )
                success += 1
            except Exception as e:
                print(f'第{i}条插入失败: {e}')
                print(f'内容: {log}')
                fail += 1
            if i % 10 == 0:
                print(f'已处理 {i}/{len(logs)} 条记录')
        
        # 提交事务
        conn.commit()
        
        print(f'操作日志数据恢复完成，成功 {success} 条，失败 {fail} 条')
        
        # 验证数据
        cursor.execute('SELECT COUNT(*) FROM operation_logs')
        count = cursor.fetchone()[0]
        print(f'数据库实际日志条数: {count}')
        
        # 显示一些示例数据
        cursor.execute('SELECT operation_type, tab_name, operation_time FROM operation_logs LIMIT 5')
        print('\n最近5条记录:')
        for row in cursor.fetchall():
            print(f'类型: {row[0]}, 标签页: {row[1]}, 时间: {row[2]}')
        
    except Exception as e:
        print(f'恢复数据时出错: {e}')
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    restore_logs() 