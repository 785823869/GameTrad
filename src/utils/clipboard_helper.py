"""
剪贴板辅助模块 - 提供跨平台的图片剪贴板操作
使用多种方法尝试获取剪贴板图片
"""

import sys
import io
import os
import traceback
from tkinter import messagebox
import platform
import logging

# 配置日志系统
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('clipboard_helper')

# 状态变量，用于跟踪可用的功能
PIL_AVAILABLE = False
PIL_IMAGE_AVAILABLE = False
IMAGEGRAB_AVAILABLE = False
WIN32_AVAILABLE = False
PYPERCLIP_AVAILABLE = False
CTYPES_AVAILABLE = False

# 检测系统信息
SYSTEM_INFO = {
    "platform": sys.platform,
    "python_version": platform.python_version(),
    "os_version": platform.version(),
    "machine": platform.machine()
}

logger.info(f"系统信息: {SYSTEM_INFO}")

# 导入所需模块，使用try-except确保即使部分模块导入失败也不会导致整个模块不可用
# 初始化时打印调试信息
logger.info("初始化剪贴板辅助模块...")

# 尝试导入PIL.Image
try:
    from PIL import Image
    PIL_IMAGE_AVAILABLE = True
    logger.info("PIL.Image 导入成功")
except ImportError as e:
    logger.error(f"PIL.Image 导入失败: {e}")

# 尝试导入PIL.ImageGrab
try:
    from PIL import ImageGrab
    IMAGEGRAB_AVAILABLE = True
    logger.info("PIL.ImageGrab 导入成功")
except ImportError as e:
    logger.error(f"PIL.ImageGrab 导入失败: {e}")

# 设置PIL是否可用的标志
PIL_AVAILABLE = PIL_IMAGE_AVAILABLE and IMAGEGRAB_AVAILABLE

# 尝试导入win32clipboard (仅在Windows平台)
if sys.platform == 'win32':
    try:
        import win32clipboard
        import win32con
        WIN32_AVAILABLE = True
        logger.info("win32clipboard 导入成功")
    except ImportError as e:
        logger.error(f"win32clipboard 导入失败: {e}")

# 尝试导入ctypes (用于低级别Windows API调用)
try:
    import ctypes
    from ctypes import windll, c_void_p, c_size_t, c_wchar_p, Structure, POINTER
    from ctypes.wintypes import BOOL, HWND, HANDLE, HGLOBAL, DWORD, LPVOID, WORD
    CTYPES_AVAILABLE = True
    logger.info("ctypes 导入成功，可以使用低级别Windows API")
except ImportError as e:
    logger.error(f"ctypes 导入失败: {e}")

# 尝试导入pyperclip作为后备方案
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
    logger.info("pyperclip 导入成功")
except ImportError as e:
    logger.error(f"pyperclip 导入失败: {e}")


