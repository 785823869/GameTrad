"""
图表工具类 - 提供增强的图表功能和样式
"""
from PyQt6.QtCharts import (QChart, QChartView, QLineSeries, QBarSeries, QBarSet, 
                           QBarCategoryAxis, QValueAxis, QSplineSeries, QScatterSeries)
from PyQt6.QtCore import Qt, QPointF, QRectF, QMargins, QPoint, QSize, QSizeF
from PyQt6.QtGui import QColor, QPainter, QPen, QLinearGradient, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import QGraphicsItem, QToolTip, QWidget, QVBoxLayout, QSlider, QLabel, QHBoxLayout, QSizePolicy

# 尝试导入QLegend，如果不可用则提供备用方案
try:
    from PyQt6.QtCharts import QLegend
    HAS_QLEGEND = True
except ImportError:
    HAS_QLEGEND = False

class EnhancedChartView(QChartView):
    """增强型图表视图，支持缩放、平移和悬停提示"""
    
    def __init__(self, chart=None, parent=None):
        # 确保先设置父部件，再进行其他初始化
        super().__init__(parent)
        
        # 如果提供了图表，设置图表
        if chart:
            self.setChart(chart)
            # 确保图表与视图具有相同的父部件
            if parent and chart.parent() != parent:
                chart.setParent(parent)
        
        # 强制嵌入模式，防止在独立窗口显示
        self.setWindowFlags(Qt.WindowType.Widget)
        
        # 额外的设置以防止独立窗口显示
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, False)
        
        # 禁用独立窗口功能
        if chart:
            chart.setWindowFlags(Qt.WindowType.Widget)
            chart.setParent(self)
        
        # 启用抗锯齿
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 允许缩放和平移交互
        self.setRubberBand(QChartView.RubberBand.RectangleRubberBand)
        self.setMouseTracking(True)  # 启用鼠标跟踪
        
        # 设置尺寸策略，使图表能够在所有方向上扩展
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 缩放状态
        self.is_zoomed = False
        
        # 上次鼠标位置
        self.last_mouse_pos = QPoint()
        
        # 数据系列中点的值映射
        self.point_values = {}
        
        # 禁用上下文菜单，防止右键点击显示菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        
        # 强制更新以确保图表正确显示
        self.update()
    
    def showEvent(self, event):
        """重写显示事件，确保图表正确显示"""
        super().showEvent(event)
        
        # 确保图表适应视图大小，需要将QSize转换为QSizeF
        if self.chart():
            size = self.size()
            size_f = QSizeF(size.width(), size.height())
            self.chart().resize(size_f)
            
            # 确保图表不会在单独窗口显示
            self.chart().setWindowFlags(Qt.WindowType.Widget)
            if self.chart().parent() != self:
                self.chart().setParent(self)
    
    def resizeEvent(self, event):
        """处理窗口大小调整事件，确保图表正确调整大小"""
        super().resizeEvent(event)
        
        # 如果未缩放，则自动调整图表以适应新的大小
        if not self.is_zoomed and self.chart():
            try:
                # 将QSize转换为QSizeF
                size = self.size()
                size_f = QSizeF(size.width(), size.height())
                self.chart().resize(size_f)
                # 调用update以确保图表元素正确定位
                self.chart().update()
            except (TypeError, AttributeError) as e:
                # 如果方法不可用，记录错误并跳过
                print(f"图表调整大小错误: {e}")
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = event.pos()
            event.accept()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，显示数据点提示和平移图表"""
        # 平移处理
        if event.buttons() & Qt.MouseButton.LeftButton and self.is_zoomed:
            # 计算移动距离
            delta = QPoint(event.pos() - self.last_mouse_pos)
            self.last_mouse_pos = event.pos()
            
            # 转换为图表坐标系并平移
            self.chart().scroll(-delta.x(), delta.y())
            event.accept()
        else:
            # 数据点悬停提示
            found = False
            
            # 检查是否接近数据点
            for series_name, points in self.point_values.items():
                for i, (x, y, label) in enumerate(points):
                    # 转换为视图坐标系
                    point_pos = self.chart().mapToPosition(QPointF(x, y))
                    
                    # 检查鼠标是否在点附近
                    distance = ((point_pos.x() - event.pos().x()) ** 2 + 
                               (point_pos.y() - event.pos().y()) ** 2) ** 0.5
                    
                    if distance < 15:  # 15像素的检测半径
                        QToolTip.showText(event.globalPosition().toPoint(), label, self)
                        found = True
                        break
                
                if found:
                    break
            
            # 如果鼠标不在数据点附近，隐藏提示
            if not found:
                QToolTip.hideText()
        
        super().mouseMoveEvent(event)
    
    def wheelEvent(self, event):
        """处理滚轮事件，用于缩放图表"""
        # 向上滚动放大，向下滚动缩小
        factor = 1.15
        if event.angleDelta().y() < 0:
            factor = 1.0 / factor
        
        # 以鼠标位置为中心缩放
        self.chart().zoom(factor)
        
        # 更新缩放状态
        self.is_zoomed = self.chart().isZoomed()
        
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """双击重置缩放"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.chart().zoomReset()
            self.is_zoomed = False
            event.accept()
        super().mouseDoubleClickEvent(event)
    
    def set_point_values(self, series_name, points_data):
        """设置数据点值映射，用于提示显示
        points_data: 列表 [(x, y, label), ...]
        """
        self.point_values[series_name] = points_data


