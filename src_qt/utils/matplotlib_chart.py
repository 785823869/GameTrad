"""
Matplotlib图表工具 - 提供基于Matplotlib的图表封装
"""
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
import random

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt

# 配置matplotlib中文支持
try:
    import platform
    if platform.system() == 'Windows':
        matplotlib.rc('font', family='Microsoft YaHei')
    elif platform.system() == 'Darwin':  # macOS
        matplotlib.rc('font', family='PingFang SC')
    else:  # Linux等其他系统
        matplotlib.rc('font', family='WenQuanYi Micro Hei')
except:
    # 如果配置失败，使用通用设置
    matplotlib.rcParams['axes.unicode_minus'] = False


class MatplotlibChart(QWidget):
    """Matplotlib图表基类，提供基本的图表功能和样式"""
    
    def __init__(self, parent=None, title='图表', figsize=(5, 4), dpi=100, toolbar=True):
        """
        初始化图表组件
        
        参数:
        parent -- 父widget
        title -- 图表标题
        figsize -- 图表大小，元组(宽, 高)，单位为英寸
        dpi -- 图表分辨率
        toolbar -- 是否显示工具栏
        """
        super().__init__(parent)
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 创建matplotlib图表
        self.figure = Figure(figsize=figsize, dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 设置图表属性
        self.figure.patch.set_facecolor('#ffffff')  # 设置图表背景色
        
        # 添加工具栏（如果需要）
        if toolbar:
            self.toolbar = NavigationToolbar(self.canvas, self)
            self.layout.addWidget(self.toolbar)
        
        # 添加画布到布局
        self.layout.addWidget(self.canvas)
        
        # 设置标题和默认属性
        self.title = title
        
        # 创建默认坐标轴
        self.axes = self.figure.add_subplot(111)
        
        # 初始化图表
        self.init_chart()
    
    def init_chart(self):
        """初始化图表，设置默认样式"""
        self.axes.clear()
        self.axes.set_title(self.title)
        self.axes.grid(True, linestyle='--', alpha=0.7)
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_title(self, title):
        """更新图表标题"""
        self.title = title
        self.axes.set_title(title)
        self.canvas.draw()
    
    def clear(self):
        """清除图表内容"""
        self.axes.clear()
        self.init_chart()
    
    def save_chart(self, filename, dpi=300):
        """保存图表为图片文件"""
        self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')


class LineChart(MatplotlibChart):
    """折线图实现"""
    
    def __init__(self, parent=None, title='折线图', figsize=(5, 4), dpi=100, toolbar=True):
        super().__init__(parent, title, figsize, dpi, toolbar)
        
        # 折线图特有设置
        self.axes.set_xlabel('X轴')
        self.axes.set_ylabel('Y轴')
    
    def plot_data(self, data, marker='o', linestyle='-', color=None, label=None):
        """
        绘制单个折线数据
        
        参数:
        data -- 包含x,y序列的字典或元组 {'x': [...], 'y': [...]} 或 (x_list, y_list)
        marker -- 数据点标记样式
        linestyle -- 线条样式
        color -- 线条颜色
        label -- 图例标签
        """
        if isinstance(data, dict):
            x_data = data.get('x', [])
            y_data = data.get('y', [])
        elif isinstance(data, tuple) and len(data) == 2:
            x_data, y_data = data
        else:
            raise ValueError("数据格式错误，需要字典{'x':[...], 'y':[...]}或元组(x_list, y_list)")
        
        if len(x_data) != len(y_data):
            raise ValueError("X和Y数据长度不匹配")
        
        self.axes.plot(x_data, y_data, marker=marker, linestyle=linestyle, color=color, label=label)
        
        if label:
            self.axes.legend(loc='best')
        
        # 自动旋转日期标签以避免重叠
        if isinstance(x_data[0], (str, datetime)):
            plt.setp(self.axes.get_xticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_multiple(self, data_list):
        """
        绘制多条折线
        
        参数:
        data_list -- 数据列表，每项包含：
            {
                'data': {'x': [...], 'y': [...]},
                'marker': 'o',  # 可选
                'linestyle': '-',  # 可选
                'color': 'blue',  # 可选
                'label': '数据1'  # 可选
            }
        """
        self.axes.clear()
        self.axes.set_title(self.title)
        self.axes.grid(True, linestyle='--', alpha=0.7)
        
        colors = plt.cm.tab10.colors  # 使用matplotlib的颜色循环
        
        for i, item in enumerate(data_list):
            data = item.get('data', {})
            marker = item.get('marker', 'o')
            linestyle = item.get('linestyle', '-')
            color = item.get('color', colors[i % len(colors)])
            label = item.get('label', f'数据{i+1}')
            
            if isinstance(data, dict):
                x_data = data.get('x', [])
                y_data = data.get('y', [])
            elif isinstance(data, tuple) and len(data) == 2:
                x_data, y_data = data
            else:
                continue
            
            self.axes.plot(x_data, y_data, marker=marker, linestyle=linestyle, color=color, label=label)
        
        self.axes.legend(loc='best')
        
        # 自动旋转标签
        plt.setp(self.axes.get_xticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def set_axes_labels(self, xlabel=None, ylabel=None):
        """设置坐标轴标签"""
        if xlabel:
            self.axes.set_xlabel(xlabel)
        if ylabel:
            self.axes.set_ylabel(ylabel)
        self.canvas.draw()


class BarChart(MatplotlibChart):
    """柱状图实现"""
    
    def __init__(self, parent=None, title='柱状图', figsize=(5, 4), dpi=100, toolbar=True):
        super().__init__(parent, title, figsize, dpi, toolbar)
        
        # 柱状图特有设置
        self.axes.set_xlabel('类别')
        self.axes.set_ylabel('数值')
    
    def plot_data(self, categories, values, color=None, width=0.7, label=None):
        """
        绘制柱状图
        
        参数:
        categories -- 类别标签列表
        values -- 数值列表
        color -- 柱形颜色
        width -- 柱宽
        label -- 图例标签
        """
        if len(categories) != len(values):
            raise ValueError("类别和数值长度不匹配")
        
        x = range(len(categories))
        bars = self.axes.bar(x, values, width=width, color=color, label=label)
        
        # 为柱子添加数值标签
        for bar in bars:
            height = bar.get_height()
            self.axes.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{height:.1f}',
                ha='center', va='bottom', rotation=0
            )
        
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(categories)
        
        if label:
            self.axes.legend(loc='best')
        
        # 自动旋转类别标签以避免重叠
        if len(categories) > 5:
            plt.setp(self.axes.get_xticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_grouped_bars(self, categories, data_sets):
        """
        绘制分组柱状图
        
        参数:
        categories -- 类别标签列表
        data_sets -- 数据集列表，每项包含：
            {
                'values': [...],  # 数值列表
                'label': '数据1',  # 图例标签
                'color': 'blue'  # 颜色（可选）
            }
        """
        self.axes.clear()
        self.axes.set_title(self.title)
        self.axes.grid(True, linestyle='--', alpha=0.7)
        
        n_bars = len(data_sets)
        bar_width = 0.8 / n_bars
        colors = plt.cm.tab10.colors
        
        for i, data_set in enumerate(data_sets):
            values = data_set.get('values', [])
            label = data_set.get('label', f'数据{i+1}')
            color = data_set.get('color', colors[i % len(colors)])
            
            x = [j + i * bar_width for j in range(len(categories))]
            self.axes.bar(x, values, width=bar_width, color=color, label=label)
        
        # 设置X轴刻度和标签
        middle_positions = [j + (n_bars - 1) * bar_width / 2 for j in range(len(categories))]
        self.axes.set_xticks(middle_positions)
        self.axes.set_xticklabels(categories)
        
        self.axes.legend(loc='best')
        
        # 自动旋转类别标签以避免重叠
        if len(categories) > 5:
            plt.setp(self.axes.get_xticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def set_axes_labels(self, xlabel=None, ylabel=None):
        """设置坐标轴标签"""
        if xlabel:
            self.axes.set_xlabel(xlabel)
        if ylabel:
            self.axes.set_ylabel(ylabel)
        self.canvas.draw()


class PieChart(MatplotlibChart):
    """饼图实现"""
    
    def __init__(self, parent=None, title='饼图', figsize=(5, 4), dpi=100, toolbar=True):
        super().__init__(parent, title, figsize, dpi, toolbar)
    
    def plot_data(self, labels, values, colors=None, explode=None, autopct='%1.1f%%', shadow=False):
        """
        绘制饼图
        
        参数:
        labels -- 扇区标签列表
        values -- 数值列表
        colors -- 颜色列表（可选）
        explode -- 突出显示的扇区偏移量列表（可选）
        autopct -- 百分比格式（可选）
        shadow -- 是否显示阴影（可选）
        """
        self.axes.clear()
        self.axes.set_title(self.title)
        
        # 设置为等比例，确保饼图是圆形的
        self.axes.axis('equal')
        
        wedges, texts, autotexts = self.axes.pie(
            values, 
            labels=labels, 
            colors=colors,
            explode=explode,
            autopct=autopct,
            shadow=shadow,
            startangle=90
        )
        
        # 调整自动百分比文本
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
        
        self.figure.tight_layout()
        self.canvas.draw()


class ScatterChart(MatplotlibChart):
    """散点图实现"""
    
    def __init__(self, parent=None, title='散点图', figsize=(5, 4), dpi=100, toolbar=True):
        super().__init__(parent, title, figsize, dpi, toolbar)
        
        # 散点图特有设置
        self.axes.set_xlabel('X轴')
        self.axes.set_ylabel('Y轴')
    
    def plot_data(self, x_data, y_data, color=None, marker='o', s=50, alpha=0.7, label=None):
        """
        绘制散点图
        
        参数:
        x_data -- X坐标数据列表
        y_data -- Y坐标数据列表
        color -- 点颜色
        marker -- 点样式
        s -- 点大小
        alpha -- 透明度
        label -- 图例标签
        """
        if len(x_data) != len(y_data):
            raise ValueError("X和Y数据长度不匹配")
        
        self.axes.scatter(x_data, y_data, color=color, marker=marker, s=s, alpha=alpha, label=label)
        
        if label:
            self.axes.legend(loc='best')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_multiple_datasets(self, datasets):
        """
        绘制多个散点数据集
        
        参数:
        datasets -- 数据集列表，每项包含：
            {
                'x': [...],  # X坐标列表
                'y': [...],  # Y坐标列表
                'color': 'blue',  # 颜色（可选）
                'marker': 'o',  # 点样式（可选）
                's': 50,  # 点大小（可选）
                'alpha': 0.7,  # 透明度（可选）
                'label': '数据1'  # 图例标签（可选）
            }
        """
        self.axes.clear()
        self.axes.set_title(self.title)
        self.axes.grid(True, linestyle='--', alpha=0.7)
        
        colors = plt.cm.tab10.colors
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', '+']
        
        for i, dataset in enumerate(datasets):
            x_data = dataset.get('x', [])
            y_data = dataset.get('y', [])
            color = dataset.get('color', colors[i % len(colors)])
            marker = dataset.get('marker', markers[i % len(markers)])
            s = dataset.get('s', 50)
            alpha = dataset.get('alpha', 0.7)
            label = dataset.get('label', f'数据{i+1}')
            
            self.axes.scatter(x_data, y_data, color=color, marker=marker, s=s, alpha=alpha, label=label)
        
        self.axes.legend(loc='best')
        self.figure.tight_layout()
        self.canvas.draw()
    
    def set_axes_labels(self, xlabel=None, ylabel=None):
        """设置坐标轴标签"""
        if xlabel:
            self.axes.set_xlabel(xlabel)
        if ylabel:
            self.axes.set_ylabel(ylabel)
        self.canvas.draw() 