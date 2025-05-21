const path = require('path');
const fs = require('fs');
const { PythonShell } = require('python-shell');
const logger = require('../utils/logger');

// 默认邮件配置
const defaultEmailConfig = {
  enabled: false,
  smtp_server: 'smtp.qq.com',
  smtp_port: 587,
  username: '',
  password: '',
  sender: 'GameTrad系统',
  recipients: [],
  retry_count: 3,
  retry_delay: 5,
  enable_log: true,
  log_days: 30,
  enable_daily_report: false,
  daily_report_time: '20:00'
};

// 存储配置的文件路径
const configPath = path.join(__dirname, '../../config/email_config.json');

// 加载邮件配置
const loadEmailConfig = () => {
  try {
    // 确保配置目录存在
    const configDir = path.dirname(configPath);
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }

    // 如果配置文件不存在，则使用默认配置并创建文件
    if (!fs.existsSync(configPath)) {
      fs.writeFileSync(configPath, JSON.stringify(defaultEmailConfig, null, 2), 'utf8');
      logger.info('已创建默认邮件配置文件');
      return { ...defaultEmailConfig };
    }

    // 读取配置文件
    const configData = fs.readFileSync(configPath, 'utf8');
    const config = JSON.parse(configData);
    logger.info('已加载邮件配置');
    
    // 合并默认配置和保存的配置，确保所有字段都存在
    return { ...defaultEmailConfig, ...config };
  } catch (error) {
    logger.error(`加载邮件配置失败: ${error.message}`);
    return { ...defaultEmailConfig };
  }
};

// 保存邮件配置
const saveEmailConfig = (config) => {
  try {
    // 确保配置目录存在
    const configDir = path.dirname(configPath);
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }

    // 写入配置文件
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf8');
    logger.info('已保存邮件配置');
    return true;
  } catch (error) {
    logger.error(`保存邮件配置失败: ${error.message}`);
    return false;
  }
};

// 获取邮件配置
exports.getEmailConfig = (req, res) => {
  try {
    const config = loadEmailConfig();
    return res.json({
      success: true,
      config: config
    });
  } catch (error) {
    logger.error(`获取邮件配置失败: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `获取邮件配置失败: ${error.message}`
    });
  }
};

// 保存邮件配置
exports.saveEmailConfig = (req, res) => {
  try {
    const newConfig = req.body;
    
    // 简单验证
    if (!newConfig || typeof newConfig !== 'object') {
      return res.status(400).json({
        success: false,
        message: '无效的配置数据'
      });
    }
    
    // 确保敏感字段正确格式化
    const formattedConfig = {
      ...newConfig,
      smtp_port: parseInt(newConfig.smtp_port) || 587,
      retry_count: parseInt(newConfig.retry_count) || 3,
      retry_delay: parseInt(newConfig.retry_delay) || 5,
      log_days: parseInt(newConfig.log_days) || 30,
      recipients: Array.isArray(newConfig.recipients) ? newConfig.recipients : []
    };
    
    // 保存配置
    const saved = saveEmailConfig(formattedConfig);
    
    if (saved) {
      return res.json({
        success: true,
        message: '邮件配置已保存',
        config: formattedConfig
      });
    } else {
      return res.status(500).json({
        success: false,
        message: '保存邮件配置失败'
      });
    }
  } catch (error) {
    logger.error(`保存邮件配置失败: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `保存邮件配置失败: ${error.message}`
    });
  }
};

// 测试邮件配置
exports.testEmailConfig = (req, res) => {
  try {
    const config = req.body;
    
    // 简单验证
    if (!config || typeof config !== 'object') {
      return res.status(400).json({
        success: false,
        message: '无效的配置数据'
      });
    }
    
    // 确保必要字段存在
    if (!config.smtp_server || !config.username || !config.password) {
      return res.status(400).json({
        success: false,
        message: '缺少必要的邮件服务器配置'
      });
    }
    
    // 如果没有收件人，则无法测试
    if (!Array.isArray(config.recipients) || config.recipients.length === 0) {
      return res.status(400).json({
        success: false,
        message: '请先添加至少一个收件人'
      });
    }
    
    // 使用Python脚本发送测试邮件
    const options = {
      mode: 'json',
      pythonPath: 'python', // 根据系统环境可能需要调整
      pythonOptions: ['-u'], // 不缓冲 stdout 和 stderr
      scriptPath: path.join(__dirname, '../../..'), // 项目根目录
      args: ['test_email'],
      jsonString: JSON.stringify(config)
    };
    
    logger.info('开始测试邮件配置...');
    
    // 直接返回成功响应，不等待Python脚本执行完成
    // 因为发送邮件可能需要一些时间，避免前端等待超时
    res.json({
      success: true,
      message: '测试邮件发送中，请检查邮箱'
    });
    
    // 在后台执行邮件发送测试
    PythonShell.run('src/utils/email_sender.py', options, (err, results) => {
      if (err) {
        logger.error(`测试邮件发送失败: ${err.message}`);
      } else if (results && results.length > 0) {
        const result = results[0];
        if (result.success) {
          logger.info('测试邮件发送成功');
        } else {
          logger.error(`测试邮件发送失败: ${result.message}`);
        }
      }
    });
    
  } catch (error) {
    logger.error(`测试邮件配置失败: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: `测试邮件配置失败: ${error.message}`
    });
  }
}; 