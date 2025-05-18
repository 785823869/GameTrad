# GameTrad (游戏交易管理系统)

<div align="center">

![Version](https://img.shields.io/badge/Version-1.3.1-blue)
![Language](https://img.shields.io/badge/Language-Python-blue)
![Framework](https://img.shields.io/badge/Framework-TKinter%20|%20PyQt6-orange)
![License](https://img.shields.io/badge/License-专有软件-red)

</div>

## 项目概述

**GameTrad** 是一个专为游戏物品交易设计的高效管理系统，提供完整的库存管理、交易记录、市场监控和数据分析功能。系统目前有两个版本：

- **TKinter版本**：基于tkinter和ttkbootstrap构建的经典版本
- **PyQt6版本**：基于PyQt6构建的现代化界面版本

强大的数据统计功能和市场监控能力，帮助您实时掌握交易状态和库存价值，降低交易风险，提高盈利空间。

### 最新更新

- **价格显示优化**：银两行情和女娲石行情默认显示DD373平台的图表，其他平台可通过选择框切换
- **图表UI优化**：改进仪表盘中物价趋势图表显示，解决中文字体乱码问题
- **X轴显示优化**：优化图表X轴日期标签显示，实现均匀间距，提升美观度
- **搜索功能增强**：为物品下拉框增加搜索功能，支持实时过滤，快速定位物品
- **库存物品管理优化**：下拉框显示所有库存管理物品，包括库存为0的物品
- **价格显示优化**：改进银两行情和女娲石行情数据的自动加载和缓存机制
- **UI响应性提升**：改进界面响应速度和整体用户体验

## 项目文件结构

```
GameTrad/
├── main.py                     # 程序主入口文件
├── run_migration_tool.py       # 数据迁移工具启动脚本
├── test_db_connection.py       # 数据库连接测试脚本
├── requirements.txt            # 项目依赖列表
├── game_trad.spec              # PyInstaller配置文件
├── README.md                   # 项目说明文档(当前文件)
├── update_notes.md             # 更新说明文档
├── LICENSE                     # 许可证文件
├── build_installer.bat         # 安装包构建脚本
├── installer_utf8.nsi          # NSIS安装包配置文件
├── src/                        # 源代码目录
│   ├── __init__.py             # 包初始化文件
│   ├── clear_all_data.py       # 数据清理工具
│   │   ├── __init__.py
│   │   ├── core/                   # 核心功能模块
│   │   │   ├── __init__.py
│   │   │   ├── db_manager.py       # 数据库管理
│   │   │   ├── formula_manager.py  # 公式管理
│   │   │   ├── inventory_calculator.py # 库存计算
│   │   │   ├── inventory_manager.py # 库存管理
│   │   │   └── trade_analyzer.py   # 交易分析
│   │   ├── gui/                    # 图形界面模块
│   │   │   ├── __init__.py
│   │   │   ├── main_window.py      # 主窗口
│   │   │   ├── import_data_dialog.py # 数据导入对话框
│   │   │   ├── components/         # UI组件
│   │   │   ├── dialogs/            # 对话框
│   │   │   ├── tabs/               # 标签页
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dashboard_tab.py # 仪表盘页面
│   │   │   │   ├── inventory_tab.py # 库存管理页面
│   │   │   │   ├── stock_in_tab.py  # 入库管理页面
│   │   │   │   ├── stock_out_tab.py # 出库管理页面
│   │   │   │   ├── trade_monitor_tab.py # 交易监控页面
│   │   │   │   ├── nvwa_price_tab.py # 女娲石价格页面
│   │   │   │   ├── silver_price_tab.py # 银两价格页面
│   │   │   │   └── log_tab.py       # 日志页面
│   │   │   └── utils/              # GUI工具
│   │   ├── scripts/                # 脚本工具
│   │   │   ├── __init__.py
│   │   │   ├── check_tabs.py       # 标签页检查
│   │   │   ├── import_data_overwrite.py # 数据导入覆盖
│   │   │   ├── import_to_db.py     # 数据导入到数据库
│   │   │   ├── init_db.py          # 数据库初始化
│   │   │   ├── migrate_data.py     # 数据迁移
│   │   │   ├── migrate_data_gui.py # 数据迁移GUI
│   │   │   └── test_data_migration.py # 数据迁移测试
│   │   └── utils/                  # 工具类
│   │       ├── __init__.py
│   │       ├── clipboard_helper.py # 剪贴板助手
│   │       ├── logger.py           # 日志工具
│   │       ├── ocr.py              # OCR识别
│   │       ├── operation_types.py  # 操作类型
│   │       ├── path_resolver.py    # 路径解析
│   │       ├── recipe_parser.py    # 配方解析
│   │       ├── restore_logs.py     # 日志恢复
│   │       ├── sidebar.py          # 侧边栏
│   │       ├── ui_manager.py       # UI管理
│   │       └── updater.py          # 更新工具
│   ├── data/                       # 数据目录
│   │   └── icon.ico                # 程序图标
│   ├── docs/                       # 文档目录
│   ├── config/                     # 配置目录
│   │   └── server_chan_config.json # Server酱配置
│   └── dist/                       # 打包输出目录
├── build/                      # 构建临时目录
└── logs/                       # 日志目录
```

## 主要功能

### 1. 仪表盘（dashboard_tab.py）

提供全面的数据概览和可视化分析：
- 总库存价值、利润率分析
- 市场行情实时监控（银两/女娲石价格）
- 物价趋势图表，支持选择物品查看价格历史走势
- 均匀分布的日期标签，美观直观的图表显示
- 高级搜索和过滤功能，快速定位所需物品
- 库存详情一览，支持自动滚动显示
- 用户库存监控，实时掌握客户物品库存情况

### 2. 库存管理（inventory_tab.py）

全面管理游戏物品库存：
- 实时掌握剩余数量、平均成本和库存价值
- 自动计算平均成本、利润和预估利润
- 支持物品名称搜索和筛选
- 单个物品的完整入库/出库历史
- 包含所有库存管理物品，即使库存为0

### 3. 入库管理（stock_in_tab.py）

管理所有入库记录：
- 记录物品名称、入库时间、数量、成本和库存价值
- 支持手动添加、编辑和删除
- OCR图像识别自动录入数据
- 批量导入CSV文件

### 4. 出库管理（stock_out_tab.py）

管理所有出库记录：
- 记录物品名称、出库时间、数量、单价和总金额
- 自动计算利润和手续费
- 支持OCR识别、自动添加
- 批量导入CSV文件

### 5. 交易监控（trade_monitor_tab.py）

自动监控交易市场情况：
- 实时价格、目标价提醒、策略建议
- 自动计算成本、利润和利润率
- 资金效率分析
- OCR识别市场情况，快速添加

### 6. 价格监控（silver_price_tab.py, nvwa_price_tab.py）

监控游戏货币价格：
- 自动抓取多个平台价格数据
- 价格趋势对比
- 异常价格自动通知
- 可设置价格异常提醒和通过Server酱推送
- 优化的价格数据缓存机制，减少API请求次数
- 银两行情和女娲石行情默认显示DD373平台的图表，其他平台可通过选择框切换

### 7. 数据管理（migrate_data.py, migrate_data_gui.py）

完善的数据输入输出功能：
- 支持CSV格式数据输入输出
- 自动备份和恢复数据
- 详细的数据日志记录
- 支持数据迁移和备份

### 8. 自定义公式与物品词典（formula_manager.py）

丰富的自定义功能：
- 灵活扩展的库存价值计算公式
- 物品名称词典管理
- Server酱推送配置
- 图表显示和资源配置

## 核心模块说明

### main.py
主入口文件，负责初始化程序环境、创建GUI窗口，并处理程序启动和关闭流程。

### src/core/
包含核心业务逻辑模块：
- `db_manager.py`: 数据库连接和操作管理
- `inventory_calculator.py`: 库存价值和利润计算
- `inventory_manager.py`: 库存物品管理
- `formula_manager.py`: 自定义计算公式管理
- `trade_analyzer.py`: 交易数据分析

### src/gui/
包含所有GUI相关代码：
- `main_window.py`: 主窗口实现，整合各个标签页
- `tabs/`: 各功能标签页实现（仪表盘、库存、入库、出库等）
- `components/`: 可复用UI组件
- `dialogs/`: 对话框实现

### src/utils/
包含各种工具类：
- `logger.py`: 日志记录工具
- `path_resolver.py`: 文件路径解析（兼容开发环境和打包环境）
- `updater.py`: 在线更新功能
- `ocr.py`: OCR图像识别集成
- `clipboard_helper.py`: 剪贴板操作助手

### src/scripts/
包含各种脚本工具：
- `migrate_data.py`: 数据迁移核心功能
- `migrate_data_gui.py`: 数据迁移GUI界面
- `init_db.py`: 数据库初始化脚本

## 安装与使用

### 系统要求
- **操作系统**：Windows 10/11
- **Python**：3.8 及以上
- **内存**：4GB+
- **磁盘空间**：500MB+
- **数据库**：MySQL 5.7+（已配置远程连接）

### 安装方法

#### 1. 安装包安装（推荐）
直接运行 `GameTrad_Setup.exe` 安装程序

#### 2. 源码运行

1. 克隆或下载项目代码
2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
3. 运行应用程序：
   ```
   python main.py
   ```

#### 3. 自行构建

如需自行构建可执行文件和安装包，按以下步骤操作：

1. 构建可执行文件：
   ```
   pyinstaller game_trad.spec
   ```

2. 构建安装包（需要安装NSIS）：
   ```
   build_installer.bat
   ```

### 使用说明

1. 首次启动时，系统会自动连接到远程数据库
2. 在仪表盘中可以查看价格行情和库存概览
3. 通过侧边栏可切换到不同的功能模块
4. 使用仪表盘中的搜索框快速查找特定物品
5. 周期按钮切换图表时间范围（日/周/月）

## 技术栈

### TKinter版本
- **GUI框架**：tkinter + ttkbootstrap
- **图表组件**：matplotlib（支持中文字体自适应）
- **数据处理**：pandas, numpy
- **数据库**：MySQL (mysqlclient)
- **网络请求**：requests
- **中文支持**：自动检测并应用系统中文字体

### PyQt6版本
- **GUI框架**：PyQt6
- **图表组件**：matplotlib
- **数据处理**：pandas, numpy
- **数据库**：MySQL (mysqlclient)
- **网络请求**：requests

## 数据库说明

本系统已经配置好远程MySQL数据库连接，用户**无需安装本地MySQL服务**即可正常使用。数据存储在云端服务器上，支持多设备数据共享和同步。

> 注意：使用本系统需要保持网络连接，以确保与远程数据库的正常通信。

## 常见问题 FAQ

### 1. 价格行情显示"加载中..."

可能原因和解决方法：
- 网络连接问题：检查网络连接是否正常
- API访问限制：等待一段时间后重试
- 价格数据源异常：尝试切换到银两/女娲石行情标签页，再回到仪表盘
- 重启应用：关闭并重新启动应用程序
- 查看日志：查看控制台输出，了解具体错误信息

### 2. 数据库连接失败

检查服务、参数、权限，确保网络连接正常。如需修改连接配置，可编辑 `src/core/db_manager.py` 中的连接参数。

### 3. OCR 识别失败

确保图片清晰度足够高，网络连接正常。可尝试重新截图或调整OCR识别参数提高识别准确率。

### 4. 物品搜索不显示某些物品

默认情况下，系统会显示所有库存管理中的物品，包括库存为0的物品。如果特定物品不显示在下拉框中，可能有以下原因：
- 该物品尚未添加到库存管理系统
- 搜索文本与物品名称不匹配，尝试使用更简短的关键词
- 刷新仪表盘，重新加载物品列表

### 5. 图表显示中文乱码

系统会自动检测并使用合适的中文字体。如果仍然出现乱码问题：
- 确保系统安装了中文字体（如微软雅黑、宋体等）
- 重启应用程序，让系统重新检测字体
- 查看控制台输出，了解字体检测和应用情况

## 版本规划

1. **数据分析增强**：增加更高级的统计分析和预测功能
2. **移动端支持**：开发配套移动应用，随时随地管理交易
3. **AI辅助决策**：引入智能交易策略建议和价格预测
4. **云端同步增强**：增强数据同步和备份能力
5. **多语言支持**：增加英文等其他语言界面
6. **自定义图表**：允许用户自定义仪表盘和图表显示

## 更新日志

### v1.3.1 (2024-07)
- 银两行情和女娲石行情默认显示DD373平台的图表，其他平台可通过选择框切换
- 优化代码结构和性能
- 修复其他已知问题

### v1.3.0 (2024-07)
- 更新图标资源，改进程序快捷方式显示
- 优化安装程序配置，确保任务栏图标显示正确
- 修复其他已知问题和性能优化

### v1.2.0 (2024-06)
- 优化图表UI，解决中文字体乱码问题
- 改进X轴日期标签显示，实现均匀间距
- 增加物品搜索功能，支持实时过滤
- 显示所有库存管理物品，包括库存为0的物品
- 优化价格数据加载和缓存机制

### v1.1.0 (2024-04)
- 价格显示优化：修复了仪表盘中银两行情和女娲石行情数据的自动加载问题
- UI优化：改进了界面响应速度和用户体验
- 增加PyQt6版本：全新基于PyQt6的现代化界面版本

### v1.0.0 (2024-02)
- 首次发布，包含核心功能
- 支持库存管理、入库出库、交易监控和价格监控

## 软件许可

本软件为专有软件，使用受到限制。详见 [LICENSE](LICENSE) 文件。

## 开发团队

- **开发者**：三只小猪
- **版本**：1.3.1

---

<div align="center">

感谢使用 GameTrad 游戏交易管理系统

</div>