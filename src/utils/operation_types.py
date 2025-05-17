"""
操作类型定义模块
提供标准化的操作类型常量、分类和显示文本
"""

class OperationType:
    """操作类型常量类，定义所有可能的操作类型"""
    
    # 添加操作
    ADD = "添加"
    BATCH_ADD = "批量添加"
    IMPORT = "导入"
    UPLOAD = "上传"
    OCR_IMPORT = "OCR导入"
    
    # 修改操作
    MODIFY = "修改"
    UPDATE = "更新"
    EDIT = "编辑"
    BATCH_EDIT = "批量修改"
    
    # 删除操作
    DELETE = "删除"
    BATCH_DELETE = "批量删除"
    CLEAR = "清空"
    
    # 查询操作
    QUERY = "查询"
    EXPORT = "导出"
    PRINT = "打印"
    SEARCH = "搜索"
    
    # 系统操作
    SYSTEM = "系统"
    CONFIG = "配置"
    BACKUP = "备份"
    RESTORE = "恢复"
    
    # 其他操作
    OTHER = "其他"

    @classmethod
    def get_all_types(cls):
        """获取所有操作类型"""
        return [value for key, value in cls.__dict__.items() 
                if not key.startswith('__') and not callable(getattr(cls, key))]
    
    @classmethod
    def get_add_types(cls):
        """获取所有添加类操作"""
        return [cls.ADD, cls.BATCH_ADD, cls.IMPORT, cls.UPLOAD, cls.OCR_IMPORT]
    
    @classmethod
    def get_modify_types(cls):
        """获取所有修改类操作"""
        return [cls.MODIFY, cls.UPDATE, cls.EDIT, cls.BATCH_EDIT]
    
    @classmethod
    def get_delete_types(cls):
        """获取所有删除类操作"""
        return [cls.DELETE, cls.BATCH_DELETE, cls.CLEAR]
    
    @classmethod
    def get_query_types(cls):
        """获取所有查询类操作"""
        return [cls.QUERY, cls.EXPORT, cls.PRINT, cls.SEARCH]
    
    @classmethod
    def get_system_types(cls):
        """获取所有系统类操作"""
        return [cls.SYSTEM, cls.CONFIG, cls.BACKUP, cls.RESTORE]
    
    @classmethod
    def get_category(cls, op_type):
        """获取操作类型所属的分类"""
        if op_type in cls.get_add_types():
            return "添加类"
        elif op_type in cls.get_modify_types():
            return "修改类"
        elif op_type in cls.get_delete_types():
            return "删除类"
        elif op_type in cls.get_query_types():
            return "查询类"
        elif op_type in cls.get_system_types():
            return "系统类"
        else:
            return "其他类"
    
    @classmethod
    def can_revert(cls, op_type):
        """判断操作类型是否可以回退"""
        # 查询类和系统类操作通常不需要回退
        if op_type in cls.get_query_types() or op_type in cls.get_system_types():
            return False
        return True
    
    @classmethod
    def get_display_text(cls, op_type):
        """获取操作类型的显示文本"""
        return op_type  # 当前直接返回操作类型字符串，根据需要可以定义更丰富的显示文本


class TabName:
    """标签页名称常量类，定义所有可能的标签页名称"""
    
    DASHBOARD = "仪表盘"
    INVENTORY = "库存管理"
    STOCK_IN = "入库管理"
    STOCK_OUT = "出库管理"
    TRADE_MONITOR = "交易监控"
    NVWA_PRICE = "女娲石行情"
    SILVER_PRICE = "银两行情"
    LOG = "操作日志"
    SYSTEM = "系统"
    
    @classmethod
    def get_all_tabs(cls):
        """获取所有标签页名称"""
        return [value for key, value in cls.__dict__.items() 
                if not key.startswith('__') and not callable(getattr(cls, key))] 