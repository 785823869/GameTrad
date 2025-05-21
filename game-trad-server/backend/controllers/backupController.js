const path = require('path');
const fs = require('fs');
const { PythonShell } = require('python-shell');
const logger = require('../utils/logger');

// 备份设置
let backupSettings = {
  auto_backup_enabled: false,
  backup_frequency: 'daily',
  backup_time: '03:00',
  keep_days: 30,
  email_notification: true,
  backup_method: 'sql' // 'sql' 或 'file'
};

// 尝试从配置文件中加载备份设置
try {
  const settingsPath = path.join(__dirname, '../../config/backup_settings.json');
  if (fs.existsSync(settingsPath)) {
    const savedSettings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
    backupSettings = { ...backupSettings, ...savedSettings };
    logger.info('已加载备份设置');
  }
} catch (error) {
  logger.error(`加载备份设置失败: ${error.message}`);
}

// 获取备份列表
exports.getBackupList = async (req, res) => {
  try {
    // 使用Node.js文件系统，直接读取备份目录
    const backupDir = path.join(process.cwd(), 'database_backups');
    
    // 确保备份目录存在
    if (!fs.existsSync(backupDir)) {
      fs.mkdirSync(backupDir, { recursive: true });
      logger.info(`已创建备份目录: ${backupDir}`);
      return res.json({
        success: true,
        backups: []
      });
    }
    
    // 获取所有备份文件
    const files = fs.readdirSync(backupDir);
    
    // 过滤并格式化备份文件信息
    const backups = files
      .filter(file => file.startsWith('backup_') && (file.endsWith('.sql') || file.endsWith('.db') || file.endsWith('.json')))
      .map(file => {
        const filePath = path.join(backupDir, file);
        const stats = fs.statSync(filePath);
        
        // 从文件名解析时间
        let createdAt = null;
        try {
          const timeMatch = file.match(/backup_(\d{8})_(\d{6})/);
          if (timeMatch) {
            const dateStr = timeMatch[1];
            const timeStr = timeMatch[2];
            createdAt = `${dateStr.slice(0,4)}-${dateStr.slice(4,6)}-${dateStr.slice(6,8)} ${timeStr.slice(0,2)}:${timeStr.slice(2,4)}:${timeStr.slice(4,6)}`;
          }
        } catch (err) {
          logger.warn(`无法解析备份文件日期: ${file}`);
          createdAt = new Date(stats.mtime).toLocaleString();
        }
        
        // 确定备份类型
        let backupType = 'unknown';
        if (file.endsWith('.sql')) backupType = 'sql';
        else if (file.endsWith('.db')) backupType = 'file';
        else if (file.endsWith('.json')) backupType = 'json';
        
        // 格式化文件大小
        const sizeBytes = stats.size;
        let sizeFormatted = '';
        if (sizeBytes < 1024) {
          sizeFormatted = `${sizeBytes} B`;
        } else if (sizeBytes < 1024 * 1024) {
          sizeFormatted = `${(sizeBytes / 1024).toFixed(2)} KB`;
        } else if (sizeBytes < 1024 * 1024 * 1024) {
          sizeFormatted = `${(sizeBytes / (1024 * 1024)).toFixed(2)} MB`;
        } else {
          sizeFormatted = `${(sizeBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
        }
        
        return {
          filename: file,
          created_at: createdAt || new Date(stats.mtime).toLocaleString(),
          size: sizeBytes,
          size_formatted: sizeFormatted,
          path: filePath,
          type: backupType
        };
      });
    
    // 按时间倒序排序
    backups.sort((a, b) => {
      return new Date(b.created_at) - new Date(a.created_at);
    });
    
    logger.info(`已获取${backups.length}个备份文件`);
    return res.json({
      success: true,
      backups: backups
    });
  } catch (error) {
    logger.error(`获取备份列表异常: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `获取备份列表失败: ${error.message}`
    });
  }
};

// 获取备份设置
exports.getBackupSettings = async (req, res) => {
  try {
    return res.json({
      success: true,
      settings: backupSettings
    });
  } catch (error) {
    logger.error(`获取备份设置失败: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `获取备份设置失败: ${error.message}`
    });
  }
};

// 保存备份设置
exports.saveBackupSettings = async (req, res) => {
  try {
    const newSettings = req.body;
    
    // 验证设置数据
    if (typeof newSettings.auto_backup_enabled !== 'boolean') {
      return res.status(400).json({
        success: false,
        message: '无效的自动备份设置'
      });
    }
    
    // 更新设置
    backupSettings = {
      ...backupSettings,
      auto_backup_enabled: newSettings.auto_backup_enabled,
      backup_frequency: newSettings.backup_frequency || 'daily',
      backup_time: newSettings.backup_time || '03:00',
      keep_days: parseInt(newSettings.keep_days) || 30,
      email_notification: newSettings.email_notification !== false,
      backup_method: newSettings.backup_method === 'file' ? 'file' : 'sql'
    };
    
    // 保存到配置文件
    const configDir = path.join(__dirname, '../../config');
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
    
    fs.writeFileSync(
      path.join(configDir, 'backup_settings.json'),
      JSON.stringify(backupSettings, null, 2),
      'utf8'
    );
    
    logger.info('已保存备份设置');
    
    return res.json({
      success: true,
      message: '备份设置已保存',
      settings: backupSettings
    });
  } catch (error) {
    logger.error(`保存备份设置失败: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `保存备份设置失败: ${error.message}`
    });
  }
};