def get_clipboard_image_win32():
    """
    使用win32clipboard直接访问Windows剪贴板获取图片
    
    返回:
        PIL.Image 或 None: 成功则返回PIL.Image对象，失败则返回None
    """
    if not (WIN32_AVAILABLE and PIL_IMAGE_AVAILABLE):
        logger.warning("win32clipboard或PIL.Image不可用")
        return None
        
    try:
        # 打开剪贴板
        win32clipboard.OpenClipboard()
        
        # 尝试获取位图格式的数据
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
            logger.info("检测到剪贴板中有DIB格式的图像数据")
            # 获取数据
            data = win32clipboard.GetClipboardData(win32con.CF_DIB)
            win32clipboard.CloseClipboard()
            
            # 构造BMP文件头
            offset = 14  # BMP文件头大小
            header_size = int.from_bytes(data[0:4], byteorder='little')
            file_size = len(data) + offset
            
            # 创建BMP文件头
            header = (
                b'BM' +                                 # 签名
                file_size.to_bytes(4, byteorder='little') +  # 文件大小
                b'\x00\x00\x00\x00' +                  # 保留字段
                offset.to_bytes(4, byteorder='little')      # 像素数据偏移量
            )
            
            # 拼接BMP头和数据
            bmp_data = header + data
            
            try:
                # 从内存中加载图像
                from io import BytesIO
                img = Image.open(BytesIO(bmp_data))
                logger.info(f"成功从DIB数据创建图像，尺寸: {img.size}")
                return img
            except Exception as e:
                logger.error(f"从BMP数据创建图像失败: {e}")
        else:
            # 检查其他可能的图像格式
            formats = [win32con.CF_DIB, win32con.CF_BITMAP, win32con.CF_METAFILEPICT, win32con.CF_ENHMETAFILE]
            available_formats = [fmt for fmt in formats if win32clipboard.IsClipboardFormatAvailable(fmt)]
            logger.info(f"剪贴板中没有DIB格式的图像，可用格式: {available_formats}")
            
        win32clipboard.CloseClipboard()
        return None
    except Exception as e:
        logger.error(f"win32 方法获取剪贴板图片失败: {e}")
        traceback.print_exc()
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        return None


def get_clipboard_image_pil():
    """
    使用PIL.ImageGrab获取剪贴板图片
    
    返回:
        PIL.Image 或 None: 成功则返回PIL.Image对象，失败则返回None
    """
    if not IMAGEGRAB_AVAILABLE:
        logger.warning("PIL.ImageGrab不可用")
        return None
        
    try:
        logger.info("尝试使用PIL.ImageGrab获取剪贴板图片")
        img = ImageGrab.grabclipboard()
        
        # 验证是否为图片对象
        if img is not None and isinstance(img, Image.Image):
            logger.info(f"成功获取到图片，尺寸: {img.size}")
            return img
        elif isinstance(img, list) and len(img) > 0 and os.path.isfile(img[0]):
            # 如果是文件路径列表，尝试加载第一个文件
            try:
                logger.info(f"尝试从剪贴板文件路径加载图片: {img[0]}")
                image = Image.open(img[0])
                logger.info(f"成功从文件加载图片，尺寸: {image.size}")
                return image
            except Exception as e:
                logger.error(f"从文件加载图片失败: {e}")
        else:
            logger.warning(f"PIL.ImageGrab返回的不是图片对象: {type(img)}")
                
        return None
    except Exception as e:
        logger.error(f"PIL方法获取剪贴板图片失败: {e}")
        traceback.print_exc()
        return None


