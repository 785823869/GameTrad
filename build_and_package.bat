@echo off
REM 设置UTF-8编码
chcp 65001 > nul
echo ========================================
echo GameTrad游戏交易系统 - 构建与打包脚本
echo 版本: 1.3.1
echo ========================================
echo.

REM 设置环境变量
set VERSION=1.3.1
set DIST_DIR=dist
set BUILD_DIR=build
set INSTALLER_NAME=GameTrad_Setup_%VERSION%.exe

echo 步骤1: 清理上一次构建的文件
echo ----------------------------------------
if exist "%DIST_DIR%" (
    echo 删除dist目录...
    rmdir /s /q "%DIST_DIR%"
)
if exist "%BUILD_DIR%" (
    echo 删除build目录...
    rmdir /s /q "%BUILD_DIR%"
)
if exist "%INSTALLER_NAME%" (
    echo 删除旧的安装程序...
    del /f /q "%INSTALLER_NAME%"
)
echo 清理完成!
echo.

echo 步骤2: 使用PyInstaller构建可执行文件
echo ----------------------------------------
echo 正在构建可执行文件...

REM 检查Python和PyInstaller是否可用
python --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 找不到Python!
    echo 请确保Python已安装并添加到PATH中。
    pause
    exit /b 1
)

REM 使用pip安装PyInstaller（如果尚未安装）
python -m pip show pyinstaller >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller未安装，正在安装...
    python -m pip install pyinstaller
)

REM 使用python -m运行PyInstaller
python -m PyInstaller game_trad.spec

REM 检查PyInstaller是否成功
if not exist "%DIST_DIR%\GameTrad.exe" (
    echo 错误: PyInstaller构建失败!
    echo 请检查错误信息并解决问题。
    pause
    exit /b 1
)
echo PyInstaller构建成功!
echo.

echo 步骤3: 构建安装程序
echo ----------------------------------------
REM 检查NSIS是否安装
where makensis >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到NSIS安装。请安装NSIS并确保makensis在PATH中。
    echo 您可以从 https://nsis.sourceforge.io/Download 下载NSIS。
    pause
    exit /b 1
)

echo 正在生成安装包...
makensis installer_utf8.nsi

REM 检查安装包是否成功生成
if exist "%INSTALLER_NAME%" (
    echo 安装包生成成功: %INSTALLER_NAME%
    echo 安装包大小: 
    for %%F in ("%INSTALLER_NAME%") do @echo %%~zF 字节
) else (
    echo 错误: 安装包生成失败。
    pause
    exit /b 1
)
echo.

echo 步骤4: 创建安装说明
echo ----------------------------------------
echo 正在创建安装说明文件...
echo # GameTrad游戏交易系统安装说明 > "安装说明.md"
echo. >> "安装说明.md"
echo ## 版本信息 >> "安装说明.md"
echo - 版本号: %VERSION% >> "安装说明.md"
echo - 构建日期: %DATE% >> "安装说明.md"
echo. >> "安装说明.md"
echo ## 安装步骤 >> "安装说明.md"
echo 1. 运行 %INSTALLER_NAME% >> "安装说明.md"
echo 2. 按照安装向导进行操作 >> "安装说明.md"
echo 3. 完成安装后，从开始菜单或桌面快捷方式启动程序 >> "安装说明.md"
echo. >> "安装说明.md"
echo ## 系统要求 >> "安装说明.md"
echo - Windows 10/11 操作系统 >> "安装说明.md"
echo - 4GB及以上内存 >> "安装说明.md"
echo - 500MB可用磁盘空间 >> "安装说明.md"
echo - 网络连接（连接远程数据库） >> "安装说明.md"
echo. >> "安装说明.md"
echo ## 更新说明 >> "安装说明.md"
echo 详细更新内容请参考程序包中的update_notes.md文件 >> "安装说明.md"
echo. >> "安装说明.md"

echo 安装说明文件创建成功!
echo.

echo ========================================
echo 构建和打包过程完成!
echo ----------------------------------------
echo 可执行文件: %DIST_DIR%\GameTrad.exe
echo 安装程序: %INSTALLER_NAME%
echo 安装说明: 安装说明.md
echo ========================================
echo.
echo 感谢使用GameTrad游戏交易系统!
echo.
pause 