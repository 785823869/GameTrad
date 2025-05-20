import React from 'react';
import { Box, styled } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

// 布局容器
const LayoutContainer = styled(Box)({
  display: 'flex',
  height: '100vh',
  width: '100%',
  overflow: 'hidden'
});

// 内容区域
const ContentContainer = styled(Box)({
  flexGrow: 1,
  height: '100%',
  overflow: 'auto',
  backgroundColor: '#f8fafc'
});

/**
 * 主布局组件
 * 包含侧边栏和内容区域
 */
const MainLayout = () => {
  return (
    <LayoutContainer>
      {/* 侧边栏 */}
      <Sidebar />
      
      {/* 内容区域 */}
      <ContentContainer>
        <Outlet />
      </ContentContainer>
    </LayoutContainer>
  );
};

export default MainLayout; 