# 游戏交易系统 (Game Trading System)

一个功能强大的游戏交易管理系统，支持库存、交易、价格监控、OCR识别和数据分析。采用现代化 Python GUI，适合游戏物品管理、数据分析和自动化处理。

---

## 目录结构

```
GameTrad/
├── src/                # 主程序源码
│   ├── core/           # 核心业务逻辑
│   ├── gui/            # 图形界面与标签页
│   ├── utils/          # 工具与辅助模块
│   └── scripts/        # 脚本
├── data/               # 数据、配置、图标等资源
├── tests/              # 单元测试
├── docs/               # 文档
├── requirements.txt    # 依赖列表
├── game_trad.spec      # PyInstaller 打包配置
├── installer_utf8.nsi  # NSIS 安装包脚本
└── LICENSE             # 许可证
```

---

## 主要功能

- **库存管理**：实时追踪、自动计算库存价值、利润分析
- **入库/出库管理**：OCR图片识别、批量导入、成本与利润统计
- **交易监控**：实时价格、目标价提醒、策略建议
- **价格监控**：银两/女娲石等价格趋势、异常提醒
- **数据管理**：导入导出、备份恢复、日志、迁移工具
- **自定义公式与物品词典**：灵活扩展
- **Server酱推送**：价格异常自动通知

---

## 技术栈

- Python 3.8+
- ttkbootstrap (现代化 Tkinter GUI)
- MySQL 5.7+
- OCR (Pillow, 其他)
- 多线程/模块化设计

---

## 环境要求

- Windows 10/11
- Python 3.8 及以上
- MySQL 5.7 及以上
- 4GB+ 内存，500MB+ 磁盘空间

---

## 快速开始

1. **克隆项目**
   ```bash
   git clone [repository_url]
   cd GameTrad
   ```

2. **创建虚拟环境并安装依赖**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **配置数据库**
   - 创建 MySQL 数据库
   - 修改 `src/core/db_manager.py` 里的连接参数
   - 初始化表结构（可用脚本或首次运行自动创建）

4. **运行主程序**
   ```bash
   python -m src.gui.main_window
   ```

---

## 打包与分发

### 1. 生成可执行文件

```bash
pyinstaller game_trad.spec
```
- 结果在 `dist/GameTrad.exe`

### 2. 生成安装包（推荐）

- 确保 `dist/GameTrad.exe` 存在
- 运行 NSIS 脚本（需先安装 NSIS）：
  ```powershell
  & 'C:\Program Files (x86)\NSIS\makensis.exe' installer_utf8.nsi
  ```
- 生成的 `GameTrad_Setup.exe` 即为安装包

### 3. 安装与分发

- 运行 `GameTrad_Setup.exe`，按提示安装
- 安装后在开始菜单/桌面找到快捷方式
- 目标机器需有 MySQL 数据库

---

## 配置说明

- **数据库**：`src/core/db_manager.py` 配置
- **物品词典**：`data/item_dict.txt`
- **Server酱**：设置菜单内配置
- **图标/资源**：`data/icon.ico` 及相关目录

---

## 常见问题 FAQ

- **数据库连接失败**：检查服务、参数、权限
- **OCR 识别失败**：图片清晰度、网络、重试
- **价格更新失败**：网络/API、日志排查
- **打包失败**：依赖、路径、资源文件完整性

---

## 贡献指南

1. Fork & 新建分支
2. 提交更改并推送
3. 创建 Pull Request

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE)

---

## 联系方式

- 作者：三只小猪
- 邮箱：[your_email@example.com]
- 项目主页：[repository_url]

---

如需更详细的用户手册、API 文档，请查阅 `docs/` 目录。