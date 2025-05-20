@echo off
echo 正在安装前端依赖...
cd game-trad-server/frontend/react
npm install

if %ERRORLEVEL% neq 0 (
    echo 安装依赖失败
    pause
    exit /b 1
)

echo 依赖安装完成，正在启动前端...
npm start

if %ERRORLEVEL% neq 0 (
    echo 前端启动失败
    pause
)

pause 