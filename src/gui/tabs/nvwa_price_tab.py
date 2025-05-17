import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import matplotlib
import matplotlib.dates
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import platform
import re
import matplotlib.font_manager as fm
import requests
import time
import threading
import pandas as pd
import matplotlib.ticker as ticker

class NvwaPriceTab:
    def __init__(self, notebook, main_gui=None):
        self.notebook = notebook
        self.main_gui = main_gui
        
        # 检查是否在新UI结构中运行
        if isinstance(self.notebook, tb.Frame):
            # 新UI结构，notebook实际上是框架
            self.nvwa_tab = notebook
        else:
            # 旧UI结构，notebook是Notebook
            self.nvwa_tab = ttk.Frame(notebook, padding=10)
            self.notebook.add(self.nvwa_tab, text="女娲石行情")
        
        # 初始化变量
        self._last_nvwa_data = None
        self._dragging = False
        self._drag_start = None
        self._orig_xlim = None
        self._orig_ylim = None
        self._auto_refresh_var = tk.BooleanVar(value=False)
        self._max_points = 100  # 显示的最大点数
        self._mpl_cursor = None
        
        # 设置中文字体
        self.setup_fonts()
        
        # 初始化UI
        self._init_ui()
        
        # 自动刷新女娲石价格
        self.auto_refresh_nvwa_price()
        
    def setup_fonts(self):
        """设置中文字体支持"""
        # 检测操作系统
        system = platform.system()
        
        # 查找可用的中文字体
        font_found = False
        if system == 'Windows':
            chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi']
        elif system == 'Darwin':  # macOS
            chinese_fonts = ['PingFang SC', 'Heiti SC', 'STHeiti', 'STFangsong']
        else:  # Linux等其他系统
            chinese_fonts = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Droid Sans Fallback']
        
        for font_name in chinese_fonts:
            font_paths = fm.findSystemFonts(fontpaths=None)
            for path in font_paths:
                try:
                    if font_name.lower() in fm.FontProperties(fname=path).get_name().lower():
                        self.chinese_font = font_name
                        font_found = True
                        break
                except Exception as e:
                    pass
            if font_found:
                break
        
        # 使用备选方案
        if not font_found:
            try:
                plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
                plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
                self.chinese_font = 'SimHei'
            except:
                # 最后的备选方案
                self.chinese_font = 'Microsoft YaHei'

    def _init_ui(self):
        # 创建现代化的顶部控制栏
        control_frame = ttk.Frame(self.nvwa_tab, style="Card.TFrame")
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # 使用网格布局，更加整齐
        control_frame.columnconfigure(0, weight=0)
        control_frame.columnconfigure(1, weight=0)
        control_frame.columnconfigure(2, weight=0)
        control_frame.columnconfigure(3, weight=0)
        control_frame.columnconfigure(4, weight=0)
        control_frame.columnconfigure(5, weight=0)
        control_frame.columnconfigure(6, weight=1)  # 弹性空间
        
        # 平台选择
        ttk.Label(control_frame, text="平台:", font=(self.chinese_font, 10)).grid(row=0, column=0, padx=(5, 2), pady=5, sticky="e")
        self.platform = ttk.Combobox(control_frame, values=["全部", "7881", "DD373"], state="readonly", width=8, font=(self.chinese_font, 10))
        self.platform.set("全部")
        self.platform.grid(row=0, column=1, padx=2, pady=5, sticky="w")
        self.platform.bind("<<ComboboxSelected>>", lambda e: self.refresh_nvwa_price())
        
        # 天数选择
        ttk.Label(control_frame, text="天数:", font=(self.chinese_font, 10)).grid(row=0, column=2, padx=(10, 2), pady=5, sticky="e")
        self.days = ttk.Combobox(control_frame, values=["7", "15", "30", "90", "180", "365"], state="readonly", width=5, font=(self.chinese_font, 10))
        self.days.set("30")
        self.days.grid(row=0, column=3, padx=2, pady=5, sticky="w")
        
        # 控制按钮 - 使用更现代的按钮样式
        refresh_btn = ttk.Button(control_frame, text="刷新", command=self.refresh_nvwa_price, style="primary.TButton", width=6)
        refresh_btn.grid(row=0, column=4, padx=(10, 2), pady=5)
        
        auto_refresh_cb = ttk.Checkbutton(control_frame, text="自动刷新", variable=self._auto_refresh_var, 
                       command=self.auto_refresh_nvwa_price, style="primary.TCheckbutton")
        auto_refresh_cb.grid(row=0, column=5, padx=5, pady=5)
        
        # 右侧按钮组
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=0, column=7, padx=5, pady=5, sticky="e")
        
        ttk.Button(btn_frame, text="重置缩放", command=self.reset_nvwa_zoom, style="info.TButton", width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="导出图表", command=self.export_nvwa_chart, style="info.TButton", width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="导出数据", command=self.export_nvwa_data, style="info.TButton", width=8).pack(side=tk.LEFT, padx=2)
        
        # 信息展示区 - 移除背景色，使其透明
        info_frame = ttk.Frame(self.nvwa_tab)  # 移除style="Card.TFrame"
        info_frame.pack(fill='x', padx=10, pady=5)
        
        # 使用更现代的卡片设计，移除背景色
        def create_info_card(parent, title, value="--", highlight=False):
            card = ttk.Frame(parent, padding=10)  # 移除style="Card.TFrame"
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # 标题使用小号字体
            ttk.Label(card, text=title, font=(self.chinese_font, 11), 
                     foreground="#555555").pack(anchor="w")
            
            # 值使用大号粗体字
            value_label = ttk.Label(
                card, text=value, font=(self.chinese_font, 18, "bold"),
                foreground="#2c3e50" if not highlight else "#e74c3c"
            )
            value_label.pack(anchor="w", pady=(2, 0))
            
            return value_label
        
        self.current_price_label = create_info_card(info_frame, "当前价格")
        self.avg_price_label = create_info_card(info_frame, "7日均价")
        self.amplitude_label = create_info_card(info_frame, "振幅", highlight=True)
        
        # 创建图表 - 使用更现代的设计，与银两行情保持一致
        chart_frame = ttk.LabelFrame(self.nvwa_tab, text="价格走势图", style="Card.TLabelframe", padding=10)
        chart_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 创建图表，完全与银两行情相同的方式
        self.nvwa_fig = Figure(figsize=(10, 6), dpi=100, facecolor='#ffffff')
        self.nvwa_ax1 = self.nvwa_fig.add_subplot(111)
        self.nvwa_ax1.set_facecolor('#ffffff')
        
        # 设置图表样式
        self.nvwa_fig.subplots_adjust(left=0.08, right=0.92, top=0.9, bottom=0.15)
        
        self.nvwa_canvas = FigureCanvasTkAgg(self.nvwa_fig, chart_frame)
        self.nvwa_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 设置鼠标事件
        self.nvwa_canvas.mpl_connect('scroll_event', self._on_nvwa_scroll)
        self.nvwa_canvas.mpl_connect('button_press_event', self._on_nvwa_press)
        self.nvwa_canvas.mpl_connect('motion_notify_event', self._on_nvwa_motion)
        self.nvwa_canvas.mpl_connect('button_release_event', self._on_nvwa_release)
        
        # 刷新数据显示
        self.refresh_nvwa_price()

    def refresh_nvwa_price(self):
        """刷新女娲石价格"""
        self._fetch_and_draw_nvwa_price()
        
    def _fetch_and_draw_nvwa_price(self):
        """从服务器获取数据并绘制"""
        def fetch_data():
            try:
                days = int(self.days.get())
                platform = self.platform.get()
                
                url = f"https://www.zxsjinfo.com/api/nvwa-price?days={days}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data and 'series' in data:
                    self._last_nvwa_data = data
                    # 确保在主线程中更新UI
                    self.nvwa_tab.after(0, lambda: self._draw_nvwa_price(data, platform, days))
            except Exception as e:
                print(f"Error fetching nvwa price: {e}")
                # 如果失败，尝试使用上次的数据
                if self._last_nvwa_data:
                    self.nvwa_tab.after(0, lambda: self._draw_nvwa_price(self._last_nvwa_data, platform, days))
        
        thread = threading.Thread(target=fetch_data)
        thread.daemon = True
        thread.start()
    
    def _draw_nvwa_price(self, data, platform, days):
        """绘制女娲石价格走势图，优化视觉样式"""
        try:
            self.nvwa_ax1.clear()
            
            # 设置图表风格 - 纯白背景提高对比度
            self.nvwa_ax1.set_facecolor('#ffffff')
            self.nvwa_ax1.grid(True, linestyle='--', alpha=0.7, color='#cccccc')
            self.nvwa_ax1.set_title("女娲石价格走势", fontsize=14, fontweight='bold', fontproperties=self.chinese_font, color='#2c3e50')
            self.nvwa_ax1.set_xlabel("日期", fontsize=12, fontproperties=self.chinese_font, color='#2c3e50')
            self.nvwa_ax1.set_ylabel("价格 (元/个)", fontsize=12, fontproperties=self.chinese_font, color='#2c3e50')
            
            # 修改整个图表背景色
            self.nvwa_fig.patch.set_facecolor('#ffffff')
            
            # 过滤平台
            filtered_series = {}
            filtered_dates = {}
            
            for series, series_data in data['series'].items():
                # 过滤掉UU898平台
                if series == 'UU898' or (platform != '全部' and series != platform):
                    continue
                time_list = data['dates'].get(series, [])
                if not series_data or not time_list or len(series_data) != len(time_list):
                    continue
                
                # 限制点数，防止图表过于拥挤
                if len(series_data) > self._max_points:
                    step = max(1, len(series_data) // self._max_points)
                    series_data = series_data[::step]
                    time_list = time_list[::step]
                filtered_series[series] = series_data
                filtered_dates[series] = time_list
            
            # 使用更高对比度的颜色方案
            colors = ['#2980b9', '#c0392b']  # 深蓝和深红，更高对比度
            info_updated = False
            first_valid_series_data = None
            
            for idx, (series, series_data) in enumerate(filtered_series.items()):
                time_list = filtered_dates.get(series)
                if not time_list or len(series_data) != len(time_list):
                    continue
                if isinstance(time_list[0], str):
                    try:
                        time_list = [datetime.strptime(t, "%Y-%m-%d") for t in time_list]
                    except Exception:
                        time_list = [pd.to_datetime(t) for t in time_list]
                
                # 绘制更高对比度的线条，与银两行情完全相同的样式
                self.nvwa_ax1.plot(time_list, series_data,
                                  label=series,
                                  color=colors[idx % len(colors)],
                                  linewidth=2.5,  # 增加线宽
                                  marker='o',
                                  markersize=5,  # 增大标记点
                                  markerfacecolor='white',
                                  markeredgecolor=colors[idx % len(colors)],
                                  markeredgewidth=1.5,
                                  alpha=1.0)  # 提高不透明度
                
                # 更新信息面板
                if first_valid_series_data is None and series_data:
                    first_valid_series_data = (series, series_data)
                
                if not info_updated and (str(platform) == str(series) or (platform == '全部' and idx == 0)):
                    if series_data:
                        current_price = series_data[-1]
                        self.current_price_label.config(text=f"{current_price:.4f}")
                        last_7_days = series_data[-7:] if len(series_data) >= 7 else series_data
                        avg_7_days = sum(last_7_days) / len(last_7_days)
                        self.avg_price_label.config(text=f"{avg_7_days:.4f}")
                        max_price = max(series_data)
                        min_price = min(series_data)
                        amplitude = ((max_price - min_price) / min_price) * 100 if min_price else 0
                        self.amplitude_label.config(
                            text=f"{amplitude:.2f}%",
                            foreground='#c0392b' if amplitude > 5 else '#2980b9'  # 使用更高对比度的颜色
                        )
                        info_updated = True
            
            # 如果未更新信息面板但有有效数据，则使用第一个有效数据更新
            if not info_updated and first_valid_series_data:
                _, series_data = first_valid_series_data
                current_price = series_data[-1]
                self.current_price_label.config(text=f"{current_price:.4f}")
                last_7_days = series_data[-7:] if len(series_data) >= 7 else series_data
                avg_7_days = sum(last_7_days) / len(last_7_days)
                self.avg_price_label.config(text=f"{avg_7_days:.4f}")
                max_price = max(series_data)
                min_price = min(series_data)
                amplitude = ((max_price - min_price) / min_price) * 100 if min_price else 0
                self.amplitude_label.config(
                    text=f"{amplitude:.2f}%",
                    foreground='#c0392b' if amplitude > 5 else '#2980b9'  # 使用更高对比度的颜色
                )
            
            # 添加图例
            if filtered_series:
                # 设置图例样式 - 提高对比度
                legend = self.nvwa_ax1.legend(loc='upper left', frameon=True, fancybox=True, 
                                          framealpha=0.9, edgecolor='#2c3e50')
                for text in legend.get_texts():
                    text.set_fontproperties(self.chinese_font)
                    text.set_color('#2c3e50')  # 设置图例文字颜色
                
                # 设置x轴日期格式
                self.nvwa_ax1.xaxis.set_major_locator(ticker.MaxNLocator(10))
                self.nvwa_ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m-%d'))
                
                # 设置刻度标签字体和颜色 - 提高可读性
                for label in self.nvwa_ax1.get_xticklabels():
                    label.set_fontproperties(self.chinese_font)
                    label.set_fontsize(9)
                    label.set_color('#2c3e50')  # 深色文字
                    
                for label in self.nvwa_ax1.get_yticklabels():
                    label.set_fontproperties(self.chinese_font)
                    label.set_fontsize(9)
                    label.set_color('#2c3e50')  # 深色文字
                
                self.nvwa_fig.autofmt_xdate(rotation=30)
            
            # 调整布局
            self.nvwa_fig.tight_layout(pad=3.0)
            self.nvwa_canvas.draw()
            
        except Exception as e:
            print(f"绘制女娲石价格图表错误: {e}")
            import traceback
            traceback.print_exc()

    def _on_nvwa_scroll(self, event):
        if event.inaxes != self.nvwa_ax1:
            return
        cur_xlim = self.nvwa_ax1.get_xlim()
        cur_ylim = self.nvwa_ax1.get_ylim()
        xdata = event.xdata
        ydata = event.ydata
        base_scale = 1.1
        scale = base_scale if event.button == 'up' else 1/base_scale
        new_width = (cur_xlim[1] - cur_xlim[0]) / scale
        new_height = (cur_ylim[1] - cur_ylim[0]) / scale
        self.nvwa_ax1.set_xlim([xdata - new_width*(xdata-cur_xlim[0])/(cur_xlim[1]-cur_xlim[0]),
                               xdata + new_width*(cur_xlim[1]-xdata)/(cur_xlim[1]-cur_xlim[0])])
        self.nvwa_ax1.set_ylim([ydata - new_height*(ydata-cur_ylim[0])/(cur_ylim[1]-cur_ylim[0]),
                               ydata + new_height*(cur_ylim[1]-ydata)/(cur_ylim[1]-cur_ylim[0])])
        self.nvwa_canvas.draw_idle()

    def _on_nvwa_press(self, event):
        if event.inaxes != self.nvwa_ax1:
            return
        self._dragging = True
        self._drag_start = (event.xdata, event.ydata)
        self._orig_xlim = self.nvwa_ax1.get_xlim()
        self._orig_ylim = self.nvwa_ax1.get_ylim()
        if self._mpl_cursor:
            self._mpl_cursor.enabled = False

    def _on_nvwa_motion(self, event):
        if not self._dragging or event.inaxes != self.nvwa_ax1:
            return
        if event.xdata is None or event.ydata is None:
            return
        dx = event.xdata - self._drag_start[0]
        dy = event.ydata - self._drag_start[1]
        self.nvwa_ax1.set_xlim(self._orig_xlim[0] - dx, self._orig_xlim[1] - dx)
        self.nvwa_ax1.set_ylim(self._orig_ylim[0] - dy, self._orig_ylim[1] - dy)
        self.nvwa_canvas.draw_idle()

    def _on_nvwa_release(self, event):
        self._dragging = False
        if self._mpl_cursor:
            self._mpl_cursor.enabled = True

    def reset_nvwa_zoom(self):
        self.nvwa_ax1.autoscale()
        self.nvwa_canvas.draw_idle()

    def auto_refresh_nvwa_price(self):
        if self._auto_refresh_var.get():
            self.refresh_nvwa_price()
            self.nvwa_tab.after(60000, self.auto_refresh_nvwa_price)

    def export_nvwa_chart(self):
        import tkinter.filedialog as fd
        file_path = fd.asksaveasfilename(defaultextension='.png', filetypes=[('PNG图片', '*.png')])
        if file_path:
            self.nvwa_fig.savefig(file_path, dpi=200)
            messagebox.showinfo("成功", f"图表已导出到 {file_path}")

    def export_nvwa_data(self):
        """导出价格数据到CSV文件"""
        import tkinter.filedialog as fd
        file_path = fd.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV文件', '*.csv')])
        if not file_path:
            return
        
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                writer.writerow(['日期', '7881价格', 'DD373价格'])
                
                # 获取数据
                data = self._last_nvwa_data
                if not data:
                    messagebox.showerror("错误", "没有数据可导出")
                    return
                
                dates_7881 = data.get('dates', {}).get('7881', [])
                dates_dd373 = data.get('dates', {}).get('DD373', [])
                prices_7881 = data.get('series', {}).get('7881', [])
                prices_dd373 = data.get('series', {}).get('DD373', [])
                
                # 创建日期到价格的映射
                price_map_7881 = dict(zip(dates_7881, prices_7881))
                price_map_dd373 = dict(zip(dates_dd373, prices_dd373))
                
                # 合并所有日期
                all_dates = sorted(set(dates_7881 + dates_dd373))
                
                # 写入数据
                for date in all_dates:
                    row = [
                        date,
                        f"{price_map_7881.get(date, ''):.4f}" if date in price_map_7881 else '',
                        f"{price_map_dd373.get(date, ''):.4f}" if date in price_map_dd373 else ''
                    ]
                    writer.writerow(row)
            
            messagebox.showinfo("成功", f"数据已导出到 {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出数据失败: {e}") 