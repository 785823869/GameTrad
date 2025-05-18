# GameTrad 项目结构

## 目录结构

```
GameTrad/
├── build/                  # PyInstaller构建临时文件
├── config/                 # 配置文件目录
├── data/                   # 资源文件目录
│   └── icon.ico            # 程序图标
├── database_backups/       # 数据库备份目录
├── dist/                   # PyInstaller构建输出目录
│   └── GameTrad.exe        # 编译后的可执行文件
├── docs/                   # 文档目录
│   └── project_structure.md # 项目结构文档
├── logs/                   # 日志文件目录
├── src/                    # 源代码目录
│   ├── core/               # 核心功能模块
│   │   ├── db_manager.py   # 数据库管理器
│   │   ├── formula_manager.py # 公式管理器
│   │   ├── inventory_calculator.py # 库存计算器
│   │   ├── inventory_manager.py # 库存管理器
│   │   └── trade_analyzer.py # 交易分析器
│   ├── gui/                # 图形界面模块
│   │   ├── components/     # UI组件
│   │   ├── dialogs/        # 对话框
│   │   ├── tabs/           # 标签页
│   │   │   ├── dashboard_tab.py # 仪表盘标签页
│   │   │   ├── inventory_tab.py # 库存管理标签页
│   │   │   ├── log_tab.py  # 日志标签页
│   │   │   ├── nvwa_price_tab.py # 女娲石价格标签页
│   │   │   ├── silver_price_tab.py # 银两价格标签页
│   │   │   ├── stock_in_tab.py # 入库管理标签页
│   │   │   ├── stock_out_tab.py # 出库管理标签页
│   │   │   └── trade_monitor_tab.py # 交易监控标签页
│   │   ├── utils/          # GUI工具函数
│   │   ├── import_data_dialog.py # 数据导入对话框
│   │   └── main_window.py  # 主窗口
│   ├── scripts/            # 脚本文件
│   │   └── import_data_overwrite.py # 数据导入脚本
│   └── utils/              # 工具函数
│       └── path_resolver.py # 路径解析器
├── tests/                  # 测试目录
├── .gitignore              # Git忽略文件
├── build_installer.bat     # 安装包构建脚本
├── game_trad.spec          # PyInstaller规范文件
├── installer_utf8.nsi      # NSIS安装脚本
├── LICENSE                 # 许可证文件
├── main.py                 # 程序入口点
├── README.md               # 项目说明文件
├── requirements.txt        # 依赖项列表
├── server_chan_config.json # Server酱配置文件
└── update_notes.md         # 更新说明文件
```

## 核心模块说明

### 1. 数据库管理 (`src/core/db_manager.py`)
- 负责与MySQL数据库的连接和交互
- 提供数据的增删改查操作
- 管理数据库结构和表关系

### 2. 库存管理 (`src/core/inventory_manager.py`)
- 管理游戏物品库存
- 处理入库和出库操作
- 计算库存价值和平均成本

### 3. 库存计算器 (`src/core/inventory_calculator.py`)
- 计算库存数据
- 从入库和出库记录重新计算库存
- 更新库存表

### 4. 公式管理器 (`src/core/formula_manager.py`)
- 管理自定义计算公式
- 处理价格计算和转换
- 支持公式的导入和导出

### 5. 交易分析器 (`src/core/trade_analyzer.py`)
- 分析交易数据和趋势
- 计算利润和利润率
- 提供交易策略建议

## GUI模块说明

### 1. 主窗口 (`src/gui/main_window.py`)
- 程序的主界面
- 管理所有标签页和菜单
- 处理全局事件和状态

### 2. 标签页 (`src/gui/tabs/`)
- **仪表盘** (`dashboard_tab.py`): 提供数据概览和可视化分析
- **库存管理** (`inventory_tab.py`): 管理游戏物品库存
- **入库管理** (`stock_in_tab.py`): 管理入库记录
- **出库管理** (`stock_out_tab.py`): 管理出库记录
- **交易监控** (`trade_monitor_tab.py`): 监控交易市场情况
- **银两价格** (`silver_price_tab.py`): 监控银两价格
- **女娲石价格** (`nvwa_price_tab.py`): 监控女娲石价格
- **日志** (`log_tab.py`): 显示系统日志

### 3. 对话框 (`src/gui/dialogs/`)
- 各种弹出对话框，如添加、编辑、确认等

### 4. 组件 (`src/gui/components/`)
- 可重用的UI组件，如自定义表格、图表等

## 工具模块说明

### 1. 路径解析器 (`src/utils/path_resolver.py`)
- 处理文件和目录路径
- 确保在不同环境下路径正确

### 2. 数据导入 (`src/scripts/import_data_overwrite.py`)
- 处理CSV数据的导入
- 支持批量导入入库和出库记录

## 构建和部署

### 1. PyInstaller规范 (`game_trad.spec`)
- 定义如何打包应用程序
- 指定包含的文件和依赖项

### 2. NSIS安装脚本 (`installer_utf8.nsi`)
- 定义安装程序的行为
- 配置安装选项和快捷方式

### 3. 构建脚本 (`build_installer.bat`)
- 自动化构建过程
- 生成可执行文件和安装包 