const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const db = require('../utils/db');

// 辅助函数：获取库存价格
const fetchInventoryPrice = async (itemName) => {
  const inventoryQuery = "SELECT avg_price FROM inventory WHERE item_name = ?";
  return await db.fetchOne(inventoryQuery, [itemName]);
};

// 格式化出库记录数据
const formatStockOutItem = (item) => {
  // 打印每个对象的结构以便调试
  console.log("原始出库数据记录:", JSON.stringify(item));
  
  // 检查数据结构，确保我们能够安全地访问
  if (!item) {
    logger.error("接收到空的出库数据库记录");
    return null;
  }
  
  // 确保transaction_time是正确的ISO格式日期字符串
  let formattedDate;
  try {
    // 获取transaction_time - 根据数据库查询结果可能是索引或属性名
    // 如果返回的是数组格式的结果，使用索引2访问
    // 如果返回的是对象格式的结果，使用属性名访问
    const rawDate = Array.isArray(item) ? item[2] : item.transaction_time;
    
    // 如果transaction_time是Date对象，转换为ISO字符串
    if (rawDate instanceof Date) {
      formattedDate = rawDate.toISOString();
    } 
    // 如果是字符串，尝试创建Date对象再转回ISO字符串
    else if (typeof rawDate === 'string') {
      formattedDate = new Date(rawDate).toISOString();
    } 
    // 其他情况下返回当前时间
    else {
      formattedDate = new Date().toISOString();
    }
  } catch (err) {
    // 如果转换失败，使用当前时间
    logger.error(`日期格式化失败: ${err.message}, 原始值: ${JSON.stringify(item)}`);
    formattedDate = new Date().toISOString();
  }
  
  // 确保物品名称不为空
  let itemName;
  // 如果返回的是数组格式的结果，使用索引1访问
  if (Array.isArray(item)) {
    itemName = item[1] || '';
  } else {
    // 如果是对象格式，优先使用item_name，备选使用itemName
    itemName = item.item_name || item.itemName || '';
  }
  
  // 如果物品名称仍然为空，使用一个占位值
  if (!itemName) {
    logger.warn(`发现空物品名，记录ID: ${Array.isArray(item) ? item[0] : item.id}`);
    itemName = `物品_${Math.random().toString(36).substr(2, 5)}`;
  }
  
  // 根据数据库返回结果的格式(数组或对象)构建统一的输出格式
  return {
    id: Array.isArray(item) ? item[0] : (item.id || 0),
    item_name: itemName,
    transaction_time: formattedDate,
    quantity: Array.isArray(item) ? Number(item[3] || 0) : Number(item.quantity || 0),
    unit_price: Array.isArray(item) ? Number(item[4] || 0) : Number(item.unit_price || 0),
    fee: Array.isArray(item) ? Number(item[5] || 0) : Number(item.fee || 0),
    total_amount: Array.isArray(item) ? Number(item[6] || 0) : Number(item.total_amount || 0),
    note: Array.isArray(item) ? (item[7] || '') : (item.note || '')
  };
};