// 创建新备份
exports.createBackup = async (req, res) => {
  try {
    // 获取Socket.IO实例
    const io = req.app.get('io');
    const backupId = Date.now(); // 生成唯一的备份ID
    
    // 解析请求参数，添加性能选项
    const { compression = false, incremental = false } = req.body;
    
    // 根据用户选择的方法确定备份类型和日志描述
    let backupMethod = '';
    let backupType = '';
    
    if (backupSettings.backup_method === 'file') {
      backupMethod = '文件备份';
      backupType = 'db';
    } else if (backupSettings.backup_method === 'sql') {
      backupMethod = 'SQL备份';
      backupType = 'sql';
    } else {
      backupMethod = 'JSON备份';
      backupType = 'json';
    }
    
    // 向前端发送初始备份状态
    io.emit('backup:start', {
      id: backupId,
      method: backupMethod,
      progress: 0,
      status: 'starting',
      message: `开始${backupMethod}进程...`,
      logs: [`[${new Date().toLocaleTimeString()}] 开始创建数据库备份 (${backupMethod})...`]
    });
    
    logger.info(`开始创建数据库备份 (${backupMethod})...`);
    
    // 确保备份目录存在
    const backupDir = path.join(process.cwd(), 'database_backups');
    if (!fs.existsSync(backupDir)) {
      fs.mkdirSync(backupDir, { recursive: true });
      const logMessage = `已创建备份目录: ${backupDir}`;
      io.emit('backup:log', { id: backupId, message: logMessage });
      logger.info(logMessage);
    }
    
    // 生成备份文件名
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '_').split('.')[0];
    const backupFileName = `backup_${timestamp.replace(/_/g, '')}`;
    const fileExt = `.${backupType}`;
    const backupFilePath = path.join(backupDir, backupFileName + fileExt);
    
    // 更新进度为10%
    io.emit('backup:progress', { 
      id: backupId, 
      progress: 10,
      status: 'preparing',
      message: '准备备份中...'
    });
    
    // 根据备份方法执行不同的备份操作
    if (backupSettings.backup_method === 'file') {
      // 文件备份方式 - 直接复制数据库文件
      try {
        // 更新进度为20%
        io.emit('backup:progress', { 
          id: backupId, 
          progress: 20,
          status: 'locating',
          message: '定位数据库文件...'
        });
        
        // 确定数据库文件路径 - 假设使用SQLite数据库，文件位于项目根目录
        const dbFilePath = path.join(process.cwd(), '..', 'gametrad.db');
        
        if (!fs.existsSync(dbFilePath)) {
          const errorMsg = `找不到数据库文件: ${dbFilePath}`;
          io.emit('backup:error', { 
            id: backupId, 
            error: errorMsg
          });
          return res.status(404).json({
            success: false,
            message: errorMsg
          });
        }
        
        // 更新进度为40%
        io.emit('backup:progress', { 
          id: backupId, 
          progress: 40,
          status: 'copying',
          message: '复制数据库文件中...'
        });
        
        // 复制数据库文件
        fs.copyFileSync(dbFilePath, backupFilePath);
        
        // 如果启用了压缩，则压缩备份文件
        if (compression) {
          io.emit('backup:progress', { 
            id: backupId, 
            progress: 60,
            status: 'compressing',
            message: '压缩备份文件中...'
          });
          
          // 这里应该有压缩文件的代码，例如使用zlib等库
          // 简化版实现，实际需要实现文件压缩
          const logMessage = `压缩备份文件已启用，但功能尚未实现`;
          io.emit('backup:log', { id: backupId, message: logMessage });
          logger.warn(logMessage);
        }
        
        // 更新进度为80%
        io.emit('backup:progress', { 
          id: backupId, 
          progress: 80,
          status: 'finalizing',
          message: '完成备份文件...'
        });
        
        // 获取文件大小并格式化
        const sizeBytes = fs.statSync(backupFilePath).size;
        let sizeFormatted = '';
        if (sizeBytes < 1024) {
          sizeFormatted = `${sizeBytes} B`;
        } else if (sizeBytes < 1024 * 1024) {
          sizeFormatted = `${(sizeBytes / 1024).toFixed(2)} KB`;
        } else if (sizeBytes < 1024 * 1024 * 1024) {
          sizeFormatted = `${(sizeBytes / (1024 * 1024)).toFixed(2)} MB`;
        } else {
          sizeFormatted = `${(sizeBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
        }
        
        // 更新进度为100%
        io.emit('backup:progress', { 
          id: backupId, 
          progress: 100,
          status: 'completed',
          message: `完成文件备份，大小: ${sizeFormatted}`
        });
        
        const successMessage = `文件备份成功: ${backupFilePath} (${sizeFormatted})`;
        io.emit('backup:log', { id: backupId, message: successMessage });
        logger.info(successMessage);
        
        io.emit('backup:complete', { 
          id: backupId, 
          path: backupFilePath,
          size: sizeBytes,
          size_formatted: sizeFormatted
        });
        
        return res.json({
          success: true,
          message: `数据库文件备份成功，大小: ${sizeFormatted}`,
          backup_path: backupFilePath
        });
      } catch (err) {
        logger.error(`文件备份失败: ${err.message}`);
        io.emit('backup:error', { 
          id: backupId, 
          error: `备份失败: ${err.message}`
        });
        
        return res.status(500).json({
          success: false,
          message: `文件备份失败: ${err.message}`
        });
      }
    } else if (backupSettings.backup_method === 'sql') {
      // SQL备份方式 - 使用SQL导出
      try {
        // 更新进度为20%
        io.emit('backup:progress', { 
          id: backupId, 
          progress: 20,
          status: 'preparing',
          message: '准备SQL导出...'
        });
        
        // 使用Python脚本执行SQL导出
        const method = 'backup';
        
        const options = {
          mode: 'json',
          pythonPath: 'python', // 根据系统环境可能需要调整
          pythonOptions: ['-u'], // 不缓冲 stdout 和 stderr
          scriptPath: path.join(__dirname, '../../..'), // 项目根目录
          args: [method, backupFileName]
        };

        const logMessage = `开始SQL备份数据库...`;
        io.emit('backup:log', { id: backupId, message: logMessage });
        logger.info(logMessage);
        
        // 更新进度为40%
        io.emit('backup:progress', { 
          id: backupId, 
          progress: 40,
          status: 'exporting',
          message: '导出SQL数据中...'
        });
        
        // 使用Promise包装PythonShell调用
        const pythonResult = await new Promise((resolve, reject) => {
          PythonShell.run('src/utils/db_backup_connector.py', options, (err, results) => {
            if (err) {
              reject(err);
              return;
            }
            resolve(results);
          });
        });
        
        // 处理Python脚本返回的结果
        if (pythonResult && pythonResult.length > 0) {
          const result = pythonResult[0];
          if (result.success) {
            // 更新进度为80%
            io.emit('backup:progress', { 
              id: backupId, 
              progress: 80,
              status: 'finalizing',
              message: '完成SQL备份...'
            });
            
            const sizeBytes = fs.statSync(backupFilePath).size;
            let sizeFormatted = '';
            if (sizeBytes < 1024) {
              sizeFormatted = `${sizeBytes} B`;
            } else if (sizeBytes < 1024 * 1024) {
              sizeFormatted = `${(sizeBytes / 1024).toFixed(2)} KB`;
            } else if (sizeBytes < 1024 * 1024 * 1024) {
              sizeFormatted = `${(sizeBytes / (1024 * 1024)).toFixed(2)} MB`;
            } else {
              sizeFormatted = `${(sizeBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
            }
            
            // 更新进度为100%
            io.emit('backup:progress', { 
              id: backupId, 
              progress: 100,
              status: 'completed',
              message: `完成SQL备份，大小: ${sizeFormatted}`
            });
            
            const successMessage = `SQL备份成功: ${backupFilePath} (${sizeFormatted})`;
            io.emit('backup:log', { id: backupId, message: successMessage });
            logger.info(successMessage);
            
            io.emit('backup:complete', { 
              id: backupId, 
              path: backupFilePath,
              size: sizeBytes,
              size_formatted: sizeFormatted
            });
            
            return res.json({
              success: true,
              message: `数据库SQL备份成功，大小: ${sizeFormatted}`,
              backup_path: backupFilePath
            });
          } else {
            const errorMessage = `SQL备份失败: ${result.message}`;
            io.emit('backup:error', { 
              id: backupId, 
              error: errorMessage
            });
            logger.error(errorMessage);
            
            return res.status(500).json({
              success: false,
              message: errorMessage
            });
          }
        } else {
          // 如果Python脚本没有输出结果，我们回退到JSON备份
          const warningMessage = `SQL备份过程无返回结果，回退到JSON备份...`;
          io.emit('backup:log', { id: backupId, message: warningMessage });
          logger.warn(warningMessage);
          
          // 继续执行JSON备份（下面的else代码块）
          backupSettings.backup_method = 'json';
          backupType = 'json';
          backupMethod = 'JSON备份';
          const jsonFilePath = path.join(backupDir, backupFileName + '.json');
          
          // 调用fallbackToJsonBackup函数
          return await fallbackToJsonBackup(req, res, {
            backupId,
            backupFileName,
            backupDir,
            io,
            compression
          });
        }
      } catch (err) {
        const errorMessage = `SQL备份异常: ${err.message}，回退到JSON备份...`;
        io.emit('backup:log', { id: backupId, message: errorMessage });
        logger.error(errorMessage);
        
        // 回退到JSON备份
        backupSettings.backup_method = 'json';
        backupType = 'json';
        backupMethod = 'JSON备份';
        const jsonFilePath = path.join(backupDir, backupFileName + '.json');
        
        // 调用fallbackToJsonBackup函数
        return await fallbackToJsonBackup(req, res, {
          backupId,
          backupFileName,
          backupDir,
          io,
          compression
        });
      }
    } else {
      // JSON备份方式 - 导出数据表为JSON格式
      return await executeJsonBackup(req, res, {
        backupId, 
        backupFileName,
        backupFilePath,
        backupDir,
        io,
        compression,
        incremental
      });
    }
  } catch (error) {
    logger.error(`创建备份异常: ${error.message}`);
    
    // 尝试获取Socket.IO实例发送错误，但要处理可能的错误
    try {
      const io = req.app.get('io');
      if (io) {
        io.emit('backup:error', { 
          id: Date.now(), 
          error: `创建备份失败: ${error.message}`
        });
      }
    } catch (socketError) {
      logger.error(`发送错误通知失败: ${socketError.message}`);
    }
    
    return res.status(500).json({
      success: false,
      message: `创建备份失败: ${error.message}`
    });
  }
};

