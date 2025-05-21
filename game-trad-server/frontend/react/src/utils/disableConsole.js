/**
 * disableConsole.js
 * 
 * 在生产环境中禁用所有控制台日志输出
 * 当环境变量REACT_APP_DISABLE_CONSOLE为true时会自动禁用
 */

// 检查是否应该禁用控制台
const shouldDisable = () => {
  // 检查环境变量
  if (process.env.REACT_APP_DISABLE_CONSOLE === 'true') {
    return true;
  }
  
  // 在生产环境中，如果未特别指定保留控制台输出，则禁用
  if (process.env.NODE_ENV === 'production') {
    // 可以通过localStorage覆盖此行为
    try {
      const preserveLogs = localStorage.getItem('gametrad_preserve_logs');
      if (preserveLogs === 'true') {
        return false;
      }
    } catch (e) {
      // 忽略localStorage错误
    }
    return true;
  }
  
  return false;
};

// 禁用控制台输出
const disableConsole = () => {
  if (shouldDisable()) {
    const noop = () => {};
    
    // 保存原始控制台方法的引用
    const originalConsole = {
      log: console.log,
      info: console.info,
      debug: console.debug,
      warn: console.warn,
      error: console.error
    };
    
    // 替换所有非关键方法
    console.log = noop;
    console.info = noop;
    console.debug = noop;
    
    // 可选择性保留警告和错误
    // console.warn = noop;
    // console.error = noop;
    
    // 提供恢复方法（用于调试）
    console.restore = () => {
      console.log = originalConsole.log;
      console.info = originalConsole.info;
      console.debug = originalConsole.debug;
      console.warn = originalConsole.warn;
      console.error = originalConsole.error;
      delete console.restore;
      return '控制台日志已恢复';
    };
    
    return true;
  }
  return false;
};

export default disableConsole; 