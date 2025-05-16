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

class DashboardTab(Frame):
    def __init__(self, master=None, main_gui=None, **kwargs):
        super().__init__(master, **kwargs)
        self.main_gui = main_gui
        # 设置中文字体
        self.setup_fonts()
        # 创建自定义样式
        self.setup_styles()
        self.create_widgets()
        
    def setup_fonts(self):
        """设置中文字体支持"""
        # 检测操作系统
        system = platform.system()
        
        # 设置tkinter默认字体
        self.default_font = font.nametofont("TkDefaultFont")
        self.text_font = font.nametofont("TkTextFont")
        self.fixed_font = font.nametofont("TkFixedFont")
        
        # 设置matplotlib中文字体
        if system == 'Windows':
            # Windows系统常见中文字体
            chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi']
        elif system == 'Darwin':  # macOS
            chinese_fonts = ['PingFang SC', 'Heiti SC', 'STHeiti', 'STFangsong']
        else:  # Linux等其他系统
            chinese_fonts = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Droid Sans Fallback']
        
        # 查找可用的中文字体
        font_found = False
        for font_name in chinese_fonts:
            try:
                # 检查当前系统是否有这个字体
                if font_name.lower() in [f.lower() for f in font.families()]:
                    # 为tkinter设置中文字体
                    self.default_font.configure(family=font_name)
                    self.text_font.configure(family=font_name)
                    self.fixed_font.configure(family=font_name)
                    
                    # 为matplotlib设置中文字体
                    plt.rcParams['font.family'] = [font_name, 'sans-serif']
                    plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
                    self.chinese_font = font_name
                    font_found = True
                    break
            except Exception:
                continue
                
        # 如果在tkinter字体中找不到合适的中文字体，尝试用matplotlib的字体查找机制
        if not font_found:
            for font_name in chinese_fonts:
                try:
                    font_path = fm.findfont(fm.FontProperties(family=font_name))
                    if os.path.basename(font_path).lower() != 'dejavusans.ttf':  # 不是默认字体
                        plt.rcParams['font.family'] = [font_name, 'sans-serif']
                        plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
                        self.chinese_font = font_name
                        
                        # 尝试为tkinter设置同样的字体
                        try:
                            self.default_font.configure(family=font_name)
                            self.text_font.configure(family=font_name)
                            self.fixed_font.configure(family=font_name)
                        except:
                            pass
                            
                        font_found = True
                        break
                except Exception:
                    continue
        
        # 最后的备选方案
        if not font_found:
            try:
                plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
                plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
                self.chinese_font = 'SimHei'
                try:
                    self.default_font.configure(family='SimHei')
                    self.text_font.configure(family='SimHei')
                    self.fixed_font.configure(family='SimHei')
                except:
                    # 实在不行就用微软雅黑名称
                    self.chinese_font = 'Microsoft YaHei'
            except:
                # 最后的备选方案
                self.chinese_font = 'Microsoft YaHei'
        
    def setup_styles(self):
        """设置自定义样式"""
        style = Style()
        # 卡片标题样式
        style.configure("Card.TLabelframe", borderwidth=0, relief="flat")
        style.configure("Card.TLabelframe.Label", font=(self.chinese_font, 12, "bold"), foreground="#555555")
        
        # 卡片值样式
        style.configure("CardValue.TLabel", font=(self.chinese_font, 24, "bold"), foreground="#2c3e50")
        # 卡片描述样式
        style.configure("CardDesc.TLabel", font=(self.chinese_font, 10), foreground="#7f8c8d")
        
        # 正值和负值的不同颜色
        style.configure("Positive.TLabel", foreground="#27ae60")
        style.configure("Negative.TLabel", foreground="#e74c3c")
        
        # 表格样式
        style.configure("Dashboard.Treeview", rowheight=28, font=(self.chinese_font, 10))
        style.configure("Dashboard.Treeview.Heading", font=(self.chinese_font, 10, "bold"))
        
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
        # 设置主背景色
        self.configure(style="TFrame")
        
        # 顶部搜索和标签栏
        top_frame = Frame(self, bootstyle="light")
        top_frame.pack(fill='x', pady=(0, 10))
        
        # 标签按钮区域
        tabs_frame = Frame(top_frame, bootstyle="light")
        tabs_frame.pack(side='left', padx=5)
        
        # 使用更现代的按钮样式
        Button(tabs_frame, text="概览", bootstyle="primary").pack(side='left', padx=2)
        Button(tabs_frame, text="详情", bootstyle="secondary").pack(side='left', padx=2)
        Button(tabs_frame, text="分析", bootstyle="secondary").pack(side='left', padx=2)
        
        # 搜索框
        search_frame = Frame(top_frame, bootstyle="light")
        search_frame.pack(side='right', padx=5)
        search_entry = Entry(search_frame, width=20, font=(self.chinese_font, 9))
        search_entry.insert(0, "搜索...")
        search_entry.pack(side='right')
        search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, 'end') if search_entry.get() == "搜索..." else None)
        search_entry.bind("<FocusOut>", lambda e: search_entry.insert(0, "搜索...") if search_entry.get() == "" else None)

        # 统计卡片区域
        stats_frame = Frame(self, bootstyle="light")
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
                "bg_color": "#e8f4fc"
            },
            {
                "title": "总库存价值",
                "value": f"${total_inventory_value:,.2f}",
                "desc": f"{inventory_mom:+.2f}% 月环比",
                "is_positive": inventory_mom >= 0,
                "icon": "📦",
                "bg_color": "#e8fcf4"
            },
            {
                "title": "活跃用户",
                "value": f"{active_users:,}",
                "desc": f"{active_users_mom:+.2f}% 月环比",
                "is_positive": active_users_mom >= 0,
                "icon": "👥",
                "bg_color": "#fcf8e8"
            }
        ]
        
        # 创建卡片
        for card_info in card_data:
            # 创建卡片容器
            card = Frame(stats_frame, bootstyle="light")
            card.pack(side='left', expand=True, fill='both', padx=5)
            
            # 卡片内部使用网格布局
            card.columnconfigure(0, weight=1)
            card.columnconfigure(1, weight=0)
            
            # 标题和图标行
            title_frame = Frame(card, bootstyle="light")
            title_frame.grid(row=0, column=0, sticky='w', pady=(0, 5))
            
            Label(title_frame, text=card_info["title"], font=(self.chinese_font, 11, "bold"), 
                  foreground="#555555").pack(side='left')
            
            # 数值显示
            value_label = Label(card, text=card_info["value"], 
                               font=(self.chinese_font, 22, "bold"), 
                               foreground="#2c3e50")
            value_label.grid(row=1, column=0, sticky='w')
            
            # 环比显示
            desc_style = "Positive.TLabel" if card_info["is_positive"] else "Negative.TLabel"
            desc_label = Label(card, text=card_info["desc"], style=desc_style)
            desc_label.grid(row=2, column=0, sticky='w')
            
            # 右侧图标
            icon_label = Label(card, text=card_info["icon"], font=("Segoe UI Emoji", 24))
            icon_label.grid(row=0, column=1, rowspan=3, padx=(0, 10))

        # 主体区域
        main_frame = Frame(self, bootstyle="light")
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

        # 用户列表
        user_frame = LabelFrame(main_frame, text="最近活跃用户", bootstyle="primary")
        user_frame.pack(side='left', pady=10, fill='y')
        
        # 使用树形视图替代简单标签
        user_tree = ttk.Treeview(user_frame, columns=("name", "email", "last_active"), 
                                 show="headings", height=10, style="Dashboard.Treeview")
        user_tree.heading("name", text="用户名")
        user_tree.heading("email", text="邮箱")
        user_tree.heading("last_active", text="最近活动")
        
        user_tree.column("name", width=100)
        user_tree.column("email", width=180)
        user_tree.column("last_active", width=100)
        
        user_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 添加用户数据
        user_data = [
            ("Helena", "email@figmasfakedomain.net", "今天"),
            ("Oscar", "email@figmasfakedomain.net", "昨天"),
            ("Daniel", "email@figmasfakedomain.net", "2天前"),
            ("Daniel Jay Park", "email@figmasfakedomain.net", "3天前"),
            ("Mark Rojas", "email@figmasfakedomain.net", "1周前"),
            ("李明", "email@figmasfakedomain.net", "1周前"),
            ("王芳", "email@figmasfakedomain.net", "2周前"),
            ("张伟", "email@figmasfakedomain.net", "2周前"),
            ("刘洋", "email@figmasfakedomain.net", "1个月前"),
            ("陈晓", "email@figmasfakedomain.net", "1个月前"),
        ]
        
        for user in user_data:
            user_tree.insert("", "end", values=user)
        
        # 添加滚动条
        user_scrollbar = ttk.Scrollbar(user_frame, orient="vertical", command=user_tree.yview)
        user_tree.configure(yscrollcommand=user_scrollbar.set)
        user_scrollbar.pack(side='right', fill='y')

        # 下方区域
        bottom_frame = Frame(self, bootstyle="light")
        bottom_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # 数据表
        table_frame = LabelFrame(bottom_frame, text="流量来源", bootstyle="primary")
        table_frame.pack(side='left', padx=(0, 10), pady=10, fill='both', expand=True)
        
        # 使用树形视图
        source_tree = ttk.Treeview(table_frame, columns=("source", "sessions", "change"), 
                                  show="headings", height=6, style="Dashboard.Treeview")
        source_tree.heading("source", text="来源")
        source_tree.heading("sessions", text="会话数")
        source_tree.heading("change", text="变化")
        
        source_tree.column("source", width=150)
        source_tree.column("sessions", width=100, anchor='center')
        source_tree.column("change", width=100, anchor='center')
        
        source_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 添加数据
        source_data = [
            ("website.net", "4,321", "+84%"),
            ("search.com", "4,033", "-8%"),
            ("social.app", "3,128", "+2%"),
            ("ads.platform", "2,104", "+33%"),
            ("partner.site", "2,003", "+30%"),
            ("blog.company", "1,894", "+15%"),
            ("direct", "405", "-12%"),
        ]
        
        for idx, (source, sessions, change) in enumerate(source_data):
            item_id = source_tree.insert("", "end", values=(source, sessions, change))
            # 根据变化值设置行颜色
            if change.startswith("+"):
                source_tree.tag_configure(f"positive_{idx}", background="#e8fff0")
                source_tree.item(item_id, tags=(f"positive_{idx}",))
            elif change.startswith("-"):
                source_tree.tag_configure(f"negative_{idx}", background="#fff0f0")
                source_tree.item(item_id, tags=(f"negative_{idx}",))

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