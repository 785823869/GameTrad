import tkinter as tk
from ttkbootstrap import Frame, Label, LabelFrame, Entry, Button, Style
from ttkbootstrap.constants import *
from tkinter import ttk, font
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.font_manager as fm
import random
from datetime import datetime, timedelta
import platform
import os
import requests
import json
import threading
import time
import warnings
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
warnings.simplefilter('ignore', InsecureRequestWarning)

class DashboardTab(Frame):
    def __init__(self, parent_frame, main_gui=None, **kwargs):
        super().__init__(parent_frame, **kwargs)
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        
        # 设置背景色
        self.configure(style="TFrame")
        self.bg_color = "#f5f5f5"  # 定义统一的背景色
        
        # 创建变量
        self.total_items_var = tk.StringVar(value="0")
        self.total_quantity_var = tk.StringVar(value="0")
        self.total_value_var = tk.StringVar(value="¥0.00")
        self.low_stock_var = tk.StringVar(value="0项")
        self.total_profit_var = tk.StringVar(value="¥0.00")
        
        # 自动滚动相关变量
        self.auto_scroll_enabled = False
        self.auto_scroll_timer_id = None
        self.auto_scroll_speed = 2000  # 滚动速度(毫秒)
        
        # 库存详情表格自动滚动相关变量
        self.inventory_auto_scroll_enabled = True  # 默认启用
        self.inventory_auto_scroll_timer_id = None
        self.inventory_auto_scroll_speed = 3000  # 滚动速度(毫秒)
        
        # 设置中文字体
        self.chinese_font = main_gui.chinese_font
        
        # 价格数据缓存
        self.silver_price_cache = None
        self.nvwa_price_cache = None
        self.last_price_update = 0
        self.price_cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'price_cache.json')
        
        # 加载缓存的价格数据
        self.load_price_cache()
        print(f"初始化时价格缓存状态: 银两={self.silver_price_cache}, 女娲石={self.nvwa_price_cache}, 最后更新时间={(datetime.fromtimestamp(self.last_price_update) if self.last_price_update else '无')}")
        
        # 创建自定义样式
        self.setup_styles()
        # 填充整个父容器
        self.pack(fill='both', expand=True)
        # 创建界面
        self.create_widgets()
        
        # 延迟加载数据，确保界面完全渲染后再获取价格数据
        print("设置2秒后刷新仪表盘...")
        self.after(2000, self.refresh_dashboard)
        
        # 如果5秒后价格还未刷新，再尝试一次
        print("设置5秒后再次尝试刷新价格...")
        self.after(5000, self.refresh_price_data)
        
        # 绑定销毁事件，确保清理资源
        self.bind("<Destroy>", self.on_destroy)
    
    def on_destroy(self, event):
        """处理销毁事件，清理资源"""
        # 如果事件的窗口是当前窗口(非子组件)，则执行清理
        if event.widget == self:
            self.cleanup_resources()
    
    def cleanup_resources(self):
        """清理资源"""
        # 停止用户库存监控表格自动滚动
        self.stop_auto_scroll()
        
        # 停止库存详情表格自动滚动
        self.stop_inventory_auto_scroll()
    
    def setup_styles(self):
        """设置自定义样式"""
        style = Style()
        # 卡片标题样式
        style.configure("Card.TLabelframe", borderwidth=0, relief="flat")
        style.configure("Card.TLabelframe.Label", font=(self.chinese_font, 12, "bold"), foreground="#2c3e50")
        
        # 卡片值样式 - 加深文字颜色
        style.configure("CardValue.TLabel", font=(self.chinese_font, 24, "bold"), foreground="#2c3e50")
        # 卡片描述样式 - 提高对比度
        style.configure("CardDesc.TLabel", font=(self.chinese_font, 10), foreground="#34495e")
        
        # 正值和负值的不同颜色 - 增强对比度
        style.configure("Positive.TLabel", foreground="#27ae60")  # 深绿色
        style.configure("Negative.TLabel", foreground="#c0392b")  # 深红色
        
        # 表格样式 - 提高可读性
        style.configure("Dashboard.Treeview", 
                       rowheight=28, 
                       font=(self.chinese_font, 10),
                       background="#ffffff",
                       fieldbackground="#ffffff",
                       foreground="#2c3e50")
                       
        style.configure("Dashboard.Treeview.Heading", 
                       font=(self.chinese_font, 10, "bold"),
                       background="#e0e6ed",
                       foreground="#2c3e50")
        
        # 用户库存监控表格的颜色标签样式
        style.map("Dashboard.Treeview",
                 background=[("selected", "#3498db")],
                 foreground=[("selected", "#ffffff")])
        
        # 注意：Treeview标签样式(如高库存、低库存和交替行颜色)
        # 需要在Treeview实例上使用tag_configure进行配置，而不是在Style对象上
        
        # 配置所有标签使用中文字体
        style.configure("TLabel", font=(self.chinese_font, 10))
        style.configure("TButton", font=(self.chinese_font, 10))
        style.configure("TEntry", font=(self.chinese_font, 10))
        style.configure("TCheckbutton", font=(self.chinese_font, 10))
        style.configure("TRadiobutton", font=(self.chinese_font, 10))
        style.configure("TCombobox", font=(self.chinese_font, 10))
        
        # 设置标签框
        style.configure("TLabelframe", font=(self.chinese_font, 10))
        style.configure("TLabelframe.Label", font=(self.chinese_font, 10, "bold"))
        
        # 主题级别的默认字体设置
        style.configure(".", font=(self.chinese_font, 10))

    def get_monthly_profit(self, year, month):
        db_manager = getattr(self.main_gui, 'db_manager', None)
        if db_manager is None:
            return 0.0
        # 获取本月第一天和下月第一天
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year+1, 1, 1)
        else:
            end = datetime(year, month+1, 1)
        # 查询本月所有出库记录
        stock_out = db_manager.fetch_all(
            "SELECT quantity, unit_price, fee FROM stock_out WHERE transaction_time >= %s AND transaction_time < %s",
            (start, end)
        )
        profit = 0.0
        for row in stock_out:
            try:
                q, p, f = float(row[0]), float(row[1]), float(row[2])
                profit += q * p - f
            except Exception:
                continue
        return profit

    def get_total_profit_and_mom(self):
        now = datetime.now()
        this_month_profit = self.get_monthly_profit(now.year, now.month)
        # 上月
        if now.month == 1:
            last_month = 12
            last_year = now.year - 1
        else:
            last_month = now.month - 1
            last_year = now.year
        last_month_profit = self.get_monthly_profit(last_year, last_month)
        if abs(last_month_profit) < 1e-6:
            mom = 0.0
        else:
            mom = (this_month_profit - last_month_profit) / abs(last_month_profit) * 100
        return this_month_profit, mom

    def get_total_inventory_value(self):
        """计算库存管理中所有物品的库存价值总和"""
        db_manager = getattr(self.main_gui, 'db_manager', None)
        if db_manager is None:
            return 0.0
            
        # 获取入库和出库数据
        stock_in_data = db_manager.get_stock_in()
        stock_out_data = db_manager.get_stock_out()
        
        # 计算每种物品的库存和价值
        inventory_dict = {}
        
        # 统计入库
        for row in stock_in_data:
            try:
                _, item_name, _, qty, cost, *_ = row
                qty = float(qty)
                cost = float(cost)
                if item_name not in inventory_dict:
                    inventory_dict[item_name] = {
                        'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                    }
                inventory_dict[item_name]['in_qty'] += qty
                inventory_dict[item_name]['in_amount'] += cost
            except Exception:
                continue
                
        # 统计出库
        for row in stock_out_data:
            try:
                _, item_name, _, qty, unit_price, fee, deposit, total_amount, note, *_ = row
                qty = float(qty)
                unit_price = float(unit_price)
                fee = float(fee)
                amount = unit_price * qty - fee
                if item_name not in inventory_dict:
                    inventory_dict[item_name] = {
                        'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                    }
                inventory_dict[item_name]['out_qty'] += qty
                inventory_dict[item_name]['out_amount'] += amount
            except Exception:
                continue
                
        # 计算总库存价值
        total_value = 0.0
        for item, data in inventory_dict.items():
            remain_qty = data['in_qty'] - data['out_qty']
            if remain_qty <= 0:
                continue
            in_avg = data['in_amount'] / data['in_qty'] if data['in_qty'] else 0
            value = remain_qty * in_avg
            total_value += value
            
        return total_value
        
    def get_inventory_value_mom(self):
        """计算库存价值的月环比变化"""
        # 这里简化处理，返回一个固定的月环比数据
        # 实际应用中可以保存历史数据并计算真实的月环比
        return 33.0
        
    def get_active_users_count(self):
        """获取活跃用户数量"""
        # 示例数据，实际应用中应从数据库获取
        return 10353
        
    def get_active_users_mom(self):
        """获取活跃用户月环比变化"""
        # 示例数据，实际应用中应从数据库获取
        return -8.0

    def get_out_amounts_by_period(self, year, month, period='day'):
        """返回本月每日/每周/每月出库总金额列表[(label, amount), ...]"""
        db_manager = getattr(self.main_gui, 'db_manager', None)
        if db_manager is None:
            return []
        import calendar
        from collections import defaultdict
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year+1, 1, 1)
        else:
            end = datetime(year, month+1, 1)
        stock_out = db_manager.fetch_all(
            "SELECT transaction_time, quantity, unit_price, fee FROM stock_out WHERE transaction_time >= %s AND transaction_time < %s",
            (start, end)
        )
        result = []
        if period == 'day':
            daily_amount = defaultdict(float)
            for row in stock_out:
                try:
                    dt, q, p, f = row
                    day = dt.day if hasattr(dt, 'day') else int(str(dt)[8:10])
                    amount = float(q) * float(p) - float(f)
                    daily_amount[day] += amount
                except Exception:
                    continue
            days_in_month = calendar.monthrange(year, month)[1]
            result = [(f"{d}", daily_amount.get(d, 0.0)) for d in range(1, days_in_month+1)]
        elif period == 'week':
            week_amount = defaultdict(float)
            for row in stock_out:
                try:
                    dt, q, p, f = row
                    week = dt.isocalendar()[1] if hasattr(dt, 'isocalendar') else int(str(dt)[5:7])
                    amount = float(q) * float(p) - float(f)
                    week_amount[week] += amount
                except Exception:
                    continue
            weeks = sorted(week_amount.keys())
            result = [(f"W{w}", week_amount[w]) for w in weeks]
        elif period == 'month':
            # 只统计本月
            month_amount = 0.0
            for row in stock_out:
                try:
                    q, p, f = float(row[1]), float(row[2]), float(row[3])
                    month_amount += q * p - f
                except Exception:
                    continue
            result = [(f"{year}-{month:02d}", month_amount)]
        return result

    def draw_trend_chart(self, frame, period='day'):
        # 清空frame内容
        for widget in frame.winfo_children():
            widget.destroy()
            
        # 设置matplotlib中文字体
        plt.rcParams['font.family'] = [self.chinese_font, 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
            
        now = datetime.now()
        data = self.get_out_amounts_by_period(now.year, now.month, period)
        x = [label for label, _ in data]
        y = [a for _, a in data]
        
        # 设置图表样式
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(5,3), dpi=100)
        fig.patch.set_facecolor('#f9f9f9')
        ax.set_facecolor('#f9f9f9')
        
        # 绘制线条和点
        line_color = '#3498db'
        marker_color = '#2980b9'
        highlight_color = '#e74c3c'
        
        ax.plot(x, y, color=line_color, linewidth=2, marker='o', markersize=5, 
                markerfacecolor=marker_color, markeredgecolor='white', markeredgewidth=1, zorder=3)
        
        # 高亮最后一个点
        if x and y:
            ax.scatter([x[-1]], [y[-1]], s=100, color=highlight_color, zorder=5, alpha=0.7,
                      edgecolors='white', linewidth=2)
        
        # 设置标题和标签
        ax.set_title("出库金额趋势", loc='left', fontsize=14, fontweight='bold', color='#2c3e50', fontfamily=self.chinese_font)
        ax.set_xlabel("")
        ax.set_ylabel("金额", fontsize=11, color='#7f8c8d', fontfamily=self.chinese_font)
        
        # 设置网格和边框
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#bdc3c7', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#bdc3c7')
        ax.spines['bottom'].set_color('#bdc3c7')
        
        # y轴金额格式化
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
        
        # x轴美化
        if period == 'day':
            ax.set_xticks(x[::max(1, len(x)//7)])
        ax.tick_params(axis='x', labelsize=9, colors='#7f8c8d')
        ax.tick_params(axis='y', labelsize=9, colors='#7f8c8d')
        
        # 单独设置刻度标签字体
        for label in ax.get_xticklabels():
            label.set_fontfamily(self.chinese_font)
        for label in ax.get_yticklabels():
            label.set_fontfamily(self.chinese_font)
        
        fig.tight_layout(pad=2)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

    def create_widgets(self):
        # 顶部搜索和标签栏
        top_frame = Frame(self)  # 移除背景色
        top_frame.pack(fill='x', pady=(0, 10))
        
        # 标签按钮区域
        tabs_frame = Frame(top_frame)  # 移除背景色
        tabs_frame.pack(side='left', padx=5)
        
        # 使用更现代的按钮样式
        Button(tabs_frame, text="概览", bootstyle="primary").pack(side='left', padx=2)
        Button(tabs_frame, text="详情", bootstyle="secondary").pack(side='left', padx=2)
        Button(tabs_frame, text="分析", bootstyle="secondary").pack(side='left', padx=2)
        
        # 替换搜索框为美化的刷新按钮
        refresh_frame = Frame(top_frame)  # 移除背景色
        refresh_frame.pack(side='right', padx=5)
        
        # 创建刷新按钮，使用success颜色使其更突出，添加刷新图标字符
        refresh_button = Button(
            refresh_frame, 
            text="刷新数据 ⟳", 
            bootstyle="success",
            command=self.refresh_dashboard,
            width=12
        )
        refresh_button.pack(side='right')

        # 统计卡片区域 - 移除背景色
        stats_frame = Frame(self)  # 移除背景色
        stats_frame.pack(fill='x', pady=10, padx=10)
        
        # 获取数据
        total_profit, month_on_month = self.get_total_profit_and_mom()
        total_inventory_value = self.get_total_inventory_value()
        inventory_mom = self.get_inventory_value_mom()
        active_users = self.get_active_users_count()
        active_users_mom = self.get_active_users_mom()
        
        # 卡片数据
        card_data = [
            {
                "title": "总收入",
                "value": f"${total_profit:,.2f}",
                "desc": f"{month_on_month:+.2f}% 月环比",
                "is_positive": month_on_month >= 0,
                "icon": "📈" if month_on_month >= 0 else "📉",
                "bg_color": "#f0f7fb",
                "card_style": "blue"
            },
            {
                "title": "总库存价值",
                "value": f"${total_inventory_value:,.2f}",
                "desc": f"{inventory_mom:+.2f}% 月环比",
                "is_positive": inventory_mom >= 0,
                "icon": "📦",
                "bg_color": "#f0fbf7",
                "card_style": "green"
            },
            {
                "title": "行情概览",
                "desc": "",
                "is_positive": True,
                "icon": "💰",
                "bg_color": "#fbf7f0",
                "card_style": "yellow"
            }
        ]
        
        # 创建卡片
        for idx, card_info in enumerate(card_data):
            # 创建卡片外层容器
            card_outer = Frame(stats_frame)
            card_outer.pack(side='left', expand=True, fill='both', padx=5)
            
            # 创建Canvas用于绘制圆角矩形背景
            canvas_height = 130  # 设置卡片高度
            canvas = tk.Canvas(card_outer, height=canvas_height, 
                              highlightthickness=0, bg=self.bg_color)  # 使用统一的背景色
            canvas.pack(fill='both', expand=True)
            
            # 绘制阴影
            shadow_id = self.create_card_shadow(
                canvas, 5, 5, card_outer.winfo_reqwidth()-5, canvas_height-5,
                radius=15, shadow_size=3
            )
            
            # 绘制半圆角矩形作为卡片背景（只有左上和右上为圆角）
            bg_color = card_info["bg_color"]
            rect_id = self.draw_semi_rounded_rectangle(
                canvas, 2, 2, card_outer.winfo_reqwidth()-2, canvas_height-2,
                radius=15, fill=bg_color, outline="", width=0
            )
            
            # 创建Frame作为卡片内容容器
            card = tk.Frame(canvas, bg=bg_color)
            card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.85)
            
            # 卡片内部使用网格布局
            card.columnconfigure(0, weight=1)
            card.columnconfigure(1, weight=0)
            
            # 标题行
            title_label = tk.Label(card, text=card_info["title"], 
                               font=(self.chinese_font, 11, "bold"),
                               fg="#555555", bg=bg_color)
            title_label.grid(row=0, column=0, sticky='w', pady=(5, 5))
            
            # 根据卡片类型设置内容
            if idx < 2:  # 前两个卡片（总收入，总库存价值）
                # 数值显示 - 使用透明背景
                value_label = tk.Label(card, text=card_info["value"], 
                                   font=(self.chinese_font, 22, "bold"),
                                   fg="#2c3e50", bg=bg_color)
                value_label.grid(row=1, column=0, sticky='w')
                
                # 环比显示 - 使用简约风格
                is_positive = card_info["is_positive"]
                
                # 获取环比值（去掉百分号和"月环比"文本）
                mom_text_parts = card_info["desc"].split('%')
                mom_value_text = mom_text_parts[0].replace('+','').replace('-','')
                try:
                    mom_value = float(mom_value_text)
                    is_zero = abs(mom_value) < 0.01  # 接近于0视为0
                except:
                    is_zero = False
                    
                # 分离数字部分和文本部分
                mom_percent = mom_text_parts[0] + '%'
                mom_label_text = '月环比'
                
                # 根据正负值或零值设置不同的颜色和箭头
                if is_zero:
                    arrow_color = text_color = "#607D8B"  # 中性灰色
                    arrow_icon = "–"  # 使用短横线表示持平
                elif is_positive:
                    arrow_color = text_color = "#27ae60"  # 绿色
                    arrow_icon = "▲"  # 小三角箭头
                else:
                    arrow_color = text_color = "#c0392b"  # 红色
                    arrow_icon = "▼"  # 小三角箭头
                
                # 创建一个Frame作为环比显示的容器
                mom_frame = tk.Frame(card, bg=bg_color)
                mom_frame.grid(row=2, column=0, sticky='w', pady=(3, 0))
                
                # 分开显示箭头、环比值和文本，使布局更美观
                arrow_label = tk.Label(
                    mom_frame, 
                    text=arrow_icon, 
                    font=("Segoe UI Symbol", 10, "bold"),  # 使用更清晰的图标字体
                    fg=arrow_color, 
                    bg=bg_color
                )
                arrow_label.pack(side="left", padx=(0, 3), pady=0)
                
                # 数值部分 - 使用粗体
                percent_label = tk.Label(
                    mom_frame, 
                    text=mom_percent, 
                    font=(self.chinese_font, 11, "bold"),  # 稍微增大
                    fg=text_color, 
                    bg=bg_color
                )
                percent_label.pack(side="left", padx=0, pady=0)
                
                # "月环比"文字部分 - 使用普通字体
                label_label = tk.Label(
                    mom_frame, 
                    text=mom_label_text, 
                    font=(self.chinese_font, 10),  # 普通字体
                    fg="#555555",  # 使用灰色
                    bg=bg_color
                )
                label_label.pack(side="left", padx=(2, 0), pady=0)
            else:  # 第三个卡片（行情概览）
                # 银两行情行 - 使用透明背景
                silver_frame = tk.Frame(card, bg=bg_color)
                silver_frame.grid(row=1, column=0, sticky='w', pady=(0, 5))
                
                tk.Label(silver_frame, text="银两行情:", 
                     font=(self.chinese_font, 11),
                     fg="#555555", bg=bg_color).pack(side='left')
                
                self.silver_price_label = tk.Label(silver_frame, text="加载中...", 
                                             font=(self.chinese_font, 11, "bold"),
                                             fg="#2c3e50", bg=bg_color)
                self.silver_price_label.pack(side='left', padx=(5, 0))
                
                # 女娲石行情行 - 使用透明背景
                nvwa_frame = tk.Frame(card, bg=bg_color)
                nvwa_frame.grid(row=2, column=0, sticky='w')
                
                tk.Label(nvwa_frame, text="女娲石行情:", 
                     font=(self.chinese_font, 11),
                     fg="#555555", bg=bg_color).pack(side='left')
                
                self.nvwa_price_label = tk.Label(nvwa_frame, text="加载中...", 
                                           font=(self.chinese_font, 11, "bold"),
                                           fg="#2c3e50", bg=bg_color)
                self.nvwa_price_label.pack(side='left', padx=(5, 0))
            
            # 右侧图标容器 - 使用透明背景
            icon_frame = tk.Frame(card, bg=bg_color)
            icon_frame.grid(row=0, column=1, rowspan=3, padx=(0, 5))
            
            # 右侧图标 - 使用大一点的字体
            icon_label = tk.Label(icon_frame, text=card_info["icon"], 
                              font=("Segoe UI Emoji", 30),
                              bg=bg_color)
            icon_label.pack(padx=10, pady=10)
            
            # 更新Canvas大小适应窗口
            def update_canvas_size(event, canvas=canvas, rect_id=rect_id, shadow_id=shadow_id):
                # 更新半圆角矩形
                canvas.coords(rect_id, *self.get_semi_rounded_rectangle_points(2, 2, event.width-2, event.height-2, radius=15))
                # 更新阴影
                shadow_points = [
                    5 + 15 + 3, 5 + 3,
                    event.width - 5 - 15, 5 + 3,
                    event.width - 5, 5 + 3,
                    event.width - 5 + 3, 5 + 15,
                    event.width - 5 + 3, event.height - 5,
                    event.width - 5, event.height - 5 + 3,
                    5, event.height - 5 + 3,
                    5 - 3, event.height - 5,
                    5 - 3, 5 + 15,
                    5, 5 + 3
                ]
                canvas.coords(shadow_id, *shadow_points)
            
            canvas.bind("<Configure>", update_canvas_size)

        # 主体区域 - 移除背景色
        main_frame = Frame(self)  # 移除bootstyle="light"
        main_frame.pack(fill='both', expand=True, padx=10)

        # 折线图区域（带周期切换）
        chart_container = LabelFrame(main_frame, text="销售趋势", bootstyle="primary")
        chart_container.pack(side='left', padx=(0, 10), pady=10, fill='both', expand=True)
        
        chart_top_frame = Frame(chart_container, bootstyle="light")
        chart_top_frame.pack(fill='x', padx=5, pady=5)
        
        # 周期切换按钮组
        period_var = tk.StringVar(value='day')
        period_map = {'day': '日', 'week': '周', 'month': '月'}
        
        period_frame = Frame(chart_top_frame, bootstyle="light")
        period_frame.pack(side='right')
        
        Label(period_frame, text="周期:", font=(self.chinese_font, 9)).pack(side='left')
        
        for period, label in period_map.items():
            def make_command(p=period):
                return lambda: self.change_period(period_var, p, chart_frame)
                
            btn = Button(period_frame, text=label, bootstyle="outline-secondary",
                        width=3, command=make_command())
            btn.pack(side='left', padx=2)
        
        # 图表区域
        chart_frame = Frame(chart_container, bootstyle="light")
        chart_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 初始绘制图表
        self.draw_trend_chart(chart_frame, 'day')

        # 用户库存监控 (之前是最近活跃用户)
        user_frame = LabelFrame(main_frame, text="用户库存监控", bootstyle="primary")
        user_frame.pack(side='left', pady=10, fill='y')
        
        # 创建内部内容框架
        user_content_frame = Frame(user_frame, bootstyle="light")
        user_content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 控制按钮区域
        control_frame = Frame(user_content_frame, bootstyle="light")
        control_frame.pack(fill='x', pady=(0, 5))
        
        # 添加自动滚动按钮
        self.auto_scroll_button = Button(
            control_frame, 
            text="开始自动滚动", 
            bootstyle="success-outline", 
            command=self.toggle_auto_scroll,
            width=12
        )
        self.auto_scroll_button.pack(side='right', padx=2)
        
        # 使用树形视图
        user_tree = ttk.Treeview(user_content_frame, columns=("name", "item", "inventory"), 
                                 show="headings", height=10, style="Dashboard.Treeview")
        user_tree.heading("name", text="用户名", anchor="center")
        user_tree.heading("item", text="物品", anchor="center")
        user_tree.heading("inventory", text="库存数", anchor="center")
        
        user_tree.column("name", width=120, anchor='center')
        user_tree.column("item", width=160, anchor='center')
        user_tree.column("inventory", width=100, anchor='center')
        
        # 配置标签样式，确保与setup_styles中定义的一致
        style = ttk.Style()
        style.configure("Dashboard.Treeview", rowheight=28, font=(self.chinese_font, 10))
        
        # 为Treeview组件配置标签样式
        user_tree.tag_configure("inventory_high", foreground="#27ae60")  # 高库存(绿色)
        user_tree.tag_configure("inventory_low", foreground="#c0392b")   # 低库存(红色)
        user_tree.tag_configure("evenrow", background="#f5f9fc")         # 偶数行背景色
        user_tree.tag_configure("oddrow", background="#ffffff")          # 奇数行背景色
        
        user_tree.pack(fill='both', expand=True)
        
        # 添加滚动条
        user_scrollbar = ttk.Scrollbar(user_content_frame, orient="vertical", command=user_tree.yview)
        user_tree.configure(yscrollcommand=user_scrollbar.set)
        user_scrollbar.pack(side='right', fill='y')
        
        # 保存引用以便更新数据
        self.user_inventory_tree = user_tree

        # 下方区域
        bottom_frame = Frame(self, bootstyle="light")
        bottom_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # 数据表
        table_frame = LabelFrame(bottom_frame, text="库存详情", bootstyle="primary", padding=10)
        table_frame.pack(side='left', padx=(0, 10), pady=10, fill='both', expand=True)
        
        # 创建内部框架，便于控制内边距
        inner_frame = Frame(table_frame, bootstyle="light")
        inner_frame.pack(fill='both', expand=True)
        
        # 使用树形视图
        source_tree = ttk.Treeview(inner_frame, columns=("item", "inventory", "profit_rate"), 
                                  show="headings", height=6, style="Dashboard.Treeview")
        source_tree.heading("item", text="物品", anchor="center")
        source_tree.heading("inventory", text="库存数", anchor="center")
        source_tree.heading("profit_rate", text="利润率", anchor="center")
        
        # 设置列的宽度和对齐方式，全部居中
        source_tree.column("item", width=150, anchor='center', minwidth=100)
        source_tree.column("inventory", width=100, anchor='center', minwidth=80)
        source_tree.column("profit_rate", width=100, anchor='center', minwidth=80)
        
        # 创建更好的样式
        style = ttk.Style()
        style.configure("Dashboard.Treeview", rowheight=30, font=(self.chinese_font, 10))
        style.configure("Dashboard.Treeview.Heading", font=(self.chinese_font, 10, "bold"), 
                        background="#f0f0f0", foreground="#333333", relief="flat")
        
        # 设置表格行交替颜色
        style.map("Dashboard.Treeview",
                 background=[("selected", "#3498db")],
                 foreground=[("selected", "#ffffff")])
        
        # 添加垂直滚动条
        source_scrollbar = ttk.Scrollbar(inner_frame, orient="vertical", command=source_tree.yview)
        source_tree.configure(yscrollcommand=source_scrollbar.set)
        
        # 正确的打包顺序：先打包表格，再打包滚动条
        source_tree.pack(side='left', fill='both', expand=True, padx=(0, 3), pady=0)
        source_scrollbar.pack(side='right', fill='y', pady=0)
        
        # 获取真实库存数据
        inventory_data = self.get_inventory_data()
        
        # 如果没有数据，显示示例数据
        if not inventory_data:
            inventory_data = [
                ("金币（万）", "4,321", "+24.0%", 24),
                ("银两（万）", "4,033", "+18.0%", 18),
                ("江湖声望", "3,128", "+32.0%", 32),
                ("江湖侠名", "2,104", "+33.0%", 33),
                ("充值点卡", "2,003", "+30.0%", 30),
                ("内功心法", "1,894", "+15.0%", 15),
                ("门派令牌", "405", "+12.0%", 12),
            ]
        
        # 添加数据到表格
        for idx, (item, inventory, profit_rate, rate_value) in enumerate(inventory_data):
            item_id = source_tree.insert("", "end", values=(item, inventory, profit_rate))
            
            # 设置交替行颜色底色
            if idx % 2 == 0:
                # 偶数行
                if rate_value > 0:
                    bg_color = "#e6f7f0"  # 浅绿色
                elif rate_value < 0:
                    bg_color = "#f7e6e6"  # 浅红色
                else:
                    bg_color = "#f0f0f0"  # 浅灰色
            else:
                # 奇数行 - 稍微深一点的颜色
                if rate_value > 0:
                    bg_color = "#d6efe6"  # 深一点的绿色
                elif rate_value < 0:
                    bg_color = "#efdbdb"  # 深一点的红色
                else:
                    bg_color = "#e6e6e6"  # 深一点的灰色
            
            # 配置标签和应用
            tag_name = f"row_{idx}"
            source_tree.tag_configure(tag_name, background=bg_color)
            source_tree.item(item_id, tags=(tag_name,))
            
        # 保存库存详情表格的引用供自动滚动使用
        self.inventory_detail_tree = source_tree

        # 柱状图
        chart_frame2 = LabelFrame(bottom_frame, text="月度收入", bootstyle="primary")
        chart_frame2.pack(side='left', pady=10, fill='both', expand=True)
        
        # 绘制柱状图
        plt.style.use('seaborn-v0_8-whitegrid')
        fig2, ax2 = plt.subplots(figsize=(4, 3), dpi=100)
        fig2.patch.set_facecolor('#f9f9f9')
        ax2.set_facecolor('#f9f9f9')
        
        months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
        values = [random.randint(30000, 80000) for _ in months]
        
        # 使用渐变色
        colors = ['#3498db' if i != datetime.now().month - 1 else '#e74c3c' for i in range(len(months))]
        
        bars = ax2.bar(months, values, color=colors, width=0.6, edgecolor='white', linewidth=1)
        
        # 高亮当前月
        current_month_idx = datetime.now().month - 1
        if 0 <= current_month_idx < len(months):
            ax2.text(current_month_idx, values[current_month_idx] + 2000, "当前", 
                    ha='center', va='bottom', color='#e74c3c', fontweight='bold', fontfamily=self.chinese_font)
        
        # 美化图表
        ax2.set_ylabel("金额", fontsize=10, color='#7f8c8d', fontfamily=self.chinese_font)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color('#bdc3c7')
        ax2.spines['bottom'].set_color('#bdc3c7')
        ax2.tick_params(axis='x', labelsize=8, colors='#7f8c8d', rotation=45)
        ax2.tick_params(axis='y', labelsize=8, colors='#7f8c8d')
        
        # 单独设置刻度标签字体
        for label in ax2.get_xticklabels():
            label.set_fontfamily(self.chinese_font)
        for label in ax2.get_yticklabels():
            label.set_fontfamily(self.chinese_font)
        
        # 格式化y轴
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x/1000)}k"))
        
        fig2.tight_layout(pad=2)
        canvas2 = FigureCanvasTkAgg(fig2, master=chart_frame2)
        canvas2.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        plt.close(fig2)

    def change_period(self, period_var, period, chart_frame):
        """切换周期并重绘图表"""
        period_var.set(period)
        self.draw_trend_chart(chart_frame, period)

    def refresh_dashboard(self):
        """刷新仪表盘数据"""
        try:
            # 先停止现有的滚动
            self.stop_inventory_auto_scroll()
            
            # 获取库存统计
            inventory_stats = self.db_manager.get_inventory_stats()
            if inventory_stats:
                total_items, total_quantity, total_value = inventory_stats
                self.total_items_var.set(f"{total_items}")
                self.total_quantity_var.set(f"{total_quantity:,}")
                self.total_value_var.set(f"¥{total_value:,.2f}")
            
            # 获取零库存物品
            zero_inventory = self.db_manager.get_zero_inventory_items()
            
            # 只在low_stock_tree存在时才操作
            if hasattr(self, 'low_stock_tree'):
                # 清空零库存列表
                for item in self.low_stock_tree.get_children():
                    self.low_stock_tree.delete(item)
                
                # 添加零库存物品
                if zero_inventory:
                    self.low_stock_var.set(f"{len(zero_inventory)}项")
                    
                    for item in zero_inventory:
                        item_id, item_name, quantity = item
                        self.low_stock_tree.insert("", "end", values=(item_name, quantity), tags=("warning",))
                    
                    # 设置警告标签样式
                    self.low_stock_tree.tag_configure("warning", foreground="#ff6000")
                else:
                    self.low_stock_var.set("0项")
            elif hasattr(self, 'low_stock_var'):
                # 如果没有tree但有var,仍然可以更新计数
                if zero_inventory:
                    self.low_stock_var.set(f"{len(zero_inventory)}项")
                else:
                    self.low_stock_var.set("0项")
            
            # 更新用户库存监控
            if hasattr(self, 'user_inventory_tree'):
                self.update_user_inventory_monitor()
                
            # 获取最近交易记录
            recent_transactions = self.db_manager.get_recent_transactions(5)
            
            # 只在recent_trades_tree存在时才操作
            if hasattr(self, 'recent_trades_tree'):
                # 清空最近交易列表
                for item in self.recent_trades_tree.get_children():
                    self.recent_trades_tree.delete(item)
                
                # 添加最近交易
                if recent_transactions:
                    for transaction in recent_transactions:
                        _, item_name, _, quantity, price, _, _, _, transaction_time, *_ = transaction
                        
                        # 格式化日期时间
                        if isinstance(transaction_time, str):
                            transaction_time = transaction_time
                        else:
                            transaction_time = transaction_time.strftime("%Y-%m-%d %H:%M")
                            
                        self.recent_trades_tree.insert("", "end", values=(
                            item_name, 
                            f"{int(quantity):,}", 
                            f"¥{float(price):,.2f}", 
                            transaction_time
                        ))
            
            # 刷新银两和女娲石价格数据
            self.refresh_price_data()
            
            # 刷新完成后，启动库存详情表格的自动滚动
            # 延迟1秒启动，确保数据加载完成
            self.after(1000, self.start_inventory_auto_scroll)
            
        except Exception as e:
            print(f"刷新仪表盘失败: {e}")
            import traceback
            traceback.print_exc()
            
    def refresh_price_data(self):
        """专门用于刷新价格数据的方法"""
        if not hasattr(self, 'silver_price_label') or not hasattr(self, 'nvwa_price_label'):
            return

        # 立即显示缓存的价格数据（如果有）
        if self.silver_price_cache:
            self.silver_price_label.config(text=self.silver_price_cache)
        if self.nvwa_price_cache:
            self.nvwa_price_label.config(text=self.nvwa_price_cache)
        
        # 定义是否应该立即刷新价格数据的条件
        force_refresh = (
            # 如果银两价格显示为"加载中..."，强制刷新
            (hasattr(self, 'silver_price_label') and self.silver_price_label.cget("text") == "加载中...") or
            # 如果距离上次更新超过5分钟，强制刷新
            (time.time() - self.last_price_update > 300) or  # 5分钟 = 300秒
            # 如果缓存中没有价格数据，强制刷新
            (not self.silver_price_cache or not self.nvwa_price_cache)
        )
        
        # 如果满足强制刷新条件，在后台线程中获取最新价格
        if force_refresh:
            print("正在强制刷新价格数据...")
            self.fetch_prices_in_thread()
        else:
            print(f"使用缓存的价格数据，上次更新时间: {datetime.fromtimestamp(self.last_price_update)}")

        # 只有当无法从API和缓存获取数据时，才尝试从其他Tab或数据库获取
        if not self.silver_price_cache and not self.nvwa_price_cache:
            # 从银两行情和女娲石行情标签页获取当前价格
            self._legacy_price_fetch()

    def fetch_prices_in_thread(self):
        """在后台线程中获取价格数据"""
        def fetch_task():
            silver_price = self.fetch_silver_price()
            nvwa_price = self.fetch_nvwa_price()
            
            # 在主线程中更新UI
            self.after(0, lambda: self.update_price_labels(silver_price, nvwa_price))
        
        threading.Thread(target=fetch_task, daemon=True).start()
    
    def update_price_labels(self, silver_price, nvwa_price):
        """更新价格标签"""
        if hasattr(self, 'silver_price_label'):
            if silver_price:
                self.silver_price_label.config(text=silver_price)
            elif self.silver_price_cache:
                self.silver_price_label.config(text=self.silver_price_cache)
        
        if hasattr(self, 'nvwa_price_label'):
            if nvwa_price:
                self.nvwa_price_label.config(text=nvwa_price)
            elif self.nvwa_price_cache:
                self.nvwa_price_label.config(text=self.nvwa_price_cache)

    def fetch_silver_price(self):
        """直接从API获取银两价格数据"""
        try:
            # 使用与SilverPriceTab相同的正确API URL
            urls = [
                "https://www.zxsjinfo.com/api/gold-price?days=7&server=%E7%91%B6%E5%85%89%E6%B2%81%E9%9B%AA",  # 从SilverPriceTab验证可用的URL
                "https://www.zxsjinfo.com/api/gold-price?days=7",  # 不带服务器参数的URL
                "https://www.zxsjinfo.com/api/silver-price?days=7",  # 原始URL
                "https://www.zxsjinfo.com/api/silver_price?days=7",  # 下划线替代连字符
                "https://www.zxsjinfo.com/api/price?type=silver&days=7",  # 可能的通用格式
                "https://www.zxsjinfo.com/api/game-prices?item=silver&days=7"  # 另一种可能格式
            ]
            
            # 更详细的日志输出
            print(f"开始获取银两价格数据，尝试多个URL...")
            
            for url in urls:
                try:
                    print(f"尝试从 {url} 获取银两价格")
                    # 增加超时时间并忽略SSL验证（与main_window一致）
                    response = requests.get(url, timeout=20, verify=False)
                    print(f"请求状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        # 打印JSON结构，帮助调试
                        print(f"获取到数据结构: {list(data.keys() if isinstance(data, dict) else ['不是字典'])}")
                        
                        if data and isinstance(data, dict):
                            if 'series' in data:
                                # 优先使用DD373平台价格
                                if 'DD373' in data['series'] and data['series']['DD373'] and len(data['series']['DD373']) > 0:
                                    latest_price = data['series']['DD373'][-1]
                                    self.silver_price_cache = f"¥{latest_price:.2f}/万"
                                    self.last_price_update = time.time()
                                    self.save_price_cache()
                                    print(f"成功获取银两价格(DD373): {self.silver_price_cache}")
                                    return self.silver_price_cache
                                
                                # 如果没有DD373平台，使用任何可用平台
                                print(f"发现的平台: {list(data['series'].keys())}")
                                for platform, prices in data['series'].items():
                                    print(f"发现平台: {platform}, 价格数量: {len(prices) if prices else 0}")
                                    if prices and len(prices) > 0:
                                        latest_price = prices[-1]
                                        # 更新缓存
                                        self.silver_price_cache = f"¥{latest_price:.2f}/万"
                                        self.last_price_update = time.time()
                                        self.save_price_cache()
                                        print(f"成功获取银两价格({platform}): {self.silver_price_cache}")
                                        return self.silver_price_cache
                            elif 'price' in data:
                                # 可能的替代格式
                                latest_price = float(data['price'])
                                self.silver_price_cache = f"¥{latest_price:.2f}/万"
                                self.last_price_update = time.time()
                                self.save_price_cache()
                                print(f"成功获取银两价格(替代格式): {self.silver_price_cache}")
                                return self.silver_price_cache
                            else:
                                # 尝试其他可能的数据结构
                                print(f"未识别的数据结构: {data}")
                                for key, value in data.items():
                                    print(f"键: {key}, 值类型: {type(value)}")
                except Exception as e:
                    print(f"尝试URL {url} 失败: {e}")
                    continue
            
            # 直接从main_gui获取价格数据
            try:
                if hasattr(self.main_gui, 'fetch_silver_price_multi_series'):
                    print("尝试从main_gui.fetch_silver_price_multi_series获取价格...")
                    data = self.main_gui.fetch_silver_price_multi_series(7)
                    if data and 'series' in data:
                        # 优先使用DD373平台价格，与main_window中的代码保持一致
                        if 'DD373' in data['series'] and data['series']['DD373'] and len(data['series']['DD373']) > 0:
                            latest_price = data['series']['DD373'][-1]
                            self.silver_price_cache = f"¥{latest_price:.2f}/万"
                            self.last_price_update = time.time()
                            self.save_price_cache()
                            print(f"从main_gui成功获取银两价格(DD373): {self.silver_price_cache}")
                            return self.silver_price_cache
                        # 尝试使用其他平台价格
                        for platform, prices in data['series'].items():
                            if prices and len(prices) > 0:
                                latest_price = prices[-1]
                                self.silver_price_cache = f"¥{latest_price:.2f}/万"
                                self.last_price_update = time.time()
                                self.save_price_cache()
                                print(f"从main_gui成功获取银两价格({platform}): {self.silver_price_cache}")
                                return self.silver_price_cache
            except Exception as e:
                print(f"从main_gui获取银两价格失败: {e}")
            
            # 所有URL都失败，尝试从SilverPriceTab直接获取当前价格
            if hasattr(self.main_gui, 'silver_price_tab') and self.main_gui.silver_price_tab:
                if hasattr(self.main_gui.silver_price_tab, 'current_price_label'):
                    try:
                        silver_text = self.main_gui.silver_price_tab.current_price_label.cget("text")
                        if silver_text and silver_text != "--":
                            print(f"从SilverPriceTab获取到价格: {silver_text}")
                            # 转换格式为¥xx.xx/万
                            try:
                                price_value = float(silver_text)
                                silver_text = f"¥{price_value:.2f}/万"
                            except:
                                pass
                            self.silver_price_cache = silver_text
                            self.last_price_update = time.time()
                            self.save_price_cache()
                            return silver_text
                    except Exception as e:
                        print(f"从SilverPriceTab获取价格失败: {e}")
            
            # 如果缓存中有数据，返回缓存
            if self.silver_price_cache:
                print(f"使用缓存的银两价格: {self.silver_price_cache}")
                return self.silver_price_cache
                
            return None
        except Exception as e:
            print(f"获取银两价格失败(外层异常): {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def fetch_nvwa_price(self):
        """直接从API获取女娲石价格数据"""
        try:
            # 使用NvwaPriceTab中相同的API地址
            url = "https://www.zxsjinfo.com/api/nvwa-price?days=7"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and 'series' in data:
                    # 获取最新价格
                    for platform, prices in data['series'].items():
                        if prices and len(prices) > 0:
                            latest_price = prices[-1]
                            # 更新缓存
                            self.nvwa_price_cache = f"¥{latest_price:.2f}/个"
                            self.last_price_update = time.time()
                            self.save_price_cache()
                            return self.nvwa_price_cache
            return None
        except Exception as e:
            print(f"获取女娲石价格失败: {e}")
            return None
    
    def load_price_cache(self):
        """加载缓存的价格数据"""
        try:
            if os.path.exists(self.price_cache_file):
                with open(self.price_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.silver_price_cache = cache_data.get('silver_price')
                    self.nvwa_price_cache = cache_data.get('nvwa_price')
                    self.last_price_update = cache_data.get('timestamp', 0)
        except Exception as e:
            print(f"加载价格缓存失败: {e}")
    
    def save_price_cache(self):
        """保存价格数据到缓存文件"""
        try:
            cache_data = {
                'silver_price': self.silver_price_cache,
                'nvwa_price': self.nvwa_price_cache,
                'timestamp': self.last_price_update
            }
            with open(self.price_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"保存价格缓存失败: {e}")
            
    def _legacy_price_fetch(self):
        """实现旧的从其他Tab或数据库获取价格的方法"""
        # 获取银两价格
        silver_price = "加载中..."
        silver_from_ui = False
        
        # 先尝试从UI获取
        if hasattr(self.main_gui, 'silver_price_tab') and self.main_gui.silver_price_tab:
            if hasattr(self.main_gui.silver_price_tab, 'current_price_label'):
                try:
                    silver_text = self.main_gui.silver_price_tab.current_price_label.cget("text")
                    if silver_text and silver_text != "--":
                        silver_price = silver_text
                        silver_from_ui = True
                except Exception:
                    pass
        
        # 如果无法从UI获取，直接从数据库获取
        if not silver_from_ui:
            try:
                silver_data = self.db_manager.fetch_one(
                    "SELECT price FROM silver_price ORDER BY update_time DESC LIMIT 1"
                )
                if silver_data and silver_data[0]:
                    silver_price = f"¥{float(silver_data[0]):.2f}/万"
            except Exception as e:
                print(f"从数据库获取银两价格数据失败: {e}")
        
        self.silver_price_label.config(text=silver_price)
        if silver_price != "加载中...":
            self.silver_price_cache = silver_price
            self.last_price_update = time.time()
            self.save_price_cache()
        
        # 获取女娲石价格
        nvwa_price = "加载中..."
        nvwa_from_ui = False
        
        # 先尝试从UI获取
        if hasattr(self.main_gui, 'nvwa_price_tab') and self.main_gui.nvwa_price_tab:
            if hasattr(self.main_gui.nvwa_price_tab, 'current_price_label'):
                try:
                    nvwa_text = self.main_gui.nvwa_price_tab.current_price_label.cget("text")
                    if nvwa_text and nvwa_text != "--":
                        nvwa_price = nvwa_text
                        nvwa_from_ui = True
                except Exception:
                    pass
        
        # 如果无法从UI获取，直接从数据库获取
        if not nvwa_from_ui:
            try:
                nvwa_data = self.db_manager.fetch_one(
                    "SELECT price FROM nvwa_price ORDER BY update_time DESC LIMIT 1"
                )
                if nvwa_data and nvwa_data[0]:
                    nvwa_price = f"¥{float(nvwa_data[0]):.2f}/个"
            except Exception as e:
                print(f"从数据库获取女娲石价格数据失败: {e}")
        
        self.nvwa_price_label.config(text=nvwa_price)
        if nvwa_price != "加载中...":
            self.nvwa_price_cache = nvwa_price
            self.last_price_update = time.time()
            self.save_price_cache()

    def draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        """绘制圆角矩形"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)
        
    def draw_semi_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        """绘制半圆角矩形（只有上方圆角）"""
        points = [
            x1 + radius, y1,  # 左上角圆角起始点
            x2 - radius, y1,  # 右上角圆角起始点
            x2, y1,           # 右上角顶点
            x2, y1 + radius,  # 右上角圆角结束点
            x2, y2,           # 右下角（直角）
            x1, y2,           # 左下角（直角）
            x1, y1 + radius,  # 左上角圆角结束点
            x1, y1            # 左上角顶点
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)
        
    def get_semi_rounded_rectangle_points(self, x1, y1, x2, y2, radius=25):
        """获取半圆角矩形的点（只有上方圆角）"""
        return [
            x1 + radius, y1,  # 左上角圆角起始点
            x2 - radius, y1,  # 右上角圆角起始点
            x2, y1,           # 右上角顶点
            x2, y1 + radius,  # 右上角圆角结束点
            x2, y2,           # 右下角（直角）
            x1, y2,           # 左下角（直角）
            x1, y1 + radius,  # 左上角圆角结束点
            x1, y1            # 左上角顶点
        ]
        
    def create_card_shadow(self, canvas, x1, y1, x2, y2, radius=15, shadow_size=3):
        """为卡片创建阴影效果"""
        # 绘制阴影（浅灰色多边形，稍微偏移）
        shadow_offset = shadow_size
        shadow_points = [
            x1 + radius + shadow_offset, y1 + shadow_offset,
            x2 - radius, y1 + shadow_offset,
            x2, y1 + shadow_offset,
            x2 + shadow_offset, y1 + radius,
            x2 + shadow_offset, y2,
            x2, y2 + shadow_offset,
            x1, y2 + shadow_offset, 
            x1 - shadow_offset, y2,
            x1 - shadow_offset, y1 + radius,
            x1, y1 + shadow_offset
        ]
        return canvas.create_polygon(shadow_points, fill="#E0E0E0", outline="", smooth=True)

    def get_inventory_data(self):
        """从数据库获取库存管理数据，计算库存数量和利润率"""
        db_manager = getattr(self.main_gui, 'db_manager', None)
        if db_manager is None:
            return []
            
        # 获取入库和出库数据
        stock_in_data = db_manager.get_stock_in()
        stock_out_data = db_manager.get_stock_out()
        
        # 计算每种物品的库存和价值
        inventory_dict = {}
        
        # 统计入库
        for row in stock_in_data:
            try:
                _, item_name, _, qty, cost, *_ = row
                qty = float(qty)
                cost = float(cost)
                if item_name not in inventory_dict:
                    inventory_dict[item_name] = {
                        'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                    }
                inventory_dict[item_name]['in_qty'] += qty
                inventory_dict[item_name]['in_amount'] += cost
            except Exception as e:
                continue
                
        # 统计出库
        for row in stock_out_data:
            try:
                _, item_name, _, qty, unit_price, fee, deposit, total_amount, note, *_ = row
                qty = float(qty)
                unit_price = float(unit_price)
                fee = float(fee)
                amount = unit_price * qty - fee
                if item_name not in inventory_dict:
                    inventory_dict[item_name] = {
                        'in_qty': 0, 'in_amount': 0, 'out_qty': 0, 'out_amount': 0
                    }
                inventory_dict[item_name]['out_qty'] += qty
                inventory_dict[item_name]['out_amount'] += amount
            except Exception as e:
                continue
        
        # 计算库存数量和利润率
        result = []
        for item, data in inventory_dict.items():
            remain_qty = data['in_qty'] - data['out_qty']
            
            # 显示所有物品，不管库存是否为正
            # 计算平均入库成本和平均出库价格
            in_avg = data['in_amount'] / data['in_qty'] if data['in_qty'] else 0
            out_avg = data['out_amount'] / data['out_qty'] if data['out_qty'] else 0
            
            # 计算利润率
            profit_rate = 0
            if in_avg > 0 and out_avg > 0:
                profit_rate = (out_avg - in_avg) / in_avg * 100
            
            # 格式化数据 - 改进格式化方式
            if abs(remain_qty) < 1000:
                formatted_qty = f"{int(remain_qty):d}"
            else:
                formatted_qty = f"{int(remain_qty):,d}"
                
            formatted_rate = f"{profit_rate:+.1f}%"
            
            result.append((item, formatted_qty, formatted_rate, profit_rate))
        
        # 首先按库存是否为正排序，然后按库存数量从高到低排序
        result.sort(key=lambda x: (-1 if float(x[1].replace(',', '')) > 0 else 1, -float(x[1].replace(',', '').replace('-', ''))))
        
        # 取所有项，但最多显示7项
        return result[:7]

    def update_user_inventory_monitor(self):
        """更新用户库存监控数据"""
        # 先停止现有的自动滚动
        self.stop_auto_scroll()
        
        # 清空现有数据
        for item in self.user_inventory_tree.get_children():
            self.user_inventory_tree.delete(item)
            
        # 加载备注规则配置
        note_rules = self.load_note_rules()
        if not note_rules:
            # 如果没有规则，显示一条提示信息
            self.user_inventory_tree.insert("", "end", values=("未设置规则", "请在设置->公式管理中配置", ""))
            return
            
        # 获取入库和出库数据
        try:
            stock_in_data = self.db_manager.get_stock_in()
            stock_out_data = self.db_manager.get_stock_out()
            
            # 遍历每个备注规则
            for note_value, username in note_rules.items():
                # 查找所有该备注值对应的物品
                items_with_note = {}
                
                # 处理入库数据
                for row in stock_in_data:
                    try:
                        _, item_name, _, qty, _, _, note, *_ = row
                        if note and str(note).strip() == note_value:
                            if item_name not in items_with_note:
                                items_with_note[item_name] = {'in': 0, 'out': 0}
                            items_with_note[item_name]['in'] += float(qty)
                    except Exception as e:
                        continue
                        
                # 处理出库数据
                for row in stock_out_data:
                    try:
                        _, item_name, _, qty, _, _, _, _, note, *_ = row
                        if note and str(note).strip() == note_value:
                            if item_name not in items_with_note:
                                items_with_note[item_name] = {'in': 0, 'out': 0}
                            items_with_note[item_name]['out'] += float(qty)
                    except Exception as e:
                        continue
                
                # 计算每个物品的库存数量并添加到表格
                for item_name, quantities in items_with_note.items():
                    inventory = quantities['in'] - quantities['out']
                    if inventory > 0:  # 只显示有库存的物品
                        # 设置库存数量的阈值，用于颜色标记
                        # 库存大于100为高库存(绿色)，小于30为低库存(红色)
                        tags = []
                        if inventory > 100:
                            tags.append('inventory_high')  # 高库存标签
                        elif inventory < 30:
                            tags.append('inventory_low')   # 低库存标签
                            
                        self.user_inventory_tree.insert("", "end", values=(
                            username,
                            item_name,
                            f"{int(inventory):,}"
                        ), tags=tags)
                        
            # 设置交替行颜色
            for i, item_id in enumerate(self.user_inventory_tree.get_children()):
                # 获取当前标签
                current_tags = list(self.user_inventory_tree.item(item_id, "tags"))
                # 添加交替行颜色标签
                if i % 2 == 0:
                    if 'evenrow' not in current_tags:
                        current_tags.append('evenrow')
                else:
                    if 'oddrow' not in current_tags:
                        current_tags.append('oddrow')
                # 更新标签
                self.user_inventory_tree.item(item_id, tags=current_tags)
                    
            # 如果没有数据，显示提示信息
            if not self.user_inventory_tree.get_children():
                self.user_inventory_tree.insert("", "end", values=("无匹配数据", "请检查备注规则设置", ""))
            
            # 检查是否应该启动自动滚动
            # 如果行数大于5，自动开始滚动
            if len(self.user_inventory_tree.get_children()) > 5:
                # 如果之前已启用自动滚动，则重新启动
                if self.auto_scroll_enabled:
                    self.start_auto_scroll()
                
        except Exception as e:
            print(f"更新用户库存监控失败: {e}")
            self.user_inventory_tree.insert("", "end", values=("加载失败", str(e), ""))
            
    def load_note_rules(self):
        """加载备注规则配置"""
        try:
            import os
            import json
            note_rules_path = os.path.join("data", "config", "note_rules.json")
            if os.path.exists(note_rules_path):
                with open(note_rules_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # 返回默认规则
                return {"41": "柒柒柒嗷"}
        except Exception as e:
            print(f"加载备注规则失败: {e}")
            # 返回默认规则
            return {"41": "柒柒柒嗷"}

    def start_auto_scroll(self):
        """开始自动滚动"""
        if not hasattr(self, 'user_inventory_tree'):
            return
        
        # 检查是否有足够多的行来滚动
        all_items = self.user_inventory_tree.get_children()
        if len(all_items) <= 1:
            return
        
        self.auto_scroll_enabled = True
        self.perform_auto_scroll()
    
    def stop_auto_scroll(self):
        """停止自动滚动"""
        self.auto_scroll_enabled = False
        if self.auto_scroll_timer_id:
            self.after_cancel(self.auto_scroll_timer_id)
            self.auto_scroll_timer_id = None
    
    def perform_auto_scroll(self):
        """执行自动滚动"""
        if not self.auto_scroll_enabled or not hasattr(self, 'user_inventory_tree'):
            return
        
        # 获取所有项
        all_items = self.user_inventory_tree.get_children()
        if not all_items:
            self.auto_scroll_timer_id = self.after(self.auto_scroll_speed, self.perform_auto_scroll)
            return
        
        # 获取当前选中行
        current_selection = self.user_inventory_tree.selection()
        
        # 如果没有选中行或者选中的是最后一行，则选中第一行
        if not current_selection or current_selection[0] == all_items[-1]:
            next_item = all_items[0]
        else:
            # 找到当前选中行的下一行
            current_index = all_items.index(current_selection[0])
            next_item = all_items[current_index + 1]
        
        # 清除现有选择并选择下一行
        self.user_inventory_tree.selection_set(next_item)
        
        # 确保选中行可见
        self.user_inventory_tree.see(next_item)
        
        # 设置定时器进行下一次滚动
        self.auto_scroll_timer_id = self.after(self.auto_scroll_speed, self.perform_auto_scroll)
    
    def toggle_auto_scroll(self):
        """切换自动滚动状态"""
        if self.auto_scroll_enabled:
            self.stop_auto_scroll()
            if hasattr(self, 'auto_scroll_button'):
                self.auto_scroll_button.config(text="开始自动滚动", bootstyle="success")
        else:
            self.start_auto_scroll()
            if hasattr(self, 'auto_scroll_button'):
                self.auto_scroll_button.config(text="停止自动滚动", bootstyle="danger") 

    def start_inventory_auto_scroll(self):
        """开始库存详情表格自动滚动"""
        if not hasattr(self, 'inventory_detail_tree'):
            return
        
        # 检查是否有足够多的行来滚动
        all_items = self.inventory_detail_tree.get_children()
        if len(all_items) <= 1:
            return
        
        self.inventory_auto_scroll_enabled = True
        self.perform_inventory_auto_scroll()
    
    def stop_inventory_auto_scroll(self):
        """停止库存详情表格自动滚动"""
        self.inventory_auto_scroll_enabled = False
        if self.inventory_auto_scroll_timer_id:
            self.after_cancel(self.inventory_auto_scroll_timer_id)
            self.inventory_auto_scroll_timer_id = None
    
    def perform_inventory_auto_scroll(self):
        """执行库存详情表格自动滚动"""
        if not self.inventory_auto_scroll_enabled or not hasattr(self, 'inventory_detail_tree'):
            return
        
        # 获取所有项
        all_items = self.inventory_detail_tree.get_children()
        if not all_items:
            self.inventory_auto_scroll_timer_id = self.after(self.inventory_auto_scroll_speed, self.perform_inventory_auto_scroll)
            return
        
        # 获取当前选中行
        current_selection = self.inventory_detail_tree.selection()
        
        # 如果没有选中行或者选中的是最后一行，则选中第一行
        if not current_selection or current_selection[0] == all_items[-1]:
            next_item = all_items[0]
        else:
            # 找到当前选中行的下一行
            current_index = all_items.index(current_selection[0])
            next_item = all_items[current_index + 1]
        
        # 清除现有选择并选择下一行
        self.inventory_detail_tree.selection_set(next_item)
        
        # 确保选中行可见
        self.inventory_detail_tree.see(next_item)
        
        # 设置定时器进行下一次滚动
        self.inventory_auto_scroll_timer_id = self.after(self.inventory_auto_scroll_speed, self.perform_inventory_auto_scroll)