/**
 * 获取所有出库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getStockOut = async (req, res) => {
  try {
    const stockOutData = await db.get_stock_out();
    
    // 格式化数据
    const formattedItems = [];
    for (const item of stockOutData) {
      // 基本数据格式化
      const formattedItem = formatStockOutItem(item);
      if (!formattedItem) continue;
      
      try {
        // 获取物品对应的库存价格
        const inventoryData = await fetchInventoryPrice(formattedItem.item_name);
        
        // 计算利润
        if (inventoryData && inventoryData.avg_price) {
          const avgCost = Number(inventoryData.avg_price);
          const quantity = formattedItem.quantity;
          const totalRevenue = formattedItem.total_amount;
          
          // 计算利润 = 总收入 - (平均成本 × 数量)
          formattedItem.profit = totalRevenue - (avgCost * quantity);
          
          // 计算利润率 = 利润 / 成本总额 * 100%
          const totalCost = avgCost * quantity;
          formattedItem.profit_rate = totalCost > 0 ? (formattedItem.profit / totalCost) * 100 : 0;
        } else {
          formattedItem.profit = 0;
          formattedItem.profit_rate = 0;
        }
      } catch (e) {
        logger.error(`计算利润字段出错: ${e.message}`);
        formattedItem.profit = 0;
        formattedItem.profit_rate = 0;
      }
      
      formattedItems.push(formattedItem);
    }
    
    // 添加日志，记录返回的数据结构
    logger.info(`返回出库数据: ${formattedItems.length} 条记录, 示例: ${JSON.stringify(formattedItems.slice(0, 1))}`);
    
    res.status(200).json(formattedItems);
  } catch (error) {
    logger.error(`获取出库数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取出库数据失败',
      error: error.message
    });
  }
};

/**
 * 添加出库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.addStockOut = async (req, res) => {
  try {
    // 验证和处理必要字段
    if (!req.body.item_name || !req.body.item_name.trim()) {
      return res.status(400).json({
        success: false,
        message: '物品名称不能为空'
      });
    }
    
    if (!req.body.quantity || isNaN(Number(req.body.quantity)) || Number(req.body.quantity) <= 0) {
      return res.status(400).json({
        success: false,
        message: '数量必须为正数'
      });
    }
    
    if (!req.body.unit_price || isNaN(Number(req.body.unit_price)) || Number(req.body.unit_price) <= 0) {
      return res.status(400).json({
        success: false,
        message: '单价必须为正数'
      });
    }
    
    // 准备出库记录数据
    const itemName = req.body.item_name.trim();
    const quantity = Number(req.body.quantity);
    const unitPrice = Number(req.body.unit_price);
    const fee = Number(req.body.fee || 0);
    const totalAmount = (quantity * unitPrice) - fee;
    
    const stockOutData = {
      item_name: itemName,
      transaction_time: new Date().toISOString(), // 使用当前时间
      quantity: quantity,
      unit_price: unitPrice,
      fee: fee,
      total_amount: totalAmount,
      note: req.body.note || ''
    };
    
    // 保存出库记录
    const saveResult = await db.save_stock_out(stockOutData);
    
    if (!saveResult) {
      return res.status(400).json({
        success: false,
        message: '保存出库记录失败'
      });
    }
    
    // 更新库存
    const inventoryResult = await db.decrease_inventory(itemName, quantity);
    
    if (!inventoryResult) {
      logger.warn(`出库记录已保存，但更新库存失败: ${itemName}`);
      // 返回一个警告但不是错误
      return res.status(200).json({
        success: true,
        warning: true,
        message: '出库记录添加成功，但库存更新失败，可能库存不足'
      });
    }
    
    res.status(200).json({
      success: true,
      message: '出库记录添加成功，库存已更新'
    });
  } catch (error) {
    logger.error(`添加出库记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '添加出库记录失败',
      error: error.message
    });
  }
};

/**
 * 更新出库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.updateStockOut = async (req, res) => {
  try {
    const { id } = req.params;
    
    // 首先获取现有记录
    const query = "SELECT * FROM stock_out WHERE id = ?";
    const existingRecord = await db.fetchOne(query, [id]);
    
    if (!existingRecord) {
      return res.status(404).json({
        success: false,
        message: '出库记录不存在'
      });
    }
    
    // 准备新的数据
    const itemName = req.body.item_name.trim();
    const quantity = Number(req.body.quantity);
    const unitPrice = Number(req.body.unit_price);
    const fee = Number(req.body.fee || 0);
    const totalAmount = (quantity * unitPrice) - fee;
    
    // 更新记录
    const updateQuery = `
      UPDATE stock_out 
      SET 
        item_name = ?, 
        quantity = ?, 
        unit_price = ?, 
        fee = ?,
        total_amount = ?,
        note = ?
      WHERE 
        id = ?
    `;
    
    const params = [
      itemName,
      quantity,
      unitPrice,
      fee,
      totalAmount,
      req.body.note || '',
      id
    ];
    
    const result = await db.execute(updateQuery, params);
    
    if (result) {
      res.status(200).json({
        success: true,
        message: '出库记录更新成功'
      });
    } else {
      res.status(400).json({
        success: false,
        message: '出库记录更新失败'
      });
    }
  } catch (error) {
    logger.error(`更新出库记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '更新出库记录失败',
      error: error.message
    });
  }
};

/**
 * 删除出库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.deleteStockOut = async (req, res) => {
  try {
    const { id } = req.params;
    
    // 首先获取记录，以便后续可以恢复库存
    const query = "SELECT * FROM stock_out WHERE id = ?";
    const record = await db.fetchOne(query, [id]);
    
    if (!record) {
      return res.status(404).json({
        success: false,
        message: '出库记录不存在'
      });
    }
    
    // 删除记录
    const deleteQuery = "DELETE FROM stock_out WHERE id = ?";
    const result = await db.execute(deleteQuery, [id]);
    
    if (result) {
      // 可选：删除后恢复库存
      // 这里需要根据业务需求决定是否要恢复库存
      // await db.increase_inventory(record.item_name, record.quantity);
      
      res.status(200).json({
        success: true,
        message: '出库记录删除成功'
      });
    } else {
      res.status(400).json({
        success: false,
        message: '出库记录删除失败'
      });
    }
  } catch (error) {
    logger.error(`删除出库记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '删除出库记录失败',
      error: error.message
    });
  }
};

/**
 * OCR导入出库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.importStockOut = async (req, res) => {
  try {
    const records = req.body;
    
    if (!Array.isArray(records)) {
      return res.status(400).json({
        success: false,
        message: '导入数据格式不正确，应为数组'
      });
    }
    
    const results = {
      success: 0,
      failed: 0,
      errors: []
    };
    
    // 处理每一条记录
    for (const record of records) {
      try {
        // 验证并转换数据
        if (!record.item_name || !record.quantity || !record.unit_price) {
          results.failed++;
          results.errors.push(`记录缺少必需字段: ${JSON.stringify(record)}`);
          continue;
        }
        
        // 确保物品名称不为空
        const itemName = record.item_name;
        const quantity = parseFloat(record.quantity) || 0;
        const unitPrice = parseFloat(record.unit_price) || 0;
        const fee = parseFloat(record.fee) || 0;
        
        // 计算总金额
        const totalAmount = (quantity * unitPrice) - fee;
        
        const stockOutData = {
          item_name: itemName,
          transaction_time: new Date().toISOString(),
          quantity: quantity,
          unit_price: unitPrice,
          fee: fee,
          total_amount: totalAmount,
          note: record.note || '通过OCR导入'
        };
        
        // 保存出库记录
        const saveSuccess = await db.save_stock_out(stockOutData);
        
        if (saveSuccess) {
          // 更新库存
          const inventorySuccess = await db.decrease_inventory(itemName, quantity);
          
          if (inventorySuccess) {
            results.success++;
          } else {
            results.failed++;
            results.errors.push(`更新库存失败，可能库存不足: ${JSON.stringify(stockOutData)}`);
          }
        } else {
          results.failed++;
          results.errors.push(`保存出库记录失败: ${JSON.stringify(stockOutData)}`);
        }
      } catch (err) {
        results.failed++;
        results.errors.push(`处理记录出错: ${err.message}`);
      }
    }
    
    res.status(200).json({
      success: true,
      message: `导入完成: 成功${results.success}条，失败${results.failed}条`,
      results
    });
  } catch (error) {
    logger.error(`导入出库记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '导入出库记录失败',
      error: error.message
    });
  }
}; 