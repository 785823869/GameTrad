import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { io } from 'socket.io-client';
import {
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Divider,
  Alert,
  Snackbar,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControlLabel,
  Switch,
  TextField,
  Card,
  CardContent,
  Chip,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  MenuItem,
  FormControl,
  RadioGroup,
  Radio,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Collapse
} from '@mui/material';
import {
  Backup as BackupIcon,
  RestorePage as RestoreIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Schedule as ScheduleIcon,
  Info as InfoIcon,
  Storage as StorageIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';

// Socket.IO服务器URL
const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000';

const DatabaseBackup = () => {
  // 状态
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [settings, setSettings] = useState({
    auto_backup_enabled: false,
    backup_frequency: 'daily',
    keep_days: 30,
    backup_time: '03:00',
    email_notification: true,
    backup_method: 'sql'
  });
  
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  
  // 备份进度状态
  const [backupProgress, setBackupProgress] = useState({
    active: false,
    id: null,
    progress: 0,
    status: 'idle',
    message: '',
    method: '',
    logs: []
  });
  
  // 高级备份选项
  const [advancedOptions, setAdvancedOptions] = useState({
    compression: false,
    incremental: false
  });
  
  // 备份日志区域显示状态
  const [showLogs, setShowLogs] = useState(false);
  
  // 日志滚动区域引用
  const logsEndRef = useRef(null);
  
  // Socket.IO连接
  const socketRef = useRef(null);
  
  // 加载备份列表
  useEffect(() => {
    fetchBackups();
    fetchSettings();
    
    // 初始化Socket.IO连接
    socketRef.current = io(SOCKET_URL);
    
    // 监听备份事件
    socketRef.current.on('backup:start', (data) => {
      setBackupProgress(prev => ({
        ...prev,
        active: true,
        id: data.id,
        progress: data.progress || 0,
        status: data.status || 'starting',
        message: data.message || '开始备份...',
        method: data.method || '',
        logs: data.logs || []
      }));
    });
    
    socketRef.current.on('backup:progress', (data) => {
      setBackupProgress(prev => ({
        ...prev,
        progress: data.progress,
        status: data.status,
        message: data.message
      }));
    });
    
    socketRef.current.on('backup:log', (data) => {
      if (data.id === backupProgress.id) {
        setBackupProgress(prev => ({
          ...prev,
          logs: [...prev.logs, `[${new Date().toLocaleTimeString()}] ${data.message}`]
        }));
      }
    });
    
    socketRef.current.on('backup:complete', (data) => {
      setBackupProgress(prev => ({
        ...prev,
        progress: 100,
        status: 'completed',
        message: `备份完成，大小: ${data.size_formatted}`
      }));
      
      // 成功后5秒重置UI
      setTimeout(() => {
        setBackupProgress({
          active: false,
          id: null,
          progress: 0,
          status: 'idle',
          message: '',
          method: '',
          logs: []
        });
        setBackupLoading(false);
      }, 5000);
      
      // 刷新备份列表
      fetchBackups();
    });
    
    socketRef.current.on('backup:error', (data) => {
      setBackupProgress(prev => ({
        ...prev,
        status: 'error',
        message: `错误: ${data.error}`
      }));
      
      showNotification(`备份失败: ${data.error}`, 'error');
      setBackupLoading(false);
    });
    
    // 清理函数
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);
  
  // 滚动日志到底部
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [backupProgress.logs]);
  
  // 获取备份列表
  const fetchBackups = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/backup/list');
      
      if (response.data && response.data.success) {
        setBackups(response.data.backups || []);
      } else {
        showNotification(`获取备份列表失败: ${response.data.message}`, 'error');
      }
    } catch (err) {
      showNotification(`获取备份列表失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 获取备份设置
  const fetchSettings = async () => {
    try {
      const response = await axios.get('/api/backup/settings');
      
      if (response.data && response.data.success) {
        setSettings(response.data.settings);
      }
    } catch (err) {
      showNotification(`获取备份设置失败: ${err.message}`, 'error');
    }
  };
  
  // 保存备份设置
  const saveSettings = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/backup/settings', settings);
      
      if (response.data && response.data.success) {
        showNotification('备份设置已保存', 'success');
        setSettingsDialogOpen(false);
      } else {
        showNotification(`保存设置失败: ${response.data.message}`, 'error');
      }
    } catch (err) {
      showNotification(`保存设置失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 创建备份
  const createBackup = async () => {
    try {
      setBackupLoading(true);
      
      // 使用高级选项
      const response = await axios.post('/api/backup/create', advancedOptions);
      
      // 如果没有收到Socket.IO的进度事件，5秒后重置状态
      setTimeout(() => {
        if (backupLoading && !backupProgress.active) {
          setBackupLoading(false);
          showNotification('备份操作超时或未收到进度更新', 'warning');
        }
      }, 5000);
      
    } catch (err) {
      showNotification(`创建备份失败: ${err.message}`, 'error');
      setBackupLoading(false);
    }
  };
  
  // 恢复备份
  const restoreBackup = async () => {
    if (!selectedBackup) return;
    
    try {
      setLoading(true);
      setRestoreDialogOpen(false);
      
      const response = await axios.post('/api/backup/restore', {
        filename: selectedBackup.filename
      });
      
      if (response.data && response.data.success) {
        showNotification('数据库恢复成功！可能需要重新启动应用', 'success');
      } else {
        showNotification(`恢复失败: ${response.data.message}`, 'error');
      }
    } catch (err) {
      showNotification(`恢复备份失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 删除备份
  const deleteBackup = async () => {
    if (!selectedBackup) return;
    
    try {
      setLoading(true);
      setDeleteDialogOpen(false);
      
      const response = await axios.delete(`/api/backup/delete/${selectedBackup.filename}`);
      
      if (response.data && response.data.success) {
        showNotification('备份文件已删除', 'success');
        fetchBackups(); // 刷新备份列表
      } else {
        showNotification(`删除失败: ${response.data.message}`, 'error');
      }
    } catch (err) {
      showNotification(`删除备份失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 下载备份
  const downloadBackup = (backup) => {
    window.open(`/api/backup/download/${backup.filename}`, '_blank');
  };
  
  // 清理旧备份
  const cleanupOldBackups = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/backup/cleanup', {
        keep_days: settings.keep_days
      });
      
      if (response.data && response.data.success) {
        showNotification(`已清理${response.data.deleted_count || 0}个过期备份`, 'success');
        fetchBackups(); // 刷新备份列表
      } else {
        showNotification(`清理失败: ${response.data.message}`, 'error');
      }
    } catch (err) {
      showNotification(`清理备份失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 打开设置对话框
  const openSettingsDialog = () => {
    setSettingsDialogOpen(true);
  };
  
  // 处理设置变更
  const handleSettingChange = (e) => {
    const { name, value, checked, type } = e.target;
    
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // 打开删除对话框
  const openDeleteDialog = (backup) => {
    setSelectedBackup(backup);
    setDeleteDialogOpen(true);
  };
  
  // 打开恢复对话框
  const openRestoreDialog = (backup) => {
    setSelectedBackup(backup);
    setRestoreDialogOpen(true);
  };
  
  // 显示通知
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };
  
  // 关闭通知
  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };
  
  // 处理分页变化
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  // 处理每页行数变化
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // 格式化时间
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };
  
  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  // 处理高级选项变更
  const handleAdvancedOptionChange = (e) => {
    const { name, checked } = e.target;
    
    setAdvancedOptions(prev => ({
      ...prev,
      [name]: checked
    }));
  };
  
  // 切换日志显示
  const toggleShowLogs = () => {
    setShowLogs(!showLogs);
  };
  
  // 获取状态颜色
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success.main';
      case 'error':
        return 'error.main';
      case 'starting':
      case 'preparing':
        return 'info.main';
      case 'processing':
      case 'copying':
      case 'exporting':
      case 'compressing':
        return 'primary.main';
      default:
        return 'text.secondary';
    }
  };
  
  // 获取状态图标
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <CircularProgress size={16} thickness={6} />;
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h5" component="h2">
          数据库备份与恢复
        </Typography>
      </Box>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" component="div" gutterBottom>
                备份状态
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  自动备份:
                </Typography>
                <Chip 
                  label={settings.auto_backup_enabled ? "已启用" : "未启用"} 
                  color={settings.auto_backup_enabled ? "success" : "default"}
                  size="small"
                />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  备份频率:
                </Typography>
                <Typography variant="body2">
                  {settings.backup_frequency === 'daily' ? '每日' : 
                   settings.backup_frequency === 'weekly' ? '每周' : '自定义'}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  备份时间:
                </Typography>
                <Typography variant="body2">
                  {settings.backup_time}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  保留天数:
                </Typography>
                <Typography variant="body2">
                  {settings.keep_days} 天
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" component="div" gutterBottom>
                备份统计
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  备份总数:
                </Typography>
                <Typography variant="body2">
                  {backups.length} 个
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  最新备份:
                </Typography>
                <Typography variant="body2">
                  {backups.length > 0 ? formatDate(backups[0].created_at) : '无'}
                </Typography>
              </Box>
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<ScheduleIcon />}
                  onClick={openSettingsDialog}
                  fullWidth
                >
                  备份设置
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          startIcon={backupLoading ? <CircularProgress size={20} /> : <BackupIcon />}
          onClick={createBackup}
          disabled={backupLoading || loading}
        >
          {backupLoading ? '备份中...' : '创建备份'}
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchBackups}
          disabled={loading || backupLoading}
        >
          刷新列表
        </Button>
        <Button
          variant="outlined"
          color="secondary"
          startIcon={<DeleteIcon />}
          onClick={cleanupOldBackups}
          disabled={loading || backupLoading}
        >
          清理旧备份
        </Button>
      </Box>
      
      <Typography variant="h6" gutterBottom>
        备份文件列表
      </Typography>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : backups.length > 0 ? (
        <>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>备份文件</TableCell>
                  <TableCell>创建时间</TableCell>
                  <TableCell>文件大小</TableCell>
                  <TableCell align="center">操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {backups
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((backup) => (
                    <TableRow key={backup.filename}>
                      <TableCell>{backup.filename}</TableCell>
                      <TableCell>{formatDate(backup.created_at)}</TableCell>
                      <TableCell>{formatFileSize(backup.size)}</TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                          <Tooltip title="下载">
                            <IconButton
                              color="primary"
                              onClick={() => downloadBackup(backup)}
                              size="small"
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="恢复">
                            <IconButton
                              color="secondary"
                              onClick={() => openRestoreDialog(backup)}
                              size="small"
                            >
                              <RestoreIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="删除">
                            <IconButton
                              color="error"
                              onClick={() => openDeleteDialog(backup)}
                              size="small"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={backups.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            labelRowsPerPage="每页行数:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} / 共${count}条`}
          />
        </>
      ) : (
        <Box sx={{ py: 4, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            暂无备份文件，请点击"创建备份"按钮创建新备份
          </Typography>
        </Box>
      )}
      
      {/* 备份设置对话框 */}
      <Dialog open={settingsDialogOpen} onClose={() => setSettingsDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>备份设置</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 0 }}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.auto_backup_enabled}
                    onChange={handleSettingChange}
                    name="auto_backup_enabled"
                    color="primary"
                  />
                }
                label="启用自动备份"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="备份频率"
                name="backup_frequency"
                value={settings.backup_frequency}
                onChange={handleSettingChange}
                fullWidth
                disabled={!settings.auto_backup_enabled}
              >
                <MenuItem value="daily">每日</MenuItem>
                <MenuItem value="weekly">每周</MenuItem>
                <MenuItem value="custom">自定义</MenuItem>
              </TextField>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                label="备份时间"
                name="backup_time"
                type="time"
                value={settings.backup_time}
                onChange={handleSettingChange}
                fullWidth
                InputLabelProps={{
                  shrink: true,
                }}
                disabled={!settings.auto_backup_enabled}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                label="备份保留天数"
                name="keep_days"
                type="number"
                value={settings.keep_days}
                onChange={handleSettingChange}
                fullWidth
                InputProps={{ inputProps: { min: 1 } }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.email_notification}
                    onChange={handleSettingChange}
                    name="email_notification"
                    color="primary"
                    disabled={!settings.auto_backup_enabled}
                  />
                }
                label="备份完成后发送邮件通知"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2" gutterBottom>
                备份方式
              </Typography>
              <FormControl component="fieldset">
                <RadioGroup
                  row
                  name="backup_method"
                  value={settings.backup_method || 'sql'}
                  onChange={handleSettingChange}
                >
                  <FormControlLabel 
                    value="sql" 
                    control={<Radio />} 
                    label="SQL导出备份" 
                  />
                  <FormControlLabel 
                    value="file" 
                    control={<Radio />} 
                    label="数据库文件备份" 
                  />
                  <FormControlLabel 
                    value="json" 
                    control={<Radio />} 
                    label="JSON数据备份" 
                  />
                </RadioGroup>
                <Typography variant="caption" color="text.secondary">
                  {settings.backup_method === 'file' 
                    ? "文件备份：直接复制数据库文件，速度快但需要关闭连接。适用于SQLite数据库。" 
                    : settings.backup_method === 'json'
                    ? "JSON备份：将数据导出为JSON格式，速度快且兼容性好。不依赖数据库工具，推荐使用。"
                    : "SQL导出备份：导出SQL语句，兼容性好但速度较慢。适用于MySQL等数据库。"}
                </Typography>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialogOpen(false)}>取消</Button>
          <Button 
            onClick={saveSettings} 
            variant="contained" 
            color="primary"
            startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
            disabled={loading}
          >
            {loading ? '保存中...' : '保存设置'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>删除备份</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除备份 <b>{selectedBackup?.filename}</b> 吗？此操作无法撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>取消</Button>
          <Button onClick={deleteBackup} color="error">
            删除
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 恢复确认对话框 */}
      <Dialog open={restoreDialogOpen} onClose={() => setRestoreDialogOpen(false)}>
        <DialogTitle>恢复备份</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要从备份 <b>{selectedBackup?.filename}</b> 恢复数据库吗？
            <br /><br />
            <Alert severity="warning">
              此操作将覆盖当前数据库中的所有数据，建议先创建当前数据库的备份。
              恢复操作完成后可能需要重启应用。
            </Alert>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRestoreDialogOpen(false)}>取消</Button>
          <Button onClick={restoreBackup} color="secondary">
            恢复
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 备份进度区域 */}
      <Grid item xs={12}>
        <Collapse in={backupProgress.active}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                  备份进度 - {backupProgress.method}
                </Typography>
                <Chip 
                  label={backupProgress.status} 
                  color={
                    backupProgress.status === 'completed' ? 'success' : 
                    backupProgress.status === 'error' ? 'error' : 'primary'
                  }
                  size="small"
                  icon={getStatusIcon(backupProgress.status)}
                />
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" sx={{ flexGrow: 1 }}>
                    {backupProgress.message}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {backupProgress.progress}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={backupProgress.progress} 
                  color={
                    backupProgress.status === 'error' ? 'error' : 'primary'
                  }
                  sx={{ height: 10, borderRadius: 5 }}
                />
              </Box>
              
              <Box>
                <Button
                  size="small"
                  startIcon={<ExpandMoreIcon />}
                  onClick={toggleShowLogs}
                >
                  {showLogs ? '隐藏日志' : '显示日志'}
                </Button>
                
                <Collapse in={showLogs}>
                  <Paper 
                    variant="outlined" 
                    sx={{ 
                      mt: 2, 
                      p: 2, 
                      maxHeight: 200, 
                      overflow: 'auto',
                      backgroundColor: 'rgba(0, 0, 0, 0.03)'
                    }}
                  >
                    {backupProgress.logs.map((log, index) => (
                      <Typography 
                        key={index} 
                        variant="body2" 
                        fontFamily="monospace"
                        fontSize="0.8rem"
                        whiteSpace="pre-wrap"
                        sx={{ mb: 0.5 }}
                      >
                        {log}
                      </Typography>
                    ))}
                    <div ref={logsEndRef} />
                  </Paper>
                </Collapse>
              </Box>
            </CardContent>
          </Card>
        </Collapse>
      </Grid>
      
      {/* 通知 */}
      <Snackbar
        open={notification.open}
        autoHideDuration={5000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default DatabaseBackup; 