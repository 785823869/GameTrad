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
  // 在DEBUG模式下才输出详细日志
  const DEBUG = process.env.DEBUG_LEVEL === 'verbose';
  
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
    logger.error(`日期格式化失败: ${err.message}, 原始值: ${DEBUG ? JSON.stringify(item) : '已隐藏'}`);
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
    
    // 生成MySQL兼容的日期格式 (YYYY-MM-DD HH:MM:SS)
    const now = new Date();
    const mysqlDateTime = now.toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');
    
    const stockOutData = {
      item_name: itemName,
      transaction_time: mysqlDateTime, // 使用MySQL兼容格式
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
    // 记录原始请求数据用于调试
    logger.info(`收到OCR导入请求，数据类型: ${typeof req.body}`);
    logger.info(`原始请求数据: ${JSON.stringify(req.body).substring(0, 1000)}`);
    
    // 添加请求处理开始计时
    const startTime = Date.now();
    
    // 处理两种可能的请求格式：直接数组或者{records:[...]}对象
    let records = req.body;
    
    // 检查是否是{records:[...]}格式
    if (req.body && req.body.records && Array.isArray(req.body.records)) {
      records = req.body.records;
      logger.info('收到records对象格式的OCR导入数据');
    }
    
    // 确保records是数组
    if (!Array.isArray(records)) {
      logger.error(`导入数据格式不正确，应为数组: ${typeof records}, 值: ${JSON.stringify(records).substring(0, 200)}`);
      return res.status(400).json({
        success: false,
        message: '导入数据格式不正确，应为数组'
      });
    }
    
    logger.info(`开始处理OCR导入数据，共${records.length}条记录`);
    
    // 记录更多请求细节，帮助调试
    if (records.length > 0) {
      logger.info(`首条记录完整数据: ${JSON.stringify(records[0])}`);
      logger.info(`数据字段: ${Object.keys(records[0]).join(', ')}`);
    } else {
      logger.warn('收到空数组，没有数据可处理');
      return res.status(400).json({
        success: false,
        message: '没有数据可导入'
      });
    }
    
    const results = {
      success: 0,
      failed: 0,
      errors: [],
      processed_records: [] // 记录成功处理的记录信息
    };
    
    // 预处理阶段：检查所有物品是否存在于库存中
    logger.info("预处理阶段：检查所有物品是否存在于库存中");
    const itemsToCheck = records.map(record => record.item_name).filter(name => name);
    const uniqueItems = [...new Set(itemsToCheck)]; // 去重
    
    // 创建物品名称到库存情况的映射
    const inventoryMap = {};
    
    for (const itemName of uniqueItems) {
      try {
        const inventoryCheck = await db.fetchOne(
          "SELECT id, item_name, quantity, avg_price FROM inventory WHERE item_name = ?", 
          [itemName]
        );
        
        if (inventoryCheck) {
          logger.info(`物品 "${itemName}" 库存情况: 数量=${inventoryCheck.quantity}, 均价=${inventoryCheck.avg_price}`);
          inventoryMap[itemName] = inventoryCheck;
        } else {
          logger.warn(`物品 "${itemName}" 不存在于库存中，将尝试自动创建`);
          
          // 尝试在库存中添加物品，初始化为0库存
          try {
            const insertResult = await db.execute(
              "INSERT INTO inventory (item_name, quantity, avg_price, break_even_price, selling_price, profit, profit_rate, total_profit, inventory_value) VALUES (?, 0, 0, 0, 0, 0, 0, 0, 0)",
              [itemName]
            );
            
            if (insertResult) {
              logger.info(`成功创建物品 "${itemName}" 的库存记录，初始库存为0`);
              inventoryMap[itemName] = { id: insertResult.insertId, item_name: itemName, quantity: 0, avg_price: 0 };
            } else {
              logger.error(`无法创建物品 "${itemName}" 的库存记录`);
              inventoryMap[itemName] = null;
            }
          } catch (insertError) {
            logger.error(`创建物品库存记录失败: ${insertError.message}`);
            inventoryMap[itemName] = null;
          }
        }
      } catch (checkError) {
        logger.error(`检查物品 "${itemName}" 库存时出错: ${checkError.message}`);
        inventoryMap[itemName] = null;
      }
    }
    
    // 处理每一条记录
    for (const record of records) {
      try {
        // 详细记录每条记录的处理
        logger.info(`处理记录: ${JSON.stringify(record)}`);
        
        // 严格验证并转换数据
        if (!record.item_name || record.quantity === undefined || record.unit_price === undefined) {
          const missingFields = [];
          if (!record.item_name) missingFields.push('item_name');
          if (record.quantity === undefined) missingFields.push('quantity');
          if (record.unit_price === undefined) missingFields.push('unit_price');
          
          results.failed++;
          const errorMsg = `记录缺少必需字段: ${missingFields.join(', ')}`;
          logger.warn(errorMsg);
          logger.warn(`无效记录数据: ${JSON.stringify(record)}`);
          results.errors.push(errorMsg);
          continue;
        }
        
        // 确保物品名称不为空且数据类型转换
        const itemName = String(record.item_name).trim();
        
        // 转换数值并进行验证
        let quantity, unitPrice, fee, totalAmount;
        try {
          quantity = Number(record.quantity);
          unitPrice = Number(record.unit_price);
          fee = Number(record.fee || 0);
          
          // 检查是否是有效数字
          if (isNaN(quantity) || isNaN(unitPrice) || isNaN(fee)) {
            results.failed++;
            const errorMsg = `数据包含无效数字: 数量=${record.quantity}, 单价=${record.unit_price}, 手续费=${record.fee}`;
            logger.warn(errorMsg);
            results.errors.push(errorMsg);
            continue;
          }
          
          // 计算总金额 - 比较传入的总金额与计算值是否一致
          const calculatedTotal = (quantity * unitPrice) - fee;
          totalAmount = Number(record.total_amount || calculatedTotal);
          
          // 如果传入了总金额但与计算值相差较大，记录警告并使用计算值
          if (record.total_amount !== undefined && Math.abs(totalAmount - calculatedTotal) > 0.01) {
            logger.warn(`总金额与计算值不一致，使用计算值: 传入值=${totalAmount}, 计算值=${calculatedTotal}`);
            totalAmount = calculatedTotal;
          }
        } catch (e) {
          results.failed++;
          const errorMsg = `数据转换错误: ${e.message}`;
          logger.error(errorMsg);
          logger.error(`错误数据: ${JSON.stringify(record)}`);
          results.errors.push(errorMsg);
          continue;
        }
        
        // 检查数值有效性
        if (quantity <= 0 || unitPrice < 0) {
          results.failed++;
          const errorMsg = `数据值无效: 数量=${quantity}, 单价=${unitPrice}`;
          logger.warn(errorMsg);
          results.errors.push(errorMsg);
          continue;
        }
        
        // 检查物品库存
        const inventoryInfo = inventoryMap[itemName];
        let warningMsg = '';
        
        if (!inventoryInfo) {
          warningMsg = `物品 "${itemName}" 在库存中不存在且无法创建`;
          logger.warn(warningMsg);
          results.errors.push(warningMsg);
          results.failed++;
          continue;
        } else {
          logger.info(`物品 "${itemName}" 当前库存: ${inventoryInfo.quantity}, 出库数量: ${quantity}`);
          // 如果库存不足，记录警告但继续处理
          if (inventoryInfo.quantity < quantity) {
            warningMsg = `物品 "${itemName}" 库存不足，当前库存: ${inventoryInfo.quantity}, 需求数量: ${quantity}, 将导致库存为负`;
            logger.warn(warningMsg);
            // 不再将警告添加到errors，而是单独记录
          }
        }
        
        logger.info(`处理记录: 物品=${itemName}, 数量=${quantity}, 单价=${unitPrice}, 手续费=${fee}, 总金额=${totalAmount}`);
        
        // 准备保存的数据
        const stockOutData = {
          item_name: itemName,
          transaction_time: record.transaction_time || new Date().toISOString(),
          quantity: quantity,
          unit_price: unitPrice,
          fee: fee,
          total_amount: totalAmount,
          note: record.note || '通过OCR导入'
        };
        
        // 确保交易时间格式符合MySQL要求
        if (stockOutData.transaction_time && typeof stockOutData.transaction_time === 'string') {
          // 将ISO格式(2025-05-21T07:54:54.159Z)转换为MySQL格式(2025-05-21 07:54:54)
          stockOutData.transaction_time = stockOutData.transaction_time.replace('T', ' ').replace(/\.\d+Z$/, '');
          logger.info(`转换后的日期格式: ${stockOutData.transaction_time}`);
        }
        
        // 检查是否已存在相同的记录，避免重复导入
        try {
          logger.info(`检查潜在重复记录: 物品=${itemName}, 数量=${quantity}, 单价=${unitPrice}, 时间=${stockOutData.transaction_time}`);
          
          // 修复的重复检测查询 - 纠正语法错误并确保正确处理结果
          const duplicateCheckQuery = `
            SELECT id, fee, total_amount FROM stock_out 
            WHERE item_name = ? 
            AND quantity = ? 
            AND unit_price = ?
            AND DATE(transaction_time) = DATE(?)
            AND HOUR(transaction_time) = HOUR(?)
            AND MINUTE(transaction_time) = MINUTE(?)
          `;
          
          const [duplicates] = await db.execute(duplicateCheckQuery, [
            stockOutData.item_name,
            stockOutData.quantity,
            stockOutData.unit_price,
            stockOutData.transaction_time,
            stockOutData.transaction_time,
            stockOutData.transaction_time
          ]);
          
          // 添加防错处理确保duplicates总是数组
          const duplicatesArray = Array.isArray(duplicates) ? duplicates : [];
          
          logger.info(`重复检测结果: 找到${duplicatesArray.length}条潜在重复记录`);
          
          if (duplicatesArray.length > 0) {
            // 已存在相同记录，记录详细日志并跳过
            const duplicateId = duplicatesArray[0].id;
            const duplicateFee = duplicatesArray[0].fee || 0;
            const duplicateTotal = duplicatesArray[0].total_amount || 0;
            
            // 详细记录差异
            logger.warn(`发现重复记录: ID=${duplicateId}, 物品=${itemName}, 数量=${quantity}, 单价=${unitPrice}`);
            logger.warn(`现有手续费=${duplicateFee}, 新手续费=${stockOutData.fee}`);
            logger.warn(`现有总金额=${duplicateTotal}, 新总金额=${stockOutData.total_amount}`);
            logger.warn(`跳过此重复记录，防止重复导入`);
            
            // 记录成功处理(跳过)的记录
            results.success++;
            results.processed_records.push({
              id: duplicateId,
              item_name: itemName,
              quantity: quantity,
              unit_price: unitPrice,
              fee: stockOutData.fee, // 添加手续费信息
              total_amount: stockOutData.total_amount,
              status: 'skipped',
              message: '跳过重复记录',
              warning: warningMsg || undefined
            });
            
            continue; // 跳过此记录的后续处理
          }
        } catch (dupCheckError) {
          logger.error(`检查重复记录时出错: ${dupCheckError.message}`);
          // 记录详细错误信息以便调试
          logger.error(`错误堆栈: ${dupCheckError.stack || '无堆栈信息'}`);
          logger.error(`检查的数据: item_name=${stockOutData.item_name}, quantity=${stockOutData.quantity}, unit_price=${stockOutData.unit_price}, time=${stockOutData.transaction_time}`);
          // 即使检查失败，也继续处理，避免因检查失败而阻止正常导入
        }
        
        // 使用事务保存记录和更新库存
        const conn = await db.getConnection();
        try {
          await conn.beginTransaction();
          
          // 1. 保存出库记录
          logger.info(`准备保存出库记录: ${JSON.stringify(stockOutData)}`);
          const [insertResult] = await conn.query(
            `INSERT INTO stock_out (item_name, transaction_time, quantity, unit_price, fee, total_amount, note) 
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            [
              stockOutData.item_name,
              stockOutData.transaction_time,
              stockOutData.quantity,
              stockOutData.unit_price,
              stockOutData.fee,
              stockOutData.total_amount,
              stockOutData.note
            ]
          );
          
          const insertId = insertResult.insertId;
          logger.info(`出库记录保存成功: ID=${insertId}`);
          
          // 2. 更新库存
          const [updateResult] = await conn.query(
            "UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?",
            [stockOutData.quantity, stockOutData.item_name]
          );
          
          logger.info(`库存更新结果: affectedRows=${updateResult.affectedRows}`);
          
          if (updateResult.affectedRows === 0) {
            throw new Error(`更新库存失败: 找不到物品 "${stockOutData.item_name}"`);
          }
          
          // 提交事务
          await conn.commit();
          logger.info(`交易提交成功`);
          
          // 记录成功处理的记录
          results.success++;
          results.processed_records.push({
            id: insertId,
            item_name: itemName,
            quantity: quantity,
            unit_price: unitPrice,
            status: 'success',
            warning: warningMsg || undefined
          });
          
          logger.info(`成功导入记录: ${itemName}, 数量: ${quantity}`);
          
          // 更新内存中的库存映射，以便于后续记录使用最新的库存数据
          if (inventoryMap[itemName]) {
            inventoryMap[itemName].quantity -= quantity;
            logger.info(`更新内存中的库存映射，${itemName}当前库存更新为: ${inventoryMap[itemName].quantity}`);
          }
          
        } catch (dbError) {
          // 回滚事务
          await conn.rollback();
          logger.error(`数据库操作失败，已回滚: ${dbError.message}`);
          
          results.failed++;
          const errorMsg = `保存出库记录失败: ${itemName}, 错误: ${dbError.message}`;
          logger.error(errorMsg);
          results.errors.push(errorMsg);
          
        } finally {
          // 释放连接
          conn.release();
        }
        
      } catch (err) {
        results.failed++;
        const errorMsg = `处理记录出错: ${err.message}`;
        logger.error(`${errorMsg}, 详细错误: ${err.stack || '无堆栈信息'}`);
        results.errors.push(errorMsg);
      }
    }
    
    // 计算处理耗时
    const endTime = Date.now();
    const processTime = endTime - startTime;
    
    logger.info(`OCR导入处理完成，耗时: ${processTime}ms, 成功: ${results.success}, 失败: ${results.failed}`);
    if (results.errors.length > 0) {
      logger.info(`导入错误: ${JSON.stringify(results.errors)}`);
    }
    
    res.status(200).json({
      success: true,
      message: `导入完成: 成功${results.success}条，失败${results.failed}条`,
      process_time_ms: processTime,
      results
    });
  } catch (error) {
    logger.error(`导入出库记录失败: ${error.message}`);
    logger.error(`导入失败详细错误: ${error.stack || '无堆栈信息'}`);
    res.status(500).json({
      success: false,
      message: '导入出库记录失败',
      error: error.message
    });
  }
}; 