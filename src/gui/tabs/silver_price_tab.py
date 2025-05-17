import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import requests
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates
import matplotlib.font_manager as fm
import numpy as np
import platform
import os
import time
import pandas as pd

class SilverPriceTab:
    def __init__(self, notebook, main_gui=None):
        # 检查是否在新UI结构中运行
        if isinstance(notebook, ttk.Frame) or isinstance(notebook, tk.Frame):
            # 新UI结构，notebook实际上是框架
            self.silver_tab = notebook
        else:
            # 旧UI结构，notebook是Notebook
            self.silver_tab = ttk.Frame(notebook)
            notebook.add(self.silver_tab, text="银两价格")
            
        self.main_gui = main_gui
        self._max_points = 1000
        self._dragging = False
        self._drag_start = None
        self._orig_xlim = None
        self._orig_ylim = None
        self._mpl_cursor = None
        self._last_refresh_time = 0
        self._refresh_interval = 60
        self._auto_refresh_var = tk.BooleanVar(value=False)
        self._last_silver_data = None
        
        # 设置中文字体
        self.setup_fonts()
        
        self._init_ui()
        self.refresh_silver_price()
        
    def setup_fonts(self):
        """设置中文字体支持"""
        # 检测操作系统
        system = platform.system()
        
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
                font_path = fm.findfont(fm.FontProperties(family=font_name))
                if os.path.basename(font_path).lower() != 'dejavusans.ttf':  # 不是默认字体
                    plt.rcParams['font.family'] = [font_name, 'sans-serif']
                    plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
                    self.chinese_font = font_name
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
            except:
                # 最后的备选方案
                self.chinese_font = 'Microsoft YaHei'
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 用来正常显示中文标签
                plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

    def _init_ui(self):
        # 创建现代化的顶部控制栏
        control_frame = ttk.Frame(self.silver_tab, style="Card.TFrame")
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
        self.platform.bind("<<ComboboxSelected>>", lambda e: self.refresh_silver_price())

        # 天数选择
        ttk.Label(control_frame, text="天数:", font=(self.chinese_font, 10)).grid(row=0, column=2, padx=(10, 2), pady=5, sticky="e")
        self.days = ttk.Combobox(control_frame, values=["7", "15", "30", "90", "180", "365"], state="readonly", width=5, font=(self.chinese_font, 10))
        self.days.set("30")
        self.days.grid(row=0, column=3, padx=2, pady=5, sticky="w")

        # 控制按钮 - 使用更现代的按钮样式
        refresh_btn = ttk.Button(control_frame, text="刷新", command=self.refresh_silver_price, style="primary.TButton", width=6)
        refresh_btn.grid(row=0, column=4, padx=(10, 2), pady=5)
        
        auto_refresh_cb = ttk.Checkbutton(control_frame, text="自动刷新", variable=self._auto_refresh_var, 
                       command=self.auto_refresh_silver_price, style="primary.TCheckbutton")
        auto_refresh_cb.grid(row=0, column=5, padx=5, pady=5)
        
        # 右侧按钮组
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=0, column=7, padx=5, pady=5, sticky="e")
        
        ttk.Button(btn_frame, text="重置缩放", command=self.reset_silver_zoom, style="info.TButton", width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="导出图表", command=self.export_silver_chart, style="info.TButton", width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="导出数据", command=self.export_silver_data, style="info.TButton", width=8).pack(side=tk.LEFT, padx=2)

        # 信息展示区 - 移除背景色，使其透明
        info_frame = ttk.Frame(self.silver_tab)  # 移除style="Card.TFrame"
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

        # 创建图表 - 使用更现代的设计
        chart_frame = ttk.LabelFrame(self.silver_tab, text="价格走势图", style="Card.TLabelframe", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.silver_fig = Figure(figsize=(10, 6), dpi=100, facecolor='#f8f9fa')
        self.silver_ax1 = self.silver_fig.add_subplot(111)
        self.silver_ax1.set_facecolor('#f8f9fa')
        
        # 设置图表样式
        self.silver_fig.subplots_adjust(left=0.08, right=0.92, top=0.9, bottom=0.15)
        
        self.silver_canvas = FigureCanvasTkAgg(self.silver_fig, master=chart_frame)
        self.silver_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 绑定事件
        self.silver_canvas.mpl_connect('scroll_event', self._on_silver_scroll)
        self.silver_canvas.mpl_connect('button_press_event', self._on_silver_press)
        self.silver_canvas.mpl_connect('button_release_event', self._on_silver_release)
        self.silver_canvas.mpl_connect('motion_notify_event', self._on_silver_motion)

    def refresh_silver_price(self):
        threading.Thread(target=self._fetch_and_draw_silver_price, daemon=True).start()

    def _fetch_and_draw_silver_price(self):
        try:
            days = int(self.days.get())
            platform = self.platform.get()
            data = self.fetch_silver_price_multi_series(days)
            self._last_silver_data = data
            self.silver_tab.after(0, lambda: self._draw_silver_price(data, platform, days))
        except Exception as e:
            print(f"Error fetching silver price data: {e}")

    def _draw_silver_price(self, data, platform, days):
        """绘制银两价格走势图"""
        try:
            self.silver_ax1.clear()
            
            # 设置图表风格 - 纯白背景提高对比度
            self.silver_ax1.set_facecolor('#ffffff')
            self.silver_ax1.grid(True, linestyle='--', alpha=0.7, color='#cccccc')
            self.silver_ax1.set_title("银两价格走势", fontsize=14, fontweight='bold', fontproperties=self.chinese_font, color='#2c3e50')
            self.silver_ax1.set_xlabel("日期", fontsize=12, fontproperties=self.chinese_font, color='#2c3e50')
            self.silver_ax1.set_ylabel("价格 (元/万两)", fontsize=12, fontproperties=self.chinese_font, color='#2c3e50')
            
            # 修改整个图表背景色
            self.silver_fig.patch.set_facecolor('#ffffff')
            
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
                
                # 绘制更高对比度的线条
                self.silver_ax1.plot(time_list, series_data,
                                  label=series,
                                  color=colors[idx % len(colors)],
                                  linewidth=2.5,  # 增加线宽
                                  marker='o',
                                  markersize=5,  # 增大标记点
                                  markerfacecolor='white',
                                  markeredgecolor=colors[idx % len(colors)],
                                  markeredgewidth=1.5,
                                  alpha=1.0)  # 提高不透明度
                
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
            
            # 设置图例样式 - 提高对比度
            legend = self.silver_ax1.legend(loc='upper left', frameon=True, fancybox=True, 
                                        framealpha=0.9, edgecolor='#2c3e50')
            for text in legend.get_texts():
                text.set_fontproperties(self.chinese_font)
                text.set_color('#2c3e50')  # 设置图例文字颜色
            
            # 设置x轴日期格式
            import matplotlib.ticker as ticker
            self.silver_ax1.xaxis.set_major_locator(ticker.MaxNLocator(10))
            self.silver_ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m-%d'))
            
            # 设置刻度标签字体和颜色 - 提高可读性
            for label in self.silver_ax1.get_xticklabels():
                label.set_fontproperties(self.chinese_font)
                label.set_fontsize(9)
                label.set_color('#2c3e50')  # 深色文字
                
            for label in self.silver_ax1.get_yticklabels():
                label.set_fontproperties(self.chinese_font)
                label.set_fontsize(9)
                label.set_color('#2c3e50')  # 深色文字
            
            self.silver_fig.autofmt_xdate(rotation=30)
            self.silver_canvas.draw_idle()
        except Exception as e:
            print(f"Error drawing silver price chart: {e}")

    def fetch_silver_price_multi_series(self, days):
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                url = f"https://www.zxsjinfo.com/api/gold-price?days={days}&server=%E7%91%B6%E5%85%89%E6%B2%81%E9%9B%AA"
                resp = requests.get(url, timeout=20, verify=False)
                resp.raise_for_status()
                data = resp.json()
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

    def _on_silver_scroll(self, event):
        if event.inaxes != self.silver_ax1:
            return

        cur_xlim = self.silver_ax1.get_xlim()
        cur_ylim = self.silver_ax1.get_ylim()
        xdata = event.xdata
        ydata = event.ydata
        base_scale = 1.1
        scale = base_scale if event.button == 'up' else 1/base_scale
        new_width = (cur_xlim[1] - cur_xlim[0]) / scale
        new_height = (cur_ylim[1] - cur_ylim[0]) / scale

        self.silver_ax1.set_xlim([xdata - new_width*(xdata-cur_xlim[0])/(cur_xlim[1]-cur_xlim[0]),
                                 xdata + new_width*(cur_xlim[1]-xdata)/(cur_xlim[1]-cur_xlim[0])])
        self.silver_ax1.set_ylim([ydata - new_height*(ydata-cur_ylim[0])/(cur_ylim[1]-cur_ylim[0]),
                                 ydata + new_height*(cur_ylim[1]-ydata)/(cur_ylim[1]-cur_ylim[0])])
        self.silver_canvas.draw_idle()

    def _on_silver_press(self, event):
        if event.inaxes != self.silver_ax1:
            return
        self._dragging = True
        self._drag_start = (event.xdata, event.ydata)
        self._orig_xlim = self.silver_ax1.get_xlim()
        self._orig_ylim = self.silver_ax1.get_ylim()

    def _on_silver_motion(self, event):
        if not self._dragging or event.inaxes != self.silver_ax1:
            return
        if event.xdata is None or event.ydata is None:
            return

        dx = event.xdata - self._drag_start[0]
        dy = event.ydata - self._drag_start[1]
        self.silver_ax1.set_xlim(self._orig_xlim[0] - dx, self._orig_xlim[1] - dx)
        self.silver_ax1.set_ylim(self._orig_ylim[0] - dy, self._orig_ylim[1] - dy)
        self.silver_canvas.draw_idle()

    def _on_silver_release(self, event):
        self._dragging = False

    def reset_silver_zoom(self):
        self.silver_ax1.autoscale()
        self.silver_canvas.draw_idle()

    def auto_refresh_silver_price(self):
        if self._auto_refresh_var.get():
            self.refresh_silver_price()
            self.silver_tab.after(60000, self.auto_refresh_silver_price)

    def export_silver_chart(self):
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[('PNG图片', '*.png')]
        )
        if file_path:
            self.silver_fig.savefig(file_path, dpi=200)
            messagebox.showinfo("成功", f"图表已导出到 {file_path}")

    def export_silver_data(self):
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV文件', '*.csv')]
        )
        if not file_path:
            return

        data = self._last_silver_data
        if not data:
            messagebox.showerror("错误", "暂无可导出的数据")
            return

        all_keys = list(data['series'].keys())
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