# 添加一个使用ctypes直接调用Windows API的方法
def get_clipboard_image_ctypes():
    """
    使用ctypes直接调用Windows API获取剪贴板图片
    
    返回:
        PIL.Image 或 None: 成功则返回PIL.Image对象，失败则返回None
    """
    if not (CTYPES_AVAILABLE and PIL_IMAGE_AVAILABLE) or sys.platform != 'win32':
        logger.warning("ctypes或PIL.Image不可用，或者不是Windows平台")
        return None
    
    try:
        # 定义常量
        CF_BITMAP = 2
        CF_DIB = 8
        CF_DIBV5 = 17
        GMEM_MOVEABLE = 0x0002
        
        # 尝试打开剪贴板
        if not windll.user32.OpenClipboard(None):
            logger.error("无法打开剪贴板")
            return None
        
        logger.info("尝试使用ctypes访问剪贴板")
        
        # 检查是否有DIB格式数据
        if windll.user32.IsClipboardFormatAvailable(CF_DIB):
            logger.info("检测到DIB格式数据")
            try:
                # 获取剪贴板数据句柄
                handle = windll.user32.GetClipboardData(CF_DIB)
                if not handle:
                    logger.error("无法获取剪贴板数据句柄")
                    windll.user32.CloseClipboard()
                    return None
                
                # 锁定内存以访问数据
                data_ptr = windll.kernel32.GlobalLock(handle)
                if not data_ptr:
                    logger.error("无法锁定内存")
                    windll.user32.CloseClipboard()
                    return None
                
                # 获取数据大小
                size = windll.kernel32.GlobalSize(handle)
                logger.info(f"剪贴板数据大小: {size}字节")
                
                # 复制数据
                buffer = ctypes.create_string_buffer(size)
                ctypes.memmove(buffer, data_ptr, size)
                
                # 解锁内存
                windll.kernel32.GlobalUnlock(handle)
                windll.user32.CloseClipboard()
                
                # 构造BMP文件
                offset = 14  # BMP文件头大小
                
                # 从DIB数据中读取信息头大小
                header_size = int.from_bytes(buffer.raw[0:4], byteorder='little')
                logger.info(f"DIB信息头大小: {header_size}字节")
                
                # 计算文件大小
                file_size = size + offset
                
                # 创建BMP文件头
                header = (
                    b'BM' +                                # 签名
                    file_size.to_bytes(4, byteorder='little') +  # 文件大小
                    b'\x00\x00\x00\x00' +                 # 保留字段
                    offset.to_bytes(4, byteorder='little')     # 像素数据偏移量
                )
                
                # 拼接完整的BMP文件数据
                bmp_data = header + buffer.raw
                
                # 从内存中加载图像
                from io import BytesIO
                img = Image.open(BytesIO(bmp_data))
                logger.info(f"成功通过ctypes从DIB数据创建图像，尺寸: {img.size}")
                return img
                
            except Exception as e:
                logger.error(f"通过ctypes处理DIB数据时出错: {e}")
                traceback.print_exc()
                windll.user32.CloseClipboard()
                return None
        else:
            logger.warning("剪贴板中没有DIB格式的图像数据")
            windll.user32.CloseClipboard()
            return None
            
    except Exception as e:
        logger.error(f"ctypes方法获取剪贴板图片失败: {e}")
        traceback.print_exc()
        try:
            windll.user32.CloseClipboard()
        except:
            pass
        return None


