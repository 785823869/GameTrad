import React from 'react';
import { 
  Menu, 
  MenuItem, 
  ListItemIcon, 
  ListItemText, 
  Divider 
} from '@mui/material';
import { 
  ContentCopy as CopyIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

/**
 * 库存管理右键菜单组件
 * 
 * @param {Object} props - 组件属性
 * @param {Object} props.anchorPosition - 菜单锚点位置 {top, left}
 * @param {boolean} props.open - 菜单是否打开
 * @param {function} props.onClose - 关闭菜单的回调函数
 * @param {Object} props.selectedItem - 当前选中的物品
 * @param {function} props.onCopyName - 复制物品名称的回调函数
 * @param {function} props.onDelete - 删除物品的回调函数
 * @param {function} props.onEdit - 编辑物品的回调函数
 * @param {function} props.onRefreshItem - 刷新物品数据的回调函数
 */
const InventoryMenu = ({ 
  anchorPosition, 
  open, 
  onClose,
  selectedItem,
  onCopyName,
  onDelete,
  onEdit,
  onRefreshItem
}) => {
  // 如果没有选中物品，则不显示菜单
  if (!selectedItem) return null;

  // 处理复制物品名称
  const handleCopyName = () => {
    onCopyName && onCopyName(selectedItem);
    onClose();
  };

  // 处理删除物品
  const handleDelete = () => {
    onDelete && onDelete(selectedItem);
    onClose();
  };

  // 处理编辑物品
  const handleEdit = () => {
    onEdit && onEdit(selectedItem);
    onClose();
  };

  // 处理刷新物品数据
  const handleRefreshItem = () => {
    onRefreshItem && onRefreshItem(selectedItem);
    onClose();
  };

  return (
    <Menu
      open={open}
      onClose={onClose}
      anchorReference="anchorPosition"
      anchorPosition={anchorPosition ? { top: anchorPosition.top, left: anchorPosition.left } : undefined}
    >
      <MenuItem onClick={handleCopyName}>
        <ListItemIcon>
          <CopyIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>复制物品名称</ListItemText>
      </MenuItem>
      
      <MenuItem onClick={handleEdit}>
        <ListItemIcon>
          <EditIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>编辑物品</ListItemText>
      </MenuItem>
      
      <MenuItem onClick={handleRefreshItem}>
        <ListItemIcon>
          <RefreshIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>刷新物品数据</ListItemText>
      </MenuItem>
      
      <Divider />
      
      <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>
        <ListItemIcon>
          <DeleteIcon fontSize="small" color="error" />
        </ListItemIcon>
        <ListItemText>删除物品</ListItemText>
      </MenuItem>
    </Menu>
  );
};

export default InventoryMenu; 