// 执行JSON备份的辅助函数
async function executeJsonBackup(req, res, options) {
  const { 
    backupId, 
    backupFileName = `backup_${Date.now()}`,
    backupFilePath = null,
    backupDir = path.join(process.cwd(), 'database_backups'),
    io = req.app.get('io'),
    compression = false,
    incremental = false
  } = options;
  
  try {
    // 更新进度为20%
    io.emit('backup:progress', { 
      id: backupId, 
      progress: 20,
      status: 'collecting',
      message: '收集数据库表信息...'
    });
    
    // 假设我们有一个数据库服务模块用于获取所有数据
    // 这里是一个简单的模拟示例，实际应用中需要根据您的数据库连接方式调整
    const tables = ['inventory', 'stock_in', 'stock_out', 'transactions', 'recipes']; // 根据实际表名调整
    const backupData = {
      timestamp: new Date().toISOString(),
      version: '1.0',
      tables: {}
    };
    
    // 从文件系统中获取各表数据
    // 这只是一个示例，您需要根据实际数据存储方式调整此代码
    const dataDir = path.join(process.cwd(), '..', 'data');
    
    // 更新进度为30%
    io.emit('backup:progress', { 
      id: backupId, 
      progress: 30,
      status: 'reading',
      message: '读取数据表...'
    });
    
    if (fs.existsSync(dataDir)) {
      const files = fs.readdirSync(dataDir);
      
      // 计算每个表的进度增量
      const progressPerTable = 50 / Math.max(files.length, 1);
      let currentProgress = 30;
      
      for (const file of files) {
        if (file.endsWith('.json')) {
          try {
            const tableName = file.replace('.json', '');
            
            // 更新进度和日志
            currentProgress += progressPerTable;
            io.emit('backup:progress', { 
              id: backupId, 
              progress: Math.min(80, Math.round(currentProgress)),
              status: 'processing',
              message: `处理表: ${tableName}...`
            });
            
            const tableData = JSON.parse(fs.readFileSync(path.join(dataDir, file), 'utf8'));
            backupData.tables[tableName] = tableData;
            
            const logMessage = `已备份表: ${tableName}`;
            io.emit('backup:log', { id: backupId, message: logMessage });
            logger.info(logMessage);
          } catch (err) {
            const errorMessage = `备份表 ${file} 失败: ${err.message}`;
            io.emit('backup:log', { id: backupId, message: errorMessage });
            logger.error(errorMessage);
          }
        }
      }
    } else {
      const warningMessage = `数据目录不存在: ${dataDir}`;
      io.emit('backup:log', { id: backupId, message: warningMessage });
      logger.warn(warningMessage);
    }
    
    // 更新进度为90%
    io.emit('backup:progress', { 
      id: backupId, 
      progress: 90,
      status: 'saving',
      message: '保存备份文件...'
    });
    
    // 确保备份文件路径存在
    const finalBackupPath = backupFilePath || path.join(backupDir, `${backupFileName}.json`);
    
    // 将备份数据写入文件
    fs.writeFileSync(finalBackupPath, JSON.stringify(backupData, null, 2), 'utf8');
    
    // 如果启用了压缩，则压缩备份文件
    if (compression) {
      io.emit('backup:progress', { 
        id: backupId, 
        progress: 95,
        status: 'compressing',
        message: '压缩备份文件中...'
      });
      
      // 这里应该有压缩文件的代码，例如使用zlib等库
      // 简化版实现，实际需要实现文件压缩
      const logMessage = `压缩备份文件已启用，但功能尚未实现`;
      io.emit('backup:log', { id: backupId, message: logMessage });
      logger.warn(logMessage);
    }
    
    // 获取文件大小并格式化
    const sizeBytes = fs.statSync(finalBackupPath).size;
    let sizeFormatted = '';
    if (sizeBytes < 1024) {
      sizeFormatted = `${sizeBytes} B`;
    } else if (sizeBytes < 1024 * 1024) {
      sizeFormatted = `${(sizeBytes / 1024).toFixed(2)} KB`;
    } else if (sizeBytes < 1024 * 1024 * 1024) {
      sizeFormatted = `${(sizeBytes / (1024 * 1024)).toFixed(2)} MB`;
    } else {
      sizeFormatted = `${(sizeBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
    
    // 更新进度为100%
    io.emit('backup:progress', { 
      id: backupId, 
      progress: 100,
      status: 'completed',
      message: `完成JSON备份，大小: ${sizeFormatted}`
    });
    
    const successMessage = `JSON备份成功: ${finalBackupPath} (${sizeFormatted})`;
    io.emit('backup:log', { id: backupId, message: successMessage });
    logger.info(successMessage);
    
    io.emit('backup:complete', { 
      id: backupId, 
      path: finalBackupPath,
      size: sizeBytes,
      size_formatted: sizeFormatted
    });
    
    return res.json({
      success: true,
      message: `数据库JSON备份成功，大小: ${sizeFormatted}`,
      backup_path: finalBackupPath
    });
  } catch (err) {
    const errorMessage = `JSON备份失败: ${err.message}`;
    io.emit('backup:error', { 
      id: backupId, 
      error: errorMessage
    });
    logger.error(errorMessage);
    
    return res.status(500).json({
      success: false,
      message: errorMessage
    });
  }
}

// SQL备份失败时回退到JSON备份
async function fallbackToJsonBackup(req, res, options) {
  const { 
    backupId, 
    backupFileName,
    backupDir,
    io = req.app.get('io'),
    compression
  } = options;
  
  // 记录回退日志
  io.emit('backup:log', { id: backupId, message: '正在回退到JSON备份...' });
  
  // 更新进度
  io.emit('backup:progress', { 
    id: backupId, 
    progress: 40,
    status: 'fallback',
    message: '回退到JSON备份中...'
  });
  
  // 调用JSON备份函数
  return await executeJsonBackup(req, res, {
    backupId,
    backupFileName,
    backupFilePath: path.join(backupDir, `${backupFileName}.json`),
    backupDir,
    io,
    compression
  });
}

// 恢复备份
exports.restoreBackup = async (req, res) => {
  try {
    const { filename } = req.body;
    
    if (!filename) {
      return res.status(400).json({
        success: false,
        message: '缺少备份文件名'
      });
    }
    
    // 安全检查：确保文件名只包含安全字符
    // 支持多种备份文件格式
    if (!/^backup_\d{14}\.(sql|db|json)$/.test(filename)) {
      return res.status(400).json({
        success: false,
        message: '无效的备份文件名'
      });
    }
    
    // 根据文件扩展名确定恢复方法
    const isFileBackup = filename.endsWith('.db');
    const isJsonBackup = filename.endsWith('.json');
    
    // 获取备份文件路径
    const backupDir = path.join(process.cwd(), 'database_backups');
    const backupPath = path.join(backupDir, filename);
    
    // 检查备份文件是否存在
    if (!fs.existsSync(backupPath)) {
      return res.status(404).json({
        success: false,
        message: '备份文件不存在'
      });
    }
    
    if (isFileBackup) {
      // 文件备份恢复 - 直接复制文件
      try {
        // 确定数据库文件路径
        const dbFilePath = path.join(process.cwd(), '..', 'gametrad.db');
        
        // 如果当前数据库文件存在，创建备份
        const tempBackupPath = `${dbFilePath}.temp_backup`;
        if (fs.existsSync(dbFilePath)) {
          fs.copyFileSync(dbFilePath, tempBackupPath);
          logger.info(`已创建临时备份: ${tempBackupPath}`);
        }
        
        try {
          // 复制备份文件到数据库文件位置
          fs.copyFileSync(backupPath, dbFilePath);
          logger.info(`文件备份恢复成功: ${filename}`);
          
          // 恢复成功后，删除临时备份
          if (fs.existsSync(tempBackupPath)) {
            fs.unlinkSync(tempBackupPath);
          }
          
          return res.json({
            success: true,
            message: '数据库文件恢复成功'
          });
        } catch (err) {
          // 恢复失败，尝试还原原始文件
          logger.error(`文件恢复失败: ${err.message}`);
          
          if (fs.existsSync(tempBackupPath)) {
            fs.copyFileSync(tempBackupPath, dbFilePath);
            fs.unlinkSync(tempBackupPath);
            logger.info('已还原原始数据库文件');
          }
          
          return res.status(500).json({
            success: false,
            message: `恢复失败: ${err.message}`
          });
        }
      } catch (err) {
        logger.error(`文件恢复过程出错: ${err.message}`);
        return res.status(500).json({
          success: false,
          message: `恢复失败: ${err.message}`
        });
      }
    } else if (isJsonBackup) {
      // JSON备份恢复
      try {
        // 读取备份文件
        const backupData = JSON.parse(fs.readFileSync(backupPath, 'utf8'));
        
        // 检查备份数据格式
        if (!backupData.tables || typeof backupData.tables !== 'object') {
          return res.status(400).json({
            success: false,
            message: '无效的备份数据格式'
          });
        }
        
        // 确定数据目录
        const dataDir = path.join(process.cwd(), '..', 'data');
        if (!fs.existsSync(dataDir)) {
          fs.mkdirSync(dataDir, { recursive: true });
          logger.info(`已创建数据目录: ${dataDir}`);
        }
        
        // 恢复各表数据
        const tables = Object.keys(backupData.tables);
        for (const tableName of tables) {
          try {
            const tableData = backupData.tables[tableName];
            const tableFilePath = path.join(dataDir, `${tableName}.json`);
            
            // 如果文件已存在，创建临时备份
            if (fs.existsSync(tableFilePath)) {
              const tempPath = `${tableFilePath}.bak`;
              fs.copyFileSync(tableFilePath, tempPath);
            }
            
            // 写入恢复的数据
            fs.writeFileSync(tableFilePath, JSON.stringify(tableData, null, 2), 'utf8');
            logger.info(`已恢复表: ${tableName}`);
          } catch (err) {
            logger.error(`恢复表 ${tableName} 数据失败: ${err.message}`);
          }
        }
        
        logger.info(`JSON备份恢复成功: ${filename}`);
        return res.json({
          success: true,
          message: `成功恢复 ${tables.length} 个数据表`
        });
      } catch (err) {
        logger.error(`JSON恢复过程出错: ${err.message}`);
        return res.status(500).json({
          success: false,
          message: `恢复失败: ${err.message}`
        });
      }
    } else {
      // SQL备份恢复 - 仍然使用Python脚本
      try {
        const method = 'restore';
        
        const options = {
          mode: 'json',
          pythonPath: 'python', // 根据系统环境可能需要调整
          pythonOptions: ['-u'], // 不缓冲 stdout 和 stderr
          scriptPath: path.join(__dirname, '../../..'), // 项目根目录
          args: [method, filename]
        };

        logger.info(`开始从SQL备份恢复数据库: ${filename}`);
        
        // 使用Promise包装PythonShell调用，允许异步/等待
        const pythonResult = await new Promise((resolve, reject) => {
          PythonShell.run('src/utils/db_backup_connector.py', options, (err, results) => {
            if (err) {
              reject(err);
              return;
            }
            resolve(results);
          });
        });
        
        // 处理Python脚本返回的结果
        if (pythonResult && pythonResult.length > 0) {
          const result = pythonResult[0];
          if (result.success) {
            logger.info(`SQL备份恢复成功: ${result.message}`);
            return res.json({
              success: true,
              message: result.message || 'SQL备份恢复成功'
            });
          } else {
            logger.error(`SQL备份恢复失败: ${result.message}`);
            return res.status(500).json({
              success: false,
              message: result.message || 'SQL备份恢复失败'
            });
          }
        } else {
          logger.error('SQL备份恢复过程无返回结果');
          return res.status(500).json({
            success: false,
            message: 'SQL备份恢复过程无返回结果'
          });
        }
      } catch (err) {
        logger.error(`SQL备份恢复异常: ${err.message}`);
        return res.status(500).json({
          success: false,
          message: `SQL备份恢复失败: ${err.message}`
        });
      }
    }
  } catch (error) {
    logger.error(`恢复备份异常: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `恢复备份失败: ${error.message}`
    });
  }
};

