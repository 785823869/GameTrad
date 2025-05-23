# GameTrad Web应用启动说明

## 前置需求

使用本Web应用需要安装以下软件：

1. Node.js (推荐版本 v16.0.0 或更高)
2. npm (通常随Node.js一起安装)
3. MySQL数据库 (服务器已配置连接到远程MySQL服务器)

## 启动方法

本应用提供了三个批处理脚本用于启动服务：

### 1. 一键启动 (推荐)

双击运行 `start_all.bat`，该脚本会:
- 安装所有必要的依赖
- 同时启动后端API服务器和前端React应用

### 2. 分别启动

如果您希望分别启动前端和后端，可以：

- 双击运行 `start_server.bat` 启动后端API服务器
- 双击运行 `start_frontend.bat` 启动前端React应用

## 访问应用

服务启动后：
- 前端界面: http://localhost:3000
- 后端API: http://localhost:5000/api

## 常见问题

1. **启动失败**
   - 检查Node.js是否正确安装
   - 检查是否有其他程序占用了3000或5000端口

2. **无法连接到数据库**
   - 请确保您的网络可以连接到远程数据库服务器
   - 检查防火墙设置是否允许数据库连接

3. **前端显示"无法连接到服务器"**
   - 确认后端服务器是否已启动
   - 检查控制台是否有错误信息

## 注意事项

- 初次启动可能需要较长时间安装依赖
- 请保持网络连接稳定
- 关闭应用时，请同时关闭前端和后端窗口 