def get_clipboard_image_temp_file():
    """
    通过临时文件获取剪贴板图片 - 作为最后的备选方案
    
    返回:
        PIL.Image 或 None: 成功则返回PIL.Image对象，失败则返回None
    """
    if not PIL_IMAGE_AVAILABLE or sys.platform != 'win32':
        logger.warning("PIL.Image不可用，或者不是Windows平台")
        return None
        
    try:
        import tempfile
        import subprocess
        
        logger.info("尝试通过临时文件获取剪贴板图片")
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_filename = temp_file.name
        temp_file.close()
        
        # 使用PowerShell命令保存剪贴板图片到临时文件
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        if ($([System.Windows.Forms.Clipboard]::ContainsImage())) {{
            $image = [System.Windows.Forms.Clipboard]::GetImage()
            $image.Save('{temp_filename}', [System.Drawing.Imaging.ImageFormat]::Png)
            Write-Output "SUCCESS"
        }} else {{
            Write-Output "NO_IMAGE"
        }}
        '''
        
        # 执行PowerShell脚本
        logger.info("执行PowerShell脚本获取剪贴板图片")
        result = subprocess.run(['powershell', '-Command', ps_script], 
                               capture_output=True, text=True)
        
        if "SUCCESS" in result.stdout:
            # 从临时文件加载图片
            logger.info(f"尝试从临时文件加载图片: {temp_filename}")
            img = Image.open(temp_filename)
            logger.info(f"成功从临时文件加载图片，尺寸: {img.size}")
            
            # 删除临时文件
            try:
                os.remove(temp_filename)
            except:
                pass
                
            return img
        else:
            logger.warning("PowerShell脚本未能获取到剪贴板图片")
            logger.debug(f"PowerShell输出: {result.stdout}")
            logger.debug(f"PowerShell错误: {result.stderr}")
            
            # 删除临时文件
            try:
                os.remove(temp_filename)
            except:
                pass
                
            return None
    except Exception as e:
        logger.error(f"通过临时文件获取剪贴板图片失败: {e}")
        traceback.print_exc()
        return None


def get_clipboard_image():
    """
    尝试多种方法从剪贴板获取图片，按优先级尝试
    
    返回:
        PIL.Image 或 None: 成功则返回PIL.Image对象，失败则返回None
    """
    # 尝试各种方法，按优先级排序
    methods = [
        ("PIL", get_clipboard_image_pil),
        ("win32", get_clipboard_image_win32),
        ("ctypes", get_clipboard_image_ctypes),
        ("temp_file", get_clipboard_image_temp_file)
    ]
    
    for name, method in methods:
        try:
            logger.info(f"尝试使用{name}方法获取剪贴板图片...")
            img = method()
            if img is not None:
                logger.info(f"{name}方法成功获取到图片")
                return img
        except Exception as e:
            logger.error(f"{name}方法出现异常: {e}")
            traceback.print_exc()
    
    logger.warning("所有方法都未能获取到剪贴板图片")
    return None


def diagnose_clipboard():
    """
    诊断剪贴板功能并返回详细状态报告
    
    返回:
        dict: 包含诊断信息的字典
    """
    report = {
        "system_info": SYSTEM_INFO,
        "modules": {
            "PIL_IMAGE_AVAILABLE": PIL_IMAGE_AVAILABLE,
            "IMAGEGRAB_AVAILABLE": IMAGEGRAB_AVAILABLE,
            "WIN32_AVAILABLE": WIN32_AVAILABLE,
            "CTYPES_AVAILABLE": CTYPES_AVAILABLE,
            "PYPERCLIP_AVAILABLE": PYPERCLIP_AVAILABLE
        },
        "clipboard_state": {},
        "possible_issues": [],
        "recommendations": []
    }
    
    # 检查剪贴板状态
    if sys.platform == 'win32' and WIN32_AVAILABLE:
        try:
            win32clipboard.OpenClipboard()
            
            # 检查剪贴板格式
            formats = {
                win32con.CF_TEXT: "文本",
                win32con.CF_UNICODETEXT: "Unicode文本",
                win32con.CF_DIB: "DIB图像",
                win32con.CF_BITMAP: "位图",
                win32con.CF_METAFILEPICT: "图元文件图片",
                win32con.CF_ENHMETAFILE: "增强型图元文件"
            }
            
            available_formats = []
            for fmt_id, fmt_name in formats.items():
                if win32clipboard.IsClipboardFormatAvailable(fmt_id):
                    available_formats.append(fmt_name)
            
            report["clipboard_state"]["available_formats"] = available_formats
            win32clipboard.CloseClipboard()
        except Exception as e:
            report["clipboard_state"]["error"] = str(e)
    
    # 分析可能的问题
    if not PIL_IMAGE_AVAILABLE:
        report["possible_issues"].append("PIL Image模块不可用")
        report["recommendations"].append("执行 'pip install pillow' 安装PIL库")
    
    if not IMAGEGRAB_AVAILABLE:
        report["possible_issues"].append("PIL ImageGrab模块不可用")
        if sys.platform == 'win32':
            report["recommendations"].append("确认Pillow库安装正确，或尝试重新安装: 'pip uninstall pillow' 然后 'pip install pillow'")
        else:
            report["recommendations"].append("ImageGrab模块通常仅在Windows上工作，Linux和macOS可能需要使用其他方法")
    
    if sys.platform == 'win32' and not WIN32_AVAILABLE:
        report["possible_issues"].append("win32clipboard模块不可用")
        report["recommendations"].append("执行 'pip install pywin32' 安装pywin32库")
    
    # 基于Python版本的建议
    py_version = tuple(map(int, platform.python_version().split('.')))
    if py_version >= (3, 12, 0):
        report["possible_issues"].append(f"Python {platform.python_version()} 是较新版本，可能与某些库不完全兼容")
        report["recommendations"].append("考虑使用Python 3.11或更早的稳定版本")
    
    # 检查剪贴板内容
    has_image = False
    for method_name in ["PIL", "win32", "ctypes", "temp_file"]:
        try:
            if method_name == "PIL" and get_clipboard_image_pil() is not None:
                has_image = True
                report["clipboard_state"]["method_works"] = method_name
                break
            elif method_name == "win32" and get_clipboard_image_win32() is not None:
                has_image = True
                report["clipboard_state"]["method_works"] = method_name
                break
            elif method_name == "ctypes" and get_clipboard_image_ctypes() is not None:
                has_image = True
                report["clipboard_state"]["method_works"] = method_name
                break
            elif method_name == "temp_file" and get_clipboard_image_temp_file() is not None:
                has_image = True
                report["clipboard_state"]["method_works"] = method_name
                break
        except:
            pass
    
    report["clipboard_state"]["has_image"] = has_image
    
    if not has_image:
        report["possible_issues"].append("剪贴板中没有图片，或无法访问剪贴板图片")
        report["recommendations"].append("确认剪贴板中有图片，可以先尝试在图片编辑器中复制图片")
    
    return report


def show_clipboard_error():
    """显示剪贴板操作错误的通用消息"""
    # 运行诊断
    report = diagnose_clipboard()
    
    # 生成详细的错误信息
    error_details = ""
    
    # 添加模块状态信息
    if not PIL_IMAGE_AVAILABLE:
        error_details += "• PIL Image模块不可用\n"
    if not IMAGEGRAB_AVAILABLE:
        error_details += "• PIL ImageGrab模块不可用\n"
    if sys.platform == 'win32' and not WIN32_AVAILABLE:
        error_details += "• win32clipboard模块不可用\n"
    
    # 添加剪贴板状态信息
    if "available_formats" in report["clipboard_state"]:
        if not report["clipboard_state"]["available_formats"]:
            error_details += "• 剪贴板为空或无法访问剪贴板\n"
        elif "DIB图像" not in report["clipboard_state"]["available_formats"] and "位图" not in report["clipboard_state"]["available_formats"]:
            error_details += f"• 剪贴板内容类型: {', '.join(report['clipboard_state']['available_formats'])}\n"
            error_details += "• 剪贴板中没有图片数据\n"
    
    # 添加系统信息
    error_details += f"• 系统: {SYSTEM_INFO['platform']} {SYSTEM_INFO['os_version']}\n"
    error_details += f"• Python版本: {SYSTEM_INFO['python_version']}\n"
    
    # 添加建议
    if report["recommendations"]:
        error_details += "\n可能的解决方案:\n"
        for i, rec in enumerate(report["recommendations"], 1):
            error_details += f"{i}. {rec}\n"
    
    # 如果没有特定的错误原因，提供通用提示
    if not error_details:
        error_details = "• 无法访问剪贴板或剪贴板中没有图片\n• 请检查系统权限或使用'上传图片'替代"
    
    # 显示错误消息
    messagebox.showwarning(
        "剪贴板图片功能受限", 
        f"无法从剪贴板获取图片，详细信息:\n\n{error_details}\n\n请使用'上传图片'按钮代替。"
    )


def is_clipboard_image_available():
    """
    检查剪贴板中是否有图片
    
    返回:
        bool: 如果剪贴板中有图片返回True，否则返回False
    """
    try:
        return get_clipboard_image() is not None
    except Exception:
        return False


# 初始化时打印组件状态
logger.info(f"剪贴板辅助模块状态: PIL_AVAILABLE={PIL_AVAILABLE}, IMAGEGRAB_AVAILABLE={IMAGEGRAB_AVAILABLE}, WIN32_AVAILABLE={WIN32_AVAILABLE}, CTYPES_AVAILABLE={CTYPES_AVAILABLE}") 