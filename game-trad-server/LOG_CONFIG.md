# GameTrad 日志配置说明

## 调试数据过多问题解决方案

如果您遇到控制台输出调试数据过多的问题，可以通过以下方法调整日志级别：

### 1. 创建或编辑 .env 文件

在项目根目录 `game-trad-server/` 下创建 `.env` 文件（如果不存在），添加以下内容：

```
# 日志设置
LOG_LEVEL=WARN      # 可选值: ERROR, WARN, INFO, DEBUG (默认为 WARN)
LOG_ALL_TO_DB=false # 是否将所有日志级别记录到数据库
DB_DEBUG=false      # 是否显示数据库调试信息
```

### 2. 日志级别说明

- **ERROR**: 只显示错误信息，控制台输出最少
- **WARN**: 显示警告和错误信息（建议日常使用）
- **INFO**: 显示信息、警告和错误信息（一般调试使用）
- **DEBUG**: 显示所有调试信息（调试问题时使用）

### 3. 日志文件

即使减少了控制台输出，所有日志仍会被记录到文件中：
- `logs/app.log`: 所有级别的日志
- `logs/error.log`: 仅错误日志

### 4. 执行数据库迁移

我们创建了一个数据库迁移脚本，用于解决"Unknown column 'profit'"错误：

```bash
node backend/migrations/add_profit_columns.js
```

这将为 `stock_out` 表添加缺失的 `profit` 列，解决常见的数据库错误日志。

### 5. 查看日志

您可以通过 API 或直接访问日志文件来查看历史日志：

- API: `GET /api/logs?type=app&limit=100` 
- 文件: 查看 `logs/app.log` 和 `logs/error.log`

## 更多信息

如果您需要对日志系统进行更多自定义，请修改以下文件：

- `backend/utils/logger.js`: 主日志系统
- `backend/utils/requestTracker.js`: 请求跟踪器
- `backend/utils/db.js`: 数据库日志 