import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { styled, alpha } from '@mui/material/styles';
import { 
  Box, 
  Drawer, 
  AppBar, 
  Toolbar, 
  Typography, 
  Divider, 
  List, 
  IconButton, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText, 
  useMediaQuery,
  Avatar,
  Button,
  Tooltip
} from '@mui/material';
import { 
  Menu as MenuIcon, 
  Dashboard as DashboardIcon, 
  Image as ImageIcon, 
  Description as DescriptionIcon, 
  Article as ArticleIcon, 
  Update as UpdateIcon, 
  Settings as SettingsIcon,
  Brightness4 as DarkModeIcon,
  Notifications as NotificationsIcon,
  Help as HelpIcon
} from '@mui/icons-material';
import { Link, useLocation } from 'react-router-dom';

const drawerWidth = 260;

const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme, open }) => ({
    flexGrow: 1,
    padding: theme.spacing(3),
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    marginLeft: `-${drawerWidth}px`,
    ...(open && {
      transition: theme.transitions.create('margin', {
        easing: theme.transitions.easing.easeOut,
        duration: theme.transitions.duration.enteringScreen,
      }),
      marginLeft: 0,
    }),
  }),
);

const AppBarStyled = styled(AppBar, { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme, open }) => ({
    transition: theme.transitions.create(['margin', 'width'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    ...(open && {
      width: `calc(100% - ${drawerWidth}px)`,
      marginLeft: `${drawerWidth}px`,
      transition: theme.transitions.create(['margin', 'width'], {
        easing: theme.transitions.easing.easeOut,
        duration: theme.transitions.duration.enteringScreen,
      }),
    }),
  }),
);

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 2),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
  justifyContent: 'flex-start',
}));

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(0, 2),
}));

const LogoWrapper = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
}));

const Logo = styled('div')(({ theme }) => ({
  width: 40,
  height: 40,
  borderRadius: 8,
  background: 'linear-gradient(135deg, #42a5f5 0%, #1976d2 100%)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#fff',
  fontWeight: 'bold',
  fontSize: 18,
  boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
}));

const UserSection = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
}));

const ActionButton = styled(IconButton)(({ theme }) => ({
  width: 40,
  height: 40,
  borderRadius: 8,
  backgroundColor: alpha(theme.palette.common.white, 0.15),
  '&:hover': {
    backgroundColor: alpha(theme.palette.common.white, 0.25),
  },
}));

const menuItems = [
  { text: '仪表盘', icon: <DashboardIcon />, path: '/' },
  { text: 'OCR识别', icon: <ImageIcon />, path: '/ocr' },
  { text: '配方管理', icon: <DescriptionIcon />, path: '/recipes' },
  { text: '日志查看', icon: <ArticleIcon />, path: '/logs' },
  { text: '更新管理', icon: <UpdateIcon />, path: '/update' },
  { text: '设置', icon: <SettingsIcon />, path: '/settings' },
];

function MainLayout() {
  const location = useLocation();
  const isMobile = useMediaQuery((theme) => theme.breakpoints.down('md'));
  const [open, setOpen] = useState(!isMobile);

  const handleDrawerToggle = () => {
    setOpen(!open);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBarStyled position="fixed" open={open}>
        <StyledToolbar>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              onClick={handleDrawerToggle}
              edge="start"
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div">
              GameTrad管理控制台
            </Typography>
          </Box>
          <UserSection>
            <Tooltip title="通知">
              <ActionButton color="inherit">
                <NotificationsIcon />
              </ActionButton>
            </Tooltip>
            <Tooltip title="帮助">
              <ActionButton color="inherit">
                <HelpIcon />
              </ActionButton>
            </Tooltip>
            <Tooltip title="切换暗色模式">
              <ActionButton color="inherit">
                <DarkModeIcon />
              </ActionButton>
            </Tooltip>
            <Avatar 
              alt="管理员" 
              src="/avatar.png" 
              sx={{ 
                width: 40, 
                height: 40,
                border: '2px solid rgba(255, 255, 255, 0.8)',
                cursor: 'pointer'
              }} 
            />
          </UserSection>
        </StyledToolbar>
      </AppBarStyled>
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            boxShadow: '0 0 20px rgba(0, 0, 0, 0.05)',
            border: 'none',
          },
        }}
        variant={isMobile ? "temporary" : "persistent"}
        anchor="left"
        open={open}
        onClose={isMobile ? handleDrawerToggle : undefined}
      >
        <DrawerHeader>
          <LogoWrapper>
            <Logo>GT</Logo>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              GameTrad
            </Typography>
          </LogoWrapper>
        </DrawerHeader>
        <Divider />
        <Box sx={{ p: 2 }}>
          <Button 
            variant="contained" 
            fullWidth
            sx={{
              borderRadius: 2,
              py: 1,
              background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
              boxShadow: '0 4px 10px rgba(25, 118, 210, 0.3)',
              textTransform: 'none',
              fontWeight: 600
            }}
          >
            新建交易
          </Button>
        </Box>
        <List sx={{ px: 1 }}>
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <ListItem 
                key={item.text} 
                disablePadding
                component={Link}
                to={item.path}
                sx={{ 
                  color: 'inherit', 
                  textDecoration: 'none',
                  mb: 0.5
                }}
              >
                <ListItemButton
                  sx={{
                    borderRadius: 2,
                    bgcolor: isActive ? 'primary.lighter' : 'transparent',
                    color: isActive ? 'primary.main' : 'text.primary',
                    '&:hover': {
                      bgcolor: isActive ? 'primary.lighter' : 'action.hover',
                    },
                    transition: 'all 0.2s',
                  }}
                >
                  <ListItemIcon 
                    sx={{ 
                      color: isActive ? 'primary.main' : 'inherit',
                      minWidth: 36
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.text} 
                    primaryTypographyProps={{
                      fontWeight: isActive ? 600 : 400,
                    }}
                  />
                  {isActive && (
                    <Box 
                      sx={{ 
                        width: 4, 
                        height: 36, 
                        bgcolor: 'primary.main',
                        borderRadius: 4,
                        ml: 1
                      }} 
                    />
                  )}
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
        <Box sx={{ flexGrow: 1 }} />
        <Box sx={{ p: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
            GameTrad v1.3.1
          </Typography>
        </Box>
      </Drawer>
      <Main open={open}>
        <DrawerHeader />
        <Outlet />
      </Main>
    </Box>
  );
}

export default MainLayout; 