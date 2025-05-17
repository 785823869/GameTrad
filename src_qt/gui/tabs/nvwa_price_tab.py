"""
女娲石行情标签页 - 女娲石价格行情分析
"""
from src_qt.gui.tabs.price_tab import PriceTab

class NvwaPriceTab(PriceTab):
    """女娲石行情标签页"""
    
    def __init__(self, parent_frame, main_gui=None):
        # 调用父类构造函数，传入物品名称和图表标题
        super().__init__(parent_frame, main_gui, "女娲石", "女娲石价格走势")
        
        # 女娲石特有的属性和设置
        self._last_nvwa_data = None  # 保持与旧代码的兼容性
        
        # 刷新数据
        self.refresh_data()
    
    def refresh_data(self):
        """刷新女娲石价格数据"""
        # 获取时间范围
        days = self.get_days_from_range()
        
        # 生成测试数据
        data = self.generate_test_data(days)
        
        # 保存一份到女娲石特有的属性中，以保持与旧代码的兼容性
        self._last_nvwa_data = data
        
        # 更新图表和表格
        self.update_ui_with_data(data) 