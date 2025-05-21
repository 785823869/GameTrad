/**
 * 认证中间件
 * 用于验证API请求权限
 */

// 当前为开发模式，简化认证机制
const requireAuth = (req, res, next) => {
  // 在开发环境中，跳过认证，直接通过所有请求
  next();
};

module.exports = {
  requireAuth
}; 