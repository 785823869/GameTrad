"""
OCR文本识别模块
提供从图像中提取文本的功能
"""
import io
import base64
import requests
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def recognize_text(image):
    """
    从图像中识别文本
    
    参数:
        image: PIL.Image对象
        
    返回:
        str: 识别的文本
    """
    try:
        # 优先使用远程API识别
        return recognize_text_api(image)
    except Exception as e:
        logger.error(f"远程OCR识别失败: {str(e)}")
        # 备用方案：本地简单识别 (可自行集成Tesseract或其他OCR库)
        return "无法识别文本，请检查网络连接或使用其他方式导入数据。"

def recognize_text_api(image):
    """
    使用远程API识别文本
    
    参数:
        image: PIL.Image对象
        
    返回:
        str: 识别的文本
    """
    # 转换图像为base64编码
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # 调用API
    url = "http://sql.didiba.uk:1224/api/ocr"  # 替换为实际的API地址
    payload = {
        "base64": img_b64,
        "options": {
            "data.format": "text"
        }
    }
    headers = {"Content-Type": "application/json"}
    
    # 发送请求
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    
    # 解析结果
    result = response.json()
    text = result.get('data', '')
    
    return text 