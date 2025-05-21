const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const db = require('../utils/db');

/**
 * 获取所有入库记录
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getStockIn = async (req, res) => {
  try {
    const stockInData = await db.get_stock_in();
    
    // 格式化数据
    const formattedData = stockInData.map(item => {
      // 打印每个对象的结构以便调试
      console.log("原始数据库记录:", JSON.stringify(item));
      
      // 检查数据结构，确保我们能够安全地访问
      if (!item) {
        logger.error("接收到空的数据库记录");
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
      
      // 如果物品名称仍然为空，使用一个占位值但不是"未知物品"
      if (!itemName) {
        logger.warn(`发现空物品名，记录ID: ${Array.isArray(item) ? item[0] : item.id}`);
        itemName = `物品_${Math.random().toString(36).substr(2, 5)}`;
      }
      
      // 根据数据库返回结果的格式(数组或对象)构建统一的输出格式
      const formattedItem = {
        id: Array.isArray(item) ? item[0] : (item.id || 0),
        item_name: itemName,
        transaction_time: formattedDate,
        quantity: Array.isArray(item) ? Number(item[3] || 0) : Number(item.quantity || 0),
        cost: Array.isArray(item) ? Number(item[4] || 0) : Number(item.cost || 0),
        avg_cost: Array.isArray(item) ? Number(item[5] || 0) : Number(item.avg_cost || 0),
        deposit: Array.isArray(item) ? Number(item[6] || 0) : Number(item.deposit || 0),
        note: Array.isArray(item) ? (item[7] || '') : (item.note || '')
      };
      
      return formattedItem;
    }).filter(item => item !== null); // 过滤掉任何无效的记录
    
    // 添加日志，记录返回的数据结构
    logger.info(`返回入库数据: ${formattedData.length} 条记录, 示例: ${JSON.stringify(formattedData.slice(0, 1))}`);
    
    res.status(200).json(formattedData);
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
    
    if (!req.body.cost || isNaN(Number(req.body.cost)) || Number(req.body.cost) <= 0) {
      return res.status(400).json({
        success: false,
        message: '花费必须为正数'
      });
    }
    
    // 准备入库记录数据
    const itemName = req.body.item_name.trim();
    const quantity = Number(req.body.quantity);
    const cost = Number(req.body.cost);
    // 确保均价总是从成本和数量计算得出
    const avgCost = quantity > 0 ? cost / quantity : 0;
    
    const stockInData = {
      item_name: itemName,
      transaction_time: new Date().toISOString(), // 使用当前时间
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
    const inventoryResult = await db.increase_inventory(itemName, quantity, avgCost);
    
    if (!inventoryResult) {
      logger.warn(`入库记录已保存，但更新库存失败: ${itemName}`);
    }
    
    res.status(200).json({
      success: true,
      message: '入库记录添加成功' + (inventoryResult ? '，库存已更新' : '，但库存未能更新')
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
        if (!record.item_name || !record.quantity || !record.cost) {
          results.failed++;
          results.errors.push(`记录缺少必需字段: ${JSON.stringify(record)}`);
          continue;
        }
        
        // 确保物品名称不为空
        const itemName = record.item_name || '未知物品';
        const quantity = parseFloat(record.quantity) || 0;
        const cost = parseFloat(record.cost) || 0;
        
        // 计算均价，如果数量为0则设为0避免除以零错误
        const avgCost = quantity > 0 ? (cost / quantity) : 0;
        
        const stockInData = {
          item_name: itemName,
          transaction_time: new Date().toISOString(), // 使用当前时间
          quantity: quantity,
          cost: cost,
          avg_cost: parseFloat(record.avg_cost) || avgCost,
          note: record.note || '通过OCR导入'
        };
        
        // 保存入库记录
        const saveSuccess = await db.save_stock_in(stockInData);
        
        if (saveSuccess) {
          // 更新库存
          const inventorySuccess = await db.increase_inventory(
            itemName, 
            quantity,
            avgCost
          );
          
          if (inventorySuccess) {
            results.success++;
          } else {
            results.failed++;
            results.errors.push(`更新库存失败: ${JSON.stringify(stockInData)}`);
          }
        } else {
          results.failed++;
          results.errors.push(`保存入库记录失败: ${JSON.stringify(stockInData)}`);
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
    logger.error(`导入入库记录失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '导入入库记录失败',
      error: error.message
    });
  }
}; 