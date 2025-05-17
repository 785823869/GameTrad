"""
GameTrad交易系统 - 主窗口
"""
import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                            QVBoxLayout, QStackedWidget, QMessageBox, QMenu, 
                            QMenuBar, QStatusBar, QDialog, QFileDialog, QSizePolicy,
                            QPushButton, QLabel)
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QIcon, QFont

from src_qt.utils.sidebar import ModernSidebar
from src_qt.utils.ui_manager import UIManager
from src_qt.utils.responsive_layout import LayoutMode, WindowSizeThreshold

class GameTradingSystemGUI(QMainWindow):
    """GameTrad交易系统主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GameTrad交易系统")
        self.resize(1280, 800)
        
        # 初始化UI管理器
        self.ui_manager = UIManager()
        
        # 创建数据库管理器 (稍后实现)
        # self.db_manager = DatabaseManager()
        
        # 响应式布局状态
        self.sidebar_expanded = True
        self.sidebar_toggle_animation = None
        
        # 设置界面
        self.setup_ui()
        
        # 创建菜单
        self.create_menu()
        
        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 自动刷新计时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(300000)  # 5分钟刷新一次
    
    def setup_ui(self):
        """设置界面布局"""
        # 主窗口部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建包含侧边栏和切换按钮的容器
        sidebar_container = QWidget()
        sidebar_container_layout = QHBoxLayout(sidebar_container)
        sidebar_container_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_container_layout.setSpacing(0)
        
        # 创建侧边栏
        self.sidebar = ModernSidebar(sidebar_container)
        sidebar_container_layout.addWidget(self.sidebar)
        
        # 创建侧边栏切换按钮
        self.sidebar_toggle_btn = QPushButton("◀")
        self.sidebar_toggle_btn.setFixedSize(20, 60)
        self.sidebar_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 0;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        self.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
        sidebar_container_layout.addWidget(self.sidebar_toggle_btn)
        
        main_layout.addWidget(sidebar_container)
        
        # 创建内容区堆叠部件
        self.content_stack = QStackedWidget()
        # 设置内容区域为可扩展的，以便自适应窗口大小变化
        self.content_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.content_stack)
        
        # 设置侧边栏内容区
        self.sidebar.set_content_widget(self.content_stack)
        
        # 添加标签页
        self.init_tabs()
        
        # 设置窗口的最小尺寸，防止窗口过小影响界面排版
        self.setMinimumSize(800, 600)
    
    def init_tabs(self):
        """初始化所有标签页"""
        # 仪表盘
        from src_qt.gui.tabs.dashboard_tab import DashboardTab
        tab_frame, self.dashboard_tab = self.sidebar.add_tab(
            "仪表盘", "📊", DashboardTab, {"main_gui": self}
        )
        self.content_stack.addWidget(tab_frame)
        
        # 库存管理
        from src_qt.gui.tabs.inventory_tab import InventoryTab
        tab_frame, self.inventory_tab = self.sidebar.add_tab(
            "库存管理", "📦", InventoryTab, {"main_gui": self}
        )
        self.content_stack.addWidget(tab_frame)
        
        # 入库管理
        from src_qt.gui.tabs.stock_in_tab import StockInTab
        tab_frame, self.stock_in_tab = self.sidebar.add_tab(
            "入库管理", "📥", StockInTab, {"main_gui": self}
        )
        self.content_stack.addWidget(tab_frame)
        
        # 出库管理
        from src_qt.gui.tabs.stock_out_tab import StockOutTab
        tab_frame, self.stock_out_tab = self.sidebar.add_tab(
            "出库管理", "📤", StockOutTab, {"main_gui": self}
        )
        self.content_stack.addWidget(tab_frame)
        
        # 交易监控
        from src_qt.gui.tabs.trade_monitor_tab import TradeMonitorTab
        tab_frame, self.trade_monitor_tab = self.sidebar.add_tab(
            "交易监控", "📈", TradeMonitorTab, {"main_gui": self}
        )
        self.content_stack.addWidget(tab_frame)
        
        # 女娲石行情
        from src_qt.gui.tabs.nvwa_price_tab import NvwaPriceTab
        tab_frame, self.nvwa_price_tab = self.sidebar.add_tab(
            "女娲石行情", "💎", NvwaPriceTab, {"main_gui": self}
        )
        self.content_stack.addWidget(tab_frame)
        
        # 银两行情
        from src_qt.gui.tabs.silver_price_tab import SilverPriceTab
        tab_frame, self.silver_price_tab = self.sidebar.add_tab(
            "银两行情", "💰", SilverPriceTab, {"main_gui": self}
        )
        self.content_stack.addWidget(tab_frame)
        
        # 操作日志
        from src_qt.gui.tabs.log_tab import LogTab
        tab_frame, self.log_tab = self.sidebar.add_tab(
            "操作日志", "📝", LogTab, {"main_gui": self}
        )
        self.content_stack.addWidget(tab_frame)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        data_migration_action = QAction("数据迁移", self)
        data_migration_action.triggered.connect(self.open_data_migration)
        file_menu.addAction(data_migration_action)
        
        import_data_action = QAction("导入数据", self)
        import_data_action.triggered.connect(self.open_import_data_dialog)
        file_menu.addAction(import_data_action)
        
        export_reports_action = QAction("导出报告", self)
        export_reports_action.triggered.connect(self.export_reports)
        file_menu.addAction(export_reports_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        server_config_action = QAction("Server酱配置", self)
        server_config_action.triggered.connect(self.open_server_chan_config)
        settings_menu.addAction(server_config_action)
        
        formula_manager_action = QAction("公式管理", self)
        formula_manager_action.triggered.connect(self.open_formula_manager)
        settings_menu.addAction(formula_manager_action)
        
        item_dict_action = QAction("物品字典管理", self)
        item_dict_action.triggered.connect(self.open_item_dict_manager)
        settings_menu.addAction(item_dict_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def refresh_all(self):
        """刷新所有数据"""
        # 稍后实现
        self.statusBar.showMessage("正在刷新数据...", 2000)
    
    def open_data_migration(self):
        """打开数据迁移窗口"""
        # 稍后实现
        QMessageBox.information(self, "提示", "数据迁移功能正在开发中，敬请期待。")
    
    def open_import_data_dialog(self):
        """打开导入数据对话框"""
        # 稍后实现
        QMessageBox.information(self, "提示", "导入数据功能正在开发中，敬请期待。")
    
    def export_reports(self):
        """导出报告"""
        # 稍后实现
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出报表", "", "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )
        if file_path:
            QMessageBox.information(self, "提示", f"报告已导出到 {file_path}")
    
    def open_server_chan_config(self):
        """打开Server酱配置窗口"""
        # 稍后实现
        QMessageBox.information(self, "提示", "Server酱配置功能正在开发中，敬请期待。")
    
    def open_formula_manager(self):
        """打开公式管理窗口"""
        # 稍后实现
        QMessageBox.information(self, "提示", "公式管理功能正在开发中，敬请期待。")
    
    def open_item_dict_manager(self):
        """物品词典管理窗口"""
        # 稍后实现
        QMessageBox.information(self, "提示", "物品词典管理功能正在开发中，敬请期待。")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
GameTrad 游戏交易系统 v2.0.0

简介：
GameTrad是一款专业的游戏物品交易管理系统，提供全面的库存管理、交易监控和数据分析功能，帮助游戏玩家和交易商高效管理游戏物品交易流程，实现利润最大化。

核心功能：
✦ 仪表盘 - 实时数据概览与图表分析
✦ 库存管理 - 智能库存追踪与价值评估
✦ 入库管理 - 多渠道物品入库与数据记录
✦ 出库管理 - 高效物品出库与利润计算
✦ 交易监控 - 实时市场价格与交易策略
✦ 行情分析 - 女娲石/银两价格趋势分析
✦ 操作日志 - 完整历史记录与回滚功能

技术特性：
• 基于Python与PyQt6构建的现代UI
• 多线程异步处理，确保操作流畅
• OCR图像识别，支持自动数据提取
• 智能数据分析与可视化图表
• 云端数据存储与多设备同步

作者：三只小猪

版权所有 © 2025 GameTrad团队
保留所有权利
        """
        QMessageBox.about(self, "关于", about_text)
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        reply = QMessageBox.question(
            self, '确认', "确定要退出程序吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 关闭数据库连接
            # if hasattr(self, 'db_manager'):
            #     self.db_manager.close()
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event):
        """窗口大小变化事件处理"""
        # 调用父类方法
        super().resizeEvent(event)
        
        current_width = event.size().width()
        current_height = event.size().height()
        
        # 更新UI管理器的布局模式
        layout_mode_changed = self.ui_manager.update_layout_mode(current_width)
        
        # 自动折叠侧边栏
        self.auto_collapse_sidebar(current_width)
        
        # 如果布局模式发生变化，通知所有标签页
        if layout_mode_changed:
            current_mode = self.ui_manager.get_current_layout_mode()
            self.update_all_tabs_layout(current_mode)
    
    def toggle_sidebar(self):
        """切换侧边栏显示/隐藏状态"""
        if self.sidebar_toggle_animation and self.sidebar_toggle_animation.state() == QPropertyAnimation.State.Running:
            return
        
        # 停止正在进行的动画
        if self.sidebar_toggle_animation:
            self.sidebar_toggle_animation.stop()
        
        # 创建动画
        self.sidebar_toggle_animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.sidebar_toggle_animation.setDuration(300)
        self.sidebar_toggle_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        if self.sidebar_expanded:
            # 收起侧边栏
            self.sidebar_toggle_animation.setStartValue(self.sidebar.width())
            self.sidebar_toggle_animation.setEndValue(0)
            self.sidebar_toggle_btn.setText("▶")
        else:
            # 展开侧边栏
            self.sidebar_toggle_animation.setStartValue(0)
            self.sidebar_toggle_animation.setEndValue(220)  # 侧边栏默认宽度
            self.sidebar_toggle_btn.setText("◀")
        
        self.sidebar_toggle_animation.start()
        self.sidebar_expanded = not self.sidebar_expanded
    
    def auto_collapse_sidebar(self, width):
        """根据窗口宽度自动折叠侧边栏"""
        if width < WindowSizeThreshold.COMPACT_WIDTH and self.sidebar_expanded:
            self.toggle_sidebar()
    
    def update_all_tabs_layout(self, layout_mode):
        """更新所有标签页的布局"""
        # 获取所有标签页
        tab_pages = [
            self.dashboard_tab,
            self.inventory_tab,
            self.stock_in_tab,
            self.stock_out_tab,
            self.trade_monitor_tab,
            self.nvwa_price_tab,
            self.silver_price_tab,
            self.log_tab
        ]
        
        # 通知每个标签页更新布局
        for tab in tab_pages:
            if tab and hasattr(tab, 'update_layout_for_mode'):
                tab.update_layout_for_mode(layout_mode)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建UI管理器并应用样式
    ui_manager = UIManager()
    ui_manager.apply_modern_style(app)
    
    # 创建主窗口
    main_window = GameTradingSystemGUI()
    main_window.show()
    
    sys.exit(app.exec()) 