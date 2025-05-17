from src.core.db_manager import DatabaseManager

def remove_duplicate_inventory():
    """删除库存表中的重复物品记录"""
    print("开始检查和清理重复的库存数据...")
    db = DatabaseManager()
    
    # 查询所有库存数据
    inventory_data = db.fetch_all("SELECT * FROM inventory")
    print(f"当前库存记录总数: {len(inventory_data)}")
    
    # 按物品名分组
    items_by_name = {}
    for item in inventory_data:
        item_id, item_name = item[0], item[1]
        if item_name not in items_by_name:
            items_by_name[item_name] = []
        items_by_name[item_name].append(item_id)
    
    # 检查每个物品是否有重复记录
    duplicates_found = 0
    for item_name, id_list in items_by_name.items():
        if len(id_list) > 1:
            print(f"物品 '{item_name}' 有 {len(id_list)} 条重复记录: {id_list}")
            duplicates_found += len(id_list) - 1
    
    if duplicates_found == 0:
        print("没有发现重复记录，库存数据正常。")
        return
    
    # 确认是否要删除重复记录
    choice = input(f"发现 {duplicates_found} 条重复记录。是否删除除最新记录外的所有重复项？(y/n): ")
    if choice.lower() != 'y':
        print("操作已取消")
        return
    
    # 删除每个物品的重复记录，只保留ID最大的一条（最新添加的记录）
    for item_name, id_list in items_by_name.items():
        if len(id_list) > 1:
            # 排序ID列表，保留最大ID
            id_list.sort(reverse=True)
            keep_id = id_list[0]
            delete_ids = id_list[1:]
            
            # 删除重复记录
            for delete_id in delete_ids:
                db.execute_query("DELETE FROM inventory WHERE id = %s", (delete_id,))
                print(f"已删除物品 '{item_name}' 的重复记录 ID: {delete_id}")
    
    # 验证清理结果
    inventory_data = db.fetch_all("SELECT * FROM inventory")
    print(f"清理完成，当前库存记录总数: {len(inventory_data)}")
    
    # 最后重新检查是否还有重复
    items_by_name = {}
    for item in inventory_data:
        item_id, item_name = item[0], item[1]
        if item_name not in items_by_name:
            items_by_name[item_name] = []
        items_by_name[item_name].append(item_id)
    
    duplicates = 0
    for item_name, id_list in items_by_name.items():
        if len(id_list) > 1:
            duplicates += 1
    
    if duplicates == 0:
        print("验证通过：所有重复记录已清除")
    else:
        print(f"警告：仍有 {duplicates} 个物品存在重复记录")

if __name__ == "__main__":
    remove_duplicate_inventory() 