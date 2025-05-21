import React, { useState } from 'react';
import {
  Container,
  Box,
  Grid,
  Paper,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider
} from '@mui/material';
import {
  Notifications as ServerChanIcon,
  Email as EmailIcon,
  Backup as BackupIcon,
  Storage as DatabaseIcon,
  Functions as FormulaIcon,
  Notes as NoteRulesIcon,
  Category as ItemDictionaryIcon
} from '@mui/icons-material';

// 子组件导入
import ServerChanConfig from './ServerChanConfig';
import EmailConfig from './EmailConfig';
import DatabaseBackup from './DatabaseBackup';
import DatabaseConnection from './DatabaseConnection';
import FormulaManager from './FormulaManager';
import NoteRulesConfig from './NoteRulesConfig';
import ItemDictionaryManager from './ItemDictionaryManager';

const SettingsLayout = () => {
  // 当前选中的设置菜单项
  const [selectedSetting, setSelectedSetting] = useState('server-chan');

  // 设置菜单配置
  const settingMenuItems = [
    { 
      id: 'server-chan', 
      name: 'Server酱配置', 
      icon: <ServerChanIcon />, 
      component: ServerChanConfig 
    },
    { 
      id: 'email', 
      name: 'QQ邮箱推送设置', 
      icon: <EmailIcon />, 
      component: EmailConfig 
    },
    { 
      id: 'database-backup', 
      name: '数据库备份与恢复', 
      icon: <BackupIcon />, 
      component: DatabaseBackup 
    },
    { 
      id: 'database-connection', 
      name: '数据库连接设置', 
      icon: <DatabaseIcon />, 
      component: DatabaseConnection 
    },
    { 
      id: 'formula-manager', 
      name: '公式管理', 
      icon: <FormulaIcon />, 
      component: FormulaManager 
    },
    { 
      id: 'note-rules', 
      name: '备注规则配置', 
      icon: <NoteRulesIcon />, 
      component: NoteRulesConfig 
    },
    { 
      id: 'item-dictionary', 
      name: '物品字典管理', 
      icon: <ItemDictionaryIcon />, 
      component: ItemDictionaryManager 
    }
  ];

  // 获取当前选中的组件
  const CurrentSettingComponent = settingMenuItems.find(item => item.id === selectedSetting)?.component || (() => <div>选择一个设置项</div>);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          系统设置
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* 设置菜单侧边栏 */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ height: '100%' }}>
            <List component="nav" aria-label="设置菜单">
              {settingMenuItems.map((item) => (
                <ListItemButton
                  key={item.id}
                  selected={selectedSetting === item.id}
                  onClick={() => setSelectedSetting(item.id)}
                >
                  <ListItemIcon>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.name} />
                </ListItemButton>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* 设置内容区域 */}
        <Grid item xs={12} md={9}>
          <Paper sx={{ p: 3, minHeight: 500 }}>
            <CurrentSettingComponent />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SettingsLayout; 