// 删除备份
exports.deleteBackup = async (req, res) => {
  try {
    const { filename } = req.params;
    
    // 添加详细日志
    logger.info(`尝试删除备份文件: ${filename}`);
    logger.info(`请求参数: ${JSON.stringify(req.params)}`);
    
    if (!filename) {
      return res.status(400).json({
        success: false,
        message: '缺少备份文件名'
      });
    }
    
    // 安全检查：确保文件名只包含安全字符
    // 支持SQL备份文件、数据库文件和JSON文件
    if (!/^backup_\d{14}\.(sql|db|json)$/.test(filename)) {
      return res.status(400).json({
        success: false,
        message: '无效的备份文件名'
      });
    }
    
    const backupDir = path.join(process.cwd(), 'database_backups');
    const backupPath = path.join(backupDir, filename);
    
    if (!fs.existsSync(backupPath)) {
      return res.status(404).json({
        success: false,
        message: '备份文件不存在'
      });
    }
    
    fs.unlinkSync(backupPath);
    logger.info(`已删除备份文件: ${filename}`);
    
    return res.json({
      success: true,
      message: `已删除备份文件: ${filename}`
    });
  } catch (error) {
    logger.error(`删除备份失败: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `删除备份失败: ${error.message}`
    });
  }
};

// 下载备份
exports.downloadBackup = async (req, res) => {
  try {
    const { filename } = req.params;
    
    if (!filename) {
      return res.status(400).json({
        success: false,
        message: '缺少备份文件名'
      });
    }
    
    // 安全检查：确保文件名只包含安全字符
    // 支持SQL备份文件、数据库文件和JSON文件
    if (!/^backup_\d{14}\.(sql|db|json)$/.test(filename)) {
      return res.status(400).json({
        success: false,
        message: '无效的备份文件名'
      });
    }
    
    const backupDir = path.join(process.cwd(), 'database_backups');
    const backupPath = path.join(backupDir, filename);
    
    if (!fs.existsSync(backupPath)) {
      return res.status(404).json({
        success: false,
        message: '备份文件不存在'
      });
    }
    
    logger.info(`用户下载备份文件: ${filename}`);
    return res.download(backupPath);
  } catch (error) {
    logger.error(`下载备份失败: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `下载备份失败: ${error.message}`
    });
  }
};

