"""
OCR工具类 - 处理OCR识别相关功能
"""
import re
import io
import base64
import json
import requests
from PyQt6.QtWidgets import QMessageBox


class OCRUtils:
    """OCR工具类，提供OCR文本解析功能"""
    
    @staticmethod
    def send_ocr_request(image, timeout=20):
        """
        发送OCR请求到API服务器
        
        Args:
            image: PIL图像对象
            timeout: 超时时间(秒)
            
        Returns:
            识别的文本内容，失败返回None
        """
        try:
            buf = io.BytesIO()
            image.save(buf, format='PNG')
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            url = "http://sql.didiba.uk:1224/api/ocr"
            payload = {
                "base64": img_b64,
                "options": {
                    "data.format": "text"
                }
            }
            headers = {"Content-Type": "application/json"}
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            ocr_result = resp.json()
            return ocr_result.get('data')
        except Exception as e:
            QMessageBox.critical(None, "OCR识别错误", f"OCR识别请求失败: {str(e)}")
            return None
    
    @staticmethod
    def parse_stock_in_ocr_text(text, dict_items=None):
        """
        解析入库OCR文本，提取入库相关信息
        
        Args:
            text: OCR识别的文本内容
            dict_items: 物品字典，用于匹配物品名
            
        Returns:
            解析后的入库数据字典，失败返回None
        """
        try:
            lines = text.strip().split('\n')
            item_name = None
            quantity = None
            cost = None
            
            for line in lines:
                if '品名' in line or '物品' in line:
                    match = re.search(r'[：:]\s*(.+)$', line)
                    if match:
                        item_name = match.group(1).strip()
                elif '数量' in line:
                    match = re.search(r'[：:]\s*(\d+)', line)
                    if match:
                        quantity = int(match.group(1))
                elif '价格' in line or '金额' in line or '花费' in line:
                    match = re.search(r'[：:]\s*(\d+)', line)
                    if match:
                        cost = float(match.group(1))
            
            if item_name and quantity and cost:
                return {
                    'item_name': item_name,
                    'quantity': quantity,
                    'cost': cost
                }
            return None
        except Exception as e:
            QMessageBox.critical(None, "解析错误", f"入库数据解析失败: {str(e)}")
            return None
    
    @staticmethod
    def parse_stock_out_ocr_text(text, dict_items=None):
        """
        解析出库OCR文本，提取出库相关信息
        
        Args:
            text: OCR识别的文本内容
            dict_items: 物品字典，用于匹配物品名
            
        Returns:
            解析后的出库数据字典，失败返回None
        """
        try:
            lines = text.strip().split('\n')
            item_name = None
            quantity = None
            unit_price = None
            fee = 0
            
            for line in lines:
                if '品名' in line or '物品' in line:
                    match = re.search(r'[：:]\s*(.+)$', line)
                    if match:
                        item_name = match.group(1).strip()
                elif '数量' in line:
                    match = re.search(r'[：:]\s*(\d+)', line)
                    if match:
                        quantity = int(match.group(1))
                elif '单价' in line or '价格' in line:
                    match = re.search(r'[：:]\s*(\d+)', line)
                    if match:
                        unit_price = float(match.group(1))
                elif '手续费' in line or '费用' in line:
                    match = re.search(r'[：:]\s*(\d+)', line)
                    if match:
                        fee = float(match.group(1))
            
            if item_name and quantity and unit_price:
                return {
                    'item_name': item_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'fee': fee
                }
            return None
        except Exception as e:
            QMessageBox.critical(None, "解析错误", f"出库数据解析失败: {str(e)}")
            return None
    
    @staticmethod
    def parse_monitor_ocr_text(text, dict_items=None):
        """
        解析交易监控OCR文本，提取监控相关信息
        
        Args:
            text: OCR识别的文本内容
            dict_items: 物品字典，用于匹配物品名(必须提供)
            
        Returns:
            解析后的监控数据列表，失败返回空列表
        """
        try:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            # 检查物品字典是否可用
            if not dict_items:
                QMessageBox.warning(None, "物品字典为空", 
                    "物品字典未设置或内容为空，无法分割物品名。请在'物品字典管理'中添加物品名后重试。")
                return []
            
            # 1. 提取物品名行
            item_line = ''
            for idx, line in enumerate(lines):
                if line.startswith('物品'):
                    items_block = []
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['品质', '数量', '等级', '一口价']):
                            break
                        items_block.append(lines[j])
                    item_line = ''.join(items_block)
                    break
            
            # 2. 用物品字典分割物品名
            item_names = []
            pos = 0
            while pos < len(item_line):
                matched = False
                for name in sorted(dict_items, key=lambda x: -len(x)):
                    if item_line.startswith(name, pos):
                        item_names.append(name)
                        pos += len(name)
                        matched = True
                        break
                if not matched:
                    pos += 1
            
            # 3. 提取所有数量
            quantities = []
            for idx, line in enumerate(lines):
                if line.startswith('数量'):
                    qty_block = []
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['一口价', '等级', '品质']):
                            break
                        qty_block.append(lines[j])
                    qty_line = ''.join(qty_block)
                    # 提取数字
                    qty_digits = re.findall(r'\d+', qty_line)
                    quantities.extend([int(q) for q in qty_digits])
            
            # 4. 提取所有一口价
            prices = []
            for idx, line in enumerate(lines):
                if line.startswith('一口价'):
                    price_block = []
                    for j in range(idx+1, len(lines)):
                        if any(lines[j].startswith(x) for x in ['数量', '等级', '品质', '物品']):
                            break
                        price_block.append(lines[j])
                    price_line = ''.join(price_block)
                    # 提取数字
                    price_digits = re.findall(r'\d+', price_line)
                    prices.extend([int(p) for p in price_digits])
            
            # 5. 组装数据
            result = []
            min_len = min(len(item_names), len(quantities), len(prices)) if item_names and quantities and prices else 0
            for i in range(min_len):
                result.append({
                    'item_name': item_names[i],
                    'quantity': quantities[i],
                    'market_price': prices[i]
                })
            return result
        except Exception as e:
            QMessageBox.critical(None, "解析错误", f"监控数据解析失败: {str(e)}")
            return [] 