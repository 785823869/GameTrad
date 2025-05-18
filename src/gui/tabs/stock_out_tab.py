import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog as fd
# PIL导入，只需基本模块
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    # 如果PIL模块不完整，创建一个占位符
    PIL_AVAILABLE = False
    messagebox.showwarning("模块缺失", "PIL图像处理模块不完整，图片粘贴功能将不可用。请确保正确安装Pillow库。")
import io, base64, requests
from datetime import datetime
import tkinter as tk
import re
from src.gui.dialogs import ModalInputDialog
from src.gui.components import OCRPreview, OCRPreviewDialog
from src.utils import clipboard_helper

class StockOutTab:
    def __init__(self, notebook, main_gui):
        """初始化出库管理标签页"""
        self.notebook = notebook
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        # 设置中文字体
        self.chinese_font = main_gui.chinese_font
        
        # 保存图片列表
        self._pending_ocr_images_out = []
        
        # 悬停行索引
        self.last_hover_row = None
        
        # 添加剪贴板监听状态标志
        self.monitoring_clipboard = False
        self.monitor_job_id = None
        
        # 创建标签页
        self.create_tab()
        
        # 设置样式
        self.setup_styles()
        
        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def setup_styles(self):
        """设置自定义样式"""
        style = tb.Style()
        
        # 表格样式
        style.configure("StockOut.Treeview", 
                      rowheight=32,  # 增加行高
                      font=(self.chinese_font, 10),
                      background="#ffffff",
                      fieldbackground="#ffffff",
                      foreground="#2c3e50")
                      
        style.configure("StockOut.Treeview.Heading", 
                      font=(self.chinese_font, 10, "bold"),
                      background="#e0e6ed",
                      foreground="#2c3e50")
        
        # 移除表格行鼠标悬停效果的style.map设置，改为使用标签和事件处理
        style.map('StockOut.Treeview', 
                background=[('selected', '#e69c57')])  # 只保留选中效果
        
        # 按钮样式
        style.configure("StockOut.TButton", 
                      font=(self.chinese_font, 11),
                      foreground="#ffffff")
        
        # 标签样式
        style.configure("StockOut.TLabel", 
                      font=(self.chinese_font, 10),
                      foreground="#2c3e50")
        
        # 创建统一的LabelFrame样式，背景色与主窗口背景色匹配
        style.configure("Unified.TLabelframe", 
                      background="#f0f0f0",  # 与主窗口背景色匹配
                      borderwidth=1)
                      
        style.configure("Unified.TLabelframe.Label", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#2c3e50",
                      background="#f0f0f0")  # 与主窗口背景色匹配
        
        # 创建统一的标签样式
        style.configure("Unified.TLabel", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#2c3e50",
                      background="#f0f0f0")  # 与主窗口背景色匹配
        
        # 创建透明LabelFrame样式
        style.configure("Transparent.TLabelframe", 
                      background="transparent",  # 透明背景
                      borderwidth=1)
                      
        style.configure("Transparent.TLabelframe.Label", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#2c3e50",
                      background="transparent")  # 透明背景
        
        # 过滤器样式
        style.configure("Filter.TLabel", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#3a506b")
                      
        style.configure("Filter.TEntry", 
                      font=(self.chinese_font, 10),
                      foreground="#2c3e50")

    def create_tab(self):
        # 检查是否在新UI结构中运行
        if isinstance(self.notebook, tk.Frame) or isinstance(self.notebook, tb.Frame):
            # 新UI结构，notebook实际上是框架
            stock_out_frame = self.notebook
        else:
            # 旧UI结构，notebook是Notebook
            stock_out_frame = tb.Frame(self.notebook, padding=10, bootstyle="light")
            self.notebook.add(stock_out_frame, text="出库管理")
        
        # 创建上方的工具栏
        toolbar = tb.Frame(stock_out_frame, bootstyle="light")
        toolbar.pack(fill='x', pady=(0, 5))
        
        # 过滤器区域
        filter_frame = tb.LabelFrame(toolbar, text="筛选", style="Unified.TLabelframe", padding=5)
        filter_frame.pack(side='left', fill='y', padx=(0, 10))
        
        tb.Label(filter_frame, text="物品:", style="Unified.TLabel").pack(side='left', padx=2)
        
        self.stock_out_filter_var = tb.StringVar()
        filter_entry = tb.Entry(filter_frame, textvariable=self.stock_out_filter_var, width=12, bootstyle="warning")
        filter_entry.pack(side='left', padx=2)
        filter_entry.bind("<Return>", lambda e: self.refresh_stock_out())
        
        tb.Button(filter_frame, text="筛选", command=self.refresh_stock_out, bootstyle="warning-outline").pack(side='left', padx=2)
        tb.Button(filter_frame, text="清除", command=lambda: [self.stock_out_filter_var.set(""), self.refresh_stock_out()], bootstyle="secondary-outline").pack(side='left', padx=2)
        
        # 主区域分割
        main_area = tb.Frame(stock_out_frame, bootstyle="light")
        main_area.pack(fill='both', expand=True)
        
        # 表格区域
        table_frame = tb.Frame(main_area, bootstyle="light")
        table_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # 表格和滚动条
        columns = ('物品', '当前时间', '出库数量', '出库单价', '手续费', '总金额', '备注')
        
        # 设置表头和列宽
        column_widths = {
            '物品': 180,     # 加宽物品名称列
            '当前时间': 160,
            '出库数量': 90,
            '出库单价': 95,
            '手续费': 85,
            '总金额': 120,    # 增加总金额列宽度
            '备注': 170      # 加宽备注列
        }
        
        # 设置列对齐方式
        column_aligns = {
            '物品': 'center',     # 文本居中对齐
            '当前时间': 'center',
            '出库数量': 'center',  # 数字居中对齐
            '出库单价': 'center',  # 数字居中对齐
            '手续费': 'center',    # 数字居中对齐
            '总金额': 'center',    # 数字居中对齐
            '备注': 'center'      # 文本居中对齐
        }
        
        # 创建表格
        self.stock_out_tree = tb.Treeview(table_frame, columns=columns, show='headings', 
                                         height=16, bootstyle="warning", style="StockOut.Treeview")
        
        for col in columns:
            self.stock_out_tree.heading(col, text=col, anchor='center')
            width = column_widths.get(col, 120)
            align = column_aligns.get(col, 'center')
            self.stock_out_tree.column(col, width=width, anchor=align)
            
        # 滚动条
        scrollbar = tb.Scrollbar(table_frame, orient="vertical", command=self.stock_out_tree.yview, bootstyle="warning-round")
        self.stock_out_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滚动条
        self.stock_out_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        
        # 配置表格样式
        self.stock_out_tree.tag_configure('evenrow', background='#fdf7f0')  # 柔和的橙色背景
        self.stock_out_tree.tag_configure('oddrow', background='#ffffff')
        self.stock_out_tree.tag_configure('total', background='#fff8dc', font=(self.chinese_font, 11, 'bold'))
        # 添加悬停高亮标签
        self.stock_out_tree.tag_configure('hovering', background='#fff8ed')  # 鼠标悬停效果
        
        # 绑定鼠标移动事件
        self.stock_out_tree.bind("<Motion>", self.on_treeview_motion)
        # 记录上一个高亮的行
        self.last_hover_row = None
        
        # 右侧面板
        right_panel = tb.Frame(main_area, width=260, bootstyle="light")
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        
        # 操作按钮区
        actions_frame = tb.LabelFrame(right_panel, text="操作", style="Unified.TLabelframe", padding=5)
        actions_frame.pack(fill='x', pady=(0, 10))
        
        # 添加记录按钮 - 使用明显的颜色
        tb.Button(
            actions_frame, 
            text="添加出库记录", 
            command=self.show_add_stock_out_dialog,
            bootstyle="warning"
        ).pack(fill='x', pady=5, ipady=5)
        
        tb.Button(actions_frame, text="刷新出库记录", command=self.refresh_stock_out, 
                bootstyle="warning-outline").pack(fill='x', pady=2, ipady=2)
        
        # OCR工具区域 - 使用统一样式
        ocr_tools_frame = tb.LabelFrame(right_panel, text="OCR工具", style="Unified.TLabelframe", padding=5)
        ocr_tools_frame.pack(fill='x', pady=(0, 10))
        
        tb.Button(ocr_tools_frame, text="上传图片自动出库", command=self.upload_ocr_import_stock_out,
                bootstyle="warning").pack(fill='x', pady=2, ipady=2)
                
        tb.Button(ocr_tools_frame, text="批量识别粘贴图片", command=self.batch_ocr_import_stock_out,
                bootstyle="warning-outline").pack(fill='x', pady=2, ipady=2)
        
        # 添加监听剪贴板按钮
        self.monitor_button = tb.Button(
            ocr_tools_frame, 
            text="监听剪贴板", 
            command=self.toggle_clipboard_monitoring,
            bootstyle="warning"
        )
        self.monitor_button.pack(fill='x', pady=2, ipady=2)
        
        # 使用键盘快捷键提示
        shortcut_frame = tb.Frame(right_panel, bootstyle="light")
        shortcut_frame.pack(fill='x', pady=(0, 5))
        
        tb.Label(shortcut_frame, text="快捷键: Ctrl+V 粘贴图片", bootstyle="secondary").pack(anchor='w')
        
        # OCR预览区域 - 使用统一样式
        ocr_frame = tb.LabelFrame(right_panel, text="OCR图片预览", style="Unified.TLabelframe", padding=5)
        ocr_frame.pack(fill='x', pady=5, padx=2)
        
        # 创建OCR预览组件
        self.ocr_preview = OCRPreview(ocr_frame, height=150)
        self.ocr_preview.pack(fill='both', expand=True, padx=2, pady=5)
        self.ocr_preview.set_callback(self.delete_ocr_image_out)
        
        # 绑定Ctrl+V快捷键
        right_panel.bind_all('<Control-v>', self.paste_ocr_import_stock_out)
        
        # 右键菜单
        self.stock_out_menu = tb.Menu(self.stock_out_tree, tearoff=0)
        self.stock_out_menu.add_command(label="编辑", command=lambda: self.edit_stock_out_item(None))
        self.stock_out_menu.add_command(label="删除", command=self.delete_stock_out_item)
        self.stock_out_menu.add_separator()
        self.stock_out_menu.add_command(label="复制物品名", command=lambda: self.copy_item_name())
        
        # 绑定右键菜单
        self.stock_out_tree.bind("<Button-3>", self.show_stock_out_menu)
        
        # 支持Ctrl+A全选和双击编辑
        self.stock_out_tree.bind('<Control-a>', lambda e: [self.stock_out_tree.selection_set(self.stock_out_tree.get_children()), 'break'])
        self.stock_out_tree.bind("<Double-1>", self.edit_stock_out_item)
        
        # 底部状态栏
        status_frame = tb.Frame(stock_out_frame, bootstyle="light")
        status_frame.pack(fill='x', side='bottom', pady=(5, 0))
        
        self.status_var = tb.StringVar(value="就绪")
        status_label = tb.Label(status_frame, textvariable=self.status_var, bootstyle="secondary")
        status_label.pack(side='left')
        
        # 初始加载数据
        self.refresh_stock_out()
                
    def show_add_stock_out_dialog(self):
        """显示添加出库记录的模态对话框"""
        fields = [
            ("物品", "item_name", "str"),
            ("出库数量", "quantity", "int"),
            ("出库单价", "unit_price", "float"),
            ("手续费", "fee", "float"),
            ("备注", "note", "str")
        ]
        
        # 添加解释说明
        explanation = (
            "出库记录说明:\n"
            "- 物品会自动检查库存是否足够\n"
            "- 总金额 = 数量×单价 - 手续费\n"
            "- 出库后会自动更新库存"
        )
        
        # 使用增强的ModalInputDialog类
        dialog = ModalInputDialog(
            self.main_gui.root,
            "添加出库记录",
            fields,
            self.process_add_stock_out,
            explanation=explanation  # 使用新增的参数传入说明文本
        )
        
        # 使用新的set_field_style方法设置字段样式
        dialog.set_field_style("item_name", "Dialog.TLabel", "warning")
        dialog.set_field_style("quantity", "Dialog.TLabel", "warning")
    
    def process_add_stock_out(self, values):
        """处理添加出库记录的回调"""
        try:
            item = values["item_name"]
            quantity = values["quantity"]
            unit_price = values["unit_price"]
            fee = values["fee"]
            note = values["note"]
            
            total_amount = quantity * unit_price - fee
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 检查库存
            inventory = self.db_manager.get_item_inventory(item)
            if inventory is not None and inventory[0] < quantity:
                if not messagebox.askyesno("库存不足", f"物品 {item} 库存不足，当前库存: {inventory[0]}，出库数量: {quantity}。确定继续出库吗？"):
                    return
            
            self.db_manager.save_stock_out({
                'item_name': item,
                'transaction_time': now,
                'quantity': quantity,
                'unit_price': unit_price,
                'fee': fee,
                'deposit': 0.0,  # 设置押金默认值为0
                'total_amount': total_amount,
                'note': note if note is not None else ''
            })
            
            if inventory is not None:
                self.db_manager.decrease_inventory(item, quantity)
            
            self.refresh_stock_out()
            
            # 确保库存页面也更新
            if hasattr(self.main_gui, 'inventory_tab') and self.main_gui.inventory_tab:
                self.main_gui.inventory_tab.refresh_inventory(show_dialog=False)
                
            self.main_gui.refresh_inventory()
            # 使用正确的操作类型常量
            from src.utils.operation_types import OperationType, TabName
            self.main_gui.log_operation(OperationType.ADD, TabName.STOCK_OUT, {
                'item_name': item,
                'quantity': quantity,
                'unit_price': unit_price,
                'fee': fee,
                'total_amount': total_amount,
                'note': note if note is not None else ''
            })
            
            messagebox.showinfo("成功", "出库记录添加成功！")
            self.status_var.set(f"已添加: {item} x {quantity}")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            self.status_var.set(f"添加记录失败: {str(e)}")

    def refresh_stock_out(self):
        """刷新出库记录表格"""
        for item in self.stock_out_tree.get_children():
            self.stock_out_tree.delete(item)
            
        self.status_var.set("正在加载数据...")
        stock_out_data = self.db_manager.get_stock_out()
        filter_text = self.stock_out_filter_var.get().strip()
        filtered = []
        
        for item in stock_out_data:
            try:
                # 正确解析数据库查询结果，包括押金字段
                _, item_name, transaction_time, quantity, unit_price, fee, deposit, total_amount, note, *_ = item
            except Exception as e:
                messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nitem={item}")
                continue
                
            if not filter_text or filter_text in str(item_name):
                filtered.append((item_name, transaction_time, quantity, unit_price, fee, total_amount, note))
                
        # 添加数据到表格
        total = [0, 0, 0, 0, 0]  # 数量、单价和、手续费和、总额
        
        for i, (item_name, transaction_time, quantity, unit_price, fee, total_amount, note) in enumerate(filtered):
            # 设置交替行颜色
            row_tags = ('evenrow',) if i % 2 == 0 else ('oddrow',)
            
            # 格式化数字显示
            quantity_display = f"{int(quantity):,}" if quantity else "0"
            unit_price_display = f"{int(round(unit_price)):,}" if unit_price else "0"
            fee_display = f"{int(round(fee)):,}" if fee else "0"
            total_amount_display = f"{int(round(total_amount)):,}" if total_amount else "0"
            
            self.stock_out_tree.insert('', 'end', values=(
                item_name,
                transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                quantity_display,
                unit_price_display,
                fee_display,
                total_amount_display,
                note if note is not None else ''
            ), tags=row_tags)
            
            try:
                total[0] += int(quantity)
                total[1] += int(round(unit_price))
                total[2] += int(round(fee))
                total[3] += int(round(total_amount))
            except:
                pass
                
        # 合计行
        if filter_text and filtered:
            self.stock_out_tree.insert('', 'end', values=(
                '合计', '', 
                f"{total[0]:,}", 
                f"{total[1]:,}", 
                f"{total[2]:,}", 
                f"{total[3]:,}", 
                ''
            ), tags=('total',))
            
        self.status_var.set(f"共 {len(filtered)} 条记录  |  上次更新: {datetime.now().strftime('%H:%M:%S')}")

    def edit_stock_out_item(self, event):
        """编辑出库记录"""
        if event:  # 如果是通过双击事件触发
            item_id = self.stock_out_tree.identify_row(event.y)
        else:  # 如果是通过右键菜单触发
            selected = self.stock_out_tree.selection()
            if not selected:
                return
            item_id = selected[0]
            
        if not item_id:
            return
            
        values = self.stock_out_tree.item(item_id)['values']
        
        # 使用ttkbootstrap创建更美观的编辑窗口
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑出库记录")
        edit_win.minsize(420, 500)
        edit_win.configure(bg='#f0f0f0')
        
        # 设置窗口图标和样式
        edit_win.iconbitmap(self.main_gui.root.iconbitmap()) if hasattr(self.main_gui.root, 'iconbitmap') and callable(self.main_gui.root.iconbitmap) else None
        
        style = tb.Style()
        style.configure('Edit.TLabel', font=(self.chinese_font, 11), background='#f0f0f0')
        style.configure('Edit.TEntry', font=(self.chinese_font, 11))
        style.configure('Edit.TButton', font=(self.chinese_font, 12, 'bold'), background='#ff9800', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#ffb74d')], foreground=[('active', '#3e2723')])
        style.configure('Edit.TFrame', background='#f0f0f0')
        
        # 创建内容框架
        content_frame = tb.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        
        # 字段标题和数据类型
        labels = ["物品", "出库时间", "出库数量", "出库单价", "手续费", "总金额", "备注"]
        types = [str, str, int, float, float, float, str]
        entries = []
        error_labels = []
        
        # 处理表格值，移除千位分隔符
        processed_values = list(values)
        if len(processed_values) >= 7:
            # 处理数量字段(索引2)
            if processed_values[2]:
                processed_values[2] = self._safe_int_convert(processed_values[2])
            # 处理单价字段(索引3)
            if processed_values[3]:
                # 转换为浮点数后取整为整数
                float_val = self._safe_float_convert(processed_values[3])
                processed_values[3] = int(round(float_val))
            # 处理手续费字段(索引4)
            if processed_values[4]:
                # 转换为浮点数后取整为整数
                float_val = self._safe_float_convert(processed_values[4])
                processed_values[4] = int(round(float_val))
            # 处理总金额字段(索引5)
            if processed_values[5]:
                # 转换为浮点数后取整为整数
                float_val = self._safe_float_convert(processed_values[5])
                processed_values[5] = int(round(float_val))
        
        # 创建字段
        for i, (label, val, typ) in enumerate(zip(labels, processed_values, types)):
            # 使用ttkbootstrap的标签，确保背景色一致
            tb.Label(
                content_frame, 
                text=label+":", 
                font=(self.chinese_font, 11),
                bootstyle="default",
                style='Edit.TLabel',
                anchor='e'  # 右对齐文本
            ).grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
                
            entry = tb.Entry(content_frame, validate='key', validatecommand=vcmd, bootstyle="warning") if vcmd else tb.Entry(content_frame, bootstyle="warning")
            entry.insert(0, val)
            entry.grid(row=i*2, column=1, padx=12, pady=4, sticky='ew')
            entries.append(entry)
            
            # 使用ttkbootstrap的标签作为错误提示，确保背景色一致
            err = tb.Label(
                content_frame, 
                text="", 
                bootstyle="danger",
                style='Edit.TLabel',
                font=(self.chinese_font, 10)
            )
            err.grid(row=i*2+1, column=0, columnspan=2, sticky='w', padx=12)
            error_labels.append(err)
            
        # 配置网格布局，使第二列可以扩展
        content_frame.columnconfigure(1, weight=1)
        
        def save():
            new_vals = [e.get() for e in entries]
            valid = True
            for idx, (val, typ, err_lbl) in enumerate(zip(new_vals, types, error_labels)):
                err_lbl.config(text="")
                if typ is int:
                    if not val.isdigit():
                        err_lbl.config(text="请输入正整数")
                        entries[idx].focus_set()
                        valid = False
                        break
                elif typ is float:
                    try:
                        float(val)
                    except Exception:
                        err_lbl.config(text="请输入数字")
                        entries[idx].focus_set()
                        valid = False
                        break
            if not valid:
                return
                
            try:
                new_vals[2] = int(new_vals[2])
                new_vals[3] = float(new_vals[3])
                new_vals[4] = float(new_vals[4])
                new_vals[5] = float(new_vals[5])
            except Exception:
                error_labels[2].config(text="数字字段必须为有效数字")
                entries[2].focus_set()
                return
                
            if not messagebox.askyesno("确认", "确定要保存修改吗？"):
                return
                
            self.db_manager.delete_stock_out(values[0], values[1])
            self.db_manager.save_stock_out({
                'item_name': new_vals[0],
                'transaction_time': new_vals[1],
                'quantity': new_vals[2],
                'unit_price': new_vals[3],
                'fee': new_vals[4],
                'deposit': 0.0,
                'total_amount': new_vals[5],
                'note': new_vals[6]
            })
            
            self.refresh_stock_out()
            edit_win.destroy()
            # 使用正确的操作类型常量
            from src.utils.operation_types import OperationType, TabName
            self.main_gui.log_operation(OperationType.MODIFY, TabName.STOCK_OUT, {'old': values, 'new': new_vals})
            self.status_var.set(f"已编辑: {new_vals[0]} 记录")
            
        # 按钮区域
        button_frame = tb.Frame(edit_win, bootstyle="light")
        button_frame.pack(side='bottom', fill='x', pady=20)
        
        # 创建按钮
        cancel_btn = tb.Button(button_frame, text="取消", command=edit_win.destroy, bootstyle="secondary")
        cancel_btn.pack(side='left', padx=20, ipadx=20)
        
        save_btn = tb.Button(button_frame, text="保存", command=save, bootstyle="warning")
        save_btn.pack(side='right', padx=20, ipadx=20)

    def delete_stock_out_item(self):
        """删除出库记录"""
        selected_items = self.stock_out_tree.selection()
        if not selected_items:
            return
            
        names = [self.stock_out_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下出库记录吗？\n" + "，".join(str(n) for n in names)
        
        if messagebox.askyesno("确认删除", msg):
            deleted_data = []  # 用于记录被删除的数据
            for item in selected_items:
                values = self.stock_out_tree.item(item)['values']
                if len(values) >= 2:
                    try:
                        # 获取完整数据用于记录
                        item_data = {
                            'item_name': values[0],
                            'transaction_time': values[1],
                            'quantity': self._safe_int_convert(values[2]) if len(values) > 2 else 0,
                            'unit_price': self._safe_float_convert(values[3]) if len(values) > 3 else 0.0,
                            'fee': self._safe_float_convert(values[4]) if len(values) > 4 else 0.0,
                            'deposit': 0.0,  # 默认押金值
                            'total_amount': self._safe_float_convert(values[5]) if len(values) > 5 else 0.0,
                            'note': values[6] if len(values) > 6 else ''
                        }
                        deleted_data.append(item_data)
                        self.db_manager.delete_stock_out(values[0], values[1])
                    except Exception as e:
                        messagebox.showerror("删除失败", f"删除记录时发生错误: {str(e)}")
            
            # 记录操作日志
            if deleted_data:
                from src.utils.operation_types import OperationType, TabName
                self.main_gui.log_operation(OperationType.DELETE, TabName.STOCK_OUT, deleted_data)
            
            self.refresh_stock_out()
            self.status_var.set(f"已删除 {len(selected_items)} 条记录")
    
    def _safe_int_convert(self, value):
        """安全地将值转换为整数，处理带有千位分隔符的情况"""
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                # 移除千位分隔符和其他非数字字符
                clean_value = ''.join(c for c in value if c.isdigit())
                return int(clean_value) if clean_value else 0
            return 0
        except Exception as e:
            print(f"整数转换异常: {e}, 值: {value}")
            return 0
            
    def _safe_float_convert(self, value):
        """安全地将值转换为浮点数，处理带有千位分隔符的情况"""
        try:
            if isinstance(value, float):
                return value
            if isinstance(value, int):
                return float(value)
            if isinstance(value, str):
                # 移除千位分隔符
                clean_value = value.replace(',', '')
                return float(clean_value) if clean_value else 0.0
            return 0.0
        except Exception as e:
            print(f"浮点数转换异常: {e}, 值: {value}")
            return 0.0

    def copy_item_name(self):
        """复制选中的物品名称到剪贴板"""
        selected_items = self.stock_out_tree.selection()
        if not selected_items:
            return
        
        item_name = self.stock_out_tree.item(selected_items[0])['values'][0]
        self.notebook.clipboard_clear()
        self.notebook.clipboard_append(item_name)
        self.status_var.set(f"已复制: {item_name}")

    def refresh_ocr_image_preview_out(self):
        self.ocr_preview.clear_images()
        for img in self._pending_ocr_images_out:
            self.ocr_preview.add_image(img)

    def delete_ocr_image_out(self, idx):
        if 0 <= idx < len(self._pending_ocr_images_out):
            self._pending_ocr_images_out.pop(idx)
            self.refresh_ocr_image_preview_out()

    def upload_ocr_import_stock_out(self):
        """上传图片进行OCR识别导入"""
        if not PIL_AVAILABLE:
            messagebox.showwarning("功能不可用", "PIL图像处理模块不可用，无法使用图片上传功能。请确保正确安装Pillow库。")
            return
            
        file_path = fd.askopenfilename(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        try:
            # 确保Image已正确导入
            img = Image.open(file_path)
            self._pending_ocr_images_out.append(img)
            # 使用refresh_ocr_image_preview_out方法刷新图片显示
            self.refresh_ocr_image_preview_out()
            messagebox.showinfo("提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def batch_ocr_import_stock_out(self):
        """批量OCR识别处理出库数据"""
        # 从新组件获取图片列表
        ocr_images = self.ocr_preview.get_images()
        if not ocr_images:
            messagebox.showinfo("提示", "请先添加图片")
            return
            
        all_data = []
        for img in ocr_images:
            try:
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                url = "http://sql.didiba.uk:1224/api/ocr"
                payload = {
                    "base64": img_b64,
                    "options": {
                        "data.format": "text"
                    }
                }
                headers = {"Content-Type": "application/json"}
                resp = requests.post(url, json=payload, headers=headers, timeout=20)
                resp.raise_for_status()
                ocr_result = resp.json()
                text = ocr_result.get('data')
                if not text:
                    continue
                
                # 首先尝试使用最新的V3解析方法
                data = self.parse_stock_out_ocr_text_v3(text)
                # 如果V3方法失败，尝试V2方法
                if not data:
                    data = self.parse_stock_out_ocr_text_v2(text)
                # 如果V2方法也失败，回退到通用方法
                if not data:
                    data = self.parse_stock_out_ocr_text(text)
                    
                if data:
                    # 确保数据包含所有必要字段
                    if 'note' not in data:
                        data['note'] = ''
                    if 'fee' not in data:
                        data['fee'] = 0
                    if 'total_amount' not in data:
                        data['total_amount'] = data['quantity'] * data['unit_price'] - data.get('fee', 0)
                    
                    # 确保数据包含预览对话框期望的字段名
                    if 'item_name' in data and '物品名称' not in data:
                        data['物品名称'] = data['item_name']
                    if 'quantity' in data and '数量' not in data:
                        data['数量'] = data['quantity']
                    if 'unit_price' in data and '单价' not in data:
                        data['单价'] = data['unit_price']
                    if 'fee' in data and '手续费' not in data:
                        data['手续费'] = data['fee']
                    if 'total_amount' in data and '总金额' not in data:
                        data['总金额'] = data['total_amount']
                    if 'note' in data and '备注' not in data:
                        data['备注'] = data['note']
                        
                    print(f"添加到预览的数据: {data}")  # 调试输出
                    all_data.append(data)
            except Exception as e:
                messagebox.showerror("错误", f"OCR识别失败: {e}")
                
        if all_data:
            print(f"预览数据列表: {all_data}")  # 调试输出
            # 显示OCR识别数据预览窗口
            self.show_ocr_preview_dialog(all_data)
        else:
            messagebox.showwarning("警告", "未能识别有效的出库记录！")

    def show_ocr_preview_dialog(self, ocr_data_list):
        """显示OCR识别数据预览窗口（表格形式）"""
        print(f"OCR预览数据: {ocr_data_list}")  # 调试输出
        
        # 定义列
        columns = ('物品', '出库数量', '出库单价', '手续费', '总金额', '备注')
        
        # 设置列宽和对齐方式
        column_widths = {
            '物品': 180,
            '出库数量': 90,
            '出库单价': 95,
            '手续费': 95,
            '总金额': 120,
            '备注': 150
        }
        
        column_aligns = {
            '物品': 'center',  # 文本居中对齐
            '出库数量': 'center',  # 数字居中对齐
            '出库单价': 'center',
            '手续费': 'center',
            '总金额': 'center',
            '备注': 'center'  # 文本居中对齐
        }
        
        # 确保每条数据都有必要的字段，并进行字段映射
        for data in ocr_data_list:
            if isinstance(data, dict):
                # 确保有备注字段
                if 'note' not in data:
                    data['note'] = ''
                if '备注' not in data:
                    data['备注'] = data.get('note', '')
                
                # 字段映射：确保内部字段名和中文字段名都存在
                field_mappings = {
                    'item_name': '物品',
                    'quantity': '出库数量',
                    'unit_price': '出库单价',
                    'fee': '手续费',
                    'total_amount': '总金额',
                    'note': '备注'
                }
                
                for eng_key, cn_key in field_mappings.items():
                    if eng_key in data and cn_key not in data:
                        data[cn_key] = data[eng_key]
                    elif cn_key in data and eng_key not in data:
                        data[eng_key] = data[cn_key]
                
                print(f"映射后的数据: {data}")  # 调试输出
        
        # 使用通用OCR预览对话框组件
        preview_dialog = OCRPreviewDialog(
            parent=self.main_gui.root,
            title="OCR识别数据预览",
            chinese_font=self.chinese_font
        )
        
        # 显示对话框并处理确认后的数据
        preview_dialog.show(
            data_list=ocr_data_list,
            columns=columns,
            column_widths=column_widths,
            column_aligns=column_aligns,
            callback=self.import_confirmed_ocr_data,
            bootstyle="warning"  # 使用出库管理的主题色
        )

    def import_confirmed_ocr_data(self, confirmed_data):
        """导入确认后的OCR数据"""
        success_count = 0
        error_count = 0
        error_messages = []
        
        for data in confirmed_data:
            try:
                # 确保所有必要的字段都存在
                if not isinstance(data, dict):
                    error_count += 1
                    error_messages.append(f"数据格式错误: {data}")
                    continue
                    
                # 获取必要字段，支持中文字段名
                item_name = data.get('item_name') or data.get('物品')
                if not item_name:
                    error_count += 1
                    error_messages.append("缺少物品名称")
                    continue
                    
                quantity = data.get('quantity') or data.get('出库数量')
                if not quantity:
                    error_count += 1
                    error_messages.append(f"{item_name}: 缺少数量")
                    continue
                    
                unit_price = data.get('unit_price') or data.get('出库单价')
                if not unit_price:
                    error_count += 1
                    error_messages.append(f"{item_name}: 缺少单价")
                    continue
                
                # 确保数据类型正确
                try:
                    quantity = int(quantity)
                    unit_price = float(unit_price)
                    fee = float(data.get('fee', 0)) or float(data.get('手续费', 0))  # 手续费可以为空，默认为0
                except (ValueError, TypeError):
                    error_count += 1
                    error_messages.append(f"{item_name}: 数据类型错误")
                    continue
                
                # 使用传入的总金额，如果没有则计算
                total_amount = data.get('total_amount') or data.get('总金额')
                if total_amount is None:
                    total_amount = quantity * unit_price - fee
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 自动减少库存
                success = self.db_manager.decrease_inventory(item_name, quantity)
                if not success:
                    error_count += 1
                    error_messages.append(f"{item_name}: 库存不足，无法出库数量 {quantity}")
                    continue
                    
                self.db_manager.save_stock_out({
                    'item_name': item_name,
                    'transaction_time': now,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'fee': fee,
                    'deposit': 0.0,  # 设置押金固定为0
                    'total_amount': total_amount,
                    'note': data.get('note', '') or data.get('备注', '')  # 支持中文字段名
                })
                
                success_count += 1
            except Exception as e:
                error_count += 1
                error_messages.append(f"处理记录时出错: {str(e)}")
        
        # 刷新界面
        if success_count > 0:
            self.refresh_stock_out()
            self.main_gui.refresh_inventory()
            # 清空图片列表并刷新预览
            self._pending_ocr_images_out.clear()
            self.ocr_preview.clear_images()
            # 使用正确的操作类型常量
            from src.utils.operation_types import OperationType, TabName
            self.main_gui.log_operation(OperationType.BATCH_ADD, TabName.STOCK_OUT, confirmed_data)
        
        # 显示结果消息
        if success_count > 0 and error_count == 0:
            messagebox.showinfo("成功", f"已成功导入{success_count}条出库记录！")
        elif success_count > 0 and error_count > 0:
            messagebox.showwarning("部分成功", 
                                  f"成功导入{success_count}条记录，{error_count}条记录导入失败。\n\n错误详情:\n" + 
                                  "\n".join(error_messages[:5]) + 
                                  (f"\n... 等共{len(error_messages)}个错误" if len(error_messages) > 5 else ""))
        elif success_count == 0:
            messagebox.showerror("导入失败", 
                               f"所有记录导入失败。\n\n错误详情:\n" + 
                               "\n".join(error_messages[:5]) + 
                               (f"\n... 等共{len(error_messages)}个错误" if len(error_messages) > 5 else ""))

    def parse_stock_out_ocr_text(self, text):
        """解析OCR识别后的文本，提取出库相关信息"""
        if not text or not text.strip():
            print("OCR识别文本为空")
            return None
            
        print(f"OCR识别文本：\n{text}")  # 调试输出
        
        lines = text.strip().split('\n')
        item_name = None
        quantity = None
        unit_price = None
        fee = 0
        
        # 扩展关键字匹配范围
        item_keywords = ['品名', '物品', '物品名称', '道具', '道具名称', '商品', '商品名称']
        quantity_keywords = ['数量', '个数', '件数', '数目', '出售数量', '出库数量']
        price_keywords = ['单价', '价格', '单价格', '出售价格', '出售单价', '出库价格', '出库单价', '每个价格']
        fee_keywords = ['手续费', '费用', '交易费', '平台费', '服务费', '税费']
        
        for line in lines:
            # 物品名匹配
            if any(keyword in line for keyword in item_keywords):
                # 扩展匹配模式，支持多种分隔符
                match = re.search(r'[：:]+\s*(.+)$', line)
                if not match:
                    match = re.search(r'[物品名称|品名|道具]+[^：:]*[：:]*\s*(.+)$', line)
                if match:
                    item_name = match.group(1).strip()
                    print(f"匹配到物品名：{item_name}")  # 调试输出
            
            # 数量匹配
            elif any(keyword in line for keyword in quantity_keywords):
                # 扩展匹配模式，支持多种数字格式
                match = re.search(r'[：:]+\s*([\d,]+)', line)
                if not match:
                    match = re.search(r'[数量|个数|件数]+[^：:]*[：:]*\s*([\d,]+)', line)
                if match:
                    qty_str = match.group(1).replace(',', '')
                    quantity = int(qty_str)
                    print(f"匹配到数量：{quantity}")  # 调试输出
            
            # 价格匹配
            elif any(keyword in line for keyword in price_keywords):
                # 扩展匹配模式，支持小数点和千位分隔符
                match = re.search(r'[：:]+\s*([\d,\.]+)', line)
                if not match:
                    match = re.search(r'[单价|价格]+[^：:]*[：:]*\s*([\d,\.]+)', line)
                if match:
                    price_str = match.group(1).replace(',', '')
                    unit_price = float(price_str)
                    print(f"匹配到单价：{unit_price}")  # 调试输出
            
            # 手续费匹配
            elif any(keyword in line for keyword in fee_keywords):
                # 扩展匹配模式，支持小数点和千位分隔符
                match = re.search(r'[：:]+\s*([\d,\.]+)', line)
                if not match:
                    match = re.search(r'[手续费|费用]+[^：:]*[：:]*\s*([\d,\.]+)', line)
                if match:
                    fee_str = match.group(1).replace(',', '')
                    fee = float(fee_str)
                    print(f"匹配到手续费：{fee}")  # 调试输出
        
        # 尝试从文本中提取数字作为备选
        if not item_name or not quantity or not unit_price:
            print("标准匹配失败，尝试备选提取方法")  # 调试输出
            
            # 如果没有找到物品名，尝试从第一行提取
            if not item_name and lines:
                item_name = lines[0].strip()
                print(f"备选物品名：{item_name}")  # 调试输出
            
            # 提取所有数字
            all_numbers = []
            for line in lines:
                # 匹配所有数字（包括小数）
                numbers = re.findall(r'[\d,\.]+', line)
                all_numbers.extend([n.replace(',', '') for n in numbers])
            
            # 转换为浮点数
            all_floats = []
            for n in all_numbers:
                try:
                    all_floats.append(float(n))
                except ValueError:
                    pass
            
            # 按数值大小排序
            all_floats.sort()
            print(f"提取的所有数字：{all_floats}")  # 调试输出
            
            # 如果有至少两个数字，假设较小的是数量，较大的是单价
            if len(all_floats) >= 2 and not quantity:
                for num in all_floats:
                    if num < 100 and not quantity:  # 假设数量通常小于100
                        quantity = int(num)
                        print(f"备选数量：{quantity}")  # 调试输出
            
            if len(all_floats) >= 2 and not unit_price:
                for num in reversed(all_floats):  # 从大到小
                    if num > 100 and not unit_price:  # 假设价格通常大于100
                        unit_price = float(num)
                        print(f"备选单价：{unit_price}")  # 调试输出
        
        if item_name and quantity and unit_price:
            # 计算总金额
            total_amount = quantity * unit_price - fee
            
            result = {
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'fee': fee,
                'total_amount': total_amount,
                'note': ''  # 添加空备注字段
            }
            print(f"OCR识别结果：{result}")  # 调试输出
            return result
        
        print("OCR识别失败，缺少必要信息")  # 调试输出
        return None

    def parse_stock_out_ocr_text_v2(self, text):
        """
        新的出库OCR文本解析方法，专门用于处理特定格式的出库数据
        格式示例：
        已成功售出灵之精火（66）。
        售出单价：1388银两：手续费：4581银两：
        """
        if not text or not text.strip():
            print("OCR识别文本为空")
            return None
            
        print(f"OCR识别文本(V2)：\n{text}")  # 调试输出
        
        # 提取物品名称和数量
        item_match = re.search(r'已成功售出([^（(]+)[（(](\d+)[）)]', text)
        if not item_match:
            print("未匹配到物品名称和数量")
            return None
        
        item_name = item_match.group(1).strip()
        quantity = int(item_match.group(2))
        
        # 提取单价
        price_match = re.search(r'售出单价[：:]\s*(\d+)银两', text)
        unit_price = int(price_match.group(1)) if price_match else 0
        
        # 提取手续费 - 手续费可以为空
        fee_match = re.search(r'手续费[：:]\s*(\d+)银两', text)
        fee = int(fee_match.group(1)) if fee_match else 0
        
        if item_name and quantity and unit_price:
            # 计算总金额
            total_amount = quantity * unit_price - fee
            
            result = {
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'fee': fee,
                'total_amount': total_amount,
                'note': ''  # 添加空备注字段
            }
            print(f"OCR识别结果(V2)：{result}")  # 调试输出
            return result
        
        print("OCR识别失败(V2)，缺少必要信息")  # 调试输出
        return None

    def parse_stock_out_ocr_text_v3(self, text):
        """
        第三种出库OCR文本解析方法，专门用于处理新格式的出库数据
        格式示例：
        已成功售出60诛仙古玉，请在附件中领取已计算相关费用后的收益。 136116
        """
        if not text or not text.strip():
            print("OCR识别文本为空")
            return None
            
        print(f"OCR识别文本(V3)：\n{text}")  # 调试输出
        
        # 提取物品名称和数量
        # 模式: 已成功售出[数量][物品名]，请在附件中领取...
        item_match = re.search(r'已成功售出(\d+)([^，,。]+)[，,。]', text)
        if not item_match:
            print("未匹配到V3格式的物品名称和数量")
            return None
        
        quantity = int(item_match.group(1))
        item_name = item_match.group(2).strip()
        
        # 提取总金额 - 通常是文本末尾的数字
        amount_match = re.search(r'(\d+)\s*$', text)
        total_amount = int(amount_match.group(1)) if amount_match else 0
        
        if item_name and quantity and total_amount:
            # 计算单价（总金额除以数量）
            unit_price = total_amount / quantity if quantity > 0 else 0
            
            result = {
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'fee': 0,  # 手续费默认为0
                'total_amount': total_amount,
                'note': ''  # 备注默认为空
            }
            print(f"OCR识别结果(V3)：{result}")  # 调试输出
            return result
        
        print("OCR识别失败(V3)，缺少必要信息")  # 调试输出
        return None

    def show_stock_out_menu(self, event):
        item = self.stock_out_tree.identify_row(event.y)
        if item:
            if item not in self.stock_out_tree.selection():
                self.stock_out_tree.selection_set(item)
            self.stock_out_menu.post(event.x_root, event.y_root)

    def paste_ocr_import_stock_out(self, event=None):
        """从剪贴板粘贴图片进行OCR识别"""
        if not PIL_AVAILABLE:
            messagebox.showwarning("功能不可用", "PIL图像处理模块不可用，无法使用图片粘贴功能。请确保正确安装Pillow库。")
            return
            
        try:
            # 使用辅助模块获取剪贴板图片
            img = clipboard_helper.get_clipboard_image()
            
            # 验证获取到的是否为图片
            if img is not None:
                self._pending_ocr_images_out.append(img)
                # 使用refresh_ocr_image_preview_out方法刷新图片显示
                self.refresh_ocr_image_preview_out()
                messagebox.showinfo("提示", "图片已添加并显示在下方OCR预览区，请点击'批量识别粘贴图片'按钮进行识别导入。")
            else:
                # 显示详细的错误信息
                clipboard_helper.show_clipboard_error()
        except Exception as e:
            print(f"粘贴图片异常: {str(e)}")  # 调试输出
            messagebox.showerror("错误", f"粘贴图片失败: {str(e)}\n请尝试使用'上传图片'按钮。")
            
    def on_treeview_motion(self, event):
        """处理鼠标在表格上的移动，动态应用悬停高亮效果"""
        # 识别当前鼠标位置的行
        row_id = self.stock_out_tree.identify_row(event.y)
        
        # 如果鼠标离开了上一个高亮行，恢复其原始样式
        if self.last_hover_row and self.last_hover_row != row_id:
            # 获取行的当前标签
            try:
                # 检查行是否仍然存在
                if self.last_hover_row in self.stock_out_tree.get_children():
                    current_tags = list(self.stock_out_tree.item(self.last_hover_row, 'tags'))
                    # 移除悬停标签
                    if 'hovering' in current_tags:
                        current_tags.remove('hovering')
                        self.stock_out_tree.item(self.last_hover_row, tags=current_tags)
            except Exception:
                # 如果行不存在，忽略错误
                pass
                
        # 如果鼠标位于一个有效行上，应用悬停高亮效果
        if row_id and row_id != self.last_hover_row:
            try:
                # 确保行存在
                if row_id in self.stock_out_tree.get_children():
                    # 获取行的当前标签
                    current_tags = list(self.stock_out_tree.item(row_id, 'tags'))
                    # 添加悬停标签
                    if 'hovering' not in current_tags:
                        current_tags.append('hovering')
                        self.stock_out_tree.item(row_id, tags=current_tags)
            except Exception:
                # 如果行不存在，忽略错误
                pass
                
        # 更新上一个高亮行的记录
        self.last_hover_row = row_id if row_id else None

    def toggle_clipboard_monitoring(self):
        """切换剪贴板监听状态"""
        if self.monitoring_clipboard:
            # 正在监听，停止监听
            self.stop_clipboard_monitoring()
        else:
            # 未监听，确认后开始监听
            confirm = messagebox.askyesno(
                "确认操作", 
                "将清除当前剪贴板内容并开始监听剪贴板图片。\n\n点击确认后将自动将检测到的图片添加到预览区，需手动点击批量识别按钮进行识别，是否继续？",
                icon='warning'
            )
            if confirm:
                self.start_clipboard_monitoring()
    
    def start_clipboard_monitoring(self):
        """开始监听剪贴板"""
        # 清除剪贴板内容
        try:
            if clipboard_helper.PYPERCLIP_AVAILABLE:
                import pyperclip
                pyperclip.copy('')
            elif clipboard_helper.WIN32_AVAILABLE:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.CloseClipboard()
        except Exception as e:
            self.status_var.set(f"清除剪贴板失败: {str(e)}")
            
        # 更新UI
        self.monitoring_clipboard = True
        self.monitor_button.config(text="停止监听剪贴板", bootstyle="danger")
        self.status_var.set("剪贴板监听已启动，等待图片...")
        
        # 开始监听循环
        self.check_clipboard()
    
    def stop_clipboard_monitoring(self):
        """停止监听剪贴板"""
        # 取消定时任务
        if self.monitor_job_id is not None:
            self.main_gui.root.after_cancel(self.monitor_job_id)
            self.monitor_job_id = None
            
        # 更新UI
        self.monitoring_clipboard = False
        self.monitor_button.config(text="监听剪贴板", bootstyle="warning")
        self.status_var.set("剪贴板监听已停止")
    
    def check_clipboard(self):
        """检查剪贴板是否有图片"""
        if not self.monitoring_clipboard:
            return
            
        try:
            # 检查剪贴板是否有图片
            img = clipboard_helper.get_clipboard_image()
            if img is not None:
                # 有图片，处理它
                self.process_clipboard_image(img)
                
                # 处理完后清除剪贴板
                try:
                    if clipboard_helper.PYPERCLIP_AVAILABLE:
                        import pyperclip
                        pyperclip.copy('')
                    elif clipboard_helper.WIN32_AVAILABLE:
                        import win32clipboard
                        win32clipboard.OpenClipboard()
                        win32clipboard.EmptyClipboard()
                        win32clipboard.CloseClipboard()
                except Exception as e:
                    self.status_var.set(f"清除剪贴板失败: {str(e)}")
        except Exception as e:
            self.status_var.set(f"检查剪贴板出错: {str(e)}")
            
        # 继续监听，设置下一次检查
        self.monitor_job_id = self.main_gui.root.after(1000, self.check_clipboard)  # 每秒检查一次
    
    def process_clipboard_image(self, img):
        """处理从剪贴板获取的图片"""
        try:
            # 添加到待处理图片列表
            self._pending_ocr_images_out.append(img)
            
            # 更新预览
            self.refresh_ocr_image_preview_out()
            
            # 更新状态
            self.status_var.set("已从剪贴板获取图片并添加到预览区，请点击批量识别按钮进行识别")
            
            # 不再自动调用批量识别
            # self.batch_ocr_import_stock_out()
        except Exception as e:
            self.status_var.set(f"处理剪贴板图片出错: {str(e)}")

    def on_tab_changed(self, event):
        """标签页切换事件处理"""
        # 检查当前标签页是否为出库管理
        current_tab = self.notebook.index("current")
        if current_tab != self.notebook.index(self.notebook.select()):
            # 如果切换到其他标签页，停止剪贴板监听
            if self.monitoring_clipboard:
                self.stop_clipboard_monitoring()
    
    def cleanup(self):
        """清理资源，在窗口关闭时调用"""
        # 停止剪贴板监听
        if self.monitoring_clipboard:
            self.stop_clipboard_monitoring()

    # 其余方法：add_stock_out, refresh_stock_out, edit_stock_out_item, delete_stock_out_item, OCR相关等
    # ...（后续补全所有出库管理相关方法）... 