; UTF-8 缂栫爜澹版槑
Unicode true

; 瀹夎绋嬪簭鍒濆瀹氫箟甯搁噺
!define PRODUCT_NAME "娓告垙浜ゆ槗绯荤粺"
!define PRODUCT_VERSION "1.0"
!define PRODUCT_PUBLISHER "涓夊彧灏忕尓"
!define PRODUCT_WEB_SITE "http://www.example.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\GameTrad.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor lzma

; MUI 鐜颁唬鐣岄潰瀹氫箟
!include "MUI2.nsh"

; MUI 棰勫畾涔?
!define MUI_ABORTWARNING
!define MUI_ICON "data\icon.ico"
!define MUI_UNICON "data\icon.ico"

; 娆㈣繋椤甸潰
!insertmacro MUI_PAGE_WELCOME
; 璁稿彲鍗忚椤甸潰
!insertmacro MUI_PAGE_LICENSE "LICENSE"
; 瀹夎鐩綍閫夋嫨椤甸潰
!insertmacro MUI_PAGE_DIRECTORY
; 瀹夎杩囩▼椤甸潰
!insertmacro MUI_PAGE_INSTFILES
; 瀹夎瀹屾垚椤甸潰
!define MUI_FINISHPAGE_RUN "$INSTDIR\GameTrad.exe"
!insertmacro MUI_PAGE_FINISH

; 鍗歌浇绋嬪簭椤甸潰
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 瀹夎鐣岄潰鍖呭惈鐨勮瑷€璁剧疆
!insertmacro MUI_LANGUAGE "SimpChinese"

; 瀹夎绋嬪簭鐗堟湰鍙?
VIProductVersion "1.0.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "娓告垙浜ゆ槗绯荤粺"
VIAddVersionKey /LANG=2052 "Comments" "娓告垙浜ゆ槗绠＄悊绯荤粺"
VIAddVersionKey /LANG=2052 "CompanyName" "涓夊彧灏忕尓"
VIAddVersionKey /LANG=2052 "LegalTrademarks" ""
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (C) 2024"
VIAddVersionKey /LANG=2052 "FileDescription" "娓告垙浜ゆ槗绯荤粺瀹夎绋嬪簭"
VIAddVersionKey /LANG=2052 "FileVersion" "1.0.0.0"

; 瀹夎绋嬪簭鍚嶇О
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "GameTrad_Setup.exe"
InstallDir "$PROGRAMFILES\GameTrad"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  ; 复制主程序文件
  File "dist\GameTrad.exe"
  
  ; 鍒涘缓寮€濮嬭彍鍗曞揩鎹锋柟寮?
  CreateDirectory "$SMPROGRAMS\GameTrad"
  CreateShortCut "$SMPROGRAMS\GameTrad\GameTrad.lnk" "$INSTDIR\GameTrad.exe"
  CreateShortCut "$DESKTOP\GameTrad.lnk" "$INSTDIR\GameTrad.exe"
  
  ; 鍐欏叆鍗歌浇淇℃伅
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\GameTrad.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\GameTrad.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Section Uninstall
  ; 鍒犻櫎绋嬪簭鏂囦欢
  Delete "$INSTDIR\GameTrad.exe"
  Delete "$INSTDIR\uninst.exe"
  
  ; 鍒犻櫎蹇嵎鏂瑰紡
  Delete "$SMPROGRAMS\GameTrad\GameTrad.lnk"
  Delete "$DESKTOP\GameTrad.lnk"
  RMDir "$SMPROGRAMS\GameTrad"
  
  ; 鍒犻櫎娉ㄥ唽琛ㄩ」
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  ; 鍒犻櫎瀹夎鐩綍
  RMDir /r "$INSTDIR"
SectionEnd 
