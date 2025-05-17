import tkinter as tk
import ttkbootstrap as tb
import inspect

class ModernSidebar:
    def __init__(self, parent, ui_manager, width=220, callbacks=None):
        self.parent = parent
        self.ui = ui_manager
        self.active_tab = None
        self.tabs = []
        self.tab_frames = {}
        self.callbacks = callbacks or {}  # 存储回调函数
        
        # 创建侧边栏容器
        self.sidebar = tb.Frame(parent, bootstyle="dark", width=width)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)  # 固定宽度
        
        # 创建自定义按钮样式，提高文字与背景对比度
        style = tb.Style()
        style.configure('Sidebar.TButton', 
                        background='#2c3e50',  # 深色背景
                        foreground='#ffffff',  # 白色文字
                        font=(ui_manager.main_font, 11))
                        
        style.map('Sidebar.TButton',
                  foreground=[('active', '#ffffff')],  # 确保激活状态也是白色文字
                  background=[('active', '#1a252f')])  # 激活状态背景色更深
                  
        # 创建激活状态的样式
        style.configure('SidebarActive.TButton', 
                        background='#3498db',  # 蓝色背景
                        foreground='#ffffff',  # 白色文字
                        font=(ui_manager.main_font, 11, 'bold'))
                        
        style.map('SidebarActive.TButton',
                  foreground=[('active', '#ffffff')],
                  background=[('active', '#2980b9')])  # 较深的蓝色
        
        # 创建应用标题 - 增加内边距并调整字体大小
        title_frame = tb.Frame(self.sidebar, bootstyle="dark")
        title_frame.pack(fill='x', padx=5, pady=(25, 35))
        
        # 创建GameTrad标签 - 字体大一些
        tb.Label(title_frame, 
               text="GameTrad",
               font=(ui_manager.main_font, 20, "bold"),  # 保持原始大小
               foreground="white",
               bootstyle="inverse-dark",
               anchor="center").pack(fill='x', padx=5, pady=(5, 0))
        
        # 创建交易系统标签 - 字体小一些
        tb.Label(title_frame, 
               text="交易系统",
               font=(ui_manager.main_font, 14, "bold"),  # 较小的字体
               foreground="white",
               bootstyle="inverse-dark",
               anchor="center").pack(fill='x', padx=5, pady=(0, 5))
        
        # 内容区域
        self.content_frame = tb.Frame(parent)
        self.content_frame.pack(side='right', fill='both', expand=True)
    
    def add_tab(self, title, icon, tab_class, tab_params=None):
        """添加侧边栏选项"""
        tab_id = f"tab_{len(self.tabs)}"
        
        # 创建选项按钮 - 使用自定义样式提高对比度
        tab_button = tb.Button(
            self.sidebar,
            text=f" {icon} {title}",
            style="Sidebar.TButton",  # 使用自定义按钮样式
            command=lambda: self.switch_tab(tab_id),
            width=20
        )
        tab_button.pack(pady=5, padx=10, fill='x')
        
        # 创建内容区域的框架
        tab_frame = tb.Frame(self.content_frame)
        
        # 实例化选项卡内容，处理不同的参数类型
        tab_params = tab_params or {}
        
        # 检查选项卡类的__init__方法参数
        sig = inspect.signature(tab_class.__init__)
        params = list(sig.parameters.keys())
        
        # 检查第一个参数名（self之后的第一个参数）
        first_param = params[1] if len(params) > 1 else None
        
        if first_param == 'notebook':
            # 兼容旧的选项卡类，它们期望notebook而不是parent_frame
            tab_content = tab_class(tab_frame, **tab_params)
        elif first_param == 'parent_frame':
            # 新的选项卡类，接受parent_frame参数
            tab_content = tab_class(tab_frame, **tab_params)
        else:
            # 如果无法确定参数类型，尝试直接初始化
            try:
                tab_content = tab_class(tab_frame, **tab_params)
            except Exception as e:
                import tkinter.messagebox as messagebox
                messagebox.showerror("选项卡初始化错误", f"无法初始化选项卡 {title}: {str(e)}")
                tab_content = None
        
        # 保存选项卡信息
        self.tabs.append({
            'id': tab_id,
            'title': title,
            'button': tab_button,
            'frame': tab_frame,
            'content': tab_content
        })
        
        self.tab_frames[tab_id] = tab_frame
        
        # 初始化第一个选项卡为活动状态
        if len(self.tabs) == 1:
            self.switch_tab(tab_id)
    
    def switch_tab(self, tab_id):
        """切换选项卡"""
        # 隐藏当前活动选项卡
        if self.active_tab:
            self.tab_frames[self.active_tab].pack_forget()
            
            # 更改之前活动按钮的样式 - 重置为正常样式
            for tab in self.tabs:
                if tab['id'] == self.active_tab:
                    tab['button'].configure(style="Sidebar.TButton")  # 使用自定义非激活样式
        
        # 显示新选项卡
        self.tab_frames[tab_id].pack(fill='both', expand=True)
        
        # 更新活动选项卡
        self.active_tab = tab_id
        
        # 更改当前活动按钮的样式
        tab_title = None
        for tab in self.tabs:
            if tab['id'] == tab_id:
                tab['button'].configure(style="SidebarActive.TButton")  # 使用自定义激活样式
                tab_title = tab['title']
                break
                
        # 执行tab切换回调
        if 'on_tab_changed' in self.callbacks and callable(self.callbacks['on_tab_changed']):
            # 调用回调并传递标签页标题
            self.callbacks['on_tab_changed'](tab_title=tab_title)
    
    def get_active_tab_content(self):
        """获取当前活动选项卡的内容"""
        for tab in self.tabs:
            if tab['id'] == self.active_tab:
                return tab['content']
        return None 