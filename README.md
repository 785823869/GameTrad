# GameTrad (游戏交易管理系统)

<div align="center">

![Version](https://img.shields.io/badge/Version-1.3.2-blue)
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

- **应用图标更新**：更新了应用程序图标，包括主窗口标题栏、安装包图标、桌面快捷方式和任务栏图标
- **价格显示优化**：银两行情和女娲石行情默认显示DD373平台的图表，其他平台可通过选择框切换
- **图表UI优化**：改进仪表盘中物价趋势图表显示，解决中文字体乱码问题
- **X轴显示优化**：优化图表X轴日期标签显示，实现均匀间距，提升美观度
- **搜索功能增强**：为物品下拉框增加搜索功能，支持实时过滤，快速定位物品
- **库存物品管理优化**：下拉框显示所有库存管理物品，包括库存为0的物品
- **价格显示优化**：改进银两行情和女娲石行情数据的自动加载和缓存机制
- **UI响应性提升**：改进界面响应速度和整体用户体验
- **在线更新优化**：支持从GitHub Releases自动检查和下载更新

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
├── build_and_package.bat       # 安装包构建脚本
├── simple_installer.nsi        # NSIS简单安装包配置文件
├── installer_utf8.nsi          # NSIS安装包UTF8配置文件
├── .gitignore                  # Git忽略配置文件
├── server_chan_config.json     # Server酱推送配置文件
├── 在线更新功能使用说明.md      # 在线更新功能文档
├── update_info_example.json    # 更新信息示例文件
├── 安装说明.md                  # 安装指南
├── src/                        # 源代码目录
│   ├── __init__.py             # 包初始化文件（包含版本号）
│   ├── clear_all_data.py       # 数据清理工具
│   ├── core/                   # 核心功能模块
│   │   ├── __init__.py
│   │   ├── db_manager.py       # 数据库管理
│   │   ├── formula_manager.py  # 公式管理
│   │   ├── inventory_calculator.py # 库存计算
│   │   ├── inventory_manager.py # 库存管理
│   │   └── trade_analyzer.py   # 交易分析
│   ├── gui/                    # 图形界面模块
│   │   ├── __init__.py
│   │   ├── main_window.py      # 主窗口
│   │   ├── import_data_dialog.py # 数据导入对话框
│   │   ├── components/         # UI组件
│   │   ├── dialogs/            # 对话框
│   │   │   └── modal_input_dialog.py # 模态输入对话框
│   │   ├── tabs/               # 标签页
│   │   │   ├── __init__.py
│   │   │   ├── dashboard_tab.py # 仪表盘页面
│   │   │   ├── inventory_tab.py # 库存管理页面
│   │   │   ├── stock_in_tab.py  # 入库管理页面
│   │   │   ├── stock_out_tab.py # 出库管理页面
│   │   │   ├── trade_monitor_tab.py # 交易监控页面
│   │   │   ├── nvwa_price_tab.py # 女娲石价格页面
│   │   │   ├── silver_price_tab.py # 银两价格页面
│   │   │   └── log_tab.py       # 日志页面
│   │   └── utils/              # GUI工具
│   ├── scripts/                # 脚本工具
│   │   ├── __init__.py
│   │   ├── check_tabs.py       # 标签页检查
│   │   ├── import_data_overwrite.py # 数据导入覆盖
│   │   ├── import_to_db.py     # 数据导入到数据库
│   │   ├── init_db.py          # 数据库初始化
│   │   ├── migrate_data.py     # 数据迁移
│   │   ├── migrate_data_gui.py # 数据迁移GUI
│   │   └── test_data_migration.py # 数据迁移测试
│   └── utils/                  # 工具类
│       ├── __init__.py
│       ├── clipboard_helper.py # 剪贴板助手
│       ├── logger.py           # 日志工具
│       ├── ocr.py              # OCR识别
│       ├── operation_types.py  # 操作类型
│       ├── path_resolver.py    # 路径解析
│       ├── recipe_parser.py    # 配方解析
│       ├── restore_logs.py     # 日志恢复
│       ├── sidebar.py          # 侧边栏
│       ├── ui_manager.py       # UI管理
│       └── updater.py          # 更新工具
├── data/                       # 数据目录
│   └── config/                 # 配置文件目录
├── docs/                       # 文档目录
├── build/                      # 构建临时目录
├── dist/                       # 打包输出目录
├── logs/                       # 日志目录
├── database_backups/           # 数据库备份目录
├── config/                     # 配置目录
├── .cursor/                    # Cursor IDE配置目录
├── __pycache__/                # Python缓存目录
├── tests/                      # 测试目录
└── .venv/                      # 虚拟环境目录
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

### 9. 在线更新功能（updater.py）

自动检查、下载和安装最新版本：
- 连接GitHub Releases自动检查更新
- 一键下载和安装新版本
- 版本信息和更新说明显示
- 支持手动和自动更新方式

## 在线更新功能

游戏交易系统集成了便捷的在线更新功能，让用户能够随时获取最新版本，无需手动下载安装包。

### 更新源配置

系统默认从以下GitHub仓库获取更新：
```
https://github.com/785823869/GameTrad/releases
```

### 使用方法

1. **检查更新**：点击菜单栏中的"帮助" -> "检查更新"
2. **下载更新**：如果发现新版本，点击"下载更新"按钮
3. **安装更新**：下载完成后，点击"安装更新"按钮

### 开发者发布指南

如要发布新版本，请按以下步骤：

1. 准备新版本安装包（例如：`GameTrad_Setup_1.3.3.exe`）
2. 在GitHub仓库创建新的Release
3. 上传安装包并添加详细的更新说明
4. 设置正确的版本标签（例如：`v1.3.3`）

Release信息格式示例：
```json
{
  "tag_name": "v1.3.3",
  "name": "游戏交易系统 v1.3.3",
  "body": "## 更新内容\n\n- 修复了仪表盘显示问题\n- 优化数据导入功能\n- 提升系统稳定性",
  "published_at": "2024-06-01T08:00:00Z",
  "assets": [
    {
      "name": "GameTrad_Setup_1.3.3.exe",
      "browser_download_url": "https://github.com/785823869/GameTrad/releases/download/v1.3.3/GameTrad_Setup_1.3.3.exe"
    }
  ]
}
```

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

## 安装与使用

### 系统要求
- Windows 10/11 (64位)
- 最低4GB内存
- 至少100MB可用磁盘空间

### 安装方法
1. 从GitHub Releases页面下载最新版本安装包：https://github.com/785823869/GameTrad/releases
2. 运行安装程序，按照向导完成安装
3. 启动程序，进行初始配置

### 开发环境设置
1. 克隆代码库
2. 创建虚拟环境：`python -m venv .venv`
3. 激活虚拟环境：`.venv\Scripts\activate`
4. 安装依赖：`pip install -r requirements.txt`
5. 运行程序：`python main.py`

## 常见问题

### 数据库连接错误
问题：启动程序时提示"无法连接到数据库"
解决：检查数据库文件是否存在，如果损坏，可使用备份文件恢复

### OCR识别不准确
问题：OCR识别结果不准确或失败
解决：确保图像清晰，调整OCR设置，或手动输入数据

### 价格数据未更新
问题：价格数据显示为"加载中..."
解决：检查网络连接，或重启应用程序

### 更新失败
问题：在线更新下载或安装失败
解决：尝试手动下载安装包，或检查网络连接

## 版权与许可

GameTrad是专有软件，未经许可不得复制、分发或修改。

© 2024 GameTrad团队，保留所有权利。