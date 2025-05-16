import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, StringVar
import tkinter as tk
import json

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
        
        ttk.Button(button_frame, text="删除选中", 
                  command=self.delete_log_items, 
                  bootstyle="danger-outline").pack(side='left', padx=5)
        ttk.Button(button_frame, text="导出CSV", 
                  command=self.export_log_csv, 
                  bootstyle="info-outline").pack(side='left', padx=5)
        
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
        self.log_tree.tag_configure('reverted', foreground='#7f8c8d')  # 灰色
        
        # 绑定双击事件
        self.log_tree.bind("<Double-1>", self.show_log_detail)
        
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
        """窗口大小变化时的处理函数"""
        # 仅当来自根窗口且窗口高度变化明显时才处理
        if (event and event.widget == self.main_gui.root and 
            abs(self.last_window_height - self.main_gui.root.winfo_height()) > 20):
            
            self.last_window_height = self.main_gui.root.winfo_height()
            # 重新计算页面大小并刷新界面
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

    def refresh_log_tab(self):
        """刷新日志表格"""
        # 清空表格
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
            
        try:
            # 动态计算页面大小
            self.calculate_page_size()
            
            # 获取过滤条件
            tab_name = self.filter_tab.get() if hasattr(self, 'filter_tab') else None
            if tab_name == "全部": tab_name = None
                
            op_type = self.filter_type.get() if hasattr(self, 'filter_type') else None
            if op_type == "全部": op_type = None
                
            reverted = None
            if hasattr(self, 'filter_reverted'):
                if self.filter_reverted.get() == "是": reverted = True
                elif self.filter_reverted.get() == "否": reverted = False
                
            keyword = self.log_search_var.get() if self.log_search_var.get() else None
            
            # 单独获取总记录数
            total = self.main_gui.db_manager.count_operation_logs(
                tab_name=tab_name,
                op_type=op_type,
                keyword=keyword,
                reverted=reverted
            )
            
            # 特殊情况处理：如果总记录数较少，自动调整页面大小以避免过多空白
            if total > 0 and total < self.log_page_size:
                # 如果总记录数小于计算出的页面大小，则使用总记录数作为页面大小
                adjusted_page_size = max(total, self.min_records_per_page)
                if adjusted_page_size != self.log_page_size:
                    self.log_page_size = adjusted_page_size
                    self.log_tree.configure(height=adjusted_page_size)
            
            # 查询数据
            logs = self.main_gui.db_manager.get_operation_logs(
                tab_name=tab_name,
                op_type=op_type,
                keyword=keyword,
                reverted=reverted,
                page=self.log_page,
                page_size=self.log_page_size
            )
            
            # 更新分页信息
            self.log_total_records = total
            self.log_total_pages = max(1, (total + self.log_page_size - 1) // self.log_page_size)
            
            # 如果当前页码超出范围，重置为第一页
            if self.log_page > self.log_total_pages:
                self.log_page = 1
                # 重新查询第一页数据
                logs = self.main_gui.db_manager.get_operation_logs(
                    tab_name=tab_name,
                    op_type=op_type,
                    keyword=keyword,
                    reverted=reverted,
                    page=self.log_page,
                    page_size=self.log_page_size
                )
            
            # 更新页码显示
            if hasattr(self, 'log_page_info'):
                self.log_page_info.config(text=f"页码: {self.log_page} / {self.log_total_pages}  总记录: {total}  每页: {self.log_page_size}条")
            elif hasattr(self, 'log_page_label'):
                self.log_page_label.config(text=f"第{self.log_page}/{self.log_total_pages}页")
            
            # 插入数据
            for idx, log in enumerate(logs):
                # 使用交替行颜色
                row_tags = ('evenrow',) if idx % 2 == 0 else ('oddrow',)
                
                # 根据操作类型添加颜色标签
                if '添加' in log['操作类型']:
                    op_tag = 'add'
                elif '删除' in log['操作类型']:
                    op_tag = 'delete'
                elif '修改' in log['操作类型']:
                    op_tag = 'modify'
                else:
                    op_tag = None
                    
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
                
        except Exception as e:
            import traceback
            print(f"刷新日志失败: {e}")
            traceback.print_exc()

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
            op_type = values[0].replace("（已回退）", "")
            tab = values[1]
            op_time = values[2]
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
            self.log_tree.delete(item)
            deleted_count += 1
        messagebox.showinfo("成功", f"已删除 {deleted_count} 条日志记录！")
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
        detail_window.geometry("1200x600")
        main_frame = ttk.Frame(detail_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info_frame, text=f"操作类型：{op_type}", font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Label(info_frame, text=f"标签页：{tab_name}", font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Label(info_frame, text=f"操作时间：{timestamp}", font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
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
                    ttk.Button(main_frame, text="关闭", command=detail_window.destroy).pack(pady=10)
                    return
                    
            # 处理修改日志结构 {'old':..., 'new':...}
            if isinstance(data, dict) and 'old' in data and 'new' in data:
                old_data = data['old']
                new_data = data['new']
                
                # 先显示"修改前"
                ttk.Label(main_frame, text="修改前：", font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w', padx=10)
                tree_old = ttk.Treeview(tree_frame, columns=columns, show='headings', height=1)
                for col in columns:
                    tree_old.heading(col, text=col)
                    tree_old.column(col, width=120, anchor='center')
                
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
                
                tree_old.pack(fill=tk.X, padx=10)
                
                # 再显示"修改后"，高亮显示
                ttk.Label(main_frame, text="修改后：", font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w', padx=10, pady=(10,0))
                style = ttk.Style()
                style.configure('Highlight.Treeview', background='#fffbe6')  # 淡黄色
                tree_new = ttk.Treeview(tree_frame, columns=columns, show='headings', height=1, style='Highlight.Treeview')
                for col in columns:
                    tree_new.heading(col, text=col)
                    tree_new.column(col, width=120, anchor='center')
                
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
                
                tree_new.pack(fill=tk.X, padx=10)
                ttk.Button(main_frame, text="关闭", command=detail_window.destroy).pack(pady=10)
                return
                
            # 创建一个Treeview显示所有记录
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor='center')
                
            # 增加滚动条
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
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
                style.configure('Treeview', rowheight=25)
                
                # 先定义标签
                tree.tag_configure('evenrow', background='#f0f0f0')
                tree.tag_configure('oddrow', background='white')
                
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
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # 添加记录数显示
            if isinstance(data, list) and len(data) > 1:
                ttk.Label(main_frame, text=f"共 {len(data)} 条记录", 
                         font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, pady=5, padx=10)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"显示数据失败: {str(e)}"
            ttk.Label(tree_frame, text=error_msg, font=('Microsoft YaHei', 10)).pack(pady=20)
            
        ttk.Button(main_frame, text="关闭", command=detail_window.destroy).pack(pady=10)