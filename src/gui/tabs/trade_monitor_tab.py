import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog as fd
import threading
from datetime import datetime
from PIL import Image
import json
from src.gui.dialogs import ModalInputDialog
from src.gui.components import OCRPreview

class TradeMonitorTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        self._pending_ocr_images = []  # 存储待识别的图片
        self.create_tab()

    def create_tab(self):
        # 检查是否在新UI结构中运行
        if isinstance(self.notebook, tb.Frame):
            # 新UI结构，notebook实际上是框架
            monitor_frame = self.notebook
        else:
            # 旧UI结构，notebook是Notebook
            monitor_frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(monitor_frame, text="交易监控")
        
        columns = ('物品', '当前时间', '数量', '一口价', '目标买入价', '计划卖出价', '保本卖出价', '利润', '利润率', '出库策略')
        self.monitor_tree = ttk.Treeview(monitor_frame, columns=columns, show='headings', height=16)
        for col in columns:
            self.monitor_tree.heading(col, text=col, anchor='center')
            self.monitor_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.monitor_tree.yview)
        self.monitor_tree.configure(yscrollcommand=scrollbar.set)
        self.monitor_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        right_panel = ttk.Frame(monitor_frame, width=260)
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        
        # 添加记录按钮 - 替换原来的嵌入式表单
        ttk.Button(
            right_panel, 
            text="添加监控记录", 
            command=self.show_add_monitor_dialog,
            style="primary.TButton"
        ).pack(fill='x', pady=10, ipady=8)
        
        ttk.Button(right_panel, text="刷新监控", command=self.refresh_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="上传图片自动识别导入", command=self.upload_ocr_import_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        ttk.Button(right_panel, text="批量识别粘贴图片", command=self.batch_ocr_import_monitor).pack(fill='x', pady=(0, 10), ipady=4)
        
        # 使用新的OCRPreview组件替换原来的预览区
        ocr_frame = ttk.LabelFrame(right_panel, text="OCR图片预览")
        ocr_frame.pack(fill='x', pady=5, padx=2)
        
        # 创建OCR预览组件
        self.ocr_preview = OCRPreview(ocr_frame, height=120)
        self.ocr_preview.pack(fill='both', expand=True, padx=2, pady=5)
        self.ocr_preview.set_callback(self.delete_ocr_image)
        
        # 绑定Ctrl+V快捷键
        right_panel.bind_all('<Control-v>', self.paste_ocr_import_monitor)
        
        self.monitor_tree.bind("<Double-1>", self.edit_monitor_item)
        self.monitor_menu = tb.Menu(self.monitor_tree, tearoff=0)
        self.monitor_menu.add_command(label="删除", command=self.delete_monitor_item)
        self.monitor_tree.bind("<Button-3>", self.show_monitor_menu)
    
    def show_add_monitor_dialog(self):
        """显示添加监控记录的模态对话框"""
        fields = [
            ("物品", "item_name", "str"),
            ("数量", "quantity", "int"),
            ("一口价", "market_price", "float"),
            ("目标买入价", "target_price", "float"),
            ("计划卖出价", "planned_price", "float"),
            ("出库策略", "strategy", "str")
        ]
        
        ModalInputDialog(
            self.main_gui.root,
            "添加监控记录",
            fields,
            self.process_add_monitor
        )
    
    def process_add_monitor(self, values):
        """处理添加监控记录的回调"""
        try:
            item = values["item_name"]
            quantity = values["quantity"]
            market_price = values["market_price"]
            target_price = values["target_price"]
            planned_price = values["planned_price"]
            strategy = values["strategy"]
            
            # 计算保本价、利润和利润率
            break_even_price = round(target_price * 1.03) if target_price else 0
            profit = (planned_price - target_price) * quantity if planned_price and target_price else 0
            profit_rate = round((planned_price - target_price) / target_price * 100, 2) if planned_price and target_price and target_price != 0 else 0
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存数据
            self.db_manager.save_trade_monitor({
                'item_name': item,
                'monitor_time': now,
                'quantity': quantity,
                'market_price': market_price,
                'target_price': target_price,
                'planned_price': planned_price,
                'break_even_price': break_even_price,
                'profit': profit,
                'profit_rate': profit_rate,
                'strategy': strategy
            })
            
            self.refresh_monitor()
            self.main_gui.log_operation('修改', '交易监控')
            messagebox.showinfo("成功", "监控记录添加成功！")
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def upload_ocr_import_monitor(self):
        """上传图片进行OCR识别导入"""
        file_path = fd.askopenfilename(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        try:
            img = Image.open(file_path)
            self._pending_ocr_images.append(img)
            # 使用新组件添加图片
            self.ocr_preview.add_image(img)
            messagebox.showinfo("提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")

    def batch_ocr_import_monitor(self):
        """批量识别已添加的图片，弹出预览窗口，确认后批量导入（远程API识别）"""
        # 从新组件获取图片列表
        ocr_images = self.ocr_preview.get_images()
        if not ocr_images:
            messagebox.showinfo("提示", "请先添加图片")
            return
            
        import io, base64, requests
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
                data = self.parse_monitor_ocr_text(text)
                if isinstance(data, list):
                    all_data.extend(data)
                elif data:
                    all_data.append(data)
            except Exception as e:
                messagebox.showerror("错误", f"OCR识别失败: {e}")
                
        if all_data:
            # 批量导入监控数据
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for data in all_data:
                item_name = data.get('item_name')
                quantity = data.get('quantity', 0)
                market_price = data.get('market_price', 0)
                target_price = data.get('target_price', 0)
                planned_price = data.get('planned_price', 0)
                
                # 计算保本价、利润和利润率
                break_even_price = round(target_price * 1.03) if target_price else 0
                profit = (planned_price - target_price) * quantity if planned_price and target_price else 0
                profit_rate = round((planned_price - target_price) / target_price * 100, 2) if planned_price and target_price and target_price != 0 else 0
                
                # 保存数据
                self.db_manager.save_trade_monitor({
                    'item_name': item_name,
                    'monitor_time': now,
                    'quantity': quantity,
                    'market_price': market_price,
                    'target_price': target_price,
                    'planned_price': planned_price,
                    'break_even_price': break_even_price,
                    'profit': profit,
                    'profit_rate': profit_rate,
                    'strategy': ''
                })
            
            self.refresh_monitor()
            # 清空图片列表并刷新预览
            self._pending_ocr_images.clear()
            self.ocr_preview.clear_images()
            self.main_gui.log_operation('批量修改', '交易监控', all_data)
            messagebox.showinfo("成功", f"已成功导入{len(all_data)}条监控记录！")
        else:
            messagebox.showwarning("警告", "未能识别有效的监控数据！")

    def paste_ocr_import_monitor(self, event=None):
        """从剪贴板粘贴图片进行OCR识别"""
        try:
            from PIL import ImageGrab
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

    def refresh_ocr_image_preview(self):
        """刷新OCR图片预览"""
        # 使用新组件的刷新方法
        self.ocr_preview.refresh()

    def delete_ocr_image(self, idx):
        """删除待识别的图片"""
        if 0 <= idx < len(self._pending_ocr_images):
            self._pending_ocr_images.pop(idx)

    def parse_monitor_ocr_text(self, text):
        """
        交易监控OCR文本解析，严格用物品字典分割物品名，并与数量、一口价一一对应，缺失补空。
        若物品字典为空，自动弹窗提示。
        """
        import re
        try:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            # 1. 提取物品名行
            item_line = ''
            for idx, line in enumerate(lines):
                if line.startswith('物品'):
                    items_block = []
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['品质', '数量', '等级', '一口价']):
                            break
                        items_block.append(lines[j])
                    item_line = ''.join(items_block)
                    break
            # 2. 用物品字典分割物品名
            dict_items = self.main_gui.load_item_dict() if hasattr(self.main_gui, 'load_item_dict') else []
            if not dict_items:
                messagebox.showwarning(
                    "物品字典为空",
                    "物品字典未设置或内容为空，无法分割物品名。请在'物品字典管理'中添加物品名后重试。"
                )
                return []
            item_names = []
            pos = 0
            while pos < len(item_line):
                matched = False
                for name in sorted(dict_items, key=lambda x: -len(x)):
                    if item_line.startswith(name, pos):
                        item_names.append(name)
                        pos += len(name)
                        matched = True
                        break
                if not matched:
                    pos += 1
            # 3. 提取所有数量
            quantities = []
            for idx, line in enumerate(lines):
                if line.startswith('数量'):
                    qty_block = []
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['一口价', '等级', '品质']):
                            break
                        qty_block.append(lines[j])
                    qty_line = ''.join(qty_block)
                    # 提取数字
                    qty_digits = re.findall(r'\d+', qty_line)
                    quantities.extend([int(q) for q in qty_digits])
            # 4. 提取所有一口价
            prices = []
            for idx, line in enumerate(lines):
                if line.startswith('一口价'):
                    price_block = []
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['数量', '等级', '品质', '物品']):
                            break
                        price_block.append(lines[j])
                    price_line = ''.join(price_block)
                    # 提取数字
                    price_digits = re.findall(r'\d+', price_line)
                    prices.extend([int(p) for p in price_digits])
            # 5. 组装数据
            result = []
            min_len = min(len(item_names), len(quantities), len(prices)) if item_names and quantities and prices else 0
            for i in range(min_len):
                result.append({
                    'item_name': item_names[i],
                    'quantity': quantities[i],
                    'market_price': prices[i]
                })
            return result
        except Exception as e:
            messagebox.showerror("解析错误", f"监控数据解析失败: {e}")
            return []

    def show_monitor_menu(self, event):
        """显示右键菜单"""
        iid = self.monitor_tree.identify_row(event.y)
        if iid:
            self.monitor_tree.selection_set(iid)
            self.monitor_menu.post(event.x_root, event.y_root)

    def delete_monitor_item(self):
        """删除所选监控项"""
        selected_items = self.monitor_tree.selection()
        if not selected_items:
            return
        names = [self.monitor_tree.item(item)['values'][0] for item in selected_items]
        times = [self.monitor_tree.item(item)['values'][1] for item in selected_items]
        msg = "确定要删除以下监控记录吗？\n" + "，".join(str(n) for n in names)
        deleted_data = []
        if messagebox.askyesno("确认", msg):
            for item, name, t in zip(selected_items, names, times):
                values = self.monitor_tree.item(item)['values']
                deleted_data.append(values)
                self.db_manager.delete_trade_monitor(name, t)
            self.refresh_monitor()
            self.main_gui.log_operation('删除', '交易监控', deleted_data)
            messagebox.showinfo("成功", "已删除所选监控记录！")

    def edit_monitor_item(self, event):
        """双击编辑监控项"""
        item_id = self.monitor_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.monitor_tree.item(item_id)['values']
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑监控记录")
        edit_win.minsize(440, 440)
        edit_win.configure(bg='#f4f8fb')
        style = ttk.Style()
        style.configure('Edit.TLabel', font=('微软雅黑', 11), background='#f4f8fb')
        style.configure('Edit.TEntry', font=('微软雅黑', 11))
        style.configure('Edit.TButton', font=('微软雅黑', 12, 'bold'), background='#3399ff', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#66c2ff')], foreground=[('active', '#003366')])
        content_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        labels = ["物品", "时间", "数量", "一口价", "目标买入价", "计划卖出价", "保本卖出价", "利润", "利润率", "出库策略"]
        types = [str, str, int, float, float, float, float, float, float, str]
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
                if idx in [2, 3, 4, 5]:  # 只检查重要数值字段
                    if typ is int and not val.isdigit():
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
                item_name = new_vals[0]
                quantity = int(new_vals[2])
                market_price = float(new_vals[3])
                target_price = float(new_vals[4])
                planned_price = float(new_vals[5])
                strategy = new_vals[9]
                
                # 计算保本价、利润和利润率
                break_even_price = round(target_price * 1.03)
                profit = (planned_price - target_price) * quantity
                profit_rate = round((planned_price - target_price) / target_price * 100, 2) if target_price != 0 else 0
                
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 删除旧记录
                self.db_manager.delete_trade_monitor(values[0], values[1])
                
                # 保存新记录
                self.db_manager.save_trade_monitor({
                    'item_name': item_name,
                    'monitor_time': current_time,
                    'quantity': quantity,
                    'market_price': market_price,
                    'target_price': target_price,
                    'planned_price': planned_price,
                    'break_even_price': break_even_price,
                    'profit': profit,
                    'profit_rate': profit_rate,
                    'strategy': strategy
                })
                
                self.refresh_monitor()
                edit_win.destroy()
                self.main_gui.log_operation('修改', '交易监控', {'old': values, 'new': new_vals})
                
            except Exception as e:
                messagebox.showerror("保存失败", f"更新监控记录失败: {e}")
                
        button_frame = ttk.Frame(edit_win, style='Edit.TFrame')
        button_frame.pack(side='bottom', fill='x', pady=20)
        ttk.Button(button_frame, text="保存", command=save, style='Edit.TButton').pack(pady=6, ipadx=40)

    def refresh_monitor(self):
        """刷新监控表格数据"""
        threading.Thread(target=self._fetch_and_draw_monitor).start()

    def _fetch_and_draw_monitor(self):
        """后台线程获取并显示监控数据"""
        try:
            records = self.db_manager.get_trade_monitor()
            table_data = []
            for record in records:
                try:
                    # 解包数据
                    _, item_name, monitor_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = record
                    
                    # 格式化时间
                    if hasattr(monitor_time, 'strftime'):
                        time_str = monitor_time.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        time_str = str(monitor_time)
                    
                    # 创建数据行
                    row = (
                        item_name,
                        time_str,
                        self._calc_field(quantity, 0, int),
                        self._calc_field(market_price, 0, int),
                        self._calc_field(target_price, 0, int),
                        self._calc_field(planned_price, 0, int),
                        self._calc_field(break_even_price, 0, int),
                        self._calc_field(profit, 0, int),
                        self._calc_field(profit_rate, 0, float),
                        strategy or ''
                    )
                    table_data.append(row)
                except Exception as e:
                    print(f"处理监控记录错误: {e}, record={record}")
            
            # 在主线程中更新UI
            self.main_gui.root.after(0, lambda: self._draw_monitor(table_data))
        except Exception as e:
            print(f"获取监控数据错误: {e}")
    
    def _calc_field(self, value, default_value, convert_func=None):
        """安全地计算字段值，避免None和转换错误"""
        if value is None:
            return default_value
        try:
            if convert_func:
                return convert_func(value)
            return value
        except Exception:
            return default_value
    
    def _draw_monitor(self, table_data):
        """在主线程中绘制监控表格"""
        # 清空现有数据
        for item in self.monitor_tree.get_children():
            self.monitor_tree.delete(item)
        
        # 插入新数据
        for row in table_data:
            self.monitor_tree.insert('', 'end', values=row) 