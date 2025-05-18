#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据库连接
"""
import sys
import traceback
import socket
import time
try:
    import MySQLdb
    print("成功导入MySQLdb模块")
except ImportError:
    print("无法导入MySQLdb模块，请确保已安装")
    sys.exit(1)

def test_socket_connection():
    print("\n测试套接字连接...")
    try:
        s = socket.socket()
        print(f'开始连接到 sql.didiba.uk:33306...')
        s.settimeout(5)  # 5秒超时
        result = s.connect_ex(('sql.didiba.uk', 33306))
        print(f'连接结果: {result} (0表示成功)')
        s.close()
        return result == 0
    except Exception as e:
        print(f"套接字测试失败: {e}")
        return False

def test_db_connection():
    print("\n测试MySQL数据库连接...")
    
    connection_configs = [
        {
            "host": "sql.didiba.uk", 
            "port": 33306,
            "user": "root",
            "passwd": "Cenb1017!@",  # 原始密码
            "db": "OcrTrade"
        },
        {
            "host": "sql.didiba.uk", 
            "port": 33306,
            "user": "root",
            "passwd": "123456",  # 另一种可能的密码
            "db": "OcrTrade"
        }
    ]
    
    for i, config in enumerate(connection_configs):
        print(f"\n尝试配置 #{i+1}:")
        print(f"- 主机: {config['host']}")
        print(f"- 端口: {config['port']}")
        print(f"- 用户: {config['user']}")
        print(f"- 数据库: {config['db']}")
        print(f"- 超时: 5秒")
        
        try:
            start_time = time.time()
            print(f"开始连接时间: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
            
            conn = MySQLdb.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                passwd=config['passwd'],
                db=config['db'],
                charset="utf8mb4",
                connect_timeout=5
            )
            
            end_time = time.time()
            print(f"连接完成时间: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
            print(f"连接耗时: {end_time - start_time:.2f}秒")
            
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"连接成功！MySQL版本: {version[0]}")
            
            # 测试表访问
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"数据库中的表: {[table[0] for table in tables]}")
            
            cursor.close()
            conn.close()
            print("测试完成，连接正常。")
            return True
            
        except MySQLdb.Error as e:
            print(f"MySQL错误: {e}")
            print(f"错误代码: {e.args[0]}")
            print(f"错误信息: {e.args[1] if len(e.args) > 1 else '无详细信息'}")
            # 继续尝试下一个配置
        except Exception as e:
            print(f"连接失败，发生未知错误: {e}")
            print("详细错误信息:")
            traceback.print_exc()
            # 继续尝试下一个配置
    
    # 所有配置都失败
    return False

if __name__ == "__main__":
    socket_ok = test_socket_connection()
    if socket_ok:
        print("\n套接字连接成功，开始测试MySQL连接...")
        db_ok = test_db_connection()
    else:
        print("\n套接字连接失败，无法测试MySQL连接")
        db_ok = False
        
    if socket_ok and db_ok:
        print("\n总结: 数据库连接正常，数据迁移功能可以使用")
    else:
        print("\n总结: 数据库连接异常，数据迁移功能无法正常使用")
        if socket_ok and not db_ok:
            print("原因: 可能是MySQL服务器认证问题、数据库不存在或服务器拒绝远程连接")
        else:
            print("原因: 无法连接到远程服务器") 