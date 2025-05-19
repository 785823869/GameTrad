import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox
from src.utils.email_sender import QQEmailSender

class EmailConfigDialog(tk.Toplevel):
    """邮件配置对话框"""
    
    def __init__(self, parent):
        """初始化对话框"""
        super().__init__(parent)
        self.parent = parent
        
        # 设置对话框属性
        self.title("QQ邮箱推送设置")
        self.geometry("550x600")
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
        ).pack(pady=(0, 20))
        
        # 启用选项
        self.enable_var = tk.BooleanVar(value=False)
        tb.Checkbutton(
            self.main_frame,
            text="启用邮件推送功能",
            variable=self.enable_var,
            bootstyle="primary",
            command=self.toggle_enable
        ).pack(anchor="w", pady=(0, 15))
        
        # 创建配置区域
        self.config_frame = tb.LabelFrame(self.main_frame, text="邮箱配置", padding=15)
        self.config_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
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
        
        # 重试设置
        retry_frame = tb.LabelFrame(self.main_frame, text="高级设置", padding=10)
        retry_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 重试次数
        tb.Label(retry_frame, text="发送失败重试次数:").grid(row=0, column=0, sticky="w", pady=8, padx=5)
        self.retry_count_var = tk.IntVar(value=3)
        tb.Spinbox(retry_frame, from_=1, to=10, textvariable=self.retry_count_var, width=5).grid(row=0, column=1, sticky="w")
        
        # 重试间隔
        tb.Label(retry_frame, text="重试间隔(秒):").grid(row=0, column=2, sticky="w", pady=8, padx=(20, 5))
        self.retry_delay_var = tk.IntVar(value=5)
        tb.Spinbox(retry_frame, from_=1, to=30, textvariable=self.retry_delay_var, width=5).grid(row=0, column=3, sticky="w")
        
        # 测试按钮
        tb.Button(
            self.main_frame,
            text="测试连接",
            bootstyle="info",
            command=self.test_connection
        ).pack(side=tk.LEFT, padx=5, pady=10)
        
        # 说明文本
        tb.Label(
            self.main_frame,
            text="获取授权码：QQ邮箱->设置->账户->POP3/SMTP服务->开启->生成授权码",
            bootstyle="secondary",
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT, padx=10)
        
        # 底部按钮区域
        button_frame = tb.Frame(self.main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))
        
        tb.Button(
            button_frame,
            text="保存",
            bootstyle="primary",
            command=self.save_config
        ).pack(side=tk.RIGHT, padx=5)
        
        tb.Button(
            button_frame,
            text="取消",
            bootstyle="secondary",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # 设置列权重，让第一列填充空间
        self.config_frame.columnconfigure(1, weight=1)
    
    def toggle_enable(self):
        """切换启用状态"""
        enabled = self.enable_var.get()
        state = "normal" if enabled else "disabled"
        
        # 设置所有配置控件的状态
        for child in self.config_frame.winfo_children():
            try:
                child.configure(state=state)
            except:
                pass
        
        # 特殊处理容器中的控件
        if hasattr(self, 'recipients_text'):
            self.recipients_text.configure(state=state)
    
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
        
        # 设置控件启用状态
        self.toggle_enable()
    
    def save_config(self):
        """保存配置"""
        try:
            # 收集UI中的值
            new_config = {
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
                
                if not recipients:
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
        required_fields = [
            ("smtp_server", "SMTP服务器"),
            ("smtp_port", "SMTP端口"),
            ("username", "邮箱账号"),
            ("password", "邮箱授权码")
        ]
        
        for field, name in required_fields:
            if not test_config[field]:
                messagebox.showerror("错误", f"{name}不能为空")
                return
        
        # 显示测试中对话框
        self.config_backup = self.email_sender.config.copy()
        self.email_sender.config.update(test_config)
        
        # 执行测试
        success, message = self.email_sender.test_connection()
        
        # 恢复原配置
        self.email_sender.config = self.config_backup
        
        # 显示结果
        if success:
            messagebox.showinfo("测试成功", "邮箱连接测试成功！")
        else:
            messagebox.showerror("测试失败", f"邮箱连接测试失败: {message}")
    
    def center_window(self):
        """使窗口在屏幕上居中"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y)) 