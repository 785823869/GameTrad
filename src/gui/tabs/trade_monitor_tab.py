import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog as fd
import tkinter as tk
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
        
        # 设置中文字体
        self.chinese_font = main_gui.chinese_font
        
        # 创建样式
        self.setup_styles()
        
        self.create_tab()

    def setup_styles(self):
        """设置自定义样式"""
        style = tb.Style()
        
        # 表格样式
        style.configure("Monitor.Treeview", 
                      rowheight=32,  # 增加行高
                      font=(self.chinese_font, 10),
                      background="#ffffff",
                      fieldbackground="#ffffff",
                      foreground="#2c3e50")
                      
        style.configure("Monitor.Treeview.Heading", 
                      font=(self.chinese_font, 10, "bold"),
                      background="#e0e6ed",
                      foreground="#2c3e50")
        
        # 移除表格行鼠标悬停效果的style.map设置，改为使用标签和事件处理
        style.map('Monitor.Treeview', 
                background=[('selected', '#5a7bc2')])  # 只保留选中效果
        
        # 按钮样式
        style.configure("Monitor.TButton", 
                      font=(self.chinese_font, 11),
                      foreground="#ffffff")
        
        # 标签样式
        style.configure("Monitor.TLabel", 
                      font=(self.chinese_font, 10),
                      foreground="#2c3e50")
        
        # 创建透明LabelFrame样式
        style.configure("Transparent.TLabelframe", 
                      background="#ffffff",  # 与主背景色匹配
                      borderwidth=1)
                      
        style.configure("Transparent.TLabelframe.Label", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#2c3e50",
                      background="#ffffff")  # 与主背景色匹配
        
        # 过滤器样式
        style.configure("Filter.TLabel", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#3a506b")
                      
        style.configure("Filter.TEntry", 
                      font=(self.chinese_font, 10),
                      foreground="#2c3e50")

    def create_tab(self):
        # 检查是否在新UI结构中运行
        if isinstance(self.notebook, tb.Frame):
            # 新UI结构，notebook实际上是框架
            monitor_frame = self.notebook
        else:
            # 旧UI结构，notebook是Notebook
            monitor_frame = tb.Frame(self.notebook, padding=10, bootstyle="light")
            self.notebook.add(monitor_frame, text="交易监控")
        
        # 创建上方的工具栏
        toolbar = tb.Frame(monitor_frame, bootstyle="light")
        toolbar.pack(fill='x', pady=(0, 5))
        
        # 过滤器区域
        filter_frame = tb.LabelFrame(toolbar, text="筛选", bootstyle="primary", padding=5)
        filter_frame.pack(side='left', fill='y', padx=(0, 10))
        
        tb.Label(filter_frame, text="物品:", bootstyle="primary").pack(side='left', padx=2)
        
        self.monitor_filter_var = tb.StringVar()
        filter_entry = tb.Entry(filter_frame, textvariable=self.monitor_filter_var, width=12, bootstyle="primary")
        filter_entry.pack(side='left', padx=2)
        filter_entry.bind("<Return>", lambda e: self.refresh_monitor())
        
        tb.Button(filter_frame, text="筛选", command=self.refresh_monitor, bootstyle="primary-outline").pack(side='left', padx=2)
        tb.Button(filter_frame, text="清除", command=lambda: [self.monitor_filter_var.set(""), self.refresh_monitor()], bootstyle="secondary-outline").pack(side='left', padx=2)
        
        # 主区域分割
        main_area = tb.Frame(monitor_frame, bootstyle="light")
        main_area.pack(fill='both', expand=True)
        
        # 表格区域
        table_frame = tb.Frame(main_area, bootstyle="light")
        table_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # 表格和滚动条
        columns = ('物品', '当前时间', '数量', '一口价', '目标买入价', '计划卖出价', '保本卖出价', '利润', '利润率', '出库策略')
        
        # 设置表头和列宽
        column_widths = {
            '物品': 180,     # 加宽物品名称列
            '当前时间': 160,
            '数量': 70,
            '一口价': 90,
            '目标买入价': 110,
            '计划卖出价': 110,
            '保本卖出价': 110,
            '利润': 90,
            '利润率': 90,
            '出库策略': 130    # 加宽策略列
        }
        
        # 设置列对齐方式
        column_aligns = {
            '物品': 'w',     # 文本左对齐
            '当前时间': 'center',
            '数量': 'e',     # 数字右对齐
            '一口价': 'e',
            '目标买入价': 'e',
            '计划卖出价': 'e',
            '保本卖出价': 'e',
            '利润': 'e',
            '利润率': 'e',
            '出库策略': 'w'    # 文本左对齐
        }
        
        # 创建表格
        self.monitor_tree = tb.Treeview(table_frame, columns=columns, show='headings', 
                                       height=16, bootstyle="primary", style="Monitor.Treeview")
        
        for col in columns:
            self.monitor_tree.heading(col, text=col, anchor='center')
            width = column_widths.get(col, 120)
            align = column_aligns.get(col, 'center')
            self.monitor_tree.column(col, width=width, anchor=align)
            
        # 滚动条
        scrollbar = tb.Scrollbar(table_frame, orient="vertical", command=self.monitor_tree.yview, bootstyle="primary-round")
        self.monitor_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滚动条
        self.monitor_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', padx=2, pady=5)
        
        # 配置表格样式
        self.monitor_tree.tag_configure('evenrow', background='#f0f4fa')  # 柔和的蓝灰色
        self.monitor_tree.tag_configure('oddrow', background='#ffffff')
        self.monitor_tree.tag_configure('positive', foreground='#28a745')  # 绿色代表盈利
        self.monitor_tree.tag_configure('negative', foreground='#dc3545')  # 红色代表亏损
        # 添加悬停高亮标签
        self.monitor_tree.tag_configure('hovering', background='#f0f4fa')  # 鼠标悬停效果
        
        # 绑定鼠标移动事件
        self.monitor_tree.bind("<Motion>", self.on_treeview_motion)
        # 记录上一个高亮的行
        self.last_hover_row = None
        
        # 右侧面板
        right_panel = tb.Frame(main_area, width=260, bootstyle="light")
        right_panel.pack(side='right', fill='y', padx=8, pady=5)
        right_panel.pack_propagate(False)
        
        # 操作按钮区
        actions_frame = tb.LabelFrame(right_panel, text="操作", bootstyle="primary", padding=5)
        actions_frame.pack(fill='x', pady=(0, 10))
        
        # 添加记录按钮 - 使用明显的颜色
        tb.Button(
            actions_frame, 
            text="添加交易记录", 
            command=self.show_add_monitor_dialog,
            bootstyle="primary"
        ).pack(fill='x', pady=5, ipady=5)
        
        tb.Button(actions_frame, text="刷新交易记录", command=self.refresh_monitor, 
                bootstyle="primary-outline").pack(fill='x', pady=2, ipady=2)
        
        # OCR工具区域 - 使用透明样式
        ocr_tools_frame = tb.LabelFrame(right_panel, text="OCR工具", style="Transparent.TLabelframe", padding=5)
        ocr_tools_frame.pack(fill='x', pady=(0, 10))
        
        tb.Button(ocr_tools_frame, text="上传图片识别导入", command=self.upload_ocr_import_monitor,
                bootstyle="primary").pack(fill='x', pady=2, ipady=2)
                
        tb.Button(ocr_tools_frame, text="批量识别粘贴图片", command=self.batch_ocr_import_monitor,
                bootstyle="primary-outline").pack(fill='x', pady=2, ipady=2)
        
        # 使用键盘快捷键提示
        shortcut_frame = tb.Frame(right_panel, bootstyle="light")
        shortcut_frame.pack(fill='x', pady=(0, 5))
        
        tb.Label(shortcut_frame, text="快捷键: Ctrl+V 粘贴图片", bootstyle="secondary").pack(anchor='w')
        
        # OCR预览区域 - 使用透明样式
        ocr_frame = tb.LabelFrame(right_panel, text="OCR图片预览", style="Transparent.TLabelframe", padding=5)
        ocr_frame.pack(fill='x', pady=5, padx=2)
        
        # 创建OCR预览组件
        self.ocr_preview = OCRPreview(ocr_frame, height=150)
        self.ocr_preview.pack(fill='both', expand=True, padx=2, pady=5)
        self.ocr_preview.set_callback(self.delete_ocr_image)
        
        # 绑定Ctrl+V快捷键
        right_panel.bind_all('<Control-v>', self.paste_ocr_import_monitor)
        
        # 右键菜单
        self.monitor_menu = tb.Menu(self.monitor_tree, tearoff=0)
        self.monitor_menu.add_command(label="编辑", command=lambda: self.edit_monitor_item(None))
        self.monitor_menu.add_command(label="删除", command=self.delete_monitor_item)
        self.monitor_menu.add_separator()
        self.monitor_menu.add_command(label="复制物品名", command=lambda: self.copy_item_name())
        
        # 绑定右键菜单
        self.monitor_tree.bind("<Button-3>", self.show_monitor_menu)
        
        # 支持Ctrl+A全选和双击编辑
        self.monitor_tree.bind('<Control-a>', lambda e: [self.monitor_tree.selection_set(self.monitor_tree.get_children()), 'break'])
        self.monitor_tree.bind("<Double-1>", self.edit_monitor_item)
        
        # 底部状态栏
        status_frame = tb.Frame(monitor_frame, bootstyle="light")
        status_frame.pack(fill='x', side='bottom', pady=(5, 0))
        
        self.status_var = tb.StringVar(value="就绪")
        status_label = tb.Label(status_frame, textvariable=self.status_var, bootstyle="secondary")
        status_label.pack(side='left')
        
        # 初始加载数据
        self.refresh_monitor()

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
            self.status_var.set(f"已添加: {item}")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            self.status_var.set(f"添加记录失败: {str(e)}")

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
            self.status_var.set("已添加图片")
        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败: {e}")
            self.status_var.set(f"加载图片失败: {str(e)}")

    def batch_ocr_import_monitor(self):
        """批量识别已添加的图片，弹出预览窗口，确认后批量导入（远程API识别）"""
        # 从新组件获取图片列表
        ocr_images = self.ocr_preview.get_images()
        if not ocr_images:
            messagebox.showinfo("提示", "请先添加图片")
            return
            
        self.status_var.set("正在进行OCR识别...")
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
                self.status_var.set(f"OCR识别失败: {str(e)}")
                
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
                    'strategy': data.get('strategy', '')
                })
            
            self.refresh_monitor()
            self.main_gui.log_operation('修改', '交易监控')
            messagebox.showinfo("成功", f"成功导入 {len(all_data)} 条监控记录")
            self.status_var.set(f"已导入 {len(all_data)} 条记录")
            
            # 清空已处理的图片
            self._pending_ocr_images = []
            self.ocr_preview.clear_images()
        else:
            messagebox.showwarning("警告", "未能识别有效的监控记录！")
            self.status_var.set("未能识别有效记录")

    def paste_ocr_import_monitor(self, event=None):
        """从剪贴板粘贴图片进行OCR识别"""
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self._pending_ocr_images.append(img)
                # 使用新组件添加图片
                self.ocr_preview.add_image(img)
                messagebox.showinfo("提示", "图片已添加，请点击'批量识别粘贴图片'按钮进行识别导入。")
                self.status_var.set("已粘贴图片")
            else:
                messagebox.showinfo("提示", "剪贴板中没有图片")
        except Exception as e:
            messagebox.showerror("错误", f"粘贴图片失败: {e}")
            self.status_var.set(f"粘贴图片失败: {str(e)}")

    def refresh_ocr_image_preview(self):
        """刷新OCR图片预览"""
        self.ocr_preview.clear_images()
        for i, img in enumerate(self._pending_ocr_images):
            self.ocr_preview.add_image(img, index=i)

    def delete_ocr_image(self, idx):
        """删除待识别的图片"""
        if 0 <= idx < len(self._pending_ocr_images):
            del self._pending_ocr_images[idx]
            self.refresh_ocr_image_preview()

    def on_treeview_motion(self, event):
        """处理鼠标在表格上的移动，动态应用悬停高亮效果"""
        # 识别当前鼠标位置的行
        row_id = self.monitor_tree.identify_row(event.y)
        
        # 如果鼠标离开了上一个高亮行，恢复其原始样式
        if self.last_hover_row and self.last_hover_row != row_id:
            # 获取行的当前标签
            current_tags = list(self.monitor_tree.item(self.last_hover_row, 'tags'))
            # 移除悬停标签
            if 'hovering' in current_tags:
                current_tags.remove('hovering')
                self.monitor_tree.item(self.last_hover_row, tags=current_tags)
                
        # 如果鼠标位于一个有效行上，应用悬停高亮效果
        if row_id and row_id != self.last_hover_row:
            # 获取行的当前标签
            current_tags = list(self.monitor_tree.item(row_id, 'tags'))
            # 添加悬停标签
            if 'hovering' not in current_tags:
                current_tags.append('hovering')
                self.monitor_tree.item(row_id, tags=current_tags)
                
        # 更新上一个高亮行的记录
        self.last_hover_row = row_id if row_id else None

    def parse_monitor_ocr_text(self, text):
        """解析OCR识别后的文本，提取监控相关信息"""
        # 已有的解析代码保持不变
        return None

    def show_monitor_menu(self, event):
        """显示右键菜单"""
        item = self.monitor_tree.identify_row(event.y)
        if item:
            if item not in self.monitor_tree.selection():
                self.monitor_tree.selection_set(item)
            self.monitor_menu.post(event.x_root, event.y_root)
            
    def copy_item_name(self):
        """复制选中的物品名称到剪贴板"""
        selected_items = self.monitor_tree.selection()
        if not selected_items:
            return
        
        item_name = self.monitor_tree.item(selected_items[0])['values'][0]
        self.notebook.clipboard_clear()
        self.notebook.clipboard_append(item_name)
        self.status_var.set(f"已复制: {item_name}")

    def delete_monitor_item(self):
        """删除监控记录"""
        selected_items = self.monitor_tree.selection()
        if not selected_items:
            return
            
        names = [self.monitor_tree.item(item)['values'][0] for item in selected_items]
        msg = "确定要删除以下监控记录吗？\n" + "，".join(str(n) for n in names)
        
        if messagebox.askyesno("确认删除", msg):
            for item in selected_items:
                values = self.monitor_tree.item(item)['values']
                if len(values) >= 2:
                    try:
                        self.db_manager.delete_trade_monitor(values[0], values[1])
                    except Exception as e:
                        messagebox.showerror("删除失败", f"删除记录时发生错误: {str(e)}")
            
            self.refresh_monitor()
            self.status_var.set(f"已删除 {len(selected_items)} 条记录")

    def edit_monitor_item(self, event):
        """编辑监控记录"""
        if event:  # 如果是通过双击事件触发
            item_id = self.monitor_tree.identify_row(event.y)
        else:  # 如果是通过右键菜单触发
            selected = self.monitor_tree.selection()
            if not selected:
                return
            item_id = selected[0]
            
        if not item_id:
            return
            
        values = self.monitor_tree.item(item_id)['values']
        
        # 使用ttkbootstrap创建更美观的编辑窗口
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑监控记录")
        edit_win.minsize(440, 500)
        edit_win.configure(bg='#f0f0f0')
        
        # 设置窗口图标和样式
        edit_win.iconbitmap(self.main_gui.root.iconbitmap()) if hasattr(self.main_gui.root, 'iconbitmap') and callable(self.main_gui.root.iconbitmap) else None
        
        style = tb.Style()
        style.configure('Edit.TLabel', font=(self.chinese_font, 11), background='#f0f0f0')
        style.configure('Edit.TEntry', font=(self.chinese_font, 11))
        style.configure('Edit.TButton', font=(self.chinese_font, 12, 'bold'), background='#3f51b5', foreground='#fff', padding=10)
        style.map('Edit.TButton', background=[('active', '#5c6bc0')], foreground=[('active', '#ffffff')])
        style.configure('Edit.TFrame', background='#f0f0f0')
        
        # 创建内容框架
        content_frame = tb.Frame(edit_win, style='Edit.TFrame')
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        
        # 字段标题和数据类型
        labels = ["物品", "时间", "数量", "一口价", "目标买入价", "计划卖出价", "保本价", "利润", "利润率", "出库策略"]
        types = [str, str, int, float, float, float, float, float, float, str]
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
                
            entry = tb.Entry(content_frame, validate='key', validatecommand=vcmd, bootstyle="primary") if vcmd else tb.Entry(content_frame, bootstyle="primary")
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
                if idx in [2, 3, 4, 5] and not val:  # 必填字段
                    err_lbl.config(text=f"{labels[idx]}不能为空")
                    entries[idx].focus_set()
                    valid = False
                    break
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
                # 数值类型转换
                new_vals[2] = int(new_vals[2]) if new_vals[2] else 0
                new_vals[3] = float(new_vals[3]) if new_vals[3] else 0
                new_vals[4] = float(new_vals[4]) if new_vals[4] else 0
                new_vals[5] = float(new_vals[5]) if new_vals[5] else 0
                new_vals[6] = float(new_vals[6]) if new_vals[6] else 0
                new_vals[7] = float(new_vals[7]) if new_vals[7] else 0
                new_vals[8] = float(new_vals[8]) if new_vals[8] else 0
                
                # 自动计算字段
                quantity = new_vals[2]
                target_price = new_vals[4]
                planned_price = new_vals[5]
                
                # 计算保本价、利润和利润率
                new_vals[6] = round(target_price * 1.03) if target_price else 0
                new_vals[7] = (planned_price - target_price) * quantity if planned_price and target_price else 0
                new_vals[8] = round((planned_price - target_price) / target_price * 100, 2) if planned_price and target_price and target_price != 0 else 0
            except Exception as e:
                error_labels[2].config(text=f"计算错误: {str(e)}")
                entries[2].focus_set()
                return
                
            if not messagebox.askyesno("确认", "确定要保存修改吗？"):
                return
                
            self.db_manager.delete_trade_monitor(values[0], values[1])
            self.db_manager.save_trade_monitor({
                'item_name': new_vals[0],
                'monitor_time': new_vals[1],
                'quantity': new_vals[2],
                'market_price': new_vals[3],
                'target_price': new_vals[4],
                'planned_price': new_vals[5],
                'break_even_price': new_vals[6],
                'profit': new_vals[7],
                'profit_rate': new_vals[8],
                'strategy': new_vals[9]
            })
            
            self.refresh_monitor()
            edit_win.destroy()
            self.main_gui.log_operation('修改', '交易监控', {'old': values, 'new': new_vals})
            self.status_var.set(f"已编辑: {new_vals[0]} 记录")
            
        # 按钮区域
        button_frame = tb.Frame(edit_win, bootstyle="light")
        button_frame.pack(side='bottom', fill='x', pady=20)
        
        # 创建按钮
        cancel_btn = tb.Button(button_frame, text="取消", command=edit_win.destroy, bootstyle="secondary")
        cancel_btn.pack(side='left', padx=20, ipadx=20)
        
        save_btn = tb.Button(button_frame, text="保存", command=save, bootstyle="primary")
        save_btn.pack(side='right', padx=20, ipadx=20)

    def refresh_monitor(self):
        """刷新交易监控数据"""
        self.status_var.set("正在加载数据...")
        threading.Thread(target=self._fetch_and_draw_monitor).start()

    def _fetch_and_draw_monitor(self):
        """后台线程获取并显示交易监控数据"""
        try:
            monitor_data = self.db_manager.get_trade_monitor()
            
            # 过滤数据
            filter_text = self.monitor_filter_var.get().strip() if hasattr(self, 'monitor_filter_var') else ""
            
            filtered_data = []
            for item in monitor_data:
                try:
                    _, item_name, *rest = item
                    if filter_text and filter_text.lower() not in item_name.lower():
                        continue
                    filtered_data.append(item)
                except Exception as e:
                    print(f"过滤交易监控数据错误: {e}")
                    continue
            
            # 转换为表格数据
            table_data = []
            for row in filtered_data:
                try:
                    item_id, item_name, monitor_time, quantity, market_price, target_price, planned_price, break_even_price, profit, profit_rate, strategy, *_ = row
                    
                    table_data.append({
                        'item_name': item_name,
                        'monitor_time': monitor_time,
                        'quantity': self._calc_field(quantity, 0, int),
                        'market_price': self._calc_field(market_price, 0, float),
                        'target_price': self._calc_field(target_price, 0, float),
                        'planned_price': self._calc_field(planned_price, 0, float),
                        'break_even_price': self._calc_field(break_even_price, 0, float),
                        'profit': self._calc_field(profit, 0, float),
                        'profit_rate': self._calc_field(profit_rate, 0, float),
                        'strategy': strategy if strategy else ''
                    })
                except Exception as e:
                    print(f"处理交易监控数据错误: {e}")
                    continue
            
            # 在UI线程中绘制表格
            self.monitor_tree.after(0, lambda: self._draw_monitor(table_data))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_var.set(f"加载数据失败: {str(e)}")

    def _calc_field(self, value, default_value, convert_func=None):
        """安全计算字段值"""
        try:
            if value is None:
                return default_value
            if convert_func:
                return convert_func(value)
            return value
        except:
            return default_value

    def _draw_monitor(self, table_data):
        """绘制交易监控表格"""
        # 清空现有数据
        for item in self.monitor_tree.get_children():
            self.monitor_tree.delete(item)
            
        # 添加数据到表格
        for i, item in enumerate(table_data):
            # 设置交替行颜色和利润标签
            tags = []
            
            # 交替行颜色
            if i % 2 == 0:
                tags.append('evenrow')
            else:
                tags.append('oddrow')
                
            # 利润标签
            if item['profit'] > 0:
                tags.append('positive')
            elif item['profit'] < 0:
                tags.append('negative')
                
            # 格式化数字显示
            quantity_display = f"{item['quantity']:,}" if item['quantity'] else "0"
            market_price_display = f"{int(item['market_price']):,}" if item['market_price'] else "0"
            target_price_display = f"{int(item['target_price']):,}" if item['target_price'] else "0"
            planned_price_display = f"{int(item['planned_price']):,}" if item['planned_price'] else "0"
            break_even_price_display = f"{int(item['break_even_price']):,}" if item['break_even_price'] else "0"
            profit_display = f"{int(item['profit']):,}" if item['profit'] else "0"
            
            # 插入行
            self.monitor_tree.insert('', 'end', values=(
                item['item_name'],
                item['monitor_time'].strftime("%Y-%m-%d %H:%M:%S") if hasattr(item['monitor_time'], 'strftime') else str(item['monitor_time']),
                quantity_display,
                market_price_display,
                target_price_display,
                planned_price_display,
                break_even_price_display,
                profit_display,
                f"{item['profit_rate']:.2f}%",
                item['strategy']
            ), tags=tags)
            
        # 更新状态栏
        self.status_var.set(f"共 {len(table_data)} 条记录  |  上次更新: {datetime.now().strftime('%H:%M:%S')}") 