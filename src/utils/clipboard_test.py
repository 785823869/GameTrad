#!/usr/bin/env python
"""
剪贴板功能测试脚本
用于测试各种剪贴板图片获取方法
"""

import sys
import os
import logging
from tkinter import Tk, Label, Button, Frame, Text, Scrollbar, END
import tkinter as tk
from PIL import Image, ImageTk

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入剪贴板助手模块
from src.utils import clipboard_helper

# 配置日志
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('clipboard_test')

class ClipboardTester(Tk):
    def __init__(self):
        super().__init__()
        self.title("剪贴板功能测试")
        self.geometry("800x600")
        self.create_widgets()
        
        # 添加系统信息
        self.log_text.insert(END, "系统信息:\n")
        for key, value in clipboard_helper.SYSTEM_INFO.items():
            self.log_text.insert(END, f"  {key}: {value}\n")
            
        self.log_text.insert(END, "\n模块状态:\n")
        self.log_text.insert(END, f"  PIL Image可用: {clipboard_helper.PIL_IMAGE_AVAILABLE}\n")
        self.log_text.insert(END, f"  PIL ImageGrab可用: {clipboard_helper.IMAGEGRAB_AVAILABLE}\n")
        self.log_text.insert(END, f"  win32clipboard可用: {clipboard_helper.WIN32_AVAILABLE}\n")
        self.log_text.insert(END, f"  ctypes可用: {clipboard_helper.CTYPES_AVAILABLE}\n")
        self.log_text.insert(END, f"  pyperclip可用: {clipboard_helper.PYPERCLIP_AVAILABLE}\n")
        self.log_text.insert(END, "\n准备就绪，请点击相应按钮测试剪贴板功能\n")
        
    def create_widgets(self):
        # 创建主框架
        main_frame = Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 按钮区域
        buttons_frame = Frame(main_frame)
        buttons_frame.pack(fill="x", pady=5)
        
        # 测试按钮
        Button(buttons_frame, text="综合测试", command=self.test_all).pack(side="left", padx=5)
        Button(buttons_frame, text="PIL测试", command=self.test_pil).pack(side="left", padx=5)
        Button(buttons_frame, text="Win32测试", command=self.test_win32).pack(side="left", padx=5)
        Button(buttons_frame, text="ctypes测试", command=self.test_ctypes).pack(side="left", padx=5)
        Button(buttons_frame, text="临时文件测试", command=self.test_temp_file).pack(side="left", padx=5)
        Button(buttons_frame, text="诊断", command=self.diagnose).pack(side="left", padx=5)
        Button(buttons_frame, text="清空日志", command=self.clear_log).pack(side="left", padx=5)
        
        # 日志区域
        log_frame = Frame(main_frame)
        log_frame.pack(fill="both", expand=True, pady=5)
        
        # 日志文本框和滚动条
        self.log_text = Text(log_frame, wrap="word", height=10)
        self.log_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 图像预览区域
        preview_frame = Frame(main_frame)
        preview_frame.pack(fill="both", expand=True, pady=5)
        
        self.preview_label = Label(preview_frame, text="图像预览区域")
        self.preview_label.pack(fill="both", expand=True)
        
    def log(self, message):
        """添加日志消息"""
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, END)
        self.preview_label.config(image=None, text="图像预览区域")
        
    def display_image(self, img):
        """显示图像"""
        if img:
            # 调整图像大小以适应显示区域
            max_size = (400, 300)
            img.thumbnail(max_size, Image.LANCZOS)
            
            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # 更新标签
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # 保持引用
            
            self.log(f"显示图像，尺寸: {img.size}")
        else:
            self.preview_label.config(image=None, text="未能获取图像")
            
    def test_all(self):
        """测试所有方法"""
        self.log("===== 开始综合测试 =====")
        try:
            img = clipboard_helper.get_clipboard_image()
            if img:
                self.log("成功获取剪贴板图像")
                self.display_image(img)
            else:
                self.log("未能获取剪贴板图像")
        except Exception as e:
            self.log(f"测试出错: {e}")
        self.log("===== 综合测试结束 =====\n")
            
    def test_pil(self):
        """测试PIL方法"""
        self.log("===== 开始PIL测试 =====")
        try:
            img = clipboard_helper.get_clipboard_image_pil()
            if img:
                self.log("PIL方法成功获取剪贴板图像")
                self.display_image(img)
            else:
                self.log("PIL方法未能获取剪贴板图像")
        except Exception as e:
            self.log(f"PIL测试出错: {e}")
        self.log("===== PIL测试结束 =====\n")
            
    def test_win32(self):
        """测试Win32方法"""
        self.log("===== 开始Win32测试 =====")
        try:
            img = clipboard_helper.get_clipboard_image_win32()
            if img:
                self.log("Win32方法成功获取剪贴板图像")
                self.display_image(img)
            else:
                self.log("Win32方法未能获取剪贴板图像")
        except Exception as e:
            self.log(f"Win32测试出错: {e}")
        self.log("===== Win32测试结束 =====\n")
            
    def test_ctypes(self):
        """测试ctypes方法"""
        self.log("===== 开始ctypes测试 =====")
        try:
            img = clipboard_helper.get_clipboard_image_ctypes()
            if img:
                self.log("ctypes方法成功获取剪贴板图像")
                self.display_image(img)
            else:
                self.log("ctypes方法未能获取剪贴板图像")
        except Exception as e:
            self.log(f"ctypes测试出错: {e}")
        self.log("===== ctypes测试结束 =====\n")
            
    def test_temp_file(self):
        """测试临时文件方法"""
        self.log("===== 开始临时文件测试 =====")
        try:
            img = clipboard_helper.get_clipboard_image_temp_file()
            if img:
                self.log("临时文件方法成功获取剪贴板图像")
                self.display_image(img)
            else:
                self.log("临时文件方法未能获取剪贴板图像")
        except Exception as e:
            self.log(f"临时文件测试出错: {e}")
        self.log("===== 临时文件测试结束 =====\n")
            
    def diagnose(self):
        """运行诊断"""
        self.log("===== 开始剪贴板诊断 =====")
        try:
            report = clipboard_helper.diagnose_clipboard()
            
            self.log("系统信息:")
            for k, v in report["system_info"].items():
                self.log(f"  {k}: {v}")
                
            self.log("\n模块状态:")
            for k, v in report["modules"].items():
                self.log(f"  {k}: {v}")
                
            self.log("\n剪贴板状态:")
            for k, v in report["clipboard_state"].items():
                self.log(f"  {k}: {v}")
                
            if report["possible_issues"]:
                self.log("\n可能的问题:")
                for issue in report["possible_issues"]:
                    self.log(f"  • {issue}")
                    
            if report["recommendations"]:
                self.log("\n建议:")
                for i, rec in enumerate(report["recommendations"], 1):
                    self.log(f"  {i}. {rec}")
                    
        except Exception as e:
            self.log(f"诊断出错: {e}")
            
        self.log("===== 诊断结束 =====\n")

def main():
    app = ClipboardTester()
    app.mainloop()

if __name__ == "__main__":
    main() 