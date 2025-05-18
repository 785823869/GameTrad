@echo off
chcp 936 > nul
echo 正在构建GameTrad游戏交易系统安装包...

REM 检查NSIS是否安装
where makensis >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到NSIS安装。请安装NSIS并确保makensis在PATH中。
    echo 您可以从 https://nsis.sourceforge.io/Download 下载NSIS。
    pause
    exit /b 1
)

REM 检查PyInstaller生成的可执行文件是否存在
if not exist "dist\GameTrad.exe" (
    echo 错误: 未找到PyInstaller生成的可执行文件。请先运行PyInstaller。
    echo 运行命令: pyinstaller game_trad.spec
    pause
    exit /b 1
)

REM 运行NSIS生成安装包
echo 正在生成安装包...
makensis installer_utf8.nsi

REM 检查安装包是否成功生成
if exist "GameTrad_Setup_1.3.1.exe" (
    echo 安装包生成成功: GameTrad_Setup_1.3.1.exe
) else (
    echo 错误: 安装包生成失败。
    pause
    exit /b 1
)

echo.
echo 构建完成！
pause 