// 清理旧备份
exports.cleanupOldBackups = async (req, res) => {
  try {
    const { keep_days } = req.body;
    const daysToKeep = parseInt(keep_days) || backupSettings.keep_days || 30;
    
    // 直接通过Node.js清理旧备份文件
    const backupDir = path.join(process.cwd(), 'database_backups');
    if (!fs.existsSync(backupDir)) {
      return res.json({
        success: true,
        message: '没有旧备份文件需要清理',
        deleted_count: 0,
        deleted_files: []
      });
    }
    
    // 计算截止日期
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
    
    // 获取所有备份文件
    const files = fs.readdirSync(backupDir);
    
    // 过滤出需要删除的文件
    const deletedFiles = [];
    let deletedCount = 0;
    
    for (const file of files) {
      if (!(file.startsWith('backup_') && (file.endsWith('.sql') || file.endsWith('.db') || file.endsWith('.json')))) {
        continue;
      }
      
      // 尝试从文件名解析日期
      try {
        const filePath = path.join(backupDir, file);
        const stats = fs.statSync(filePath);
        
        // 从文件名解析时间
        let fileDate = null;
        const timeMatch = file.match(/backup_(\d{14})/);
        if (timeMatch) {
          const dateTimeStr = timeMatch[1];
          const year = parseInt(dateTimeStr.slice(0, 4));
          const month = parseInt(dateTimeStr.slice(4, 6)) - 1; // 月份从0开始
          const day = parseInt(dateTimeStr.slice(6, 8));
          const hour = parseInt(dateTimeStr.slice(8, 10));
          const minute = parseInt(dateTimeStr.slice(10, 12));
          const second = parseInt(dateTimeStr.slice(12, 14));
          
          fileDate = new Date(year, month, day, hour, minute, second);
        } else {
          // 如果无法从文件名解析，使用文件修改时间
          fileDate = new Date(stats.mtime);
        }
        
        // 如果文件日期早于截止日期，删除该文件
        if (fileDate < cutoffDate) {
          fs.unlinkSync(filePath);
          deletedFiles.push(file);
          deletedCount++;
          logger.info(`已删除过期备份文件: ${file}`);
        }
      } catch (err) {
        logger.error(`处理备份文件时出错: ${err.message}`);
      }
    }
    
    logger.info(`已清理 ${deletedCount} 个过期备份文件`);
    return res.json({
      success: true,
      message: `已清理 ${deletedCount} 个过期备份文件`,
      deleted_count: deletedCount,
      deleted_files: deletedFiles
    });
  } catch (error) {
    logger.error(`清理旧备份异常: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `清理旧备份失败: ${error.message}`
    });
  }
}; 