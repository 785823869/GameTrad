const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const db = require('../utils/db');

// 格式化交易记录数据
const formatTransaction = (transaction) => {
  // 在DEBUG模式下才输出详细日志
  const DEBUG = process.env.DEBUG_LEVEL === 'verbose';
  
  // 检查数据结构，确保我们能够安全地访问
  if (!transaction) {
    logger.error("接收到空的交易数据库记录");
    return null;
  }
  
  // 确保transaction_time是正确的ISO格式日期字符串
  let formattedDate;
  try {
    const rawDate = Array.isArray(transaction) ? transaction[2] : transaction.transaction_time;
    
    if (rawDate instanceof Date) {
      formattedDate = rawDate.toISOString();
    } else if (typeof rawDate === 'string') {
      formattedDate = new Date(rawDate).toISOString();
    } else {
      formattedDate = new Date().toISOString();
    }
  } catch (err) {
    logger.error(`日期格式化失败: ${err.message}, 原始值: ${DEBUG ? JSON.stringify(transaction) : '已隐藏'}`);
    formattedDate = new Date().toISOString();
  }
  
  // 确保交易类型不为空
  let transactionType;
  if (Array.isArray(transaction)) {
    transactionType = transaction[1] || 'unknown';
  } else {
    transactionType = transaction.transaction_type || transaction.type || 'unknown';
  }
  
  // 确保物品名称不为空
  let itemName;
  if (Array.isArray(transaction)) {
    itemName = transaction[3] || '';
  } else {
    itemName = transaction.item_name || transaction.itemName || '';
  }
  
  if (!itemName) {
    logger.warn(`发现空物品名，交易ID: ${Array.isArray(transaction) ? transaction[0] : transaction.id}`);
    itemName = `物品_${Math.random().toString(36).substr(2, 5)}`;
  }
  
  // 根据数据库返回结果的格式(数组或对象)构建统一的输出格式
  return {
    id: Array.isArray(transaction) ? transaction[0] : (transaction.id || 0),
    transaction_type: transactionType,
    transaction_time: formattedDate,
    item_name: itemName,
    quantity: Array.isArray(transaction) ? Number(transaction[4] || 0) : Number(transaction.quantity || 0),
    price: Array.isArray(transaction) ? Number(transaction[5] || 0) : Number(transaction.price || 0),
    total_amount: Array.isArray(transaction) ? Number(transaction[6] || 0) : Number(transaction.total_amount || 0),
    fee: Array.isArray(transaction) ? Number(transaction[7] || 0) : Number(transaction.fee || 0),
    platform: Array.isArray(transaction) ? (transaction[8] || '') : (transaction.platform || ''),
    note: Array.isArray(transaction) ? (transaction[9] || '') : (transaction.note || '')
  };
};

