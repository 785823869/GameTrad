import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Snackbar,
  CircularProgress,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import { 
  Save as SaveIcon, 
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Backup as BackupIcon,
  Restore as RestoreIcon
} from '@mui/icons-material';

const Settings = () => {
  // 状态管理
  const [settings, setSettings] = useState({
    general: {
      appName: 'GameTrad管理系统',
      dataPath: '',
      backupEnabled: true,
      backupInterval: 24,
      logLevel: 'info'
    },
    notification: {
      enabled: false,
      email: '',
      serverChanKey: '',
      notifyOnError: true,
      notifyOnUpdate: true
    },
    display: {
      theme: 'light',
      language: 'zh_CN',
      tableRowsPerPage: 10
    }
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  const [backups, setBackups] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState(''); // 'reset', 'backup', 'restore'
  const [selectedBackup, setSelectedBackup] = useState(null);

  // 加载设置数据
  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/status/settings');
      setSettings(response.data.settings);
      setBackups(response.data.backups || []);
      setError(null);
    } catch (err) {
      console.error('获取设置数据失败:', err);
      setError('无法加载设置数据。请检查网络连接或服务器状态。');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    fetchSettings();
  }, []);

  // 处理设置变更
  const handleSettingChange = (section, name, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [name]: value
      }
    }));
  };

  // 保存设置
  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      await axios.post('/api/status/settings', { settings });
      setSnackbar({
        open: true,
        message: '设置保存成功',
        severity: 'success'
      });
    } catch (err) {
      console.error('保存设置失败:', err);
      setSnackbar({
        open: true,
        message: '设置保存失败: ' + (err.response?.data?.message || err.message),
        severity: 'error'
      });
    } finally {
      setSaving(false);
    }
  };

  // 处理对话框
  const handleOpenDialog = (type, backup = null) => {
    setDialogType(type);
    if (backup) {
      setSelectedBackup(backup);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  // 重置设置
  const handleResetSettings = async () => {
    try {
      setLoading(true);
      await axios.post('/api/status/settings/reset');
      handleCloseDialog();
      await fetchSettings();
      setSnackbar({
        open: true,
        message: '设置已重置为默认值',
        severity: 'success'
      });
    } catch (err) {
      console.error('重置设置失败:', err);
      setSnackbar({
        open: true,
        message: '重置设置失败: ' + (err.response?.data?.message || err.message),
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  // 创建备份
  const handleCreateBackup = async () => {
    try {
      setSaving(true);
      await axios.post('/api/status/backup');
      handleCloseDialog();
      await fetchSettings(); // 刷新备份列表
      setSnackbar({
        open: true,
        message: '备份创建成功',
        severity: 'success'
      });
    } catch (err) {
      console.error('创建备份失败:', err);
      setSnackbar({
        open: true,
        message: '创建备份失败: ' + (err.response?.data?.message || err.message),
        severity: 'error'
      });
    } finally {
      setSaving(false);
    }
  };

  // 恢复备份
  const handleRestoreBackup = async () => {
    if (!selectedBackup) return;
    
    try {
      setLoading(true);
      await axios.post(`/api/status/backup/restore/${selectedBackup.id}`);
      handleCloseDialog();
      await fetchSettings();
      setSnackbar({
        open: true,
        message: '备份恢复成功',
        severity: 'success'
      });
    } catch (err) {
      console.error('恢复备份失败:', err);
      setSnackbar({
        open: true,
        message: '恢复备份失败: ' + (err.response?.data?.message || err.message),
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  // 关闭提示条
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // 格式化日期
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading && !settings) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          系统设置
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchSettings}
            disabled={loading || saving}
            sx={{ mr: 1 }}
          >
            刷新
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            onClick={handleSaveSettings}
            disabled={loading || saving}
          >
            保存设置
            {saving && <CircularProgress size={24} sx={{ ml: 1 }} />}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* 基本设置 */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              基本设置
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="应用名称"
                  value={settings.general.appName}
                  onChange={(e) => handleSettingChange('general', 'appName', e.target.value)}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="数据存储路径"
                  value={settings.general.dataPath}
                  onChange={(e) => handleSettingChange('general', 'dataPath', e.target.value)}
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>日志级别</InputLabel>
                  <Select
                    value={settings.general.logLevel}
                    label="日志级别"
                    onChange={(e) => handleSettingChange('general', 'logLevel', e.target.value)}
                  >
                    <MenuItem value="debug">调试 (Debug)</MenuItem>
                    <MenuItem value="info">信息 (Info)</MenuItem>
                    <MenuItem value="warn">警告 (Warn)</MenuItem>
                    <MenuItem value="error">错误 (Error)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.general.backupEnabled}
                      onChange={(e) => handleSettingChange('general', 'backupEnabled', e.target.checked)}
                    />
                  }
                  label="启用自动备份"
                />
              </Grid>
              
              {settings.general.backupEnabled && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    type="number"
                    label="备份间隔 (小时)"
                    value={settings.general.backupInterval}
                    InputProps={{ inputProps: { min: 1, max: 720 } }}
                    onChange={(e) => handleSettingChange('general', 'backupInterval', parseInt(e.target.value) || 24)}
                  />
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>
        
        {/* 通知设置 */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              通知设置
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notification.enabled}
                      onChange={(e) => handleSettingChange('notification', 'enabled', e.target.checked)}
                    />
                  }
                  label="启用通知"
                />
              </Grid>
              
              {settings.notification.enabled && (
                <>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="通知邮箱"
                      type="email"
                      value={settings.notification.email}
                      onChange={(e) => handleSettingChange('notification', 'email', e.target.value)}
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Server酱 SCKEY"
                      value={settings.notification.serverChanKey}
                      onChange={(e) => handleSettingChange('notification', 'serverChanKey', e.target.value)}
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notification.notifyOnError}
                          onChange={(e) => handleSettingChange('notification', 'notifyOnError', e.target.checked)}
                        />
                      }
                      label="错误时通知"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notification.notifyOnUpdate}
                          onChange={(e) => handleSettingChange('notification', 'notifyOnUpdate', e.target.checked)}
                        />
                      }
                      label="更新可用时通知"
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </Paper>
        </Grid>
        
        {/* 显示设置 */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              显示设置
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>主题</InputLabel>
                  <Select
                    value={settings.display.theme}
                    label="主题"
                    onChange={(e) => handleSettingChange('display', 'theme', e.target.value)}
                  >
                    <MenuItem value="light">浅色</MenuItem>
                    <MenuItem value="dark">深色</MenuItem>
                    <MenuItem value="system">跟随系统</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>语言</InputLabel>
                  <Select
                    value={settings.display.language}
                    label="语言"
                    onChange={(e) => handleSettingChange('display', 'language', e.target.value)}
                  >
                    <MenuItem value="zh_CN">简体中文</MenuItem>
                    <MenuItem value="en_US">English (US)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  type="number"
                  label="表格每页行数"
                  value={settings.display.tableRowsPerPage}
                  InputProps={{ inputProps: { min: 5, max: 100 } }}
                  onChange={(e) => handleSettingChange('display', 'tableRowsPerPage', parseInt(e.target.value) || 10)}
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        {/* 备份管理 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="备份管理" 
              action={
                <Box>
                  <Button
                    startIcon={<BackupIcon />}
                    onClick={() => handleOpenDialog('backup')}
                    disabled={loading || saving}
                    sx={{ mr: 1 }}
                  >
                    创建备份
                  </Button>
                  <Button
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => handleOpenDialog('reset')}
                    disabled={loading || saving}
                  >
                    重置设置
                  </Button>
                </Box>
              }
            />
            <Divider />
            <CardContent sx={{ height: 250, overflow: 'auto' }}>
              {backups.length === 0 ? (
                <Typography color="text.secondary" align="center">
                  暂无备份记录
                </Typography>
              ) : (
                <List>
                  {backups.map((backup) => (
                    <ListItem
                      key={backup.id}
                      secondaryAction={
                        <Button
                          size="small"
                          startIcon={<RestoreIcon />}
                          onClick={() => handleOpenDialog('restore', backup)}
                          disabled={loading || saving}
                        >
                          恢复
                        </Button>
                      }
                    >
                      <ListItemText
                        primary={`备份 #${backup.id}`}
                        secondary={formatDate(backup.created_at)}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* 对话框 */}
      <Dialog open={openDialog} onClose={handleCloseDialog}>
        {dialogType === 'reset' && (
          <>
            <DialogTitle>重置设置</DialogTitle>
            <DialogContent>
              <DialogContentText>
                确定要将所有设置重置为默认值吗？此操作不可撤销，但不会影响您的数据。
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>取消</Button>
              <Button onClick={handleResetSettings} color="error">
                重置设置
              </Button>
            </DialogActions>
          </>
        )}
        
        {dialogType === 'backup' && (
          <>
            <DialogTitle>创建备份</DialogTitle>
            <DialogContent>
              <DialogContentText>
                确定要创建当前设置的备份吗？这将保存所有当前设置。
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>取消</Button>
              <Button onClick={handleCreateBackup} color="primary">
                创建备份
              </Button>
            </DialogActions>
          </>
        )}
        
        {dialogType === 'restore' && selectedBackup && (
          <>
            <DialogTitle>恢复备份</DialogTitle>
            <DialogContent>
              <DialogContentText>
                确定要恢复备份 #{selectedBackup.id} ({formatDate(selectedBackup.created_at)}) 吗？当前设置将被覆盖。
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>取消</Button>
              <Button onClick={handleRestoreBackup} color="primary">
                恢复备份
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
      
      {/* 提示条 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Settings; 