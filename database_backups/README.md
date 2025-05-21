# 数据库修复指南

## 修复"交易监控"页面无数据显示问题

如果您在使用"交易监控"页面时看到以下错误：

```
DB ERROR: 查询执行失败: Table 'OcrTrade.transactions' doesn't exist
```

这表示数据库中缺少必要的`transactions`表。请按照以下步骤修复：

### 方法一：使用提供的SQL脚本

1. 打开您的MySQL客户端工具（如MySQL Workbench、Navicat、phpMyAdmin等）
2. 连接到OcrTrade数据库
3. 执行`create_transactions_table.sql`脚本文件中的SQL命令

### 方法二：手动执行SQL命令

如果您无法使用上述脚本，可以手动复制并执行以下SQL命令：

```sql
CREATE TABLE IF NOT EXISTS `transactions` (
    `id` int NOT NULL AUTO_INCREMENT,
    `transaction_type` VARCHAR(50) NOT NULL,
    `transaction_time` DATETIME NOT NULL,
    `item_name` VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `quantity` INT NOT NULL,
    `price` DECIMAL(10,2) NOT NULL,
    `total_amount` DECIMAL(10,2) NOT NULL,
    `fee` DECIMAL(10,2) DEFAULT 0,
    `platform` VARCHAR(50) DEFAULT '',
    `note` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `target_price` DECIMAL(10,2) DEFAULT 0,
    `planned_price` DECIMAL(10,2) DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 添加索引以提高查询性能
CREATE INDEX idx_transaction_type ON transactions (transaction_type);
CREATE INDEX idx_transaction_time ON transactions (transaction_time);
CREATE INDEX idx_item_name ON transactions (item_name);
```

执行完成后，刷新"交易监控"页面，即可正常使用。

## 数据库连接问题

如果遇到数据库连接失败问题，请检查以下内容：

1. 确认数据库服务器是否运行
2. 检查配置文件中的连接信息是否正确，包括主机名、端口、用户名和密码
3. 确认用户是否具有访问数据库的权限

游戏交易系统的数据库配置文件位于：`~/.gametrad/db_config.json`（～代表用户主目录） 