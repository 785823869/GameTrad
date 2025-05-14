import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import requests
from datetime import datetime
import matplotlib
import matplotlib.dates

class NvwaPriceTab:
    def __init__(self, notebook):
        self.nvwa_tab = ttk.Frame(notebook)
        notebook.add(self.nvwa_tab, text="女娲石价格")
        self._max_points = 1000
        self._dragging = False
        self._drag_start = None
        self._orig_xlim = None
        self._orig_ylim = None
        self._mpl_cursor = None
        self._last_refresh_time = 0
        self._refresh_interval = 60
        self._auto_refresh_var = tk.BooleanVar(value=False)
        self._last_nvwa_data = None
        self._init_ui()
        self.refresh_nvwa_price()

    def _init_ui(self):
        control_frame = ttk.Frame(self.nvwa_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(control_frame, text="平台:").pack(side=tk.LEFT, padx=5)
        self.platform = ttk.Combobox(control_frame, values=["全部", "7881", "DD373"], state="readonly", width=10)
        self.platform.set("全部")
        self.platform.pack(side=tk.LEFT, padx=5)
        self.platform.bind("<<ComboboxSelected>>", lambda e: self.refresh_nvwa_price())
        ttk.Label(control_frame, text="天数:").pack(side=tk.LEFT, padx=5)
        self.days = ttk.Combobox(control_frame, values=["7", "15", "30", "90", "180", "365"], state="readonly", width=5)
        self.days.set("30")
        self.days.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="刷新", command=self.refresh_nvwa_price).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(control_frame, text="自动刷新", variable=self._auto_refresh_var, command=self.auto_refresh_nvwa_price).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="重置缩放", command=self.reset_nvwa_zoom).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出图表", command=self.export_nvwa_chart).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出数据", command=self.export_nvwa_data).pack(side=tk.LEFT, padx=5)
        # 信息展示区
        info_frame = tk.Frame(self.nvwa_tab, bg='#f8f8f8')
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
        self.nvwa_fig = Figure(figsize=(10, 6), dpi=100)
        self.nvwa_ax1 = self.nvwa_fig.add_subplot(111)
        self.nvwa_canvas = FigureCanvasTkAgg(self.nvwa_fig, master=self.nvwa_tab)
        self.nvwa_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.nvwa_canvas.mpl_connect('scroll_event', self._on_nvwa_scroll)
        self.nvwa_canvas.mpl_connect('button_press_event', self._on_nvwa_press)
        self.nvwa_canvas.mpl_connect('button_release_event', self._on_nvwa_release)
        self.nvwa_canvas.mpl_connect('motion_notify_event', self._on_nvwa_motion)

    def refresh_nvwa_price(self):
        threading.Thread(target=self._fetch_and_draw_nvwa_price, daemon=True).start()

    def _fetch_and_draw_nvwa_price(self):
        try:
            days = int(self.days.get())
            platform = self.platform.get()
            url = f"https://www.zxsjinfo.com/api/nvwa-price?days={days}&server=%E7%91%B6%E5%85%89%E6%B2%81%E9%9B%AA"
            resp = requests.get(url, timeout=20, verify=False)
            resp.raise_for_status()
            data = resp.json()
            self._last_nvwa_data = data
            self.nvwa_tab.after(0, lambda: self._draw_nvwa_price(data, platform, days))
        except Exception as e:
            print(f"Error fetching nvwa price data: {e}")
            messagebox.showerror("错误", f"获取女娲石价格数据失败: {e}")

    def _draw_nvwa_price(self, data, platform, days):
        try:
            self.nvwa_ax1.clear()
            self.nvwa_ax1.set_title(f"女娲石价格走势 ({days}天)")
            self.nvwa_ax1.set_xlabel("时间")
            self.nvwa_ax1.set_ylabel("价格 (元/颗)")
            self.nvwa_ax1.grid(True, linestyle='--', alpha=0.7)
            allowed_platforms = ["7881", "DD373"]
            filtered_series = {}
            filtered_dates = {}
            # 信息栏重置
            self.current_price_label.config(text="--", fg='#222')
            self.avg_price_label.config(text="--", fg='#222')
            self.amplitude_label.config(text="--", fg='#ff4444')
            for series, series_data in data.get('series', {}).items():
                if series not in allowed_platforms:
                    continue
                if platform != "全部" and str(series) != str(platform):
                    continue
                time_list = data.get('dates', {}).get(series, [])
                if time_list and isinstance(time_list[0], str):
                    try:
                        time_list = [datetime.strptime(t, "%Y-%m-%d") for t in time_list]
                    except Exception:
                        import pandas as pd
                        time_list = [pd.to_datetime(t) for t in time_list]
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
                if isinstance(time_list[0], str):
                    try:
                        time_list = [datetime.strptime(t, "%Y-%m-%d") for t in time_list]
                    except Exception:
                        import pandas as pd
                        time_list = [pd.to_datetime(t) for t in time_list]
                self.nvwa_ax1.plot(time_list, series_data,
                                  label=series,
                                  color=colors[idx % len(colors)],
                                  linewidth=1.5,
                                  alpha=0.8)
                if first_valid_series_data is None and series_data:
                    first_valid_series_data = (series, series_data)
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
            self.nvwa_ax1.legend(loc='upper left')
            import matplotlib.ticker as ticker
            self.nvwa_ax1.xaxis.set_major_locator(ticker.MaxNLocator(10))
            self.nvwa_ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m-%d'))
            self.nvwa_fig.autofmt_xdate()
            self.nvwa_canvas.draw_idle()
        except Exception as e:
            print(f"Error drawing nvwa price chart: {e}")

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
        import tkinter.filedialog as fd
        file_path = fd.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV文件', '*.csv')])
        if not file_path:
            return
        data = self._last_nvwa_data
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