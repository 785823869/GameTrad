import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox, scrolledtext
from src.utils.email_sender import QQEmailSender
from src.gui.dialogs.email_preview_dialog import EmailPreviewDialog
from src.utils import clipboard_helper

class EmailConfigDialog(tk.Toplevel):
    """邮件配置对话框"""
    
    def __init__(self, parent):
        """初始化对话框"""
        super().__init__(parent)
        self.parent = parent
        
        # 记录打开对话框前的图片剪贴板状态
        self.previous_clipboard_state = clipboard_helper.enable_image_clipboard
        
        # 临时禁用图片剪贴板功能
        clipboard_helper.enable_image_clipboard = False
        
        # 设置对话框属性
        self.title("QQ邮箱推送设置")
        self.geometry("700x750")  # 增加窗口高度确保底部按钮可见
        self.resizable(False, False)
        self.transient(parent)  # 设置为父窗口的临时窗口
        self.grab_set()  # 模态对话框
        
        # 邮件发送器实例
        self.email_sender = QQEmailSender()
        self.config = self.email_sender.config.copy()
        
        # 创建UI
        self.create_widgets()
        
        # 加载配置到UI
        self.load_config_to_ui()
        
        # 居中显示
        self.center_window()
        
        # 设置关闭事件处理
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        """关闭窗口时恢复之前的图片剪贴板状态"""
        # 恢复之前的图片剪贴板状态
        clipboard_helper.enable_image_clipboard = self.previous_clipboard_state
        
        # 关闭窗口
        self.destroy()
    
    def create_widgets(self):
        """创建对话框控件"""
        # 创建主容器
        self.main_frame = tb.Frame(self, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题
        tb.Label(
            self.main_frame, 
            text="QQ邮箱推送设置",
            font=("Microsoft YaHei", 16, "bold"),
            bootstyle="primary",
        ).pack(pady=(0, 15))
        
        # 启用选项
        self.enable_var = tk.BooleanVar(value=False)
        tb.Checkbutton(
            self.main_frame,
            text="启用邮件推送功能",
            variable=self.enable_var,
            bootstyle="primary",
            command=self.toggle_enable
        ).pack(anchor="w", pady=(0, 10))
        
        # 创建标签页控件
        self.notebook = tb.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建基本配置标签页
        self.basic_config_tab = tb.Frame(self.notebook, padding=10)
        self.notebook.add(self.basic_config_tab, text="基本设置")
        self._create_basic_config_tab()
        
        # 创建邮件模板标签页
        self.templates_tab = tb.Frame(self.notebook, padding=10)
        self.notebook.add(self.templates_tab, text="邮件模板")
        self._create_templates_tab()
        
        # 创建自定义模板标签页
        self.custom_templates_tab = tb.Frame(self.notebook, padding=10)
        self.notebook.add(self.custom_templates_tab, text="自定义模板")
        self._create_custom_templates_tab()
        
        # 创建高级设置标签页
        self.advanced_tab = tb.Frame(self.notebook, padding=10)
        self.notebook.add(self.advanced_tab, text="高级设置")
        self._create_advanced_tab()
        
        # 说明文本
        tb.Label(
            self.main_frame,
            text="获取授权码：QQ邮箱->设置->账户->POP3/SMTP服务->开启->生成授权码",
            bootstyle="secondary",
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT, padx=10)
        
        # 底部按钮区域
        button_frame = tb.Frame(self.main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # 测试连接按钮
        tb.Button(
            button_frame,
            text="测试连接",
            bootstyle="info",
            command=self.test_connection
        ).pack(side=tk.LEFT, padx=5)
        
        # 测试发送按钮
        self.test_send_btn = tb.Button(
            button_frame,
            text="发送测试邮件",
            bootstyle="success",
            command=self.send_test_email
        )
        self.test_send_btn.pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        tb.Button(
            button_frame,
            text="保存",
            bootstyle="primary",
            command=self.save_config
        ).pack(side=tk.RIGHT, padx=5)
        
        # 取消按钮
        tb.Button(
            button_frame,
            text="取消",
            bootstyle="secondary",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _create_basic_config_tab(self):
        """创建基本设置标签页内容"""
        # 创建配置区域
        self.config_frame = tb.LabelFrame(self.basic_config_tab, text="邮箱配置", padding=15)
        self.config_frame.pack(fill=tk.BOTH, expand=True)
        
        # SMTP服务器
        tb.Label(self.config_frame, text="SMTP服务器:").grid(row=0, column=0, sticky="w", pady=8)
        self.smtp_server_var = tk.StringVar()
        tb.Entry(self.config_frame, textvariable=self.smtp_server_var, width=30).grid(row=0, column=1, sticky="ew", padx=5)
        tb.Label(self.config_frame, text="QQ邮箱为: smtp.qq.com", bootstyle="secondary").grid(row=0, column=2, sticky="w", padx=5)
        
        # SMTP端口
        tb.Label(self.config_frame, text="SMTP端口:").grid(row=1, column=0, sticky="w", pady=8)
        self.smtp_port_var = tk.StringVar()
        tb.Entry(self.config_frame, textvariable=self.smtp_port_var, width=30).grid(row=1, column=1, sticky="ew", padx=5)
        tb.Label(self.config_frame, text="QQ邮箱为: 587", bootstyle="secondary").grid(row=1, column=2, sticky="w", padx=5)
        
        # 邮箱账号
        tb.Label(self.config_frame, text="邮箱账号:").grid(row=2, column=0, sticky="w", pady=8)
        self.username_var = tk.StringVar()
        tb.Entry(self.config_frame, textvariable=self.username_var, width=30).grid(row=2, column=1, sticky="ew", padx=5)
        tb.Label(self.config_frame, text="完整QQ邮箱地址", bootstyle="secondary").grid(row=2, column=2, sticky="w", padx=5)
        
        # 授权码
        tb.Label(self.config_frame, text="邮箱授权码:").grid(row=3, column=0, sticky="w", pady=8)
        self.password_var = tk.StringVar()
        tb.Entry(self.config_frame, textvariable=self.password_var, width=30, show="*").grid(row=3, column=1, sticky="ew", padx=5)
        tb.Label(self.config_frame, text="QQ邮箱设置->账户->开启POP3/SMTP", bootstyle="secondary").grid(row=3, column=2, sticky="w", padx=5)
        
        # 发件人名称
        tb.Label(self.config_frame, text="发件人名称:").grid(row=4, column=0, sticky="w", pady=8)
        self.sender_var = tk.StringVar()
        tb.Entry(self.config_frame, textvariable=self.sender_var, width=30).grid(row=4, column=1, sticky="ew", padx=5)
        tb.Label(self.config_frame, text="显示的发件人名称", bootstyle="secondary").grid(row=4, column=2, sticky="w", padx=5)
        
        # 收件人列表
        tb.Label(self.config_frame, text="收件人列表:").grid(row=5, column=0, sticky="w", pady=8)
        self.recipients_frame = tb.Frame(self.config_frame)
        self.recipients_frame.grid(row=5, column=1, columnspan=2, sticky="ew", pady=8)
        
        self.recipients_text = tb.Text(self.recipients_frame, height=5, width=40)
        self.recipients_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        recipient_scrollbar = tb.Scrollbar(self.recipients_frame, command=self.recipients_text.yview)
        recipient_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recipients_text.config(yscrollcommand=recipient_scrollbar.set)
        
        tb.Label(self.config_frame, text="每行一个邮箱地址", bootstyle="secondary").grid(row=6, column=1, sticky="w", pady=2)
        
        # 底部按钮区域
        bottom_frame = tb.Frame(self.basic_config_tab)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        # 添加单独的保存基本设置按钮
        tb.Button(
            bottom_frame,
            text="保存基本设置",
            bootstyle="primary",
            command=self.save_basic_settings,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # 添加测试连接按钮
        tb.Button(
            bottom_frame,
            text="测试连接",
            bootstyle="info",
            command=self.test_connection,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        # 创建基本设置标签页中的测试邮件按钮
        self.tab_test_send_btn = tb.Button(
            bottom_frame,
            text="发送测试邮件",
            bootstyle="success",
            command=self.send_test_email,
            width=15
        )
        self.tab_test_send_btn.pack(side=tk.RIGHT, padx=5)
        
        # 设置列权重，让第一列填充空间
        self.config_frame.columnconfigure(1, weight=1)
    
    def _create_templates_tab(self):
        """创建邮件模板标签页内容"""
        # 模板选择区域
        select_frame = tb.LabelFrame(self.templates_tab, text="模板选择", padding=10)
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        tb.Label(select_frame, text="选择模板:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.template_var = tk.StringVar(value="trade_update")
        
        # 获取可用模板
        built_in_templates = [
            ("trade_update", "交易更新通知"), 
            ("system_alert", "系统警报"), 
            ("daily_report", "日报"), 
            ("backup_success", "备份成功通知")
        ]
        
        # 合并内置模板和自定义模板
        all_templates = [t[0] for t in built_in_templates]
        all_templates.extend(self.email_sender.custom_templates.keys())
        
        self.template_menu = tb.Combobox(
            select_frame, 
            textvariable=self.template_var,
            values=all_templates,
            state="readonly",
            width=20
        )
        self.template_menu.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        self.template_menu.bind("<<ComboboxSelected>>", self.update_template_preview)
        
        # 模板名称对应显示名
        self.template_names = {t[0]: t[1] for t in built_in_templates}
        # 添加自定义模板到显示名字典
        for name in self.email_sender.custom_templates:
            self.template_names[name] = f"自定义: {name}"
        
        # 预览按钮 - 使用新的HTML预览功能
        preview_btn = tb.Button(
            select_frame,
            text="预览",
            bootstyle="info",
            command=self.show_html_preview
        )
        preview_btn.grid(row=0, column=2, sticky="w", pady=5, padx=5)
        
        # 模板预览区域
        preview_frame = tb.LabelFrame(self.templates_tab, text="模板预览", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # 预览标题
        tb.Label(preview_frame, text="主题:").grid(row=0, column=0, sticky="w", pady=5)
        self.preview_subject_var = tk.StringVar()
        tb.Entry(preview_frame, textvariable=self.preview_subject_var, state="normal", width=60).grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        
        # 预览内容
        tb.Label(preview_frame, text="内容:").grid(row=1, column=0, sticky="nw", pady=5)
        self.preview_content = scrolledtext.ScrolledText(preview_frame, height=15, width=60, wrap=tk.WORD)
        self.preview_content.grid(row=1, column=1, sticky="nsew", pady=5, padx=5)
        
        # 设置列权重
        preview_frame.columnconfigure(1, weight=1)
        
        # 初始显示第一个模板的预览
        self.update_template_preview(None)
    
    def _create_custom_templates_tab(self):
        """创建自定义模板标签页内容"""
        # 模板管理区域
        manage_frame = tb.Frame(self.custom_templates_tab)
        manage_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 模板名称输入和选择
        template_info_frame = tb.LabelFrame(manage_frame, text="模板管理", padding=10)
        template_info_frame.pack(fill=tk.X, expand=True, padx=10, pady=5)
        
        # 模板名称输入区域
        name_frame = tb.Frame(template_info_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        tb.Label(name_frame, text="模板名称:").pack(side=tk.LEFT, padx=5)
        self.custom_template_name_var = tk.StringVar()
        custom_name_entry = tb.Entry(name_frame, textvariable=self.custom_template_name_var, width=20)
        custom_name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 已保存模板选择区域
        saved_frame = tb.Frame(template_info_frame)
        saved_frame.pack(fill=tk.X, pady=5)
        
        tb.Label(saved_frame, text="已保存模板:").pack(side=tk.LEFT, padx=5)
        self.saved_templates_var = tk.StringVar()
        self.saved_templates_combo = tb.Combobox(saved_frame, textvariable=self.saved_templates_var, width=20)
        self.saved_templates_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.saved_templates_combo.bind("<<ComboboxSelected>>", self.load_selected_template)
        
        # 刷新按钮
        tb.Button(
            saved_frame, 
            text="刷新", 
            bootstyle="secondary", 
            command=self.refresh_template_list,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        
        # 按钮区域
        button_frame = tb.Frame(template_info_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 新建、保存、删除按钮
        tb.Button(button_frame, text="新建模板", bootstyle="success", width=12, 
                 command=self.new_custom_template).pack(side=tk.LEFT, padx=5)
        tb.Button(button_frame, text="保存模板", bootstyle="primary", width=12,
                 command=self.save_custom_template).pack(side=tk.LEFT, padx=5)
        tb.Button(button_frame, text="删除模板", bootstyle="danger", width=12,
                 command=self.delete_custom_template).pack(side=tk.LEFT, padx=5)
        
        # 创建左右分栏布局
        content_frame = tb.Frame(self.custom_templates_tab)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 左侧编辑区域
        left_frame = tb.LabelFrame(content_frame, text="模板编辑", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 主题编辑
        tb.Label(left_frame, text="主题:").grid(row=0, column=0, sticky="w", pady=5)
        self.custom_subject_var = tk.StringVar()
        tb.Entry(left_frame, textvariable=self.custom_subject_var, width=45).grid(row=0, column=1, sticky="ew", pady=5)
        
        # 内容编辑
        tb.Label(left_frame, text="HTML内容:").grid(row=1, column=0, sticky="nw", pady=5)
        self.custom_content_text = scrolledtext.ScrolledText(left_frame, height=15, width=45, wrap=tk.WORD)
        self.custom_content_text.grid(row=1, column=1, sticky="nsew", pady=5)
        
        # 设置列权重
        left_frame.columnconfigure(1, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # 右侧变量提示区域
        right_frame = tb.LabelFrame(content_frame, text="可用变量", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        variables_text = (
            "在模板中使用这些变量:\n\n"
            "{{item_name}} - 物品名称\n\n"
            "{{price}} - 价格\n\n"
            "{{quantity}} - 数量\n\n"
            "{{time}} - 时间\n\n"
            "{{server}} - 服务器\n\n"
            "{{status}} - 状态\n\n"
            "{{message}} - 消息内容\n\n"
            "{{filename}} - 文件名\n\n"
            "{{path}} - 路径\n\n"
            "{{size}} - 大小\n\n"
        )
        
        var_label = tb.Label(right_frame, text=variables_text, justify=tk.LEFT)
        var_label.pack(anchor="nw", fill=tk.BOTH)
        
        # 首次加载已保存模板列表
        self.refresh_template_list()
    
    def _create_advanced_tab(self):
        """创建高级设置标签页内容"""
        # 重试设置
        retry_frame = tb.LabelFrame(self.advanced_tab, text="发送设置", padding=10)
        retry_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 重试次数
        tb.Label(retry_frame, text="发送失败重试次数:").grid(row=0, column=0, sticky="w", pady=8, padx=5)
        self.retry_count_var = tk.IntVar(value=3)
        tb.Spinbox(retry_frame, from_=1, to=10, textvariable=self.retry_count_var, width=5).grid(row=0, column=1, sticky="w")
        
        # 重试间隔
        tb.Label(retry_frame, text="重试间隔(秒):").grid(row=0, column=2, sticky="w", pady=8, padx=(20, 5))
        self.retry_delay_var = tk.IntVar(value=5)
        tb.Spinbox(retry_frame, from_=1, to=30, textvariable=self.retry_delay_var, width=5).grid(row=0, column=3, sticky="w")
        
        # 日志设置
        log_frame = tb.LabelFrame(self.advanced_tab, text="日志设置", padding=10)
        log_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 启用邮件发送日志
        self.enable_log_var = tk.BooleanVar(value=True)
        tb.Checkbutton(
            log_frame,
            text="记录邮件发送日志",
            variable=self.enable_log_var,
            bootstyle="primary"
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        # 设置日志保留天数
        tb.Label(log_frame, text="日志保留天数:").grid(row=0, column=1, sticky="w", pady=5, padx=(20, 5))
        self.log_days_var = tk.IntVar(value=30)
        tb.Spinbox(log_frame, from_=1, to=365, textvariable=self.log_days_var, width=5).grid(row=0, column=2, sticky="w")
        
        # 计划任务设置
        schedule_frame = tb.LabelFrame(self.advanced_tab, text="计划任务", padding=10)
        schedule_frame.pack(fill=tk.X)
        
        # 启用日报邮件
        self.enable_daily_report_var = tk.BooleanVar(value=False)
        tb.Checkbutton(
            schedule_frame,
            text="启用每日报告",
            variable=self.enable_daily_report_var,
            bootstyle="primary"
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        # 日报发送时间
        tb.Label(schedule_frame, text="发送时间:").grid(row=0, column=1, sticky="w", pady=5, padx=(20, 5))
        self.daily_report_hour_var = tk.IntVar(value=20)
        tb.Spinbox(schedule_frame, from_=0, to=23, width=3, textvariable=self.daily_report_hour_var).grid(row=0, column=2, sticky="w")
        tb.Label(schedule_frame, text=":").grid(row=0, column=3)
        self.daily_report_minute_var = tk.IntVar(value=0)
        tb.Spinbox(schedule_frame, from_=0, to=59, width=3, textvariable=self.daily_report_minute_var).grid(row=0, column=4, sticky="w")
    
    def toggle_enable(self):
        """切换启用状态"""
        enabled = self.enable_var.get()
        state = "normal" if enabled else "disabled"
        
        # 设置测试发送按钮状态
        self.test_send_btn.configure(state=state)
        
        # 设置标签页中的测试邮件按钮状态
        if hasattr(self, 'tab_test_send_btn'):
            self.tab_test_send_btn.configure(state=state)
        
        # 设置所有配置控件的状态
        for child in self.config_frame.winfo_children():
            try:
                child.configure(state=state)
            except:
                pass
        
        # 特殊处理容器中的控件
        if hasattr(self, 'recipients_text'):
            self.recipients_text.configure(state=state)
    
    def update_template_preview(self, event=None):
        """更新模板预览"""
        try:
            template_name = self.template_var.get()
            
            # 创建示例上下文
            context = {
                "item_name": "测试物品",
                "price": "1000",
                "quantity": "5",
                "time": "2023-05-19 14:30:00",
                "server": "测试服务器",
                "status": "成功",
                "message": "这是一条测试消息",
                "filename": "backup_20230519.sql",
                "path": "/data/backups/backup_20230519.sql",
                "size": "1.2 MB"
            }
            
            # 首先检查是否是自定义模板
            if template_name in self.email_sender.custom_templates:
                template_data = self.email_sender.custom_templates[template_name]
                
                # 渲染模板
                subject = self.email_sender.render_template(template_data["subject"], context)
                content = self.email_sender.render_template(template_data["content"], context)
                
                # 更新预览
                self.preview_subject_var.set(subject)
                
                # 更新内容预览
                self.preview_content.delete(1.0, tk.END)
                self.preview_content.insert(tk.END, content)
                
                # 确保UI更新
                self.update_idletasks()
                return
                
            # 否则使用内置模板
            template_func = self.email_sender._get_template(template_name)
            if template_func:
                subject, content, is_html = template_func(context)
                
                # 更新预览
                self.preview_subject_var.set(subject)
                
                # 更新内容预览
                self.preview_content.delete(1.0, tk.END)
                self.preview_content.insert(tk.END, content)
                
                # 确保UI更新
                self.update_idletasks()
            else:
                self.preview_subject_var.set(f"未找到模板: {template_name}")
                self.preview_content.delete(1.0, tk.END)
                self.preview_content.insert(tk.END, "无法加载选中的模板。")
                
        except Exception as e:
            import traceback
            error_msg = f"预览模板时出错: {str(e)}\n{traceback.format_exc()}"
            self.preview_subject_var.set("模板预览错误")
            self.preview_content.delete(1.0, tk.END)
            self.preview_content.insert(tk.END, error_msg)
            
            # 记录错误以便调试
            self.email_sender.logger.error(error_msg)
    
    def new_custom_template(self):
        """新建自定义模板"""
        # 清空表单
        self.custom_template_name_var.set("my_template")
        self.custom_subject_var.set("自定义邮件主题")
        self.custom_content_text.delete(1.0, tk.END)
        self.custom_content_text.insert(tk.END, "<html><body><h1>自定义邮件内容</h1><p>在此编辑您的HTML内容</p></body></html>")
    
    def save_custom_template(self):
        """保存自定义模板"""
        template_name = self.custom_template_name_var.get().strip()
        subject = self.custom_subject_var.get().strip()
        content = self.custom_content_text.get(1.0, tk.END).strip()
        
        # 验证输入
        if not template_name:
            messagebox.showerror("错误", "请输入模板名称")
            return
            
        if not subject:
            messagebox.showerror("错误", "请输入邮件主题")
            return
            
        if not content:
            messagebox.showerror("错误", "请输入模板内容")
            return
        
        # 保存模板
        try:
            success = self.email_sender.save_custom_template(
                template_name=template_name,
                subject=subject,
                content=content,
                is_html=True
            )
            
            if success:
                messagebox.showinfo("成功", f"模板 '{template_name}' 保存成功")
            else:
                messagebox.showerror("错误", "保存模板失败")
        except Exception as e:
            messagebox.showerror("错误", f"保存模板时出错: {str(e)}")
    
    def delete_custom_template(self):
        """删除自定义模板"""
        template_name = self.custom_template_name_var.get().strip()
        
        if not template_name:
            messagebox.showerror("错误", "请输入要删除的模板名称")
            return
            
        if template_name not in self.email_sender.custom_templates:
            messagebox.showerror("错误", f"模板 '{template_name}' 不存在")
            return
            
        # 确认删除
        confirm = messagebox.askyesno("确认删除", f"确定要删除模板 '{template_name}' 吗？此操作不可恢复。")
        if not confirm:
            return
            
        # 执行删除
        try:
            success = self.email_sender.delete_custom_template(template_name)
            if success:
                messagebox.showinfo("成功", f"模板 '{template_name}' 已删除")
                # 清空表单
                self.custom_template_name_var.set("")
                self.custom_subject_var.set("")
                self.custom_content_text.delete(1.0, tk.END)
            else:
                messagebox.showerror("错误", "删除模板失败")
        except Exception as e:
            messagebox.showerror("错误", f"删除模板时出错: {str(e)}")
    
    def send_test_email(self):
        """发送测试邮件"""
        if not self.enable_var.get():
            messagebox.showwarning("警告", "邮件功能未启用，请先启用邮件功能")
            return
        
        # 收集当前UI中的配置
        test_config = self._collect_config()
        
        if not test_config.get("enabled"):
            messagebox.showwarning("警告", "邮件功能未启用")
            return
        
        if not test_config.get("smtp_server") or not test_config.get("username"):
            messagebox.showwarning("警告", "请先完成邮箱配置")
            return
            
        if not test_config.get("recipients"):
            messagebox.showwarning("警告", "请至少添加一个收件人")
            return
        
        # 保存当前配置用于测试
        config_backup = self.email_sender.config.copy()
        self.email_sender.config.update(test_config)
        
        try:
            # 发送测试邮件
            template_name = self.template_var.get()
            context = {
                "item_name": "测试物品",
                "price": "1000",
                "quantity": "5",
                "time": "2023-05-19 14:30:00",
                "server": "测试服务器",
                "status": "成功",
                "message": "这是一封测试邮件，用于验证QQ邮箱推送功能是否正常。",
                "filename": "backup_20230519.sql",
                "path": "/data/backups/backup_20230519.sql",
                "size": "1.2 MB"
            }
            
            # 从UI获取收件人列表
            recipients_text = self.recipients_text.get(1.0, tk.END).strip()
            recipients = [r.strip() for r in recipients_text.split("\n") if r.strip()]
            
            if not recipients:
                messagebox.showwarning("警告", "收件人列表为空，请在基本设置标签页的收件人列表中添加至少一个邮箱地址")
                return
            
            # 发送测试邮件，明确指定收件人参数
            success = self.email_sender.send_template_email(
                template_name=template_name,
                context=context,
                recipients=recipients,  # 直接传递收件人列表
                immediate=True  # 立即发送，而不是加入队列
            )
            
            if success:
                messagebox.showinfo("成功", f"测试邮件已发送至以下收件人：\n{', '.join(recipients)}\n\n请检查收件箱")
            else:
                messagebox.showerror("错误", "测试邮件发送失败，请检查日志")
        except Exception as e:
            messagebox.showerror("错误", f"发送测试邮件时出错: {str(e)}")
        finally:
            # 恢复原始配置
            self.email_sender.config = config_backup
    
    def _collect_config(self):
        """收集UI中的配置"""
        try:
            # 收集UI中的值
            config = {
                "enabled": self.enable_var.get(),
                "smtp_server": self.smtp_server_var.get(),
                "smtp_port": int(self.smtp_port_var.get()),
                "username": self.username_var.get(),
                "password": self.password_var.get(),
                "sender": self.sender_var.get(),
                "retry_count": self.retry_count_var.get(),
                "retry_delay": self.retry_delay_var.get()
            }
            
            # 收集收件人列表
            recipients_text = self.recipients_text.get(1.0, tk.END).strip()
            recipients = [r.strip() for r in recipients_text.split("\n") if r.strip()]
            config["recipients"] = recipients
            
            # 收集高级设置
            config["enable_log"] = self.enable_log_var.get()
            config["log_days"] = self.log_days_var.get()
            config["enable_daily_report"] = self.enable_daily_report_var.get()
            config["daily_report_time"] = f"{self.daily_report_hour_var.get():02d}:{self.daily_report_minute_var.get():02d}"
            
            return config
        except Exception as e:
            messagebox.showerror("错误", f"收集配置时出错: {str(e)}")
            return {}
    
    def load_config_to_ui(self):
        """将配置加载到UI控件"""
        self.enable_var.set(self.config.get("enabled", False))
        self.smtp_server_var.set(self.config.get("smtp_server", "smtp.qq.com"))
        self.smtp_port_var.set(str(self.config.get("smtp_port", 587)))
        self.username_var.set(self.config.get("username", ""))
        self.password_var.set(self.config.get("password", ""))
        self.sender_var.set(self.config.get("sender", "GameTrad系统"))
        self.retry_count_var.set(self.config.get("retry_count", 3))
        self.retry_delay_var.set(self.config.get("retry_delay", 5))
        
        # 设置收件人列表
        recipients = self.config.get("recipients", [])
        self.recipients_text.delete(1.0, tk.END)
        self.recipients_text.insert(tk.END, "\n".join(recipients))
        
        # 设置高级选项
        self.enable_log_var.set(self.config.get("enable_log", True))
        self.log_days_var.set(self.config.get("log_days", 30))
        self.enable_daily_report_var.set(self.config.get("enable_daily_report", False))
        
        # 解析日报时间
        daily_report_time = self.config.get("daily_report_time", "20:00")
        try:
            hour, minute = daily_report_time.split(":")
            self.daily_report_hour_var.set(int(hour))
            self.daily_report_minute_var.set(int(minute))
        except:
            self.daily_report_hour_var.set(20)
            self.daily_report_minute_var.set(0)
        
        # 设置控件启用状态
        self.toggle_enable()
    
    def save_config(self):
        """保存配置"""
        try:
            # 收集UI中的值
            new_config = self._collect_config()
            
            # 验证必要字段
            if new_config["enabled"]:
                required_fields = [
                    ("smtp_server", "SMTP服务器"),
                    ("smtp_port", "SMTP端口"),
                    ("username", "邮箱账号"),
                    ("password", "邮箱授权码")
                ]
                
                for field, name in required_fields:
                    if not new_config[field]:
                        messagebox.showerror("错误", f"{name}不能为空")
                        return
                
                if not new_config.get("recipients"):
                    messagebox.showerror("错误", "请至少添加一个收件人")
                    return
            
            # 保存配置
            success = self.email_sender.save_config(new_config)
            if success:
                messagebox.showinfo("成功", "邮箱配置已保存")
                self.destroy()
            else:
                messagebox.showerror("错误", "保存配置失败，请查看日志")
                
        except ValueError as e:
            messagebox.showerror("错误", f"数值格式错误: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置时出错: {str(e)}")
    
    def test_connection(self):
        """测试邮箱连接"""
        # 收集当前UI中的配置
        test_config = {
            "enabled": True,  # 测试时强制启用
            "smtp_server": self.smtp_server_var.get(),
            "smtp_port": int(self.smtp_port_var.get()),
            "username": self.username_var.get(),
            "password": self.password_var.get(),
            "sender": self.sender_var.get()
        }
        
        # 验证必要字段
        if not test_config["smtp_server"] or not test_config["username"] or not test_config["password"]:
            messagebox.showwarning("警告", "请先填写SMTP服务器、邮箱账号和授权码")
            return
        
        # 临时设置配置用于测试
        self.config_backup = self.email_sender.config.copy()
        self.email_sender.config.update(test_config)
        
        try:
            # 测试连接
            success, message = self.email_sender.test_connection()
            if success:
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)
        finally:
            # 恢复原始配置
            self.email_sender.config = self.config_backup
    
    def center_window(self):
        """使窗口在屏幕上居中"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y)) 

    def refresh_template_list(self):
        """刷新已保存模板列表"""
        template_list = list(self.email_sender.custom_templates.keys())
        self.saved_templates_combo['values'] = template_list
        
        # 只在有模板时设置当前值
        if template_list:
            self.saved_templates_combo.current(0)
            # 自动加载第一个模板
            self.load_selected_template(None)
    
    def load_selected_template(self, event):
        """加载选中的模板"""
        selected_template = self.saved_templates_var.get()
        if selected_template and selected_template in self.email_sender.custom_templates:
            template_data = self.email_sender.custom_templates[selected_template]
            self.custom_template_name_var.set(selected_template)
            self.custom_subject_var.set(template_data['subject'])
            self.custom_content_text.delete(1.0, tk.END)
            self.custom_content_text.insert(tk.END, template_data['content'])
    
    def show_html_preview(self):
        """显示HTML格式的邮件预览"""
        try:
            template_name = self.template_var.get()
            
            # 创建示例上下文
            context = {
                "item_name": "测试物品",
                "price": "1000",
                "quantity": "5",
                "time": "2023-05-19 14:30:00",
                "server": "测试服务器",
                "status": "成功",
                "message": "这是一条测试消息，用于验证预览功能。",
                "filename": "backup_20230519.sql",
                "path": "/data/backups/backup_20230519.sql",
                "size": "1.2 MB"
            }
            
            # 首先更新文本预览（保持原有功能)
            self.update_template_preview(None)
            
            # 获取预览内容
            subject = self.preview_subject_var.get()
            
            # 获取HTML内容
            html_content = ""
            
            # 首先检查是否是自定义模板
            if template_name in self.email_sender.custom_templates:
                template_data = self.email_sender.custom_templates[template_name]
                html_content = self.email_sender.render_template(template_data["content"], context)
            else:
                # 否则使用内置模板
                template_func = self.email_sender._get_template(template_name)
                if template_func:
                    _, html_content, _ = template_func(context)
            
            # 创建预览对话框
            preview = EmailPreviewDialog(subject, html_content)
            preview.show()
            
        except Exception as e:
            import traceback
            error_msg = f"预览模板时出错: {str(e)}\n{traceback.format_exc()}"
            messagebox.showerror("错误", f"无法显示预览: {str(e)}")
            self.email_sender.logger.error(error_msg)
    
    def save_basic_settings(self):
        """仅保存基本设置标签页中的配置信息"""
        try:
            # 收集基本设置中的值
            new_config = self.config.copy()  # 保留其他设置
            
            # 更新基本设置
            new_config.update({
                "enabled": self.enable_var.get(),
                "smtp_server": self.smtp_server_var.get(),
                "smtp_port": int(self.smtp_port_var.get()),
                "username": self.username_var.get(),
                "password": self.password_var.get(),
                "sender": self.sender_var.get(),
            })
            
            # 收集收件人列表
            recipients_text = self.recipients_text.get(1.0, tk.END).strip()
            recipients = [r.strip() for r in recipients_text.split("\n") if r.strip()]
            new_config["recipients"] = recipients
            
            # 验证必要字段
            if new_config["enabled"]:
                required_fields = [
                    ("smtp_server", "SMTP服务器"),
                    ("smtp_port", "SMTP端口"),
                    ("username", "邮箱账号"),
                    ("password", "邮箱授权码")
                ]
                
                for field, name in required_fields:
                    if not new_config[field]:
                        messagebox.showerror("错误", f"{name}不能为空")
                        return
                
                if not new_config.get("recipients"):
                    messagebox.showerror("错误", "请至少添加一个收件人")
                    return
            
            # 保存配置
            success = self.email_sender.save_config(new_config)
            if success:
                messagebox.showinfo("成功", "基本设置已保存")
                # 更新本地配置副本
                self.config = new_config
            else:
                messagebox.showerror("错误", "保存基本设置失败，请查看日志")
                
        except ValueError as e:
            messagebox.showerror("错误", f"数值格式错误: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存基本设置时出错: {str(e)}") 