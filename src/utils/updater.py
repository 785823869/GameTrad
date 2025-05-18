"""
在线更新模块 - 处理应用程序的版本检查、下载和安装更新
"""
import os
import sys
import json
import tempfile
import threading
import subprocess
import requests
from tkinter import messagebox
from urllib.parse import urlparse
from src import __version__

# 导入模块内部使用的日志和路径工具
try:
    from src.utils.logger import get_module_logger
    from src.utils.path_resolver import get_temp_dir, is_frozen, get_user_data_dir
    
    logger = get_module_logger(__name__)
except ImportError:
    # 如果日志系统未初始化，使用简单的控制台输出
    import logging
    logger = logging.getLogger(__name__)
    
    def is_frozen():
        return getattr(sys, 'frozen', False)
    
    def get_temp_dir():
        temp_dir = os.path.join(tempfile.gettempdir(), "GameTrad")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    def get_user_data_dir():
        try:
            import appdirs
            user_data_dir = appdirs.user_data_dir("GameTrad")
            os.makedirs(user_data_dir, exist_ok=True)
            return user_data_dir
        except:
            temp_dir = os.path.join(tempfile.gettempdir(), "GameTrad", "data")
            os.makedirs(temp_dir, exist_ok=True)
            return temp_dir

class AppUpdater:
    """应用程序更新器类"""
    
    def __init__(self, update_url=None):
        """
        初始化更新器
        
        Args:
            update_url: 检查更新的API URL，如果为None则使用默认GitHub地址
        """
        self.update_url = update_url or "https://api.github.com/repos/785823869/GameTrad/releases/latest"
        self.direct_download_url = "https://github.com/785823869/GameTrad/releases/download/Game/GameTrad_Setup.exe"
        self.current_version = __version__
        self.latest_version = None
        self.download_url = None
        self.release_notes = None
        self.is_required = False
        self.publish_date = None
        self._download_thread = None
        self._progress_callback = None
        self._error_callback = None
        self._complete_callback = None
        
        # 记录初始化信息
        logger.info(f"更新器初始化: 当前版本={self.current_version}, API={self.update_url}")
        logger.debug(f"直接下载URL: {self.direct_download_url}")
    
    def check_for_updates(self):
        """
        检查是否有可用的更新
        
        Returns:
            tuple: (有更新, 更新信息字典)
        """
        try:
            # 尝试从GitHub API获取最新版本信息
            try:
                logger.info(f"正在请求更新信息: {self.update_url}")
                
                # 增加超时和用户代理
                headers = {
                    'User-Agent': f'GameTrad/{self.current_version} UpdateChecker'
                }
                response = requests.get(self.update_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # 解析GitHub API响应
                github_data = response.json()
                logger.debug(f"获取到GitHub响应: {github_data.get('tag_name', 'Unknown')}")
                
                # 提取版本号（移除v前缀如果存在）
                version = github_data.get("tag_name", "")
                if version.startswith("v"):
                    version = version[1:]
                
                # 获取下载URL（使用第一个asset或备用URL）
                assets = github_data.get("assets", [])
                if assets and len(assets) > 0:
                    self.download_url = assets[0].get("browser_download_url")
                    logger.info(f"从GitHub资源获取下载URL: {self.download_url}")
                else:
                    # 如果没有资源，使用直接下载URL
                    self.download_url = self.direct_download_url
                    logger.info(f"使用备用下载URL: {self.download_url}")
                
                self.latest_version = version or "1.0.1"  # 默认版本
                self.release_notes = github_data.get("body", "")
                self.publish_date = github_data.get("published_at", "").split("T")[0]
                self.is_required = False  # GitHub API没有必需更新的概念
                
                logger.info(f"获取到版本信息: 最新={self.latest_version}, 发布日期={self.publish_date}")
                
            except Exception as e:
                logger.warning(f"GitHub API请求失败: {e}，使用备用方式")
                
                # 备用方式：尝试从注册表或配置文件获取更新URL
                try:
                    # 在Windows系统上尝试从注册表获取
                    if sys.platform == 'win32':
                        import winreg
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\GameTrad") as key:
                            reg_url = winreg.QueryValueEx(key, "UpdateURL")[0]
                            if reg_url:
                                self.download_url = reg_url
                                logger.info(f"从注册表获取更新URL: {self.download_url}")
                except:
                    logger.debug("无法从注册表获取更新URL")
                
                # 如果注册表获取失败，使用硬编码的下载URL
                if not self.download_url:
                    self.download_url = self.direct_download_url
                    logger.info(f"使用硬编码下载URL: {self.download_url}")
                
                # 尝试从文件名解析版本
                try:
                    # 解析URL获取文件名
                    parsed_url = urlparse(self.download_url)
                    filename = os.path.basename(parsed_url.path)
                    
                    # 尝试从文件名中提取版本号
                    import re
                    version_match = re.search(r'(\d+\.\d+\.\d+)', filename)
                    if version_match:
                        self.latest_version = version_match.group(1)
                        logger.info(f"从文件名提取版本号: {self.latest_version}")
                    else:
                        # 如果无法从文件名提取，则假设为下一个版本
                        current_parts = self.current_version.split('.')
                        next_minor = int(current_parts[2]) + 1
                        self.latest_version = f"{current_parts[0]}.{current_parts[1]}.{next_minor}"
                        logger.info(f"假设下一个版本号: {self.latest_version}")
                except Exception as e:
                    # 如果解析失败，则假设为下一个小版本
                    logger.warning(f"版本号解析失败: {e}")
                    current_parts = self.current_version.split('.')
                    next_minor = int(current_parts[2]) + 1
                    self.latest_version = f"{current_parts[0]}.{current_parts[1]}.{next_minor}"
                    logger.info(f"假设下一个版本号: {self.latest_version}")
                
                self.release_notes = "此版本包含功能改进和错误修复。"
                self.publish_date = "未知"
                self.is_required = False
            
            # 比较版本
            compare_result = self.compare_versions(self.latest_version, self.current_version)
            has_update = compare_result > 0
            
            logger.info(f"版本比较结果: 当前={self.current_version}, 最新={self.latest_version}, " +
                       f"比较结果={compare_result}, 有更新={has_update}")
            
            # 确保下载URL已设置
            if has_update and not self.download_url:
                self.download_url = self.direct_download_url
                logger.warning(f"未找到下载URL，使用默认URL: {self.download_url}")
            
            return has_update, {
                "version": self.latest_version,
                "download_url": self.download_url,
                "release_notes": self.release_notes,
                "required": self.is_required,
                "publish_date": self.publish_date,
                "current_version": self.current_version,
                "environment": "打包环境" if is_frozen() else "开发环境"
            }
        except Exception as e:
            logger.error(f"检查更新时出错: {e}", exc_info=True)
            return False, {
                "error": str(e),
                "current_version": self.current_version,
                "environment": "打包环境" if is_frozen() else "开发环境"
            }
    
    def download_update(self, progress_callback=None, error_callback=None, complete_callback=None):
        """
        下载更新文件
        
        Args:
            progress_callback: 进度回调函数，参数为进度百分比(0-100)
            error_callback: 错误回调函数，参数为错误信息
            complete_callback: 完成回调函数，参数为下载的文件路径
        """
        if not self.download_url:
            error_msg = "没有可用的下载链接"
            logger.error(error_msg)
            if error_callback:
                error_callback(error_msg)
            return
        
        self._progress_callback = progress_callback
        self._error_callback = error_callback
        self._complete_callback = complete_callback
        
        logger.info(f"开始下载更新: {self.download_url}")
        
        # 在后台线程中下载
        self._download_thread = threading.Thread(target=self._download_thread_func)
        self._download_thread.daemon = True
        self._download_thread.start()
    
    def _download_thread_func(self):
        """下载线程函数"""
        try:
            # 从URL中提取文件名
            parsed_url = urlparse(self.download_url)
            filename = os.path.basename(parsed_url.path)
            
            # 如果文件名为空，使用默认名称
            if not filename:
                filename = f"GameTrad_Setup_{self.latest_version}.exe"
            
            # 使用应用数据目录或临时目录下载
            try:
                download_dir = os.path.join(get_user_data_dir(), "downloads")
                os.makedirs(download_dir, exist_ok=True)
            except:
                download_dir = get_temp_dir()
            
            file_path = os.path.join(download_dir, filename)
            logger.info(f"下载目标路径: {file_path}")
            
            # 添加用户代理和重试机制
            headers = {
                'User-Agent': f'GameTrad/{self.current_version} Updater'
            }
            
            retry_count = 3
            retry_wait = 2  # 秒
            
            for attempt in range(retry_count):
                try:
                    # 下载文件
                    with requests.get(self.download_url, stream=True, timeout=60, headers=headers) as response:
                        response.raise_for_status()
                        total_size = int(response.headers.get('content-length', 0))
                        logger.info(f"开始下载文件: 大小={total_size} 字节")
                        
                        block_size = 8192  # 8 KB
                        downloaded = 0
                        
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=block_size):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    
                                    # 计算进度并回调
                                    if total_size > 0 and self._progress_callback:
                                        progress = int((downloaded / total_size) * 100)
                                        self._progress_callback(progress)
                                        
                                        # 每10%记录一次进度
                                        if progress % 10 == 0 and progress > 0:
                                            logger.debug(f"下载进度: {progress}% ({downloaded}/{total_size} 字节)")
                    
                    # 下载成功，跳出重试循环
                    logger.info(f"下载完成: {file_path}")
                    break
                    
                except Exception as e:
                    # 如果不是最后一次尝试则重试
                    if attempt < retry_count - 1:
                        logger.warning(f"下载失败，将在{retry_wait}秒后重试: {e}")
                        import time
                        time.sleep(retry_wait)
                    else:
                        # 最后一次尝试也失败，抛出异常
                        raise
            
            # 验证下载的文件
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                raise Exception("下载文件为空或不存在")
            
            # 检查是否为有效的可执行文件（仅适用于Windows）
            if sys.platform == 'win32' and not file_path.endswith('.exe'):
                raise Exception("下载的文件不是有效的Windows可执行文件")
            
            # 下载完成，调用回调函数
            logger.info("下载成功，准备安装")
            if self._complete_callback:
                self._complete_callback(file_path)
                
        except Exception as e:
            error_msg = f"下载更新时出错: {e}"
            logger.error(error_msg, exc_info=True)
            if self._error_callback:
                self._error_callback(str(e))
    
    def install_update(self, file_path):
        """
        安装更新
        
        Args:
            file_path: 安装文件路径
            
        Returns:
            bool: 安装是否成功启动
        """
        try:
            logger.info(f"准备安装更新: {file_path}")
            
            # 验证文件存在且有效
            if not os.path.exists(file_path):
                logger.error(f"安装文件不存在: {file_path}")
                return False
            
            if sys.platform == 'win32':
                # Windows系统使用subprocess启动安装程序
                # 使用runas提权运行安装程序
                try:
                    # 尝试以管理员身份运行
                    logger.info("尝试以管理员身份启动安装程序")
                    from win32com.shell import shellcon, shell
                    shell.ShellExecuteEx(
                        lpVerb='runas', 
                        lpFile=file_path,
                        nShow=1
                    )
                    logger.info("成功启动安装程序")
                    return True
                except:
                    # 如果ShellExecuteEx失败，使用普通方式启动
                    logger.warning("管理员权限启动失败，尝试普通方式启动")
                    subprocess.Popen([file_path], shell=True)
                    logger.info("成功启动安装程序(普通权限)")
                    return True
            else:
                # 其他系统可能需要不同的安装方法
                logger.warning(f"不支持的操作系统: {sys.platform}，无法自动安装")
                return False
        except Exception as e:
            logger.error(f"启动安装程序时出错: {e}", exc_info=True)
            return False
    
    @staticmethod
    def compare_versions(version1, version2):
        """
        比较两个版本号
        
        Args:
            version1: 第一个版本号
            version2: 第二个版本号
            
        Returns:
            int: 如果version1 > version2返回1，相等返回0，小于返回-1
        """
        try:
            # 确保版本号格式正确
            v1_parts = version1.strip().split('.')
            v2_parts = version2.strip().split('.')
            
            # 转换为整数进行比较
            try:
                v1_parts = [int(x) for x in v1_parts]
                v2_parts = [int(x) for x in v2_parts]
            except ValueError:
                # 如果转换失败，尝试字符串比较
                logger.warning(f"版本号无法转换为整数，将使用字符串比较: {version1} vs {version2}")
                return (version1 > version2) - (version1 < version2)
            
            # 补齐版本号长度
            while len(v1_parts) < len(v2_parts):
                v1_parts.append(0)
            while len(v2_parts) < len(v1_parts):
                v2_parts.append(0)
            
            # 比较各部分
            for i in range(len(v1_parts)):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1
            
            return 0
        except Exception as e:
            logger.error(f"比较版本号时出错: {e}", exc_info=True)
            # 如果版本号格式不正确，返回0（相等）
            return 0 