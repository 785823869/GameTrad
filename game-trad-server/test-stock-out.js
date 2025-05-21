// 测试save_stock_out函数是否允许库存为负
const db = require('./backend/utils/db');

async function testSaveStockOut() {
  console.log('开始测试save_stock_out函数...');
  
  try {
    // 获取当前日期的MySQL格式
    const now = new Date();
    const mysqlDateTime = now.toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');
    
    // 测试库存不足的情况 - 灵之精火
    const testData = {
      item_name: '灵之精火',
      transaction_time: mysqlDateTime, // 使用MySQL兼容的日期格式
      quantity: 10000, // 设置一个很大的数量，确保超过库存
      unit_price: 100,
      fee: 0,
      total_amount: 1000000,
      note: '测试库存为负的情况'
    };
    
    console.log(`准备导出物品 "${testData.item_name}"，数量 ${testData.quantity}`);
    console.log(`使用的日期格式: ${testData.transaction_time}`);
    
    // 先查询当前库存
    const inventory = await db.fetchOne(
      "SELECT item_name, quantity FROM inventory WHERE item_name = ?", 
      [testData.item_name]
    );
    
    if (inventory) {
      console.log(`当前库存: ${inventory.item_name} - ${inventory.quantity}个`);
    } else {
      console.log(`物品 "${testData.item_name}" 不存在于库存中，将自动创建`);
    }
    
    // 尝试保存出库记录
    console.log('调用save_stock_out函数...');
    const result = await db.save_stock_out(testData);
    
    if (result) {
      console.log('✅ 测试成功! 即使库存不足，出库记录仍然保存成功');
      console.log('出库记录ID:', result.insertId);
      
      // 检查库存是否为负数
      const updatedInventory = await db.fetchOne(
        "SELECT item_name, quantity FROM inventory WHERE item_name = ?", 
        [testData.item_name]
      );
      
      if (updatedInventory) {
        console.log(`更新后库存: ${updatedInventory.item_name} - ${updatedInventory.quantity}个`);
        
        if (updatedInventory.quantity < 0) {
          console.log('✅ 库存成功变为负数!');
        } else {
          console.log('❌ 库存未变为负数，请检查代码');
        }
      } else {
        console.log('❌ 无法查询更新后的库存，请检查代码');
      }
    } else {
      console.log('❌ 测试失败! 出库记录保存失败');
    }
  } catch (error) {
    console.error('❌ 测试过程中出错:', error);
  } finally {
    // 关闭数据库连接
    process.exit(0);
  }
}

// 运行测试
testSaveStockOut(); 