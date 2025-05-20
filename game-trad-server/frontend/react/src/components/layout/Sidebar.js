import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Box, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Divider, 
  Button,
  Typography,
  styled 
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Inventory as InventoryIcon,
  AddBox as StockInIcon,
  RemoveCircle as StockOutIcon,
  MonitorHeart as TradeMonitorIcon,
  Diamond as NvwaPriceIcon,
  MonetizationOn as SilverPriceIcon,
  History as LogIcon,
  ImageSearch as OcrIcon,
  ReceiptLong as RecipeIcon,
  Update as UpdateIcon,
  Settings as SettingsIcon,
  Add as AddIcon
} from '@mui/icons-material';

// 侧边栏样式
const SidebarContainer = styled(Box)(({ theme }) => ({
  width: 250,
  height: '100%',
  backgroundColor: '#1e293b',
  color: 'white',
  display: 'flex',
  flexDirection: 'column',
  overflowY: 'auto',
  boxShadow: '2px 0 10px rgba(0, 0, 0, 0.1)',
  zIndex: 100,
  '&::-webkit-scrollbar': {
    width: 6,
  },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 3,
  }
}));

// 标题样式
const SidebarHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-start',
  borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
}));

// Logo样式
const Logo = styled(Box)(({ theme }) => ({
  width: 40,
  height: 40,
  backgroundColor: '#2563eb',
  borderRadius: 8,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginRight: theme.spacing(2),
  fontSize: 18,
  fontWeight: 'bold',
  color: 'white'
}));

// 导航项样式
const NavItem = styled(ListItem)(({ theme, active }) => ({
  padding: theme.spacing(1, 3),
  margin: theme.spacing(0.5, 1),
  borderRadius: 6,
  cursor: 'pointer',
  transition: 'all 0.2s',
  backgroundColor: active ? 'rgba(37, 99, 235, 0.8)' : 'transparent',
  '&:hover': {
    backgroundColor: active ? 'rgba(37, 99, 235, 0.8)' : 'rgba(255, 255, 255, 0.08)',
  },
  '& .MuiListItemIcon-root': {
    minWidth: 36,
    color: active ? 'white' : 'rgba(255, 255, 255, 0.6)',
  },
  '& .MuiTypography-root': {
    fontWeight: active ? 500 : 400,
    fontSize: '0.95rem',
  }
}));

// 新交易按钮样式
const NewTradeButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(2),
  borderRadius: 8,
  padding: theme.spacing(1, 0),
  color: 'white',
  fontWeight: 'bold',
  textTransform: 'none',
  background: 'linear-gradient(45deg, #1976d2 30%, #2196f3 90%)',
  boxShadow: '0 4px 10px rgba(0, 0, 0, 0.25)',
  '&:hover': {
    background: 'linear-gradient(45deg, #1565c0 30%, #1e88e5 90%)',
  }
}));

// 导航分组标题
const NavGroupTitle = styled(Typography)(({ theme }) => ({
  fontSize: '0.75rem',
  color: 'rgba(255, 255, 255, 0.5)',
  padding: theme.spacing(1, 3),
  marginTop: theme.spacing(1),
  fontWeight: 500,
  textTransform: 'uppercase',
  letterSpacing: '0.5px'
}));

const Sidebar = () => {
  const location = useLocation();
  const currentPath = location.pathname;

  // 菜单项配置
  const menuItems = [
    {
      title: '主要功能',
      items: [
        { name: '仪表盘', icon: <DashboardIcon />, path: '/' },
        { name: '库存管理', icon: <InventoryIcon />, path: '/inventory' },
        { name: '入库管理', icon: <StockInIcon />, path: '/stock-in' },
        { name: '出库管理', icon: <StockOutIcon />, path: '/stock-out' },
        { name: '交易监控', icon: <TradeMonitorIcon />, path: '/trade-monitor' }
      ]
    },
    {
      title: '行情分析',
      items: [
        { name: '女娲石行情', icon: <NvwaPriceIcon />, path: '/nvwa-price' },
        { name: '银两行情', icon: <SilverPriceIcon />, path: '/silver-price' }
      ]
    },
    {
      title: '数据工具',
      items: [
        { name: 'OCR识别', icon: <OcrIcon />, path: '/ocr' },
        { name: '配方管理', icon: <RecipeIcon />, path: '/recipes' },
        { name: '操作日志', icon: <LogIcon />, path: '/logs' }
      ]
    },
    {
      title: '系统',
      items: [
        { name: '更新管理', icon: <UpdateIcon />, path: '/updates' },
        { name: '设置', icon: <SettingsIcon />, path: '/settings' }
      ]
    }
  ];

  return (
    <SidebarContainer>
      {/* 侧边栏标题 */}
      <SidebarHeader>
        <Logo>GT</Logo>
        <Typography variant="h6" component="div" fontWeight={600}>
          GameTrad
        </Typography>
      </SidebarHeader>

      {/* 新建交易按钮 */}
      <NewTradeButton 
        variant="contained" 
        startIcon={<AddIcon />}
        component={Link}
        to="/new-trade"
      >
        新建交易
      </NewTradeButton>

      {/* 导航菜单 */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', py: 1 }}>
        {menuItems.map((group, groupIndex) => (
          <React.Fragment key={groupIndex}>
            <NavGroupTitle variant="subtitle2">
              {group.title}
            </NavGroupTitle>
            <List component="nav" disablePadding>
              {group.items.map((item, index) => (
                <NavItem
                  key={index}
                  active={currentPath === item.path ? 1 : 0}
                  component={Link}
                  to={item.path}
                >
                  <ListItemIcon>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.name} 
                    primaryTypographyProps={{ 
                      color: currentPath === item.path ? 'white' : 'rgba(255, 255, 255, 0.7)' 
                    }}
                  />
                </NavItem>
              ))}
            </List>
            {groupIndex < menuItems.length - 1 && (
              <Divider sx={{ backgroundColor: 'rgba(255, 255, 255, 0.08)', my: 1 }} />
            )}
          </React.Fragment>
        ))}
      </Box>

      {/* 版本信息 */}
      <Box sx={{ p: 2, textAlign: 'center', fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.5)' }}>
        GameTrad v1.3.1
      </Box>
    </SidebarContainer>
  );
};

export default Sidebar; 