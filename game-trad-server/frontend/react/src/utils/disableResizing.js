/**
 * disableResizing.js
 * 提供精确的禁用调整大小功能的工具
 */

// 精确识别调整大小元素的选择器列表
const RESIZER_SELECTORS = [
  // 确切ID和类名选择器
  '#root > div > div.MuiBox-root.css-10s1gw4 > div.MuiBox-root.css-oc39ss',
  'div.MuiBox-root.css-oc39ss',
  '.resize-handle',
  '.Resizer',
  
  // 数据属性选择器
  '[data-testid="resizer"]',
  '[data-resizable="true"]'
];

// 确保不被禁用的UI元素选择器
const PRESERVE_SELECTORS = [
  // 导航和侧边栏元素
  '.MuiDrawer-root',
  '.MuiDrawer-paper',
  '.MuiDrawer-docked',
  '.MuiDrawer-modal',
  'nav',
  '.sidebar',
  '.menu-button',
  '.menu-item',
  '.sidebar-nav',
  '.MuiList-root',
  '.MuiListItem-root',
  '.MuiListItemIcon-root',
  '.MuiListItemText-root',
  '.MuiSvgIcon-root',
  '.MuiIconButton-root',
  '.MuiAppBar-root',
  '.MuiToolbar-root',
  
  // 确保任何可能的菜单容器元素
  '[role="menu"]',
  '[role="menuitem"]',
  '[role="menubar"]',
  '[role="navigation"]',
  
  // 交互元素
  'a', 'button', '[role="button"]', '.MuiButtonBase-root', 
  'input', 'select', 'textarea',
  
  // 确保特定的侧边栏相关元素不会被禁用 - 使用更广泛的选择器
  '.MuiDrawer-root *',
  '.sidebar *',
  'nav *',
  '.menu-container *',
  '.MuiList-root *',
  '[role="navigation"] *',
  
  // 通用Material-UI组件，可能用于菜单
  '.MuiPaper-root',
  '.MuiCollapse-root',
  '.MuiCollapse-wrapper',
  '.MuiCollapse-wrapperInner'
];

/**
 * 创建并应用禁用调整大小的样式
 */
export function applyResizingDisableStyles() {
  const style = document.createElement('style');
  
  // 使用CSS变量定义统一的禁用属性
  style.textContent = `
    :root {
      --disable-resize-props: none !important;
      --disable-resizer-display: none !important;
      --disable-resizer-events: none !important;
      --enable-pointer-events: auto !important;
      --enable-display: flex !important;
    }
    
    /* 全局禁用调整大小功能 */
    * {
      resize: var(--disable-resize-props);
    }
    
    /* 精确禁用调整大小元素 */
    ${RESIZER_SELECTORS.join(',\n    ')} {
      resize: var(--disable-resize-props);
      pointer-events: var(--disable-resizer-events);
      user-select: var(--disable-resizer-events);
      display: var(--disable-resizer-display);
    }
    
    /* 确保菜单和交互元素正常显示和工作 - 提高选择器优先级 */
    ${PRESERVE_SELECTORS.join(',\n    ')} {
      cursor: pointer !important;
      pointer-events: var(--enable-pointer-events) !important;
      display: inherit !important;
      visibility: visible !important;
      opacity: 1 !important;
      z-index: auto !important;
      position: relative !important;
      width: auto !important;
      height: auto !important;
    }
    
    /* 确保特定UI组件的布局 - 更强大的规则 */
    .MuiDrawer-root, 
    .MuiDrawer-paper, 
    .sidebar, 
    nav,
    .menu-button, 
    .menu-item, 
    .sidebar-nav,
    .MuiList-root,
    .MuiListItem-root,
    [role="navigation"],
    [role="menu"],
    [role="menuitem"] {
      display: var(--enable-display) !important;
      pointer-events: var(--enable-pointer-events) !important;
      user-select: auto !important;
      visibility: visible !important;
      opacity: 1 !important;
    }
    
    /* 禁用具有调整大小相关样式的元素 */
    div[style*="resize"],
    div[style*="cursor: ns-resize"],
    div[style*="cursor: ew-resize"],
    div[style*="cursor: nwse-resize"],
    div[style*="cursor: nesw-resize"] {
      resize: var(--disable-resize-props);
      cursor: default !important;
      pointer-events: var(--disable-resizer-events);
      user-select: var(--disable-resizer-events);
      display: var(--disable-resizer-display);
    }
    
    /* 确保导航菜单元素不会被隐藏 */
    .MuiDrawer-root,
    .MuiDrawer-paper,
    .MuiList-root,
    .MuiListItem-root {
      display: block !important;
    }
    
    /* 修复特定菜单项的布局 */
    .MuiListItem-root {
      display: flex !important;
    }
  `;
  
  document.head.appendChild(style);
}

