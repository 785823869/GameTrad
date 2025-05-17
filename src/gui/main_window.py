import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog
from tkinter import StringVar
from src.core.inventory_manager import InventoryManager
from src.utils.recipe_parser import RecipeParser
from src.core.trade_analyzer import TradeAnalyzer
from datetime import datetime, timedelta
import json
from src.core.db_manager import DatabaseManager
import os
import requests
import re
import matplotlib
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
matplotlib.use('Agg')  # 防止多线程冲突
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
import mplcursors
import numpy as np  # 用于统计区
import time
import threading
from src.core.formula_manager import FormulaManagerWindow
from PIL import ImageGrab, ImageTk
import io, base64
import tkinter.filedialog as fd
import pandas as pd
import tkinter.simpledialog as simpledialog
import tkinter as tk
import webbrowser
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from src.gui.tabs.nvwa_price_tab import NvwaPriceTab
from src.gui.tabs.silver_price_tab import SilverPriceTab
from src.gui.tabs.log_tab import LogTab
from src.gui.tabs.trade_monitor_tab import TradeMonitorTab
from src.gui.tabs.inventory_tab import InventoryTab
from src.gui.tabs.stock_out_tab import StockOutTab
from src.gui.tabs.stock_in_tab import StockInTab
from src.gui.tabs.dashboard_tab import DashboardTab
# 导入ImportDataDialog
from src.gui.import_data_dialog import ImportDataDialog
# 导入UI管理器
from src.utils.ui_manager import UIManager
from src.utils.sidebar import ModernSidebar
# 导入更新对话框
from src.gui.dialogs.update_dialog import UpdateDialog
# 导入版本信息
from src import __version__

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

class GameTradingSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏交易系统")
        self.root.geometry("1713x852")
        self.root.resizable(True, True)  # 允许调整窗口大小
        
        # 不能像这样设置主题，应该在创建窗口时指定
        # self.root.style = tb.Style(theme="flatly")
        
        # 定义全局背景色
        self.global_bg_color = "#f0f0f0"
        
        self.db_manager = DatabaseManager()
        self._pending_ocr_images = []
        
        # 设置默认中文字体
        self.chinese_font = 'Microsoft YaHei'
        
        # 创建UI管理器
        self.ui_manager = UIManager(root)
        
        # 创建界面 (create_main_interface方法内部会调用load_saved_data和refresh_all)
        self.create_main_interface()
        
        # 添加Server酱配置
        self.server_chan_key = StringVar()
        self.server_chan_enabled = StringVar(value="0")
        self.price_threshold = StringVar(value="1000000")
        self.load_server_chan_config()
        
        # 创建菜单
        self.create_menu()
        
    def create_menu(self):
        menubar = tb.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="数据迁移", command=self.open_data_migration)
        file_menu.add_command(label="导入数据", command=self.open_import_data_dialog)
        file_menu.add_command(label="导出报告", command=self.export_reports)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 设置菜单
        settings_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="Server酱配置", command=self.open_server_chan_config)
        settings_menu.add_command(label="公式管理", command=self.open_formula_manager)
        settings_menu.add_command(label="物品字典管理", command=self.open_item_dict_manager)
        
        # 帮助菜单
        help_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="检查更新", command=self.check_for_updates)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def check_for_updates(self):
        """检查应用程序更新"""
        # 使用GitHub Releases作为更新源
        update_url = "https://api.github.com/repos/785823869/GameTrad/releases/latest"
        direct_download_url = "https://github.com/785823869/GameTrad/releases/download/Game/GameTrad_Setup.exe"
        
        print(f"开始检查更新，API URL: {update_url}, 下载URL: {direct_download_url}")
        
        # 创建更新器实例并设置直接下载URL
        from src.utils.updater import AppUpdater
        updater = AppUpdater(update_url)
        updater.direct_download_url = direct_download_url
        
        # 创建并显示更新对话框
        update_dialog = UpdateDialog(self.root, updater=updater)
        update_dialog.show()
        
    def open_server_chan_config(self):
        """打开Server酱配置窗口"""
        config_window = tb.Toplevel(self.root)
        config_window.title("Server酱配置")
        config_window.geometry("400x300")
        
        frame = ttk.Frame(config_window, padding="10")
        frame.pack(fill=BOTH, expand=True)
        
        # SendKey输入框
        ttk.Label(frame, text="SendKey:").pack(anchor=W, pady=5)
        key_entry = ttk.Entry(frame, textvariable=self.server_chan_key, width=40)
        key_entry.pack(fill=X, pady=5)
        
        # 启用开关
        enable_frame = ttk.Frame(frame)
        enable_frame.pack(fill=X, pady=10)
        ttk.Label(enable_frame, text="启用推送:").pack(side=LEFT)
        enable_switch = ttk.Checkbutton(enable_frame, variable=self.server_chan_enabled, 
                                      onvalue="1", offvalue="0")
        enable_switch.pack(side=LEFT, padx=5)
        
        # 价格阈值设置
        threshold_frame = ttk.LabelFrame(frame, text="价格阈值设置", padding="5")
        threshold_frame.pack(fill=X, pady=10)
        
        # 阈值输入框，支持小数
        ttk.Label(threshold_frame, text="银两价格阈值:").pack(anchor=W, pady=5)
        vcmd = (config_window.register(lambda s: re.match(r'^\d*\.?\d*$', s) is not None or s == ''), '%P')
        threshold_entry = ttk.Entry(threshold_frame, textvariable=self.price_threshold, width=20, validate='key', validatecommand=vcmd)
        threshold_entry.pack(side=LEFT, padx=5)
        ttk.Label(threshold_frame, text="元/万两").pack(side=LEFT)
        
        # 保存按钮
        def save_config():
            try:
                # 验证价格阈值是否为有效小数
                threshold = float(self.price_threshold.get())
                if threshold <= 0:
                    raise ValueError("价格阈值必须大于0")
                self.save_server_chan_config()
                config_window.destroy()
                messagebox.showinfo("成功", "配置已保存")
            except ValueError as e:
                messagebox.showerror("错误", f"价格阈值无效: {str(e)}")
            
        ttk.Button(frame, text="保存", command=save_config).pack(pady=10)
        
    def show_about(self):
        """显示关于对话框"""
        about_text = """
GameTrad 游戏交易系统 v{version}

简介：
GameTrad是一款专业的游戏物品交易管理系统，提供全面的库存管理、交易监控和数据分析功能，帮助游戏玩家和交易商高效管理游戏物品交易流程，实现利润最大化。

核心功能：
✦ 仪表盘 - 实时数据概览与图表分析
✦ 库存管理 - 智能库存追踪与价值评估
✦ 入库管理 - 多渠道物品入库与数据记录
✦ 出库管理 - 高效物品出库与利润计算
✦ 交易监控 - 实时市场价格与交易策略
✦ 行情分析 - 女娲石/银两价格趋势分析
✦ 操作日志 - 完整历史记录与回滚功能

技术特性：
• 基于Python 3.8+与ttkbootstrap构建的现代UI
• 多线程异步处理，确保操作流畅
• OCR图像识别，支持自动数据提取
• 智能数据分析与可视化图表
• 云端数据存储与多设备同步
• 在线自动更新功能

作者：三只小猪

版权所有 © 2025 GameTrad团队
保留所有权利
        """.format(version=__version__)
        messagebox.showinfo("关于", about_text)

    def load_server_chan_config(self):
        """加载Server酱配置"""
        try:
            with open('server_chan_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.server_chan_key.set(config.get('key', ''))
                self.server_chan_enabled.set(config.get('enabled', '0'))
                self.price_threshold.set(str(config.get('price_threshold', 1000000)))
                self.last_push_time = config.get('last_push_time', '')
        except FileNotFoundError:
            self.last_push_time = ''
            pass
            
    def save_server_chan_config(self):
        """保存Server酱配置"""
        config = {
            'key': self.server_chan_key.get(),
            'enabled': self.server_chan_enabled.get(),
            'price_threshold': float(self.price_threshold.get()),
            'last_push_time': self.last_push_time
        }
        with open('server_chan_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
    def should_send_daily_notification(self):
        """检查是否应该发送每日通知"""
        if not self.last_push_time:
            return True
        
        last_push = datetime.strptime(self.last_push_time, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        
        # 如果是新的一天，则应该发送通知
        return last_push.date() < now.date()

    def send_daily_price_notification(self):
        """发送每日价格通知"""
        try:
            # 获取当前银两和女娲石价格
            silver_price = None
            nvwa_price = None
            
            if hasattr(self, 'silver_price_tab'):
                silver_data = self.silver_price_tab._last_silver_data
                if silver_data and 'series' in silver_data:
                    dd373_data = silver_data['series'].get('DD373', [])
                    if dd373_data:
                        silver_price = dd373_data[-1]
            
            if hasattr(self, 'nvwa_price_tab'):
                nvwa_data = self.nvwa_price_tab._last_nvwa_data
                if nvwa_data and 'series' in nvwa_data:
                    dd373_data = nvwa_data['series'].get('DD373', [])
                    if dd373_data:
                        nvwa_price = dd373_data[-1]

            if silver_price is not None or nvwa_price is not None:
                title = "每日价格更新"
                content = "当前价格信息：\n"
                if silver_price is not None:
                    content += f"银两：{silver_price:.4f} 元/万两\n"
                if nvwa_price is not None:
                    content += f"女娲石：{nvwa_price:.4f} 元/颗\n"

                # 发送通知
                self.send_server_chan_notification(title, content)
                # 新增：记录推送日志
                self.log_operation('推送', '银两石价格', {'title': title, 'content': content})
                # 更新最后推送时间
                self.last_push_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.save_server_chan_config()

        except Exception as e:
            print(f"发送每日价格通知失败: {e}")

    def send_server_chan_notification(self, title, content):
        """发送Server酱通知"""
        try:
            if not self.server_chan_key:
                return
            url = f"https://sctapi.ftqq.com/{self.server_chan_key}.send"
            data = {
                "title": title,
                "desp": content
            }
            resp = requests.post(url, data=data, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"发送Server酱通知失败: {e}")
            
    def fetch_silver_price_multi_series(self, days):
        """获取银两价格数据，并只对DD373平台突破阈值时推送"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                url = f"https://www.zxsjinfo.com/api/gold-price?days={days}&server=%E7%91%B6%E5%85%89%E6%B2%81%E9%9B%AA"
                resp = requests.get(url, timeout=20, verify=False)
                resp.raise_for_status()
                data = resp.json()
                
                # 只检测DD373平台
                threshold = float(self.price_threshold.get())
                dd373_series = data.get('series', {}).get('DD373')
                if dd373_series and len(dd373_series) > 0:
                    latest_price = dd373_series[-1]
                    if latest_price > threshold:
                        self.send_server_chan_notification(
                            "银两价格异常警告 - DD373",
                            f"平台：DD373\n当前价格：{latest_price:.4f} 元/万两\n阈值：{threshold:.4f} 元/万两"
                        )
                        # 新增：记录推送日志
                        self.log_operation('推送', '银两石价格', {
                            'title': "银两价格异常警告 - DD373",
                            'content': f"平台：DD373\n当前价格：{latest_price:.4f} 元/万两\n阈值：{threshold:.4f} 元/万两"
                        })
                
                # 返回标准结构
                return {
                    'series': data.get('series', {}),
                    'dates': data.get('dates', {}),
                    'ma': data.get('ma', {})
                }
                
            except requests.exceptions.SSLError as e:
                if attempt < max_retries - 1:
                    print(f"SSL错误，正在重试 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"SSL错误，已达到最大重试次数: {e}")
                    raise
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"请求错误，正在重试 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"请求错误，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                print(f"获取银两价格数据时发生错误: {e}")
                raise
        raise Exception("获取银两价格数据失败，已达到最大重试次数")

    def __del__(self):
        """析构函数，确保关闭数据库连接"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
    
    def create_main_interface(self):
        # 创建现代化侧边栏
        self.sidebar = ModernSidebar(self.root, self.ui_manager)
        
        # 添加标签页到侧边栏
        self.sidebar.add_tab("仪表盘", "📊", DashboardTab, {"main_gui": self})
        self.sidebar.add_tab("库存管理", "📦", InventoryTab, {"main_gui": self})
        self.sidebar.add_tab("入库管理", "📥", StockInTab, {"main_gui": self})
        self.sidebar.add_tab("出库管理", "📤", StockOutTab, {"main_gui": self})
        self.sidebar.add_tab("交易监控", "📈", TradeMonitorTab, {"main_gui": self})
        self.sidebar.add_tab("女娲石行情", "💎", NvwaPriceTab, {"main_gui": self})
        self.sidebar.add_tab("银两行情", "💰", SilverPriceTab, {"main_gui": self})
        self.sidebar.add_tab("操作日志", "📝", LogTab, {"main_gui": self})
        
        # 保存标签页引用，兼容旧代码
        for tab in self.sidebar.tabs:
            if "仪表盘" in tab['title']:
                self.dashboard_tab = tab['content']
            elif "库存管理" in tab['title']:
                self.inventory_tab = tab['content']
            elif "入库管理" in tab['title']:
                self.stock_in_tab = tab['content']
            elif "出库管理" in tab['title']:
                self.stock_out_tab = tab['content']
            elif "交易监控" in tab['title']:
                self.trade_monitor_tab = tab['content']
            elif "女娲石行情" in tab['title']:
                self.nvwa_price_tab = tab['content']
            elif "银两行情" in tab['title']:
                self.silver_price_tab = tab['content']
            elif "操作日志" in tab['title']:
                self.log_tab = tab['content']
        
        # 加载保存的数据
        self.load_saved_data()
        
        # 启动后自动刷新所有标签页数据
        self.refresh_all()
        
        # 日志持久化
        self.operation_logs = list(self._load_operation_logs())
        self.undo_stack = [log for log in self.operation_logs if not log[5]]  # 假设"已回退"是元组的第6个字段（索引5）
        self.redo_stack = [log for log in self.operation_logs if log[5]]
        
        # 在 __init__ 里添加：
        self.current_ocr_tab = None
        
    def load_saved_data(self):
        """从数据库加载数据"""
        try:
            # 加载库存数据
            inventory_data = self.db_manager.get_inventory()
            for item in inventory_data:
                try:
                    _, item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value, *_ = item
                    self.inventory_tab.inventory_tree.insert('', 'end', values=(
                        item_name,
                        quantity,
                        f"{safe_float(avg_price):.2f}",
                        f"{safe_float(break_even_price):.2f}",
                        f"{safe_float(selling_price):.2f}",
                        f"{safe_float(profit):.2f}",
                        f"{safe_float(profit_rate):.2f}%",
                        f"{safe_float(total_profit):.2f}",
                        f"{safe_float(inventory_value):.2f}"
                    ))
                except Exception as e:
                    messagebox.showerror("数据结构异常", f"库存数据结构异常: {e}\nitem={item}")
                    continue
            
            # 加载入库记录
            stock_in_data = self.db_manager.get_stock_in()
            for item in stock_in_data:
                try:
                    _, item_name, transaction_time, quantity, cost, avg_cost, note, *_ = item
                    self.stock_in_tab.stock_in_tree.insert('', 'end', values=(
                        item_name,
                        transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                        quantity,
                        f"{safe_float(cost):.2f}",
                        f"{safe_float(avg_cost):.2f}",
                        note if note is not None else ''
                    ))
                except Exception as e:
                    messagebox.showerror("数据结构异常", f"入库数据结构异常: {e}\nitem={item}")
                    continue
            
            # 加载出库记录
            stock_out_data = self.db_manager.get_stock_out()
            for item in stock_out_data:
                try:
                    _, item_name, transaction_time, quantity, unit_price, fee, deposit, total_amount, note, *_ = item
                    self.stock_out_tab.stock_out_tree.insert('', 'end', values=(
                        item_name,
                        transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                        int(quantity),
                        safe_float(unit_price),
                        safe_float(fee),
                        safe_float(total_amount),
                        note if note is not None else ''
                    ))
                except Exception as e:
                    messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\nitem={item}")
                    continue
            
            # 加载监控记录
            monitor_data = self.db_manager.get_trade_monitor()
            for item in monitor_data:
                try:
                    _, item_name, monitor_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = item
                    self.trade_monitor_tab.monitor_tree.insert('', 'end', values=(
                        item_name,
                        monitor_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(monitor_time, 'strftime') else str(monitor_time),
                        quantity,
                        f"{safe_float(market_price):.2f}",
                        f"{safe_float(target_price):.2f}",
                        f"{safe_float(planned_price):.2f}",
                        f"{safe_float(break_even_price):.2f}",
                        f"{safe_float(profit):.2f}",
                        f"{safe_float(profit_rate):.2f}%",
                        strategy
                    ))
                except Exception as e:
                    messagebox.showerror("数据结构异常", f"监控数据结构异常: {e}\nitem={item}")
                    continue
            
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
        # 新增：强制刷新入库表格，确保显示最新数据
        self.refresh_stock_in()

    def refresh_all(self):
        """刷新所有数据"""
        # 使用Tab类中的刷新方法，防止重复刷新
        if hasattr(self, 'inventory_tab'):
            self.inventory_tab.refresh_inventory()
        else:
            # 只有在没有标签页时才使用主窗口方法
            self.refresh_inventory()
            
        if hasattr(self, 'stock_out_tab'):
            self.stock_out_tab.refresh_stock_out()
        else:
            self.refresh_stock_out()
            
        if hasattr(self, 'stock_in_tab'):
            self.stock_in_tab.refresh_stock_in()
        
        if hasattr(self, 'nvwa_price_tab'):
            self.nvwa_price_tab.refresh_nvwa_price()
        
        if hasattr(self, 'silver_price_tab'):
            self.silver_price_tab.refresh_silver_price()
        
        if hasattr(self, 'trade_monitor_tab'):
            self.trade_monitor_tab.refresh_monitor()
    
    def refresh_inventory(self):
        for item in self.inventory_tab.inventory_tree.get_children():
            self.inventory_tab.inventory_tree.delete(item)
        stock_in_data = self.db_manager.get_stock_in()
        stock_out_data = self.db_manager.get_stock_out()
        inventory_dict = {}
        for row in stock_in_data:
            try:
                _, item_name, _, qty, cost, *_ = row
            except Exception as e:
                messagebox.showerror("数据结构异常", f"入库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nrow={row}")
                continue
            if item_name not in inventory_dict:
                inventory_dict[item_name] = {
                    'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                }
            inventory_dict[item_name]['in_qty'] += qty
            inventory_dict[item_name]['in_amount'] += cost
        for row in stock_out_data:
            try:
                _, item_name, _, qty, unit_price, fee, deposit, total_amount, note, *_ = row
            except Exception as e:
                messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nrow={row}")
                continue
            amount = unit_price * qty - fee
            if item_name not in inventory_dict:
                inventory_dict[item_name] = {
                    'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                }
            inventory_dict[item_name]['out_qty'] += qty
            inventory_dict[item_name]['out_amount'] += amount
        formula_dict = {}
        try:
            import json
            if os.path.exists("field_formulas.json"):
                with open("field_formulas.json", "r", encoding="utf-8") as f:
                    formula_json = json.load(f)
                    formula_dict = formula_json.get("库存管理", {})
        except Exception as e:
            formula_dict = {}
        for item, data in inventory_dict.items():
            remain_qty = data['in_qty'] - data['out_qty']
            in_avg = data['in_amount'] / data['in_qty'] if data['in_qty'] else 0
            out_avg = data['out_amount'] / data['out_qty'] if data['out_qty'] else 0
            default_formula = {
                '利润': '(out_avg - in_avg) * out_qty if out_qty else 0',
                '利润率': '((out_avg - in_avg) / in_avg * 100) if in_avg else 0',
                '成交利润额': '(out_avg - in_avg) * out_qty if out_qty else 0',
                '库存价值': 'remain_qty * in_avg'
            }
            ctx = {
                'in_qty': data['in_qty'],
                'in_amount': data['in_amount'],
                'out_qty': data['out_qty'],
                'out_amount': data['out_amount'],
                'remain_qty': remain_qty,
                'in_avg': in_avg,
                'out_avg': out_avg
            }
            def calc_field(field):
                formula = None
                if field in formula_dict:
                    formulas = formula_dict[field]
                    if formulas:
                        formula = list(formulas.values())[0]
                if not formula:
                    formula = default_formula.get(field, '0')
                try:
                    return eval(formula, {}, ctx)
                except Exception:
                    return 0
            profit = calc_field('利润')
            profit_rate = calc_field('利润率')
            total_profit = calc_field('成交利润额')
            value = calc_field('库存价值')
            self.inventory_tab.inventory_tree.insert('', 'end', values=(
                item,
                int(remain_qty),
                str(int(round(in_avg))),
                str(int(round(in_avg))),  # 保本均价=入库均价
                str(int(round(out_avg))),
                f"{int(profit/10000)}万",  # 利润以万为单位整数
                f"{int(round(profit_rate))}%",
                f"{int(total_profit/10000)}万",  # 成交利润额以万为单位整数
                f"{value/10000:.2f}万"  # 库存价值以万为单位保留两位小数
            ))

    def _fetch_and_draw_inventory(self):
        # 数据库操作放到后台线程
        stock_in_data = self.db_manager.get_stock_in()
        stock_out_data = self.db_manager.get_stock_out()
        inventory_dict = {}
        # 统计入库
        for row in stock_in_data:
            try:
                _, item_name, _, qty, cost, *_ = row
            except Exception as e:
                messagebox.showerror("数据结构异常", f"入库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nrow={row}")
                continue
            if item_name not in inventory_dict:
                inventory_dict[item_name] = {
                    'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                }
            inventory_dict[item_name]['in_qty'] += qty
            inventory_dict[item_name]['in_amount'] += cost
        # 统计出库
        for row in stock_out_data:
            try:
                _, item_name, _, qty, unit_price, fee, deposit, total_amount, note, *_ = row
            except Exception as e:
                messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nrow={row}")
                continue
            amount = unit_price * qty - fee
            if item_name not in inventory_dict:
                inventory_dict[item_name] = {
                    'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                }
            inventory_dict[item_name]['out_qty'] += qty
            inventory_dict[item_name]['out_amount'] += amount
        # 加载自定义公式
        formula_dict = {}
        try:
            import json
            if os.path.exists("field_formulas.json"):
                with open("field_formulas.json", "r", encoding="utf-8") as f:
                    formula_json = json.load(f)
                    formula_dict = formula_json.get("库存管理", {})
        except Exception as e:
            formula_dict = {}
        # 生成库存表数据
        table_data = []
        for item, data in inventory_dict.items():
            remain_qty = data['in_qty'] - data['out_qty']
            in_avg = data['in_amount'] / data['in_qty'] if data['in_qty'] else 0
            out_avg = data['out_amount'] / data['out_qty'] if data['out_qty'] else 0
            default_formula = {
                '利润': '(out_avg - in_avg) * out_qty if out_qty else 0',
                '利润率': '((out_avg - in_avg) / in_avg * 100) if in_avg else 0',
                '成交利润额': '(out_avg - in_avg) * out_qty if out_qty else 0',
                '库存价值': 'remain_qty * in_avg'
            }
            ctx = {
                'in_qty': data['in_qty'],
                'in_amount': data['in_amount'],
                'out_qty': data['out_qty'],
                'out_amount': data['out_amount'],
                'remain_qty': remain_qty,
                'in_avg': in_avg,
                'out_avg': out_avg
            }
            def calc_field(field):
                formula = None
                if field in formula_dict:
                    formulas = formula_dict[field]
                    if formulas:
                        formula = list(formulas.values())[0]
                if not formula:
                    formula = default_formula.get(field, '0')
                try:
                    return eval(formula, {}, ctx)
                except Exception:
                    return 0
            profit = calc_field('利润')
            profit_rate = calc_field('利润率')
            total_profit = calc_field('成交利润额')
            value = calc_field('库存价值')
            table_data.append((
                item,
                remain_qty,
                f"{in_avg:.2f}",
                f"{in_avg:.2f}",
                f"{out_avg:.2f}",
                f"{profit:.2f}",
                f"{profit_rate:.2f}%",
                f"{total_profit:.2f}",
                f"{value:.2f}"
            ))
        # 回到主线程刷新表格
        self.root.after(0, lambda: self._draw_inventory(table_data))

    def _draw_inventory(self, table_data):
        for item in self.inventory_tab.inventory_tree.get_children():
            self.inventory_tab.inventory_tree.delete(item)
        for row in table_data:
            self.inventory_tab.inventory_tree.insert('', 'end', values=row)

    def refresh_stock_in(self):
        """刷新入库记录"""
        self.stock_in_tab.refresh_stock_in()

    def refresh_stock_out(self):
        for item in self.stock_out_tab.stock_out_tree.get_children():
            self.stock_out_tab.stock_out_tree.delete(item)
        records = self.db_manager.get_stock_out()
        filter_text = self.stock_out_filter_var.get().strip().lower() if hasattr(self, 'stock_out_filter_var') else ''
        keywords = filter_text.split()
        filtered = []
        for record in records:
            try:
                _, item_name, transaction_time, quantity, unit_price, fee, deposit, total_amount, note, *_ = record
                name_lc = str(item_name).lower()
                if keywords and not all(k in name_lc for k in keywords):
                    continue
                values = (
                    item_name,
                    transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                    int(quantity),
                    int(float(unit_price)),
                    int(float(fee)),
                    int(float(total_amount)),
                    note if note is not None else ''
                )
                filtered.append(values)
                self.stock_out_tab.stock_out_tree.insert('', 'end', values=values)
            except Exception as e:
                messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nrecord={record}")
                continue
        # 合计行
        if filter_text and filtered:
            total_qty = sum(int(row[2]) for row in filtered)
            total_fee = sum(int(row[4]) for row in filtered)
            total_amount = sum(int(row[5]) for row in filtered)
            self.stock_out_tab.stock_out_tree.insert('', 'end', values=(
                '合计', '', total_qty, '', total_fee, total_amount, ''
            ), tags=('total',))

    def refresh_monitor(self):
        threading.Thread(target=self._fetch_and_draw_monitor, daemon=True).start()

    def _fetch_and_draw_monitor(self):
        monitor_data = self.db_manager.get_trade_monitor()
        table_data = []
        # 加载自定义公式
        formula_dict = {}
        try:
            import json
            if os.path.exists("field_formulas.json"):
                with open("field_formulas.json", "r", encoding="utf-8") as f:
                    formula_json = json.load(f)
                    formula_dict = formula_json.get("交易监控", {})
        except Exception as e:
            formula_dict = {}
        for item in monitor_data:
            try:
                _, item_name, monitor_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = item
                # 构建上下文
                ctx = {
                    '物品': item_name,
                    '当前时间': monitor_time,
                    '数量': quantity,
                    '一口价': float(market_price),
                    '目标买入价': float(target_price),
                    '计划卖出价': float(planned_price),
                    '保本卖出价': float(break_even_price),
                    '利润': float(profit),
                    '利润率': float(profit_rate),
                    '出库策略': strategy
                }
                # 依次应用自定义公式
                def calc_field(field, default_value):
                    formula = None
                    if field in formula_dict:
                        formulas = formula_dict[field]
                        if formulas:
                            formula = list(formulas.values())[0]
                    if not formula:
                        return default_value
                    try:
                        return eval(formula, {}, ctx)
                    except Exception:
                        return default_value
                break_even_price_val = calc_field('保本卖出价', float(break_even_price))
                profit_val = calc_field('利润', float(profit))
                profit_rate_val = calc_field('利润率', float(profit_rate))
                table_data.append((
                    item_name,
                    monitor_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(monitor_time, 'strftime') else str(monitor_time),
                    int(quantity),
                    str(int(round(float(market_price)))),
                    str(int(round(float(target_price)))),
                    str(int(round(float(planned_price)))),
                    str(int(round(float(break_even_price_val)))),
                    f"{profit_val:.2f}",
                    f"{profit_rate_val:.2f}%",
                    strategy
                ))
            except Exception as e:
                messagebox.showerror("数据结构异常", f"监控数据结构异常: {e}\n请检查表结构与代码字段一致性。\nitem={item}")
                continue
        self.root.after(0, lambda: self._draw_monitor(table_data))

    def _draw_monitor(self, table_data):
        for item in self.trade_monitor_tab.monitor_tree.get_children():
            self.trade_monitor_tab.monitor_tree.delete(item)
        for row in table_data:
            self.trade_monitor_tab.monitor_tree.insert('', 'end', values=row)
        # 不插入合计行

    def add_stock_in(self):
        """添加入库记录"""
        try:
            item = self.stock_in_item.get()
            quantity = int(self.stock_in_quantity.get())
            cost = float(self.stock_in_cost.get())
            note = self.stock_in_note.get()
            avg_cost = cost / quantity
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db_manager.save_stock_in({
                'item_name': item,
                'transaction_time': now,
                'quantity': quantity,
                'cost': cost,
                'avg_cost': avg_cost,
                'deposit': 0.00,  # 默认押金为0
                'note': note if note is not None else ''
            })
            self.db_manager.increase_inventory(item, quantity, avg_cost)
            self.refresh_stock_in()
            self.refresh_inventory()
            self.stock_in_item.delete(0, 'end')
            self.stock_in_quantity.delete(0, 'end')
            self.stock_in_cost.delete(0, 'end')
            self.stock_in_note.delete(0, 'end')
            self.log_operation('修改', '入库管理')
            messagebox.showinfo("成功", "入库记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
    
    def add_stock_out(self):
        """添加出库记录"""
        try:
            item = self.stock_out_item.get()
            quantity = int(self.stock_out_quantity.get())
            price = float(self.stock_out_price.get())
            fee = float(self.stock_out_fee.get())
            note = self.stock_out_note.get()
            total_amount = quantity * price - fee
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 自动减少库存
            success = self.db_manager.decrease_inventory(item, quantity)
            if not success:
                messagebox.showerror("错误", f"库存不足，无法出库 {item} 数量 {quantity}")
                return
            self.db_manager.save_stock_out({
                'item_name': item,
                'transaction_time': now,
                'quantity': quantity,
                'unit_price': price,
                'fee': fee,
                'deposit': 0.0,  # 新增字段，防止错位
                'total_amount': total_amount,
                'note': note if note is not None else ''
            })
            self.refresh_stock_out()
            self.refresh_inventory()
            # 清空输入框
            self.stock_out_item.delete(0, 'end')
            self.stock_out_quantity.delete(0, 'end')
            self.stock_out_price.delete(0, 'end')
            self.stock_out_fee.delete(0, 'end')
            self.stock_out_note.delete(0, 'end')
            # 记录操作日志
            self.log_operation('修改', '出库管理')
            messagebox.showinfo("成功", "出库记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
    
    def export_reports(self):
        import pandas as pd
        import os
        from tkinter import filedialog
        try:
            # 收集所有表格数据
            inventory_data = [self.inventory_tab.inventory_tree.item(item)['values'] for item in self.inventory_tab.inventory_tree.get_children()]
            stock_in_data = [self.stock_in_tab.stock_in_tree.item(item)['values'] for item in self.stock_in_tab.stock_in_tree.get_children()]
            stock_out_data = [self.stock_out_tab.stock_out_tree.item(item)['values'] for item in self.stock_out_tab.stock_out_tree.get_children()]
            monitor_data = [self.trade_monitor_tab.monitor_tree.item(item)['values'] for item in self.trade_monitor_tab.monitor_tree.get_children()]

            # 定义表头
            inventory_columns = ['物品', '库存数', '总入库均价', '保本均价', '总出库均价', '利润', '利润率', '成交利润额', '库存价值']
            stock_in_columns = ['物品', '当前时间', '入库数量', '入库花费', '入库均价', '备注']
            stock_out_columns = ['物品', '当前时间', '出库数量', '单价', '手续费', '出库总金额', '备注']
            monitor_columns = ['物品', '当前时间', '数量', '一口价', '目标买入价', '计划卖出价', '保本卖出价', '利润', '利润率', '出库策略']

            # 让用户选择文件名和格式
            file_path = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel文件', '*.xlsx'), ('CSV文件', '*.csv')],
                title='导出报表'
            )
            if not file_path:
                return

            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.xlsx':
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    pd.DataFrame(inventory_data, columns=inventory_columns).to_excel(writer, sheet_name='库存', index=False)
                    pd.DataFrame(stock_in_data, columns=stock_in_columns).to_excel(writer, sheet_name='入库', index=False)
                    pd.DataFrame(stock_out_data, columns=stock_out_columns).to_excel(writer, sheet_name='出库', index=False)
                    pd.DataFrame(monitor_data, columns=monitor_columns).to_excel(writer, sheet_name='监控', index=False)
                messagebox.showinfo('成功', f'所有报表已导出到 {file_path}')
            elif ext == '.csv':
                base = os.path.splitext(file_path)[0]
                pd.DataFrame(inventory_data, columns=inventory_columns).to_csv(base + '_库存.csv', index=False, encoding='utf-8-sig')
                pd.DataFrame(stock_in_data, columns=stock_in_columns).to_csv(base + '_入库.csv', index=False, encoding='utf-8-sig')
                pd.DataFrame(stock_out_data, columns=stock_out_columns).to_csv(base + '_出库.csv', index=False, encoding='utf-8-sig')
                pd.DataFrame(monitor_data, columns=monitor_columns).to_csv(base + '_监控.csv', index=False, encoding='utf-8-sig')
                messagebox.showinfo('成功', f'所有报表已导出为多个csv文件（以{base}_开头）')
            else:
                messagebox.showerror('错误', '不支持的文件格式')
        except Exception as e:
            messagebox.showerror('错误', f'导出报表失败: {str(e)}')

    def export_inventory(self):
        threading.Thread(target=self._export_inventory_thread, daemon=True).start()

    def _export_inventory_thread(self):
        try:
            with open("inventory_report.csv", "w", encoding="utf-8") as f:
                f.write("物品,库存数,总入库均价,保本均价,总出库均价,利润,利润率,成交利润额,库存价值\n")
                for item in self.inventory_tab.inventory_tree.get_children():
                    try:
                        values = self.inventory_tab.inventory_tree.item(item)['values']
                        item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value, *_ = values
                        formatted_values = [
                            item_name,
                            str(int(quantity)),
                            str(int(avg_price)),
                            str(int(break_even_price)),
                            str(int(selling_price)),
                            str(int(profit)),
                            values[6],
                            str(int(total_profit)),
                            str(int(inventory_value))
                        ]
                        f.write(",".join(formatted_values) + "\n")
                    except Exception as e:
                        print(f"导出库存项失败: {e}")
                        continue
            self.root.after(0, lambda: messagebox.showinfo("成功", "库存报表已导出到 inventory_report.csv"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"导出库存报表失败: {str(e)}"))

    def export_stock_in(self):
        threading.Thread(target=self._export_stock_in_thread, daemon=True).start()

    def _export_stock_in_thread(self):
        try:
            with open("stock_in_report.csv", "w", encoding="utf-8") as f:
                f.write("物品,当前时间,入库数量,入库花费,入库均价,备注\n")
                for item in self.stock_in_tab.stock_in_tree.get_children():
                    try:
                        values = self.stock_in_tab.stock_in_tree.item(item)['values']
                        item_name, transaction_time, quantity, cost, avg_cost, note, *_ = values
                        formatted_values = [
                            item_name,
                            transaction_time,
                            str(int(quantity)),
                            str(int(round(cost))),
                            str(int(round(avg_cost))),
                            note
                        ]
                        f.write(",".join(formatted_values) + "\n")
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("数据结构异常", f"stock_in_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}"))
                        continue
            self.root.after(0, lambda: messagebox.showinfo("成功", "入库报表已导出到 stock_in_report.csv"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"导出入库报表失败: {str(e)}"))

    def export_stock_out(self):
        threading.Thread(target=self._export_stock_out_thread, daemon=True).start()

    def _export_stock_out_thread(self):
        try:
            with open("stock_out_report.csv", "w", encoding="utf-8") as f:
                f.write("物品,当前时间,出库数量,单价,手续费,出库总金额,备注\n")
                for item in self.stock_out_tab.stock_out_tree.get_children():
                    try:
                        values = self.stock_out_tab.stock_out_tree.item(item)['values']
                        item_name, transaction_time, quantity, unit_price, fee, total_amount, note, *_ = values
                        formatted_values = [
                            item_name,
                            transaction_time,
                            str(int(float(quantity))),
                            str(int(float(unit_price))),
                            str(int(float(fee))),
                            str(int(float(total_amount))),
                            note
                        ]
                        f.write(",".join(formatted_values) + "\n")
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("数据结构异常", f"stock_out_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}"))
                        continue
            self.root.after(0, lambda: messagebox.showinfo("成功", "出库报表已导出到 stock_out_report.csv"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"导出出库报表失败: {str(e)}"))

    def export_monitor(self):
        threading.Thread(target=self._export_monitor_thread, daemon=True).start()

    def _export_monitor_thread(self):
        try:
            with open("monitor_report.csv", "w", encoding="utf-8") as f:
                f.write("物品,当前时间,数量,一口价,目标买入价,计划卖出价,保本卖出价,利润,利润率,出库策略\n")
                for item in self.trade_monitor_tab.monitor_tree.get_children():
                    try:
                        values = self.trade_monitor_tab.monitor_tree.item(item)['values']
                        item_name, transaction_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = values
                        formatted_values = [
                            item_name,
                            transaction_time,
                            str(int(quantity)),
                            str(int(values[3])),
                            str(int(values[4])),
                            str(int(values[5])),
                            str(int(values[6])),
                            str(int(values[7])),
                            values[8],
                            values[9]
                        ]
                        f.write(",".join(formatted_values) + "\n")
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("数据结构异常", f"monitor_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}"))
                        continue
            self.root.after(0, lambda: messagebox.showinfo("成功", "监控报表已导出到 monitor_report.csv"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"导出监控报表失败: {str(e)}"))

    def open_formula_manager(self):
        """打开公式管理窗口"""
        FormulaManagerWindow(self.root, self)

    def _on_tab_changed_ocr(self, event=None):
        tab = self.notebook.tab(self.notebook.select(), 'text')
        # 先解绑所有
        self.root.unbind_all('<Control-v>')
        if tab == '入库管理':
            self.root.bind_all('<Control-v>', self.stock_in_tab.paste_ocr_import_stock_in)
            self.current_ocr_tab = 'in'
        elif tab == '出库管理':
            self.root.bind_all('<Control-v>', self.stock_out_tab.paste_ocr_import_stock_out)
            self.current_ocr_tab = 'out'
        elif tab == '交易监控':
            self.root.bind_all('<Control-v>', self.trade_monitor_tab.paste_ocr_import_monitor)
            self.current_ocr_tab = 'monitor'
        else:
            self.current_ocr_tab = None

    def parse_stock_out_ocr_text(self, text):
        """解析出库OCR文本，所有金额字段转为整数，正则兼容多种格式。"""
        try:
            # 提取物品名称和数量（兼容所有括号类型）
            item_match = re.search(r'已成功售出([^（(]+)[（(](\d+)[）)]', text)
            if not item_match:
                return None
            
            item_name = item_match.group(1).strip()
            quantity = int(item_match.group(2))
            
            # 优化正则，兼容多种格式
            price_match = re.search(r'售出单价[:： ]*([0-9]+)银两', text)
            price = int(price_match.group(1)) if price_match else 0
            
            fee_match = re.search(r'手续费[:： ]*([0-9]+)银两', text)
            fee = int(fee_match.group(1)) if fee_match else 0
            
            total_amount = quantity * price - fee
            
            return {
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': int(price),
                'fee': int(fee),
                'deposit': 0.0,
                'total_amount': int(total_amount),
                'note': 'OCR导入'
            }
        except Exception as e:
            print(f"解析出库OCR文本失败: {e}")
            return None

    def parse_monitor_ocr_text(self, text):
        """
        交易监控OCR文本解析，提取物品、数量、一口价，确保每个物品为一条数据，兼容多栏换行。
        优先用物品词典分割物品名。
        若物品/数量/一口价数量不一致，补全缺失项并弹窗提示。
        """
        import re
        try:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            # 1. 提取物品名
            item_names = []
            for idx, line in enumerate(lines):
                if line.startswith('物品'):
                    # 合并物品下所有非表头行
                    items_block = []
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['品质', '数量', '等级', '一口价']):
                            break
                        items_block.append(lines[j])
                    items_str = ' '.join(items_block)
                    # 优先用词典分割
                    dict_items = self.load_item_dict()
                    pos = 0
                    while pos < len(items_str):
                        matched = False
                        for name in sorted(dict_items, key=lambda x: -len(x)):
                            if items_str.startswith(name, pos):
                                item_names.append(name)
                                pos += len(name)
                                matched = True
                                break
                        if not matched:
                            # 跳过无法识别的字符
                            pos += 1
                    break
            # 2. 提取数量
            quantities = []
            for idx, line in enumerate(lines):
                if line.startswith('数量'):
                    qty_block = []
                    # 把本行的数字也提取出来
                    qty_block.append(line.replace('数量', '').strip())
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['一口价', '物品', '品质', '等级']):
                            break
                        qty_block.append(lines[j])
                    quantities = [int(x) for x in re.findall(r'\d+', ' '.join(qty_block))]
                    break
            # 3. 提取一口价
            prices = []
            for idx, line in enumerate(lines):
                if line.startswith('一口价'):
                    price_block = []
                    price_block.append(line.replace('一口价', '').strip())
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['数量', '物品', '品质', '等级']):
                            break
                        price_block.append(lines[j])
                    prices = [int(x) for x in re.findall(r'\d+', ' '.join(price_block))]
                    break
            n = max(len(item_names), len(quantities), len(prices))
            result = []
            for i in range(n):
                result.append({
                    'item_name': item_names[i] if i < len(item_names) else '',
                    'quantity': quantities[i] if i < len(quantities) else '',
                    'market_price': prices[i] if i < len(prices) else '',
                    'note': 'OCR导入' if (i < len(item_names) and i < len(quantities) and i < len(prices)) else '数据缺失'
                })
            if not (len(item_names) == len(quantities) == len(prices)):
                messagebox.showwarning(
                    "数据不完整",
                    f"物品数：{len(item_names)}，数量：{len(quantities)}，一口价：{len(prices)}。请检查OCR识别结果，部分数据可能丢失。"
                )
            return result
        except Exception as e:
            print(f"解析交易监控OCR文本失败: {e}")
            return []

    def open_item_dict_manager(self):
        """物品词典管理窗口"""
        win = tb.Toplevel(self.root)
        win.title("物品词典管理")
        win.geometry("400x350")
        listbox = tk.Listbox(win, font=("微软雅黑", 12))
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        # 加载词典
        items = self.load_item_dict()
        for item in items:
            listbox.insert('end', item)
        # 按钮区
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill='x', pady=8)
        def add_item():
            name = simpledialog.askstring("添加物品", "输入物品名：", parent=win)
            if name and name not in items:
                listbox.insert('end', name)
                items.append(name)
        def del_item():
            sel = listbox.curselection()
            if sel:
                idx = sel[0]
                items.pop(idx)
                listbox.delete(idx)
        def save_dict():
            with open(os.path.join('data', 'item_dict.txt'), 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(item+'\n')
            messagebox.showinfo("保存成功", "物品词典已保存！")
        ttk.Button(btn_frame, text="添加", command=add_item).pack(side='left', padx=10, ipadx=8)
        ttk.Button(btn_frame, text="删除", command=del_item).pack(side='left', padx=10, ipadx=8)
        ttk.Button(btn_frame, text="保存", command=save_dict).pack(side='right', padx=10, ipadx=8)

    def load_item_dict(self):
        """加载物品字典列表，自动修复为项目根目录下data/item_dict.txt"""
        try:
            # 自动修复：始终用项目根目录下的data/item_dict.txt
            base_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(base_dir, '../../'))
            dict_path = os.path.join(project_root, 'data', 'item_dict.txt')
            if not os.path.exists(dict_path):
                return []
            with open(dict_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"读取物品字典失败: {e}")
            return []

    def show_about(self):
        """显示关于对话框"""
        about_text = """
GameTrad 游戏交易系统 v2.0.0

简介：
GameTrad是一款专业的游戏物品交易管理系统，提供全面的库存管理、交易监控和数据分析功能，帮助游戏玩家和交易商高效管理游戏物品交易流程，实现利润最大化。

核心功能：
✦ 仪表盘 - 实时数据概览与图表分析
✦ 库存管理 - 智能库存追踪与价值评估
✦ 入库管理 - 多渠道物品入库与数据记录
✦ 出库管理 - 高效物品出库与利润计算
✦ 交易监控 - 实时市场价格与交易策略
✦ 行情分析 - 女娲石/银两价格趋势分析
✦ 操作日志 - 完整历史记录与回滚功能

技术特性：
• 基于Python 3.8+与ttkbootstrap构建的现代UI
• 多线程异步处理，确保操作流畅
• OCR图像识别，支持自动数据提取
• 智能数据分析与可视化图表
• 云端数据存储与多设备同步

作者：三只小猪

版权所有 © 2025 GameTrad团队
保留所有权利
        """
        messagebox.showinfo("关于", about_text)

    def log_jump_page(self):
        try:
            page = int(self.log_jump_var.get())
            if 1 <= page <= self.log_total_pages:
                self.log_page = page
                self.refresh_log_tab()
            else:
                messagebox.showwarning("提示", f"页码范围：1~{self.log_total_pages}")
        except Exception:
            messagebox.showwarning("提示", "请输入有效的页码")

    def _on_silver_press(self, event):
        if event.button == 1:  # 左键
            self._dragging = True
            self._drag_start = (event.xdata, event.ydata)
            self._orig_xlim = self.silver_ax1.get_xlim()
            self._orig_ylim = self.silver_ax1.get_ylim()

    def _on_silver_motion(self, event):
        if getattr(self, '_dragging', False) and event.xdata is not None and event.ydata is not None:
            dx = event.xdata - self._drag_start[0]
            dy = event.ydata - self._drag_start[1]
            x0, x1 = self._orig_xlim
            y0, y1 = self._orig_ylim
            self.silver_ax1.set_xlim(x0 - dx, x1 - dx)
            self.silver_ax1.set_ylim(y0 - dy, y1 - dy)
            self.silver_canvas.draw_idle()

    def _on_silver_release(self, event):
        self._dragging = False

    def show_preview(self, data, columns=None, field_map=None, on_confirm=None):
        import datetime
        preview_window = tk.Toplevel(self.root)
        preview_window.title("预览")
        preview_window.geometry("900x600")

        selected_items = set(range(len(data)))

        # 顶部按钮区（左右分布）
        top_button_frame = ttk.Frame(preview_window)
        top_button_frame.pack(side=tk.TOP, fill=tk.X, pady=8)
        btn_style = {'width': 12, 'padding': 6}
        # 左侧按钮
        left_btns = ttk.Frame(top_button_frame)
        left_btns.pack(side=tk.LEFT)
        def select_all():
            for iid in tree.get_children():
                tree.selection_add(iid)
            selected_items.clear()
            selected_items.update(range(len(data)))
        def deselect_all():
            tree.selection_remove(tree.get_children())
            selected_items.clear()
        ttk.Button(left_btns, text="全选", command=select_all, **btn_style).pack(side=tk.LEFT, padx=8)
        ttk.Button(left_btns, text="全不选", command=deselect_all, **btn_style).pack(side=tk.LEFT, padx=8)
        # 右侧按钮
        right_btns = ttk.Frame(top_button_frame)
        right_btns.pack(side=tk.RIGHT)
        def confirm():
            selected_data = [data[idx] for idx in sorted(selected_items)]
            if on_confirm:
                on_confirm(selected_data)
            else:
                is_stock_in = False
                for idx in sorted(selected_items):
                    row = data[idx]
                    if isinstance(row, dict):
                        # 判断是入库还是出库
                        if 'cost' in row and 'avg_cost' in row:
                            is_stock_in = True
                            if 'transaction_time' not in row:
                                row['transaction_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            self.db_manager.save_stock_in(row)
                        else:
                            if 'transaction_time' not in row:
                                row['transaction_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            self.db_manager.save_stock_out(row)
                if is_stock_in:
                    self.refresh_stock_in()
                else:
                    self.refresh_stock_out()
            preview_window.destroy()
            messagebox.showinfo("成功", "数据已成功导入！")
        ttk.Button(right_btns, text="取消", command=preview_window.destroy, **btn_style).pack(side=tk.RIGHT, padx=10)
        ttk.Button(right_btns, text="确认导入", command=confirm, **btn_style).pack(side=tk.RIGHT, padx=10)

        # 创建表格
        tree = ttk.Treeview(preview_window, columns=columns, show='headings', height=20, selectmode='extended')
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')
        for idx, row in enumerate(data):
            if isinstance(row, dict):
                values = []
                for col in columns:
                    key = field_map.get(col, col)
                    val = row.get(key, "")
                    try:
                        if isinstance(val, (int, float)):
                            if "率" in col:
                                val = f"{val:.2f}%"
                            elif "价" in col or "金额" in col or "花费" in col or "利润" in col:
                                val = f"{val:,.2f}"
                            else:
                                val = f"{int(val):,}"
                        elif isinstance(val, str) and val.replace(".", "").isdigit():
                            if "率" in col:
                                val = f"{float(val):.2f}%"
                            elif "价" in col or "金额" in col or "花费" in col or "利润" in col:
                                val = f"{float(val):,.2f}"
                            else:
                                val = f"{int(float(val)):,}"
                    except (ValueError, TypeError):
                        pass
                    values.append(str(val))
            else:
                values = [str(x) for x in row]
            tree.insert('', 'end', iid=str(idx), values=values)
        tree.selection_set(tree.get_children())
        def on_select(event):
            selected_items.clear()
            for iid in tree.selection():
                selected_items.add(int(iid))
        tree.bind('<<TreeviewSelect>>', on_select)
        scrollbar = ttk.Scrollbar(preview_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def open_data_migration(self):
        """打开数据迁移窗口"""
        migration_window = tk.Toplevel(self.root)
        migration_window.title("数据迁移")
        migration_window.geometry("400x300")
        
        main_frame = ttk.Frame(migration_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # 添加说明标签
        ttk.Label(main_frame, text="数据迁移功能正在开发中，敬请期待。").pack(pady=10)

    def _load_operation_logs(self):
        """加载操作日志"""
        try:
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute("SELECT * FROM operation_logs ORDER BY operation_time DESC")
            logs = cursor.fetchall()
            cursor.close()
            return logs
        except Exception as e:
            print(f"加载操作日志失败: {e}")
            return []

    def delete_log_items(self):
        selected_items = self.log_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要删除的日志记录！")
            return
        if not messagebox.askyesno("确认", f"确定要删除选中的 {len(selected_items)} 条日志记录吗？此操作不可恢复。"):
            return
        deleted_count = 0
        for item in selected_items:
            values = self.log_tree.item(item)['values']
            # 通过操作类型、标签页、操作时间唯一定位日志
            op_type = values[0].replace("（已回退）", "")
            tab = values[1]
            op_time = values[2]
            # 删除数据库中的日志
            try:
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM operation_logs WHERE operation_type=%s AND tab_name=%s AND operation_time=%s",
                    (op_type, tab, op_time)
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"删除数据库日志失败: {e}")
            # 删除界面上的
            self.log_tree.delete(item)
            deleted_count += 1
        messagebox.showinfo("成功", f"已删除 {deleted_count} 条日志记录！")
        self.refresh_log_tab()

    def refresh_after_operation(self):
        """操作后刷新所有数据"""
        self.refresh_inventory()
        self.refresh_stock_out()

    def refresh_after_delete(self):
        """删除后刷新所有数据"""
        self.refresh_inventory()
        self.refresh_stock_out()

    def refresh_after_edit(self):
        """编辑后刷新所有数据"""
        self.refresh_inventory()
        self.refresh_stock_out()

    def refresh_after_import(self):
        """导入后刷新所有数据"""
        self.refresh_inventory()
        self.refresh_stock_out()

    def refresh_after_export(self):
        """导出后刷新所有数据"""
        self.refresh_inventory()
        self.refresh_stock_out()

    def refresh_after_ocr(self):
        """OCR后刷新所有数据"""
        self.refresh_inventory()
        self.refresh_stock_out()

    def _save_operation_logs(self):
        """占位方法，防止 AttributeError。可根据需要实现日志持久化。"""
        pass

    def undo_last_operation(self):
        logs = self.db_manager.get_operation_logs(
            tab_name=None, op_type=None, keyword=None, reverted=False, page=1, page_size=1
        )
        if not logs:
            messagebox.showinfo("提示", "没有可回退的操作！")
            return
        last_log = logs[0]
        op_type = last_log['操作类型']
        tab = last_log['标签页']
        data = last_log['数据']
        # 回退逻辑
        if op_type == '添加' and tab == '入库管理':
            if isinstance(data, list):
                for row in data:
                    self.db_manager.delete_stock_in(row['item_name'], row['transaction_time'])
            elif isinstance(data, dict):
                self.db_manager.delete_stock_in(data['item_name'], data['transaction_time'])
            self.refresh_stock_in()
            self.refresh_inventory()
        elif op_type == '添加' and tab == '出库管理':
            if isinstance(data, list):
                for row in data:
                    self.db_manager.delete_stock_out(row['item_name'], row['transaction_time'])
            elif isinstance(data, dict):
                self.db_manager.delete_stock_out(data['item_name'], data['transaction_time'])
            self.refresh_stock_out()
            self.refresh_inventory()
        elif op_type == '添加' and tab == '交易监控':
            if isinstance(data, list):
                for row in data:
                    self.db_manager.delete_trade_monitor(row['item_name'], row['monitor_time'])
            elif isinstance(data, dict):
                self.db_manager.delete_trade_monitor(data['item_name'], data['monitor_time'])
            self.trade_monitor_tab.refresh_monitor()
        elif op_type == '删除' and tab == '入库管理':
            if isinstance(data, list):
                for row in data:
                    self.db_manager.save_stock_in(row)
            elif isinstance(data, dict):
                self.db_manager.save_stock_in(data)
            self.refresh_stock_in()
            self.refresh_inventory()
        elif op_type == '删除' and tab == '出库管理':
            if isinstance(data, list):
                for row in data:
                    self.db_manager.save_stock_out(row)
            elif isinstance(data, dict):
                self.db_manager.save_stock_out(data)
            self.refresh_stock_out()
            self.refresh_inventory()
        elif op_type == '删除' and tab == '交易监控':
            if isinstance(data, list):
                for row in data:
                    self.db_manager.save_trade_monitor(row)
            elif isinstance(data, dict):
                self.db_manager.save_trade_monitor(data)
            self.trade_monitor_tab.refresh_monitor()
        elif op_type == '修改' and tab == '入库管理':
            if isinstance(data, dict) and 'old' in data:
                old = data['old']
                self.db_manager.delete_stock_in(old[0], old[1])
                self.db_manager.save_stock_in({
                    'item_name': old[0],
                    'transaction_time': old[1],
                    'quantity': int(old[2]),
                    'cost': float(old[3]),
                    'avg_cost': float(old[4]),
                    'note': old[5] if len(old) > 5 else ''
                })
                self.refresh_stock_in()
                self.refresh_inventory()
        elif op_type == '修改' and tab == '出库管理':
            if isinstance(data, dict) and 'old' in data:
                old = data['old']
                self.db_manager.delete_stock_out(old[0], old[1])
                self.db_manager.save_stock_out({
                    'item_name': old[0],
                    'transaction_time': old[1],
                    'quantity': int(old[2]),
                    'unit_price': float(old[3]),
                    'fee': float(old[4]),
                    'deposit': 0.0,
                    'total_amount': float(old[5]),
                    'note': old[6] if len(old) > 6 else ''
                })
                self.refresh_stock_out()
                self.refresh_inventory()
        elif op_type == '修改' and tab == '交易监控':
            if isinstance(data, dict) and 'old' in data:
                old = data['old']
                self.db_manager.delete_trade_monitor(old[0], old[1])
                self.db_manager.save_trade_monitor({
                    'item_name': old[0],
                    'monitor_time': old[1],
                    'quantity': int(old[2]),
                    'market_price': float(old[3]),
                    'target_price': float(old[4]),
                    'planned_price': float(old[5]),
                    'break_even_price': float(old[6]),
                    'profit': float(old[7]),
                    'profit_rate': float(str(old[8]).strip('%')),
                    'strategy': old[9]
                })
                self.trade_monitor_tab.refresh_monitor()
        # 标记日志为已回退
        if 'id' in last_log:
            self.db_manager.update_operation_log_reverted(last_log['id'], True)
        self.log_tab.refresh_log_tab()
        messagebox.showinfo("提示", f"已回退操作: {op_type} - {tab}")

    def redo_last_operation(self):
        """前进（撤销回退）"""
        messagebox.showinfo("提示", "已恢复操作（示例实现）")

    def log_operation(self, op_type, tab_name, data=None, reverted=False):
        """记录操作日志，data为被操作的数据内容，reverted为是否已回退"""
        import json
        from datetime import datetime
        log = {
            '操作类型': op_type,
            '标签页': tab_name,
            '操作时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '数据': data,
            '已回退': reverted
        }
        # 保存到数据库（如有）
        if hasattr(self, 'db_manager') and hasattr(self.db_manager, 'save_operation_log'):
            self.db_manager.save_operation_log(op_type, tab_name, data, reverted)
        # 内存同步（可选，便于撤销/重做等）
        if hasattr(self, 'operation_logs'):
            self.operation_logs.append(log)
        # 日志tab界面同步（如有）
        if hasattr(self, 'log_tab') and hasattr(self.log_tab, 'log_tree'):
            self.log_tab.log_tree.insert('', 'end', values=(
                log['操作类型'] + ("（已回退）" if reverted else ""),
                log['标签页'],
                log['操作时间'],
                json.dumps(log['数据'], ensure_ascii=False)
            ))

    def open_import_data_dialog(self):
        """打开导入数据对话框"""
        ImportDataDialog(self)

    def on_tab_changed(self, event):
        """兼容旧代码，处理标签页切换事件"""
        # 获取当前活动标签页的内容
        active_content = self.sidebar.get_active_tab_content()
        if active_content == self.log_tab:
            self.log_tab.refresh_log_tab()

if __name__ == "__main__":
    root = tb.Window(themename="flatly")  # 使用flatly主题
    root.title("GameTrad交易管理系统")
    root.geometry("1280x800")
    app = GameTradingSystemGUI(root)
    root.mainloop() 