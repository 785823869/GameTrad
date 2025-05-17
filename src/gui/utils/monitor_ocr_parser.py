"""
交易监控OCR专用解析器
用于解析交易监控界面的截图OCR文本，提取物品名称、数量和一口价等信息
"""
import re


def parse_monitor_ocr_text(text, item_dict=None):
    """
    解析交易监控OCR文本，提取物品、数量、一口价，确保每个物品为一条数据
    
    参数:
        text: OCR识别后的文本
        item_dict: 物品字典列表，用于物品名称识别
    
    返回:
        list: 解析后的数据列表，每项包含item_name, quantity, market_price等字段
    """
    try:
        print(f"正在解析交易监控OCR文本: {text}")
        
        # 确保item_dict不为None
        if item_dict is None:
            item_dict = []
        
        # 对输入文本进行预处理
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        # 尝试提取物品、数量和一口价的区块
        item_block = ""
        quantity_block = ""
        price_block = ""
        
        item_mode = False
        quantity_mode = False
        price_mode = False
        
        for idx, line in enumerate(lines):
            # 判断当前行是否为标题行
            if line.startswith('物品') or '物品' in line:
                item_mode = True
                quantity_mode = False
                price_mode = False
                continue
            elif line.startswith('数量') or '数量' in line:
                item_mode = False
                quantity_mode = True
                price_mode = False
                # 如果"数量"行自身包含数字，直接提取为第一个数量
                if '数量' in line:
                    # 提取"数量"后面的数字，这是第一个数字
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        quantity_block += " ".join(numbers) + " "
                continue
            elif line.startswith('一口价') or '一口价' in line:
                item_mode = False
                quantity_mode = False
                price_mode = True
                # 如果"一口价"行自身包含数字，直接提取为第一个价格
                if '一口价' in line:
                    # 提取"一口价"后面的数字，这是第一个价格
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        price_block += " ".join(numbers) + " "
                continue
            
            # 根据当前模式，将行添加到相应的区块
            if item_mode:
                item_block += line + " "
            elif quantity_mode:
                quantity_block += line + " "
            elif price_mode:
                price_block += line + " "
        
        print(f"物品区块: {item_block}")
        print(f"数量区块: {quantity_block}")
        print(f"一口价区块: {price_block}")
        
        # 提取物品名
        item_names = []
        
        # 非物品关键词过滤列表
        non_item_keywords = ["品质", "珍品", "灵品", "精品", "普通", "等级", "特效", 
                           "绑定", "耐久", "修理", "级别", "o", "O", "口"]
        
        if item_dict and len(item_dict) > 0:
            # 使用物品字典进行识别
            pos = 0
            item_block = item_block.strip()
            
            while pos < len(item_block):
                matched = False
                # 按长度降序排序字典，优先匹配较长的物品名
                for name in sorted(item_dict, key=lambda x: -len(x)):
                    if pos + len(name) <= len(item_block) and item_block[pos:pos+len(name)] == name:
                        item_names.append(name)
                        pos += len(name)
                        matched = True
                        break
                
                if not matched:
                    # 无法匹配，跳过当前字符
                    pos += 1
        else:
            # 没有物品字典，尝试根据空格分割并过滤非物品关键词
            raw_names = [name.strip() for name in re.split(r'\s+', item_block) if name.strip()]
            
            for name in raw_names:
                # 跳过纯数字
                if name.isdigit():
                    continue
                    
                # 跳过包含非物品关键词的名称
                if any(keyword in name for keyword in non_item_keywords):
                    continue
                    
                # 跳过过短的名称（通常小于2个字符的不是物品名）
                if len(name) < 2:
                    continue
                    
                item_names.append(name)
        
        # 没有识别到物品名，尝试使用更宽松的提取方法
        if not item_names:
            # 从物品区块中提取可能的物品名
            # 去除常见非物品词
            for keyword in non_item_keywords:
                item_block = item_block.replace(keyword, " ")
                
            # 重新分割并过滤
            potential_items = [name.strip() for name in re.split(r'\s+', item_block) if name.strip()]
            for name in potential_items:
                if len(name) >= 2 and not name.isdigit():
                    item_names.append(name)
        
        # 提取数量和一口价（使用正则表达式匹配数字）
        quantities = [int(num) for num in re.findall(r'\d+', quantity_block)]
        prices = [int(num) for num in re.findall(r'\d+', price_block)]
        
        print(f"提取的物品名: {item_names}")
        print(f"提取的数量: {quantities}")
        print(f"提取的一口价: {prices}")
        
        # 构建结果列表
        result = []
        
        # 如果只有一个物品名但有多个数量和价格，创建多条记录
        if len(item_names) == 1 and (len(quantities) > 1 or len(prices) > 1):
            item_name = item_names[0]
            max_entries = max(len(quantities), len(prices))
            
            for i in range(max_entries):
                item = {
                    'item_name': item_name,
                    'quantity': quantities[i] if i < len(quantities) else 0,
                    'market_price': prices[i] if i < len(prices) else 0,
                    'note': 'OCR导入' if (i < len(quantities) and i < len(prices)) else '数据缺失'
                }
                result.append(item)
                
        # 多个物品名的情况
        elif len(item_names) > 1:
            for i, item_name in enumerate(item_names):
                item = {
                    'item_name': item_name,
                    'quantity': quantities[i] if i < len(quantities) else 0,
                    'market_price': prices[i] if i < len(prices) else 0,
                    'note': 'OCR导入' if (i < len(quantities) and i < len(prices)) else '数据缺失'
                }
                result.append(item)
                
        # 只有一个物品名且数量/价格也是一个的情况
        elif len(item_names) == 1:
            item = {
                'item_name': item_names[0],
                'quantity': quantities[0] if quantities else 0,
                'market_price': prices[0] if prices else 0,
                'note': 'OCR导入'
            }
            result.append(item)
            
        # 无物品名但有数量和价格，按数量和价格的最小数量创建记录
        elif quantities and prices:
            count = min(len(quantities), len(prices))
            for i in range(count):
                item = {
                    'item_name': f'未知物品_{i+1}',
                    'quantity': quantities[i],
                    'market_price': prices[i],
                    'note': 'OCR导入(物品名缺失)'
                }
                result.append(item)
        
        # 检查数据完整性
        if not result:
            print("未能提取到有效数据")
        else:
            print(f"成功解析数据，共生成{len(result)}条记录")
        
        return result
    
    except Exception as e:
        print(f"解析交易监控OCR文本失败: {str(e)}")
        # 返回空列表而不是None，便于后续处理
        return []


