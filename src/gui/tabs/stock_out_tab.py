import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog as fd
from PIL import ImageGrab, ImageTk
import io, base64, requests
from datetime import datetime
import tkinter as tk
import re
from src.gui.dialogs import ModalInputDialog
from src.gui.components import OCRPreview

class StockOutTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        self._pending_ocr_images_out = []
        self.create_tab()

    def create_tab(self):
        # 检查是否在新UI结构中运行
        if isinstance(self.notebook, tk.Frame) or isinstance(self.notebook, tb.Frame):
            # 新UI结构，notebook实际上是框架
            stock_out_frame = self.notebook
        else:
            # 旧UI结构，notebook是Notebook
            stock_out_frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(stock_out_frame, text="出库管理")
        
        columns = ('物品', '当前时间', '数量', '单价', '手续费', '总金额', '备注')
        self.stock_out_tree = ttk.Treeview(stock_out_frame, columns=columns, show='headings', height=16)
        for col in columns:
            self.stock_out_tree.heading(col, text=col, anchor='center')
            self.stock_out_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(stock_out_frame, orient="vertical", command=self.stock_out_tree.yview)
        self.stock_out_tree.configure(yscrollcommand=scrollbar.set)
        self.stock_out_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        self.stock_out_tree.tag_configure('total', background='#ffe066', font=('微软雅黑', 11, 'bold'))
        right_panel = ttk.Frame(stock_out_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        self.stock_out_filter_var = tb.StringVar()
        filter_row = ttk.Frame(right_panel)
        filter_row.pack(fill='x', pady=2)
        ttk.Label(filter_row, text="物品筛选:").pack(side='left')
        filter_entry = ttk.Entry(filter_row, textvariable=self.stock_out_filter_var, width=12)
        filter_entry.pack(side='left', padx=2)
        ttk.Button(filter_row, text="筛选", command=self.refresh_stock_out).pack(side='left', padx=2)
        
        # 添加记录按钮 - 替换原来的嵌入式表单
        ttk.Button(
            right_panel, 
            text="添加出库记录", 
            command=self.show_add_stock_out_dialog,
            style="primary.TButton"
        ).pack(fill='x', pady=10, ipady=8)
        
        ttk.Button(right_panel, text="刷新出库记录", command=self.refresh_stock_out).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="上传图片自动识别导入", command=self.upload_ocr_import_stock_out).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="批量识别粘贴图片", command=self.batch_ocr_import_stock_out).pack(fill='x', pady=(0, 10), ipady=4)

        # 使用新的OCRPreview组件替换原来的预览区
        ocr_frame = ttk.LabelFrame(right_panel, text="OCR图片预览")
        ocr_frame.pack(fill='x', pady=5, padx=2)
        
        # 创建OCR预览组件
        self.ocr_preview = OCRPreview(ocr_frame, height=120)
        self.ocr_preview.pack(fill='both', expand=True, padx=2, pady=5)
        self.ocr_preview.set_callback(self.delete_ocr_image_out)
        
        # 绑定Ctrl+V快捷键
        right_panel.bind_all('<Control-v>', self.paste_ocr_import_stock_out)
        
        self.stock_out_menu = tb.Menu(self.stock_out_tree, tearoff=0)
        self.stock_out_menu.add_command(label="删除", command=self.delete_stock_out_item)
        self.stock_out_tree.bind("<Button-3>", self.show_stock_out_menu)
        self.stock_out_tree.bind('<Control-a>', lambda e: [self.stock_out_tree.selection_set(self.stock_out_tree.get_children()), 'break'])
        self.stock_out_tree.bind("<Double-1>", self.edit_stock_out_item)
    
    def show_add_stock_out_dialog(self):
        """显示添加出库记录的模态对话框"""
        fields = [
            ("物品", "item_name", "str"),
            ("数量", "quantity", "int"),
            ("单价", "unit_price", "float"),
            ("手续费", "fee", "float"),
            ("备注", "note", "str")
        ]
        
        ModalInputDialog(
            self.main_gui.root,
            "添加出库记录",
            fields,
            self.process_add_stock_out
        )
    
    def process_add_stock_out(self, values):
        """处理添加出库记录的回调"""
        try:
            item = values["item_name"]
            quantity = values["quantity"]
            price = values["unit_price"]
            fee = values["fee"]
            note = values["note"]
            
            total_amount = quantity * price - fee
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 自动减少库存
            success = self.db_manager.decrease_inventory(item, quantity)
            if not success:
                messagebox.showerror("错误", f"库存不足，无法出库 {item} 数量 {quantity}")
                return
                
            self.db_manager.save_stock_out({
                'item_name': item,
                'transaction_time': now,
                'quantity': quantity,
                'unit_price': price,
                'fee': fee,
                'deposit': 0.0,
                'total_amount': total_amount,
                'note': note if note is not None else ''
            })
            
            self.refresh_stock_out()
            self.main_gui.refresh_inventory()
            
            # 记录操作日志
            self.main_gui.log_operation('修改', '出库管理')
            messagebox.showinfo("成功", "出库记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def add_stock_out(self):
        try:
            item = self.stock_out_item.get()
            quantity = int(self.stock_out_quantity.get())
            price = float(self.stock_out_price.get())
            fee = float(self.stock_out_fee.get())
            note = self.stock_out_note.get()
            total_amount = quantity * price - fee
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 自动减少库存
            success = self.db_manager.decrease_inventory(item, quantity)
            if not success:
                messagebox.showerror("错误", f"库存不足，无法出库 {item} 数量 {quantity}")
                return
            self.db_manager.save_stock_out({
                'item_name': item,
                'transaction_time': now,
                'quantity': quantity,
                'unit_price': price,
                'fee': fee,
                'deposit': 0.0,
                'total_amount': total_amount,
                'note': note if note is not None else ''
            })
            self.refresh_stock_out()
            self.main_gui.refresh_inventory()
            # 清空输入框
            self.stock_out_item.delete(0, 'end')
            self.stock_out_quantity.delete(0, 'end')
            self.stock_out_price.delete(0, 'end')
            self.stock_out_fee.delete(0, 'end')
            self.stock_out_note.delete(0, 'end')
            # 记录操作日志
            self.main_gui.log_operation('修改', '出库管理')
            messagebox.showinfo("成功", "出库记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def refresh_stock_out(self):
        for item in self.stock_out_tree.get_children():
            self.stock_out_tree.delete(item)
        records = self.db_manager.get_stock_out()
        filter_text = self.stock_out_filter_var.get().strip().lower() if hasattr(self, 'stock_out_filter_var') else ''
        keywords = filter_text.split()
        filtered = []
        for record in records:
            try:
                _, item_name, transaction_time, quantity, unit_price, fee, deposit, total_amount, note, *_ = record
                name_lc = str(item_name).lower()
                if keywords and not all(k in name_lc for k in keywords):
                    continue
                values = (
                    item_name,
                    transaction_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(transaction_time, 'strftime') else str(transaction_time),
                    int(quantity),
                    int(float(unit_price)),
                    int(float(fee)),
                    int(float(total_amount)),
                    note if note is not None else ''
                )
                filtered.append(values)
                self.stock_out_tree.insert('', 'end', values=values)
            except Exception as e:
                messagebox.showerror("数据结构异常", f"出库数据结构异常: {e}\nrecord={record}")
                continue
        # 合计行
        if filter_text and filtered:
            total_qty = sum(int(row[2]) for row in filtered)
            total_fee = sum(int(row[4]) for row in filtered)
            total_amount = sum(int(row[5]) for row in filtered)
            self.stock_out_tree.insert('', 'end', values=(
                '合计', '', total_qty, '', total_fee, total_amount, ''
            ), tags=('total',))

    def edit_stock_out_item(self, event):
        item_id = self.stock_out_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.stock_out_tree.item(item_id)['values']
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑出库记录")
        edit_win.minsize(440, 440)
        edit_win.configure(bg='#f4f8fb')
        style = ttk.Style()
        style.configure('Edit.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=('微软雅黑', 11))
        style.configure('Edit.TButton', font=('微软雅黑', 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        content_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        labels = ["物品", "时间", "数量", "单价", "手续费", "总金额", "备注"]
        types = [str, str, int, float, float, float, str]
        entries = []
        error_labels = []
        for i, (label, val, typ) in enumerate(zip(labels, values, types)):
            ttk.Label(content_frame, text=label+":", style='Edit.TLabel').grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
            entry = ttk.Entry(content_frame, validate='key', validatecommand=vcmd, style='Edit.TEntry') if vcmd else ttk.Entry(content_frame, style='Edit.TEntry')
            entry.insert(0, val)
            entry.grid(row=i*2, column=1, padx=12, pady=4, sticky='w')
            entries.append(entry)
            err = ttk.Label(content_frame, text="", foreground="red", background='#f4f8fb', font=('微软雅黑', 10))
            err.grid(row=i*2+1, column=0, columnspan=2, sticky='w', padx=12)
            error_labels.append(err)
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
                error_labels[2].config(text="数量/单价/手续费/总金额必须为数字")
                entries[2].focus_set()
                return
            if not messagebox.askyesno("确认", "确定要保存修改吗？"):
                return
            self.db_manager.delete_stock_out(values[0], values[1])
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db_manager.save_stock_out({
                'item_name': new_vals[0],
                'transaction_time': current_time,
                'quantity': new_vals[2],
                'unit_price': new_vals[3],
                'fee': new_vals[4],
                'deposit': 0.0,
                'total_amount': new_vals[5],
                'note': new_vals[6]
            })
            self.refresh_stock_out()
            edit_win.destroy()
            self.main_gui.log_operation('修改', '出库管理', {'old': values, 'new': new_vals})
        button_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        ttk.Button(button_frame, text="保存", command=save, style='Edit.TButton').pack(pady=6, ipadx=40)

    def refresh_ocr_image_preview_out(self):
        """刷新OCR图片预览"""
        # 使用新组件的刷新方法
        self.ocr_preview.refresh()

    def delete_ocr_image_out(self, idx):
        """删除待识别的图片"""
        if 0 <= idx < len(self._pending_ocr_images_out):
            self._pending_ocr_images_out.pop(idx)

    def paste_ocr_import_stock_out(self, event=None):
        """从剪贴板粘贴图片进行OCR识别"""
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self._pending_ocr_images_out.append(img)
                # 使用新组件添加图片
                self.ocr_preview.add_image(img)
                messagebox.showinfo("提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
            else:
                messagebox.showinfo("提示", "剪贴板中没有图片")
        except Exception as e:
            messagebox.showerror("错误", f"粘贴图片失败: {e}")

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
                data = self.parse_stock_out_ocr_text(text)
                if data:
                    all_data.append(data)
            except Exception as e:
                messagebox.showerror("错误", f"OCR识别失败: {e}")
                
        if all_data:
            # 批量导入数据
            for data in all_data:
                item_name = data.get('item_name')
                quantity = data.get('quantity')
                unit_price = data.get('unit_price')
                fee = data.get('fee', 0)
                total_amount = quantity * unit_price - fee
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 自动减少库存
                success = self.db_manager.decrease_inventory(item_name, quantity)
                if not success:
                    messagebox.showerror("错误", f"库存不足，无法出库 {item_name} 数量 {quantity}")
                    continue
                    
                self.db_manager.save_stock_out({
                    'item_name': item_name,
                    'transaction_time': now,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'fee': fee,
                    'deposit': 0.0,
                    'total_amount': total_amount,
                    'note': ''
                })
            
            self.refresh_stock_out()
            self.main_gui.refresh_inventory()
            # 清空图片列表并刷新预览
            self._pending_ocr_images_out.clear()
            self.ocr_preview.clear_images()
            self.main_gui.log_operation('批量修改', '出库管理', all_data)
            messagebox.showinfo("成功", f"已成功导入{len(all_data)}条出库记录！")
        else:
            messagebox.showwarning("警告", "未能识别有效的出库记录！")

    def show_stock_out_menu(self, event):
        """显示右键菜单"""
        iid = self.stock_out_tree.identify_row(event.y)
        if iid:
            self.stock_out_tree.selection_set(iid)
            self.stock_out_menu.post(event.x_root, event.y_root)

    def delete_stock_out_item(self):
        selected_items = self.stock_out_tree.selection()
        if not selected_items:
            return
        names = [self.stock_out_tree.item(item)['values'][0] for item in selected_items]
        times = [self.stock_out_tree.item(item)['values'][1] for item in selected_items]
        msg = "确定要删除以下出库记录吗？\n" + "，".join(str(n) for n in names)
        deleted_data = []
        if messagebox.askyesno("确认", msg):
            for item, name, t in zip(selected_items, names, times):
                values = self.stock_out_tree.item(item)['values']
                deleted_data.append(values)
                self.db_manager.delete_stock_out(name, t)
            self.refresh_stock_out()
            self.main_gui.log_operation('删除', '出库管理', deleted_data)
            messagebox.showinfo("成功", "已删除所选出库记录！")

    def upload_ocr_import_stock_out(self):
        """上传图片进行OCR识别导入"""
        file_path = fd.askopenfilename(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        try:
            from PIL import Image
            img = Image.open(file_path)
            self._pending_ocr_images_out.append(img)
            # 使用新组件添加图片
            self.ocr_preview.add_image(img)
            messagebox.showinfo("提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def parse_stock_out_ocr_text(self, text):
        """解析OCR识别后的文本，提取出库相关信息"""
        lines = text.strip().split('\n')
        item_name = None
        quantity = None
        unit_price = None
        fee = 0
        
        for line in lines:
            if '品名' in line or '物品' in line:
                match = re.search(r'[：:]\s*(.+)$', line)
                if match:
                    item_name = match.group(1).strip()
            elif '数量' in line:
                match = re.search(r'[：:]\s*(\d+)', line)
                if match:
                    quantity = int(match.group(1))
            elif '单价' in line or '价格' in line:
                match = re.search(r'[：:]\s*(\d+)', line)
                if match:
                    unit_price = float(match.group(1))
            elif '手续费' in line or '费用' in line:
                match = re.search(r'[：:]\s*(\d+)', line)
                if match:
                    fee = float(match.group(1))
        
        if item_name and quantity and unit_price:
            return {
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'fee': fee
            }
        return None

    # 其余方法：add_stock_out, refresh_stock_out, edit_stock_out_item, delete_stock_out_item, OCR相关等
    # ...（后续补全所有出库管理相关方法）... 