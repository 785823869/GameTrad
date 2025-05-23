; UTF-8 编码声明
Unicode true

; 安装程序初始定义常量
!define PRODUCT_NAME "游戏交易系统"
!define PRODUCT_VERSION "1.3.2"
!define PRODUCT_PUBLISHER "三只小猪"
!define PRODUCT_WEB_SITE "https://github.com/785823869/GameTrad"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\GameTrad.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor lzma

; MUI 现代界面定义
!include "MUI2.nsh"

; MUI 预定义
!define MUI_ABORTWARNING
!define MUI_ICON "data\icon.ico"
!define MUI_UNICON "data\icon.ico"

; 欢迎页面
!insertmacro MUI_PAGE_WELCOME
; 许可协议页面
!insertmacro MUI_PAGE_LICENSE "LICENSE"
; 安装目录选择页面
!insertmacro MUI_PAGE_DIRECTORY
; 安装过程页面
!insertmacro MUI_PAGE_INSTFILES
; 安装完成页面
!define MUI_FINISHPAGE_RUN "$INSTDIR\GameTrad.exe"
!insertmacro MUI_PAGE_FINISH

; 卸载程序页面
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 安装界面包含的语言设置
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装程序版本号
VIProductVersion "1.3.2.0"
VIAddVersionKey /LANG=2052 "ProductName" "游戏交易系统"
VIAddVersionKey /LANG=2052 "Comments" "游戏交易管理系统"
VIAddVersionKey /LANG=2052 "CompanyName" "三只小猪"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (C) 2024"
VIAddVersionKey /LANG=2052 "FileDescription" "游戏交易系统安装程序"
VIAddVersionKey /LANG=2052 "FileVersion" "1.3.2.0"

; 安装程序名称
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "GameTrad_Setup_${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\GameTrad"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  ; 复制主程序文件
  File "dist\GameTrad.exe"
  
  ; 复制图标文件到安装目录
  SetOutPath "$INSTDIR\data"
  File "data\icon.ico"
  SetOutPath "$INSTDIR"
  
  ; 复制文档文件
  SetOutPath "$INSTDIR\docs"
  File /r "docs\*.*"
  SetOutPath "$INSTDIR"
  
  ; 复制README和LICENSE
  File "README.md"
  File "LICENSE"
  File "update_notes.md"
  
  ; 创建开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\游戏交易系统"
  CreateShortCut "$SMPROGRAMS\游戏交易系统\游戏交易系统.lnk" "$INSTDIR\GameTrad.exe" "" "$INSTDIR\data\icon.ico"
  CreateShortCut "$DESKTOP\游戏交易系统.lnk" "$INSTDIR\GameTrad.exe" "" "$INSTDIR\data\icon.ico"
  
  ; 写入卸载信息
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\GameTrad.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\data\icon.ico"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Section Uninstall
  ; 删除程序文件
  Delete "$INSTDIR\GameTrad.exe"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\update_notes.md"
  
  ; 删除图标和文档
  Delete "$INSTDIR\data\icon.ico"
  RMDir /r "$INSTDIR\docs"
  RMDir "$INSTDIR\data"
  
  ; 删除快捷方式
  Delete "$SMPROGRAMS\游戏交易系统\游戏交易系统.lnk"
  Delete "$DESKTOP\游戏交易系统.lnk"
  RMDir "$SMPROGRAMS\游戏交易系统"
  
  ; 删除注册表项
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  ; 删除安装目录
  RMDir /r "$INSTDIR"
SectionEnd 