import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import ttkbootstrap as tb

class OCRPreview(ttk.Frame):
    """
    通用OCR图片预览组件，用于显示待OCR识别的图片
    支持图片显示、删除和放大预览功能
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.images = []  # 存储原始图片对象列表
        self.thumbnails = []  # 存储缩略图对象列表
        self.photo_refs = []  # 存储PhotoImage引用，防止被垃圾回收
        self.callback = None  # 删除图片后的回调函数
        
        # 获取父组件的背景色，用于透明效果
        try:
            parent_bg = parent.cget("background")
            if not parent_bg:
                parent_bg = "#f0f0f0"  # 默认背景色
        except:
            parent_bg = "#f0f0f0"  # 默认背景色
        
        # 创建滚动区域以支持多图片
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=parent_bg)
        self.scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # 配置滚动
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        
        # 布局
        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="bottom", fill="x")
        
        # 初始提示标签
        self.empty_label = ttk.Label(self.scrollable_frame, text="暂无图片，请添加或粘贴图片")
        self.empty_label.pack(pady=10)
        
        # 绑定鼠标滚轮事件
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        if self.winfo_containing(event.x_root, event.y_root) == self.canvas:
            self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def set_callback(self, callback):
        """设置删除图片后的回调函数"""
        self.callback = callback
        
    def add_image(self, image, callback=None):
        """添加图片到预览区"""
        if callback:
            self.callback = callback
            
        # 添加到图片列表
        self.images.append(image)
        
        # 清除无图片提示
        if self.empty_label.winfo_exists():
            self.empty_label.pack_forget()
            
        # 刷新显示
        self.refresh()
        
    def delete_image(self, idx):
        """删除指定索引的图片"""
        if 0 <= idx < len(self.images):
            self.images.pop(idx)
            self.refresh()
            
            # 显示无图片提示
            if not self.images and self.empty_label.winfo_exists():
                self.empty_label.pack(pady=10)
                
            # 执行回调
            if self.callback:
                self.callback(idx)
                
    def clear_images(self):
        """清除所有图片"""
        self.images.clear()
        self.refresh()
        
        # 显示无图片提示
        if self.empty_label.winfo_exists():
            self.empty_label.pack(pady=10)
            
    def refresh(self):
        """刷新图片显示"""
        # 清除所有现有预览
        for widget in self.scrollable_frame.winfo_children():
            if widget != self.empty_label:
                widget.destroy()
                
        # 清除引用
        self.thumbnails.clear()
        self.photo_refs.clear()
        
        # 重新创建图片预览
        for idx, img in enumerate(self.images):
            # 创建图片容器
            frame = ttk.Frame(self.scrollable_frame)
            frame.pack(side=tk.LEFT, padx=5, pady=5)
            
            # 创建缩略图
            thumb = img.copy()
            thumb.thumbnail((80, 80))
            self.thumbnails.append(thumb)
            
            # 创建Photo对象并保持引用
            photo = ImageTk.PhotoImage(thumb)
            self.photo_refs.append(photo)
            
            # 创建图片标签
            lbl = ttk.Label(frame, image=photo, cursor="hand2")
            lbl.pack(pady=(0, 2))
            
            # 绑定点击事件，点击放大预览
            lbl.bind("<Button-1>", lambda e, img=img, idx=idx: self._show_enlarged(img, idx))
            
            # 创建删除按钮
            btn = ttk.Button(frame, text="删除", width=5, 
                           command=lambda i=idx: self.delete_image(i))
            btn.pack()
            
    def _show_enlarged(self, img, idx):
        """显示放大的图片预览"""
        # 创建顶层窗口
        top = tb.Toplevel(self)
        top.title(f"图片预览 #{idx+1}")
        top.geometry("600x600")
        
        # 根据窗口大小调整图片
        display_img = img.copy()
        display_img.thumbnail((580, 580))
        
        # 创建Photo对象
        photo = ImageTk.PhotoImage(display_img)
        
        # 创建标签显示图片
        label = ttk.Label(top, image=photo)
        label.image = photo  # 保持引用
        label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # 添加关闭按钮
        ttk.Button(top, text="关闭", command=top.destroy).pack(pady=10)
        
    def get_images(self):
        """获取所有图片列表"""
        return self.images.copy() 