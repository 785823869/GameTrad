import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class OCRPreviewDialog:
    """
    通用OCR识别结果预览对话框组件
    用于在所有具有OCR功能的标签页中显示统一风格的预览窗口
    支持表格显示、数据编辑和确认导入
    """
    def __init__(self, parent, title="OCR识别数据预览", chinese_font=None):
        """
        初始化OCR预览对话框
        
        参数:
            parent: 父窗口
            title: 对话框标题
            chinese_font: 中文字体
        """
        self.parent = parent
        self.title = title
        self.chinese_font = chinese_font or "SimHei"
        self.window = None
        self.callback = None
        self.tree = None
        self.tree_data = {}
        self.edit_entry = None
        self.edit_frame = None
        self.current_edit = {
            'item_id': None,
            'column': None,
            'column_index': None
        }
        self.last_hover_row = None  # 记录上一个高亮的行
        self.bootstyle = "warning"  # 默认样式，将在show方法中更新
    
    def show(self, data_list, columns, column_widths=None, column_aligns=None, 
             callback=None, bootstyle="warning"):
        """
        显示OCR预览对话框
        
        参数:
            data_list: 要显示的数据列表
            columns: 列名元组，如 ('物品名称', '数量', '单价', '手续费', '总金额')
            column_widths: 列宽字典，如 {'物品名称': 180, '数量': 90}
            column_aligns: 列对齐方式字典，如 {'物品名称': 'w', '数量': 'e'}
            callback: 确认导入后的回调函数，接收确认后的数据列表作为参数
            bootstyle: 对话框样式，如 "warning", "primary", "info"
        """
        self.callback = callback
        self.bootstyle = bootstyle
        
        # 创建预览窗口
        self.window = tb.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.minsize(650, 450)
        self.window.geometry("750x550")
        
        # 设置窗口图标
        if hasattr(self.parent, 'iconbitmap') and callable(self.parent.iconbitmap):
            self.window.iconbitmap(self.parent.iconbitmap())
        
        # 创建主框架
        main_frame = tb.Frame(self.window, bootstyle="light")
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 标题标签
        tb.Label(
            main_frame, 
            text="请确认OCR识别结果，可以在导入前修改数据（双击单元格可编辑）", 
            font=(self.chinese_font, 12, "bold"),
            bootstyle=bootstyle
        ).pack(pady=(0, 10))
        
        # 工具栏区域，添加批量操作按钮
        toolbar_frame = tb.Frame(main_frame, bootstyle="light")
        toolbar_frame.pack(fill='x', pady=(0, 5))
        
        # 添加全选按钮
        select_all_btn = tb.Button(
            toolbar_frame,
            text="全选",
            command=self._select_all_items,
            bootstyle=f"{bootstyle}-outline",
            width=10
        )
        select_all_btn.pack(side='left', padx=(0, 5))
        
        # 添加取消选择按钮
        deselect_all_btn = tb.Button(
            toolbar_frame,
            text="取消选择",
            command=self._deselect_all_items,
            bootstyle="secondary-outline",
            width=10
        )
        deselect_all_btn.pack(side='left', padx=5)
        
        # 添加删除选中记录按钮
        delete_selected_btn = tb.Button(
            toolbar_frame,
            text="删除选中",
            command=self._delete_selected_items,
            bootstyle="danger-outline",
            width=10
        )
        delete_selected_btn.pack(side='left', padx=5)
        
        # 添加批量设置备注按钮
        batch_note_btn = tb.Button(
            toolbar_frame,
            text="批量备注",
            command=self._batch_add_note,
            bootstyle=f"{bootstyle}-outline",
            width=10
        )
        batch_note_btn.pack(side='left', padx=5)
        
        # 添加选择提示
        selection_tip = tb.Label(
            toolbar_frame,
            text="提示: Ctrl+A全选, Shift多选连续项, Ctrl点击多选不连续项",
            bootstyle="secondary",
            font=(self.chinese_font, 9)
        )
        selection_tip.pack(side='right', padx=5)
        
        # 创建表格框架，限制高度
        table_container = tb.Frame(main_frame, bootstyle="light", height=350)
        table_container.pack(fill='both', expand=True, pady=(0, 15))
        table_container.pack_propagate(False)  # 防止子组件影响容器大小
        
        # 创建表格框架
        table_frame = tb.Frame(table_container, bootstyle="light")
        table_frame.pack(fill='both', expand=True)
        
        # 配置表格样式，增加行高
        style = tb.Style()
        style.configure(f"{bootstyle}.Treeview", 
                      rowheight=32,  # 增加行高，与主表格一致
                      font=(self.chinese_font, 10),
                      background="#ffffff",
                      fieldbackground="#ffffff",
                      foreground="#2c3e50")
                      
        style.configure(f"{bootstyle}.Treeview.Heading", 
                      font=(self.chinese_font, 10, "bold"),
                      background="#e0e6ed",
                      foreground="#2c3e50")
        
        # 设置默认列宽和对齐方式
        if not column_widths:
            column_widths = {col: 120 for col in columns}
        
        if not column_aligns:
            column_aligns = {col: 'center' for col in columns}
            # 通常第一列是名称，左对齐
            if len(columns) > 0:
                column_aligns[columns[0]] = 'w'
            # 通常数字列右对齐
            for col in columns:
                if '数量' in col or '价格' in col or '单价' in col or '金额' in col or '费' in col:
                    column_aligns[col] = 'e'
        
        # 创建表格，启用多选模式
        self.tree = tb.Treeview(table_frame, columns=columns, show='headings', 
                               height=10, bootstyle=bootstyle, style=f"{bootstyle}.Treeview",
                               selectmode='extended')  # 启用多选模式
        
        for col in columns:
            self.tree.heading(col, text=col, anchor='center')
            width = column_widths.get(col, 120)
            align = column_aligns.get(col, 'center')
            self.tree.column(col, width=width, anchor=align)
        
        # 滚动条
        scrollbar = tb.Scrollbar(table_frame, orient="vertical", command=self.tree.yview, 
                               bootstyle=f"{bootstyle}-round")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滚动条
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 配置表格样式
        self.tree.tag_configure('evenrow', background='#fdf7f0')  # 柔和的橙色背景
        self.tree.tag_configure('oddrow', background='#ffffff')
        self.tree.tag_configure('hovering', background='#fff8ed')  # 鼠标悬停效果
        
        # 绑定鼠标移动事件
        self.tree.bind("<Motion>", self._on_treeview_motion)
        
        # 绑定全选快捷键
        self.tree.bind('<Control-a>', self._select_all_shortcut)
        
        # 清空树数据
        self.tree_data = {}
        
        # 添加数据到表格
        self._populate_tree(data_list)
        
        # 创建编辑框
        self.edit_frame = tb.Frame(self.window)
        self.edit_entry = tb.Entry(self.edit_frame, bootstyle=bootstyle)
        
        # 绑定事件
        self.tree.bind('<Double-1>', self._edit_cell)
        self.edit_entry.bind('<Return>', self._save_edit)
        self.edit_entry.bind('<FocusOut>', self._save_edit)
        
        # 显示所选项目数量
        self.status_var = tb.StringVar(value="共 0 项已选中")
        status_bar = tb.Label(main_frame, textvariable=self.status_var, bootstyle="secondary")
        status_bar.pack(side='bottom', anchor='w', padx=5, pady=(0, 5))
        
        # 绑定选择变化事件
        self.tree.bind('<<TreeviewSelect>>', self._update_selection_status)
        
        # 按钮区域 - 使用固定高度的框架
        button_container = tb.Frame(main_frame, bootstyle="light", height=60)
        button_container.pack(side='bottom', fill='x')
        button_container.pack_propagate(False)  # 防止子组件影响容器大小
        
        # 按钮框架
        button_frame = tb.Frame(button_container)
        button_frame.pack(expand=True, fill='both')
        
        # 取消按钮
        tb.Button(
            button_frame, 
            text="取消", 
            command=self.window.destroy,
            bootstyle="secondary",
            width=15
        ).pack(side='left', padx=40, pady=5, ipady=8, ipadx=15)
        
        # 导入按钮
        tb.Button(
            button_frame, 
            text="确认导入", 
            command=self._import_data,
            bootstyle=bootstyle,
            width=15
        ).pack(side='right', padx=40, pady=5, ipady=8, ipadx=15)
        
        # 设置模态
        self.window.transient(self.parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)
    
    def _populate_tree(self, data_list):
        """将数据填充到表格中"""
        print(f"填充表格的数据列表: {data_list}")  # 调试输出
        
        for i, data in enumerate(data_list):
            # 设置交替行颜色
            row_tags = ('evenrow',) if i % 2 == 0 else ('oddrow',)
            
            # 获取所有值
            values = []
            print(f"处理数据: {data}")  # 调试输出
            print(f"表格列: {self.tree['columns']}")  # 调试输出
            
            for col in self.tree['columns']:
                # 尝试从数据中获取值，如果不存在则使用空字符串
                if isinstance(data, dict):
                    # 直接尝试使用列名作为键
                    value = data.get(col, '')
                    if value == '' and col.lower().replace(' ', '_') in data:
                        # 如果没有找到，尝试使用转换后的键名
                        key = col.lower().replace(' ', '_')
                        value = data.get(key, '')
                    print(f"列 {col} 的值: {value}")  # 调试输出
                else:
                    # 如果数据不是字典，假设是列表或元组
                    try:
                        idx = self.tree['columns'].index(col)
                        value = data[idx] if idx < len(data) else ''
                    except:
                        value = ''
                
                # 格式化数字
                if isinstance(value, (int, float)) and ('花费' in col or '费' in col):
                    # 花费和费用类数据显示为整数，无小数
                    value = f"{int(value):,}"
                elif isinstance(value, (int, float)) and '金额' in col:
                    value = f"{int(value):,}"  # 金额也显示为整数
                elif isinstance(value, (int, float)):
                    value = f"{value:,}"
                
                values.append(value)
            
            # 插入数据
            item_id = self.tree.insert('', 'end', values=values, tags=row_tags)
            print(f"插入的值: {values}")  # 调试输出
            
            # 存储原始数据
            self.tree_data[item_id] = data
    
    def _select_all_items(self):
        """全选所有项目"""
        for item in self.tree.get_children():
            self.tree.selection_add(item)
        self._update_selection_status()
    
    def _deselect_all_items(self):
        """取消所有选择"""
        self.tree.selection_remove(*self.tree.selection())
        self._update_selection_status()
    
    def _delete_selected_items(self):
        """删除选中的项目"""
        selected = self.tree.selection()
        if not selected:
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected)} 条记录吗？"):
            for item_id in selected:
                # 从表格和数据中删除
                self.tree.delete(item_id)
                if item_id in self.tree_data:
                    del self.tree_data[item_id]
            
            # 更新选中状态
            self._update_selection_status()
    
    def _select_all_shortcut(self, event):
        """响应Ctrl+A全选快捷键"""
        self._select_all_items()
        return "break"  # 阻止事件继续传播
    
    def _update_selection_status(self, event=None):
        """更新选中状态栏显示"""
        selected_count = len(self.tree.selection())
        self.status_var.set(f"共 {selected_count} 项已选中")
    
    def _edit_cell(self, event):
        """处理双击编辑单元格"""
        # 获取点击的单元格
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item_id or not column:
            return
        
        # 获取列索引（从#1开始）
        column_index = int(column[1:]) - 1
        
        # 不允许编辑某些列（如总金额列）
        if self.tree['columns'][column_index] == '总金额':
            return
        
        # 获取单元格区域
        bbox = self.tree.bbox(item_id, column)
        if not bbox:
            return
        
        # 配置编辑框
        self.edit_entry.delete(0, 'end')
        current_value = self.tree.item(item_id, 'values')[column_index]
        self.edit_entry.insert(0, current_value)
        
        # 放置编辑框
        self.edit_frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        self.edit_entry.pack(fill='both', expand=True)
        self.edit_entry.focus_set()
        
        # 更新当前编辑信息
        self.current_edit['item_id'] = item_id
        self.current_edit['column'] = column
        self.current_edit['column_index'] = column_index
    
    def _save_edit(self, event=None):
        """保存编辑结果"""
        if not self.current_edit['item_id']:
            return
        
        item_id = self.current_edit['item_id']
        column_index = self.current_edit['column_index']
        column_name = self.tree['columns'][column_index]
        new_value = self.edit_entry.get()
        
        # 获取当前行的值
        values = list(self.tree.item(item_id, 'values'))
        
        # 更新值
        values[column_index] = new_value
        
        # 更新树数据
        data = self.tree_data[item_id]
        if isinstance(data, dict):
            # 将列名转换为键名
            key = column_name.lower().replace(' ', '_')
            
            # 尝试转换为适当的类型
            try:
                if '数量' in column_name:
                    # 确保数量是正整数
                    int_value = int(new_value.replace(',', ''))
                    if int_value <= 0:
                        messagebox.showwarning("输入错误", "数量必须是正整数")
                        self.edit_entry.focus_set()
                        return
                    data[key] = int_value
                    # 同时更新英文键名
                    data['quantity'] = int_value
                    values[column_index] = f"{int_value:,}"
                elif '单价' in column_name:
                    # 确保单价是正数
                    float_value = float(new_value.replace(',', ''))
                    if float_value <= 0:
                        messagebox.showwarning("输入错误", "单价必须是正数")
                        self.edit_entry.focus_set()
                        return
                    data[key] = float_value
                    # 同时更新英文键名
                    data['unit_price'] = float_value
                    values[column_index] = f"{int(float_value):,}" if float_value >= 1 else f"{float_value:.2f}"
                elif '手续费' in column_name:
                    # 手续费可以是0或正数
                    float_value = float(new_value.replace(',', ''))
                    if float_value < 0:
                        messagebox.showwarning("输入错误", "手续费不能为负数")
                        self.edit_entry.focus_set()
                        return
                    data[key] = float_value
                    # 同时更新英文键名
                    data['fee'] = float_value
                    values[column_index] = f"{int(float_value):,}" if float_value >= 1 else f"{float_value:.2f}"
                elif '价格' in column_name or '花费' in column_name:
                    float_value = float(new_value.replace(',', ''))
                    if float_value <= 0:
                        messagebox.showwarning("输入错误", "价格必须是正数")
                        self.edit_entry.focus_set()
                        return
                    data[key] = float_value
                    values[column_index] = f"{int(float_value):,}" if float_value >= 1 else f"{float_value:.2f}"
                else:
                    data[key] = new_value
            except ValueError:
                messagebox.showwarning("输入错误", f"'{column_name}'必须是有效的数字")
                self.edit_entry.focus_set()
                return
            
            # 如果存在总金额列，更新总金额
            if '总金额' in self.tree['columns']:
                total_index = self.tree['columns'].index('总金额')
                
                # 获取必要的数据，优先使用标准化的键名
                quantity = data.get('quantity', data.get('数量', 0))
                unit_price = data.get('unit_price', data.get('单价', data.get('价格', 0)))
                fee = data.get('fee', data.get('手续费', 0))
                
                # 计算总金额
                if quantity and unit_price:
                    total = quantity * unit_price - fee
                    data['总金额'] = total
                    data['total_amount'] = total
                    values[total_index] = f"{int(total):,}"  # 显示为整数
        
        # 更新表格
        self.tree.item(item_id, values=values)
        
        # 隐藏编辑框
        self.edit_frame.place_forget()
        self.current_edit['item_id'] = None
    
    def _import_data(self):
        """导入按钮的回调函数"""
        # 获取选中的条目，如果没有选择则获取所有条目
        selected_items = self.tree.selection()
        items_to_import = selected_items if selected_items else self.tree.get_children()
        
        # 如果选择了部分记录，则需要确认
        if selected_items and len(selected_items) < len(self.tree.get_children()):
            if not messagebox.askyesno("确认导入", f"您选择了 {len(selected_items)} 条记录进行导入，是否继续？\n选择\"否\"将导入所有记录。"):
                # 用户点击"否"，导入所有记录
                items_to_import = self.tree.get_children()
        
        confirmed_data = []
        
        for item_id in items_to_import:
            data = self.tree_data[item_id]
            
            # 数据验证
            if isinstance(data, dict):
                # 检查是否有入库管理所需的必要字段
                required_fields = ['物品名称', '数量']
                required_keys = ['item_name', 'quantity']
                
                # 检查字典中是否有所有必要的键
                missing_keys = []
                
                # 检查英文键名
                for key in required_keys:
                    if key not in data:
                        # 尝试查找对应的中文键名
                        if key == 'item_name' and '物品名称' in data:
                            data[key] = data['物品名称']
                        elif key == 'quantity' and '数量' in data:
                            data[key] = data['数量']
                        else:
                            missing_keys.append(key)
                
                # 如果还有缺失的键，显示错误
                if missing_keys:
                    item_values = self.tree.item(item_id, 'values')
                    item_desc = f"物品: {item_values[0]}" if item_values and len(item_values) > 0 else "未知物品"
                    messagebox.showerror("数据不完整", f"{item_desc} 缺少必要字段: {', '.join(missing_keys)}\n请确保填写了所有必要信息。")
                    return
                
                # 确保数据类型正确
                try:
                    data['quantity'] = int(data['quantity'])
                    
                    # 处理花费字段 - 优先使用cost，如果没有则尝试使用unit_price计算
                    if 'cost' not in data and 'unit_price' in data:
                        data['cost'] = float(data['unit_price']) * data['quantity']
                    elif 'cost' in data:
                        data['cost'] = float(data['cost'])
                    else:
                        # 如果既没有cost也没有unit_price，则报错
                        item_values = self.tree.item(item_id, 'values')
                        item_desc = f"物品: {item_values[0]}" if item_values and len(item_values) > 0 else "未知物品"
                        messagebox.showerror("数据不完整", f"{item_desc} 缺少花费或单价信息\n请确保填写了花费或单价。")
                        return
                    
                    # 处理均价字段 - 如果没有则计算
                    if 'avg_cost' not in data:
                        data['avg_cost'] = data['cost'] / data['quantity'] if data['quantity'] > 0 else 0
                    else:
                        data['avg_cost'] = float(data['avg_cost'])
                    
                    # 确保有备注字段
                    if 'note' not in data:
                        data['note'] = ''
                    
                except (ValueError, TypeError) as e:
                    item_values = self.tree.item(item_id, 'values')
                    item_desc = f"物品: {item_values[0]}" if item_values and len(item_values) > 0 else "未知物品"
                    messagebox.showerror("数据格式错误", f"{item_desc} 的数据格式不正确: {str(e)}\n请确保数量为整数，花费和均价为数字。")
                    return
            
            confirmed_data.append(data)
        
        # 关闭预览窗口
        self.window.destroy()
        
        # 调用回调函数
        if self.callback:
            self.callback(confirmed_data)

    def _on_treeview_motion(self, event):
        """处理鼠标在表格上的移动，动态应用悬停高亮效果"""
        # 识别当前鼠标位置的行
        row_id = self.tree.identify_row(event.y)
        
        # 如果鼠标离开了上一个高亮行，恢复其原始样式
        if self.last_hover_row and self.last_hover_row != row_id:
            # 获取行的当前标签
            current_tags = list(self.tree.item(self.last_hover_row, 'tags'))
            # 移除悬停标签
            if 'hovering' in current_tags:
                current_tags.remove('hovering')
                self.tree.item(self.last_hover_row, tags=current_tags)
                
        # 如果鼠标位于一个有效行上，应用悬停高亮效果
        if row_id and row_id != self.last_hover_row:
            # 获取行的当前标签
            current_tags = list(self.tree.item(row_id, 'tags'))
            # 添加悬停标签
            if 'hovering' not in current_tags:
                current_tags.append('hovering')
                self.tree.item(row_id, tags=current_tags)
                
        # 更新上一个高亮行的记录
        self.last_hover_row = row_id if row_id else None

    def _batch_add_note(self):
        """批量添加备注"""
        # 获取选中的项目，如果没有选中，则应用于所有项目
        selected_items = self.tree.selection()
        target_items = selected_items if selected_items else self.tree.get_children()
        
        if not target_items:
            messagebox.showinfo("提示", "没有可用的记录")
            return
        
        # 创建一个自定义对话框获取备注文本
        class BatchNoteDialog(tk.simpledialog.Dialog):
            def __init__(self, parent, title, bootstyle, chinese_font):
                self.note_text = ""
                self.bootstyle = bootstyle
                self.chinese_font = chinese_font
                super().__init__(parent, title)
            
            def body(self, master):
                tb.Label(
                    master,
                    text="请输入要批量添加的备注内容：",
                    font=(self.chinese_font, 10),
                    bootstyle=self.bootstyle
                ).grid(row=0, column=0, sticky="w", padx=10, pady=5)
                
                # 使用普通的tk.Text而不是tb.Text，因为tb.Text不支持bootstyle参数
                self.note_entry = tk.Text(
                    master,
                    width=40,
                    height=4,
                    font=(self.chinese_font, 10)
                )
                self.note_entry.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
                
                # 设置提示
                if selected_items:
                    item_count = len(selected_items)
                    tb.Label(
                        master,
                        text=f"将应用于已选中的 {item_count} 条记录",
                        font=(self.chinese_font, 9),
                        bootstyle="secondary"
                    ).grid(row=2, column=0, sticky="w", padx=10, pady=5)
                else:
                    tb.Label(
                        master,
                        text="将应用于所有记录",
                        font=(self.chinese_font, 9),
                        bootstyle="secondary"
                    ).grid(row=2, column=0, sticky="w", padx=10, pady=5)
                
                return self.note_entry  # 初始聚焦组件
            
            def apply(self):
                self.note_text = self.note_entry.get("1.0", "end-1c")
        
        # 显示对话框
        dialog = BatchNoteDialog(
            self.window,
            "批量添加备注",
            self.bootstyle,
            self.chinese_font
        )
        
        if not dialog.note_text:
            return  # 用户取消或没有输入文本
        
        # 更新所有目标记录的备注字段
        note_column_index = -1
        
        # 查找备注列的索引
        for i, col in enumerate(self.tree['columns']):
            if '备注' in col or col == 'note':
                note_column_index = i
                break
        
        # 如果找不到备注列，则尝试查找数据字典中是否有备注字段
        has_note_field = False
        if note_column_index == -1:
            # 检查第一条记录数据结构
            if target_items and self.tree_data:
                first_data = self.tree_data[target_items[0]]
                if isinstance(first_data, dict) and ('note' in first_data or '备注' in first_data):
                    has_note_field = True
        
        # 应用备注到所有目标记录
        for item_id in target_items:
            data = self.tree_data[item_id]
            
            # 更新树视图中的显示（如果有备注列）
            if note_column_index >= 0:
                values = list(self.tree.item(item_id, "values"))
                values[note_column_index] = dialog.note_text
                self.tree.item(item_id, values=values)
            
            # 更新数据字典
            if isinstance(data, dict):
                # 同时更新中文和英文键名
                data['note'] = dialog.note_text
                data['备注'] = dialog.note_text
        
        # 显示成功消息
        count = len(target_items)
        messagebox.showinfo("成功", f"已为 {count} 条记录设置备注")

    def _dummy_method(self):
        """用于确保文件正确结束"""
        pass 