/**
 * 获取所有交易记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getTransactions = async (req, res) => {
  try {
    // 查询参数
    const limit = parseInt(req.query.limit) || 100;
    const offset = parseInt(req.query.offset) || 0;
    const type = req.query.type; // 可选的交易类型过滤
    
    // 获取交易记录
    const transactionData = await db.get_transactions(type, limit, offset);
    
    // 格式化数据
    const formattedItems = [];
    for (const transaction of transactionData) {
      const formattedTransaction = formatTransaction(transaction);
      if (!formattedTransaction) continue;
      
      formattedItems.push(formattedTransaction);
    }
    
    // 添加日志，记录返回的数据结构
    logger.info(`返回交易数据: ${formattedItems.length} 条记录, 示例: ${JSON.stringify(formattedItems.slice(0, 1))}`);
    
    res.status(200).json(formattedItems);
  } catch (error) {
    logger.error(`获取交易数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取交易数据失败',
      error: error.message
    });
  }
};

/**
 * 添加交易记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.addTransaction = async (req, res) => {
  try {
    // 验证和处理必要字段
    if (!req.body.transaction_type || !req.body.transaction_type.trim()) {
      return res.status(400).json({
        success: false,
        message: '交易类型不能为空'
      });
    }
    
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
    
    if (!req.body.price || isNaN(Number(req.body.price)) || Number(req.body.price) <= 0) {
      return res.status(400).json({
        success: false,
        message: '价格必须为正数'
      });
    }
    
    // 准备交易记录数据
    const transactionType = req.body.transaction_type.trim();
    const itemName = req.body.item_name.trim();
    const quantity = Number(req.body.quantity);
    const price = Number(req.body.price);
    const fee = Number(req.body.fee || 0);
    const totalAmount = (quantity * price) - fee;
    
    // 生成MySQL兼容的日期格式 (YYYY-MM-DD HH:MM:SS)
    const now = new Date();
    const mysqlDateTime = now.toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');
    
    const transactionData = {
      transaction_type: transactionType,
      transaction_time: mysqlDateTime,
      item_name: itemName,
      quantity: quantity,
      price: price,
      total_amount: totalAmount,
      fee: fee,
      platform: req.body.platform || '',
      note: req.body.note || ''
    };
    
    // 保存交易记录
    const saveResult = await db.save_transaction(transactionData);
    
    if (!saveResult) {
      return res.status(400).json({
        success: false,
        message: '保存交易记录失败'
      });
    }
    
    res.status(200).json({
      success: true,
      message: '交易记录添加成功'
    });
  } catch (error) {
    logger.error(`添加交易记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '添加交易记录失败',
      error: error.message
    });
  }
};

/**
 * OCR导入交易记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.importTransactions = async (req, res) => {
  try {
    // 记录原始请求数据用于调试
    logger.info(`收到OCR交易导入请求，数据类型: ${typeof req.body}`);
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
    
    logger.info(`开始处理OCR交易导入数据，共${records.length}条记录`);
    
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
        logger.info(`处理交易记录: ${JSON.stringify(record)}`);
        
        // 检查交易类型
        if (!record.transaction_type) {
          // 如果未提供交易类型，尝试推断
          if (record.type) {
            record.transaction_type = record.type;
          } else {
            // 默认为"buy"类型
            record.transaction_type = "buy";
            logger.warn(`交易记录未指定类型，默认设置为"buy": ${JSON.stringify(record)}`);
          }
        }
        
        // 严格验证并转换数据
        if (!record.item_name || record.quantity === undefined || record.price === undefined) {
          const missingFields = [];
          if (!record.item_name) missingFields.push('item_name');
          if (record.quantity === undefined) missingFields.push('quantity');
          if (record.price === undefined) missingFields.push('price');
          
          results.failed++;
          const errorMsg = `记录缺少必需字段: ${missingFields.join(', ')}`;
          logger.warn(errorMsg);
          logger.warn(`无效记录数据: ${JSON.stringify(record)}`);
          results.errors.push(errorMsg);
          continue;
        }
        
        // 确保物品名称不为空且数据类型转换
        const itemName = String(record.item_name).trim();
        const transactionType = String(record.transaction_type).trim();
        
        // 转换数值并进行验证
        let quantity, price, fee, totalAmount;
        try {
          quantity = parseFloat(record.quantity);
          price = parseFloat(record.price);
          fee = parseFloat(record.fee || 0);
          
          // 检查是否是有效数字
          if (isNaN(quantity) || isNaN(price) || isNaN(fee)) {
            results.failed++;
            const errorMsg = `数据包含无效数字: 数量=${record.quantity}, 价格=${record.price}, 手续费=${record.fee}`;
            logger.warn(errorMsg);
            results.errors.push(errorMsg);
            continue;
          }
          
          // 计算总金额 - 比较传入的总金额与计算值是否一致
          const calculatedTotal = (quantity * price) - fee;
          totalAmount = parseFloat(record.total_amount || calculatedTotal);
          
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
        if (quantity <= 0 || price < 0) {
          results.failed++;
          const errorMsg = `数据值无效: 数量=${quantity}, 价格=${price}`;
          logger.warn(errorMsg);
          results.errors.push(errorMsg);
          continue;
        }
        
        logger.info(`处理记录: 类型=${transactionType}, 物品=${itemName}, 数量=${quantity}, 价格=${price}, 总额=${totalAmount}`);
        
        // 准备保存的数据
        const transactionData = {
          transaction_type: transactionType,
          transaction_time: record.transaction_time || new Date().toISOString(),
          item_name: itemName,
          quantity: quantity,
          price: price,
          total_amount: totalAmount,
          fee: fee,
          platform: record.platform || '',
          note: record.note || '通过OCR导入'
        };
        
        // 确保交易时间格式符合MySQL要求
        if (transactionData.transaction_time && typeof transactionData.transaction_time === 'string') {
          // 将ISO格式(2025-05-21T07:54:54.159Z)转换为MySQL格式(2025-05-21 07:54:54)
          transactionData.transaction_time = transactionData.transaction_time.replace('T', ' ').replace(/\.\d+Z$/, '');
          logger.info(`转换后的日期格式: ${transactionData.transaction_time}`);
        }
        
        // 保存交易记录
        logger.info(`准备保存交易记录: ${JSON.stringify(transactionData)}`);
        
        const startTime = Date.now();
        const saveResult = await db.save_transaction(transactionData);
        const endTime = Date.now();
        logger.info(`保存操作耗时: ${endTime - startTime}ms`);
        
        if (saveResult) {
          logger.info(`交易记录保存成功: ${itemName}, ID=${saveResult.insertId || '未返回'}`);
          
          // 记录成功处理的记录
          results.success++;
          results.processed_records.push({
            id: saveResult.insertId,
            transaction_type: transactionType,
            item_name: itemName,
            quantity: quantity,
            status: 'success'
          });
          logger.info(`成功导入记录: ${transactionType} ${itemName}, 数量: ${quantity}`);
        } else {
          results.failed++;
          const errorMsg = `保存交易记录失败: ${itemName}`;
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
    
    logger.info(`OCR交易导入处理完成，成功: ${results.success}, 失败: ${results.failed}`);
    if (results.errors.length > 0) {
      logger.info(`导入错误: ${JSON.stringify(results.errors)}`);
    }
    
    res.status(200).json({
      success: true,
      message: `导入完成: 成功${results.success}条，失败${results.failed}条`,
      results
    });
  } catch (error) {
    logger.error(`导入交易记录失败: ${error.message}`);
    logger.error(`导入失败详细错误: ${error.stack || '无堆栈信息'}`);
    res.status(500).json({
      success: false,
      message: '导入交易记录失败',
      error: error.message
    });
  }
};

/**
 * 更新交易记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.updateTransaction = async (req, res) => {
  try {
    const { id } = req.params;
    
    // 首先获取现有记录
    const query = "SELECT * FROM transactions WHERE id = ?";
    const existingRecord = await db.fetchOne(query, [id]);
    
    if (!existingRecord) {
      return res.status(404).json({
        success: false,
        message: '交易记录不存在'
      });
    }
    
    // 验证和处理必要字段
    if (!req.body.transaction_type || !req.body.transaction_type.trim()) {
      return res.status(400).json({
        success: false,
        message: '交易类型不能为空'
      });
    }
    
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
    
    if (!req.body.price || isNaN(Number(req.body.price)) || Number(req.body.price) <= 0) {
      return res.status(400).json({
        success: false,
        message: '价格必须为正数'
      });
    }
    
    // 准备更新数据
    const transactionType = req.body.transaction_type.trim();
    const itemName = req.body.item_name.trim();
    const quantity = Number(req.body.quantity);
    const price = Number(req.body.price);
    const fee = Number(req.body.fee || 0);
    const totalAmount = (quantity * price) - fee;
    const platform = req.body.platform || '';
    const note = req.body.note || '';
    
    // 更新记录
    const result = await db.update_transaction(id, {
      transaction_type: transactionType,
      item_name: itemName,
      quantity: quantity,
      price: price,
      total_amount: totalAmount,
      fee: fee,
      platform: platform,
      note: note
    });
    
    if (result) {
      res.status(200).json({
        success: true,
        message: '交易记录更新成功'
      });
    } else {
      res.status(400).json({
        success: false,
        message: '交易记录更新失败'
      });
    }
  } catch (error) {
    logger.error(`更新交易记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '更新交易记录失败',
      error: error.message
    });
  }
};

/**
 * 删除交易记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.deleteTransaction = async (req, res) => {
  try {
    const { id } = req.params;
    
    // 首先检查记录是否存在
    const query = "SELECT * FROM transactions WHERE id = ?";
    const record = await db.fetchOne(query, [id]);
    
    if (!record) {
      return res.status(404).json({
        success: false,
        message: '交易记录不存在'
      });
    }
    
    // 删除记录
    const result = await db.delete_transaction(id);
    
    if (result) {
      res.status(200).json({
        success: true,
        message: '交易记录删除成功'
      });
    } else {
      res.status(400).json({
        success: false,
        message: '交易记录删除失败'
      });
    }
  } catch (error) {
    logger.error(`删除交易记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '删除交易记录失败',
      error: error.message
    });
  }
}; 