import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox
import json
import os

PAGE_FIELDS = {
    "库存管理": ["物品", "库存数", "总入库均价", "保本均价", "总出库均价", "利润", "利润率", "成交利润额", "库存价值"],
    "入库管理": ["物品", "当前时间", "入库数量", "入库花费", "入库均价", "备注"],
    "出库管理": ["物品", "当前时间", "出库数量", "单价", "手续费", "出库总数量", "出货均价", "出库总金额", "备注"],
    "交易监控": ["物品", "当前时间", "数量", "一口价", "目标买入价", "计划卖出价", "保本卖出价", "利润", "利润率", "入库策略"],
    "备注规则": ["备注值", "用户名"]  # 新增备注规则页面
}

OPS = ['+', '-', '*', '/', '(', ')']

class FormulaManagerWindow(tb.Toplevel):
    def __init__(self, master, main_gui):
        super().__init__(master)
        self.title("公式管理")
        self.geometry("900x650")
        self.main_gui = main_gui
        self.formula_dict = {}
        self.note_rules_dict = {}  # 新增备注规则字典
        self.page_var = tb.StringVar(value="库存管理")
        self.entries = {}
        self._load_formulas()
        self._load_note_rules()  # 加载备注规则
        self._build_ui()

    def _load_formulas(self):
        if os.path.exists("field_formulas.json"):
            try:
                with open("field_formulas.json", "r", encoding="utf-8") as f:
                    self.formula_dict = json.load(f)
            except Exception:
                self.formula_dict = {}
        else:
            self.formula_dict = {}

    def _load_note_rules(self):
        """加载备注规则配置"""
        try:
            note_rules_path = os.path.join("data", "config", "note_rules.json")
            if os.path.exists(note_rules_path):
                with open(note_rules_path, "r", encoding="utf-8") as f:
                    self.note_rules_dict = json.load(f)
            else:
                # 默认规则示例
                self.note_rules_dict = {"41": "柒柒柒嗷"}
                # 确保目录存在
                os.makedirs(os.path.join("data", "config"), exist_ok=True)
                # 保存默认规则
                self._save_note_rules()
        except Exception as e:
            print(f"加载备注规则失败: {e}")
            self.note_rules_dict = {"41": "柒柒柒嗷"}  # 默认规则

    def _save_note_rules(self):
        """保存备注规则配置"""
        try:
            note_rules_path = os.path.join("data", "config", "note_rules.json")
            with open(note_rules_path, "w", encoding="utf-8") as f:
                json.dump(self.note_rules_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存备注规则失败: {e}")

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill='x')
        ttk.Label(top_frame, text="选择标签页:").pack(side='left')
        page_cb = ttk.Combobox(top_frame, textvariable=self.page_var, values=list(PAGE_FIELDS.keys()), state='readonly', width=12)
        page_cb.pack(side='left', padx=8)
        page_cb.bind("<<ComboboxSelected>>", lambda e: self._build_fields())
        ttk.Button(top_frame, text="刷新", command=self._build_fields).pack(side='left', padx=8)
        self.fields_frame = ttk.Frame(self, padding=10)
        self.fields_frame.pack(fill='both', expand=True)
        self._build_fields()
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack()
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="关闭", command=self.destroy).pack(side='left', padx=10)

    def _build_fields(self):
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        page = self.page_var.get()
        fields = PAGE_FIELDS[page]
        self.entries = {}
        zebra_colors = ['#f8fafd', '#e6f0fa']
        
        if page == "备注规则":
            self._build_note_rules_fields(zebra_colors)
        else:
            self._build_formula_fields(fields, zebra_colors)

    def _build_formula_fields(self, fields, zebra_colors):
        """构建公式字段UI"""
        for idx, field in enumerate(fields):
            bg = zebra_colors[idx % 2]
            row_frame = ttk.Frame(self.fields_frame, style='Custom.TFrame')
            row_frame.pack(fill='x', pady=0, padx=0)
            row_frame.configure(style='Custom.TFrame')
            # 设置背景色
            row_frame.tk_setPalette(background=bg)
            # 字段名加粗
            ttk.Label(row_frame, text=field+" 公式:", width=12, font=('微软雅黑', 11, 'bold'), background=bg).pack(side='left', padx=6, pady=8)
            entry = ttk.Entry(row_frame, width=50)
            entry.pack(side='left', padx=4, pady=8)
            entry.insert(0, self._get_formula(self.page_var.get(), field))
            self.entries[field] = entry
            # 字段变量下拉框+添加按钮
            var_var = tb.StringVar(value=fields[0])
            var_cb = ttk.Combobox(row_frame, textvariable=var_var, values=fields, state='readonly', width=12)
            var_cb.pack(side='left', padx=2)
            ttk.Button(row_frame, text="添加字段", width=8, command=lambda v=var_var, e=entry: self._insert_to_entry(e, v.get())).pack(side='left', padx=2)
            # 运算符下拉框+添加按钮
            op_var = tb.StringVar(value=OPS[0])
            op_cb = ttk.Combobox(row_frame, textvariable=op_var, values=OPS, state='readonly', width=4)
            op_cb.pack(side='left', padx=2)
            ttk.Button(row_frame, text="添加符号", width=8, command=lambda o=op_var, e=entry: self._insert_to_entry(e, o.get())).pack(side='left', padx=2)
            # 分割线
            sep = ttk.Separator(self.fields_frame, orient='horizontal')
            sep.pack(fill='x', pady=0)

    def _build_note_rules_fields(self, zebra_colors):
        """构建备注规则配置UI"""
        # 1. 添加说明
        instruction_frame = ttk.Frame(self.fields_frame)
        instruction_frame.pack(fill='x', pady=10)
        ttk.Label(instruction_frame, text="备注规则配置", font=('微软雅黑', 12, 'bold')).pack(anchor='w')
        ttk.Label(instruction_frame, text="配置入库/出库管理中备注字段数值与用户名的映射关系。例如：备注为41时，对应用户名为'柒柒柒嗷'").pack(anchor='w', pady=5)
        
        # 2. 添加现有规则
        rules_frame = ttk.Frame(self.fields_frame)
        rules_frame.pack(fill='both', expand=True, pady=10)
        
        # 创建现有规则表格
        columns = ("备注值", "用户名")
        self.rules_tree = ttk.Treeview(rules_frame, columns=columns, show='headings', height=10)
        for col in columns:
            self.rules_tree.heading(col, text=col, anchor='center')  # 设置列标题居中
            self.rules_tree.column(col, width=100, anchor='center')  # 设置列内容居中
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(rules_frame, orient="vertical", command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.rules_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 填充现有规则数据
        for note_value, username in self.note_rules_dict.items():
            self.rules_tree.insert('', 'end', values=(note_value, username))
        
        # 3. 添加规则编辑区
        edit_frame = ttk.Frame(self.fields_frame)
        edit_frame.pack(fill='x', pady=10)
        
        # 备注值输入框
        note_frame = ttk.Frame(edit_frame)
        note_frame.pack(side='left', padx=10)
        ttk.Label(note_frame, text="备注值:").pack(side='left')
        self.note_entry = ttk.Entry(note_frame, width=10)
        self.note_entry.pack(side='left', padx=5)
        
        # 用户名输入框
        user_frame = ttk.Frame(edit_frame)
        user_frame.pack(side='left', padx=10)
        ttk.Label(user_frame, text="用户名:").pack(side='left')
        self.username_entry = ttk.Entry(user_frame, width=20)
        self.username_entry.pack(side='left', padx=5)
        
        # 按钮区
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.pack(side='left', padx=10)
        ttk.Button(btn_frame, text="添加规则", command=self._add_note_rule).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="删除选中", command=self._delete_note_rule).pack(side='left', padx=5)
        
        # 绑定双击事件编辑
        self.rules_tree.bind('<Double-1>', self._edit_note_rule)

    def _add_note_rule(self):
        """添加或更新备注规则"""
        note_value = self.note_entry.get().strip()
        username = self.username_entry.get().strip()
        
        if not note_value or not username:
            messagebox.showwarning("输入错误", "备注值和用户名都不能为空")
            return
            
        # 更新字典
        self.note_rules_dict[note_value] = username
        
        # 更新表格
        # 先检查是否已存在该备注值
        for item in self.rules_tree.get_children():
            if self.rules_tree.item(item)['values'][0] == note_value:
                self.rules_tree.item(item, values=(note_value, username))
                break
        else:
            # 如果不存在则添加新行
            self.rules_tree.insert('', 'end', values=(note_value, username))
        
        # 清空输入框
        self.note_entry.delete(0, 'end')
        self.username_entry.delete(0, 'end')

    def _delete_note_rule(self):
        """删除选中的备注规则"""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的规则")
            return
            
        for item in selected:
            note_value = self.rules_tree.item(item)['values'][0]
            # 从字典中删除
            if note_value in self.note_rules_dict:
                del self.note_rules_dict[note_value]
            # 从表格中删除
            self.rules_tree.delete(item)

    def _edit_note_rule(self, event):
        """双击编辑备注规则"""
        item = self.rules_tree.identify_row(event.y)
        if not item:
            return
            
        # 获取当前值
        values = self.rules_tree.item(item)['values']
        if not values or len(values) < 2:
            return
            
        # 填充到输入框
        self.note_entry.delete(0, 'end')
        self.username_entry.delete(0, 'end')
        self.note_entry.insert(0, values[0])
        self.username_entry.insert(0, values[1])

    def _insert_to_entry(self, entry, text):
        entry.focus_set()
        pos = entry.index('insert')
        entry.insert(pos, text)

    def _get_formula(self, page, field):
        if page in self.formula_dict and field in self.formula_dict[page] and self.formula_dict[page][field]:
            return list(self.formula_dict[page][field].values())[0]
        return ""

    def _save(self):
        page = self.page_var.get()
        
        if page == "备注规则":
            # 保存备注规则
            self._save_note_rules()
            messagebox.showinfo("成功", "备注规则已保存！")
            self.destroy()
            return
            
        # 保存公式
        if page not in self.formula_dict:
            self.formula_dict[page] = {}
        for field, entry in self.entries.items():
            formula = entry.get().strip()
            if formula:
                self.formula_dict[page][field] = {"自定义": formula}
            else:
                self.formula_dict[page].pop(field, None)
        try:
            with open("field_formulas.json", "w", encoding="utf-8") as f:
                json.dump(self.formula_dict, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "公式已保存！")
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}") 