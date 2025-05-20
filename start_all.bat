@echo off
echo 正在安装所有依赖并启动应用...
cd game-trad-server

echo 安装服务器依赖...
npm install

if %ERRORLEVEL% neq 0 (
    echo 安装服务器依赖失败
    pause
    exit /b 1
)

echo 安装前端依赖...
cd frontend/react
npm install

if %ERRORLEVEL% neq 0 (
    echo 安装前端依赖失败
    pause
    exit /b 1
)

cd ../..
echo 依赖安装完成，正在启动应用...
npm run dev:all

if %ERRORLEVEL% neq 0 (
    echo 应用启动失败
    pause
)

pause 