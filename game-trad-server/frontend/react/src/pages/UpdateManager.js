import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Divider, 
  LinearProgress, 
  Alert, 
  Card, 
  CardContent,
  CardActions,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Snackbar
} from '@mui/material';
import { 
  CheckCircle as CheckCircleIcon, 
  Warning as WarningIcon, 
  AccessTime as AccessTimeIcon, 
  CloudDownload as CloudDownloadIcon,
  SystemUpdateAlt as SystemUpdateAltIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';

// 更新状态映射
const updateStatusMap = {
  'idle': { label: '空闲', color: 'default', icon: <AccessTimeIcon /> },
  'available': { label: '可更新', color: 'success', icon: <CheckCircleIcon /> },
  'up-to-date': { label: '已是最新', color: 'primary', icon: <CheckCircleIcon /> },
  'downloading': { label: '下载中', color: 'warning', icon: <CloudDownloadIcon /> },
  'downloaded': { label: '下载完成', color: 'success', icon: <CloudDownloadIcon /> },
  'installing': { label: '安装中', color: 'warning', icon: <SystemUpdateAltIcon /> },
  'completed': { label: '更新完成', color: 'success', icon: <CheckCircleIcon /> },
  'error': { label: '错误', color: 'error', icon: <WarningIcon /> }
};

function UpdateManager() {
  const [updateStatus, setUpdateStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  // 获取更新状态
  const fetchUpdateStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/update/status');
      
      if (response.data.success) {
        setUpdateStatus(response.data.status);
      } else {
        throw new Error(response.data.message || '获取更新状态失败');
      }
    } catch (err) {
      setError(err.message || '获取更新状态时发生错误');
      setOpenSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  // 检查更新
  const handleCheckUpdate = async () => {
    try {
      setLoading(true);
      setUpdateSuccess(false);
      const response = await axios.post('/api/update/check');
      
      if (response.data.success) {
        setUpdateStatus(response.data.status);
        
        if (response.data.updateAvailable) {
          setUpdateSuccess(true);
          setError('发现新版本可用');
        } else {
          setUpdateSuccess(true);
          setError('已是最新版本');
        }
        setOpenSnackbar(true);
      } else {
        throw new Error(response.data.message || '检查更新失败');
      }
    } catch (err) {
      setError(err.message || '检查更新时发生错误');
      setOpenSnackbar(true);
      setUpdateSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  // 下载更新
  const handleDownloadUpdate = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/update/download');
      
      if (response.data.success) {
        setUpdateStatus(response.data.status);
        setUpdateSuccess(true);
        setError('更新下载成功');
        setOpenSnackbar(true);
      } else {
        throw new Error(response.data.message || '下载更新失败');
      }
    } catch (err) {
      setError(err.message || '下载更新时发生错误');
      setOpenSnackbar(true);
      setUpdateSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  // 安装更新
  const handleInstallUpdate = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/update/install');
      
      if (response.data.success) {
        setUpdateStatus(response.data.status);
        setUpdateSuccess(true);
        setError('更新安装成功');
        setOpenSnackbar(true);
      } else {
        throw new Error(response.data.message || '安装更新失败');
      }
    } catch (err) {
      setError(err.message || '安装更新时发生错误');
      setOpenSnackbar(true);
      setUpdateSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  // 处理Snackbar关闭
  const handleCloseSnackbar = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpenSnackbar(false);
  };

  // 组件挂载时获取更新状态
  useEffect(() => {
    fetchUpdateStatus();
    
    // 定时刷新状态
    const intervalId = setInterval(() => {
      if (updateStatus && ['downloading', 'installing'].includes(updateStatus.updateStatus)) {
        fetchUpdateStatus();
      }
    }, 2000);
    
    return () => clearInterval(intervalId);
  }, [updateStatus]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        更新管理
      </Typography>
      
      <Grid container spacing={3}>
        {/* 当前状态 */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              当前版本状态
            </Typography>
            
            {loading && !updateStatus ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : updateStatus ? (
              <List>
                <ListItem>
                  <ListItemIcon>
                    <SystemUpdateAltIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="当前版本" 
                    secondary={updateStatus.currentVersion || '未知'} 
                  />
                </ListItem>
                
                {updateStatus.availableVersion && (
                  <ListItem>
                    <ListItemIcon>
                      <CloudDownloadIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary="可用版本" 
                      secondary={updateStatus.availableVersion} 
                    />
                  </ListItem>
                )}
                
                <ListItem>
                  <ListItemIcon>
                    <AccessTimeIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="最后检查时间" 
                    secondary={
                      updateStatus.lastChecked 
                        ? new Date(updateStatus.lastChecked).toLocaleString() 
                        : '从未检查'
                    } 
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemIcon>
                    {updateStatusMap[updateStatus.updateStatus]?.icon || <AccessTimeIcon />}
                  </ListItemIcon>
                  <ListItemText 
                    primary="更新状态" 
                    secondary={
                      <Chip 
                        label={updateStatusMap[updateStatus.updateStatus]?.label || updateStatus.updateStatus} 
                        color={updateStatusMap[updateStatus.updateStatus]?.color || 'default'} 
                        size="small" 
                      />
                    } 
                  />
                </ListItem>
                
                {(updateStatus.updateStatus === 'downloading' || updateStatus.updateStatus === 'downloaded') && (
                  <ListItem>
                    <Box sx={{ width: '100%' }}>
                      <Typography variant="body2" gutterBottom>
                        下载进度: {updateStatus.downloadProgress}%
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={updateStatus.downloadProgress} 
                        sx={{ height: 10, borderRadius: 5 }} 
                      />
                    </Box>
                  </ListItem>
                )}
                
                {(updateStatus.updateStatus === 'installing' || updateStatus.updateStatus === 'completed') && (
                  <ListItem>
                    <Box sx={{ width: '100%' }}>
                      <Typography variant="body2" gutterBottom>
                        安装进度: {updateStatus.installProgress}%
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={updateStatus.installProgress} 
                        sx={{ height: 10, borderRadius: 5 }} 
                      />
                    </Box>
                  </ListItem>
                )}
                
                {updateStatus.error && (
                  <ListItem>
                    <Alert severity="error" sx={{ width: '100%' }}>
                      {updateStatus.error}
                    </Alert>
                  </ListItem>
                )}
              </List>
            ) : (
              <Alert severity="info">
                无法获取更新状态信息
              </Alert>
            )}
            
            <Divider sx={{ my: 2 }} />
            
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
              <Button 
                variant="outlined" 
                onClick={fetchUpdateStatus}
                disabled={loading}
              >
                刷新状态
              </Button>
              <Button 
                variant="contained" 
                onClick={handleCheckUpdate}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : null}
              >
                检查更新
              </Button>
            </Box>
          </Paper>
        </Grid>
        
        {/* 更新操作 */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              更新操作
            </Typography>
            
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  下载更新
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  从服务器下载最新版本的安装包
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  size="small" 
                  color="primary"
                  onClick={handleDownloadUpdate}
                  disabled={
                    loading || 
                    !updateStatus || 
                    !updateStatus.updateAvailable || 
                    ['downloading', 'downloaded', 'installing', 'completed'].includes(updateStatus.updateStatus)
                  }
                  startIcon={
                    updateStatus && updateStatus.updateStatus === 'downloading' 
                      ? <CircularProgress size={16} /> 
                      : null
                  }
                >
                  {updateStatus && updateStatus.updateStatus === 'downloading' 
                    ? '下载中...' 
                    : updateStatus && updateStatus.updateStatus === 'downloaded'
                      ? '已下载' 
                      : '下载更新'}
                </Button>
              </CardActions>
            </Card>
            
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  安装更新
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  安装已下载的更新包并重启服务
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  size="small" 
                  color="primary"
                  onClick={handleInstallUpdate}
                  disabled={
                    loading || 
                    !updateStatus || 
                    updateStatus.updateStatus !== 'downloaded'
                  }
                  startIcon={
                    updateStatus && updateStatus.updateStatus === 'installing' 
                      ? <CircularProgress size={16} /> 
                      : null
                  }
                >
                  {updateStatus && updateStatus.updateStatus === 'installing' 
                    ? '安装中...' 
                    : updateStatus && updateStatus.updateStatus === 'completed'
                      ? '已完成' 
                      : '安装更新'}
                </Button>
              </CardActions>
            </Card>
          </Paper>
        </Grid>
        
        {/* 更新日志 */}
        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              更新日志
            </Typography>
            
            {updateStatus && updateStatus.availableVersion ? (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  版本 {updateStatus.availableVersion} 更新内容:
                </Typography>
                <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <ReactMarkdown>
                    {`## 更新内容\n\n- 修复了仪表盘显示问题\n- 优化数据导入功能\n- 提升系统稳定性`}
                  </ReactMarkdown>
                </Box>
              </Box>
            ) : (
              <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                无可用更新或尚未检查更新
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      <Snackbar 
        open={openSnackbar} 
        autoHideDuration={6000} 
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={updateSuccess ? "success" : "error"} 
          sx={{ width: '100%' }}
        >
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default UpdateManager; 