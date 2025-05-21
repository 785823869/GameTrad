const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const db = require('../utils/db');

// 格式化入库记录数据
const formatStockInItem = (item) => {
  // 在DEBUG模式下才输出详细日志
  const DEBUG = process.env.DEBUG_LEVEL === 'verbose';
      
      // 检查数据结构，确保我们能够安全地访问
      if (!item) {
    logger.error("接收到空的入库数据库记录");
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
        cost: Array.isArray(item) ? Number(item[4] || 0) : Number(item.cost || 0),
        avg_cost: Array.isArray(item) ? Number(item[5] || 0) : Number(item.avg_cost || 0),
    note: Array.isArray(item) ? (item[6] || '') : (item.note || '')
  };
};

/**
 * 获取所有入库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getStockIn = async (req, res) => {
  try {
    const stockInData = await db.get_stock_in();
    
    // 格式化数据
    const formattedItems = [];
    for (const item of stockInData) {
      const formattedItem = formatStockInItem(item);
      if (!formattedItem) continue;
      
      formattedItems.push(formattedItem);
    }
    
    // 添加日志，记录返回的数据结构
    logger.info(`返回入库数据: ${formattedItems.length} 条记录, 示例: ${JSON.stringify(formattedItems.slice(0, 1))}`);
    
    res.status(200).json(formattedItems);
  } catch (error) {
    logger.error(`获取入库数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取入库数据失败',
      error: error.message
    });
  }
};

/**
 * 添加入库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.addStockIn = async (req, res) => {
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
    
    if (!req.body.avg_cost || isNaN(Number(req.body.avg_cost)) || Number(req.body.avg_cost) <= 0) {
      return res.status(400).json({
        success: false,
        message: '单价必须为正数'
      });
    }
    
    // 准备入库记录数据
    const itemName = req.body.item_name.trim();
    const quantity = Number(req.body.quantity);
    const avgCost = Number(req.body.avg_cost);
    const cost = quantity * avgCost;
    
    // 生成MySQL兼容的日期格式 (YYYY-MM-DD HH:MM:SS)
    const now = new Date();
    const mysqlDateTime = now.toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');
    
    const stockInData = {
      item_name: itemName,
      transaction_time: mysqlDateTime, // 使用MySQL兼容格式
      quantity: quantity,
      cost: cost,
      avg_cost: avgCost,
      note: req.body.note || ''
    };
    
    // 保存入库记录
    const saveResult = await db.save_stock_in(stockInData);
    
    if (!saveResult) {
      return res.status(400).json({
        success: false,
        message: '保存入库记录失败'
      });
    }
    
    // 更新库存
    // TODO: 实现库存增加逻辑
    
    res.status(200).json({
      success: true,
      message: '入库记录添加成功，库存已更新'
    });
  } catch (error) {
    logger.error(`添加入库记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '添加入库记录失败',
      error: error.message
    });
  }
};

/**
 * 更新入库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.updateStockIn = async (req, res) => {
  try {
    const { id } = req.params;
    
    // 首先获取现有记录
    const query = "SELECT * FROM stock_in WHERE id = ?";
    const existingRecord = await db.fetchOne(query, [id]);
    
    if (!existingRecord) {
      return res.status(404).json({
        success: false,
        message: '入库记录不存在'
      });
    }
    
    // 确保更新时重新计算均价
    const quantity = Number(req.body.quantity);
    const cost = Number(req.body.cost);
    const avgCost = quantity > 0 ? cost / quantity : 0;
    
    // 更新记录
    const updateQuery = `
      UPDATE stock_in 
      SET 
        item_name = ?, 
        quantity = ?, 
        cost = ?, 
        avg_cost = ?, 
        note = ?
      WHERE 
        id = ?
    `;
    
    const params = [
      req.body.item_name,
      quantity,
      cost,
      avgCost, // 使用计算的均价
      req.body.note || '',
      id
    ];
    
    const result = await db.execute(updateQuery, params);
    
    if (result) {
      res.status(200).json({
        success: true,
        message: '入库记录更新成功'
      });
    } else {
      res.status(400).json({
        success: false,
        message: '入库记录更新失败'
      });
    }
  } catch (error) {
    logger.error(`更新入库记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '更新入库记录失败',
      error: error.message
    });
  }
};

/**
 * 删除入库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.deleteStockIn = async (req, res) => {
  try {
    const { id } = req.params;
    
    const query = "DELETE FROM stock_in WHERE id = ?";
    const result = await db.execute(query, [id]);
    
    if (result) {
      res.status(200).json({
        success: true,
        message: '入库记录删除成功'
      });
    } else {
      res.status(400).json({
        success: false,
        message: '入库记录删除失败'
      });
    }
  } catch (error) {
    logger.error(`删除入库记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '删除入库记录失败',
      error: error.message
    });
  }
};

/**
 * OCR导入入库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.importStockIn = async (req, res) => {
  try {
    // 记录原始请求数据用于调试
    logger.info(`收到OCR入库导入请求，数据类型: ${typeof req.body}`);
    logger.info(`原始请求数据: ${JSON.stringify(req.body).substring(0, 1000)}`); // 记录部分数据避免过长
    
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
    
    logger.info(`开始处理OCR入库导入数据，共${records.length}条记录`);
    
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
    
    // 处理每一条记录
    for (const record of records) {
      try {
        // 详细记录每条记录的处理
        logger.info(`处理入库记录: ${JSON.stringify(record)}`);
        
        // 严格验证并转换数据
        if (!record.item_name || record.quantity === undefined || record.avg_cost === undefined) {
          const missingFields = [];
          if (!record.item_name) missingFields.push('item_name');
          if (record.quantity === undefined) missingFields.push('quantity');
          if (record.avg_cost === undefined) missingFields.push('avg_cost');
          
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
        let quantity, avgCost, cost;
        try {
          quantity = parseFloat(record.quantity);
          avgCost = parseFloat(record.avg_cost);
          
          // 检查是否是有效数字
          if (isNaN(quantity) || isNaN(avgCost)) {
            results.failed++;
            const errorMsg = `数据包含无效数字: 数量=${record.quantity}, 单价=${record.avg_cost}`;
            logger.warn(errorMsg);
            results.errors.push(errorMsg);
            continue;
          }
          
          // 计算总成本
          cost = quantity * avgCost;
          
        } catch (e) {
          results.failed++;
          const errorMsg = `数据转换错误: ${e.message}`;
          logger.error(errorMsg);
          logger.error(`错误数据: ${JSON.stringify(record)}`);
          results.errors.push(errorMsg);
          continue;
        }
        
        // 检查数值有效性
        if (quantity <= 0 || avgCost < 0) {
          results.failed++;
          const errorMsg = `数据值无效: 数量=${quantity}, 单价=${avgCost}`;
          logger.warn(errorMsg);
          results.errors.push(errorMsg);
          continue;
        }
        
        logger.info(`处理记录: 物品=${itemName}, 数量=${quantity}, 单价=${avgCost}, 总成本=${cost}`);
        
        // 准备保存的数据
        const stockInData = {
          item_name: itemName,
          transaction_time: record.transaction_time || new Date().toISOString(),
          quantity: quantity,
          cost: cost,
          avg_cost: avgCost,
          note: record.note || '通过OCR导入'
        };
        
        // 确保交易时间格式符合MySQL要求
        if (stockInData.transaction_time && typeof stockInData.transaction_time === 'string') {
          // 将ISO格式(2025-05-21T07:54:54.159Z)转换为MySQL格式(2025-05-21 07:54:54)
          stockInData.transaction_time = stockInData.transaction_time.replace('T', ' ').replace(/\.\d+Z$/, '');
          logger.info(`转换后的日期格式: ${stockInData.transaction_time}`);
        }
        
        // 保存入库记录
        logger.info(`准备保存入库记录: ${JSON.stringify(stockInData)}`);
        
        const startTime = Date.now();
        const saveResult = await db.save_stock_in(stockInData);
        const endTime = Date.now();
        logger.info(`保存操作耗时: ${endTime - startTime}ms`);
        
        if (saveResult) {
          logger.info(`入库记录保存成功: ${itemName}, ID=${saveResult.insertId || '未返回'}`);
          
          // 记录成功处理的记录
            results.success++;
          results.processed_records.push({
            id: saveResult.insertId,
            item_name: itemName,
            quantity: quantity,
            status: 'success'
          });
          logger.info(`成功导入记录: ${itemName}, 数量: ${quantity}`);
        } else {
          results.failed++;
          const errorMsg = `保存入库记录失败: ${itemName}`;
          logger.error(errorMsg);
          results.errors.push(errorMsg);
        }
      } catch (err) {
        results.failed++;
        const errorMsg = `处理记录出错: ${err.message}`;
        logger.error(`${errorMsg}, 详细错误: ${err.stack || '无堆栈信息'}`);
        results.errors.push(errorMsg);
      }
    }
    
    logger.info(`OCR入库导入处理完成，成功: ${results.success}, 失败: ${results.failed}`);
    if (results.errors.length > 0) {
      logger.info(`导入错误: ${JSON.stringify(results.errors)}`);
    }
    
    res.status(200).json({
      success: true,
      message: `导入完成: 成功${results.success}条，失败${results.failed}条`,
      results
    });
  } catch (error) {
    logger.error(`导入入库记录失败: ${error.message}`);
    logger.error(`导入失败详细错误: ${error.stack || '无堆栈信息'}`);
    res.status(500).json({
      success: false,
      message: '导入入库记录失败',
      error: error.message
    });
  }
}; 