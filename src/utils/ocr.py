"""
通用OCR文本识别模块
提供图像文字识别功能，使用外部API服务
"""
import io
import base64
import requests
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)

def recognize_text(img):
    """
    使用OCR API识别图片中的文本
    
    参数:
        img: PIL.Image对象，要识别的图片
        
    返回:
        str: 识别出的文本，如果识别失败则返回空字符串
    
    异常:
        可能引发请求相关的异常，如ConnectionError, Timeout等
    """
    try:
        # 转换图片为base64编码
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # 发送API请求
        url = "http://sql.didiba.uk:1224/api/ocr"
        payload = {
            "base64": img_b64,
            "options": {
                "data.format": "text"
            }
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info("正在发送OCR识别请求...")
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        
        ocr_result = resp.json()
        text = ocr_result.get('data', '')
        
        if not text:
            logger.warning("OCR识别返回空文本")
        else:
            logger.info(f"成功识别文本，长度:{len(text)}")
            
        return text
        
    except requests.exceptions.RequestException as e:
        logger.error(f"OCR API请求失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"OCR识别过程中发生未知错误: {str(e)}")
        raise 