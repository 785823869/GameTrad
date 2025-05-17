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
    
    def check_for_updates(self):
        """
        检查是否有可用的更新
        
        Returns:
            tuple: (有更新, 更新信息字典)
        """
        try:
            # 尝试从GitHub API获取最新版本信息
            try:
                print(f"正在请求更新信息: {self.update_url}")
                response = requests.get(self.update_url, timeout=10)
                response.raise_for_status()
                
                # 解析GitHub API响应
                github_data = response.json()
                print(f"获取到GitHub响应: {github_data}")
                
                # 提取版本号（移除v前缀如果存在）
                version = github_data.get("tag_name", "")
                if version.startswith("v"):
                    version = version[1:]
                
                # 获取下载URL（使用第一个asset或备用URL）
                assets = github_data.get("assets", [])
                if assets and len(assets) > 0:
                    self.download_url = assets[0].get("browser_download_url")
                    print(f"从GitHub资源获取下载URL: {self.download_url}")
                else:
                    # 如果没有资源，使用直接下载URL
                    self.download_url = self.direct_download_url
                    print(f"使用备用下载URL: {self.download_url}")
                
                self.latest_version = version or "1.0.1"  # 默认版本
                self.release_notes = github_data.get("body", "")
                self.publish_date = github_data.get("published_at", "").split("T")[0]
                self.is_required = False  # GitHub API没有必需更新的概念
                
            except Exception as e:
                print(f"GitHub API请求失败: {e}，使用备用方式")
                
                # 备用方式：使用硬编码的下载URL和版本信息
                self.download_url = self.direct_download_url
                print(f"使用硬编码下载URL: {self.download_url}")
                
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
                    else:
                        # 如果无法从文件名提取，则假设为下一个版本
                        current_parts = self.current_version.split('.')
                        next_minor = int(current_parts[2]) + 1
                        self.latest_version = f"{current_parts[0]}.{current_parts[1]}.{next_minor}"
                except:
                    # 如果解析失败，则假设为下一个小版本
                    current_parts = self.current_version.split('.')
                    next_minor = int(current_parts[2]) + 1
                    self.latest_version = f"{current_parts[0]}.{current_parts[1]}.{next_minor}"
                
                self.release_notes = "此版本包含功能改进和错误修复。"
                self.publish_date = "未知"
                self.is_required = False
            
            has_update = self.compare_versions(self.latest_version, self.current_version) > 0
            print(f"版本比较: 当前={self.current_version}, 最新={self.latest_version}, 有更新={has_update}")
            
            # 确保下载URL已设置
            if has_update and not self.download_url:
                self.download_url = self.direct_download_url
                print(f"未找到下载URL，使用默认URL: {self.download_url}")
            
            return has_update, {
                "version": self.latest_version,
                "download_url": self.download_url,
                "release_notes": self.release_notes,
                "required": self.is_required,
                "publish_date": self.publish_date
            }
        except Exception as e:
            print(f"检查更新时出错: {e}")
            return False, {"error": str(e)}
    
    def download_update(self, progress_callback=None, error_callback=None, complete_callback=None):
        """
        下载更新文件
        
        Args:
            progress_callback: 进度回调函数，参数为进度百分比(0-100)
            error_callback: 错误回调函数，参数为错误信息
            complete_callback: 完成回调函数，参数为下载的文件路径
        """
        if not self.download_url:
            if error_callback:
                error_callback("没有可用的下载链接")
            return
        
        self._progress_callback = progress_callback
        self._error_callback = error_callback
        self._complete_callback = complete_callback
        
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
            
            # 创建临时目录用于下载
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, filename)
            
            # 下载文件
            with requests.get(self.download_url, stream=True, timeout=60) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024  # 1 KB
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
            
            # 下载完成，调用回调函数
            if self._complete_callback:
                self._complete_callback(file_path)
                
        except Exception as e:
            print(f"下载更新时出错: {e}")
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
            if sys.platform == 'win32':
                # Windows系统使用subprocess启动安装程序
                subprocess.Popen([file_path], shell=True)
                return True
            else:
                # 其他系统可能需要不同的安装方法
                return False
        except Exception as e:
            print(f"启动安装程序时出错: {e}")
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
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
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
        except Exception:
            # 如果版本号格式不正确，返回0（相等）
            return 0 