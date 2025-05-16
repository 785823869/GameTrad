import tkinter as tk
from ttkbootstrap import Frame, Label, LabelFrame, Entry, Button
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random
from datetime import datetime, timedelta

class DashboardTab(Frame):
    def __init__(self, master=None, main_gui=None, **kwargs):
        super().__init__(master, **kwargs)
        self.main_gui = main_gui
        self.create_widgets()

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
        fig, ax = plt.subplots(figsize=(5,3))
        # 美化风格
        ax.plot(x, y, color='black', linewidth=2, marker='o', markersize=7, zorder=3)
        if x and y:
            ax.scatter([x[-1]], [y[-1]], s=200, color='black', zorder=4, alpha=0.12, edgecolors='none')
            ax.scatter([x[-1]], [y[-1]], s=60, color='black', zorder=5)
        ax.set_title("出库金额趋势", loc='left', fontsize=13, fontweight='bold')
        ax.set_xlabel("")
        ax.set_ylabel("金额 ($)", fontsize=11)
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, zorder=0)
        # y轴金额格式化
        import matplotlib.ticker as mticker
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
        # x轴美化
        if period == 'day':
            ax.set_xticks(x[::max(1, len(x)//7)])
        ax.tick_params(axis='x', labelsize=9)
        ax.tick_params(axis='y', labelsize=9)
        fig.tight_layout(pad=2)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

    def create_widgets(self):
        # 顶部Tab和搜索
        top_frame = Frame(self)
        top_frame.pack(fill='x', pady=10)
        Button(top_frame, text="Tab1").pack(side='left', padx=5)
        Button(top_frame, text="Tab2").pack(side='left', padx=5)
        Button(top_frame, text="Tab3").pack(side='left', padx=5)
        Entry(top_frame, width=20).pack(side='right', padx=5)

        # 统计卡片
        stats_frame = Frame(self)
        stats_frame.pack(fill='x', pady=10)
        total_profit, month_on_month = self.get_total_profit_and_mom()
        for idx, (title, value, desc) in enumerate([
            ("总收入", f"${total_profit:,.2f}", f"{month_on_month:+.2f}% 月环比"),
            ("用户数", "2,405", "+33% 月环比"),
            ("活跃数", "10,353", "-8% 月环比"),
        ]):
            card = LabelFrame(stats_frame, text=title, padding=10)
            card.pack(side='left', expand=True, fill='both', padx=5)
            Label(card, text=value, font=("微软雅黑", 20, "bold")).pack()
            Label(card, text=desc, font=("微软雅黑", 10)).pack()

        # 主体区域
        main_frame = Frame(self)
        main_frame.pack(fill='both', expand=True)

        # 折线图区域（带周期切换）
        chart_frame = Frame(main_frame)
        chart_frame.pack(side='left', padx=10, pady=10, fill='both', expand=True)
        # 周期切换下拉框
        period_var = tk.StringVar(value='day')
        period_map = {'day': '日', 'week': '周', 'month': '月'}
        def on_period_change(*args):
            self.draw_trend_chart(chart_frame, period=period_var.get())
        period_menu = ttk.Combobox(chart_frame, textvariable=period_var, values=[('day'), ('week'), ('month')], width=6, state='readonly')
        period_menu.pack(anchor='ne', pady=(0, 2))
        period_menu.bind('<<ComboboxSelected>>', on_period_change)
        # 初始绘制
        self.draw_trend_chart(chart_frame, period='day')

        # 用户列表
        user_frame = LabelFrame(main_frame, text="用户列表", padding=10)
        user_frame.pack(side='left', padx=10, pady=10, fill='y')
        for name, email in [
            ("Helena", "email@figmasfakedomain.net"),
            ("Oscar", "email@figmasfakedomain.net"),
            ("Daniel", "email@figmasfakedomain.net"),
            ("Daniel Jay Park", "email@figmasfakedomain.net"),
            ("Mark Rojas", "email@figmasfakedomain.net"),
        ]:
            Label(user_frame, text=f"{name}\n{email}", anchor='w', justify='left').pack(anchor='w', pady=2)

        # 下方区域
        bottom_frame = Frame(self)
        bottom_frame.pack(fill='both', expand=True)

        # 数据表
        table_frame = LabelFrame(bottom_frame, text="来源统计", padding=10)
        table_frame.pack(side='left', padx=10, pady=10, fill='y')
        tree = ttk.Treeview(table_frame, columns=("source", "sessions", "change"), show='headings', height=8)
        tree.heading("source", text="来源")
        tree.heading("sessions", text="会话数")
        tree.heading("change", text="变化")
        tree.pack()
        for row in [
            ("website.net", 4321, "+84%"),
            ("website.net", 4033, "-8%"),
            ("website.net", 3128, "+2%"),
            ("website.net", 2104, "+33%"),
            ("website.net", 2003, "+30%"),
            ("website.net", 1894, "+15%"),
            ("website.net", 405, "-12%"),
        ]:
            tree.insert('', 'end', values=row)

        # 柱状图
        fig2, ax2 = plt.subplots(figsize=(3,2))
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [random.randint(30000, 80000) for _ in months]
        ax2.bar(months, values, color='black')
        ax2.set_title("月度数据")
        ax2.set_ylabel("金额")
        canvas2 = FigureCanvasTkAgg(fig2, master=bottom_frame)
        canvas2.get_tk_widget().pack(side='left', padx=10, pady=10)
        plt.close(fig2) 