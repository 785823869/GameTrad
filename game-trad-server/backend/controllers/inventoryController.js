const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const db = require('../utils/db');
const dbHelper = require('../utils/dbHelper');

/**
 * 获取所有库存数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getInventory = async (req, res) => {
  try {
    const inventory = await db.getAllInventory();
    res.status(200).json(inventory);
  } catch (error) {
    logger.error(`获取库存数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取库存数据失败',
      error: error.message
    });
  }
};

/**
 * 重新计算库存数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.recalculateInventory = async (req, res) => {
  try {
    // 模拟Python客户端的重新计算库存功能
    await db.recalculateInventory();
    
    // 获取更新后的库存数据
    const inventory = await db.getAllInventory();
    
    res.status(200).json({
      success: true,
      message: '库存数据已重新计算',
      inventory
    });
  } catch (error) {
    logger.error(`重新计算库存数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '重新计算库存数据失败',
      error: error.message
    });
  }
};

/**
 * 导出库存数据
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.exportInventory = async (req, res) => {
  try {
    const { format = 'xlsx' } = req.query;
    const inventory = await db.getAllInventory();
    
    if (!inventory || inventory.length === 0) {
      return res.status(404).json({
        success: false,
        message: '没有库存数据可供导出'
      });
    }
    
    const exportsDir = path.join(__dirname, '../../uploads/exports');
    await fs.ensureDir(exportsDir);
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `inventory_${timestamp}.${format}`;
    const filePath = path.join(exportsDir, filename);
    
    if (format === 'csv') {
      // 生成CSV文件
      const header = '物品,库存数,总入库均价,保本均价,总出库均价,利润,利润率,成交利润额,库存价值\n';
      const rows = inventory.map(item => 
        `"${item.item_name}",${item.quantity},${item.avg_price},${item.break_even_price},${item.selling_price},${item.profit},${item.profit_rate},${item.total_profit},${item.inventory_value}`
      ).join('\n');
      
      await fs.writeFile(filePath, header + rows, 'utf8');
    } else {
      // 使用第三方库生成Excel文件
      const excel = require('excel4node');
      
      const wb = new excel.Workbook();
      const ws = wb.addWorksheet('库存数据');
      
      // 样式
      const headerStyle = wb.createStyle({
        font: {
          bold: true,
          size: 12
        },
        fill: {
          type: 'pattern',
          patternType: 'solid',
          fgColor: '#D9D9D9'
        }
      });
      
      // 添加表头
      const headers = ['物品', '库存数', '总入库均价', '保本均价', '总出库均价', '利润', '利润率', '成交利润额', '库存价值'];
      headers.forEach((header, i) => {
        ws.cell(1, i + 1).string(header).style(headerStyle);
      });
      
      // 添加数据行
      inventory.forEach((item, i) => {
        ws.cell(i + 2, 1).string(item.item_name);
        ws.cell(i + 2, 2).number(Number(item.quantity));
        ws.cell(i + 2, 3).number(Number(item.avg_price));
        ws.cell(i + 2, 4).number(Number(item.break_even_price));
        ws.cell(i + 2, 5).number(Number(item.selling_price));
        ws.cell(i + 2, 6).number(Number(item.profit));
        ws.cell(i + 2, 7).number(Number(item.profit_rate));
        ws.cell(i + 2, 8).number(Number(item.total_profit));
        ws.cell(i + 2, 9).number(Number(item.inventory_value));
      });
      
      // 写入文件
      await wb.write(filePath);
    }
    
    // 返回文件下载URL
    const downloadUrl = `/uploads/exports/${filename}`;
    
    res.status(200).json({
      success: true,
      message: '库存数据导出成功',
      downloadUrl,
      format
    });
  } catch (error) {
    logger.error(`导出库存数据失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '导出库存数据失败',
      error: error.message
    });
  }
};

/**
 * 获取零库存或负库存的物品
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getZeroInventoryItems = async (req, res) => {
  try {
    const zeroItems = await db.getZeroInventoryItems();
    res.status(200).json({
      success: true,
      count: zeroItems.length,
      data: zeroItems
    });
  } catch (error) {
    logger.error(`获取零库存物品失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取零库存物品失败',
      error: error.message
    });
  }
};

/**
 * 删除库存项目
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.deleteInventoryItem = async (req, res) => {
  try {
    const { id } = req.params;
    
    // 检查物品是否存在
    const itemExists = await db.checkInventoryItemExists(id);
    
    if (!itemExists) {
      return res.status(404).json({
        success: false,
        message: '物品不存在'
      });
    }
    
    // 删除物品
    await db.deleteInventoryItem(id);
    
    res.status(200).json({
      success: true,
      message: '物品已删除',
      id
    });
  } catch (error) {
    logger.error(`删除库存物品失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '删除库存物品失败',
      error: error.message
    });
  }
}; 