import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox, filedialog as fd
import tkinter as tk
import threading
from datetime import datetime
from PIL import Image
import json
import os
from src.gui.dialogs import ModalInputDialog
from src.gui.components import OCRPreview, OCRPreviewDialog
from src.utils import clipboard_helper
import pandas as pd
from src.gui.utils.monitor_ocr_parser import parse_monitor_ocr_text

class TradeMonitorTab:
    def __init__(self, notebook, main_gui):
        self.main_gui = main_gui
        self.db_manager = main_gui.db_manager
        self.notebook = notebook
        
        # 设置中文字体
        self.chinese_font = main_gui.chinese_font
        
        # 添加OCR图片存储列表
        self._pending_ocr_images = []
        
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
                      foreground="#2c3e50")
                      
        style.configure("Monitor.Treeview.Heading", 
                      font=(self.chinese_font, 10, "bold"),
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
        
        # 创建统一的LabelFrame样式，背景色与主窗口背景色匹配
        style.configure("Unified.TLabelframe", 
                      borderwidth=1)
                      
        style.configure("Unified.TLabelframe.Label", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#2c3e50")
        
        # 创建统一的标签样式
        style.configure("Unified.TLabel", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#2c3e50")
        
        # 创建透明LabelFrame样式
        style.configure("Transparent.TLabelframe", 
                      borderwidth=1)
                      
        style.configure("Transparent.TLabelframe.Label", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#2c3e50")
        
        # 过滤器样式
        style.configure("Filter.TLabel", 
                      font=(self.chinese_font, 10, "bold"),
                      foreground="#3a506b")
                      
        style.configure("Filter.TEntry", 
                      font=(self.chinese_font, 10),
                      foreground="#2c3e50")
        
        # 添加不同来源字段的样式
        style.configure('OCR.TLabel', font=(self.chinese_font, 11), foreground='#0066cc')  # OCR识别的字段
        style.configure('Manual.TLabel', font=(self.chinese_font, 11), foreground='#006633')  # 人工编辑的字段
        style.configure('Calculated.TLabel', font=(self.chinese_font, 11), foreground='#993366')  # 计算得出的字段

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
        filter_frame = tb.LabelFrame(toolbar, text="筛选", style="Unified.TLabelframe", padding=5)
        filter_frame.pack(side='left', fill='y', padx=(0, 10))
        
        tb.Label(filter_frame, text="物品:", style="Unified.TLabel").pack(side='left', padx=2)
        
        self.monitor_filter_var = tb.StringVar()
        filter_entry = tb.Entry(filter_frame, textvariable=self.monitor_filter_var, width=12, bootstyle="primary")
        filter_entry.pack(side='left', padx=2)
        filter_entry.bind("<Return>", lambda e: self.refresh_monitor())
        
        tb.Button(filter_frame, text="筛选", command=self.refresh_monitor, bootstyle="primary-outline").pack(side='left', padx=2)
        tb.Button(filter_frame, text="清除", command=lambda: [self.monitor_filter_var.set(""), self.refresh_monitor()], bootstyle="secondary-outline").pack(side='left', padx=2)
        
        # 添加字段来源图例
        legend_frame = tb.Frame(toolbar, bootstyle="light")
        legend_frame.pack(side='right', fill='y', padx=(0, 10))
        
        tb.Label(legend_frame, text="字段说明:", style="Unified.TLabel").pack(side='left', padx=2)
        tb.Label(legend_frame, text="人工编辑", bootstyle="success", font=(self.chinese_font, 9)).pack(side='left', padx=2)
        
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
        
        # 添加不同来源字段的表格标签
        self.monitor_tree.tag_configure('ocr_field', foreground='#0066cc')  # OCR识别字段，蓝色
        self.monitor_tree.tag_configure('manual_field', foreground='#006633', font=(self.chinese_font, 10, 'bold'))  # 人工编辑字段，绿色加粗
        self.monitor_tree.tag_configure('calc_field', foreground='#993366')  # 自动计算字段，紫色
        
        # 绑定鼠标移动事件
        self.monitor_tree.bind("<Motion>", self.on_treeview_motion)
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
            text="添加交易记录", 
            command=self.show_add_monitor_dialog,
            bootstyle="primary"
        ).pack(fill='x', pady=5, ipady=5)
        
        tb.Button(actions_frame, text="刷新交易记录", command=self.refresh_monitor, 
                bootstyle="primary-outline").pack(fill='x', pady=2, ipady=2)
        
        # OCR工具区域 - 使用统一样式
        ocr_tools_frame = tb.LabelFrame(right_panel, text="OCR工具", style="Unified.TLabelframe", padding=5)
        ocr_tools_frame.pack(fill='x', pady=(0, 10))
        
        tb.Button(ocr_tools_frame, text="上传图片识别导入", command=self.upload_ocr_import_monitor,
                bootstyle="primary").pack(fill='x', pady=2, ipady=2)
                
        tb.Button(ocr_tools_frame, text="批量识别粘贴图片", command=self.batch_ocr_import_monitor,
                bootstyle="primary-outline").pack(fill='x', pady=2, ipady=2)
        
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
        
        # 在对话框中使用不同颜色标识不同来源字段
        style = tb.Style()
        style.configure('OCR.TLabel', font=(self.chinese_font, 11), foreground='#0066cc')  # OCR识别的字段
        style.configure('Manual.TLabel', font=(self.chinese_font, 11), foreground='#006633')  # 人工编辑的字段
        
        # 添加解释说明
        explanation = (
            "字段说明:\n"
            "- 输入物品、数量、一口价等信息\n"
            "- 目标买入价、计划卖出价、出库策略为人工编辑字段"
        )
        
        # 使用自定义样式创建对话框
        dialog = ModalInputDialog(
            self.main_gui.root,
            "添加交易监控记录",
            fields,
            self.process_add_monitor
        )
        
        # 修改对话框框架，添加说明文本
        explanation_label = tb.Label(
            dialog.dialog,
            text=explanation,
            justify="left",
            font=(self.chinese_font, 10),
            bootstyle="primary",
            padding=10
        )
        explanation_label.place(x=20, y=20, width=440, height=80)
        
        # 调整内容框架位置，为说明文本留出空间
        dialog.content_frame.place(x=20, y=100, relwidth=0.95, height=dialog.h-180)
        
        # 为不同类型的字段设置不同样式
        for i, (label, field_name, _) in enumerate(fields):
            label_widget = dialog.content_frame.winfo_children()[i*3]  # 每个字段有3个子组件：标签、输入框、错误提示
            
            # 设置标签样式
            if i >= 3:  # 目标买入价、计划卖出价、出库策略是人工编辑字段
                label_widget.configure(style='Manual.TLabel', bootstyle="success")
                
        # 等待对话框完成

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
        file_path = fd.askopenfilename(
            title="选择图片", 
            filetypes=[
                ("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff"),
                ("PNG文件", "*.png"),
                ("JPG文件", "*.jpg;*.jpeg"),
                ("所有文件", "*.*")
            ],
            multiple=True  # 允许多选
        )
        
        if not file_path:
            return
            
        # 如果是单个文件路径，转换为列表
        if isinstance(file_path, str):
            file_path = [file_path]
            
        success_count = 0
        error_count = 0
        error_messages = []
            
        for path in file_path:
            try:
                img = Image.open(path)
                # 添加到待处理图片列表
                self._pending_ocr_images.append(img)
                success_count += 1
            except Exception as e:
                error_count += 1
                error_messages.append(f"{os.path.basename(path)}: {str(e)}")
        
        # 刷新OCR预览组件显示
        self.refresh_ocr_image_preview()
                
        # 更新状态和提供反馈
        if success_count > 0:
            if error_count > 0:
                # 部分成功
                self.status_var.set(f"已添加{success_count}张图片，{error_count}张添加失败")
                messagebox.showinfo(
                    "部分图片已添加", 
                    f"成功添加{success_count}张图片，{error_count}张添加失败。\n\n"
                    f"请点击'批量识别粘贴图片'按钮进行识别导入。"
                )
            else:
                # 全部成功
                self.status_var.set(f"已添加{success_count}张图片")
                messagebox.showinfo(
                    "图片已添加", 
                    f"已成功添加{success_count}张图片。\n\n"
                    f"请点击'批量识别粘贴图片'按钮进行识别导入。"
                )
        elif error_count > 0:
            # 全部失败
            self.status_var.set("图片加载失败")
            error_details = "\n".join(error_messages[:5])
            if len(error_messages) > 5:
                error_details += f"\n... 等共{len(error_messages)}个错误"
                
            messagebox.showerror(
                "图片加载失败", 
                f"无法加载所选图片:\n\n{error_details}"
            )

    def batch_ocr_import_monitor(self):
        """批量OCR识别导入交易监控数据"""
        # 从待处理图片列表获取图片，而不是从OCR预览组件
        if not self._pending_ocr_images:
            messagebox.showinfo("提示", "请先添加图片")
            return
            
        try:
            self.status_var.set("正在进行OCR识别...")
            
            # 显示进度
            progress_window = tk.Toplevel(self.notebook)
            progress_window.title("OCR识别中")
            progress_window.geometry("300x100")
            
            progress_label = tk.Label(progress_window, text="正在处理图片...", font=('SimHei', 10))
            progress_label.pack(pady=10)
            
            progress = ttk.Progressbar(progress_window, orient="horizontal", length=250, mode="determinate")
            progress.pack(pady=10)
            
            total_images = len(self._pending_ocr_images)
            
            # 创建全局变量存储OCR结果，确保在线程完成后仍然可用
            self._ocr_processing_result = []
            
            def process_images():
                import io
                import base64
                import requests
                
                all_ocr_data = []  # 局部变量存储OCR结果
                
                for i, img in enumerate(self._pending_ocr_images):
                    # 更新进度
                    progress_window.after(10, lambda p=((i+1)/total_images*100): progress.configure(value=p))
                    progress_window.after(10, lambda idx=i+1, total=total_images: 
                                         progress_label.configure(text=f"处理图片 {idx}/{total}..."))
                    
                    try:
                        # 直接在这里实现OCR API调用
                        buf = io.BytesIO()
                        img.save(buf, format='PNG')
                        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        
                        # 发送API请求
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
                        ocr_text = ocr_result.get('data', '')
                        
                        if not ocr_text:
                            print(f"图片 {i+1} OCR识别返回空文本")
                            continue
                            
                        print(f"OCR识别结果：\n{ocr_text}")  # 调试输出
                        
                        # 解析OCR文本，使用专用解析器
                        item_dict = self.main_gui.load_item_dict()
                        ocr_data = parse_monitor_ocr_text(ocr_text, item_dict)
                        
                        # 调试信息：打印解析结果
                        print(f"解析到的OCR数据: {ocr_data}")
                        
                        # 将结果添加到列表
                        if ocr_data:
                            all_ocr_data.extend(ocr_data)
                            
                    except Exception as e:
                        print(f"处理图片 {i+1} 时出错: {str(e)}")
                
                # 保存局部OCR结果到类变量
                self._ocr_processing_result = all_ocr_data
                
                # 调试信息：打印最终的OCR数据列表
                print(f"所有OCR数据: {all_ocr_data}")
                print(f"数据列表长度: {len(all_ocr_data)}")
                
                # 在主线程上显示结果，使用progress_window.after确保在窗口销毁前调度
                progress_window.after(100, self._finish_ocr_processing)
                
            # 在新线程中处理图片
            threading.Thread(target=process_images, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("错误", f"OCR识别失败: {str(e)}")
            self.status_var.set(f"OCR识别失败: {str(e)}")
    
    def _finish_ocr_processing(self):
        """OCR处理完成后的回调函数，显示结果或错误信息"""
        # 关闭进度窗口（如果存在）
        for child in self.main_gui.root.winfo_children():
            if isinstance(child, tk.Toplevel) and child.title() == "OCR识别中":
                child.destroy()
                
        # 检查处理结果
        if hasattr(self, '_ocr_processing_result') and self._ocr_processing_result:
            # 确保在主线程中调用预览窗口
            print("准备显示OCR预览对话框...")
            # 直接调用，不使用after，因为我们已经在主线程中
            self.show_ocr_preview_dialog(self._ocr_processing_result)
        else:
            messagebox.showwarning("警告", "OCR识别未提取到有效数据，请检查图片或尝试手动输入。")
            self.status_var.set("OCR识别未提取到有效数据")

    def show_ocr_preview_dialog(self, ocr_data_list):
        """显示OCR识别数据预览窗口（表格形式）"""
        # 添加调试信息
        print(f"开始显示OCR预览对话框，数据列表长度: {len(ocr_data_list)}")
        
        # 定义列 - 只保留物品、数量、一口价三个字段
        columns = ('物品', '数量', '一口价')
        
        # 设置列宽和对齐方式 - 只保留需要的字段
        column_widths = {
            '物品': 200,  # 增加物品列宽度，更好地显示物品名称
            '数量': 100,
            '一口价': 100
        }
        
        column_aligns = {
            '物品': 'w',  # 文本左对齐
            '数量': 'e',  # 数字右对齐
            '一口价': 'e'
        }
        
        # 转换数据格式，确保与表格列匹配
        display_data = []
        for data in ocr_data_list:
            if isinstance(data, dict):
                # 调试信息
                print(f"处理OCR数据项: {data}")
                
                # 获取基本字段，支持英文字段名和中文字段名
                item_name = data.get('item_name', '') or data.get('物品', '')
                quantity = data.get('quantity', 0) or data.get('数量', 0)
                market_price = data.get('market_price', 0) or data.get('一口价', 0)
                
                # 确保有备注字段
                note = data.get('note', '') or data.get('备注', '')
                
                # 构建标准化的数据对象 - 只包含必要字段
                processed_data = {
                    '物品': item_name,
                    '数量': quantity,
                    '一口价': market_price,
                    # 保留英文字段名，确保数据验证能通过
                    'item_name': item_name,
                    'quantity': quantity,
                    'market_price': market_price,
                    # 保留note字段，用于可能的备注
                    'note': note
                }
                
                # 调试信息
                print(f"处理后的数据项: {processed_data}")
                
                display_data.append(processed_data)
        
        # 打印最终显示数据
        print(f"预处理后的显示数据列表长度: {len(display_data)}")
        
        try:
            # 使用通用OCR预览对话框组件
            preview_dialog = OCRPreviewDialog(
                parent=self.main_gui.root,
                title="监控记录数据预览",
                chinese_font=self.chinese_font
            )
            
            # 显示对话框并处理确认后的数据
            print("调用OCRPreviewDialog.show()方法显示预览对话框...")
            preview_dialog.show(
                data_list=display_data,
                columns=columns,
                column_widths=column_widths,
                column_aligns=column_aligns,
                callback=self.import_confirmed_ocr_data,
                bootstyle="primary"  # 使用交易监控的主题色
            )
            print("OCRPreviewDialog.show()方法调用完成")
            
        except Exception as e:
            print(f"显示OCR预览对话框失败: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"显示OCR预览对话框失败: {str(e)}")

    def import_confirmed_ocr_data(self, confirmed_data):
        """导入确认后的OCR数据"""
        success_count = 0
        error_count = 0
        error_messages = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for data in confirmed_data:
            try:
                # 确保所有必要的字段都存在
                if not isinstance(data, dict):
                    error_count += 1
                    error_messages.append(f"数据格式错误: {data}")
                    continue
                
                # 获取必要字段，支持英文和中文字段名
                item_name = data.get('item_name', '') or data.get('物品', '')
                if not item_name:
                    error_count += 1
                    error_messages.append("缺少物品名称")
                    continue
                    
                quantity = data.get('quantity', 0) or data.get('数量', 0)
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
                
                # 获取价格字段
                market_price = data.get('market_price', 0) or data.get('一口价', 0)
                try:
                    market_price = int(market_price)
                except (ValueError, TypeError):
                    error_count += 1
                    error_messages.append(f"{item_name}: 一口价必须是数字")
                    continue
                
                # 获取或计算目标买入价
                target_price = data.get('target_price', 0) or data.get('目标买入价', 0)
                if not target_price and market_price:
                    # 如果没有提供目标买入价，默认设置为一口价的95%
                    target_price = int(market_price * 0.95)
                    print(f"未提供目标买入价，自动设置为一口价的95%: {target_price}")
                
                try:
                    target_price = int(target_price)
                except (ValueError, TypeError):
                    error_count += 1
                    error_messages.append(f"{item_name}: 目标买入价必须是数字")
                    continue
                
                # 获取或计算计划卖出价
                planned_price = data.get('planned_price', 0) or data.get('计划卖出价', 0)
                if not planned_price and target_price:
                    # 如果没有提供计划卖出价，默认设置为目标买入价的110%
                    planned_price = int(target_price * 1.1)
                    print(f"未提供计划卖出价，自动设置为目标买入价的110%: {planned_price}")
                
                try:
                    planned_price = int(planned_price)
                except (ValueError, TypeError):
                    error_count += 1
                    error_messages.append(f"{item_name}: 计划卖出价必须是数字")
                    continue
                
                # 计算保本价、利润和利润率
                break_even_price = round(target_price * 1.03) if target_price else 0
                profit = (planned_price - target_price) * quantity if planned_price and target_price else 0
                profit_rate = round((planned_price - target_price) / target_price * 100, 2) if planned_price and target_price and target_price != 0 else 0
                
                # 备注/策略
                strategy = data.get('strategy', '') or data.get('出库策略', '') or data.get('note', '') or data.get('备注', '')
                
                # 保存数据
                saved_data = {
                    'item_name': item_name,
                    'monitor_time': now,
                    'quantity': quantity,
                    'market_price': market_price,
                    'target_price': target_price,
                    'planned_price': planned_price,
                    'break_even_price': break_even_price,
                    'profit': profit,
                    'profit_rate': profit_rate,
                    'strategy': strategy
                }
                
                # 调试输出
                print(f"保存交易监控数据: {saved_data}")
                
                # 保存到数据库
                self.db_manager.save_trade_monitor(saved_data)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_message = f"{data.get('item_name', '未知物品')}: {str(e)}"
                error_messages.append(error_message)
                print(f"保存交易监控数据错误: {error_message}")
        
        if success_count > 0:
            self.refresh_monitor()
            self.main_gui.log_operation('批量修改', '交易监控', confirmed_data)
            messagebox.showinfo("成功", f"成功导入 {success_count} 条监控记录")
            self.status_var.set(f"已导入 {success_count} 条记录")
            
            # 清空已处理的图片列表
            self._pending_ocr_images.clear()
            # 清空OCR预览显示
            self.ocr_preview.clear_images()
        else:
            error_details = "\n".join(error_messages[:5])
            if len(error_messages) > 5:
                error_details += f"\n... 等共{len(error_messages)}个错误"
                
            messagebox.showerror("导入失败", 
                               f"所有记录导入失败。\n\n错误详情:\n{error_details}")
            self.status_var.set("未导入任何记录")

    def paste_ocr_import_monitor(self, event=None):
        """从剪贴板粘贴图片进行OCR识别"""
        try:
            # 使用辅助模块获取剪贴板图片
            img = clipboard_helper.get_clipboard_image()
            
            # 验证获取到的是否为图片
            if img is not None:
                # 添加到待处理图片列表
                self._pending_ocr_images.append(img)
                
                # 刷新OCR预览组件显示
                self.refresh_ocr_image_preview()
                
                # 提示用户下一步操作
                self.status_var.set("已粘贴图片到预览区")
                
                # 显示更友好的提示信息
                messagebox.showinfo("提示", 
                                   "图片已添加并显示在下方OCR预览区。\n\n"
                                   "请点击'批量识别粘贴图片'按钮进行识别导入，\n"
                                   "或继续粘贴更多图片进行批量处理。")
            else:
                # 详细诊断剪贴板问题
                report = clipboard_helper.diagnose_clipboard()
                formats = report.get('clipboard_state', {}).get('available_formats', [])
                
                if formats:
                    # 剪贴板有内容，但不是图片
                    messagebox.showwarning("剪贴板内容不是图片", 
                                     f"剪贴板中没有可识别的图片。\n"
                                     f"当前剪贴板内容类型: {', '.join(formats)}\n\n"
                                     f"请确保已复制图片到剪贴板，或使用'上传图片'按钮。")
                else:
                    # 剪贴板为空或无法访问
                    messagebox.showwarning("剪贴板为空", 
                                     "剪贴板中没有内容或无法访问剪贴板。\n\n"
                                     "请先复制图片到剪贴板，或使用'上传图片'按钮。")
                
                self.status_var.set("粘贴图片失败：剪贴板中没有图片")
        except Exception as e:
            error_msg = str(e)
            print(f"粘贴图片异常: {error_msg}")  # 调试输出
            
            # 提供更详细的错误信息和解决建议
            if "access" in error_msg.lower() or "permission" in error_msg.lower():
                messagebox.showerror("访问错误", 
                                  f"无法访问剪贴板: {error_msg}\n\n"
                                  f"可能的解决方案:\n"
                                  f"1. 重新启动应用程序\n"
                                  f"2. 检查是否有其他程序锁定了剪贴板\n"
                                  f"3. 使用'上传图片'按钮作为替代方法")
            else:
                messagebox.showerror("错误", 
                                  f"粘贴图片失败: {error_msg}\n\n"
                                  f"请尝试使用'上传图片'按钮。")
            
            self.status_var.set(f"粘贴图片失败: {error_msg}")

    def refresh_ocr_image_preview(self):
        """刷新OCR图片预览"""
        # 清空现有图片
        self.ocr_preview.clear_images()
        
        # 添加所有待处理图片
        for img in self._pending_ocr_images:
            self.ocr_preview.add_image(img)
            
        # 更新状态
        if self._pending_ocr_images:
            self.status_var.set(f"已添加 {len(self._pending_ocr_images)} 张图片")
        else:
            self.status_var.set("就绪")

    def delete_ocr_image(self, idx):
        """删除待识别的图片"""
        if 0 <= idx < len(self._pending_ocr_images):
            self._pending_ocr_images.pop(idx)
            self.refresh_ocr_image_preview()
            
            # 更新状态
            if self._pending_ocr_images:
                self.status_var.set(f"已删除图片，还剩 {len(self._pending_ocr_images)} 张")
            else:
                self.status_var.set("已删除全部图片")

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
        """
        解析OCR识别后的文本，提取监控相关信息
        
        注意：此方法已被替换为使用专用解析器
        """
        # 使用专用的交易监控OCR解析器
        from src.gui.utils.monitor_ocr_parser import parse_monitor_ocr_text
        item_dict = self.main_gui.load_item_dict()
        return parse_monitor_ocr_text(text, item_dict)

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
        
        # 输出调试信息，查看values
        print(f"编辑记录values: {values}")
        
        # 使用ttkbootstrap创建更美观的编辑窗口
        edit_win = tb.Toplevel(self.main_gui.root)
        edit_win.title("编辑监控记录")
        edit_win.minsize(500, 480)  # 调整窗口大小，因为减少了字段
        edit_win.configure(bg='#f0f0f0')
        
        # 设置窗口图标和样式
        edit_win.iconbitmap(self.main_gui.root.iconbitmap()) if hasattr(self.main_gui.root, 'iconbitmap') and callable(self.main_gui.root.iconbitmap) else None
        
        style = tb.Style()
        style.configure('Edit.TLabel', font=(self.chinese_font, 11))
        style.configure('Edit.TEntry', font=(self.chinese_font, 11))
        style.configure('Edit.TButton', font=(self.chinese_font, 12, 'bold'), padding=10)
        style.map('Edit.TButton', foreground=[('active', '#ffffff')])
        style.configure('Edit.TFrame', bootstyle="light")
        
        # 添加几种特殊样式，用于标识不同来源的字段
        style.configure('OCR.TLabel', font=(self.chinese_font, 11), foreground='#0066cc')  # OCR识别的字段
        style.configure('Manual.TLabel', font=(self.chinese_font, 11), foreground='#006633')  # 人工编辑的字段
        
        # 创建内容框架
        content_frame = tb.Frame(edit_win, bootstyle="light")
        content_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        
        # 添加说明标签
        explanation_frame = tb.Frame(edit_win, bootstyle="light")
        explanation_frame.pack(side='top', fill='x', padx=10, pady=(0, 10))
        
        tb.Label(
            explanation_frame,
            text="请编辑以下字段:",
            font=(self.chinese_font, 10, "bold"),
            bootstyle="primary"
        ).pack(side='left', padx=(0, 5))
        
        # 定义需要显示的字段 - 增加出库策略字段
        display_fields = ["物品", "数量", "一口价", "目标买入价", "计划卖出价", "出库策略"]
        field_indices = [0, 2, 3, 4, 5, 9]  # values中字段的索引
        field_types = [str, int, float, float, float, str]  # 字段类型
        # 标记字段来源: 'ocr'=OCR识别, 'manual'=人工编辑
        field_sources = ['ocr', 'ocr', 'ocr', 'manual', 'manual', 'manual']
        
        entries = []
        error_labels = []
        
        # 创建字段
        for i, (label, idx, typ, source) in enumerate(zip(display_fields, field_indices, field_types, field_sources)):
            # 获取原始值
            val = values[idx] if idx < len(values) else ""
            
            # 打印当前处理的字段和值
            print(f"处理字段 {label}, 索引 {idx}, 原始值: {val}, 类型: {type(val)}")
            
            # 选择标签样式
            label_style = 'Edit.TLabel'  # 默认样式
            label_bootstyle = "default"  # 默认引导样式
            
            if source == 'ocr':
                label_style = 'OCR.TLabel'
                label_bootstyle = "info"
                label_text = f"{label}:"
            elif source == 'manual':
                label_style = 'Manual.TLabel'
                label_bootstyle = "success"
                label_text = f"{label}:"
            else:
                label_text = f"{label}:"
            
            # 使用ttkbootstrap的标签，确保背景色一致
            tb.Label(
                content_frame, 
                text=label_text, 
                font=(self.chinese_font, 11),
                bootstyle=label_bootstyle,
                style=label_style,
                anchor='e'  # 右对齐文本
            ).grid(row=i*2, column=0, padx=12, pady=4, sticky='e')
            
            vcmd = None
            if typ is int:
                vcmd = (edit_win.register(lambda s: s.isdigit() or s==''), '%P')
            elif typ is float:
                vcmd = (edit_win.register(lambda s: s.replace('.','',1).isdigit() or s==''), '%P')
            
            # 所有字段都可编辑
            bootstyle = "primary"
            if source == 'ocr':
                bootstyle = "info"  # OCR字段使用不同颜色
            elif source == 'manual':
                bootstyle = "success"  # 手动编辑字段使用不同颜色
            
            entry = tb.Entry(
                content_frame, 
                validate='key', 
                validatecommand=vcmd if vcmd else None, 
                bootstyle=bootstyle
            )
            
            # 改进的值处理逻辑
            if isinstance(val, str):
                # 去除数字格式化中的逗号
                val = val.replace(",", "")
                # 去除标记前缀
                val = val.replace("[M] ", "").replace("[O] ", "")
                
                # 专门处理数量字段（对应编辑窗口中的第二个字段）
                if i == 1:  # 数量字段
                    import re
                    # 提取纯数字部分
                    num_match = re.search(r'\d+', val)
                    if num_match:
                        val = num_match.group(0)
                    print(f"数量字段处理后: {val}")
                    
                # 专门处理一口价字段（对应编辑窗口中的第三个字段）
                elif i == 2:  # 一口价字段
                    import re
                    # 提取数值（包含可能的小数点）
                    num_match = re.search(r'\d+(\.\d+)?', val)
                    if num_match:
                        val = num_match.group(0)
                    print(f"一口价字段处理后: {val}")
                    
                # 其他字段处理逻辑
                else:
                    # 去除加号、-号前缀，但保留数字部分
                    if val.startswith('+') or val.startswith('-'):
                        val = val[1:]
            
            print(f"处理后的值: {val}, 类型: {type(val)}")
            
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
            # 获取所有编辑后的值
            edited_values = [e.get() for e in entries]
            print(f"编辑后的值: {edited_values}")
            valid = True
            
            # 验证必填字段
            for idx, (val, typ, err_lbl) in enumerate(zip(edited_values, field_types, error_labels)):
                err_lbl.config(text="")
                # 验证字段值
                if idx in [0, 1, 2, 3, 4] and not val:  # 前5个字段是必填的，出库策略可以为空
                    err_lbl.config(text=f"{display_fields[idx]}不能为空")
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
                # 读取原始values，准备更新
                new_vals = list(values)
                
                # 更新需要保存的字段值
                new_vals[0] = edited_values[0]  # 物品
                
                # 确保数量为整数
                try:
                    new_vals[2] = int(edited_values[1])  # 数量
                    print(f"保存数量: {edited_values[1]} -> {new_vals[2]}")
                except ValueError as e:
                    print(f"数量转换错误: {e}")
                    new_vals[2] = 0
                
                # 确保一口价为浮点数
                try:
                    new_vals[3] = float(edited_values[2])  # 一口价
                    print(f"保存一口价: {edited_values[2]} -> {new_vals[3]}")
                except ValueError as e:
                    print(f"一口价转换错误: {e}")
                    new_vals[3] = 0.0
                
                new_vals[4] = float(edited_values[3])  # 目标买入价
                new_vals[5] = float(edited_values[4])  # 计划卖出价
                
                # 更新出库策略
                if len(new_vals) > 9:
                    new_vals[9] = edited_values[5]  # 出库策略
                else:
                    # 如果原来没有这个字段，扩展列表
                    while len(new_vals) < 10:
                        new_vals.append("")
                    new_vals[9] = edited_values[5]
                
                # 计算自动字段
                quantity = new_vals[2]
                target_price = new_vals[4]
                planned_price = new_vals[5]
                
                # 计算保本价、利润和利润率
                new_vals[6] = round(target_price * 1.03) if target_price else 0
                new_vals[7] = (planned_price - target_price) * quantity if planned_price and target_price else 0
                new_vals[8] = round((planned_price - target_price) / target_price * 100, 2) if planned_price and target_price and target_price != 0 else 0
                
            except Exception as e:
                error_labels[0].config(text=f"计算错误: {str(e)}")
                entries[0].focus_set()
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
                'strategy': new_vals[9] if len(new_vals) > 9 else ""
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
                
            # OCR识别的字段: 物品名称、数量、一口价 - 不添加前缀
            item_name_display = item['item_name'] if item['item_name'] else ""
            
            # 格式化数字显示 - 只在有值时显示
            quantity = item['quantity']
            quantity_display = f"{quantity:,}" if quantity and quantity > 0 else ("0" if quantity == 0 else "")
            
            market_price = item['market_price']
            market_price_display = f"{int(market_price):,}" if market_price and market_price > 0 else ("0" if market_price == 0 else "")
            
            # 人工编辑的字段: 目标买入价、计划卖出价、出库策略 - 不添加[M]前缀
            target_price = item['target_price']
            target_price_display = f"{int(target_price):,}" if target_price and target_price > 0 else ("0" if target_price == 0 else "")
            
            planned_price = item['planned_price']
            planned_price_display = f"{int(planned_price):,}" if planned_price and planned_price > 0 else ("0" if planned_price == 0 else "")
            
            strategy = item['strategy']
            strategy_display = strategy if strategy else ""
            
            # 自动计算的字段: 保本价、利润、利润率 - 不添加前缀
            break_even_price = item['break_even_price']
            break_even_price_display = f"{int(break_even_price):,}" if break_even_price and break_even_price > 0 else ("0" if break_even_price == 0 else "")
            
            profit = item['profit']
            # 利润可能为负值，所以特殊处理
            if profit:
                if profit > 0:
                    profit_display = f"+{int(profit):,}"
                else:
                    profit_display = f"-{abs(int(profit)):,}"
            else:
                profit_display = "0"
            
            profit_rate = item['profit_rate']
            # 利润率也可能为负值
            if profit_rate:
                if profit_rate > 0:
                    profit_rate_display = f"+{profit_rate:.2f}%"
                else:
                    profit_rate_display = f"-{abs(profit_rate):.2f}%"
            else:
                profit_rate_display = "0.00%"
            
            # 确定是否有人工编辑的字段 - 如果有，添加到标签中
            if target_price > 0 or planned_price > 0 or strategy:
                tags.append('manual_field')
            
            # 插入行
            self.monitor_tree.insert('', 'end', values=(
                item_name_display,
                item['monitor_time'].strftime("%Y-%m-%d %H:%M:%S") if hasattr(item['monitor_time'], 'strftime') else str(item['monitor_time']),
                quantity_display,
                market_price_display,
                target_price_display,
                planned_price_display,
                break_even_price_display,
                profit_display,
                profit_rate_display,
                strategy_display
            ), tags=tags)
            
        # 更新状态栏
        self.status_var.set(f"共 {len(table_data)} 条记录  |  上次更新: {datetime.now().strftime('%H:%M:%S')}") 