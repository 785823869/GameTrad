import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog
from PIL import ImageGrab, ImageTk
import io, base64, requests
from datetime import datetime
import tkinter as tk
from src.gui.dialogs import ModalInputDialog
from src.gui.components import OCRPreview

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
        filter_frame = tb.LabelFrame(toolbar, text="筛选", bootstyle="info", padding=5)
        filter_frame.pack(side='left', fill='y', padx=(0, 10))
        
        tb.Label(filter_frame, text="物品:", bootstyle="info").pack(side='left', padx=2)
        
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
        actions_frame = tb.LabelFrame(right_panel, text="操作", bootstyle="success", padding=5)
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
        
        # OCR工具区域
        ocr_tools_frame = tb.LabelFrame(right_panel, text="OCR工具", bootstyle="info", padding=5)
        ocr_tools_frame.pack(fill='x', pady=(0, 10))
        
        tb.Button(ocr_tools_frame, text="上传图片自动入库", command=self.upload_ocr_import_stock_in,
                bootstyle="info").pack(fill='x', pady=2, ipady=2)
        
        tb.Button(ocr_tools_frame, text="批量识别粘贴图片", command=self.batch_ocr_import_stock_in,
                bootstyle="info-outline").pack(fill='x', pady=2, ipady=2)
        
        # 使用键盘快捷键提示
        shortcut_frame = tb.Frame(right_panel, bootstyle="light")
        shortcut_frame.pack(fill='x', pady=(0, 5))
        
        tb.Label(shortcut_frame, text="快捷键: Ctrl+V 粘贴图片", bootstyle="secondary").pack(anchor='w')
        
        # OCR预览区域
        ocr_frame = tb.LabelFrame(right_panel, text="OCR图片预览", bootstyle="secondary", padding=5)
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
        edit_win.minsize(420, 420)
        edit_win.configure(bg='#f4f8fb')
        
        # 设置窗口图标和样式
        edit_win.iconbitmap(self.main_gui.root.iconbitmap()) if hasattr(self.main_gui.root, 'iconbitmap') and callable(self.main_gui.root.iconbitmap) else None
        
        style = tb.Style()
        style.configure('Edit.TLabel', font=(self.chinese_font, 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=(self.chinese_font, 11))
        style.configure('Edit.TButton', font=(self.chinese_font, 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        
        # 创建内容框架
        content_frame = tb.Frame(edit_win, bootstyle="light")
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        
        # 字段标题和数据类型
        labels = ["物品", "时间", "数量", "花费", "均价", "备注"]
        types = [str, str, int, float, float, str]
        entries = []
        error_labels = []
        
        # 创建字段
        for i, (label, val, typ) in enumerate(zip(labels, values, types)):
            tb.Label(content_frame, text=label+":", bootstyle="info").grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
                
            entry = tb.Entry(content_frame, validate='key', validatecommand=vcmd, bootstyle="info") if vcmd else tb.Entry(content_frame, bootstyle="info")
            entry.insert(0, val)
            entry.grid(row=i*2, column=1, padx=12, pady=4, sticky='ew')
            entries.append(entry)
            
            err = tb.Label(content_frame, text="", foreground="red", bootstyle="danger")
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
        for i, img in enumerate(self._pending_ocr_images):
            self.ocr_preview.add_image(img, index=i)

    def delete_ocr_image(self, idx):
        if 0 <= idx < len(self._pending_ocr_images):
            del self._pending_ocr_images[idx]
            self.refresh_ocr_image_preview()

    def upload_ocr_import_stock_in(self):
        """上传图片进行OCR识别导入"""
        file_path = filedialog.askopenfilename(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        try:
            from PIL import Image
            img = Image.open(file_path)
            self._pending_ocr_images.append(img)
            # 使用新组件添加图片
            self.ocr_preview.add_image(img)
            messagebox.showinfo("提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def batch_ocr_import_stock_in(self):
        """批量OCR识别处理"""
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
                data = self.parse_stock_in_ocr_text(text)
                if data:
                    all_data.append(data)
            except Exception as e:
                messagebox.showerror("错误", f"OCR识别失败: {e}")
        
        if all_data:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for data in all_data:
                item_name = data.get('item_name')
                quantity = data.get('quantity')
                cost = data.get('cost')
                avg_cost = cost / quantity if quantity > 0 else 0
                self.db_manager.save_stock_in({
                    'item_name': item_name,
                    'transaction_time': now,
                    'quantity': quantity,
                    'cost': cost,
                    'avg_cost': avg_cost,
                    'deposit': 0.0,
                    'note': ''
                })
                self.db_manager.increase_inventory(item_name, quantity, avg_cost)
            self.refresh_stock_in()
            self.main_gui.refresh_inventory()
            # 清空图片列表并刷新预览
            self._pending_ocr_images.clear()
            self.ocr_preview.clear_images()
            self.main_gui.log_operation('批量修改', '入库管理', all_data)
            messagebox.showinfo("成功", f"已成功导入{len(all_data)}条入库记录！")
        else:
            messagebox.showwarning("警告", "未能识别有效的入库记录！")

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
                'cost': cost
            }
        return None

    def show_stock_in_menu(self, event):
        item = self.stock_in_tree.identify_row(event.y)
        if item:
            if item not in self.stock_in_tree.selection():
                self.stock_in_tree.selection_set(item)
            self.stock_in_menu.post(event.x_root, event.y_root)

    def paste_ocr_import_stock_in(self, event=None):
        """从剪贴板粘贴图片进行OCR识别"""
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self._pending_ocr_images.append(img)
                # 使用新组件添加图片
                self.ocr_preview.add_image(img)
                messagebox.showinfo("提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
            else:
                messagebox.showinfo("提示", "剪贴板中没有图片")
        except Exception as e:
            messagebox.showerror("错误", f"粘贴图片失败: {e}")
            
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