class ChartUtils:
    """图表工具类，提供常用的图表增强功能"""
    
    @staticmethod
    def apply_chart_style(chart, title="", show_legend=False, legend_alignment=Qt.AlignmentFlag.AlignBottom):
        """应用标准图表样式"""
        chart.setTitle(title)
        chart.setTitleFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # 设置图例
        chart.legend().setVisible(show_legend)
        chart.legend().setAlignment(legend_alignment)
        chart.legend().setFont(QFont("Microsoft YaHei", 9))
        
        # 只有在QLegend可用且图例可见的情况下设置圆形标记
        if HAS_QLEGEND and show_legend:
            try:
                chart.legend().setMarkerShape(QLegend.MarkerShape.MarkerShapeCircle)
            except (AttributeError, TypeError):
                # 如果方法不可用，使用默认设置
                pass
        
        # 移除背景和边框
        chart.setBackgroundVisible(False)
        chart.setBackgroundBrush(QBrush(QColor("#ffffff")))
        
        # 尝试设置绘图区域背景，如果方法可用
        try:
            chart.setPlotAreaBackgroundVisible(False)
        except AttributeError:
            # 如果方法不可用，跳过此设置
            pass
        
        # 设置边距
        chart.setMargins(QMargins(5, 5, 5, 5))  # 减小边距以提供更多绘图空间
        
        # 尝试设置布局边距，如果方法可用
        try:
            chart.layout().setContentsMargins(0, 0, 0, 0)
        except (AttributeError, TypeError):
            # 如果方法不可用，跳过此设置
            pass
        
        return chart
    
    @staticmethod
    def remove_all_axes(chart):
        """移除图表中的所有坐标轴，解决坐标轴重叠问题
        
        Args:
            chart (QChart): 要处理的图表
        """
        # 获取所有坐标轴
        axes = chart.axes()
        # 逐个移除坐标轴
        for axis in axes:
            chart.removeAxis(axis)
    
    @staticmethod
    def create_gradient(color, alpha_start=0.7, alpha_end=0.1):
        """创建垂直渐变效果"""
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        
        # 顶部颜色（半透明）
        color_start = QColor(color)
        color_start.setAlphaF(alpha_start)
        gradient.setColorAt(0, color_start)
        
        # 底部颜色（更透明）
        color_end = QColor(color)
        color_end.setAlphaF(alpha_end)
        gradient.setColorAt(1, color_end)
        
        return gradient
    
    @staticmethod
    def enhance_line_series(series, color, width=2, use_gradient=True):
        """增强折线系列的视觉效果"""
        # 设置线条样式
        pen = QPen(QColor(color))
        pen.setWidth(width)
        series.setPen(pen)
        
        # 如果启用渐变填充
        if use_gradient and isinstance(series, QLineSeries):
            gradient = ChartUtils.create_gradient(color)
            series.setBrush(QBrush(gradient))
        
        return series
    
    @staticmethod
    def enhance_bar_series(bar_set, color, use_gradient=True):
        """增强柱形图的视觉效果"""
        bar_set.setColor(QColor(color))
        
        if use_gradient:
            gradient = ChartUtils.create_gradient(color, 0.8, 0.3)
            bar_set.setBrush(QBrush(gradient))
        
        return bar_set
    
    @staticmethod
    def setup_axes(chart, categories=None, min_y=0, max_y=100, y_format="%d"):
        """设置图表坐标轴"""
        # 创建Y轴
        axis_y = QValueAxis()
        axis_y.setRange(min_y, max_y)
        axis_y.setLabelFormat(y_format)
        axis_y.setGridLineVisible(True)
        axis_y.setGridLineColor(QColor("#ecf0f1"))  # 更浅的网格线
        axis_y.setMinorGridLineVisible(False)
        axis_y.setTitleText("")
        axis_y.setLabelsColor(QColor("#7f8c8d"))  # 灰色标签
        axis_y.setLabelsFont(QFont("Microsoft YaHei", 8))
        
        # 添加Y轴
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        
        # 如果提供了类别，创建X轴
        if categories:
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            axis_x.setGridLineVisible(False)
            
            # 根据类别数量动态调整标签角度和字体大小
            if len(categories) > 12:
                axis_x.setLabelsAngle(-60)
                axis_x.setLabelsFont(QFont("Microsoft YaHei", 7))
            elif len(categories) > 8:
                axis_x.setLabelsAngle(-45)
                axis_x.setLabelsFont(QFont("Microsoft YaHei", 8))
            else:
                axis_x.setLabelsAngle(0)
                axis_x.setLabelsFont(QFont("Microsoft YaHei", 8))
            
            axis_x.setLabelsColor(QColor("#7f8c8d"))  # 灰色标签
            
            # 添加X轴
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            
            return axis_x, axis_y
        
        return None, axis_y
    
    @staticmethod
    def create_mini_sparkline(data, width=50, height=20, color="#3498db"):
        """创建迷你趋势图(sparkline)"""
        widget = QWidget()
        widget.setFixedSize(width, height)
        
        # 重写绘制方法
        class SparklineWidget(QWidget):
            def __init__(self, data, color):
                super().__init__()
                self.data = data
                self.color = QColor(color)
                self.setFixedSize(width, height)
            
            def paintEvent(self, event):
                if not self.data:
                    return
                
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                # 准备路径
                path = QPainterPath()
                
                # 计算比例
                x_scale = width / (len(self.data) - 1) if len(self.data) > 1 else 0
                min_val = min(self.data)
                max_val = max(self.data) if max(self.data) > min_val else min_val + 1
                y_scale = height / (max_val - min_val) if max_val != min_val else 1
                
                # 创建路径
                path.moveTo(0, height - (self.data[0] - min_val) * y_scale)
                for i in range(1, len(self.data)):
                    x = i * x_scale
                    y = height - (self.data[i] - min_val) * y_scale
                    path.lineTo(x, y)
                
                # 绘制路径
                pen = QPen(self.color)
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawPath(path)
                
                # 强调最后一个点
                last_x = (len(self.data) - 1) * x_scale
                last_y = height - (self.data[-1] - min_val) * y_scale
                painter.setBrush(self.color)
                painter.drawEllipse(QPointF(last_x, last_y), 2, 2)
        
        return SparklineWidget(data, color)
    
    @staticmethod
    def create_time_range_selector(parent, min_days=7, max_days=90, current_days=30, callback=None):
        """创建时间范围选择器"""
        widget = QWidget(parent)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标签和滑块布局
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 最小值标签
        min_label = QLabel(f"{min_days}天")
        min_label.setMinimumWidth(30)
        control_layout.addWidget(min_label)
        
        # 滑块
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_days)
        slider.setMaximum(max_days)
        slider.setValue(current_days)
        slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        control_layout.addWidget(slider)
        
        # 最大值标签
        max_label = QLabel(f"{max_days}天")
        max_label.setMinimumWidth(30)
        control_layout.addWidget(max_label)
        
        # 显示当前值
        value_label = QLabel(f"显示: {current_days}天")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加到主布局
        layout.addLayout(control_layout)
        layout.addWidget(value_label)
        
        # 连接信号
        def on_value_changed(value):
            value_label.setText(f"显示: {value}天")
            if callback:
                callback(value)
        
        slider.valueChanged.connect(on_value_changed)
        
        return widget, slider 