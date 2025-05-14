import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog
from tkinter import StringVar
from inventory_manager import InventoryManager
from recipe_parser import RecipeParser
from trade_analyzer import TradeAnalyzer
from datetime import datetime, timedelta
import json
from db_manager import DatabaseManager
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
from formula_manager import FormulaManagerWindow
from PIL import ImageGrab, ImageTk
import io, base64
import tkinter.filedialog as fd
import pandas as pd
import tkinter.simpledialog as simpledialog
import tkinter as tk
import webbrowser
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

class GameTradingSystemGUI:
    def __init__(self, root):
        self.root = root
        self.db_manager = DatabaseManager()  # 必须最先初始化
        self.root.title("游戏交易系统")
        self.root.geometry("1542x852")
        
        # 添加Server酱配置
        self.server_chan_key = StringVar()
        self.server_chan_enabled = StringVar(value="0")
        self.price_threshold = StringVar(value="1000000")
        self.load_server_chan_config()
        
        # 创建菜单
        self.create_menu()
        
        # 创建主界面
        self.create_main_interface()
        
    def create_menu(self):
        menubar = tb.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="数据迁移", command=self.open_data_migration)
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
        help_menu.add_command(label="关于", command=self.show_about)
        
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
        
    def load_server_chan_config(self):
        """加载Server酱配置"""
        try:
            with open('server_chan_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.server_chan_key.set(config.get('key', ''))
                self.server_chan_enabled.set(config.get('enabled', '0'))
                self.price_threshold.set(str(config.get('price_threshold', 1000000)))
        except FileNotFoundError:
            pass
            
    def save_server_chan_config(self):
        """保存Server酱配置"""
        config = {
            'key': self.server_chan_key.get(),
            'enabled': self.server_chan_enabled.get(),
            'price_threshold': float(self.price_threshold.get())
        }
        with open('server_chan_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
    def send_server_chan_notification(self, title, content):
        """发送Server酱通知"""
        if self.server_chan_enabled.get() != "1":
            return
            
        key = self.server_chan_key.get()
        if not key:
            return
            
        try:
            url = f"https://sctapi.ftqq.com/{key}.send"
            data = {
                "title": title,
                "desp": content
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                self.log_operation("推送", "Server酱", f"推送成功: {title}")
            else:
                self.log_operation("推送", "Server酱", f"推送失败: {response.text}")
        except Exception as e:
            self.log_operation("推送", "Server酱", f"推送异常: {str(e)}")
            
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
        # 创建主界面
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # 创建各个功能页面
        self.create_inventory_tab()
        self.create_stock_in_tab()
        self.create_stock_out_tab()
        self.create_trade_monitor_tab()
        self.create_analysis_tab()
        self.create_log_tab()
        self.create_silver_price_tab()
        
        # 加载保存的数据
        self.load_saved_data()
        # 启动后自动刷新所有标签页数据
        self.refresh_all()
        
        # 日志持久化
        self.operation_logs = self._load_operation_logs()
        self.undo_stack = [log for log in self.operation_logs if not log.get('已回退')]
        self.redo_stack = [log for log in self.operation_logs if log.get('已回退')]
        
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        self.auto_refresh_silver_price()
        
        # 在 __init__ 里添加：
        self.current_ocr_tab = None
        self.root.bind('<<NotebookTabChanged>>', self._on_tab_changed_ocr)
        self._pending_ocr_images_out = []
        self._pending_ocr_images = []
        self._pending_ocr_images_monitor = []
    
    def on_tab_changed(self, event):
        tab = self.notebook.tab(self.notebook.select(), 'text')
        if tab == '操作日志':
            self.refresh_log_tab()

    def create_inventory_tab(self):
        """创建库存管理标签页"""
        inventory_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(inventory_frame, text="库存管理")
        
        # 库存表格
        columns = ('物品', '库存数', '总入库均价', '保本均价', '总出库均价', '利润', '利润率', '成交利润额', '库存价值')
        self.inventory_tree = ttk.Treeview(inventory_frame, columns=columns, show='headings', height=18)
        
        for col in columns:
            self.inventory_tree.heading(col, text=col, anchor='center')
            self.inventory_tree.column(col, width=120, anchor='center')
        
        scrollbar = ttk.Scrollbar(inventory_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.inventory_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        
        # 右侧操作面板
        right_panel = ttk.Frame(inventory_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        
        ttk.Button(right_panel, text="刷新库存", command=self.refresh_inventory).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="导出库存", command=self.export_inventory).pack(fill='x', pady=(0, 10), ipady=4)
        
        self.inventory_menu = tb.Menu(self.inventory_tree, tearoff=0)
        self.inventory_menu.add_command(label="删除", command=self.delete_inventory_item)
        self.inventory_tree.bind("<Button-3>", self.show_inventory_menu)
    
    def show_inventory_menu(self, event):
        """显示库存右键菜单"""
        item = self.inventory_tree.identify_row(event.y)
        if item:
            # 多选支持：如果当前行未被选中，则只选中该行，否则保持多选
            if item not in self.inventory_tree.selection():
                self.inventory_tree.selection_set(item)
            self.inventory_menu.post(event.x_root, event.y_root)

    def delete_inventory_item(self):
        """批量删除库存记录"""
        selected_items = self.inventory_tree.selection()
        if not selected_items:
            return
        names = [self.inventory_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下库存物品吗？\n" + "，".join(str(n) for n in names)
        if messagebox.askyesno("确认", msg):
            for item in selected_items:
                self.inventory_tree.delete(item)
            self.refresh_inventory()
    
    def create_stock_in_tab(self):
        """创建入库管理标签页"""
        stock_in_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(stock_in_frame, text="入库管理")
        
        # 入库表格
        columns = ('物品', '当前时间', '入库数量', '入库花费', '入库均价', '备注')
        self.stock_in_tree = ttk.Treeview(stock_in_frame, columns=columns, show='headings', height=16)
        for col in columns:
            self.stock_in_tree.heading(col, text=col, anchor='center')
            self.stock_in_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(stock_in_frame, orient="vertical", command=self.stock_in_tree.yview)
        self.stock_in_tree.configure(yscrollcommand=scrollbar.set)
        self.stock_in_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        
        # 右侧操作面板
        right_panel = ttk.Frame(stock_in_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        
        # 物品筛选控件
        self.stock_in_filter_var = tb.StringVar()
        filter_row = ttk.Frame(right_panel)
        filter_row.pack(fill='x', pady=2)
        ttk.Label(filter_row, text="物品筛选:").pack(side='left')
        filter_entry = ttk.Entry(filter_row, textvariable=self.stock_in_filter_var, width=12)
        filter_entry.pack(side='left', padx=2)
        ttk.Button(filter_row, text="筛选", command=self.refresh_stock_in).pack(side='left', padx=2)
        
        # 添加入库记录
        add_frame = ttk.LabelFrame(right_panel, text="添加入库记录", padding=10)
        add_frame.pack(fill='x', pady=8)
        ttk.Label(add_frame, text="物品:").grid(row=0, column=0, padx=5, pady=5)
        self.stock_in_item = ttk.Entry(add_frame)
        self.stock_in_item.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="数量:").grid(row=1, column=0, padx=5, pady=5)
        self.stock_in_quantity = ttk.Entry(add_frame)
        self.stock_in_quantity.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="花费:").grid(row=2, column=0, padx=5, pady=5)
        self.stock_in_cost = ttk.Entry(add_frame)
        self.stock_in_cost.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="备注:").grid(row=3, column=0, padx=5, pady=5)
        self.stock_in_note = ttk.Entry(add_frame)
        self.stock_in_note.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        add_frame.columnconfigure(1, weight=1)
        ttk.Button(add_frame, text="添加入库", command=self.add_stock_in).grid(row=4, column=0, columnspan=2, pady=10, sticky='ew')
        
        ttk.Button(right_panel, text="刷新入库记录", command=self.refresh_stock_in).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="上传图片自动入库", command=self.ocr_import_stock_in).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="批量识别粘贴图片", command=self.batch_ocr_import_stock_in).pack(fill='x', pady=(0, 10), ipady=4)
        self.ocr_image_preview_frame = ttk.Frame(right_panel)
        self.ocr_image_preview_frame.pack(fill='x', pady=5)
        
        self.stock_in_menu = tb.Menu(self.stock_in_tree, tearoff=0)
        self.stock_in_menu.add_command(label="删除", command=self.delete_stock_in_item)
        self.stock_in_tree.bind("<Button-3>", self.show_stock_in_menu)
        # 新增：Ctrl+A全选
        self.stock_in_tree.bind('<Control-a>', lambda e: [self.stock_in_tree.selection_set(self.stock_in_tree.get_children()), 'break'])
    
    def edit_stock_in_item(self, event):
        item_id = self.stock_in_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.stock_in_tree.item(item_id)['values']
        edit_win = tb.Toplevel(self.root)
        edit_win.title("编辑入库记录")
        edit_win.minsize(420, 420)
        edit_win.configure(bg='#f4f8fb')
        style = ttk.Style()
        style.configure('Edit.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=('微软雅黑', 11))
        style.configure('Edit.TButton', font=('微软雅黑', 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        content_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        labels = ["物品", "时间", "数量", "花费", "均价", "备注"]
        types = [str, str, int, float, float, str]
        entries = []
        error_labels = []
        for i, (label, val, typ) in enumerate(zip(labels, values, types)):
            ttk.Label(content_frame, text=label+":", style='Edit.TLabel').grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
            entry = ttk.Entry(content_frame, validate='key', validatecommand=vcmd, style='Edit.TEntry') if vcmd else ttk.Entry(content_frame, style='Edit.TEntry')
            entry.insert(0, val)
            entry.grid(row=i*2, column=1, padx=12, pady=4, sticky='w')
            entries.append(entry)
            err = ttk.Label(content_frame, text="", foreground="red", background='#f4f8fb', font=('微软雅黑', 10))
            err.grid(row=i*2+1, column=0, columnspan=2, sticky='w', padx=12)
            error_labels.append(err)
        def save():
            new_vals = [e.get() for e in entries]
            valid = True
            for idx, (val, typ, err_lbl) in enumerate(zip(new_vals, types, error_labels)):
                err_lbl.config(text="")
                if typ is int:
                    if not val.isdigit():
                        err_lbl.config(text="请输入正整数")
                        entries[idx].focus_set()
                        valid = False
                        break
                elif typ is float:
                    try:
                        float(val)
                    except Exception:
                        err_lbl.config(text="请输入数字")
                        entries[idx].focus_set()
                        valid = False
                        break
            if not valid:
                return
            try:
                new_vals[2] = int(new_vals[2])
                new_vals[3] = float(new_vals[3])
                new_vals[4] = float(new_vals[4])
            except Exception:
                error_labels[2].config(text="数量/花费/均价必须为数字")
                entries[2].focus_set()
                return
            if not messagebox.askyesno("确认", "确定要保存修改吗？"):
                return
            self.db_manager.delete_stock_in(values[0], values[1])
            self.db_manager.save_stock_in({
                'item_name': new_vals[0],
                'transaction_time': new_vals[1],
                'quantity': new_vals[2],
                'cost': new_vals[3],
                'avg_cost': new_vals[4],
                'note': new_vals[5]
            })
            self.refresh_stock_in()
            edit_win.destroy()
        button_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        ttk.Button(button_frame, text="保存", command=save, style='Edit.TButton').pack(pady=6, ipadx=40)

    def refresh_ocr_image_preview(self):
        for widget in self.ocr_image_preview_frame.winfo_children():
            widget.destroy()
        for idx, img in enumerate(self._pending_ocr_images):
            thumb = img.copy()
            thumb.thumbnail((80, 80))
            photo = ImageTk.PhotoImage(thumb)
            lbl = ttk.Label(self.ocr_image_preview_frame, image=photo)
            lbl.image = photo
            lbl.grid(row=0, column=idx*2, padx=4, pady=2)
            btn = ttk.Button(self.ocr_image_preview_frame, text='删除', width=5, command=lambda i=idx: self.delete_ocr_image(i))
            btn.grid(row=1, column=idx*2, padx=4, pady=2)

    def delete_ocr_image(self, idx):
        del self._pending_ocr_images[idx]
        self.refresh_ocr_image_preview()

    def paste_ocr_import_stock_in(self, event=None):
        img = ImageGrab.grabclipboard()
        if isinstance(img, list):
            img = img[0] if img else None
        if img is None or not hasattr(img, 'save'):
            messagebox.showwarning("粘贴失败", "剪贴板中没有图片")
            return
        self._pending_ocr_images.append(img)
        self.refresh_ocr_image_preview()
        messagebox.showinfo("已添加", f"已添加{len(self._pending_ocr_images)}张图片，点击批量识别可统一导入。")

    def batch_ocr_import_stock_in(self):
        if not self._pending_ocr_images:
            messagebox.showwarning("无图片", "请先粘贴图片")
            return
        all_preview_data = []
        for img in self._pending_ocr_images:
            try:
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                url = "http://sql.didiba.uk:1224/api/ocr"
                payload = {
                    "base64": img_b64,
                    "options": {
                        "data.format": "text"
                    }
                }
                headers = {"Content-Type": "application/json"}
                resp = requests.post(url, json=payload, headers=headers, timeout=20)
                resp.raise_for_status()
                ocr_result = resp.json()
                text = ocr_result.get('data')
                if not text:
                    continue
                
                # 使用新的入库解析函数处理OCR文本
                parsed_data = self.parse_stock_in_ocr_text(text)
                if parsed_data:
                    if isinstance(parsed_data, list):
                        all_preview_data.extend(parsed_data)
                    else:
                        all_preview_data.append(parsed_data)
            except Exception as e:
                print(f"OCR识别失败: {e}")
        
        if all_preview_data:
            self.show_ocr_preview(
                all_preview_data,
                columns=('物品', '入库数量', '入库花费', '入库均价', '备注'),
                field_map=['item_name', 'quantity', 'cost', 'avg_cost', 'note']
            )
        else:
            messagebox.showwarning("无有效数据", "未识别到有效的入库数据！")
        self._pending_ocr_images.clear()
        self.refresh_ocr_image_preview()
    
    def parse_stock_in_ocr_text(self, text):
        """解析入库OCR文本，合并所有同名物品为一条，数量和花费为总和，均价为总花费/总数量。"""
        try:
            # 提取所有失去的银两数量并求和
            total_cost = 0
            for cost_match in re.finditer(r'失去了银两[×xX*＊ ]*(\d+)', text):
                total_cost += int(cost_match.group(1))
            
            # 提取所有获得的物品和数量（不依赖"获得了"前缀）
            item_dict = {}
            for m in re.finditer(r'([\u4e00-\u9fa5a-zA-Z0-9]+)[×xX*＊ ]*(\d+)', text):
                item_name = m.group(1).strip()
                quantity = int(m.group(2))
                if item_name == "银两" or item_name.startswith("失去了银两"):
                    continue
                item_dict[item_name] = item_dict.get(item_name, 0) + quantity
            
            if not item_dict or total_cost == 0:
                return None
            
            # 合并所有物品为一条（如只有至纯精华）
            if len(item_dict) == 1:
                item_name, quantity = list(item_dict.items())[0]
            else:
                # 多个物品时，合并为一个物品名（用+连接），数量为总和
                item_name = '+'.join(item_dict.keys())
                quantity = sum(item_dict.values())
            
            # 计算均价并取整
            avg_cost = int(round(total_cost / quantity)) if quantity else 0
            
            # 添加当前时间
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'item_name': str(item_name),
                'transaction_time': now,
                'quantity': int(quantity),
                'cost': int(total_cost),
                'avg_cost': int(avg_cost),
                'note': 'OCR导入'
            }
        except Exception as e:
            print(f"解析入库OCR文本失败: {e}")
            return None

    def show_stock_in_menu(self, event):
        """显示入库右键菜单"""
        item = self.stock_in_tree.identify_row(event.y)
        if item:
            if item not in self.stock_in_tree.selection():
                self.stock_in_tree.selection_set(item)
            self.stock_in_menu.post(event.x_root, event.y_root)

    def delete_stock_in_item(self):
        """批量删除入库记录"""
        selected_items = self.stock_in_tree.selection()
        if not selected_items:
            return
        names = [self.stock_in_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下入库记录吗？\n" + "，".join(str(n) for n in names)
        deleted_data = []
        if messagebox.askyesno("确认", msg):
            for item in selected_items:
                values = self.stock_in_tree.item(item)['values']
                self.db_manager.delete_stock_in(values[0], values[1])
                deleted_data.append(values)
            self.refresh_stock_in()
            self.log_operation('删除', '入库管理', deleted_data)
    
    def ocr_import_stock_in(self):
        """通过UMI-OCR图片识别自动批量入库（新版接口，支持游戏截图格式，带预览确认）"""
        file_paths = fd.askopenfilenames(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_paths:
            return
        try:
            from PIL import Image
            count = 0
            for file_path in file_paths:
                img = Image.open(file_path)
                self._pending_ocr_images.append(img)
                count += 1
            self.refresh_ocr_image_preview()
            messagebox.showinfo("已添加", f"已添加{count}张图片，点击批量识别可统一导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def show_ocr_preview(self, preview_data, columns=None, field_map=None):
        """显示OCR预览窗口，支持自定义表头和字段映射"""
        if columns is None:
            columns = ('物品', '数量', '单价', '手续费', '总金额', '备注')
        if field_map is None:
            field_map = ['item_name', 'quantity', 'price', 'fee', 'total_amount', 'note']
        preview_window = tb.Toplevel(self.root)
        preview_window.title("OCR预览")
        preview_window.geometry("900x600")

        # 主Frame
        main_frame = ttk.Frame(preview_window)
        main_frame.pack(fill='both', expand=True)

        # 表格区
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(side='top', fill='both', expand=True, padx=10, pady=(10, 0))

        preview_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        for col in columns:
            preview_tree.heading(col, text=col, anchor='center')
            preview_tree.column(col, width=120, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=preview_tree.yview)
        preview_tree.configure(yscrollcommand=scrollbar.set)
        preview_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 添加数据
        for data in preview_data:
            values = tuple(data.get(field, '') for field in field_map)
            preview_tree.insert('', 'end', values=values)

        # 按钮区
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side='bottom', fill='x', pady=16)

        for text, cmd in [
            ("全选", lambda: self._select_all_items(preview_tree)),
            ("取消全选", lambda: self._deselect_all_items(preview_tree)),
            ("确认导入", lambda: self._confirm_import(preview_tree, preview_data, preview_window)),
            ("取消", preview_window.destroy)
        ]:
            ttk.Button(button_frame, text=text, command=cmd).pack(side='left', expand=True, padx=20, ipadx=10, ipady=4)

        # 添加右键菜单
        preview_menu = tb.Menu(preview_tree, tearoff=0)
        preview_tree.bind("<Button-3>", lambda e: self._show_preview_menu(e, preview_tree, preview_menu))
        # 双击编辑
        preview_tree.bind("<Double-1>", lambda e: self._edit_preview_item(e, preview_tree))
    
    def _select_all_items(self, tree):
        """全选预览项目"""
        for item in tree.get_children():
            tree.selection_add(item)
    
    def _deselect_all_items(self, tree):
        """取消全选预览项目"""
        for item in tree.get_children():
            tree.selection_remove(item)
    
    def _show_preview_menu(self, event, tree, menu):
        """显示预览右键菜单"""
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            menu.delete(0, 'end')
            menu.add_command(label="编辑", command=lambda: self._edit_preview_item(None, tree))
            menu.add_command(label="删除", command=lambda: self._delete_preview_item(tree))
            menu.post(event.x_root, event.y_root)
    
    def _edit_preview_item(self, event, tree):
        """编辑预览项目"""
        selected = tree.selection()
        if not selected:
            return
        
        item = selected[0]
        values = tree.item(item)['values']
        
        # 创建编辑窗口
        edit_window = tb.Toplevel(self.root)
        edit_window.title("编辑项目")
        edit_window.geometry("400x300")
        
        # 创建输入框
        ttk.Label(edit_window, text="物品:").grid(row=0, column=0, padx=5, pady=5)
        item_name = ttk.Entry(edit_window)
        item_name.insert(0, values[0])
        item_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="数量:").grid(row=1, column=0, padx=5, pady=5)
        quantity = ttk.Entry(edit_window)
        quantity.insert(0, values[1])
        quantity.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="单价:").grid(row=2, column=0, padx=5, pady=5)
        price = ttk.Entry(edit_window)
        price.insert(0, values[2])
        price.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="手续费:").grid(row=3, column=0, padx=5, pady=5)
        fee = ttk.Entry(edit_window)
        fee.insert(0, values[3])
        fee.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="总金额:").grid(row=4, column=0, padx=5, pady=5)
        total_amount = ttk.Entry(edit_window)
        total_amount.insert(0, values[4])
        total_amount.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(edit_window, text="备注:").grid(row=5, column=0, padx=5, pady=5)
        note = ttk.Entry(edit_window)
        note.insert(0, values[5])
        note.grid(row=5, column=1, padx=5, pady=5)
        
        def save_edit():
            try:
                new_values = (
                    item_name.get(),
                    int(quantity.get()),
                    int(price.get()),
                    int(fee.get()),
                    int(total_amount.get()),
                    note.get() if note.get() is not None else ''
                )
                tree.item(item, values=new_values)
                edit_window.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        ttk.Button(edit_window, text="保存", command=save_edit).grid(row=6, column=0, columnspan=2, pady=10)
    
    def _delete_preview_item(self, tree):
        """删除预览项目"""
        selected = tree.selection()
        if not selected:
            return
        if messagebox.askyesno("确认", "确定要删除选中的项目吗？"):
            for item in selected:
                tree.delete(item)
    
    def _confirm_import(self, tree, preview_data, preview_window):
        """自动识别数据类型并导入到正确的标签页，支持中英文字段名兼容，修复出库和监控类型判定及字段补全问题"""
        in_count = 0
        out_count = 0
        monitor_count = 0
        skipped = 0
        success = True
        for item in tree.get_children():
            values = tree.item(item)['values']
            data = {}
            for i, col in enumerate(tree['columns']):
                data[col] = values[i]
            # 字段兼容处理
            item_name = data.get('item_name') or data.get('物品')
            quantity = data.get('quantity') or data.get('数量') or data.get('入库数量')
            cost = data.get('cost') or data.get('入库花费')
            avg_cost = data.get('avg_cost') or data.get('入库均价')
            unit_price = data.get('unit_price') or data.get('单价')
            fee = data.get('fee') or data.get('手续费')
            total_amount = data.get('total_amount') or data.get('总金额')
            market_price = data.get('market_price') or data.get('一口价')
            target_price = data.get('target_price') or data.get('目标买入价')
            planned_price = data.get('planned_price') or data.get('计划卖出价')
            # 类型判断
            try:
                quantity_val = float(str(quantity).strip()) if quantity is not None and str(quantity).strip() != '' else 0
            except Exception:
                print(f"数量字段无法转换: {quantity}")
                quantity_val = 0
            try:
                unit_price_val = float(str(unit_price).strip()) if unit_price is not None and str(unit_price).strip() != '' else 0
            except Exception:
                print(f"单价字段无法转换: {unit_price}")
                unit_price_val = 0
            try:
                fee_val = float(str(fee).strip()) if fee is not None and str(fee).strip() != '' else 0
            except Exception:
                print(f"手续费字段无法转换: {fee}")
                fee_val = 0
            try:
                total_amount_val = float(str(total_amount).strip()) if total_amount is not None and str(total_amount).strip() != '' else 0
            except Exception:
                print(f"总金额字段无法转换: {total_amount}")
                total_amount_val = 0
            try:
                market_price_val = float(str(market_price).strip()) if market_price is not None and str(market_price).strip() != '' else 0
            except Exception:
                print(f"一口价字段无法转换: {market_price}")
                market_price_val = 0
            try:
                target_price_val = float(str(target_price).strip()) if target_price is not None and str(target_price).strip() != '' else 0
            except Exception:
                print(f"目标买入价字段无法转换: {target_price}")
                target_price_val = 0
            try:
                planned_price_val = float(str(planned_price).strip()) if planned_price is not None and str(planned_price).strip() != '' else 0
            except Exception:
                print(f"计划卖出价字段无法转换: {planned_price}")
                planned_price_val = 0
            # 入库数据
            if item_name and quantity_val and cost and avg_cost:
                try:
                    stock_in_data = {
                        'item_name': item_name,
                        'transaction_time': data.get('transaction_time') or data.get('当前时间') or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'quantity': quantity_val,
                        'cost': cost,
                        'avg_cost': avg_cost,
                        'note': data.get('note') or data.get('备注') or ''
                    }
                    self.db_manager.save_stock_in(stock_in_data)
                    self.db_manager.decrease_inventory(item_name, quantity_val)
                    in_count += 1
                    continue
                except Exception as e:
                    print(f"导入入库数据失败: {e}")
                    success = False
                    break
            # 出库数据（只要有物品、数量、单价、总金额即可，所有数值字段强制转float）
            if item_name and quantity_val and unit_price_val and total_amount_val:
                try:
                    stock_out_data = {
                        'item_name': item_name,
                        'transaction_time': data.get('transaction_time') or data.get('当前时间') or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'quantity': quantity_val,
                        'unit_price': unit_price_val,
                        'fee': fee_val,
                        'deposit': 0.0,
                        'total_amount': total_amount_val,
                        'note': data.get('note') or data.get('备注') or ''
                    }
                    self.db_manager.save_stock_out(stock_out_data)
                    out_count += 1
                    continue
                except Exception as e:
                    print(f"导入出库数据失败: {e}")
                    success = False
                    break
            # 监控数据（只要有物品、数量、一口价即可，其余字段补0/空）
            if item_name and quantity_val and market_price_val:
                try:
                    trade_monitor_data = {
                        'item_name': item_name,
                        'monitor_time': data.get('monitor_time') or data.get('当前时间') or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'quantity': quantity_val,
                        'market_price': market_price_val,
                        'target_price': target_price_val if target_price_val is not None else 0,
                        'planned_price': planned_price_val if planned_price_val is not None else 0,
                        'break_even_price': float(data.get('break_even_price') or data.get('保本卖出价') or 0),
                        'profit': float(data.get('profit') or data.get('利润') or 0),
                        'profit_rate': float(data.get('profit_rate') or data.get('利润率') or 0),
                        'strategy': data.get('strategy') or data.get('出库策略') or ''
                    }
                    self.db_manager.save_trade_monitor(trade_monitor_data)
                    monitor_count += 1
                    continue
                except Exception as e:
                    print(f"导入监控数据失败: {e}")
                    success = False
                    break
            # 无法识别类型，详细打印缺失的核心字段
            missing_fields = []
            if not item_name:
                missing_fields.append('物品')
            if not quantity_val:
                missing_fields.append('数量')
            if not (market_price_val or unit_price_val or cost or avg_cost or total_amount_val):
                missing_fields.append('价格相关字段')
            print(f"跳过无效数据: {data}，缺失: {','.join(missing_fields) if missing_fields else '类型不匹配'}")
            skipped += 1
        msg = "数据导入成功！"
        if in_count > 0:
            msg += f"\n入库数据：{in_count}条"
        if out_count > 0:
            msg += f"\n出库数据：{out_count}条"
        if monitor_count > 0:
            msg += f"\n监控数据：{monitor_count}条"
        if skipped > 0:
            msg += f"\n有{skipped}条无效数据已被自动跳过。"
        if success:
            messagebox.showinfo("成功", msg)
            self.refresh_all()
            if preview_window:
                preview_window.destroy()
        else:
            messagebox.showerror("错误", "部分数据导入失败，请检查数据格式是否正确")

    def create_stock_out_tab(self):
        """创建出库管理标签页"""
        stock_out_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(stock_out_frame, text="出库管理")
        
        # 出库表格
        columns = ('物品', '当前时间', '数量', '单价', '手续费', '总金额', '备注')
        self.stock_out_tree = ttk.Treeview(stock_out_frame, columns=columns, show='headings', height=16)
        for col in columns:
            self.stock_out_tree.heading(col, text=col, anchor='center')
            self.stock_out_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(stock_out_frame, orient="vertical", command=self.stock_out_tree.yview)
        self.stock_out_tree.configure(yscrollcommand=scrollbar.set)
        self.stock_out_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        
        # 右侧操作面板
        right_panel = ttk.Frame(stock_out_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        
        add_frame = ttk.LabelFrame(right_panel, text="添加出库", padding=10)
        add_frame.pack(fill='x', pady=8)
        ttk.Label(add_frame, text="物品:").grid(row=0, column=0, padx=5, pady=5)
        self.stock_out_item = ttk.Entry(add_frame)
        self.stock_out_item.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="数量:").grid(row=1, column=0, padx=5, pady=5)
        self.stock_out_quantity = ttk.Entry(add_frame)
        self.stock_out_quantity.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="单价:").grid(row=2, column=0, padx=5, pady=5)
        self.stock_out_price = ttk.Entry(add_frame)
        self.stock_out_price.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="手续费:").grid(row=3, column=0, padx=5, pady=5)
        self.stock_out_fee = ttk.Entry(add_frame)
        self.stock_out_fee.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="总金额:").grid(row=4, column=0, padx=5, pady=5)
        self.stock_out_total = ttk.Entry(add_frame)
        self.stock_out_total.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="备注:").grid(row=5, column=0, padx=5, pady=5)
        self.stock_out_note = ttk.Entry(add_frame)
        self.stock_out_note.grid(row=5, column=1, padx=5, pady=5, sticky='ew')
        add_frame.columnconfigure(1, weight=1)
        ttk.Button(add_frame, text="添加出库", command=self.add_stock_out).grid(row=6, column=0, columnspan=2, pady=10, sticky='ew')
        
        ttk.Button(right_panel, text="刷新出库记录", command=self.refresh_stock_out).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="上传图片自动识别导入", command=self.upload_ocr_import_stock_out).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="批量识别粘贴图片", command=self.batch_ocr_import_stock_out).pack(fill='x', pady=(0, 10), ipady=4)
        self.ocr_image_preview_frame_out = ttk.Frame(right_panel)
        self.ocr_image_preview_frame_out.pack(fill='x', pady=5)
        
        self.stock_out_menu = tb.Menu(self.stock_out_tree, tearoff=0)
        self.stock_out_menu.add_command(label="删除", command=self.delete_stock_out_item)
        self.stock_out_tree.bind("<Button-3>", self.show_stock_out_menu)
        # 新增：Ctrl+A全选
        self.stock_out_tree.bind('<Control-a>', lambda e: [self.stock_out_tree.selection_set(self.stock_out_tree.get_children()), 'break'])
    
    def edit_stock_out_item(self, event):
        item_id = self.stock_out_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.stock_out_tree.item(item_id)['values']
        edit_win = tb.Toplevel(self.root)
        edit_win.title("编辑出库记录")
        edit_win.minsize(440, 440)
        edit_win.configure(bg='#f4f8fb')
        style = ttk.Style()
        style.configure('Edit.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=('微软雅黑', 11))
        style.configure('Edit.TButton', font=('微软雅黑', 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        content_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        labels = ["物品", "时间", "数量", "单价", "手续费", "总金额", "备注"]
        types = [str, str, int, float, float, float, str]
        entries = []
        error_labels = []
        for i, (label, val, typ) in enumerate(zip(labels, values, types)):
            ttk.Label(content_frame, text=label+":", style='Edit.TLabel').grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
            entry = ttk.Entry(content_frame, validate='key', validatecommand=vcmd, style='Edit.TEntry') if vcmd else ttk.Entry(content_frame, style='Edit.TEntry')
            entry.insert(0, val)
            entry.grid(row=i*2, column=1, padx=12, pady=4, sticky='w')
            entries.append(entry)
            err = ttk.Label(content_frame, text="", foreground="red", background='#f4f8fb', font=('微软雅黑', 10))
            err.grid(row=i*2+1, column=0, columnspan=2, sticky='w', padx=12)
            error_labels.append(err)
        def save():
            new_vals = [e.get() for e in entries]
            valid = True
            for idx, (val, typ, err_lbl) in enumerate(zip(new_vals, types, error_labels)):
                err_lbl.config(text="")
                if typ is int:
                    if not val.isdigit():
                        err_lbl.config(text="请输入正整数")
                        entries[idx].focus_set()
                        valid = False
                        break
                elif typ is float:
                    try:
                        float(val)
                    except Exception:
                        err_lbl.config(text="请输入数字")
                        entries[idx].focus_set()
                        valid = False
                        break
            if not valid:
                return
            try:
                new_vals[2] = int(new_vals[2])
                new_vals[3] = float(new_vals[3])
                new_vals[4] = float(new_vals[4])
                new_vals[5] = float(new_vals[5])
            except Exception:
                error_labels[2].config(text="数量/单价/手续费/总金额必须为数字")
                entries[2].focus_set()
                return
            if not messagebox.askyesno("确认", "确定要保存修改吗？"):
                return
            self.db_manager.delete_stock_out(values[0], values[1])
            self.db_manager.save_stock_out({
                'item_name': new_vals[0],
                'transaction_time': new_vals[1],
                'quantity': new_vals[2],
                'unit_price': new_vals[3],
                'fee': new_vals[4],
                'deposit': 0.0,  # 新增字段，防止错位
                'total_amount': new_vals[5],
                'note': new_vals[6]
            })
            self.refresh_stock_out()
            edit_win.destroy()
        button_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        ttk.Button(button_frame, text="保存", command=save, style='Edit.TButton').pack(pady=6, ipadx=40)

    def refresh_ocr_image_preview_out(self):
        for widget in self.ocr_image_preview_frame_out.winfo_children():
            widget.destroy()
        for idx, img in enumerate(self._pending_ocr_images_out):
            thumb = img.copy()
            thumb.thumbnail((80, 80))
            photo = ImageTk.PhotoImage(thumb)
            lbl = ttk.Label(self.ocr_image_preview_frame_out, image=photo)
            lbl.image = photo
            lbl.grid(row=0, column=idx*2, padx=4, pady=2)
            btn = ttk.Button(self.ocr_image_preview_frame_out, text='删除', width=5, command=lambda i=idx: self.delete_ocr_image_out(i))
            btn.grid(row=1, column=idx*2, padx=4, pady=2)

    def delete_ocr_image_out(self, idx):
        del self._pending_ocr_images_out[idx]
        self.refresh_ocr_image_preview_out()

    def paste_ocr_import_stock_out(self, event=None):
        img = ImageGrab.grabclipboard()
        if isinstance(img, list):
            img = img[0] if img else None
        if img is None or not hasattr(img, 'save'):
            messagebox.showwarning("粘贴失败", "剪贴板中没有图片")
            return
        self._pending_ocr_images_out.append(img)
        self.refresh_ocr_image_preview_out()
        messagebox.showinfo("已添加", f"已添加{len(self._pending_ocr_images_out)}张图片，点击批量识别可统一导入。")

    def batch_ocr_import_stock_out(self):
        if not self._pending_ocr_images_out:
            messagebox.showwarning("无图片", "请先粘贴图片")
            return
        all_preview_data = []
        for img in self._pending_ocr_images_out:
            try:
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                url = "http://sql.didiba.uk:1224/api/ocr"
                payload = {
                    "base64": img_b64,
                    "options": {
                        "data.format": "text"
                    }
                }
                headers = {"Content-Type": "application/json"}
                resp = requests.post(url, json=payload, headers=headers, timeout=20)
                resp.raise_for_status()
                ocr_result = resp.json()
                text = ocr_result.get('data')
                if not text:
                    continue
                # 使用新的解析函数处理OCR文本
                parsed_data = self.parse_stock_out_ocr_text(text)
                if parsed_data:
                    all_preview_data.append(parsed_data)
            except Exception as e:
                print(f"OCR识别失败: {e}")
        if all_preview_data:
            # 统一用自动分流的show_ocr_preview，出库管理用中文表头
            self.show_ocr_preview(
                all_preview_data,
                columns=('物品', '数量', '单价', '手续费', '总金额', '备注'),
                field_map=['item_name', 'quantity', 'unit_price', 'fee', 'total_amount', 'note']
            )
        else:
            messagebox.showwarning("无有效数据", "未识别到有效的出库数据！")
        self._pending_ocr_images_out.clear()
        self.refresh_ocr_image_preview_out()

    def show_stock_out_menu(self, event):
        """显示入库右键菜单"""
        item = self.stock_out_tree.identify_row(event.y)
        if item:
            if item not in self.stock_out_tree.selection():
                self.stock_out_tree.selection_set(item)
            self.stock_out_menu.post(event.x_root, event.y_root)

    def delete_stock_out_item(self):
        """批量删除出库记录"""
        selected_items = self.stock_out_tree.selection()
        if not selected_items:
            return
        names = [self.stock_out_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下出库记录吗？\n" + "，".join(str(n) for n in names)
        deleted_data = []
        if messagebox.askyesno("确认", msg):
            for item in selected_items:
                values = self.stock_out_tree.item(item)['values']
                self.db_manager.delete_stock_out(values[0], values[1])
                deleted_data.append(values)
            self.refresh_stock_out()
            self.log_operation('删除', '出库管理', deleted_data)
    
    def upload_ocr_import_stock_out(self):
        file_paths = fd.askopenfilenames(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_paths:
            return
        try:
            from PIL import Image
            count = 0
            for file_path in file_paths:
                img = Image.open(file_path)
                self._pending_ocr_images_out.append(img)
                count += 1
            self.refresh_ocr_image_preview_out()
            messagebox.showinfo("已添加", f"已添加{count}张图片，点击批量识别可统一导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def create_trade_monitor_tab(self):
        """创建交易监控标签页"""
        monitor_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(monitor_frame, text="交易监控")
        # 交易监控表格
        columns = ('物品', '当前时间', '数量', '一口价', '目标买入价', '计划卖出价', '保本卖出价', '利润', '利润率', '出库策略')
        self.monitor_tree = ttk.Treeview(monitor_frame, columns=columns, show='headings', height=16)
        # 设置列标题和内容居中
        for col in columns:
            self.monitor_tree.heading(col, text=col, anchor='center')
            self.monitor_tree.column(col, width=120, anchor='center')
        # 添加滚动条
        scrollbar = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.monitor_tree.yview)
        self.monitor_tree.configure(yscrollcommand=scrollbar.set)
        # 布局
        self.monitor_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        # 右侧操作面板（固定宽度，无滚动条）
        right_panel = ttk.Frame(monitor_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        # 添加监控记录
        add_frame = ttk.LabelFrame(right_panel, text="添加监控", padding=10)
        add_frame.pack(fill='x', pady=8)
        ttk.Label(add_frame, text="物品:").grid(row=0, column=0, padx=5, pady=5)
        self.monitor_item = ttk.Entry(add_frame)
        self.monitor_item.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="数量:").grid(row=1, column=0, padx=5, pady=5)
        self.monitor_quantity = ttk.Entry(add_frame)
        self.monitor_quantity.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="一口价:").grid(row=2, column=0, padx=5, pady=5)
        self.monitor_price = ttk.Entry(add_frame)
        self.monitor_price.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="目标买入价:").grid(row=3, column=0, padx=5, pady=5)
        self.monitor_target_price = ttk.Entry(add_frame)
        self.monitor_target_price.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="计划卖出价:").grid(row=4, column=0, padx=5, pady=5)
        self.monitor_planned_price = ttk.Entry(add_frame)
        self.monitor_planned_price.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(add_frame, text="入库策略:").grid(row=5, column=0, padx=5, pady=5)
        self.monitor_strategy = ttk.Entry(add_frame)
        self.monitor_strategy.grid(row=5, column=1, padx=5, pady=5, sticky='ew')
        add_frame.columnconfigure(1, weight=1)
        ttk.Button(add_frame, text="添加监控", command=self.add_monitor).grid(row=6, column=0, columnspan=2, pady=10, sticky='ew')
        # 刷新按钮
        ttk.Button(right_panel, text="刷新监控", command=self.refresh_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="上传图片自动识别导入", command=self.upload_ocr_import_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="批量识别粘贴图片", command=self.batch_ocr_import_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        self.ocr_image_preview_frame_monitor = ttk.Frame(right_panel)
        self.ocr_image_preview_frame_monitor.pack(fill='x', pady=5)
        right_panel.bind_all('<Control-v>', self.paste_ocr_import_monitor)
        self.monitor_tree.bind("<Double-1>", self.edit_monitor_item)
        # 添加右键菜单支持批量删除
        self.monitor_menu = tb.Menu(self.monitor_tree, tearoff=0)
        self.monitor_menu.add_command(label="删除", command=self.delete_monitor_item)
        self.monitor_tree.bind("<Button-3>", self.show_monitor_menu)
    
    def show_monitor_menu(self, event):
        item = self.monitor_tree.identify_row(event.y)
        if not item:
            return
        # 只有当当前行未被选中时，才只选中该行，否则保持多选
        if item not in self.monitor_tree.selection():
            self.monitor_tree.selection_set(item)
        self.monitor_menu.post(event.x_root, event.y_root)

    def delete_monitor_item(self):
        """批量删除监控记录"""
        selected_items = self.monitor_tree.selection()
        if not selected_items:
            return
        names = [self.monitor_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下监控记录吗？\n" + "，".join(str(n) for n in names)
        deleted_data = []
        if messagebox.askyesno("确认", msg):
            for item in selected_items:
                values = self.monitor_tree.item(item)['values']
                self.db_manager.delete_trade_monitor(values[0], values[1])
                deleted_data.append(values)
            self.refresh_monitor()
            self.log_operation('删除', '交易监控', deleted_data)
    
    def upload_ocr_import_monitor(self):
        file_paths = fd.askopenfilenames(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_paths:
            return
        try:
            from PIL import Image
            count = 0
            for file_path in file_paths:
                img = Image.open(file_path)
                self._pending_ocr_images_monitor.append(img)
                count += 1
            self.refresh_ocr_image_preview_monitor()
            messagebox.showinfo("已添加", f"已添加{count}张图片，点击批量识别可统一导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def create_analysis_tab(self):
        """创建分析报告标签页"""
        analysis_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(analysis_frame, text="分析报告")
        
        # 创建分析结果文本框
        self.analysis_text = tb.Text(analysis_frame, wrap=tb.WORD, width=80, height=30, font=('微软雅黑', 11))
        self.analysis_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 分析按钮
        button_frame = tb.Frame(analysis_frame, padding=8)
        button_frame.pack(fill='x', pady=8)
        
        ttk.Button(button_frame, text="生成分析报告", command=self.generate_analysis).pack(side='left', padx=8)
        ttk.Button(button_frame, text="保存报告", command=self.save_analysis).pack(side='left', padx=8)
    
    def create_log_tab(self):
        """创建日志标签页"""
        log_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_frame, text="操作日志")
        columns = ("操作类型", "标签页", "操作时间")
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show='headings', height=18)
        for col in columns:
            self.log_tree.heading(col, text=col, anchor='center')
            self.log_tree.column(col, width=160, anchor='center')
        self.log_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        # 滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        # 筛选区（仅保留筛选条件）
        filter_frame = ttk.Frame(log_frame, padding=4)
        filter_frame.pack(side='top', fill='x')
        self.filter_type = StringVar(value="全部")
        self.filter_tab = StringVar(value="全部")
        self.filter_reverted = StringVar(value="全部")
        self.log_search_var = StringVar()
        self.log_page = 1
        self.log_page_size = 20
        self.log_total_pages = 1
        ttk.Label(filter_frame, text="操作类型:").pack(side='left')
        ttk.Combobox(filter_frame, textvariable=self.filter_type, values=["全部", "添加", "删除"], width=8, state='readonly').pack(side='left', padx=2)
        ttk.Label(filter_frame, text="标签页:").pack(side='left')
        ttk.Combobox(filter_frame, textvariable=self.filter_tab, values=["全部", "入库管理", "出库管理", "交易监控"], width=10, state='readonly').pack(side='left', padx=2)
        ttk.Label(filter_frame, text="已回退:").pack(side='left')
        ttk.Combobox(filter_frame, textvariable=self.filter_reverted, values=["全部", "是", "否"], width=6, state='readonly').pack(side='left', padx=2)
        ttk.Label(filter_frame, text="关键字:").pack(side='left')
        ttk.Entry(filter_frame, textvariable=self.log_search_var, width=12).pack(side='left', padx=2)
        # 新的按钮区（下方）
        btn_frame = ttk.Frame(log_frame, padding=8)
        btn_frame.pack(side='bottom', fill='x', pady=8)
        ttk.Button(btn_frame, text="搜索", command=self._log_search).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="上一页", command=self.log_prev_page).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="下一页", command=self.log_next_page).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="导出日志", command=self.export_log_csv).pack(side='left', padx=2)
        self.log_page_label = ttk.Label(btn_frame, text="第1/1页")
        self.log_page_label.pack(side='left', padx=4)
        self.log_jump_var = StringVar()
        ttk.Entry(btn_frame, textvariable=self.log_jump_var, width=4).pack(side='left')
        ttk.Button(btn_frame, text="跳转", command=self.log_jump_page).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="回退当前操作", command=self.undo_last_operation).pack(side='right', padx=8)
        ttk.Button(btn_frame, text="前进(撤销回退)", command=self.redo_last_operation).pack(side='right', padx=8)
        # 日志详情弹窗
        def show_log_detail(event):
            item = self.log_tree.identify_row(event.y)
            if not item:
                return
            values = self.log_tree.item(item)['values']
            if not values:
                return
            op_type, tab_name, timestamp, data = values
            # 创建详情窗口
            detail_window = tk.Toplevel(self.root)
            detail_window.title("操作详情")
            detail_window.geometry("600x400")
            # 创建文本框
            text = tk.Text(detail_window, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            # 添加滚动条
            scrollbar = ttk.Scrollbar(text, command=text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text.config(yscrollcommand=scrollbar.set)
            # 显示详情
            detail = f"操作类型: {op_type}\n"
            detail += f"标签页: {tab_name}\n"
            detail += f"时间: {timestamp}\n"
            detail += "数据:\n"
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    pass
            if isinstance(data, dict):
                for key, value in data.items():
                    detail += f"{key}: {value}\n"
            elif isinstance(data, list):
                for i, row in enumerate(data):
                    if isinstance(row, dict):
                        detail += f"[{i}]\n"
                        for key, value in row.items():
                            detail += f"  {key}: {value}\n"
                    else:
                        detail += f"  [{i}] {row}\n"
            else:
                import json
                try:
                    data_str = json.dumps(data, ensure_ascii=False, indent=2)
                    detail += data_str
                except Exception:
                    detail += str(data)
            text.insert(tk.END, detail)
            text.config(state=tk.DISABLED)
        self.log_tree.bind('<Double-1>', show_log_detail)

    def _log_search(self):
        self.log_page = 1
        self.refresh_log_tab()

    def log_prev_page(self):
        if self.log_page > 1:
            self.log_page -= 1
            self.refresh_log_tab()

    def log_next_page(self):
        self.log_page += 1
        self.refresh_log_tab()

    def refresh_log_tab(self):
        # 清空并重新加载日志，支持筛选
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        type_f = self.filter_type.get()
        tab_f = self.filter_tab.get()
        rev_f = self.filter_reverted.get()
        keyword = self.log_search_var.get().strip() or None
        # 计算总页数
        total_count = self.db_manager.count_operation_logs(
            tab_name=None if tab_f == "全部" else tab_f,
            op_type=None if type_f == "全部" else type_f,
            keyword=keyword,
            reverted=None if rev_f == "全部" else (rev_f == "是")
        )
        self.log_total_pages = max(1, (total_count + self.log_page_size - 1) // self.log_page_size)
        if self.log_page > self.log_total_pages:
            self.log_page = self.log_total_pages
        self.log_page_label.config(text=f"第{self.log_page}/{self.log_total_pages}页")
        logs = self.db_manager.get_operation_logs(
            tab_name=None if tab_f == "全部" else tab_f,
            op_type=None if type_f == "全部" else type_f,
            keyword=keyword,
            reverted=None if rev_f == "全部" else (rev_f == "是"),
            page=self.log_page,
            page_size=self.log_page_size
        )
        self._current_log_page_data = logs  # 保存当前页日志
        for log in logs:
            self.log_tree.insert('', 'end', values=(
                log['操作类型'] + ("（已回退）" if log.get('已回退') else ""),
                log['标签页'],
                log['操作时间']
            ))

    def export_log_csv(self):
        import pandas as pd
        type_f = self.filter_type.get()
        tab_f = self.filter_tab.get()
        rev_f = self.filter_reverted.get()
        keyword = self.log_search_var.get().strip() or None
        logs = self.db_manager.get_operation_logs(
            tab_name=None if tab_f == "全部" else tab_f,
            op_type=None if type_f == "全部" else type_f,
            keyword=keyword,
            reverted=None if rev_f == "全部" else (rev_f == "是"),
            page=1, page_size=10000
        )
        if not logs:
            messagebox.showinfo("提示", "没有可导出的日志数据")
            return
        df = pd.DataFrame(logs)
        df.to_csv("operation_logs_export.csv", index=False, encoding="utf-8-sig")
        messagebox.showinfo("导出成功", "日志已导出到 operation_logs_export.csv")

    def log_operation(self, op_type, tab_name, data=None, reverted=False):
        """记录操作日志，data为被操作的数据内容，reverted为是否已回退"""
        log = {
            '操作类型': op_type,
            '标签页': tab_name,
            '操作时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '数据': data,
            '已回退': reverted
        }
        # 保存到数据库
        self.db_manager.save_operation_log(op_type, tab_name, data, reverted)
        # 内存同步（可选，便于撤销/重做等）
        self.operation_logs.append(log)
        if not reverted:
            self.undo_stack.append(log)
        self.log_tree.insert('', 'end', values=(
            log['操作类型'] + ("（已回退）" if reverted else ""),
            log['标签页'],
            log['操作时间']
        ))

    def refresh_log_tab(self):
        # 清空并重新加载日志，支持筛选
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        type_f = self.filter_type.get()
        tab_f = self.filter_tab.get()
        rev_f = self.filter_reverted.get()
        keyword = self.log_search_var.get().strip() or None
        # 计算总页数
        total_count = self.db_manager.count_operation_logs(
            tab_name=None if tab_f == "全部" else tab_f,
            op_type=None if type_f == "全部" else type_f,
            keyword=keyword,
            reverted=None if rev_f == "全部" else (rev_f == "是")
        )
        self.log_total_pages = max(1, (total_count + self.log_page_size - 1) // self.log_page_size)
        if self.log_page > self.log_total_pages:
            self.log_page = self.log_total_pages
        self.log_page_label.config(text=f"第{self.log_page}/{self.log_total_pages}页")
        logs = self.db_manager.get_operation_logs(
            tab_name=None if tab_f == "全部" else tab_f,
            op_type=None if type_f == "全部" else type_f,
            keyword=keyword,
            reverted=None if rev_f == "全部" else (rev_f == "是"),
            page=self.log_page,
            page_size=self.log_page_size
        )
        self._current_log_page_data = logs  # 保存当前页日志
        for log in logs:
            self.log_tree.insert('', 'end', values=(
                log['操作类型'] + ("（已回退）" if log.get('已回退') else ""),
                log['标签页'],
                log['操作时间']
            ))

    def undo_last_operation(self):
        # 跳过已回退的操作
        while self.undo_stack and self.undo_stack[-1].get('已回退'):
            self.undo_stack.pop()
        if not self.undo_stack:
            messagebox.showinfo("提示", "没有可回退的操作！")
            return
        last_log = self.undo_stack.pop()
        op_type = last_log['操作类型']
        tab = last_log['标签页']
        data = last_log.get('数据')
        if op_type == '添加' and tab == '入库管理':
            if self.stock_in_tree.get_children():
                last_item = self.stock_in_tree.get_children()[0]
                values = self.stock_in_tree.item(last_item)['values']
                self.db_manager.delete_stock_in(values[0], values[1])
                self.refresh_stock_in()
                self.refresh_inventory()
        elif op_type == '添加' and tab == '出库管理':
            if self.stock_out_tree.get_children():
                last_item = self.stock_out_tree.get_children()[0]
                values = self.stock_out_tree.item(last_item)['values']
                self.db_manager.delete_stock_out(values[0], values[1])
                self.refresh_stock_out()
                self.refresh_inventory()
        elif op_type == '添加' and tab == '交易监控':
            if self.monitor_tree.get_children():
                last_item = self.monitor_tree.get_children()[0]
                values = self.monitor_tree.item(last_item)['values']
                self.db_manager.delete_trade_monitor(values[0], values[1])
                self.refresh_monitor()
        elif op_type == '删除' and tab == '入库管理' and data:
            # 恢复被删入库记录
            for values in data:
                self.db_manager.save_stock_in({
                    'item_name': values[0],
                    'transaction_time': values[1],
                    'quantity': int(values[2]),
                    'cost': float(values[3]),
                    'avg_cost': float(values[4]),
                    'note': values[5] if values[5] is not None else ''
                })
            self.refresh_stock_in()
            self.refresh_inventory()
        elif op_type == '删除' and tab == '出库管理' and data:
            for values in data:
                self.db_manager.save_stock_out({
                    'item_name': values[0],
                    'transaction_time': values[1],
                    'quantity': int(values[2]),
                    'unit_price': float(values[3]),
                    'fee': float(values[4]),
                    'total_amount': float(values[5]),
                    'note': values[6] if values[6] is not None else ''
                })
            self.refresh_stock_out()
            self.refresh_inventory()
        elif op_type == '删除' and tab == '交易监控' and data:
            for values in data:
                self.db_manager.save_trade_monitor({
                    'item_name': values[0],
                    'monitor_time': values[1],
                    'quantity': int(values[2]),
                    'market_price': float(values[3]),
                    'target_price': float(values[4]),
                    'planned_price': float(values[5]),
                    'break_even_price': float(values[6]),
                    'profit': float(values[7]),
                    'profit_rate': float(values[8].strip('%')),
                    'strategy': values[9]
                })
            self.refresh_monitor()
        else:
            messagebox.showinfo("提示", "该操作类型暂不支持回退！")
            return
        # 标记日志为已回退
        last_log['已回退'] = True
        self.redo_stack.append(last_log)
        self.refresh_log_tab()
        self._save_operation_logs()
        messagebox.showinfo("提示", f"已回退操作: {op_type} - {tab}")

    def redo_last_operation(self):
        # 前进（撤销回退）
        while self.redo_stack and not self.redo_stack[-1].get('已回退'):
            self.redo_stack.pop()
        if not self.redo_stack:
            messagebox.showinfo("提示", "没有可前进的操作！")
            return
        last_log = self.redo_stack.pop()
        op_type = last_log['操作类型']
        tab = last_log['标签页']
        data = last_log.get('数据')
        # 恢复操作
        if op_type == '添加' and tab == '入库管理' and data:
            for values in data if isinstance(data, list) else [data]:
                self.db_manager.save_stock_in({
                    'item_name': values[0],
                    'transaction_time': values[1],
                    'quantity': int(values[2]),
                    'cost': float(values[3]),
                    'avg_cost': float(values[4]),
                    'note': values[5] if values[5] is not None else ''
                })
            self.refresh_stock_in()
            self.refresh_inventory()
        elif op_type == '添加' and tab == '出库管理' and data:
            for values in data if isinstance(data, list) else [data]:
                self.db_manager.save_stock_out({
                    'item_name': values[0],
                    'transaction_time': values[1],
                    'quantity': int(values[2]),
                    'unit_price': float(values[3]),
                    'fee': float(values[4]),
                    'total_amount': float(values[5]),
                    'note': values[6] if values[6] is not None else ''
                })
            self.refresh_stock_out()
            self.refresh_inventory()
        elif op_type == '添加' and tab == '交易监控' and data:
            for values in data if isinstance(data, list) else [data]:
                self.db_manager.save_trade_monitor({
                    'item_name': values[0],
                    'monitor_time': values[1],
                    'quantity': int(values[2]),
                    'market_price': float(values[3]),
                    'target_price': float(values[4]),
                    'planned_price': float(values[5]),
                    'break_even_price': float(values[6]),
                    'profit': float(values[7]),
                    'profit_rate': float(values[8].strip('%')),
                    'strategy': values[9]
                })
            self.refresh_monitor()
        elif op_type == '删除' and tab == '入库管理' and data:
            for values in data:
                self.db_manager.delete_stock_in(values[0], values[1])
            self.refresh_stock_in()
            self.refresh_inventory()
        elif op_type == '删除' and tab == '出库管理' and data:
            for values in data:
                self.db_manager.delete_stock_out(values[0], values[1])
            self.refresh_stock_out()
            self.refresh_inventory()
        elif op_type == '删除' and tab == '交易监控' and data:
            for values in data:
                self.db_manager.delete_trade_monitor(values[0], values[1])
            self.refresh_monitor()
        else:
            messagebox.showinfo("提示", "该操作类型暂不支持前进！")
            return
        last_log['已回退'] = False
        self.undo_stack.append(last_log)
        self.refresh_log_tab()
        self._save_operation_logs()
        messagebox.showinfo("提示", f"已恢复操作: {op_type} - {tab}")

    def load_saved_data(self):
        """从数据库加载数据"""
        try:
            # 加载库存数据
            inventory_data = self.db_manager.get_inventory()
            for item in inventory_data:
                try:
                    _, item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value, *_ = item
                    self.inventory_tree.insert('', 'end', values=(
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
                    self.stock_in_tree.insert('', 'end', values=(
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
                    self.stock_out_tree.insert('', 'end', values=(
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
                    self.monitor_tree.insert('', 'end', values=(
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
    
    def refresh_all(self):
        """刷新所有显示"""
        self.refresh_inventory()
        self.refresh_stock_in()
        self.refresh_stock_out()
        self.refresh_monitor()
    
    def refresh_inventory(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
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
            self.inventory_tree.insert('', 'end', values=(
                item,
                int(remain_qty),
                str(int(round(in_avg))),
                str(int(round(in_avg))),  # 保本均价=入库均价
                str(int(round(out_avg))),
                str(int(round(profit))),
                f"{int(round(profit_rate))}%",
                f"{total_profit/10000:.2f}万",  # 成交利润额以万为单位
                f"{value/10000:.2f}万"  # 库存价值以万为单位
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
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        for row in table_data:
            self.inventory_tree.insert('', 'end', values=row)

    def refresh_stock_in(self):
        for item in self.stock_in_tree.get_children():
            self.stock_in_tree.delete(item)
        stock_in_data = self.db_manager.get_stock_in()
        filter_text = self.stock_in_filter_var.get().strip()
        filtered = []
        for item in stock_in_data:
            try:
                _, item_name, transaction_time, quantity, cost, avg_cost, note, *_ = item
            except Exception as e:
                messagebox.showerror("数据结构异常", f"入库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nitem={item}")
                continue
            if not filter_text or filter_text in str(item_name):
                filtered.append((item_name, transaction_time, quantity, cost, avg_cost, note))
        total = [0, 0, 0]  # 数量、花费、均价合计
        for item_name, transaction_time, quantity, cost, avg_cost, note in filtered:
            self.stock_in_tree.insert('', 'end', values=(
                item_name,
                transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                int(quantity),
                int(round(cost)),
                int(round(avg_cost)),
                note if note is not None else ''
            ))
            try:
                total[0] += int(quantity)
                total[1] += int(round(cost))
                total[2] += int(round(avg_cost))
            except:
                pass
        # 合计行
        if filter_text and filtered:
            self.stock_in_tree.insert('', 'end', values=(
                '合计', '', total[0], total[1], total[2]//len(filtered), ''
            ))

    def refresh_stock_out(self):
        for item in self.stock_out_tree.get_children():
            self.stock_out_tree.delete(item)
        records = self.db_manager.get_stock_out()
        for record in records:
            try:
                _, item_name, transaction_time, quantity, unit_price, fee, deposit, total_amount, note, *_ = record
                values = (
                    item_name,
                    transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                    int(quantity),
                    int(float(unit_price)),
                    int(float(fee)),
                    int(float(total_amount)),
                    note if note is not None else ''
                )
                self.stock_out_tree.insert('', 'end', values=values)
            except Exception as e:
                messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nrecord={record}")
                continue

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
        for item in self.monitor_tree.get_children():
            self.monitor_tree.delete(item)
        for row in table_data:
            self.monitor_tree.insert('', 'end', values=row)

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
            self.log_operation('添加', '入库管理')
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
            self.log_operation('添加', '出库管理')
            messagebox.showinfo("成功", "出库记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
    
    def add_monitor(self):
        """添加监控记录"""
        try:
            item = self.monitor_item.get()
            quantity = int(self.monitor_quantity.get())
            price = float(self.monitor_price.get())
            target_price = float(self.monitor_target_price.get())
            planned_price = float(self.monitor_planned_price.get())
            strategy = self.monitor_strategy.get()
            break_even_price = target_price * 1.05
            profit = price - target_price
            profit_rate = (profit / target_price) * 100
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db_manager.save_trade_monitor({
                'item_name': item,
                'monitor_time': now,
                'quantity': quantity,
                'market_price': price,
                'target_price': target_price,
                'planned_price': planned_price,
                'break_even_price': break_even_price,
                'profit': profit,
                'profit_rate': profit_rate,
                'strategy': strategy
            })
            self.refresh_monitor()
            self.monitor_item.delete(0, 'end')
            self.monitor_quantity.delete(0, 'end')
            self.monitor_price.delete(0, 'end')
            self.monitor_target_price.delete(0, 'end')
            self.monitor_planned_price.delete(0, 'end')
            self.monitor_strategy.delete(0, 'end')
            self.log_operation('添加', '交易监控')
            messagebox.showinfo("成功", "监控记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
    
    def generate_analysis(self):
        """生成分析报告"""
        self.analysis_text.delete(1.0, tb.END)
        # 添加库存状态
        self.analysis_text.insert(tb.END, "=== 库存状态 ===\n")
        for item in self.inventory_tree.get_children():
            try:
                values = self.inventory_tree.item(item)['values']
                item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value, *_ = values
                self.analysis_text.insert(tb.END, 
                    f"物品: {item_name}, 库存数: {int(quantity)}, 总入库均价: {int(avg_price)}, "
                    f"保本均价: {int(break_even_price)}, 总出库均价: {int(selling_price)}, 利润: {int(profit)}, "
                    f"利润率: {values[6]}, 成交利润额: {int(total_profit)}, 库存价值: {int(inventory_value)}\n")
            except Exception as e:
                messagebox.showerror("数据结构异常", f"inventory_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                continue
        # 添加入库统计
        self.analysis_text.insert(tb.END, "\n=== 入库统计 ===\n")
        for item in self.stock_in_tree.get_children():
            try:
                values = self.stock_in_tree.item(item)['values']
                item_name, transaction_time, quantity, cost, avg_cost, note, *_ = values
                self.analysis_text.insert(tb.END,
                    f"物品: {item_name}, 时间: {transaction_time}, 数量: {int(quantity)}, "
                    f"花费: {int(round(cost))}, 均价: {int(round(avg_cost))}, 备注: {note}\n")
            except Exception as e:
                messagebox.showerror("数据结构异常", f"stock_in_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                continue
        # 添加出库统计
        self.analysis_text.insert(tb.END, "\n=== 出库统计 ===\n")
        for item in self.stock_out_tree.get_children():
            try:
                values = self.stock_out_tree.item(item)['values']
                item_name, transaction_time, quantity, unit_price, fee, total_amount, note, *_ = values
                self.analysis_text.insert(tb.END,
                    f"物品: {item_name}, 时间: {transaction_time}, 数量: {int(quantity)}, "
                    f"单价: {int(unit_price)}, 手续费: {int(fee)}, 总金额: {int(total_amount)}, 备注: {note}\n"
                )
            except Exception as e:
                messagebox.showerror("数据结构异常", f"stock_out_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                continue
        # 添加监控统计
        self.analysis_text.insert(tb.END, "\n=== 监控统计 ===\n")
        for item in self.monitor_tree.get_children():
            try:
                values = self.monitor_tree.item(item)['values']
                item_name, transaction_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = values
                self.analysis_text.insert(tb.END,
                    f"物品: {item_name}, 时间: {transaction_time}, 数量: {int(quantity)}, "
                    f"一口价: {float(market_price):.2f}, 目标买入价: {float(target_price):.2f}, 计划卖出价: {float(planned_price):.2f}, "
                    f"保本卖出价: {float(break_even_price):.2f}, 利润: {float(profit):.2f}, 利润率: {profit_rate}, "
                    f"出库策略: {strategy}\n"
                )
            except Exception as e:
                messagebox.showerror("数据结构异常", f"monitor_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                continue
    
    def save_analysis(self):
        """保存分析报告"""
        try:
            with open("analysis_report.txt", "w", encoding="utf-8") as f:
                f.write(self.analysis_text.get(1.0, tb.END))
            messagebox.showinfo("成功", "分析报告已保存到 analysis_report.txt")
        except Exception as e:
            messagebox.showerror("错误", f"保存报告失败: {str(e)}")

    def save_all_data(self):
        """保存所有数据到数据库"""
        try:
            # 保存库存数据
            for item in self.inventory_tree.get_children():
                try:
                    values = self.inventory_tree.item(item)['values']
                    item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value, *_ = values
                    self.db_manager.save_inventory({
                        'item_name': item_name,
                        'quantity': int(quantity),
                        'avg_price': float(avg_price),
                        'break_even_price': float(break_even_price),
                        'selling_price': float(selling_price),
                        'profit': float(profit),
                        'profit_rate': float(profit_rate.strip('%')),
                        'total_profit': float(total_profit),
                        'inventory_value': float(inventory_value)
                    })
                except Exception as e:
                    messagebox.showerror("数据结构异常", f"inventory_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                    continue
            # 保存入库记录
            for item in self.stock_in_tree.get_children():
                try:
                    values = self.stock_in_tree.item(item)['values']
                    item_name, transaction_time, quantity, cost, avg_cost, note, *_ = values
                    self.db_manager.save_stock_in({
                        'item_name': item_name,
                        'transaction_time': transaction_time,
                        'quantity': int(quantity),
                        'cost': float(cost),
                        'avg_cost': float(avg_cost),
                        'note': note if note is not None else ''
                    })
                except Exception as e:
                    messagebox.showerror("数据结构异常", f"stock_in_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                    continue
            # 保存出库记录
            for item in self.stock_out_tree.get_children():
                try:
                    values = self.stock_out_tree.item(item)['values']
                    item_name, transaction_time, quantity, unit_price, fee, total_amount, note, *_ = values
                    self.db_manager.save_stock_out({
                        'item_name': item_name,
                        'transaction_time': transaction_time,
                        'quantity': int(quantity),
                        'unit_price': float(unit_price),
                        'fee': float(fee),
                        'total_amount': float(total_amount),
                        'note': note if note is not None else ''
                    })
                except Exception as e:
                    messagebox.showerror("数据结构异常", f"stock_out_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                    continue
            # 保存监控记录
            for item in self.monitor_tree.get_children():
                try:
                    values = self.monitor_tree.item(item)['values']
                    item_name, transaction_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = values
                    self.db_manager.save_trade_monitor({
                        'item_name': item_name,
                        'monitor_time': transaction_time,
                        'quantity': int(quantity),
                        'market_price': float(market_price),
                        'target_price': float(target_price),
                        'planned_price': float(planned_price),
                        'break_even_price': float(break_even_price),
                        'profit': float(profit),
                        'profit_rate': float(profit_rate),
                        'strategy': strategy
                    })
                except Exception as e:
                    messagebox.showerror("数据结构异常", f"monitor_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                    continue
            messagebox.showinfo("成功", "所有数据已保存到数据库")
        except Exception as e:
            messagebox.showerror("错误", f"保存数据失败: {str(e)}")

    def export_reports(self):
        import pandas as pd
        import os
        from tkinter import filedialog
        try:
            # 收集所有表格数据
            inventory_data = [self.inventory_tree.item(item)['values'] for item in self.inventory_tree.get_children()]
            stock_in_data = [self.stock_in_tree.item(item)['values'] for item in self.stock_in_tree.get_children()]
            stock_out_data = [self.stock_out_tree.item(item)['values'] for item in self.stock_out_tree.get_children()]
            monitor_data = [self.monitor_tree.item(item)['values'] for item in self.monitor_tree.get_children()]

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
                for item in self.inventory_tree.get_children():
                    try:
                        values = self.inventory_tree.item(item)['values']
                        item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value, *_ = values
                        # 将数字字段转换为整数
                        formatted_values = [
                            item_name,  # 物品名称
                            str(int(quantity)),  # 库存数
                            str(int(avg_price)),  # 总入库均价
                            str(int(break_even_price)),  # 保本均价
                            str(int(selling_price)),  # 总出库均价
                            str(int(profit)),  # 利润
                            values[6],  # 利润率
                            str(int(total_profit)),  # 成交利润额
                            str(int(inventory_value))   # 库存价值
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
                for item in self.stock_in_tree.get_children():
                    try:
                        values = self.stock_in_tree.item(item)['values']
                        item_name, transaction_time, quantity, cost, avg_cost, note, *_ = values
                        # 将数字字段转换为整数
                        formatted_values = [
                            item_name,  # 物品名称
                            transaction_time,  # 当前时间
                            str(int(quantity)),  # 入库数量
                            str(int(round(cost))),  # 入库花费
                            str(int(round(avg_cost))),  # 入库均价
                            note  # 备注
                        ]
                        f.write(",".join(formatted_values) + "\n")
                    except Exception as e:
                        messagebox.showerror("数据结构异常", f"stock_in_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
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
                for item in self.stock_out_tree.get_children():
                    try:
                        values = self.stock_out_tree.item(item)['values']
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
                        messagebox.showerror("数据结构异常", f"stock_out_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
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
                for item in self.monitor_tree.get_children():
                    try:
                        values = self.monitor_tree.item(item)['values']
                        item_name, transaction_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = values
                        # 将数字字段转换为整数
                        formatted_values = [
                            item_name,  # 物品名称
                            transaction_time,  # 当前时间
                            str(int(quantity)),  # 数量
                            str(int(values[3])),  # 一口价
                            str(int(values[4])),  # 目标买入价
                            str(int(values[5])),  # 计划卖出价
                            str(int(values[6])),  # 保本卖出价
                            str(int(values[7])),  # 利润
                            values[8],  # 利润率
                            values[9]   # 出库策略
                        ]
                        f.write(",".join(formatted_values) + "\n")
                    except Exception as e:
                        messagebox.showerror("数据结构异常", f"monitor_tree数据结构异常: {e}\nvalues={values if 'values' in locals() else ''}")
                        continue
            self.root.after(0, lambda: messagebox.showinfo("成功", "监控报表已导出到 monitor_report.csv"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"导出监控报表失败: {str(e)}"))

    def open_formula_manager(self):
        """打开公式管理窗口"""
        FormulaManagerWindow(self.root, self)

    def on_tab_changed(self, event):
        tab = self.notebook.tab(self.notebook.select(), 'text')
        if tab == '操作日志':
            self.refresh_log_tab()

    def create_silver_price_tab(self):
        # 创建银两价格标签页
        self.silver_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.silver_tab, text="银两价格")

        # 创建控制面板
        control_frame = ttk.Frame(self.silver_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 平台选择（只保留全部、7881、DD373）
        ttk.Label(control_frame, text="平台:").pack(side=tk.LEFT, padx=5)
        self.silver_platform = ttk.Combobox(control_frame, values=["全部", "7881", "DD373"], state="readonly", width=10)
        self.silver_platform.set("全部")
        self.silver_platform.pack(side=tk.LEFT, padx=5)
        # 绑定平台切换事件，切换时自动刷新
        self.silver_platform.bind("<<ComboboxSelected>>", lambda e: self.refresh_silver_price())

        # 天数选择
        ttk.Label(control_frame, text="天数:").pack(side=tk.LEFT, padx=5)
        self.silver_days = ttk.Combobox(control_frame, values=["7", "15", "30", "90", "180", "365"], state="readonly", width=5)
        self.silver_days.set("30")
        self.silver_days.pack(side=tk.LEFT, padx=5)

        # 刷新按钮
        ttk.Button(control_frame, text="刷新", command=self.refresh_silver_price).pack(side=tk.LEFT, padx=5)
        
        # 自动刷新开关
        self.auto_refresh_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="自动刷新", variable=self.auto_refresh_var, 
                        command=self.auto_refresh_silver_price).pack(side=tk.LEFT, padx=5)

        # 重置缩放按钮
        ttk.Button(control_frame, text="重置缩放", command=self.reset_silver_zoom).pack(side=tk.LEFT, padx=5)

        # 导出按钮
        ttk.Button(control_frame, text="导出图表", command=self.export_silver_chart).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出数据", command=self.export_silver_data).pack(side=tk.LEFT, padx=5)

        # 信息展示区（美化：卡片式高亮UI）
        info_frame = tk.Frame(self.silver_tab, bg='#f8f8f8')
        info_frame.pack(fill='x', pady=(0, 10))
        def make_info_label(parent, label_text, value_text, fg='#222', bg='#ffe066', highlight=False):
            frame = tk.Frame(parent, bg=bg, bd=0, relief='flat')
            frame.pack(side='left', padx=30, ipadx=8, ipady=2)
            label = tk.Label(frame, text=label_text, font=('微软雅黑', 12, 'bold'), bg=bg, fg=fg)
            label.pack(side='top', anchor='center')
            val_label = tk.Label(
                frame, text=value_text, font=('微软雅黑', 16, 'bold'),
                bg=bg, fg=('#ff4444' if highlight else fg)
            )
            val_label.pack(side='top', anchor='center')
            return val_label
        self.current_price_label = make_info_label(info_frame, "当前价格:", "--", fg='#222', bg='#ffe066')
        self.avg_price_label = make_info_label(info_frame, "7日均价:", "--", fg='#222', bg='#ffe066')
        self.amplitude_label = make_info_label(info_frame, "振幅:", "--", fg='#ff4444', bg='#ffe066', highlight=True)

        # 创建图表
        self.silver_fig = Figure(figsize=(10, 6), dpi=100)
        self.silver_ax1 = self.silver_fig.add_subplot(111)
        self.silver_canvas = FigureCanvasTkAgg(self.silver_fig, master=self.silver_tab)
        self.silver_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 初始化交互状态
        self._dragging = False
        self._drag_start = None
        self._orig_xlim = None
        self._orig_ylim = None
        self._last_refresh_time = 0
        self._refresh_interval = 60  # 最小刷新间隔（秒）
        self._max_points = 1000  # 最大显示点数
        self._mpl_cursor = None

        # 绑定事件
        self.silver_canvas.mpl_connect('scroll_event', self._on_silver_scroll)
        self.silver_canvas.mpl_connect('button_press_event', self._on_silver_press)
        self.silver_canvas.mpl_connect('button_release_event', self._on_silver_release)
        self.silver_canvas.mpl_connect('motion_notify_event', self._on_silver_motion)

        # 初始化图表
        self.refresh_silver_price()

    def _on_silver_scroll(self, event):
        if event.inaxes != self.silver_ax1:
            return

        # 获取当前视图范围
        cur_xlim = self.silver_ax1.get_xlim()
        cur_ylim = self.silver_ax1.get_ylim()

        # 计算缩放中心
        xdata = event.xdata
        ydata = event.ydata

        # 计算缩放因子
        base_scale = 1.1
        scale = base_scale if event.button == 'up' else 1/base_scale

        # 计算新的范围
        new_width = (cur_xlim[1] - cur_xlim[0]) / scale
        new_height = (cur_ylim[1] - cur_ylim[0]) / scale

        # 设置新的范围
        self.silver_ax1.set_xlim([xdata - new_width*(xdata-cur_xlim[0])/(cur_xlim[1]-cur_xlim[0]),
                                 xdata + new_width*(cur_xlim[1]-xdata)/(cur_xlim[1]-cur_xlim[0])])
        self.silver_ax1.set_ylim([ydata - new_height*(ydata-cur_ylim[0])/(cur_ylim[1]-cur_ylim[0]),
                                 ydata + new_height*(cur_ylim[1]-ydata)/(cur_ylim[1]-cur_ylim[0])])

        # 使用draw_idle而不是draw
        self.silver_canvas.draw_idle()

    def _on_silver_press(self, event):
        if event.inaxes != self.silver_ax1:
            return
        self._dragging = True
        self._drag_start = (event.xdata, event.ydata)
        self._orig_xlim = self.silver_ax1.get_xlim()
        self._orig_ylim = self.silver_ax1.get_ylim()
        
        # 禁用悬停
        if self._mpl_cursor:
            self._mpl_cursor.enabled = False

    def _on_silver_motion(self, event):
        if not self._dragging or event.inaxes != self.silver_ax1:
            return
            
        if event.xdata is None or event.ydata is None:
            return

        # 计算移动距离
        dx = event.xdata - self._drag_start[0]
        dy = event.ydata - self._drag_start[1]

        # 更新坐标轴范围
        self.silver_ax1.set_xlim(self._orig_xlim[0] - dx, self._orig_xlim[1] - dx)
        self.silver_ax1.set_ylim(self._orig_ylim[0] - dy, self._orig_ylim[1] - dy)

        # 使用draw_idle而不是draw
        self.silver_canvas.draw_idle()

    def _on_silver_release(self, event):
        self._dragging = False
        # 恢复悬停
        if self._mpl_cursor:
            self._mpl_cursor.enabled = True

    def refresh_silver_price(self):
        # 强制每次都刷新，不做任何间隔判断
        threading.Thread(target=self._fetch_and_draw_silver_price, daemon=True).start()

    def _fetch_and_draw_silver_price(self):
        try:
            days = int(self.silver_days.get())
            platform = self.silver_platform.get()  # 每次都取最新的
            data = self.fetch_silver_price_multi_series(days)
            self.root.after(0, lambda: self._draw_silver_price(data, platform, days))
        except Exception as e:
            print(f"Error fetching silver price data: {e}")

    def _draw_silver_price(self, data, platform, days):
        try:
            self.silver_ax1.clear()
            self.silver_ax1.set_title(f"银两价格走势 ({days}天)")
            self.silver_ax1.set_xlabel("时间")
            self.silver_ax1.set_ylabel("价格 (元/万两)")
            self.silver_ax1.grid(True, linestyle='--', alpha=0.7)

            allowed_platforms = ["7881", "DD373"]
            filtered_series = {}
            filtered_dates = {}

            # 先重置信息栏
            self.current_price_label.config(text="--", fg='#222')
            self.avg_price_label.config(text="--", fg='#222')
            self.amplitude_label.config(text="--", fg='#ff4444')

            for series, series_data in data['series'].items():
                if series not in allowed_platforms:
                    continue
                # 平台严格匹配，只有'全部'时才不过滤
                if platform != "全部" and str(series) != str(platform):
                    continue
                time_list = data['dates'].get(series, [])
                # 转换时间
                if time_list and isinstance(time_list[0], str):
                    try:
                        time_list = [datetime.strptime(t, "%Y-%m-%d") for t in time_list]
                    except Exception:
                        import pandas as pd
                        time_list = [pd.to_datetime(t) for t in time_list]
                # 降采样
                if len(series_data) > self._max_points:
                    step = max(1, len(series_data) // self._max_points)
                    series_data = series_data[::step]
                    time_list = time_list[::step]
                filtered_series[series] = series_data
                filtered_dates[series] = time_list

            colors = ['#1f77b4', '#ff7f0e']
            info_updated = False
            first_valid_series_data = None
            for idx, (series, series_data) in enumerate(filtered_series.items()):
                time_list = filtered_dates.get(series)
                if not time_list or len(series_data) != len(time_list):
                    continue
                # 修正：将时间字符串转为datetime对象
                if isinstance(time_list[0], str):
                    try:
                        time_list = [datetime.strptime(t, "%Y-%m-%d") for t in time_list]
                    except Exception:
                        import pandas as pd
                        time_list = [pd.to_datetime(t) for t in time_list]
                self.silver_ax1.plot(time_list, series_data,
                                     label=series,
                                     color=colors[idx % len(colors)],
                                     linewidth=1.5,
                                     alpha=0.8)
                # 记录第一个有数据的平台
                if first_valid_series_data is None and series_data:
                    first_valid_series_data = (series, series_data)
                # 优先显示当前选中平台
                if not info_updated and (str(platform) == str(series) or (platform == '全部' and idx == 0)):
                    if series_data:
                        current_price = series_data[-1]
                        self.current_price_label.config(text=f"{current_price:.4f}", fg='#222')
                        last_7_days = series_data[-7:] if len(series_data) >= 7 else series_data
                        avg_7_days = sum(last_7_days) / len(last_7_days)
                        self.avg_price_label.config(text=f"{avg_7_days:.4f}", fg='#222')
                        max_price = max(series_data)
                        min_price = min(series_data)
                        amplitude = ((max_price - min_price) / min_price) * 100 if min_price else 0
                        self.amplitude_label.config(
                            text=f"{amplitude:.2f}%",
                            fg='#ff4444' if amplitude > 5 else '#0056b3'
                        )
                        if amplitude > 5:
                            self.amplitude_label.config(foreground='#ff4444')
                        else:
                            self.amplitude_label.config(foreground='#0056b3')
                        info_updated = True
            # 如果没有任何平台被 info_updated，强制用第一个有数据的平台刷新信息栏
            if not info_updated and first_valid_series_data:
                _, series_data = first_valid_series_data
                current_price = series_data[-1]
                self.current_price_label.config(text=f"{current_price:.4f}", fg='#222')
                last_7_days = series_data[-7:] if len(series_data) >= 7 else series_data
                avg_7_days = sum(last_7_days) / len(last_7_days)
                self.avg_price_label.config(text=f"{avg_7_days:.4f}", fg='#222')
                max_price = max(series_data)
                min_price = min(series_data)
                amplitude = ((max_price - min_price) / min_price) * 100 if min_price else 0
                self.amplitude_label.config(
                    text=f"{amplitude:.2f}%",
                    fg='#ff4444' if amplitude > 5 else '#0056b3'
                )
                if amplitude > 5:
                    self.amplitude_label.config(foreground='#ff4444')
                else:
                    self.amplitude_label.config(foreground='#0056b3')
            self.silver_ax1.legend(loc='upper left')
            # 只显示最多10个x轴主刻度
            import matplotlib.ticker as ticker
            self.silver_ax1.xaxis.set_major_locator(ticker.MaxNLocator(10))
            self.silver_ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m-%d'))
            self.silver_fig.autofmt_xdate()
            self.silver_canvas.draw_idle()
            # 已取消悬停详情显示
        except Exception as e:
            print(f"Error drawing silver price chart: {e}")

    def reset_silver_zoom(self):
        self.silver_ax1.autoscale()
        self.silver_canvas.draw_idle()

    def auto_refresh_silver_price(self):
        if self.auto_refresh_var.get():
            self.refresh_silver_price()
            self.root.after(60000, self.auto_refresh_silver_price)  # 每分钟刷新一次

    def export_silver_chart(self):
        import tkinter.filedialog as fd
        file_path = fd.asksaveasfilename(defaultextension='.png', filetypes=[('PNG图片', '*.png')])
        if file_path:
            self.silver_fig.savefig(file_path, dpi=200)
            messagebox.showinfo("成功", f"图表已导出到 {file_path}")

    def export_silver_data(self):
        import tkinter.filedialog as fd
        file_path = fd.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV文件', '*.csv')])
        if not file_path:
            return
        data = getattr(self, '_last_silver_data', None)
        if not data:
            messagebox.showerror("错误", "暂无可导出的数据")
            return
        all_keys = list(data['series'].keys())
        # 取最长的时间轴
        max_len = max(len(data['dates'][k]) for k in all_keys if isinstance(data['dates'][k], list))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('时间,' + ','.join(all_keys) + '\n')
            for i in range(max_len):
                row = []
                t = data['dates'][all_keys[0]][i] if i < len(data['dates'][all_keys[0]]) else ''
                row.append(t)
                for k in all_keys:
                    v = data['series'][k][i] if i < len(data['series'][k]) else ''
                    row.append(str(v))
                f.write(','.join(row) + '\n')
        messagebox.showinfo("成功", f"数据已导出到 {file_path}")

    def gen_silver_stats(self, data):
        """生成统计区文本"""
        lines = []
        for series, price_list in data['series'].items():
            arr = np.array(price_list)
            lines.append(f"{series}：均价{arr.mean():.4f}，最高{arr.max():.4f}，最低{arr.min():.4f}，波动率{(arr.std()/arr.mean()*100 if arr.mean() else 0):.2f}%")
        return '\n'.join(lines)

    def _save_operation_logs(self):
        pass  # 废弃本地文件写入

    def _load_operation_logs(self):
        # 直接从数据库加载
        return self.db_manager.get_operation_logs(page=1, page_size=200)

    def _on_tab_changed_ocr(self, event=None):
        tab = self.notebook.tab(self.notebook.select(), 'text')
        # 先解绑所有
        self.root.unbind_all('<Control-v>')
        if tab == '入库管理':
            self.root.bind_all('<Control-v>', self.paste_ocr_import_stock_in)
            self.current_ocr_tab = 'in'
        elif tab == '出库管理':
            self.root.bind_all('<Control-v>', self.paste_ocr_import_stock_out)
            self.current_ocr_tab = 'out'
        elif tab == '交易监控':
            self.root.bind_all('<Control-v>', self.paste_ocr_import_monitor)
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
            with open('item_dict.txt', 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(item+'\n')
            messagebox.showinfo("保存成功", "物品词典已保存！")
        ttk.Button(btn_frame, text="添加", command=add_item).pack(side='left', padx=10, ipadx=8)
        ttk.Button(btn_frame, text="删除", command=del_item).pack(side='left', padx=10, ipadx=8)
        ttk.Button(btn_frame, text="保存", command=save_dict).pack(side='right', padx=10, ipadx=8)

    def load_item_dict(self):
        """加载物品词典列表"""
        try:
            with open('item_dict.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def edit_monitor_item(self, event):
        item_id = self.monitor_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.monitor_tree.item(item_id)['values']
        edit_win = tb.Toplevel(self.root)
        edit_win.title("编辑监控记录")
        edit_win.minsize(480, 400)
        edit_win.configure(bg='#f4f8fb')
        style = ttk.Style()
        style.configure('Edit.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=('微软雅黑', 11))
        style.configure('Edit.TButton', font=('微软雅黑', 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        content_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        labels = ["物品", "数量", "一口价", "目标买入价", "计划卖出价", "出库策略"]
        types = [str, int, float, float, float, str]
        entries = []
        error_labels = []
        edit_indices = [0, 2, 3, 4, 5, 9]  # 对应表格字段索引
        for i, (label, idx, typ) in enumerate(zip(labels, edit_indices, types)):
            ttk.Label(content_frame, text=label+":", style='Edit.TLabel').grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
            entry = ttk.Entry(content_frame, validate='key', validatecommand=vcmd, style='Edit.TEntry') if vcmd else ttk.Entry(content_frame, style='Edit.TEntry')
            entry.insert(0, values[idx])
            entry.grid(row=i*2, column=1, padx=12, pady=4, sticky='w')
            entries.append(entry)
            err = ttk.Label(content_frame, text="", foreground="red", background='#f4f8fb', font=('微软雅黑', 10))
            err.grid(row=i*2+1, column=0, columnspan=2, sticky='w', padx=12)
            error_labels.append(err)
        def save():
            new_vals = [e.get() for e in entries]
            valid = True
            for idx, (val, typ, err_lbl) in enumerate(zip(new_vals, types, error_labels)):
                err_lbl.config(text="")
                if typ is int:
                    if not val.isdigit():
                        err_lbl.config(text="请输入正整数")
                        entries[idx].focus_set()
                        valid = False
                        break
                elif typ is float:
                    try:
                        float(val)
                    except Exception:
                        err_lbl.config(text="请输入数字")
                        entries[idx].focus_set()
                        valid = False
                        break
            if not valid:
                return
            # 更新数据库：先删除原有记录再插入新记录
            try:
                self.db_manager.delete_trade_monitor(values[0], values[1])
                self.db_manager.save_trade_monitor({
                    'item_name': new_vals[0],
                    'monitor_time': values[1],  # 时间不变
                    'quantity': int(new_vals[1]),
                    'market_price': float(new_vals[2]),
                    'target_price': float(new_vals[3]),
                    'planned_price': float(new_vals[4]),
                    'break_even_price': float(values[6]),  # 保本卖出价公式自动算
                    'profit': float(values[7]),            # 利润公式自动算
                    'profit_rate': float(str(values[8]).replace('%','')), # 利润率公式自动算
                    'strategy': new_vals[5]
                })
                self.refresh_monitor()
                edit_win.destroy()
            except Exception as e:
                error_labels[0].config(text=f"保存失败: {e}")
        button_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        ttk.Button(button_frame, text="保存", command=save, style='Edit.TButton').pack(pady=6, ipadx=40)

    def show_about(self):
        """显示关于对话框"""
        about_text = """
游戏交易系统 v1.0

功能：
- 库存管理
- 入库管理
- 出库管理
- 交易监控
- 数据分析
- 数据迁移

作者：小明
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

    def batch_ocr_import_monitor(self):
        if not hasattr(self, '_pending_ocr_images_monitor') or not self._pending_ocr_images_monitor:
            messagebox.showwarning("无图片", "请先粘贴图片")
            return
        all_preview_data = []
        for img in self._pending_ocr_images_monitor:
            try:
                import io, base64, requests
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                url = "http://sql.didiba.uk:1224/api/ocr"
                payload = {
                    "base64": img_b64,
                    "options": {
                        "data.format": "text"
                    }
                }
                headers = {"Content-Type": "application/json"}
                resp = requests.post(url, json=payload, headers=headers, timeout=20)
                resp.raise_for_status()
                ocr_result = resp.json()
                text = ocr_result.get('data')
                if not text:
                    continue
                # 使用交易监控专用解析函数
                parsed_data = self.parse_monitor_ocr_text(text)
                if parsed_data:
                    all_preview_data.extend(parsed_data)
            except Exception as e:
                print(f"OCR识别失败: {e}")
        if all_preview_data:
            self.show_ocr_preview(
                all_preview_data,
                columns=('物品', '数量', '一口价', '备注'),
                field_map=['item_name', 'quantity', 'market_price', 'note']
            )
        else:
            messagebox.showwarning("无有效数据", "未识别到有效的监控数据行！")
        self._pending_ocr_images_monitor.clear()
        self.refresh_ocr_image_preview_monitor()

    def paste_ocr_import_monitor(self, event=None):
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if isinstance(img, list):
            img = img[0] if img else None
        if img is None or not hasattr(img, 'save'):
            messagebox.showwarning("粘贴失败", "剪贴板中没有图片")
            return
        if not hasattr(self, '_pending_ocr_images_monitor'):
            self._pending_ocr_images_monitor = []
        self._pending_ocr_images_monitor.append(img)
        self.refresh_ocr_image_preview_monitor()
        messagebox.showinfo("已添加", f"已添加{len(self._pending_ocr_images_monitor)}张图片，点击批量识别可统一导入。")

    def refresh_ocr_image_preview_monitor(self):
        # 清空预览区
        for widget in self.ocr_image_preview_frame_monitor.winfo_children():
            widget.destroy()
        # 显示所有待识别图片的缩略图
        if not hasattr(self, '_pending_ocr_images_monitor'):
            self._pending_ocr_images_monitor = []
        for idx, img in enumerate(self._pending_ocr_images_monitor):
            thumb = img.copy()
            thumb.thumbnail((80, 80))
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(thumb)
            lbl = ttk.Label(self.ocr_image_preview_frame_monitor, image=photo)
            lbl.image = photo
            lbl.grid(row=0, column=idx*2, padx=4, pady=2)
            btn = ttk.Button(self.ocr_image_preview_frame_monitor, text='删除', width=5, command=lambda i=idx: self.delete_ocr_image_monitor(i))
            btn.grid(row=1, column=idx*2, padx=4, pady=2)

    def delete_ocr_image_monitor(self, idx):
        del self._pending_ocr_images_monitor[idx]
        self.refresh_ocr_image_preview_monitor()

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

    def show_preview(self):
        """显示预览窗口"""
        preview_window = tb.Toplevel(self.root)
        preview_window.title("预览")
        preview_window.geometry("800x600")
        
        # 创建预览内容
        preview_frame = ttk.Frame(preview_window, padding="10")
        preview_frame.pack(fill=BOTH, expand=True)
        
        # 添加预览内容
        ttk.Label(preview_frame, text="预览内容").pack()
        
        # 关闭按钮
        ttk.Button(preview_frame, text="关闭", command=preview_window.destroy).pack(pady=10)

    def open_data_migration(self):
        """打开数据迁移窗口"""
        migration_window = tb.Toplevel(self.root)
        migration_window.title("数据迁移")
        migration_window.geometry("600x400")
        
        # 创建主框架
        main_frame = ttk.Frame(migration_window, padding="10")
        main_frame.pack(fill=BOTH, expand=True)
        
        # 添加说明标签
if __name__ == "__main__":
    root = tb.Window(themename="flatly")  # 现代天蓝色主题
    app = GameTradingSystemGUI(root)
    root.mainloop() 