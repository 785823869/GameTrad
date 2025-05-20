@echo off
echo 正在安装服务器依赖...
cd game-trad-server
npm install

if %ERRORLEVEL% neq 0 (
    echo 安装依赖失败
    pause
    exit /b 1
)

echo 依赖安装完成，正在启动服务器...
npm run dev

if %ERRORLEVEL% neq 0 (
    echo 服务器启动失败
    pause
)

pause 