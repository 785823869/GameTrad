import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, StringVar
import tkinter as tk
import json
import threading
import time
# 导入操作类型常量
from src.utils.operation_types import OperationType, TabName

class LogTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        
        # 初始化筛选变量
        self.log_search_var = tk.StringVar()
        self.log_jump_var = tk.StringVar()
        self.filter_tab = tk.StringVar(value="全部")
        self.filter_type = tk.StringVar(value="全部")
        self.filter_category = tk.StringVar(value="全部")  # 新增：操作类别筛选
        self.filter_reverted = tk.StringVar(value="全部")
        
        # 初始化分页变量
        self.log_page = 1
        self.log_page_size = 20  # 默认值，后续会动态调整
        self.log_total_pages = 1
        self.log_total_records = 0
        
        # 自适应记录数控制变量
        self.min_records_per_page = 8  # 每页最少显示的记录数
        self.row_height = 25  # 每行预估高度(像素)
        self.header_footer_height = 180  # 表头和底部控件的预估高度(像素)
        self.last_window_height = 0  # 记录上次窗口高度
        
        # 防抖动控制变量
        self.resize_timer_id = None  # 窗口大小调整的计时器ID
        self.debounce_delay = 300  # 防抖动延迟毫秒数
        
        # 加载状态控制
        self.is_loading = False
        self.status_var = tk.StringVar(value="就绪")
        
        self._init_ui()
        
    def _init_ui(self):
        # 检查是否在新UI结构中运行
        if isinstance(self.notebook, tk.Frame) or isinstance(self.notebook, tb.Frame):
            # 新UI结构，notebook实际上是框架
            log_frame = self.notebook
        else:
            # 旧UI结构，notebook是Notebook
            log_frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(log_frame, text="操作日志")
        
        self.log_frame = log_frame  # 保存引用以便后续使用
        
        # 顶部工具栏
        toolbar_frame = ttk.Frame(log_frame)
        toolbar_frame.pack(fill='x', pady=(0, 10))
        
        # 搜索区域
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side='left')
        
        ttk.Label(search_frame, text="关键词:").pack(side='left', padx=(0, 5))
        ttk.Entry(search_frame, textvariable=self.log_search_var, width=20).pack(side='left', padx=(0, 5))
        ttk.Button(search_frame, text="搜索", command=self._log_search, bootstyle="primary-outline").pack(side='left')
        
        # 操作按钮
        button_frame = ttk.Frame(toolbar_frame)
        button_frame.pack(side='right')
        
        # 添加撤销和恢复按钮
        ttk.Button(button_frame, text="撤销操作", 
                  command=self.undo_operation, 
                  bootstyle="warning-outline").pack(side='left', padx=5)
        ttk.Button(button_frame, text="恢复操作", 
                  command=self.redo_operation, 
                  bootstyle="success-outline").pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="删除选中", 
                  command=self.delete_log_items, 
                  bootstyle="danger-outline").pack(side='left', padx=5)
        ttk.Button(button_frame, text="导出CSV", 
                  command=self.export_log_csv, 
                  bootstyle="info-outline").pack(side='left', padx=5)
        
        # 筛选条件区域（新增）
        filter_frame = ttk.LabelFrame(log_frame, text="筛选条件", bootstyle="info")
        filter_frame.pack(fill='x', pady=(0, 10), padx=5)
        
        # 使用网格布局来整齐排列筛选条件
        ttk.Label(filter_frame, text="标签页:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        tab_combo = ttk.Combobox(filter_frame, textvariable=self.filter_tab, 
                              values=["全部"] + TabName.get_all_tabs(),
                              width=10, state="readonly")
        tab_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        tab_combo.bind("<<ComboboxSelected>>", lambda e: self._log_search())
        
        ttk.Label(filter_frame, text="操作类型:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        type_combo = ttk.Combobox(filter_frame, textvariable=self.filter_type, 
                               values=["全部"] + OperationType.get_all_types(),
                               width=10, state="readonly")
        type_combo.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        type_combo.bind("<<ComboboxSelected>>", lambda e: self._log_search())
        
        ttk.Label(filter_frame, text="操作类别:").grid(row=0, column=4, padx=5, pady=5, sticky='e')
        categories = ["全部", "添加类", "修改类", "删除类", "查询类", "系统类", "其他类"]
        category_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category, 
                                values=categories,
                                width=10, state="readonly")
        category_combo.grid(row=0, column=5, padx=5, pady=5, sticky='w')
        category_combo.bind("<<ComboboxSelected>>", lambda e: self._log_search())
        
        ttk.Label(filter_frame, text="已回退:").grid(row=0, column=6, padx=5, pady=5, sticky='e')
        reverted_combo = ttk.Combobox(filter_frame, textvariable=self.filter_reverted, 
                                  values=["全部", "是", "否"],
                                  width=6, state="readonly")
        reverted_combo.grid(row=0, column=7, padx=5, pady=5, sticky='w')
        reverted_combo.bind("<<ComboboxSelected>>", lambda e: self._log_search())
        
        # 重置按钮
        ttk.Button(filter_frame, text="重置筛选", 
                 command=self.reset_filters,
                 bootstyle="secondary-outline").grid(row=0, column=8, padx=10, pady=5)
        
        # 状态栏和加载指示器
        status_frame = ttk.Frame(log_frame)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # 加载进度条
        self.progress_bar = ttk.Progressbar(
            status_frame, 
            mode='indeterminate', 
            bootstyle="success-striped",
            length=200
        )
        self.progress_bar.pack(side='left', padx=(0, 10))
        
        # 状态文本
        ttk.Label(status_frame, textvariable=self.status_var).pack(side='left')
        
        # 日志表
        columns = ("操作类型", "标签页", "操作时间", "数据")
        # 动态计算初始高度，但至少保持一个最小值
        initial_height = max(18, self.calculate_treeview_height())
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show='headings', height=initial_height)
        for col in columns:
            self.log_tree.heading(col, text=col, anchor='center')
            # 设置列宽
            if col == "数据":
                self.log_tree.column(col, width=400, anchor='w')
            else:
                self.log_tree.column(col, width=120, anchor='center')
        
        # 创建垂直滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        
        # 分页控件
        pagination_frame = ttk.Frame(log_frame)
        pagination_frame.pack(side='bottom', fill='x', pady=10)
        
        ttk.Button(pagination_frame, text="上一页", 
                  command=self.log_prev_page, 
                  bootstyle="secondary-outline").pack(side='left', padx=5)
        
        ttk.Label(pagination_frame, text="跳转到:").pack(side='left', padx=5)
        ttk.Entry(pagination_frame, textvariable=self.log_jump_var, width=5).pack(side='left')
        ttk.Button(pagination_frame, text="GO", command=self.log_jump_page, bootstyle="secondary").pack(side='left', padx=5)
        
        self.log_page_info = ttk.Label(pagination_frame, text="页码: 1 / 1  总记录: 0")
        self.log_page_info.pack(side='left', padx=15)
        
        ttk.Button(pagination_frame, text="下一页", 
                  command=self.log_next_page, 
                  bootstyle="secondary-outline").pack(side='left', padx=5)
        
        # 打包表格和滚动条
        self.log_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 设置交替行背景色
        self.log_tree.tag_configure('evenrow', background='#f9f9f9')
        self.log_tree.tag_configure('oddrow', background='#ffffff')
        
        # 设置不同类型操作的颜色
        self.log_tree.tag_configure('add', foreground='#2980b9')  # 深蓝色
        self.log_tree.tag_configure('delete', foreground='#c0392b')  # 深红色
        self.log_tree.tag_configure('modify', foreground='#27ae60')  # 深绿色
        self.log_tree.tag_configure('query', foreground='#8e44ad')   # 紫色
        self.log_tree.tag_configure('system', foreground='#d35400')  # 橙色
        self.log_tree.tag_configure('other', foreground='#7f8c8d')   # 灰色
        self.log_tree.tag_configure('reverted', foreground='#95a5a6', background='#f5f5f5')  # 灰色带浅灰背景
        
        # 初始隐藏进度条
        self.progress_bar.pack_forget()
        
        # 绑定双击事件
        self.log_tree.bind("<Double-1>", self.show_log_detail)
        
        # 绑定Ctrl+A全选快捷键
        self.log_tree.bind('<Control-a>', self.select_all_logs)
        
        # 绑定窗口大小变化事件
        self.main_gui.root.bind("<Configure>", self.on_window_resize)
        
        # 记录当前窗口高度
        self.last_window_height = self.main_gui.root.winfo_height()
        
        # 加载日志数据
        self.refresh_log_tab()
    
    def calculate_treeview_height(self):
        """计算Treeview应该显示的行数"""
        try:
            # 获取窗口当前高度
            window_height = self.main_gui.root.winfo_height()
            
            # 如果窗口尚未完全初始化，使用默认值
            if window_height < 100:
                return 18
                
            # 计算可用高度并转换为行数
            available_height = window_height - self.header_footer_height
            rows = max(self.min_records_per_page, int(available_height / self.row_height))
            
            return rows
        except Exception as e:
            print(f"计算Treeview高度失败: {e}")
            return 18  # 默认值
    
    def calculate_page_size(self):
        """根据当前窗口大小和Treeview高度计算合适的页面大小"""
        try:
            # 获取Treeview可显示的行数
            visible_rows = self.calculate_treeview_height()
            
            # 更新log_tree的height属性
            self.log_tree.configure(height=visible_rows)
            
            # 页面大小等于可见行数
            self.log_page_size = visible_rows
            
            return visible_rows
        except Exception as e:
            print(f"计算页面大小失败: {e}")
            return 20  # 默认值
    
    def on_window_resize(self, event=None):
        """窗口大小变化时的处理函数，使用防抖动方式延迟处理"""
        # 仅当来自根窗口且窗口高度变化明显时才处理
        if (event and event.widget == self.main_gui.root and 
            abs(self.last_window_height - self.main_gui.root.winfo_height()) > 20):
            
            self.last_window_height = self.main_gui.root.winfo_height()
            
            # 取消之前的计时器（如果存在）
            if self.resize_timer_id:
                self.log_frame.after_cancel(self.resize_timer_id)
            
            # 设置新的计时器
            self.resize_timer_id = self.log_frame.after(
                self.debounce_delay, 
                self.delayed_resize_handler
            )
    
    def delayed_resize_handler(self):
        """延迟处理窗口大小变化的回调函数"""
        # 重置计时器ID
        self.resize_timer_id = None
        
        # 重新计算页面大小
        new_page_size = self.calculate_page_size()
        
        # 如果页面大小变化明显，则刷新表格
        if abs(new_page_size - self.log_page_size) >= 2:
            self.refresh_log_tab()
    
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
    
    def show_loading(self, is_loading=True, status="正在加载数据..."):
        """显示或隐藏加载指示器"""
        self.is_loading = is_loading
        if is_loading:
            self.status_var.set(status)
            self.progress_bar.pack(side='left', padx=(0, 10))
            self.progress_bar.start(10)  # 启动进度条动画
        else:
            self.progress_bar.stop()  # 停止进度条动画
            self.progress_bar.pack_forget()
            self.status_var.set("就绪")
    
    def refresh_log_tab(self):
        """刷新日志表格"""
        # 显示加载指示器
        self.show_loading(True)
        
        # 清空表格
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        # 启动后台线程加载数据
        threading.Thread(target=self._load_data_thread, daemon=True).start()
    
    def _load_data_thread(self):
        """在后台线程中加载数据"""
        try:
            # 动态计算页面大小
            page_size = self.calculate_page_size()
            
            # 获取过滤条件
            tab_name = self.filter_tab.get() if hasattr(self, 'filter_tab') else None
            if tab_name == "全部": tab_name = None
                
            op_type = self.filter_type.get() if hasattr(self, 'filter_type') else None
            if op_type == "全部": op_type = None
            
            # 处理操作类别筛选
            category = self.filter_category.get() if hasattr(self, 'filter_category') else None
            if category == "全部": category = None
                
            reverted = None
            if hasattr(self, 'filter_reverted'):
                if self.filter_reverted.get() == "是": reverted = True
                elif self.filter_reverted.get() == "否": reverted = False
                
            keyword = self.log_search_var.get() if self.log_search_var.get() else None
            
            # 单独获取总记录数
            total = self.db_manager.count_operation_logs(
                tab_name=tab_name,
                op_type=op_type,
                keyword=keyword,
                reverted=reverted
            )
            
            # 特殊情况处理：如果总记录数较少，自动调整页面大小以避免过多空白
            if total > 0 and total < page_size:
                # 如果总记录数小于计算出的页面大小，则使用总记录数作为页面大小
                adjusted_page_size = max(total, self.min_records_per_page)
                if adjusted_page_size != page_size:
                    page_size = adjusted_page_size
            
            # 查询数据
            logs = self.db_manager.get_operation_logs(
                tab_name=tab_name,
                op_type=op_type,
                keyword=keyword,
                reverted=reverted,
                page=self.log_page,
                page_size=page_size
            )
            
            # 如果有操作类别筛选，过滤结果
            if category:
                logs = [log for log in logs if log.get('操作类别') == category]
            
            # 记录当前使用的页面大小
            self.log_page_size = page_size
            
            # 更新分页信息
            self.log_total_records = total
            self.log_total_pages = max(1, (total + self.log_page_size - 1) // self.log_page_size)
            
            # 如果当前页码超出范围，重置为第一页
            if self.log_page > self.log_total_pages:
                self.log_page = 1
                # 重新查询第一页数据
                logs = self.db_manager.get_operation_logs(
                    tab_name=tab_name,
                    op_type=op_type,
                    keyword=keyword,
                    reverted=reverted,
                    page=self.log_page,
                    page_size=self.log_page_size
                )
            
            # 在UI线程中更新界面
            self.log_frame.after(0, lambda: self._update_ui(logs, total))
        except Exception as e:
            import traceback
            print(f"加载日志数据失败: {e}")
            traceback.print_exc()
            # 在UI线程中更新错误状态
            self.log_frame.after(0, lambda: self.show_loading(False, f"加载失败: {str(e)}"))
    
    def _update_ui(self, logs, total):
        """在主线程中更新UI元素"""
        try:
            # 更新Treeview高度
            self.log_tree.configure(height=self.log_page_size)
            
            # 更新页码显示
            if hasattr(self, 'log_page_info'):
                self.log_page_info.config(text=f"页码: {self.log_page} / {self.log_total_pages}  总记录: {total}  每页: {self.log_page_size}条")
            elif hasattr(self, 'log_page_label'):
                self.log_page_label.config(text=f"第{self.log_page}/{self.log_total_pages}页")
            
            # 插入数据
            for idx, log in enumerate(logs):
                # 使用交替行颜色
                row_tags = ('evenrow',) if idx % 2 == 0 else ('oddrow',)
                
                # 根据操作类别添加颜色标签
                category = log.get('操作类别', '')
                if category == "添加类":
                    op_tag = 'add'
                elif category == "删除类":
                    op_tag = 'delete'
                elif category == "修改类":
                    op_tag = 'modify'
                elif category == "查询类":
                    op_tag = 'query'
                elif category == "系统类":
                    op_tag = 'system'
                else:
                    op_tag = 'other'
                
                # 如果已回退，使用灰色
                if log.get('已回退'):
                    op_tag = 'reverted'
                    
                # 组合标签
                if op_tag:
                    row_tags = row_tags + (op_tag,)
                
                # 转换数据为字符串，简化显示
                data_text = str(log['数据'])
                if len(data_text) > 100:
                    data_text = data_text[:100] + "..."
                
                self.log_tree.insert('', 'end', values=(
                    log['操作类型'] + ("（已回退）" if log.get('已回退') else ""),
                    log['标签页'],
                    log['操作时间'],
                    data_text
                ), tags=row_tags)
                
            # 隐藏加载指示器
            self.show_loading(False)
            
        except Exception as e:
            import traceback
            print(f"更新日志UI失败: {e}")
            traceback.print_exc()
            # 显示错误状态
            self.show_loading(False, f"更新失败: {str(e)}")

    def export_log_csv(self):
        import pandas as pd
        import os
        from tkinter import filedialog
        try:
            logs = self.db_manager.get_operation_logs(
                tab_name=None,
                op_type=None,
                keyword=None,
                reverted=None,
                page=1,
                page_size=10000
            )
            columns = ["操作类型", "标签页", "操作时间", "数据"]
            data = [[log['操作类型'], log['标签页'], log['操作时间'], json.dumps(log['数据'], ensure_ascii=False)] for log in logs]
            file_path = filedialog.asksaveasfilename(
                filetypes=[('Excel文件', '*.xlsx'), ('CSV文件', '*.csv')],
                title='导出日志'
            )
            if not file_path:
                return
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.xlsx':
                pd.DataFrame(data, columns=columns).to_excel(file_path, index=False)
                messagebox.showinfo('成功', f'日志已导出到 {file_path}')
            elif ext == '.csv':
                pd.DataFrame(data, columns=columns).to_csv(file_path, index=False, encoding='utf-8-sig')
                messagebox.showinfo('成功', f'日志已导出为csv文件 {file_path}')
            else:
                messagebox.showerror('错误', '不支持的文件格式')
        except Exception as e:
            messagebox.showerror('错误', f'导出日志失败: {str(e)}')

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
        # 完全刷新日志界面，确保显示与数据库同步
        self.refresh_log_tab()
        
    def show_log_detail(self, event):
        item = self.log_tree.identify_row(event.y)
        if not item:
            return
        values = self.log_tree.item(item)['values']
        if not values or len(values) < 4:
            return
            
        op_type, tab_name, timestamp, _ = values  # 不使用Treeview中可能截断的数据
        
        # 从数据库中获取完整的日志记录
        try:
            # 移除可能的"（已回退）"后缀
            clean_op_type = op_type.replace("（已回退）", "").strip()
            
            # 使用数据库连接直接获取完整日志记录
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT operation_data FROM operation_logs WHERE operation_type=%s AND tab_name=%s AND operation_time=%s LIMIT 1",
                (clean_op_type, tab_name, timestamp)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result or not result[0]:
                messagebox.showwarning("提示", "未找到详细数据记录")
                return
                
            # 从数据库获取完整的JSON数据
            data_json = result[0]
        except Exception as e:
            messagebox.showerror("错误", f"获取日志详情失败: {str(e)}")
            return
            
        # 创建详情窗口
        detail_window = tk.Toplevel(self.main_gui.root)
        detail_window.title("操作详情")
        detail_window.geometry("1300x700")  # 增加默认窗口大小
        detail_window.minsize(900, 500)  # 设置最小窗口大小
        detail_window.resizable(True, True)  # 允许调整窗口大小
        
        # 使用主题样式美化界面
        style = ttk.Style()
        style.configure('Detail.TFrame', padding=12)
        style.configure('DetailHeader.TLabel', font=('Microsoft YaHei', 10, 'bold'), padding=5)
        
        # 全局设置表格行高 - 只配置基本样式，后续覆盖特定样式
        style.configure('Treeview', rowheight=25)  # 恢复默认行高
        
        # 创建特定样式，明确区分修改前和修改后的表格样式
        style.configure('HighRow.Treeview', rowheight=25)  # 恢复"修改前"表格默认行高
        
        # 特别设置"修改后"表格样式 - 增加行高使其更明显
        style.configure('Highlight.Treeview', background='#fffbe6')
        style.configure('Highlight.Treeview', rowheight=60)  # 只为"修改后"表格设置行高
        
        main_frame = ttk.Frame(detail_window, style='Detail.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 添加标题和信息区，使用Grid布局以获得更好的对齐效果
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(info_frame, text=f"操作类型：{op_type}", style='DetailHeader.TLabel').pack(side=tk.LEFT, padx=10)
        ttk.Label(info_frame, text=f"标签页：{tab_name}", style='DetailHeader.TLabel').pack(side=tk.LEFT, padx=10)
        ttk.Label(info_frame, text=f"操作时间：{timestamp}", style='DetailHeader.TLabel').pack(side=tk.LEFT, padx=10)
        
        # 创建一个带有边框的框架来容纳树形视图
        tree_container = ttk.LabelFrame(main_frame, text="数据内容", padding=15)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        tree_frame = ttk.Frame(tree_container)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)  # 增加内边距
        
        # 解析数据并显示
        try:
            # 尝试解析JSON数据
            try:
                data = json.loads(data_json) if isinstance(data_json, str) else data_json
            except json.JSONDecodeError as e:
                ttk.Label(tree_frame, text=f"JSON解析错误: {str(e)}\n\n原始数据:\n{data_json[:1000]}", 
                         font=('Microsoft YaHei', 10)).pack(pady=20)
                ttk.Button(main_frame, text="关闭", command=detail_window.destroy).pack(pady=10)
                return
                
            # 检查数据类型
            if not isinstance(data, (list, dict)):
                if data is None:
                    ttk.Label(tree_frame, text="（无数据）", font=('Microsoft YaHei', 10)).pack(pady=20)
                else:
                    ttk.Label(tree_frame, text=f"数据内容: {str(data)}", font=('Microsoft YaHei', 10)).pack(pady=20)
                ttk.Button(main_frame, text="关闭", command=detail_window.destroy).pack(pady=10)
                return
                
            # 先根据tab_name赋值columns和field_map
            if tab_name == "入库管理":
                columns = ["物品名", "入库时间", "入库数量", "入库花费", "入库均价", "备注"]
                field_map = {
                    "物品名": "item_name",
                    "入库时间": "transaction_time",
                    "入库数量": "quantity",
                    "入库花费": "cost",
                    "入库均价": "avg_cost",
                    "备注": "note"
                }
            elif tab_name == "出库管理":
                columns = ["物品名", "出库时间", "出库数量", "单价", "手续费", "总金额", "备注"]
                field_map = {
                    "物品名": "item_name",
                    "出库时间": "transaction_time",
                    "出库数量": "quantity",
                    "单价": "unit_price",
                    "手续费": "fee",
                    "总金额": "total_amount",
                    "备注": "note"
                }
            elif tab_name == "交易监控":
                columns = ["物品名", "数量", "一口价", "目标买入价", "计划卖出价", "保本卖出价", "利润", "利润率", "出库策略"]
                field_map = {
                    "物品名": "item_name",
                    "数量": "quantity",
                    "一口价": "market_price",
                    "目标买入价": "target_price",
                    "计划卖出价": "planned_price",
                    "保本卖出价": "break_even_price",
                    "利润": "profit",
                    "利润率": "profit_rate",
                    "出库策略": "strategy"
                }
            else:
                # 动态确定列和字段映射
                if isinstance(data, dict) and 'old' in data and 'new' in data:
                    sample = data['old'] if data['old'] else data['new']
                    if isinstance(sample, dict):
                        columns = list(sample.keys())
                        field_map = {col: col for col in columns}
                    elif isinstance(sample, (list, tuple)):
                        columns = [f"列{i+1}" for i in range(len(sample))]
                        field_map = {col: i for i, col in enumerate(columns)}
                    else:
                        columns = []
                        field_map = {}
                elif isinstance(data, dict):
                    columns = list(data.keys())
                    field_map = {col: col for col in columns}
                elif isinstance(data, list) and data and isinstance(data[0], dict):
                    columns = list(data[0].keys())
                    field_map = {col: col for col in columns}
                elif isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
                    columns = [f"列{i+1}" for i in range(len(data[0]))]
                    field_map = {col: i for i, col in enumerate(columns)}
                else:
                    # 无法确定列
                    ttk.Label(tree_frame, text=f"无法确定数据结构。原始数据:\n{str(data)[:1000]}", 
                             font=('Microsoft YaHei', 10)).pack(pady=20)
                    ttk.Button(main_frame, text="关闭", command=detail_window.destroy).pack(pady=10, padx=10)
                    return
                    
            # 处理修改日志结构 {'old':..., 'new':...}
            if isinstance(data, dict) and 'old' in data and 'new' in data:
                old_data = data['old']
                new_data = data['new']
                
                # 先显示"修改前"
                ttk.Label(tree_container, text="修改前：", style='DetailHeader.TLabel').pack(anchor='w', padx=10, pady=(10, 5))
                
                # 创建带有水平滚动条的容器
                old_frame = ttk.Frame(tree_frame)
                old_frame.pack(fill=tk.X, expand=True, pady=8)  # 增加垂直间距
                
                # 创建Treeview和滚动条
                tree_old = ttk.Treeview(old_frame, columns=columns, show='headings', height=1)
                h_scrollbar_old = ttk.Scrollbar(old_frame, orient="horizontal", command=tree_old.xview)
                tree_old.configure(xscrollcommand=h_scrollbar_old.set)
                
                # 设置最小列宽和弹性列宽
                min_width = 120  # 增加最小列宽
                
                # 计算每列的最佳宽度
                max_widths = self._calculate_column_widths(columns, [old_data] if old_data else [], min_width)
                
                # 设置行高
                style = ttk.Style()
                style.configure('HighRow.Treeview', rowheight=45)  # 设置"修改前"表格行高
                
                for idx, col in enumerate(columns):
                    tree_old.heading(col, text=col)
                    col_width = max_widths.get(col, min_width)
                    tree_old.column(col, width=col_width, minwidth=min_width, anchor='center')
                
                # 应用行高样式
                tree_old.configure(style='HighRow.Treeview')
                
                # 安全地处理旧数据
                try:
                    if isinstance(old_data, (list, tuple)):
                        tree_old.insert('', 'end', values=[str(x) for x in old_data])
                    elif isinstance(old_data, dict):
                        tree_old.insert('', 'end', values=[str(old_data.get(field_map.get(col, col), "")) for col in columns])
                    else:
                        tree_old.insert('', 'end', values=["(无数据)" for _ in columns])
                except Exception as e:
                    # 在出错时显示一个空行
                    tree_old.insert('', 'end', values=["处理数据出错" for _ in columns])
                    print(f"处理旧数据出错: {e}")
                
                # 布局控件
                tree_old.pack(fill=tk.X, expand=True)
                h_scrollbar_old.pack(fill=tk.X)
                
                # 再显示"修改后"，高亮显示
                ttk.Label(tree_container, text="修改后：", style='DetailHeader.TLabel').pack(anchor='w', padx=10, pady=(15, 5))
                
                # 创建带有水平滚动条的容器
                new_frame = ttk.Frame(tree_frame)
                new_frame.pack(fill=tk.X, expand=True, pady=8)  # 增加垂直间距
                
                # 重新配置"修改后"表格样式确保更改生效
                style = ttk.Style()
                # 清除可能的样式缓存
                style.configure('Highlight.Treeview', background='#fffbe6')
                style.configure('Highlight.Treeview', rowheight=60)  # 只为"修改后"表格设置行高
                
                # 创建Treeview并明确应用样式
                tree_new = ttk.Treeview(new_frame, columns=columns, show='headings', height=2, style='Highlight.Treeview')
                h_scrollbar_new = ttk.Scrollbar(new_frame, orient="horizontal", command=tree_new.xview)
                tree_new.configure(xscrollcommand=h_scrollbar_new.set)
                
                # 计算每列的最佳宽度
                max_widths_new = self._calculate_column_widths(columns, [new_data] if new_data else [], min_width)
                
                # 使用新旧数据中列宽的最大值
                for col in max_widths_new:
                    if col in max_widths:
                        max_widths[col] = max(max_widths[col], max_widths_new[col])
                    else:
                        max_widths[col] = max_widths_new[col]
                
                for idx, col in enumerate(columns):
                    tree_new.heading(col, text=col)
                    col_width = max_widths.get(col, min_width)
                    tree_new.column(col, width=col_width, minwidth=min_width, anchor='center')
                
                # 安全地处理新数据
                try:
                    if isinstance(new_data, (list, tuple)):
                        tree_new.insert('', 'end', values=[str(x) for x in new_data])
                    elif isinstance(new_data, dict):
                        tree_new.insert('', 'end', values=[str(new_data.get(field_map.get(col, col), "")) for col in columns])
                    else:
                        tree_new.insert('', 'end', values=["(无数据)" for _ in columns])
                except Exception as e:
                    # 在出错时显示一个空行
                    tree_new.insert('', 'end', values=["处理数据出错" for _ in columns])
                    print(f"处理新数据出错: {e}")
                
                # 布局控件
                tree_new.pack(fill=tk.X, expand=True)
                h_scrollbar_new.pack(fill=tk.X)
                
                # 尝试直接设置行高 - 通过表格整体高度调整
                # 已知表格只有一行，所以可以通过调整整体高度实现
                tree_new.configure(height=2)  # 设置为稍大的高度
                
                # 关闭按钮放在底部居中
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(fill=tk.X, pady=15)
                ttk.Button(button_frame, text="关闭", command=detail_window.destroy, width=15).pack(pady=10, padx=10, anchor=tk.CENTER)
                return
                
            # 创建滚动容器
            tree_scroll_frame = ttk.Frame(tree_frame)
            tree_scroll_frame.pack(fill=tk.BOTH, expand=True)
            
            # 创建Treeview和滚动条
            tree = ttk.Treeview(tree_scroll_frame, columns=columns, show='headings')
            v_scrollbar = ttk.Scrollbar(tree_scroll_frame, orient="vertical", command=tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_scroll_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # 设置行高
            style = ttk.Style()
            style.configure('Treeview', rowheight=25)  # 恢复默认行高
            
            # 计算每列的最佳宽度
            if isinstance(data, list):
                max_widths = self._calculate_column_widths(columns, data, min_width=120)  # 增加最小列宽
            else:
                max_widths = self._calculate_column_widths(columns, [data], min_width=120)
                
            # 设置列宽和标题    
            for col in columns:
                tree.heading(col, text=col)
                col_width = max_widths.get(col, 120)  # 增加默认列宽
                tree.column(col, width=col_width, minwidth=100, anchor='center')  # 增加最小列宽
            
            # 处理数据是数组的情况（特别是"添加"类型）
            if isinstance(data, list):
                # 一次添加多条记录时，显示所有记录
                for idx, row in enumerate(data):
                    try:
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
                            tree.insert('', 'end', values=values)
                        elif isinstance(row, (list, tuple)):
                            values = []
                            for i, val in enumerate(row):
                                try:
                                    if isinstance(val, (int, float)):
                                        if i < len(columns) and "率" in columns[i]:
                                            val = f"{val:.2f}%"
                                        elif i < len(columns) and any(keyword in columns[i] for keyword in ["价", "金额", "花费", "利润"]):
                                            val = f"{val:,.2f}"
                                        else:
                                            val = f"{int(val):,}"
                                    elif isinstance(val, str) and val.replace(".", "").isdigit():
                                        if i < len(columns) and "率" in columns[i]:
                                            val = f"{float(val):.2f}%"
                                        elif i < len(columns) and any(keyword in columns[i] for keyword in ["价", "金额", "花费", "利润"]):
                                            val = f"{float(val):,.2f}"
                                        else:
                                            val = f"{int(float(val)):,}"
                                except (ValueError, TypeError):
                                    pass
                                values.append(str(val))
                            tree.insert('', 'end', values=values)
                    except Exception as e:
                        print(f"处理行数据出错: {e}")
                        continue
                        
                # 设置交替行背景色
                style = ttk.Style()
                style.configure('Treeview', rowheight=45)  # 确保交替行也使用相同的行高
                
                # 先定义标签
                tree.tag_configure('evenrow', background='#f9f9f9')
                tree.tag_configure('oddrow', background='#ffffff')
                
                # 然后应用标签
                for i, item in enumerate(tree.get_children()):
                    if i % 2 == 0:
                        tree.item(item, tags=('evenrow',))
                    else:
                        tree.item(item, tags=('oddrow',))
            elif isinstance(data, dict):
                # 单条记录，直接添加
                values = []
                for col in columns:
                    key = field_map.get(col, col)
                    val = data.get(key, "")
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
                tree.insert('', 'end', values=values)
            
            # 正确布局组件
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # 添加记录数显示和按钮的框架
            footer_frame = ttk.Frame(main_frame)
            footer_frame.pack(fill=tk.X, pady=10)
            
            # 添加记录数显示
            if isinstance(data, list) and len(data) > 1:
                ttk.Label(footer_frame, text=f"共 {len(data)} 条记录", 
                         font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, pady=5, padx=10)
                
            # 关闭按钮
            ttk.Button(footer_frame, text="关闭", command=detail_window.destroy, width=15).pack(side=tk.RIGHT, pady=5, padx=10)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"显示数据失败: {str(e)}"
            ttk.Label(tree_frame, text=error_msg, font=('Microsoft YaHei', 10)).pack(pady=20)
            ttk.Button(main_frame, text="关闭", command=detail_window.destroy).pack(pady=10)
            
    def _calculate_column_widths(self, columns, data, min_width=100):
        """
        计算每一列的最佳宽度
        
        参数:
            columns: 列名列表
            data: 数据列表
            min_width: 最小列宽
            
        返回:
            字典，键为列名，值为建议宽度
        """
        max_widths = {col: min_width for col in columns}
        
        # 计算列标题的宽度
        for col in columns:
            # 列标题宽度 (一个中文字符约等于2个英文字符宽度)
            title_width = sum(2 if '\u4e00' <= ch <= '\u9fff' else 1 for ch in col) * 12  # 增加字符宽度系数
            max_widths[col] = max(max_widths[col], title_width)
        
        # 计算每列数据的最大宽度
        for row in data:
            if isinstance(row, dict):
                for col in columns:
                    key = col  # 使用列名作为键
                    val = str(row.get(key, ""))
                    # 数据宽度
                    data_width = sum(2 if '\u4e00' <= ch <= '\u9fff' else 1 for ch in val) * 12  # 增加字符宽度系数
                    max_widths[col] = max(max_widths[col], data_width)
            elif isinstance(row, (list, tuple)):
                for i, col in enumerate(columns):
                    if i < len(row):
                        val = str(row[i])
                        # 数据宽度
                        data_width = sum(2 if '\u4e00' <= ch <= '\u9fff' else 1 for ch in val) * 12  # 增加字符宽度系数
                        max_widths[col] = max(max_widths[col], data_width)
        
        # 限制最大宽度，避免过宽
        for col in max_widths:
            max_widths[col] = min(max_widths[col], 350)  # 增加最大列宽限制
        
        return max_widths

    def reset_filters(self):
        """重置所有筛选条件"""
        self.filter_tab.set("全部")
        self.filter_type.set("全部")
        self.filter_category.set("全部")
        self.filter_reverted.set("全部")
        self.log_search_var.set("")
        self.log_page = 1
        self.refresh_log_tab()

    def undo_operation(self):
        """调用主窗口的撤销操作方法"""
        if hasattr(self.main_gui, 'undo_last_operation'):
            self.main_gui.undo_last_operation()
    
    def redo_operation(self):
        """调用主窗口的恢复操作方法"""
        if hasattr(self.main_gui, 'redo_last_operation'):
            self.main_gui.redo_last_operation()

    def select_all_logs(self, event=None):
        """全选所有日志记录"""
        for item in self.log_tree.get_children():
            self.log_tree.selection_add(item)
        return "break"  # 阻止事件继续传播