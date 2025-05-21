/**
 * OCR规则管理控制器
 */
const logger = require('../utils/logger');
const db = require('../utils/db');
const { formidable } = require('formidable');
const path = require('path');
const fs = require('fs-extra');

// 定义规则类型对应的数据库表名
const RULE_TABLES = {
  'stock-in': 'ocr_rules_stock_in',
  'stock-out': 'ocr_rules_stock_out',
  'monitor': 'ocr_rules_monitor'
};

/**
 * 通用函数 - 获取规则列表
 * @param {string} type - 规则类型
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
const getRules = async (type, req, res) => {
  try {
    const table = RULE_TABLES[type];
    if (!table) {
      return res.status(400).json({
        success: false,
        message: '无效的规则类型'
      });
    }

    const query = `SELECT * FROM ${table} ORDER BY is_active DESC, name ASC`;
    const rules = await db.fetchAll(query);

    if (!rules) {
      return res.status(200).json({
        success: true,
        data: []
      });
    }

    res.status(200).json({
      success: true,
      data: rules
    });
  } catch (error) {
    logger.error(`获取${type}规则列表失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: `获取规则列表失败`,
      error: error.message
    });
  }
};

/**
 * 通用函数 - 获取单个规则
 * @param {string} type - 规则类型
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
const getRule = async (type, req, res) => {
  try {
    const table = RULE_TABLES[type];
    if (!table) {
      return res.status(400).json({
        success: false,
        message: '无效的规则类型'
      });
    }

    const { id } = req.params;
    const query = `SELECT * FROM ${table} WHERE id = ?`;
    const rule = await db.fetchOne(query, [id]);

    if (!rule) {
      return res.status(404).json({
        success: false,
        message: '规则不存在'
      });
    }

    res.status(200).json({
      success: true,
      data: rule
    });
  } catch (error) {
    logger.error(`获取${type}规则详情失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: `获取规则详情失败`,
      error: error.message
    });
  }
};

/**
 * 通用函数 - 添加规则
 * @param {string} type - 规则类型
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
const addRule = async (type, req, res) => {
  try {
    const table = RULE_TABLES[type];
    if (!table) {
      return res.status(400).json({
        success: false,
        message: '无效的规则类型'
      });
    }

    const { name, description, is_active, patterns } = req.body;

    // 验证必要字段
    if (!name || !patterns || !Array.isArray(patterns)) {
      return res.status(400).json({
        success: false,
        message: '名称和模式列表为必填字段'
      });
    }

    // 检验模式列表是否有效
    for (const pattern of patterns) {
      if (!pattern.field || !pattern.regex) {
        return res.status(400).json({
          success: false,
          message: '每个模式必须包含字段名和正则表达式'
        });
      }
    }

    // 将模式列表转换为JSON字符串
    const patternsJson = JSON.stringify(patterns);

    // 插入规则
    const query = `INSERT INTO ${table} (name, description, is_active, patterns, created_at, updated_at) VALUES (?, ?, ?, ?, NOW(), NOW())`;
    const result = await db.execute(query, [
      name,
      description || '',
      is_active === undefined ? true : Boolean(is_active),
      patternsJson
    ]);

    if (!result || !result.insertId) {
      return res.status(400).json({
        success: false,
        message: '添加规则失败'
      });
    }

    res.status(201).json({
      success: true,
      message: '规则添加成功',
      data: {
        id: result.insertId
      }
    });
  } catch (error) {
    logger.error(`添加${type}规则失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: `添加规则失败`,
      error: error.message
    });
  }
};

/**
 * 通用函数 - 更新规则
 * @param {string} type - 规则类型
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
const updateRule = async (type, req, res) => {
  try {
    const table = RULE_TABLES[type];
    if (!table) {
      return res.status(400).json({
        success: false,
        message: '无效的规则类型'
      });
    }

    const { id } = req.params;
    const { name, description, is_active, patterns } = req.body;

    // 验证必要字段
    if (!name || !patterns || !Array.isArray(patterns)) {
      return res.status(400).json({
        success: false,
        message: '名称和模式列表为必填字段'
      });
    }

    // 检验模式列表是否有效
    for (const pattern of patterns) {
      if (!pattern.field || !pattern.regex) {
        return res.status(400).json({
          success: false,
          message: '每个模式必须包含字段名和正则表达式'
        });
      }
    }

    // 将模式列表转换为JSON字符串
    const patternsJson = JSON.stringify(patterns);

    // 检查规则是否存在
    const checkQuery = `SELECT id FROM ${table} WHERE id = ?`;
    const checkResult = await db.fetchOne(checkQuery, [id]);

    if (!checkResult) {
      return res.status(404).json({
        success: false,
        message: '规则不存在'
      });
    }

    // 更新规则
    const query = `UPDATE ${table} SET name = ?, description = ?, is_active = ?, patterns = ?, updated_at = NOW() WHERE id = ?`;
    const result = await db.execute(query, [
      name,
      description || '',
      is_active === undefined ? true : Boolean(is_active),
      patternsJson,
      id
    ]);

    if (!result || result.affectedRows === 0) {
      return res.status(400).json({
        success: false,
        message: '更新规则失败'
      });
    }

    res.status(200).json({
      success: true,
      message: '规则更新成功'
    });
  } catch (error) {
    logger.error(`更新${type}规则失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: `更新规则失败`,
      error: error.message
    });
  }
};

/**
 * 通用函数 - 删除规则
 * @param {string} type - 规则类型
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
const deleteRule = async (type, req, res) => {
  try {
    const table = RULE_TABLES[type];
    if (!table) {
      return res.status(400).json({
        success: false,
        message: '无效的规则类型'
      });
    }

    const { id } = req.params;

    // 检查规则是否存在
    const checkQuery = `SELECT id FROM ${table} WHERE id = ?`;
    const checkResult = await db.fetchOne(checkQuery, [id]);

    if (!checkResult) {
      return res.status(404).json({
        success: false,
        message: '规则不存在'
      });
    }

    // 删除规则
    const query = `DELETE FROM ${table} WHERE id = ?`;
    const result = await db.execute(query, [id]);

    if (!result || result.affectedRows === 0) {
      return res.status(400).json({
        success: false,
        message: '删除规则失败'
      });
    }

    res.status(200).json({
      success: true,
      message: '规则删除成功'
    });
  } catch (error) {
    logger.error(`删除${type}规则失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: `删除规则失败`,
      error: error.message
    });
  }
};

/**
 * 通用函数 - 测试规则
 * @param {string} type - 规则类型
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
const testRule = async (type, req, res) => {
  try {
    // 确保临时目录存在
    const tempDir = path.join(__dirname, '../temp');
    fs.ensureDirSync(tempDir);
    
    // 使用formidable解析包含文件的表单数据
    const form = formidable({
      multiples: false,
      maxFileSize: 5 * 1024 * 1024, // 限制5MB
      uploadDir: tempDir,
      keepExtensions: true
    });

    form.parse(req, async (err, fields, files) => {
      if (err) {
        logger.error(`解析表单数据失败: ${err.message}`);
        return res.status(400).json({
          success: false,
          message: '解析表单数据失败',
          error: err.message
        });
      }

      try {
        // 确保有图片文件
        if (!files.image) {
          return res.status(400).json({
            success: false,
            message: '请上传图片文件'
          });
        }

        // 解析规则数据
        let rule;
        try {
          rule = JSON.parse(fields.rule);
        } catch (e) {
          return res.status(400).json({
            success: false,
            message: '规则数据格式无效',
            error: e.message
          });
        }

        // 验证规则数据
        if (!rule.patterns || !Array.isArray(rule.patterns)) {
          return res.status(400).json({
            success: false,
            message: '规则必须包含模式列表'
          });
        }

        // 暂存图片以处理OCR
        const imagePath = files.image.filepath || files.image.path || (files.image[0] && files.image[0].filepath);
        
        if (!imagePath) {
          return res.status(400).json({
            success: false,
            message: '无法获取上传图片的路径'
          });
        }
        
        // 调用OCR识别接口
        const { ocrRecognize, ocrRecognizeGameFormat } = require('../utils/ocrUtils');
        
        // 检查是否是游戏特定格式规则
        const isGameSpecificRule = rule.name && rule.name.includes('游戏特定');
        
        // 根据规则类型选择OCR识别方法
        const ocrResult = isGameSpecificRule 
          ? await ocrRecognizeGameFormat(imagePath) 
          : await ocrRecognize(imagePath);
        
        // 处理识别结果
        if (!ocrResult || !ocrResult.success) {
          return res.status(400).json({
            success: false,
            message: '图像识别失败',
            error: ocrResult?.error || '未知错误'
          });
        }

        const rawText = ocrResult.text || '';
        
        // 应用规则解析文本
        const parsed = {};
        
        // 处理多字段匹配（用于"游戏特定入库识别规则"）
        if (isGameSpecificRule) {
          // 收集所有数量和花费字段
          const quantityFields = [];
          const costFields = [];
          
          // 应用每个模式规则
          for (const pattern of rule.patterns) {
            try {
              if (!pattern.field || !pattern.regex) continue;
              
              const regex = new RegExp(pattern.regex, 'g'); // 使用g标志匹配所有出现
              const matches = [];
              let match;
              
              while ((match = regex.exec(rawText)) !== null) {
                if (match[pattern.group]) {
                  matches.push(match[pattern.group]);
                }
              }
              
              if (matches.length > 0) {
                // 如果是数量或花费字段，收集所有匹配
                if (pattern.field.startsWith('quantity_')) {
                  matches.forEach(m => quantityFields.push(parseInt(m, 10) || 0));
                } else if (pattern.field.startsWith('cost_')) {
                  matches.forEach(m => costFields.push(parseInt(m, 10) || 0));
                } else {
                  // 其他字段直接使用第一个匹配
                  parsed[pattern.field] = matches[0];
                }
              } else {
                // 如果没有匹配且非数量/花费字段，使用默认值
                if (!pattern.field.startsWith('quantity_') && !pattern.field.startsWith('cost_')) {
                  parsed[pattern.field] = pattern.default_value || '';
                }
              }
            } catch (e) {
              logger.error(`应用正则表达式失败: ${e.message}`);
              // 对于非数量/花费字段，使用默认值
              if (!pattern.field.startsWith('quantity_') && !pattern.field.startsWith('cost_')) {
                parsed[pattern.field] = pattern.default_value || '';
              }
            }
          }
          
          // 计算总数量和总花费
          if (quantityFields.length > 0) {
            parsed.quantity = quantityFields.reduce((a, b) => a + b, 0);
          }
          
          if (costFields.length > 0) {
            parsed.cost = costFields.reduce((a, b) => a + b, 0);
          }
          
          // 计算单价（如果有数量和花费）
          if (parsed.quantity && parsed.cost) {
            parsed.unit_price = Math.round(parsed.cost / parsed.quantity);
          }
        } else {
          // 标准规则处理：应用每个模式规则
          for (const pattern of rule.patterns) {
            try {
              if (!pattern.field || !pattern.regex) continue;
              
              const regex = new RegExp(pattern.regex);
              const match = regex.exec(rawText);
              
              // 如果匹配成功且指定的组存在，提取值
              if (match && match[pattern.group]) {
                parsed[pattern.field] = match[pattern.group];
              } else {
                // 使用默认值
                parsed[pattern.field] = pattern.default_value || '';
              }
            } catch (e) {
              logger.error(`应用正则表达式失败: ${e.message}`);
              // 使用默认值
              parsed[pattern.field] = pattern.default_value || '';
            }
          }
        }
        
        // 清理临时文件
        try {
          if (fs.existsSync(imagePath)) {
            fs.unlinkSync(imagePath);
          }
        } catch (err) {
          logger.error(`删除临时文件失败: ${err.message}`);
        }
        
        // 返回测试结果
        res.status(200).json({
          success: true,
          data: {
            rawText,
            parsed
          }
        });
      } catch (error) {
        // 清理临时文件（如果存在）
        if (files.image) {
          const filePath = files.image.filepath || files.image.path || (files.image[0] && files.image[0].filepath);
          if (filePath && fs.existsSync(filePath)) {
            try {
              fs.unlinkSync(filePath);
            } catch (err) {
              logger.error(`删除临时文件失败: ${err.message}`);
            }
          }
        }
        
        logger.error(`测试${type}规则失败: ${error.message}`);
        res.status(500).json({
          success: false,
          message: '测试规则失败',
          error: error.message
        });
      }
    });
  } catch (error) {
    logger.error(`处理${type}规则测试失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '处理规则测试失败',
      error: error.message
    });
  }
};

// 入库规则控制器
exports.getStockInRules = async (req, res) => {
  await getRules('stock-in', req, res);
};

exports.getStockInRule = async (req, res) => {
  await getRule('stock-in', req, res);
};

exports.addStockInRule = async (req, res) => {
  await addRule('stock-in', req, res);
};

exports.updateStockInRule = async (req, res) => {
  await updateRule('stock-in', req, res);
};

exports.deleteStockInRule = async (req, res) => {
  await deleteRule('stock-in', req, res);
};

exports.testStockInRule = async (req, res) => {
  await testRule('stock-in', req, res);
};

// 出库规则控制器
exports.getStockOutRules = async (req, res) => {
  await getRules('stock-out', req, res);
};

exports.getStockOutRule = async (req, res) => {
  await getRule('stock-out', req, res);
};

exports.addStockOutRule = async (req, res) => {
  await addRule('stock-out', req, res);
};

exports.updateStockOutRule = async (req, res) => {
  await updateRule('stock-out', req, res);
};

exports.deleteStockOutRule = async (req, res) => {
  await deleteRule('stock-out', req, res);
};

exports.testStockOutRule = async (req, res) => {
  await testRule('stock-out', req, res);
};

// 监控规则控制器
exports.getMonitorRules = async (req, res) => {
  await getRules('monitor', req, res);
};

exports.getMonitorRule = async (req, res) => {
  await getRule('monitor', req, res);
};

exports.addMonitorRule = async (req, res) => {
  await addRule('monitor', req, res);
};

exports.updateMonitorRule = async (req, res) => {
  await updateRule('monitor', req, res);
};

exports.deleteMonitorRule = async (req, res) => {
  await deleteRule('monitor', req, res);
};

exports.testMonitorRule = async (req, res) => {
  await testRule('monitor', req, res);
}; 