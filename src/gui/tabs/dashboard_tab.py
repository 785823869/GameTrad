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
import queue
import calendar

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
        self.setup_matplotlib_fonts()  # 设置Matplotlib的中文字体
        
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
    
    def setup_matplotlib_fonts(self):
        """设置Matplotlib的中文字体支持"""
        import matplotlib.font_manager as fm
        import platform
        
        # 获取当前已安装的所有字体
        all_fonts = fm.findSystemFonts(fontpaths=None, fontext='ttf')
        chinese_fonts = []
        
        # 根据操作系统设置中文字体
        system = platform.system()
        if system == "Windows":
            # Windows常见中文字体
            preferred_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi']
        elif system == "Darwin":  # macOS
            # macOS常见中文字体
            preferred_fonts = ['PingFang SC', 'Heiti SC', 'STHeiti', 'STSong', 'STKaiti']
        else:  # Linux和其他系统
            # Linux常见中文字体
            preferred_fonts = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Noto Sans CJK TC', 'Droid Sans Fallback']
        
        # 检查我们的默认字体是否已在列表中
        if self.chinese_font not in preferred_fonts:
            preferred_fonts.insert(0, self.chinese_font)
        
        # 检查每个系统字体是否支持中文
        for font_path in all_fonts:
            try:
                font_name = fm.FontProperties(fname=font_path).get_name()
                if any(preferred in font_name for preferred in preferred_fonts):
                    chinese_fonts.append(font_name)
            except Exception:
                continue
        
        # 如果没有找到中文字体，尝试使用备选方案
        if not chinese_fonts:
            # 检查每个首选字体是否可用
            available_fonts = []
            for font in preferred_fonts:
                try:
                    if fm.findfont(fm.FontProperties(family=font)) != fm.findfont(fm.FontProperties()):
                        available_fonts.append(font)
                        chinese_fonts.append(font)
                except:
                    continue
        
        # 如果仍然没有找到中文字体，使用系统默认字体
        if not chinese_fonts:
            chinese_fonts = [self.chinese_font]
            print("警告: 未能找到合适的中文字体，使用系统默认字体")
            
        # 设置Matplotlib全局字体
        plt.rcParams['font.family'] = ['sans-serif']
        plt.rcParams['font.sans-serif'] = chinese_fonts
        
        # 确保负号显示正确
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置其他图表参数以优化显示
        plt.rcParams['figure.facecolor'] = '#f9f9f9'
        plt.rcParams['axes.facecolor'] = '#f9f9f9'
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        plt.rcParams['grid.linestyle'] = '--'
        
        # 打印找到的中文字体，便于调试
        print(f"matplotlib将使用以下中文字体: {', '.join(chinese_fonts[:3])}{' 等' if len(chinese_fonts) > 3 else ''}")
    
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
        
        # 确保使用正确的中文字体
        chinese_font_family = self.get_suitable_chinese_font()
        
        # 卡片标题样式
        style.configure("Card.TLabelframe", borderwidth=0, relief="flat")
        style.configure("Card.TLabelframe.Label", font=(chinese_font_family, 12, "bold"), foreground="#2c3e50")
        
        # 卡片值样式 - 加深文字颜色
        style.configure("CardValue.TLabel", font=(chinese_font_family, 24, "bold"), foreground="#2c3e50")
        # 卡片描述样式 - 提高对比度
        style.configure("CardDesc.TLabel", font=(chinese_font_family, 10), foreground="#34495e")
        
        # 正值和负值的不同颜色 - 增强对比度
        style.configure("Positive.TLabel", foreground="#27ae60")  # 深绿色
        style.configure("Negative.TLabel", foreground="#c0392b")  # 深红色
        
        # 表格样式 - 提高可读性
        style.configure("Dashboard.Treeview", 
                       rowheight=28, 
                       font=(chinese_font_family, 10),
                       background="#ffffff",
                       fieldbackground="#ffffff",
                       foreground="#2c3e50")
                       
        style.configure("Dashboard.Treeview.Heading", 
                       font=(chinese_font_family, 10, "bold"),
                       background="#e0e6ed",
                       foreground="#2c3e50")
        
        # 用户库存监控表格的颜色标签样式
        style.map("Dashboard.Treeview",
                 background=[("selected", "#3498db")],
                 foreground=[("selected", "#ffffff")])
        
        # 注意：Treeview标签样式(如高库存、低库存和交替行颜色)
        # 需要在Treeview实例上使用tag_configure进行配置，而不是在Style对象上
        
        # 配置所有标签使用中文字体
        style.configure("TLabel", font=(chinese_font_family, 10))
        style.configure("TButton", font=(chinese_font_family, 10))
        style.configure("TEntry", font=(chinese_font_family, 10))
        style.configure("TCheckbutton", font=(chinese_font_family, 10))
        style.configure("TRadiobutton", font=(chinese_font_family, 10))
        style.configure("TCombobox", font=(chinese_font_family, 10))
        
        # 设置标签框
        style.configure("TLabelframe", font=(chinese_font_family, 10))
        style.configure("TLabelframe.Label", font=(chinese_font_family, 10, "bold"))
        
        # 主题级别的默认字体设置
        style.configure(".", font=(chinese_font_family, 10))
    
    def get_suitable_chinese_font(self):
        """获取适合系统的中文字体"""
        import platform
        import tkinter.font as tkfont
        
        # 尝试从系统获取所有可用字体
        root = self.winfo_toplevel()
        available_fonts = list(tkfont.families(root))
        
        # 根据操作系统推荐字体
        system = platform.system()
        if system == "Windows":
            preferred_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi']
        elif system == "Darwin":  # macOS
            preferred_fonts = ['PingFang SC', 'Heiti SC', 'STHeiti', 'STSong', 'STKaiti']
        else:  # Linux和其他系统
            preferred_fonts = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Noto Sans CJK TC', 'Droid Sans Fallback']
        
        # 添加当前使用的中文字体
        if self.chinese_font not in preferred_fonts:
            preferred_fonts.insert(0, self.chinese_font)
        
        # 找到第一个可用的中文字体
        for font in preferred_fonts:
            if font in available_fonts:
                print(f"使用中文字体: {font}")
                return font
        
        # 如果没有找到合适的字体，使用系统默认字体
        print("警告: 未找到合适的中文字体，使用系统默认字体")
        return self.chinese_font

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

    def get_total_trading_profit(self):
        """计算库存管理中所有物品的成交利润额总和"""
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
                
        # 计算总成交利润额
        total_profit = 0.0
        for item, data in inventory_dict.items():
            # 只计算有出库记录的物品
            if data['out_qty'] <= 0:
                continue
            # 计算入库均价
            in_avg = data['in_amount'] / data['in_qty'] if data['in_qty'] > 0 else 0
            # 计算出库均价
            out_avg = data['out_amount'] / data['out_qty'] if data['out_qty'] > 0 else 0
            # 计算成交利润额
            profit = (out_avg - in_avg) * data['out_qty'] if data['out_qty'] > 0 else 0
            total_profit += profit
            
        return total_profit

    def get_total_profit_and_mom(self):
        now = datetime.now()
        # 使用新方法计算总利润
        this_month_profit = self.get_total_trading_profit()
        
        # 月环比暂时使用固定值，因为历史数据需要额外存储
        mom = 15.0  # 示例值：15%的月环比增长
        
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
        
        # 获取合适的中文字体
        chinese_font = self.get_suitable_chinese_font()
        
        # 确保图表使用正确的中文字体
        plt.rcParams['font.family'] = ['sans-serif']
        plt.rcParams['font.sans-serif'] = [chinese_font, 'SimHei', 'Microsoft YaHei', 'STHeiti', 'WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置图表样式
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(5,3), dpi=100)
        fig.patch.set_facecolor('#f9f9f9')
        ax.set_facecolor('#f9f9f9')
        
        # 如果没有数据，显示提示信息
        if not x or not y:
            plt.close(fig)
            Label(frame, text="没有出库数据可显示", font=(chinese_font, 12)).pack(pady=50)
            return
        
        # 绘制线条和点
        line_color = '#3498db'
        marker_color = '#2980b9'
        highlight_color = '#e74c3c'
        
        # 如果期间是日/周/月，需要转换字符串日期为日期对象以便使用日期定位器
        date_objects = None
        if period == 'day':
            try:
                # 尝试将日期标签转换为日期对象
                from datetime import datetime
                # 假设x中的标签是日期字符串，格式如"10"（表示月份第10天）
                # 获取当前年月作为基准
                current_year = now.year
                current_month = now.month
                
                # 创建日期对象列表
                date_objects = []
                for date_str in x:
                    try:
                        # 尝试直接解析日期字符串
                        day = int(date_str)
                        # 创建日期对象
                        date_obj = datetime(current_year, current_month, day)
                        date_objects.append(date_obj)
                    except (ValueError, TypeError):
                        # 如果解析失败，跳过
                        continue
            except Exception as e:
                print(f"转换日期标签失败: {e}")
        
        # 绘制线条和点，使用原始x作为标签
        ax.plot(range(len(x)), y, color=line_color, linewidth=2, marker='o', markersize=5, 
                markerfacecolor=marker_color, markeredgecolor='white', markeredgewidth=1, zorder=3)
        
        # 高亮最后一个点
        if x and y:
            ax.scatter([len(x)-1], [y[-1]], s=100, color=highlight_color, zorder=5, alpha=0.7,
                      edgecolors='white', linewidth=2)
        
        # 设置标题和标签，显式指定中文字体
        ax.set_title("出库金额趋势", loc='left', fontsize=14, fontweight='bold', 
                    color='#2c3e50', fontfamily=chinese_font)
        ax.set_xlabel("", fontfamily=chinese_font)
        ax.set_ylabel("金额", fontsize=11, color='#7f8c8d', fontfamily=chinese_font)
        
        # 设置网格和边框
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#bdc3c7', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#bdc3c7')
        ax.spines['bottom'].set_color('#bdc3c7')
        
        # y轴金额格式化
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
        
        # 设置x轴刻度
        # 理想刻度数量（根据图表宽度和美观度考虑）
        ideal_ticks = 6
        
        # 设置x轴标签位置
        if len(x) <= ideal_ticks:
            # 数据点较少时，全部显示
            ax.set_xticks(range(len(x)))
            ax.set_xticklabels(x, fontfamily=chinese_font)
        else:
            # 数据点较多时，均匀选择标签位置
            step = max(1, len(x) // ideal_ticks)
            positions = list(range(0, len(x), step))
            # 确保包含最后一个点
            if (len(x) - 1) not in positions:
                positions.append(len(x) - 1)
            ax.set_xticks(positions)
            ax.set_xticklabels([x[pos] for pos in positions], fontfamily=chinese_font)
        
        # 如果有日期对象，使用matplotlib的日期定位器
        if date_objects and len(date_objects) == len(x):
            from matplotlib.dates import DateFormatter, AutoDateLocator, DayLocator, date2num
            
            # 将x轴的数值刻度替换为日期刻度
            date_nums = [date2num(date) for date in date_objects]
            
            # 使用日期定位器设置均匀间隔
            min_date = min(date_objects)
            max_date = max(date_objects)
            date_range = (max_date - min_date).days + 1
            
            # 根据日期范围选择合适的定位器
            if date_range <= 7:  # 一周内，按天间隔
                ax.xaxis.set_major_locator(DayLocator(interval=max(1, date_range // ideal_ticks)))
            else:
                # 使用自动定位器
                ax.xaxis.set_major_locator(AutoDateLocator(maxticks=ideal_ticks))
                
            # 设置日期格式
            ax.xaxis.set_major_formatter(DateFormatter('%d'))  # 仅显示日
        
        # 设置所有刻度标签的字体和旋转角度
        for label in ax.get_xticklabels():
            label.set_fontfamily(chinese_font)
            label.set_fontsize(9)
            label.set_color('#7f8c8d')
            label.set_rotation(30)
            
        for label in ax.get_yticklabels():
            label.set_fontfamily(chinese_font)
            label.set_fontsize(9)
            label.set_color('#7f8c8d')
        
        # 添加平均线
        if y:
            avg_y = sum(y) / len(y)
            ax.axhline(y=avg_y, color='#e74c3c', linestyle='--', alpha=0.5, linewidth=1)
            ax.text(
                len(x)//2, avg_y, 
                f"平均: ${int(avg_y):,}", 
                color='#e74c3c', fontsize=8, fontfamily=chinese_font,
                va='bottom', ha='center', bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2')
            )
        
        # 自动调整布局，确保标签完全显示
        fig.tight_layout(pad=2.5)
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

    def draw_price_trend_chart(self, frame, item_name, period='day'):
        """绘制物品价格趋势图"""
        # 清空frame内容
        for widget in frame.winfo_children():
            widget.destroy()
        
        if not item_name:
            # 如果没有选择物品，显示提示信息
            chinese_font = self.get_suitable_chinese_font()
            Label(frame, text="请从下拉框选择物品查看价格趋势", font=(chinese_font, 12)).pack(pady=50)
            return
            
        # 获取价格数据
        in_prices, out_prices = self.get_item_price_history(item_name, period)
        
        # 如果没有数据，显示提示信息
        if not in_prices and not out_prices:
            chinese_font = self.get_suitable_chinese_font()
            Label(frame, text=f"未找到 {item_name} 的价格数据", font=(chinese_font, 12)).pack(pady=50)
            return
        
        # 确保正确设置中文字体
        chinese_font = self.get_suitable_chinese_font()
        plt.rcParams['font.family'] = ['sans-serif']
        plt.rcParams['font.sans-serif'] = [chinese_font, 'SimHei', 'Microsoft YaHei', 'STHeiti', 'WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置图表样式
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(8,5), dpi=100)
        fig.patch.set_facecolor('#f9f9f9')
        ax.set_facecolor('#f9f9f9')
        
        # 记录是否有有效数据
        has_valid_data = False
        
        # 整合所有价格数据（入库均价和出库单价）到一个时间序列中
        all_price_data = []
        
        # 添加入库均价数据
        for dt, price in in_prices:
            if dt is not None:
                all_price_data.append((dt, price, "入库"))
        
        # 添加出库单价数据
        for dt, price in out_prices:
            if dt is not None:
                all_price_data.append((dt, price, "出库"))
        
        # 按日期排序
        all_price_data.sort(key=lambda x: x[0])
        
        if all_price_data:
            has_valid_data = True
            # 提取排序后的数据
            dates = [data[0] for data in all_price_data]
            prices = [data[1] for data in all_price_data]
            
            # 绘制整合后的价格趋势线
            ax.plot(dates, prices, color='#3498db', linewidth=2, marker='o', markersize=5,
                  markerfacecolor='#2980b9', markeredgecolor='white', markeredgewidth=1, zorder=3)
        
        # 如果没有有效数据，显示提示信息
        if not has_valid_data:
            plt.close(fig)
            chinese_font = self.get_suitable_chinese_font()
            Label(frame, text=f"无法绘制 {item_name} 的价格趋势图，数据格式异常", font=(chinese_font, 12)).pack(pady=50)
            return
            
        # 设置标题和标签 - 显式指定字体
        ax.set_title(f"{item_name}物价趋势", loc='left', fontsize=14, fontweight='bold', 
                   color='#2c3e50', fontfamily=chinese_font)
        ax.set_xlabel("日期", fontsize=10, color='#7f8c8d', fontfamily=chinese_font)
        ax.set_ylabel("价格", fontsize=11, color='#7f8c8d', fontfamily=chinese_font)
        
        # 设置网格和边框
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#bdc3c7', zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#bdc3c7')
        ax.spines['bottom'].set_color('#bdc3c7')
        
        # y轴价格格式化
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
        
        # 获取所有有效日期
        all_dates = [data[0] for data in all_price_data]
        
        if all_dates:
            # 获取日期的最小值和最大值
            min_date = min(all_dates)
            max_date = max(all_dates)
            date_range = (max_date - min_date).days + 1  # 包含首尾天数
            
            # 根据日期范围选择合适的格式
            from matplotlib.dates import DateFormatter, AutoDateLocator, DayLocator, WeekdayLocator, MonthLocator, YearLocator, date2num
            
            # 标准化日期格式
            if date_range <= 2:
                # 非常短的时间跨度，显示小时
                date_format = '%H:%M'
            elif date_range <= 7:
                # 一周以内，显示日期和小时
                date_format = '%m-%d %H:%M'
            elif date_range <= 180:
                # 半年以内，显示月-日
                date_format = '%m-%d'
            else:
                # 半年以上，显示年-月
                date_format = '%Y-%m'
            
            # 设置日期格式器
            formatter = DateFormatter(date_format)
            ax.xaxis.set_major_formatter(formatter)
            
            # 优化：创建均匀分布的日期刻度
            # 理想刻度数量（根据图表宽度和美观度考虑）
            ideal_ticks = 6
            
            # 计算均匀间隔
            if date_range <= 1:  # 一天内，按小时间隔
                from matplotlib.dates import HourLocator
                ax.xaxis.set_major_locator(HourLocator(interval=max(1, 24 // ideal_ticks)))
            elif date_range <= 7:  # 一周内，按天间隔
                ax.xaxis.set_major_locator(DayLocator(interval=max(1, date_range // ideal_ticks)))
            elif date_range <= 30:  # 一个月内，几天为一个间隔
                ax.xaxis.set_major_locator(DayLocator(interval=max(1, date_range // ideal_ticks)))
            elif date_range <= 365:  # 一年内，按月或周间隔
                if date_range <= 90:  # 三个月内，按周间隔
                    ax.xaxis.set_major_locator(WeekdayLocator(interval=max(1, date_range // 7 // ideal_ticks)))
                else:  # 按月间隔
                    ax.xaxis.set_major_locator(MonthLocator(interval=max(1, date_range // 30 // ideal_ticks)))
            else:  # 一年以上，按年或月间隔
                if date_range <= 365 * 2:  # 两年内，按月间隔
                    ax.xaxis.set_major_locator(MonthLocator(interval=max(1, date_range // 30 // ideal_ticks)))
                else:  # 按年间隔
                    ax.xaxis.set_major_locator(YearLocator(base=max(1, date_range // 365 // ideal_ticks)))
            
            # 如果以上定位器导致标签过多，使用自动定位器
            if len(ax.get_xticks()) > ideal_ticks * 1.5:
                ax.xaxis.set_major_locator(AutoDateLocator(maxticks=ideal_ticks))
        
        # 设置所有刻度标签的字体
        for label in ax.get_xticklabels():
            label.set_fontfamily(chinese_font)
        for label in ax.get_yticklabels():
            label.set_fontfamily(chinese_font)
        
        # 美化x轴和y轴刻度标签
        ax.tick_params(axis='x', labelsize=9, colors='#7f8c8d', rotation=30, labelrotation=30)
        ax.tick_params(axis='y', labelsize=9, colors='#7f8c8d')
        
        # 自动调整布局，确保标签完全显示
        fig.tight_layout(pad=2.5)  # 增加边距以确保所有标签都可见
        
        # 在图表中添加当前时间段平均价格
        if prices:
            avg_price = sum(prices) / len(prices)
            ax.axhline(y=avg_price, color='#e74c3c', linestyle='--', alpha=0.5, linewidth=1)
            ax.text(
                all_dates[len(all_dates)//2], avg_price, 
                f"平均: {int(avg_price):,}", 
                color='#e74c3c', fontsize=8, fontfamily=chinese_font,
                va='bottom', ha='center', bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2')
            )
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

    def update_price_chart(self, chart_frame, item_name, period):
        """更新价格趋势图"""
        # 更新周期变量
        if hasattr(self, 'period_var'):
            self.period_var.set(period)
        
        # 重新绘制图表
        self.draw_price_trend_chart(chart_frame, item_name, period)

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
                "title": "总利润额",
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
            chinese_font = self.get_suitable_chinese_font()
            title_label = tk.Label(card, text=card_info["title"], 
                               font=(chinese_font, 11, "bold"),
                               fg="#555555", bg=bg_color)
            title_label.grid(row=0, column=0, sticky='w', pady=(5, 5))
            
            # 根据卡片类型设置内容
            if idx < 2:  # 前两个卡片（总收入，总库存价值）
                # 数值显示 - 使用透明背景
                value_label = tk.Label(card, text=card_info["value"], 
                                   font=(chinese_font, 22, "bold"),
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
                    font=(chinese_font, 11, "bold"),  # 稍微增大
                    fg=text_color, 
                    bg=bg_color
                )
                percent_label.pack(side="left", padx=0, pady=0)
                
                # "月环比"文字部分 - 使用普通字体
                label_label = tk.Label(
                    mom_frame, 
                    text=mom_label_text, 
                    font=(chinese_font, 10),  # 普通字体
                    fg="#555555",  # 使用灰色
                    bg=bg_color
                )
                label_label.pack(side="left", padx=(2, 0), pady=0)
            else:  # 第三个卡片（行情概览）
                # 银两行情行 - 使用透明背景
                silver_frame = tk.Frame(card, bg=bg_color)
                silver_frame.grid(row=1, column=0, sticky='w', pady=(0, 5))
                
                tk.Label(silver_frame, text="银两行情:", 
                     font=(chinese_font, 11),
                     fg="#555555", bg=bg_color).pack(side='left')
                
                self.silver_price_label = tk.Label(silver_frame, text="加载中...", 
                                             font=(chinese_font, 11, "bold"),
                                             fg="#2c3e50", bg=bg_color)
                self.silver_price_label.pack(side='left', padx=(5, 0))
                
                # 女娲石行情行 - 使用透明背景
                nvwa_frame = tk.Frame(card, bg=bg_color)
                nvwa_frame.grid(row=2, column=0, sticky='w')
                
                tk.Label(nvwa_frame, text="女娲石行情:", 
                     font=(chinese_font, 11),
                     fg="#555555", bg=bg_color).pack(side='left')
                
                self.nvwa_price_label = tk.Label(nvwa_frame, text="加载中...", 
                                           font=(chinese_font, 11, "bold"),
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

        # 折线图区域（带物品选择和周期切换）
        chart_container = LabelFrame(main_frame, text="物价趋势", bootstyle="primary")
        chart_container.pack(side='left', padx=(0, 10), pady=10, fill='both', expand=True)
        
        chart_top_frame = Frame(chart_container, bootstyle="light")
        chart_top_frame.pack(fill='x', padx=5, pady=5)
        
        # 物品选择下拉框
        item_frame = Frame(chart_top_frame, bootstyle="light")
        item_frame.pack(side='left')
        
        chinese_font = self.get_suitable_chinese_font()
        Label(item_frame, text="物品:", font=(chinese_font, 9)).pack(side='left')
        
        # 添加搜索框
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            item_frame, 
            textvariable=self.search_var,
            width=8,
            font=(chinese_font, 9),
            bootstyle="primary"
        )
        search_entry.pack(side='left', padx=2)
        
        # 添加提示文本
        def on_focus_in(event):
            if search_entry.get() == "搜索物品...":
                search_entry.delete(0, tk.END)
                search_entry.config(bootstyle="primary")
                
        def on_focus_out(event):
            if not search_entry.get():
                search_entry.insert(0, "搜索物品...")
                search_entry.config(bootstyle="secondary")
        
        # 设置初始提示文本
        search_entry.insert(0, "搜索物品...")
        search_entry.config(bootstyle="secondary")
        
        # 绑定焦点事件
        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)
        
        # 添加搜索图标按钮
        search_button = ttk.Button(
            item_frame,
            text="🔍",
            width=2,
            bootstyle="primary-outline",
            command=self.apply_item_filter
        )
        search_button.pack(side='left', padx=(0, 5))
        
        # 添加清空搜索按钮
        clear_button = ttk.Button(
            item_frame,
            text="✕",
            width=2,
            bootstyle="secondary-outline",
            command=self.clear_search
        )
        clear_button.pack(side='left', padx=(0, 5))
        
        # 绑定搜索框键盘事件
        self.search_var.trace_add("write", lambda name, index, mode: self.delayed_search())
        
        # 搜索延迟计时器ID
        self.search_delay_timer = None
        
        # 获取所有物品
        self.all_items_original = self.get_all_items()
        if not self.all_items_original:
            self.all_items_original = ["--请先添加物品--"]
        
        # 创建StringVar变量并设置默认值
        self.selected_item = tk.StringVar(value=self.all_items_original[0] if self.all_items_original else "")
        
        # 创建下拉框
        self.item_dropdown = ttk.Combobox(
            item_frame, 
            textvariable=self.selected_item,
            values=self.all_items_original,
            state="readonly",
            width=15
        )
        self.item_dropdown.pack(side='left', padx=5)
        
        # 绑定选择事件
        self.item_dropdown.bind("<<ComboboxSelected>>", 
                          lambda e: self.update_price_chart(chart_frame, self.selected_item.get(), period_var.get()) if self.selected_item.get() and self.selected_item.get() != "--请先添加物品--" else None)
        
        # 周期切换按钮组
        period_var = tk.StringVar(value='day')
        self.period_var = period_var  # 保存引用以便在其他方法中使用
        period_map = {'day': '日', 'week': '周', 'month': '月'}
        
        period_frame = Frame(chart_top_frame, bootstyle="light")
        period_frame.pack(side='right')
        
        Label(period_frame, text="周期:", font=(chinese_font, 9)).pack(side='left')
        
        for period, label in period_map.items():
            def make_command(p=period):
                return lambda: self.update_price_chart(chart_frame, self.selected_item.get(), p)
                
            btn = Button(period_frame, text=label, bootstyle="outline-secondary",
                        width=3, command=make_command())
            btn.pack(side='left', padx=2)
        
        # 图表区域
        chart_frame = Frame(chart_container, bootstyle="light")
        chart_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 初始绘制图表 - 如果有物品则绘制第一个物品的价格图
        if self.all_items_original and self.all_items_original[0] != "--请先添加物品--":
            self.draw_price_trend_chart(chart_frame, self.all_items_original[0], 'day')
        else:
            # 显示提示信息
            Label(chart_frame, text="请先添加物品数据", font=(chinese_font, 12)).pack(pady=50)

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

        # 创建左侧容器框架来容纳库存详情
        left_container = Frame(bottom_frame)
        left_container.pack(side='left', fill='both', expand=False, padx=(0, 10), pady=10)
        # 设置固定宽度，避免被挤压
        left_container.config(width=400)
        
        # 数据表
        table_frame = LabelFrame(left_container, text="库存详情", bootstyle="primary", padding=10)
        table_frame.pack(fill='both', expand=True)
        
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

        # 创建右侧容器框架来容纳月度收入图表
        right_container = Frame(bottom_frame)
        right_container.pack(side='left', fill='both', expand=True, pady=10)

        # 柱状图
        chart_frame2 = LabelFrame(right_container, text="收入情况", bootstyle="primary")
        chart_frame2.pack(fill='both', expand=True)
        
        # 绘制柱状图
        plt.style.use('seaborn-v0_8-whitegrid')
        # 减小图表尺寸，给更紧凑的显示效果
        fig2, ax2 = plt.subplots(figsize=(5, 3), dpi=100)
        fig2.patch.set_facecolor('#f9f9f9')
        ax2.set_facecolor('#f9f9f9')
        
        # 获取周收入数据
        weekly_data = self.get_weekly_income()
        weeks = [date for date, _ in weekly_data]
        income_values = [income for _, income in weekly_data]
        
        # 获取合适的中文字体
        chinese_font = self.get_suitable_chinese_font()
        
        # 确保柱状图使用正确的中文字体
        plt.rcParams['font.family'] = ['sans-serif']
        plt.rcParams['font.sans-serif'] = [chinese_font, 'SimHei', 'Microsoft YaHei', 'STHeiti', 'WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 使用渐变色，当前周为红色高亮(而非上周)
        current_week_idx = len(weeks) - 2  # 倒数第二个是当前周(不是最后一个)
        colors = ['#3498db' if i != current_week_idx else '#e74c3c' for i in range(len(weeks))]
        
        bars = ax2.bar(weeks, income_values, color=colors, width=0.6, edgecolor='white', linewidth=1)
        
        # 高亮当前周
        if 0 <= current_week_idx < len(weeks):
            # 将"当前周"文字放在稍低的位置（与数值交换）
            ax2.text(current_week_idx, income_values[current_week_idx] + (max(income_values) * 0.05), "当前周", 
                    ha='center', va='bottom', color='#e74c3c', fontweight='bold', 
                    fontfamily=chinese_font, fontsize=9)
        
        # 美化图表 - 显式指定中文字体
        ax2.set_ylabel("金额", fontsize=10, color='#7f8c8d', fontfamily=chinese_font)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color('#bdc3c7')
        ax2.spines['bottom'].set_color('#bdc3c7')
        
        # 设置x轴刻度标签，显式指定字体和旋转角度
        ax2.set_xticks(range(len(weeks)))
        ax2.set_xticklabels(weeks, fontsize=8, color='#7f8c8d', rotation=45, fontfamily=chinese_font)
        
        # 设置y轴刻度标签字体
        for label in ax2.get_yticklabels():
            label.set_fontfamily(chinese_font)
            label.set_fontsize(8)
            label.set_color('#7f8c8d')
        
        # 格式化y轴
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x/1000)}k"))
        
        # 添加网格线仅在y轴
        ax2.grid(True, axis='y', linestyle='--', alpha=0.3, color='#bdc3c7')
        
        # 为当前周的柱状添加数值标签
        if 0 <= current_week_idx < len(weeks) and income_values:
            current_value = income_values[current_week_idx]
            # 移除柱内部的数值显示
            # 在柱子上方较高位置添加数值标签（与"当前周"文字交换）
            ax2.text(
                current_week_idx, 
                current_value + (max(income_values) * 0.15), # 在柱子顶部上方添加较大间距
                f"¥{current_value:,.0f}",
                ha='center', 
                va='bottom', 
                fontsize=9,
                color='#e74c3c', 
                fontweight='bold', 
                fontfamily=chinese_font
            )
        
        # 增加图表顶部标题
        ax2.set_title("收入情况", fontsize=12, fontweight='bold', color='#2c3e50', 
                      fontfamily=chinese_font, loc='left', pad=10)
        
        # 增加图表边距以确保所有标签可见
        fig2.tight_layout(pad=2.5)
        
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
                # 汇总库存
                total_items, total_quantity, total_value, _ = inventory_stats
                
                # 格式化显示
                self.total_items_var.set(f"{total_items:,}")
                self.total_quantity_var.set(f"{int(total_quantity):,}")
                self.total_value_var.set(f"¥{total_value:,.2f}")
                
            # 更新统计卡片
            # 获取利润数据
            total_profit, profit_mom = self.get_total_profit_and_mom()
            total_value = self.get_total_inventory_value()
            inventory_mom = self.get_inventory_value_mom()
            
            # 更新物价趋势部分
            if hasattr(self, 'selected_item') and hasattr(self, 'period_var'):
                # 重新获取所有物品
                updated_all_items = self.get_all_items()
                
                if hasattr(self, 'all_items_original'):
                    # 保存当前搜索文本
                    current_search = ""
                    if hasattr(self, 'search_var'):
                        current_search = self.search_var.get().strip().lower()
                    
                    # 更新原始物品列表
                    self.all_items_original = updated_all_items if updated_all_items else ["--请先添加物品--"]
                    
                    # 重新应用当前的搜索过滤
                    if current_search and hasattr(self, 'apply_item_filter'):
                        self.apply_item_filter()
                    else:
                        # 直接更新下拉框值
                        if hasattr(self, 'item_dropdown'):
                            self.item_dropdown['values'] = self.all_items_original
                
                # 查找下拉框并更新其值
                for widget in self.winfo_children():
                    if isinstance(widget, Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, LabelFrame) and child.cget("text") == "物价趋势":
                                for top_frame in child.winfo_children():
                                    if isinstance(top_frame, Frame):
                                        for frame in top_frame.winfo_children():
                                            if isinstance(frame, Frame):
                                                for w in frame.winfo_children():
                                                    if isinstance(w, ttk.Combobox):
                                                        current_item = self.selected_item.get()
                                                        
                                                        # 更新下拉框选项 - 使用过滤后的值或原始值
                                                        if hasattr(self, 'item_dropdown') and w == self.item_dropdown:
                                                            # 已在上面更新，跳过
                                                            pass
                                                        elif updated_all_items:
                                                            w['values'] = updated_all_items
                                                        else:
                                                            w['values'] = ["--请先添加物品--"]
                                                        
                                                        # 如果当前选中的物品不在列表中，则选择第一个物品
                                                        dropdown_values = w['values']
                                                        if dropdown_values and current_item not in dropdown_values:
                                                            if dropdown_values[0] != "--无匹配物品--":
                                                                self.selected_item.set(dropdown_values[0])
                                                        
                                                        # 获取图表框架并更新图表
                                                        chart_frame = None
                                                        for cf in child.winfo_children():
                                                            if isinstance(cf, Frame) and cf != top_frame:
                                                                chart_frame = cf
                                                                break
                                                                
                                                        if chart_frame:
                                                            selected_item = self.selected_item.get()
                                                            if selected_item and selected_item not in ["--请先添加物品--", "--无匹配物品--"]:
                                                                period = self.period_var.get()
                                                                self.update_price_chart(chart_frame, selected_item, period)
                                                        break
            
            # 刷新库存详情表格
            # ... 其余部分保持不变
            
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

        # 检查是否在主线程中运行
        if threading.current_thread() != threading.main_thread():
            print("警告: refresh_price_data在非主线程中调用，将使用after方法确保UI更新在主线程中执行")
            # 在主线程中安全调用此方法
            if hasattr(self, 'main_gui') and hasattr(self.main_gui, 'root'):
                self.main_gui.root.after(0, self.refresh_price_data)
            else:
                self.after(0, self.refresh_price_data)
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
        if (not self.silver_price_cache and not self.nvwa_price_cache) or \
           (hasattr(self, 'silver_price_label') and self.silver_price_label.cget("text") == "加载中..."):
            # 从银两行情和女娲石行情标签页获取当前价格
            # 这个方法必须在主线程中调用，这里已经确保我们在主线程中
            self._legacy_price_fetch()

    def fetch_prices_in_thread(self):
        """在后台线程中获取价格数据"""
        def fetch_task():
            try:
                # 获取价格数据
                silver_price = self.fetch_silver_price()
                nvwa_price = self.fetch_nvwa_price()
                
                # 使用队列传递数据到主线程
                import queue
                data_queue = queue.Queue()
                data_queue.put((silver_price, nvwa_price))
                
                # 在主线程中检查队列并更新UI
                def check_queue():
                    try:
                        if not hasattr(self, 'main_gui') or not hasattr(self.main_gui, 'root'):
                            # 组件可能已被销毁
                            return
                            
                        if data_queue.empty():
                            # 如果队列为空，继续等待
                            self.main_gui.root.after(100, check_queue)
                            return
                            
                        silver_price, nvwa_price = data_queue.get()
                        # 在主线程中安全地更新UI
                        self.update_price_labels(silver_price, nvwa_price)
                    except Exception as e:
                        print(f"更新价格标签失败: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 在主窗口上下文中启动检查队列
                if hasattr(self, 'main_gui') and hasattr(self.main_gui, 'root'):
                    self.main_gui.root.after(100, check_queue)
                
            except Exception as e:
                print(f"获取价格数据失败: {e}")
                import traceback
                traceback.print_exc()
        
        threading.Thread(target=fetch_task, daemon=True).start()
    
    def update_price_labels(self, silver_price, nvwa_price):
        """更新价格标签"""
        chinese_font = self.get_suitable_chinese_font()
        
        if hasattr(self, 'silver_price_label'):
            if silver_price:
                self.silver_price_label.config(text=silver_price, font=(chinese_font, 11, "bold"))
            elif self.silver_price_cache:
                self.silver_price_label.config(text=self.silver_price_cache, font=(chinese_font, 11, "bold"))
        
        if hasattr(self, 'nvwa_price_label'):
            if nvwa_price:
                self.nvwa_price_label.config(text=nvwa_price, font=(chinese_font, 11, "bold"))
            elif self.nvwa_price_cache:
                self.nvwa_price_label.config(text=self.nvwa_price_cache, font=(chinese_font, 11, "bold"))

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
            
            # 不要在后台线程中尝试直接访问UI组件
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
        # 这个方法应该只在主线程中调用，不应该在后台线程中执行
        if threading.current_thread() != threading.main_thread():
            print("警告: _legacy_price_fetch在非主线程中调用，可能导致UI错误")
            return
        
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
        
        if hasattr(self, 'silver_price_label'):
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
        
        if hasattr(self, 'nvwa_price_label'):
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

    def get_all_items(self):
        """获取所有库存物品列表"""
        db_manager = getattr(self.main_gui, 'db_manager', None)
        if db_manager is None:
            return []
            
        # 从库存表获取所有物品名称，包括库存为0的物品
        query = "SELECT DISTINCT item_name FROM inventory ORDER BY item_name"
        results = db_manager.fetch_all(query)
        
        # 提取物品名称
        items = [item[0] for item in results]
        
        return items
        
    def get_item_price_history(self, item_name, period='day'):
        """获取特定物品的入库均价和出库单价历史"""
        db_manager = getattr(self.main_gui, 'db_manager', None)
        if db_manager is None:
            return [], []
        
        # 获取当前日期
        now = datetime.now()
        
        # 获取入库数据
        stock_in_query = """
            SELECT transaction_time, avg_cost 
            FROM stock_in 
            WHERE item_name = %s 
            ORDER BY transaction_time
        """
        stock_in_data = db_manager.fetch_all(stock_in_query, (item_name,))
        
        # 获取出库数据
        stock_out_query = """
            SELECT transaction_time, unit_price 
            FROM stock_out 
            WHERE item_name = %s 
            ORDER BY transaction_time
        """
        stock_out_data = db_manager.fetch_all(stock_out_query, (item_name,))
        
        # 处理入库数据，确保日期是datetime对象
        in_prices = []
        for dt, price in stock_in_data:
            try:
                # 确保dt是datetime对象
                if isinstance(dt, str):
                    try:
                        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt = datetime.strptime(dt, "%Y-%m-%d")
                # 添加到处理后的数据列表
                in_prices.append((dt, float(price)))
            except Exception as e:
                print(f"处理入库数据时出错: {e}")
                continue
        
        # 处理出库数据，确保日期是datetime对象
        out_prices = []
        for dt, price in stock_out_data:
            try:
                # 确保dt是datetime对象
                if isinstance(dt, str):
                    try:
                        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt = datetime.strptime(dt, "%Y-%m-%d")
                # 添加到处理后的数据列表
                out_prices.append((dt, float(price)))
            except Exception as e:
                print(f"处理出库数据时出错: {e}")
                continue
        
        return in_prices, out_prices

    def delayed_search(self):
        """延迟搜索，避免频繁更新"""
        # 取消之前的计时器
        if self.search_delay_timer:
            self.after_cancel(self.search_delay_timer)
        
        # 创建新的延迟计时器
        self.search_delay_timer = self.after(300, self.apply_item_filter)
    
    def clear_search(self):
        """清空搜索框并重置下拉框"""
        if hasattr(self, 'search_var'):
            # 如果当前是提示文本，则不更改
            current_text = self.search_var.get()
            if current_text != "搜索物品..." and current_text:
                self.search_var.set("")
                
                # 为所有可能的搜索框恢复提示文本
                for widget in self.winfo_children():
                    for child in widget.winfo_children():
                        if isinstance(child, Frame):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Entry) and hasattr(grandchild, 'get') and not grandchild.get():
                                    # 找到可能的搜索框，设置提示文本
                                    grandchild.insert(0, "搜索物品...")
                                    grandchild.config(bootstyle="secondary")
        
        # 重置下拉框为所有物品
        if hasattr(self, 'item_dropdown') and hasattr(self, 'all_items_original'):
            self.item_dropdown['values'] = self.all_items_original
        
    def apply_item_filter(self):
        """根据搜索框内容过滤下拉框中的物品"""
        search_text = self.search_var.get().strip().lower()
        
        # 如果是提示文本，则视为空
        if search_text == "搜索物品...":
            search_text = ""
        
        if not hasattr(self, 'all_items_original') or not self.all_items_original:
            return
            
        # 如果搜索文本为空，显示所有物品
        if not search_text:
            self.item_dropdown['values'] = self.all_items_original
            return
            
        # 过滤匹配的物品
        filtered_items = [item for item in self.all_items_original if search_text in item.lower()]
        
        # 如果没有匹配项，显示一个提示
        if not filtered_items:
            filtered_items = ["--无匹配物品--"]
            
        # 更新下拉框的值
        self.item_dropdown['values'] = filtered_items
        
        # 如果当前选中的物品不在过滤结果中，清空选择
        if self.selected_item.get() not in filtered_items and filtered_items != ["--无匹配物品--"]:
            self.selected_item.set("")

    def get_weekly_income(self):
        """
        获取基于周的收入数据，从上周三早上8点到本周三早上8点为一个周期
        返回最近12周的收入数据
        """
        from datetime import datetime, timedelta
        import calendar
        
        # 获取当前时间
        now = datetime.now()
        
        # 查找当前周的周三
        days_offset = (calendar.WEDNESDAY - now.weekday()) % 7
        if days_offset == 0 and now.hour < 8:  # 如果今天是周三但还不到早上8点
            days_offset = 7  # 使用上周三
            
        current_wednesday = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=days_offset)
        
        # 生成12个周三的日期，从当前周三向前
        wednesdays = []
        for i in range(12):
            wednesday = current_wednesday - timedelta(days=i*7)
            wednesdays.append(wednesday)
        
        # 按从早到晚排序
        wednesdays.sort()
        
        # 计算每个周三到下个周三的收入
        weekly_income = []
        
        for i in range(len(wednesdays)-1):
            start_time = wednesdays[i]
            end_time = wednesdays[i+1]
            
            # 获取日期范围内的出库数据
            query_out = """
                SELECT item_name, quantity, unit_price, fee, note 
                FROM stock_out 
                WHERE transaction_time BETWEEN %s AND %s
            """
            out_records = self.db_manager.fetch_all(query_out, (start_time, end_time))
            
            # 获取日期范围内的入库数据 - 用于查找成本
            query_in = """
                SELECT item_name, AVG(avg_cost) as avg_cost
                FROM stock_in 
                GROUP BY item_name
            """
            in_records = self.db_manager.fetch_all(query_in)
            
            # 构建入库均价字典
            in_prices = {}
            for record in in_records:
                item_name, avg_cost = record
                in_prices[item_name] = float(avg_cost) if avg_cost else 0
            
            # 计算总收入
            income = 0
            for record in out_records:
                item_name, quantity, unit_price, fee, note = record
                
                # 转换为适当的类型
                quantity = int(quantity) if quantity else 0
                unit_price = float(unit_price) if unit_price else 0
                fee = float(fee) if fee else 0
                
                # 查找入库均价（成本）
                in_price = in_prices.get(item_name, 0)
                
                # 计算此次交易的收入 = (出库单价 - 入库均价) * 数量 - 手续费
                transaction_income = (unit_price - in_price) * quantity - fee
                income += transaction_income
            
            # 格式化日期为简洁显示
            date_label = start_time.strftime("%m/%d")
            weekly_income.append((date_label, income))
        
        # 添加最后一周的数据（当前周）
        # 对于最后一周，结束时间是现在
        start_time = wednesdays[-1]
        end_time = now
        
        # 获取日期范围内的出库数据
        query_out = """
            SELECT item_name, quantity, unit_price, fee, note 
            FROM stock_out 
            WHERE transaction_time BETWEEN %s AND %s
        """
        out_records = self.db_manager.fetch_all(query_out, (start_time, end_time))
        
        # 获取入库均价数据
        query_in = """
            SELECT item_name, AVG(avg_cost) as avg_cost
            FROM stock_in 
            GROUP BY item_name
        """
        in_records = self.db_manager.fetch_all(query_in)
        
        # 构建入库均价字典
        in_prices = {}
        for record in in_records:
            item_name, avg_cost = record
            in_prices[item_name] = float(avg_cost) if avg_cost else 0
        
        # 计算最后一周的总收入
        income = 0
        for record in out_records:
            item_name, quantity, unit_price, fee, note = record
            
            # 转换为适当的类型
            quantity = int(quantity) if quantity else 0
            unit_price = float(unit_price) if unit_price else 0
            fee = float(fee) if fee else 0
            
            # 查找入库均价（成本）
            in_price = in_prices.get(item_name, 0)
            
            # 计算此次交易的收入 = (出库单价 - 入库均价) * 数量 - 手续费
            transaction_income = (unit_price - in_price) * quantity - fee
            income += transaction_income
        
        # 格式化当前周日期
        date_label = start_time.strftime("%m/%d")
        weekly_income.append((date_label, income))
        
        return weekly_income