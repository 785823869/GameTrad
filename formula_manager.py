import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox
import json
import os

PAGE_FIELDS = {
    "库存管理": ["物品", "库存数", "总入库均价", "保本均价", "总出库均价", "利润", "利润率", "成交利润额", "库存价值"],
    "入库管理": ["物品", "当前时间", "入库数量", "入库花费", "入库均价", "备注"],
    "出库管理": ["物品", "当前时间", "出库数量", "单价", "手续费", "出库总数量", "出货均价", "出库总金额", "备注"],
    "交易监控": ["物品", "当前时间", "数量", "一口价", "目标买入价", "计划卖出价", "保本卖出价", "利润", "利润率", "入库策略"]
}

OPS = ['+', '-', '*', '/', '(', ')']

class FormulaManagerWindow(tb.Toplevel):
    def __init__(self, master, main_gui):
        super().__init__(master)
        self.title("公式管理")
        self.geometry("900x650")
        self.main_gui = main_gui
        self.formula_dict = {}
        self.page_var = tb.StringVar(value="库存管理")
        self.entries = {}
        self._load_formulas()
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
            entry.insert(0, self._get_formula(page, field))
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