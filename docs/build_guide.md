# GameTrad 构建指南

本文档提供了如何构建GameTrad游戏交易系统可执行文件和安装包的详细说明。

## 准备环境

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装NSIS (Nullsoft Scriptable Install System)

NSIS是用于创建Windows安装程序的开源工具。

#### 下载和安装NSIS

1. 访问NSIS官方网站: https://nsis.sourceforge.io/Download
2. 下载最新版本的NSIS (例如 "NSIS 3.08")
3. 运行下载的安装程序并完成安装

#### 将NSIS添加到系统PATH

1. 右键点击"此电脑"或"我的电脑"，选择"属性"
2. 点击"高级系统设置"
3. 在"高级"选项卡中，点击"环境变量"
4. 在"系统变量"部分，找到并选择"Path"变量，然后点击"编辑"
5. 点击"新建"，添加NSIS安装目录 (通常是 `C:\Program Files (x86)\NSIS` 或 `C:\Program Files\NSIS`)
6. 点击"确定"保存所有更改

## 构建步骤

### 1. 构建可执行文件

使用PyInstaller构建可执行文件:

```bash
pyinstaller game_trad.spec
```

成功后，可执行文件将生成在`dist`目录中。

### 2. 构建安装包

有两种方法可以构建安装包:

#### 方法1: 使用批处理脚本

运行项目根目录中的`build_installer.bat`脚本:

```bash
build_installer.bat
```

这个脚本会自动检查NSIS是否安装，然后构建安装包。

#### 方法2: 手动构建

如果您更喜欢手动构建，可以直接运行NSIS命令:

```bash
makensis installer_utf8.nsi
```

### 3. 验证安装包

构建成功后，在项目根目录中应该生成`GameTrad_Setup_1.3.1.exe`文件。

## 故障排除

### 1. "未找到NSIS安装"错误

确保:
- NSIS已正确安装
- NSIS的安装目录已添加到系统PATH中
- 如果刚刚添加PATH，请重新打开命令提示符或PowerShell

### 2. 中文显示乱码

如果批处理文件中的中文显示为乱码，可能是编码问题。确保:
- 批处理文件使用GBK/GB2312编码 (中文Windows默认编码)
- 在批处理文件开头添加`chcp 936`命令切换到中文代码页

### 3. "未找到PyInstaller生成的可执行文件"错误

确保:
- 先运行`pyinstaller game_trad.spec`命令生成可执行文件
- 检查`dist`目录中是否存在`GameTrad.exe`文件

## 注意事项

- 构建过程可能需要几分钟时间，取决于您的计算机性能
- 确保有足够的磁盘空间用于构建过程
- 构建完成后，建议测试安装包以确保一切正常工作 