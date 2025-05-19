import os
import tempfile
import webbrowser
import logging
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb

class EmailPreviewDialog:
    """邮件HTML预览对话框"""
    
    def __init__(self, subject, html_content):
        """
        初始化预览对话框
        
        Args:
            subject: 邮件主题
            html_content: HTML格式的邮件内容
        """
        self.subject = subject
        self.html_content = html_content
        self.logger = logging.getLogger(__name__)
        
    def show(self):
        """显示邮件预览"""
        try:
            # 创建临时HTML文件
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
                # 构建完整的HTML文档，包括标题和内容
                complete_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{self.subject}</title>
                    <style>
                        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 0; padding: 20px; }}
                        .preview-header {{ background-color: #f3f3f3; padding: 10px; border-bottom: 1px solid #ddd; margin-bottom: 20px; }}
                        .preview-subject {{ font-size: 18px; font-weight: bold; }}
                        .preview-note {{ font-size: 12px; color: #777; margin-top: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="preview-header">
                        <div class="preview-subject">邮件主题: {self.subject}</div>
                        <div class="preview-note">这是预览效果，实际邮件可能会有细微差异</div>
                    </div>
                    {self.html_content}
                </body>
                </html>
                """
                f.write(complete_html)
                temp_path = f.name
                
            # 在默认浏览器中打开临时文件
            webbrowser.open('file://' + os.path.abspath(temp_path))
            
            self.logger.info(f"打开邮件预览: {self.subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"无法显示邮件预览: {str(e)}", exc_info=True)
            return False


class HTMLPreviewWindow(tk.Toplevel):
    """HTML预览窗口（备用方案，需要tkinterweb库）"""
    
    def __init__(self, parent, subject, html_content):
        """初始化预览窗口"""
        super().__init__(parent)
        self.parent = parent
        
        # 设置窗口属性
        self.title(f"邮件预览 - {subject}")
        self.geometry("800x600")  # 较大的预览窗口
        self.resizable(True, True)
        self.transient(parent)  # 设置为父窗口的临时窗口
        
        try:
            # 尝试导入tkinterweb
            from tkinterweb import HtmlFrame
            
            # 创建框架
            frame = tb.Frame(self)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 创建HTML显示框架
            html_frame = HtmlFrame(frame)
            html_frame.pack(fill=tk.BOTH, expand=True)
            
            # 加载HTML内容
            html_frame.load_html(html_content)
            
            # 添加关闭按钮
            tb.Button(self, text="关闭", command=self.destroy, bootstyle="secondary").pack(pady=10)
            
        except ImportError:
            # 如果无法导入tkinterweb，显示错误消息
            message = "无法加载HTML预览。\n\n请安装tkinterweb库或使用外部浏览器预览。"
            tb.Label(
                self, 
                text=message,
                bootstyle="danger",
                font=("Microsoft YaHei", 12),
                justify=tk.CENTER
            ).pack(expand=True, padx=20, pady=20)
            
            tb.Button(
                self, 
                text="关闭", 
                command=self.destroy, 
                bootstyle="secondary"
            ).pack(pady=10)
        
        # 居中显示窗口
        self.center_window()
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}") 