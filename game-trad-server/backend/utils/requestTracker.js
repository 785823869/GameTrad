const logger = require('./logger');

/**
 * 请求跟踪中间件
 * 记录所有API请求的详细信息，用于调试和性能监控
 */
function requestTracker(req, res, next) {
  // 获取或生成请求ID
  const requestId = req.headers['x-request-id'] || 
                   `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // 将请求ID添加到请求对象，方便后续使用
  req.requestId = requestId;
  
  // 记录请求开始时间
  const startTime = Date.now();
  
  // 备份原始的end方法
  const originalEnd = res.end;
  
  // 重写response.end方法，以便记录响应时间和状态
  res.end = function(chunk, encoding) {
    // 调用原始的end方法
    originalEnd.call(this, chunk, encoding);
    
    // 计算请求处理时间
    const endTime = Date.now();
    const processingTime = endTime - startTime;
    
    // 构建请求日志信息
    const requestPath = req.originalUrl || req.url;
    const requestMethod = req.method;
    const statusCode = res.statusCode;
    const contentLength = res.getHeader('content-length') || 
                         (chunk ? Buffer.byteLength(chunk) : 0);
    
    // 获取客户端IP
    const clientIp = req.headers['x-forwarded-for'] || 
                    req.connection.remoteAddress;
    
    // 获取用户代理信息
    const userAgent = req.headers['user-agent'] || 'Unknown';
    
    // 创建详细日志信息
    const logInfo = {
      requestId,
      timestamp: new Date().toISOString(),
      method: requestMethod,
      path: requestPath,
      status: statusCode,
      processingTime: `${processingTime}ms`,
      contentLength: `${contentLength} bytes`,
      clientIp,
      userAgent
    };
    
    // 根据不同的状态码使用不同的日志级别
    if (statusCode >= 500) {
      // 服务器错误
      logger.error(`请求失败 [${requestId}] ${requestMethod} ${requestPath} ${statusCode} - ${processingTime}ms`);
      logger.error(`详细信息: ${JSON.stringify(logInfo)}`);
      
      // 记录请求体信息，但排除敏感信息
      if (req.body) {
        const sanitizedBody = { ...req.body };
        // 移除敏感字段
        ['password', 'token', 'secret', 'key'].forEach(field => {
          if (sanitizedBody[field]) sanitizedBody[field] = '[REDACTED]';
        });
        logger.error(`请求体: ${JSON.stringify(sanitizedBody)}`);
      }
    } else if (statusCode >= 400) {
      // 客户端错误
      logger.warn(`请求错误 [${requestId}] ${requestMethod} ${requestPath} ${statusCode} - ${processingTime}ms`);
      
      // 记录请求体信息，但排除敏感信息
      if (req.body) {
        const sanitizedBody = { ...req.body };
        ['password', 'token', 'secret', 'key'].forEach(field => {
          if (sanitizedBody[field]) sanitizedBody[field] = '[REDACTED]';
        });
        logger.warn(`请求体: ${JSON.stringify(sanitizedBody)}`);
      }
    } else {
      // 成功请求
      logger.info(`请求成功 [${requestId}] ${requestMethod} ${requestPath} ${statusCode} - ${processingTime}ms`);
      
      // 对OCR导入相关请求进行更详细的记录
      if (requestPath.includes('/import') && req.body) {
        logger.info(`导入请求 [${requestId}] - 数据项数: ${Array.isArray(req.body) ? req.body.length : 'N/A'}`);
      }
    }
    
    // 如果处理时间异常长（超过1秒），记录性能警告
    if (processingTime > 1000) {
      logger.warn(`性能警告: 请求处理时间超过1秒 [${requestId}] ${requestMethod} ${requestPath} - ${processingTime}ms`);
    }
  };
  
  // 将请求ID添加到响应头
  res.setHeader('X-Request-ID', requestId);
  
  // 继续处理请求
  next();
}

module.exports = requestTracker; 