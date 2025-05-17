import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog
# PIL导入添加错误处理，但是将ImageGrab移到方法内部导入
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
from src.gui.dialogs import ModalInputDialog
from src.gui.components import OCRPreview, OCRPreviewDialog
from src.utils import clipboard_helper

class StockInTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        self._pending_ocr_images = []
        
        # 设置中文字体
        self.chinese_font = main_gui.chinese_font
        
        # 创建样式
        self.setup_styles()
        
        self.create_tab()
        
    def setup_styles(self):
        """设置自定义样式"""
        style = tb.Style()
        
        # 表格样式
        style.configure("StockIn.Treeview", 
                      rowheight=32,  # 增加行高 
                      font=(self.chinese_font, 10),
                      background="#ffffff",
                      fieldbackground="#ffffff",
                      foreground="#2c3e50")
                      
        style.configure("StockIn.Treeview.Heading", 
                      font=(self.chinese_font, 10, "bold"),
                      background="#e0e6ed",
                      foreground="#2c3e50")
        
        # 移除表格行鼠标悬停效果的style.map设置，改为使用标签和事件处理
        style.map('StockIn.Treeview', 
                background=[('selected', '#52b9d8')])  # 只保留选中效果
        
        # 按钮样式
        style.configure("StockIn.TButton", 
                      font=(self.chinese_font, 11),
                      foreground="#ffffff")
        
        # 标签样式
        style.configure("StockIn.TLabel", 
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
            stock_in_frame = self.notebook
        else:
            # 旧UI结构，notebook是Notebook
            stock_in_frame = tb.Frame(self.notebook, padding=10, bootstyle="light")
            self.notebook.add(stock_in_frame, text="入库管理")
        
        # 创建上方的工具栏
        toolbar = tb.Frame(stock_in_frame, bootstyle="light")
        toolbar.pack(fill='x', pady=(0, 5))
        
        # 过滤器区域
        filter_frame = tb.LabelFrame(toolbar, text="筛选", style="Unified.TLabelframe", padding=5)
        filter_frame.pack(side='left', fill='y', padx=(0, 10))
        
        tb.Label(filter_frame, text="物品:", style="Unified.TLabel").pack(side='left', padx=2)
        
        self.stock_in_filter_var = tb.StringVar()
        filter_entry = tb.Entry(filter_frame, textvariable=self.stock_in_filter_var, width=12, bootstyle="info")
        filter_entry.pack(side='left', padx=2)
        filter_entry.bind("<Return>", lambda e: self.refresh_stock_in())
        
        tb.Button(filter_frame, text="筛选", command=self.refresh_stock_in, bootstyle="info-outline").pack(side='left', padx=2)
        tb.Button(filter_frame, text="清除", command=lambda: [self.stock_in_filter_var.set(""), self.refresh_stock_in()], bootstyle="secondary-outline").pack(side='left', padx=2)
        
        # 主区域分割
        main_area = tb.Frame(stock_in_frame, bootstyle="light")
        main_area.pack(fill='both', expand=True)
        
        # 表格区域
        table_frame = tb.Frame(main_area, bootstyle="light")
        table_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # 表格和滚动条
        columns = ('物品', '当前时间', '入库数量', '入库花费', '入库均价', '备注')
        
        # 设置表头和列宽
        column_widths = {
            '物品': 180,     # 加宽物品名称列
            '当前时间': 160,
            '入库数量': 90,
            '入库花费': 110,
            '入库均价': 90,
            '备注': 180      # 加宽备注列
        }
        
        # 设置列对齐方式
        column_aligns = {
            '物品': 'w',     # 文本左对齐
            '当前时间': 'center',
            '入库数量': 'e',  # 数字右对齐
            '入库花费': 'e',
            '入库均价': 'e',
            '备注': 'w'
        }
        
        # 创建表格
        self.stock_in_tree = tb.Treeview(table_frame, columns=columns, show='headings', 
                                        height=16, bootstyle="info", style="StockIn.Treeview")
        
        for col in columns:
            self.stock_in_tree.heading(col, text=col, anchor='center')
            width = column_widths.get(col, 120)
            align = column_aligns.get(col, 'center')
            self.stock_in_tree.column(col, width=width, anchor=align)
            
        # 滚动条
        scrollbar = tb.Scrollbar(table_frame, orient="vertical", command=self.stock_in_tree.yview, bootstyle="info-round")
        self.stock_in_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滚动条
        self.stock_in_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        
        # 配置表格样式
        self.stock_in_tree.tag_configure('evenrow', background='#f0f7fa')  # 更柔和的蓝灰色
        self.stock_in_tree.tag_configure('oddrow', background='#ffffff')
        self.stock_in_tree.tag_configure('total', background='#fff8dc', font=(self.chinese_font, 11, 'bold'))
        # 添加悬停高亮标签
        self.stock_in_tree.tag_configure('hovering', background='#e9f5fa')  # 鼠标悬停效果
        
        # 绑定鼠标移动事件
        self.stock_in_tree.bind("<Motion>", self.on_treeview_motion)
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
            text="添加入库记录", 
            command=self.show_add_stock_in_dialog,
            bootstyle="success"
        ).pack(fill='x', pady=5, ipady=5)
        
        tb.Button(actions_frame, text="刷新入库记录", command=self.refresh_stock_in, 
                bootstyle="success-outline").pack(fill='x', pady=2, ipady=2)
        
        # OCR工具区域 - 使用统一样式
        ocr_tools_frame = tb.LabelFrame(right_panel, text="OCR工具", style="Unified.TLabelframe", padding=5)
        ocr_tools_frame.pack(fill='x', pady=(0, 10))
        
        tb.Button(ocr_tools_frame, text="上传图片自动入库", command=self.upload_ocr_import_stock_in,
                bootstyle="info").pack(fill='x', pady=2, ipady=2)
        
        tb.Button(ocr_tools_frame, text="批量识别粘贴图片", command=self.batch_ocr_import_stock_in,
                bootstyle="info-outline").pack(fill='x', pady=2, ipady=2)
        
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
        self.ocr_preview.set_callback(self.delete_ocr_image)
        
        # 绑定Ctrl+V快捷键
        right_panel.bind_all('<Control-v>', self.paste_ocr_import_stock_in)
        
        # 右键菜单
        self.stock_in_menu = tb.Menu(self.stock_in_tree, tearoff=0)
        self.stock_in_menu.add_command(label="编辑", command=lambda: self.edit_stock_in_item(None))
        self.stock_in_menu.add_command(label="删除", command=self.delete_stock_in_item)
        self.stock_in_menu.add_separator()
        self.stock_in_menu.add_command(label="复制物品名", command=lambda: self.copy_item_name())
        
        # 绑定右键菜单
        self.stock_in_tree.bind("<Button-3>", self.show_stock_in_menu)
        
        # 支持Ctrl+A全选和双击编辑
        self.stock_in_tree.bind('<Control-a>', lambda e: [self.stock_in_tree.selection_set(self.stock_in_tree.get_children()), 'break'])
        self.stock_in_tree.bind("<Double-1>", self.edit_stock_in_item)
        
        # 底部状态栏
        status_frame = tb.Frame(stock_in_frame, bootstyle="light")
        status_frame.pack(fill='x', side='bottom', pady=(5, 0))
        
        self.status_var = tb.StringVar(value="就绪")
        status_label = tb.Label(status_frame, textvariable=self.status_var, bootstyle="secondary")
        status_label.pack(side='left')

    def show_add_stock_in_dialog(self):
        """显示添加入库记录的模态对话框"""
        fields = [
            ("物品", "item_name", "str"),
            ("数量", "quantity", "int"),
            ("花费", "cost", "float"),
            ("备注", "note", "str")
        ]
        
        ModalInputDialog(
            self.main_gui.root,
            "添加入库记录",
            fields,
            self.process_add_stock_in
        )
    
    def process_add_stock_in(self, values):
        """处理添加入库记录的回调"""
        try:
            item = values["item_name"]
            quantity = values["quantity"]
            cost = values["cost"]
            note = values["note"]
            
            avg_cost = cost / quantity if quantity > 0 else 0
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.db_manager.save_stock_in({
                'item_name': item,
                'transaction_time': now,
                'quantity': quantity,
                'cost': cost,
                'avg_cost': avg_cost,
                'deposit': 0.00,
                'note': note if note is not None else ''
            })
            
            self.db_manager.increase_inventory(item, quantity, avg_cost)
            self.refresh_stock_in()
            
            # 确保库存页面也更新
            if hasattr(self.main_gui, 'inventory_tab') and self.main_gui.inventory_tab:
                self.main_gui.inventory_tab.refresh_inventory()
            self.main_gui.refresh_inventory()
            
            self.main_gui.log_operation('修改', '入库管理')
            messagebox.showinfo("成功", "入库记录添加成功！")
            self.status_var.set(f"已添加: {item} x {quantity}")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            self.status_var.set(f"添加记录失败: {str(e)}")

    def refresh_stock_in(self):
        for item in self.stock_in_tree.get_children():
            self.stock_in_tree.delete(item)
            
        self.status_var.set("正在加载数据...")
        stock_in_data = self.db_manager.get_stock_in()
        filter_text = self.stock_in_filter_var.get().strip()
        filtered = []
        
        for item in stock_in_data:
            try:
                _, item_name, transaction_time, quantity, cost, avg_cost, note, *_ = item
            except Exception as e:
                messagebox.showerror("数据结构异常", f"入库数据结构异常: {e}\n请检查表结构与代码字段一致性。\nitem={item}")
                continue
            if not filter_text or filter_text in str(item_name):
                filtered.append((item_name, transaction_time, quantity, cost, avg_cost, note))
                
        total = [0, 0, 0]  # 数量、花费、均价合计
        
        for i, (item_name, transaction_time, quantity, cost, avg_cost, note) in enumerate(filtered):
            # 设置交替行颜色
            row_tags = ('evenrow',) if i % 2 == 0 else ('oddrow',)
            
            # 格式化数据以提高可读性
            quantity_display = f"{int(quantity):,}" if quantity else "0"
            cost_display = f"{int(round(cost)):,}" if cost else "0"
            # 将均价显示修改为整数
            avg_cost_display = f"{int(round(avg_cost)):,}" if avg_cost else "0"
            
            self.stock_in_tree.insert('', 'end', values=(
                item_name,
                transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                quantity_display,
                cost_display,
                avg_cost_display,
                note if note is not None else ''
            ), tags=row_tags)
            
            try:
                total[0] += int(quantity)
                total[1] += int(round(cost))
                total[2] += int(round(avg_cost))
            except:
                pass
                
        # 合计行
        if filter_text and filtered:
            self.stock_in_tree.insert('', 'end', values=(
                '合计', '', 
                f"{total[0]:,}", 
                f"{total[1]:,}", 
                f"{total[2]//len(filtered):,}" if len(filtered) > 0 else "0", 
                ''
            ), tags=('total',))
            
        self.status_var.set(f"共 {len(filtered)} 条记录  |  上次更新: {datetime.now().strftime('%H:%M:%S')}")

    def edit_stock_in_item(self, event):
        if event:  # 如果是通过双击事件触发
            item_id = self.stock_in_tree.identify_row(event.y)
        else:  # 如果是通过右键菜单触发
            selected = self.stock_in_tree.selection()
            if not selected:
                return
            item_id = selected[0]
            
        if not item_id:
            return
            
        values = self.stock_in_tree.item(item_id)['values']
        
        # 使用ttkbootstrap创建更美观的编辑窗口
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑入库记录")
        edit_win.minsize(420, 500)
        edit_win.configure(bg='#f0f0f0')
        
        # 设置窗口图标和样式
        edit_win.iconbitmap(self.main_gui.root.iconbitmap()) if hasattr(self.main_gui.root, 'iconbitmap') and callable(self.main_gui.root.iconbitmap) else None
        
        style = tb.Style()
        style.configure('Edit.TLabel', font=(self.chinese_font, 11), background='#f0f0f0')
        style.configure('Edit.TEntry', font=(self.chinese_font, 11))
        style.configure('Edit.TButton', font=(self.chinese_font, 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        style.configure('Edit.TFrame', background='#f0f0f0')
        
        # 创建内容框架
        content_frame = tb.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        
        # 字段标题和数据类型
        labels = ["物品", "时间", "数量", "花费", "均价", "备注"]
        types = [str, str, int, float, float, str]
        entries = []
        error_labels = []
        
        # 创建字段
        for i, (label, val, typ) in enumerate(zip(labels, values, types)):
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
                
            entry = tb.Entry(content_frame, validate='key', validatecommand=vcmd, bootstyle="info") if vcmd else tb.Entry(content_frame, bootstyle="info")
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
            except Exception:
                error_labels[2].config(text="数量/花费/均价必须为数字")
                entries[2].focus_set()
                return
                
            if not messagebox.askyesno("确认", "确定要保存修改吗？"):
                return
                
            self.db_manager.delete_stock_in(values[0], values[1])
            self.db_manager.save_stock_in({
                'item_name': new_vals[0],
                'transaction_time': new_vals[1],
                'quantity': new_vals[2],
                'cost': new_vals[3],
                'avg_cost': new_vals[4],
                'note': new_vals[5]
            })
            
            self.refresh_stock_in()
            edit_win.destroy()
            self.main_gui.log_operation('修改', '入库管理', {'old': values, 'new': new_vals})
            self.status_var.set(f"已编辑: {new_vals[0]} 记录")
            
        # 按钮区域
        button_frame = tb.Frame(edit_win, bootstyle="light")
        button_frame.pack(side='bottom', fill='x', pady=20)
        
        # 创建按钮
        cancel_btn = tb.Button(button_frame, text="取消", command=edit_win.destroy, bootstyle="secondary")
        cancel_btn.pack(side='left', padx=20, ipadx=20)
        
        save_btn = tb.Button(button_frame, text="保存", command=save, bootstyle="success")
        save_btn.pack(side='right', padx=20, ipadx=20)

    def delete_stock_in_item(self):
        selected_items = self.stock_in_tree.selection()
        if not selected_items:
            return
            
        names = [self.stock_in_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下入库记录吗？\n" + "，".join(str(n) for n in names)
        
        if messagebox.askyesno("确认删除", msg):
            for item in selected_items:
                values = self.stock_in_tree.item(item)['values']
                if len(values) >= 2:
                    try:
                        self.db_manager.delete_stock_in(values[0], values[1])
                    except Exception as e:
                        messagebox.showerror("删除失败", f"删除记录时发生错误: {str(e)}")
                        
            self.refresh_stock_in()
            self.status_var.set(f"已删除 {len(selected_items)} 条记录")
            
    def copy_item_name(self):
        """复制选中的物品名称到剪贴板"""
        selected_items = self.stock_in_tree.selection()
        if not selected_items:
            return
        
        item_name = self.stock_in_tree.item(selected_items[0])['values'][0]
        self.notebook.clipboard_clear()
        self.notebook.clipboard_append(item_name)
        self.status_var.set(f"已复制: {item_name}")

    def refresh_ocr_image_preview(self):
        self.ocr_preview.clear_images()
        for img in self._pending_ocr_images:
            self.ocr_preview.add_image(img)

    def delete_ocr_image(self, idx):
        if 0 <= idx < len(self._pending_ocr_images):
            del self._pending_ocr_images[idx]
            self.refresh_ocr_image_preview()

    def upload_ocr_import_stock_in(self):
        """上传图片进行OCR识别导入"""
        if not PIL_AVAILABLE:
            messagebox.showwarning("功能不可用", "PIL图像处理模块不可用，无法使用图片上传功能。请确保正确安装Pillow库。")
            return
            
        file_path = filedialog.askopenfilename(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        try:
            # 确保Image已正确导入
            img = Image.open(file_path)
            self._pending_ocr_images.append(img)
            # 使用refresh_ocr_image_preview方法刷新图片显示
            self.refresh_ocr_image_preview()
            messagebox.showinfo("提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def parse_stock_in_ocr_text(self, text):
        """解析OCR识别后的文本，提取入库相关信息"""
        import re
        lines = text.strip().split('\n')
        item_name = None
        quantity = None
        cost = None
        for line in lines:
            if '品名' in line or '物品' in line:
                match = re.search(r'[：:]\s*(.+)$', line)
                if match:
                    item_name = match.group(1).strip()
            elif '数量' in line:
                match = re.search(r'[：:]\s*(\d+)', line)
                if match:
                    quantity = int(match.group(1))
            elif '价格' in line or '金额' in line or '花费' in line:
                match = re.search(r'[：:]\s*(\d+)', line)
                if match:
                    cost = float(match.group(1))
        if item_name and quantity and cost:
            return {
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': cost
            }
        return None
        
    def parse_stock_in_ocr_text_v2(self, text):
        """
        新的入库OCR文本解析方法，专门用于处理特定格式的入库数据
        格式示例：
        系统系统系统系统系统系统系统系统
        失去了银两×262164 失去了银两×33314 失去了银两×24598 失去了银两×4600
        获得了获得了获得了
        至纯精华×121 至纯精华×15 至纯精华×11
        获得了
        至纯精华×2
        """
        if not text or not text.strip():
            print("OCR识别文本为空")
            return None
            
        print(f"OCR识别文本(V2)：\n{text}")  # 调试输出
        
        import re
        
        # 预处理文本，移除多余的空格
        text = ' '.join(text.split())
        
        # 提取所有银两×后面的数值（支持多种格式）
        cost_patterns = [
            r'失去了银两×(\d+)',  # 先匹配最长的模式
            r'银两×(\d+)',
            r'失去了(\d+)银两',
            r'花费(\d+)银两',
            r'花费了(\d+)银两'
        ]
        
        cost_matches = []
        # 创建一个集合来跟踪已经匹配到的花费值，避免重复
        matched_costs = set()
        for pattern in cost_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in matched_costs:  # 只添加未匹配过的值
                    matched_costs.add(match)
                    cost_matches.append(match)
                    print(f"匹配到花费: {match}")
        
        # 如果没有匹配到任何花费，打印一条调试信息
        if not cost_matches:
            print("未匹配到任何花费值")
        
        # 提取所有至纯精华×后面的数值（支持多种格式）
        item_name = "至纯精华"  # 固定物品名称
        item_patterns = [
            f"获得了{item_name}×(\\d+)",  # 先匹配最长的模式
            f"{item_name}×(\\d+)",
            f"获得{item_name}×(\\d+)",
            f"获得了{item_name}(\\d+)",
            f"获得{item_name}(\\d+)"
        ]
        
        item_matches = []
        # 创建一个集合来跟踪已经匹配到的数量值，避免重复
        matched_quantities = set()
        for pattern in item_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in matched_quantities:  # 只添加未匹配过的值
                    matched_quantities.add(match)
                    item_matches.append(match)
                    print(f"匹配到物品数量: {match}")
        
        # 如果没有匹配到任何物品数量，打印一条调试信息
        if not item_matches:
            print("未匹配到任何物品数量")
        
        # 如果没有找到物品或花费，返回None
        if not cost_matches or not item_matches:
            print("未找到足够的物品和花费信息")
            return None
        
        try:
            # 计算总花费 - 所有银两×后面数值的总和
            total_cost = sum(int(cost) for cost in cost_matches)
            
            # 计算总数量 - 所有至纯精华×后面数值的总和
            total_quantity = sum(int(qty) for qty in item_matches)
            
            # 计算均价
            avg_price = total_cost / total_quantity if total_quantity > 0 else 0
            
            print(f"解析结果: 物品={item_name}, 数量={total_quantity}, 花费={total_cost}, 均价={avg_price}")
            
            # 返回结构化数据，确保与OCRPreviewDialog兼容
            result = {
                'item_name': item_name,
                'quantity': total_quantity,
                'cost': total_cost,  # 总花费
                'avg_cost': avg_price,
                'unit_price': avg_price  # 添加unit_price字段以兼容预览表格
            }
            
            return result
        except Exception as e:
            print(f"处理OCR数据时出错: {e}")
            return None
        
    def batch_ocr_import_stock_in(self):
        """批量OCR识别处理"""
        # 从新组件获取图片列表
        ocr_images = self.ocr_preview.get_images()
        if not ocr_images:
            messagebox.showinfo("提示", "请先添加图片")
            return
        
        # 显示处理中提示
        self.status_var.set("正在进行OCR识别，请稍候...")
        self.main_gui.root.update()
        
        all_data = []
        error_count = 0
        
        for i, img in enumerate(ocr_images):
            try:
                # 更新状态
                self.status_var.set(f"正在处理第 {i+1}/{len(ocr_images)} 张图片...")
                self.main_gui.root.update()
                
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
                    print(f"图片 {i+1} OCR识别返回空文本")
                    error_count += 1
                    continue
                
                # 使用入库专用的OCR解析方法
                data = self.parse_stock_in_ocr_text_v2(text)
                
                # 如果专用方法失败，回退到通用方法
                if not data:
                    data = self.parse_stock_in_ocr_text(text)
                    
                if data:
                    all_data.append(data)
                else:
                    print(f"图片 {i+1} 无法解析出有效数据")
                    error_count += 1
            except Exception as e:
                error_count += 1
                print(f"处理图片 {i+1} 时出错: {e}")
                messagebox.showerror("错误", f"OCR识别失败: {e}")
        
        # 恢复状态
        self.status_var.set("就绪")
        
        if all_data:
            # 显示OCR识别数据预览窗口
            self.show_ocr_preview_dialog(all_data)
            
            # 如果有错误，显示部分成功的提示
            if error_count > 0:
                messagebox.showinfo("部分成功", 
                                   f"成功识别 {len(all_data)} 张图片，{error_count} 张图片识别失败。")
        else:
            messagebox.showwarning("警告", "未能识别有效的入库记录！请检查图片质量或内容格式。")

    def show_ocr_preview_dialog(self, ocr_data_list):
        """显示OCR识别数据预览窗口（表格形式）"""
        # 定义列 - 使用与入库管理一致的字段名
        columns = ('物品', '入库数量', '入库花费', '入库均价', '备注')
        
        # 设置列宽和对齐方式
        column_widths = {
            '物品': 180,
            '入库数量': 90,
            '入库花费': 120,
            '入库均价': 120,
            '备注': 120
        }
        
        column_aligns = {
            '物品': 'w',  # 文本左对齐
            '入库数量': 'e',  # 数字右对齐
            '入库花费': 'e',
            '入库均价': 'e',
            '备注': 'w'
        }
        
        # 转换数据格式，确保与表格列匹配
        display_data = []
        for data in ocr_data_list:
            # 确保所有必要的字段都存在
            item_name = data.get('item_name', '')
            quantity = data.get('quantity', 0)
            
            # 确保cost是总花费，而不是单价
            cost = data.get('cost', 0)
            if cost == 0 and 'unit_price' in data:
                # 如果没有直接的cost字段，使用单价乘以数量计算总花费
                cost = data.get('unit_price', 0) * quantity
                # 更新原始数据中的cost字段
                data['cost'] = cost
                
            avg_cost = data.get('avg_cost', 0)
            
            # 如果缺少均价字段，计算它
            if avg_cost == 0 and quantity > 0:
                avg_cost = cost / quantity
                data['avg_cost'] = avg_cost
                
            # 确保有备注字段
            note = data.get('note', '')
            data['note'] = note
            
            # 将均价向下取整为整数
            avg_cost_int = int(round(avg_cost))
                
            display_data.append({
                '物品': item_name,
                '入库数量': quantity,
                '入库花费': cost,  # 确保这是总花费
                '入库均价': avg_cost_int,  # 使用取整后的均价
                '备注': note,
                # 同时添加内部字段名，确保数据验证能通过
                'item_name': item_name,
                'quantity': quantity,
                'cost': cost,
                'avg_cost': avg_cost,  # 保留原始精度用于计算
                'note': note
            })
        
        # 使用通用OCR预览对话框组件
        preview_dialog = OCRPreviewDialog(
            parent=self.main_gui.root,
            title="OCR识别数据预览",
            chinese_font=self.chinese_font
        )
        
        # 显示对话框并处理确认后的数据
        preview_dialog.show(
            data_list=display_data,
            columns=columns,
            column_widths=column_widths,
            column_aligns=column_aligns,
            callback=self.import_confirmed_ocr_data,
            bootstyle="info"  # 使用入库管理的主题色
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
                    
                # 获取必要字段，支持新的中文字段名
                item_name = data.get('item_name') or data.get('物品')
                if not item_name:
                    error_count += 1
                    error_messages.append("缺少物品名称")
                    continue
                    
                quantity = data.get('quantity') or data.get('入库数量')
                if not quantity:
                    error_count += 1
                    error_messages.append(f"{item_name}: 缺少数量")
                    continue
                
                # 确保数据类型正确
                try:
                    quantity = int(quantity)
                except (ValueError, TypeError):
                    error_count += 1
                    error_messages.append(f"{item_name}: 数量必须是整数")
                    continue
                
                # 获取花费 - 支持中文字段名
                cost = data.get('cost') or data.get('入库花费')
                if cost is None:
                    error_count += 1
                    error_messages.append(f"{item_name}: 缺少花费")
                    continue
                
                try:
                    cost = float(cost)
                except (ValueError, TypeError):
                    error_count += 1
                    error_messages.append(f"{item_name}: 花费必须是数字")
                    continue
                
                # 获取均价 - 支持中文字段名
                avg_cost = data.get('avg_cost') or data.get('入库均价')
                if avg_cost is None:
                    avg_cost = cost / quantity if quantity > 0 else 0
                else:
                    try:
                        avg_cost = float(avg_cost)
                    except (ValueError, TypeError):
                        error_count += 1
                        error_messages.append(f"{item_name}: 均价必须是数字")
                        continue
                
                # 获取备注 - 支持中文字段名
                note = data.get('note') or data.get('备注', '')
                    
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 保存入库记录
                self.db_manager.save_stock_in({
                    'item_name': item_name,
                    'transaction_time': now,
                    'quantity': quantity,
                    'cost': int(cost),  # 确保花费是整数
                    'avg_cost': avg_cost,
                    'deposit': data.get('deposit', 0.00),
                    'note': note
                })
                
                # 更新库存
                self.db_manager.increase_inventory(item_name, quantity, avg_cost)
                
                success_count += 1
            except Exception as e:
                error_count += 1
                error_messages.append(f"处理记录时出错: {str(e)}")
        
        # 刷新界面
        if success_count > 0:
            self.refresh_stock_in()
            self.main_gui.refresh_inventory()
            # 清空图片列表并刷新预览
            self._pending_ocr_images.clear()
            self.ocr_preview.clear_images()
            self.main_gui.log_operation('批量修改', '入库管理', confirmed_data)
        
        # 显示结果消息
        if success_count > 0 and error_count == 0:
            messagebox.showinfo("成功", f"已成功导入{success_count}条入库记录！")
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

    def show_stock_in_menu(self, event):
        item = self.stock_in_tree.identify_row(event.y)
        if item:
            if item not in self.stock_in_tree.selection():
                self.stock_in_tree.selection_set(item)
            self.stock_in_menu.post(event.x_root, event.y_root)

    def paste_ocr_import_stock_in(self, event=None):
        """从剪贴板粘贴图片进行OCR识别"""
        if not PIL_AVAILABLE:
            messagebox.showwarning("功能不可用", "PIL图像处理模块不可用，无法使用图片粘贴功能。请确保正确安装Pillow库。")
            return
            
        try:
            # 使用辅助模块获取剪贴板图片
            img = clipboard_helper.get_clipboard_image()
            
            # 验证获取到的是否为图片
            if img is not None:
                self._pending_ocr_images.append(img)
                # 使用refresh_ocr_image_preview方法刷新图片显示
                self.refresh_ocr_image_preview()
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
        row_id = self.stock_in_tree.identify_row(event.y)
        
        # 如果鼠标离开了上一个高亮行，恢复其原始样式
        if self.last_hover_row and self.last_hover_row != row_id:
            # 获取行的当前标签
            current_tags = list(self.stock_in_tree.item(self.last_hover_row, 'tags'))
            # 移除悬停标签
            if 'hovering' in current_tags:
                current_tags.remove('hovering')
                self.stock_in_tree.item(self.last_hover_row, tags=current_tags)
                
        # 如果鼠标位于一个有效行上，应用悬停高亮效果
        if row_id and row_id != self.last_hover_row:
            # 获取行的当前标签
            current_tags = list(self.stock_in_tree.item(row_id, 'tags'))
            # 添加悬停标签
            if 'hovering' not in current_tags:
                current_tags.append('hovering')
                self.stock_in_tree.item(row_id, tags=current_tags)
                
        # 更新上一个高亮行的记录
        self.last_hover_row = row_id if row_id else None
    # ...后续补全所有入库管理相关方法... 