def extract_numbers_from_text(text):
    """
    从文本中提取数字
    
    参数:
        text: 输入文本
    
    返回:
        list: 提取的数字列表
    """
    return [int(num) for num in re.findall(r'\d+', text)]


def test_parse_monitor_ocr():
    """
    测试解析函数处理特定案例的能力
    """
    print("\n===== 测试1: 用户报告的问题文本(单物品多数量) =====")
    # 用户报告的问题文本
    test_text1 = """物品
灵矿髓灵草华至纯精华灵之精火
品质珍品
珍品灵品灵品
等级 0
o 0 o
数量 3293
8339 1039 10330
一口价 1947
1095 1085 1276"""
    
    # 调用解析函数
    result1 = parse_monitor_ocr_text(test_text1)
    
    # 验证结果
    print("\n测试1结果:")
    print(f"解析得到{len(result1)}条数据")
    for i, item in enumerate(result1):
        print(f"数据 {i+1}:")
        print(f"  物品名: {item['item_name']}")
        print(f"  数量: {item['quantity']}")
        print(f"  一口价: {item['market_price']}")
    
    # 验证数量字段
    quantities = [item['quantity'] for item in result1]
    expected = [3293, 8339, 1039, 10330]
    matches = all(q in quantities for q in expected)
    print(f"\n数量字段包含全部期望值: {'成功' if matches else '失败'}")
    print(f"期望值: {expected}")
    print(f"实际值: {quantities}")
    
    # 验证价格字段
    prices = [item['market_price'] for item in result1]
    expected = [1947, 1095, 1085, 1276]
    matches = all(p in prices for p in expected)
    print(f"\n价格字段包含全部期望值: {'成功' if matches else '失败'}")
    print(f"期望值: {expected}")
    print(f"实际值: {prices}")
    
    print("\n===== 测试2: 多物品多数量价格情况 =====")
    # 多物品情况
    test_text2 = """物品
灵矿髓 灵草华 至纯精华
数量 3293 8339 1039
一口价 1947 1095 1085"""
    
    # 调用解析函数
    result2 = parse_monitor_ocr_text(test_text2)
    
    # 验证结果
    print("\n测试2结果:")
    print(f"解析得到{len(result2)}条数据")
    for i, item in enumerate(result2):
        print(f"数据 {i+1}:")
        print(f"  物品名: {item['item_name']}")
        print(f"  数量: {item['quantity']}")
        print(f"  一口价: {item['market_price']}")
    
    print("\n===== 测试3: 无物品名只有数量价格情况 =====")
    # 无物品名情况
    test_text3 = """数量 3293 8339 1039
一口价 1947 1095 1085"""
    
    # 调用解析函数
    result3 = parse_monitor_ocr_text(test_text3)
    
    # 验证结果
    print("\n测试3结果:")
    print(f"解析得到{len(result3)}条数据")
    for i, item in enumerate(result3):
        print(f"数据 {i+1}:")
        print(f"  物品名: {item['item_name']}")
        print(f"  数量: {item['quantity']}")
        print(f"  一口价: {item['market_price']}")
    
    return {
        'test1': result1,
        'test2': result2, 
        'test3': result3
    }


# 如果直接运行此文件，执行测试
if __name__ == "__main__":
    test_parse_monitor_ocr() 