/**
 * 标记可调整大小的元素
 * 将遍历DOM并为符合条件的元素添加数据属性
 */
export function markResizableElements() {
  // 查找可能是调整大小元素的DOM节点
  const markElements = () => {
    // 查找可能的调整大小元素
    document.querySelectorAll('div').forEach(el => {
      // 检查样式，标记可能是调整大小的元素
      const style = window.getComputedStyle(el);
      if (
        style.resize !== 'none' || 
        style.cursor?.includes('resize') ||
        el.className?.toLowerCase().includes('resiz')
      ) {
        // 避免标记菜单元素
        if (
          !el.className?.toLowerCase().includes('menu') &&
          !el.className?.toLowerCase().includes('drawer') &&
          !el.className?.toLowerCase().includes('sidebar') &&
          !el.className?.toLowerCase().includes('list') &&
          !el.closest('.MuiDrawer-root') &&
          !el.closest('[role="navigation"]')
        ) {
          el.setAttribute('data-resizable', 'true');
        }
      }
    });
    
    // 特别处理已知的调整大小元素
    RESIZER_SELECTORS.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          el.setAttribute('data-resizable', 'true');
        });
      } catch (e) {
        console.warn(`选择器错误: ${selector}`, e);
      }
    });
  };
  
  // 初始标记
  markElements();
  
  // 创建观察器定期检查新元素
  const observer = new MutationObserver(() => {
    markElements();
  });
  
  // 开始观察
  observer.observe(document.body, { 
    childList: true, 
    subtree: true 
  });
}

/**
 * 移除特定的调整大小元素
 */
export function removeResizerElements() {
  const removeResizer = () => {
    RESIZER_SELECTORS.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          // 确保不移除菜单相关元素
          if (
            el && 
            !el.hasAttribute('data-preserved') &&
            !el.className?.toLowerCase().includes('menu') &&
            !el.className?.toLowerCase().includes('drawer') &&
            !el.className?.toLowerCase().includes('sidebar') &&
            !el.className?.toLowerCase().includes('list') &&
            !el.closest('.MuiDrawer-root') &&
            !el.closest('[role="navigation"]')
          ) {
            el.remove();
          }
        });
      } catch (e) {
        // 忽略选择器错误
      }
    });
  };
  
  // 初次执行
  removeResizer();
  
  // 创建观察器
  const observer = new MutationObserver(() => {
    removeResizer();
  });
  
  // 开始观察
  observer.observe(document.body, { 
    childList: true, 
    subtree: true 
  });
}

/**
 * 初始化所有禁用调整大小功能
 */
export function initDisableResizing() {
  // 应用样式
  applyResizingDisableStyles();
  
  // DOM加载完成后执行
  document.addEventListener('DOMContentLoaded', () => {
    // 标记可调整大小元素
    markResizableElements();
    
    // 移除特定调整大小元素
    removeResizerElements();
    
    // 专门确保菜单元素可见的额外函数
    ensureMenuElementsVisible();
  });
}

/**
 * 确保菜单元素可见的特殊处理
 */
function ensureMenuElementsVisible() {
  // 每200ms检查一次菜单元素，确保其可见性
  const intervalId = setInterval(() => {
    // 处理常见的菜单容器元素
    document.querySelectorAll('.MuiDrawer-root, .MuiDrawer-paper, .sidebar, [role="navigation"], .MuiList-root').forEach(el => {
      if (el && (el.style.display === 'none' || el.style.visibility === 'hidden' || el.style.opacity === '0')) {
        el.style.display = 'flex';
        el.style.visibility = 'visible';
        el.style.opacity = '1';
        el.style.pointerEvents = 'auto';
      }
    });
    
    // 恢复可能被隐藏的菜单项
    document.querySelectorAll('.MuiListItem-root, .menu-item, [role="menuitem"]').forEach(el => {
      if (el) {
        el.style.display = 'flex';
        el.style.visibility = 'visible';
        el.style.opacity = '1';
        el.style.pointerEvents = 'auto';
      }
    });
  }, 200);
  
  // 30秒后清除定时器，避免长期占用资源
  setTimeout(() => {
    clearInterval(intervalId);
  }, 30000);
}

export default initDisableResizing; 