"""
更新对话框 - 显示更新信息、下载进度和提供更新操作
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import webbrowser
import os
from src.utils.updater import AppUpdater

class UpdateDialog:
    """更新对话框类"""
    
    def __init__(self, parent, updater=None, update_url=None):
        """
        初始化更新对话框
        
        Args:
            parent: 父窗口
            updater: 更新器实例，如果为None则创建新实例
            update_url: 更新检查URL，仅在updater为None时使用
        """
        self.parent = parent
        self.updater = updater if updater else AppUpdater(update_url)
        self.dialog = None
        self.progress_var = None
        self.status_var = None
        self.download_button = None
        self.install_button = None
        self.cancel_button = None
        self.progress_bar = None
        self.notes_text = None
        self.download_path = None
        self._check_thread = None
        self.open_folder_button = None
    
    def show(self):
        """显示更新对话框并检查更新"""
        # 创建对话框
        self.dialog = tb.Toplevel(self.parent)
        self.dialog.title("检查更新")
        self.dialog.geometry("600x500")  # 进一步增加对话框大小
        self.dialog.minsize(550, 450)    # 设置最小大小
        self.dialog.resizable(True, True)  # 允许调整大小
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 设置对话框图标
        icon_path = os.path.join("data", "icon.ico")
        if os.path.exists(icon_path):
            self.dialog.iconbitmap(icon_path)
        elif hasattr(self.parent, 'iconbitmap') and callable(getattr(self.parent, 'iconbitmap', None)):
            try:
                self.dialog.iconbitmap(self.parent.iconbitmap())
            except:
                pass  # 如果继承失败，忽略错误
        
        # 居中显示
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # 创建界面元素
        self._create_widgets()
        
        # 在后台线程中检查更新
        self._check_thread = threading.Thread(target=self._check_updates)
        self._check_thread.daemon = True
        self._check_thread.start()
        
        # 等待对话框关闭
        self.parent.wait_window(self.dialog)
    
    def _create_widgets(self):
        """创建界面元素"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # 状态标签
        self.status_var = tk.StringVar(value="正在检查更新...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("", 12))
        status_label.pack(pady=10)
        
        # 版本信息框架
        version_frame = ttk.LabelFrame(main_frame, text="版本信息", padding=10)
        version_frame.pack(fill=X, pady=5)
        
        # 当前版本
        current_version_frame = ttk.Frame(version_frame)
        current_version_frame.pack(fill=X, pady=2)
        ttk.Label(current_version_frame, text="当前版本:").pack(side=LEFT)
        ttk.Label(current_version_frame, text=self.updater.current_version).pack(side=LEFT, padx=5)
        
        # 最新版本
        latest_version_frame = ttk.Frame(version_frame)
        latest_version_frame.pack(fill=X, pady=2)
        ttk.Label(latest_version_frame, text="最新版本:").pack(side=LEFT)
        self.latest_version_label = ttk.Label(latest_version_frame, text="检查中...")
        self.latest_version_label.pack(side=LEFT, padx=5)
        
        # 发布日期
        publish_date_frame = ttk.Frame(version_frame)
        publish_date_frame.pack(fill=X, pady=2)
        ttk.Label(publish_date_frame, text="发布日期:").pack(side=LEFT)
        self.publish_date_label = ttk.Label(publish_date_frame, text="检查中...")
        self.publish_date_label.pack(side=LEFT, padx=5)
        
        # 更新说明
        notes_frame = ttk.LabelFrame(main_frame, text="更新说明", padding=10)
        notes_frame.pack(fill=BOTH, expand=True, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(notes_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 文本框
        self.notes_text = tk.Text(notes_frame, wrap=tk.WORD, height=8, 
                                  yscrollcommand=scrollbar.set)
        self.notes_text.pack(fill=BOTH, expand=True)
        scrollbar.config(command=self.notes_text.yview)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=X, pady=10)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           mode='determinate', length=100)
        self.progress_bar.pack(fill=X)
        
        # 按钮区域 - 使用更合理的布局
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)
        
        # 使用网格布局，确保按钮均匀分布
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        
        # 下载按钮
        self.download_button = ttk.Button(button_frame, text="下载更新", width=12,
                                         command=self._download_update, state=DISABLED)
        self.download_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # 安装按钮
        self.install_button = ttk.Button(button_frame, text="安装更新", width=12,
                                        command=self._install_update, state=DISABLED)
        self.install_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 打开文件夹按钮
        self.open_folder_button = ttk.Button(button_frame, text="打开下载文件夹", width=15,
                                            command=self._open_download_folder, state=DISABLED)
        self.open_folder_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        
        # 取消按钮
        self.cancel_button = ttk.Button(button_frame, text="关闭", width=12,
                                       command=self.dialog.destroy)
        self.cancel_button.grid(row=0, column=3, padx=10, pady=5, sticky="ew")
    
    def _check_updates(self):
        """检查更新"""
        try:
            print("开始检查更新...")
            has_update, update_info = self.updater.check_for_updates()
            print(f"检查更新结果: has_update={has_update}, update_info={update_info}")
            
            # 确保在主线程中更新UI
            def update_ui():
                if not self.dialog:
                    return
                    
                if has_update:
                    print("发现新版本，启用下载按钮")
                    self.status_var.set("发现新版本！")
                    self.download_button.config(state=NORMAL)
                    
                    # 更新版本信息
                    self.latest_version_label.config(text=self.updater.latest_version)
                    self.publish_date_label.config(text=self.updater.publish_date or "未知")
                    
                    # 更新说明
                    if self.updater.release_notes:
                        self.notes_text.delete(1.0, tk.END)
                        self.notes_text.insert(tk.END, self.updater.release_notes)
                    else:
                        self.notes_text.delete(1.0, tk.END)
                        self.notes_text.insert(tk.END, "没有可用的更新说明")
                        
                    # 强制更新按钮状态
                    self.dialog.update_idletasks()
                    print(f"下载按钮状态: {self.download_button['state']}")
                else:
                    if "error" in update_info:
                        self.status_var.set(f"检查更新失败: {update_info.get('error', '未知错误')}")
                        self.notes_text.delete(1.0, tk.END)
                        self.notes_text.insert(tk.END, f"检查更新时发生错误:\n{update_info.get('error', '未知错误')}\n\n请稍后重试或联系开发者。")
                    else:
                        self.status_var.set("当前已是最新版本")
                    
                    self.latest_version_label.config(text=self.updater.latest_version or "未知")
                    self.publish_date_label.config(text=self.updater.publish_date or "未知")
            
            # 在主线程中执行UI更新
            self.dialog.after(0, update_ui)
            
        except Exception as e:
            print(f"检查更新异常: {e}")
            if self.dialog:
                def show_error():
                    self.status_var.set(f"检查更新出错: {e}")
                    self.notes_text.delete(1.0, tk.END)
                    self.notes_text.insert(tk.END, f"检查更新时发生错误:\n{str(e)}\n\n请检查网络连接或联系开发者。")
                self.dialog.after(0, show_error)
    
    def _download_update(self):
        """下载更新"""
        # 禁用下载按钮
        self.download_button.config(state=DISABLED)
        self.status_var.set("正在下载更新...")
        
        # 打印下载URL信息
        print(f"开始下载更新，URL: {self.updater.download_url}")
        
        if not self.updater.download_url:
            print("错误: 没有可用的下载链接")
            self.status_var.set("错误: 没有可用的下载链接")
            self.download_button.config(state=NORMAL)
            return
        
        # 开始下载
        self.updater.download_update(
            progress_callback=self._update_progress,
            error_callback=self._download_error,
            complete_callback=self._download_complete
        )
    
    def _update_progress(self, progress):
        """更新进度条"""
        if self.dialog:
            self.progress_var.set(progress)
            self.status_var.set(f"下载中... {progress}%")
    
    def _download_error(self, error_msg):
        """下载错误回调"""
        if self.dialog:
            self.status_var.set(f"下载失败: {error_msg}")
            self.download_button.config(state=NORMAL)
            self.notes_text.delete(1.0, tk.END)
            self.notes_text.insert(tk.END, f"下载更新时发生错误:\n{error_msg}\n\n请检查网络连接或联系开发者。")
    
    def _download_complete(self, file_path):
        """下载完成回调"""
        if self.dialog:
            self.download_path = file_path
            self.status_var.set("下载完成！")
            self.install_button.config(state=NORMAL)
            self.open_folder_button.config(state=NORMAL)
            
            # 更新说明文本
            self.notes_text.delete(1.0, tk.END)
            self.notes_text.insert(tk.END, f"更新已下载到:\n{file_path}\n\n点击\"安装更新\"按钮开始安装，或点击\"打开下载文件夹\"查看文件。")
    
    def _open_download_folder(self):
        """打开下载文件夹"""
        if not self.download_path:
            return
            
        try:
            # 获取文件所在目录
            file_dir = os.path.dirname(self.download_path)
            
            # 打开目录
            if os.path.exists(file_dir):
                if os.name == 'nt':  # Windows
                    os.startfile(file_dir)
                elif os.name == 'posix':  # macOS/Linux
                    import subprocess
                    subprocess.call(['open', file_dir])
        except Exception as e:
            print(f"打开下载目录失败: {e}")
    
    def _install_update(self):
        """安装更新"""
        if not self.download_path:
            return
        
        # 启动安装程序
        success = self.updater.install_update(self.download_path)
        
        if success:
            # 关闭对话框和应用程序
            self.dialog.destroy()
            self.parent.quit()
        else:
            self.status_var.set("启动安装程序失败，请手动安装")
            
            # 打开下载文件所在目录
            self._open_download_folder() 