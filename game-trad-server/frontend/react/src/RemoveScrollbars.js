/**
 * 移除水平滚动条的辅助脚本
 */
export const removeHorizontalScrollbars = () => {
  // 运行一次初始化
  applyScrollbarFixes();
  
  // 设置一个观察器，监视DOM变化以捕获动态加载的元素
  setupMutationObserver();
};

// 应用滚动条修复
const applyScrollbarFixes = () => {
  try {
    // 移除特定元素的水平滚动条
    const specificElement = document.querySelector("#root > div > div.MuiBox-root.css-10s1gw4 > div.MuiBox-root.css-oc39ss");
    if (specificElement) {
      specificElement.style.overflowX = 'hidden';
      specificElement.style.maxWidth = '100%';
      specificElement.style.paddingRight = '0';
      specificElement.style.marginRight = '0';
    }
  } catch (error) {
    console.error('Failed to apply scrollbar fixes:', error);
  }
};

// 设置变化观察器来处理动态加载的元素
const setupMutationObserver = () => {
  try {
    const observer = new MutationObserver(() => {
      applyScrollbarFixes();
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  } catch (error) {
    console.error('Failed to setup mutation observer:', error);
  }
};

export default removeHorizontalScrollbars; 