import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Paper,
  Typography,
  Box,
  TextField,
  FormControlLabel,
  Switch,
  Button,
  Grid,
  Divider,
  Alert,
  Snackbar,
  IconButton,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import {
  Send as SendIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Email as EmailIcon
} from '@mui/icons-material';

const EmailConfig = () => {
  // 状态
  const [config, setConfig] = useState({
    enabled: false,
    smtp_server: 'smtp.qq.com',
    smtp_port: 587,
    username: '',
    password: '',
    sender: 'GameTrad系统',
    recipients: [],
    retry_count: 3,
    retry_delay: 5,
    enable_log: true,
    log_days: 30,
    enable_daily_report: false,
    daily_report_time: '20:00'
  });
  
  const [newRecipient, setNewRecipient] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [recipientToDelete, setRecipientToDelete] = useState(null);

  // 加载配置
  useEffect(() => {
    fetchConfig();
  }, []);

  // 获取配置
  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/settings/email-config');
      
      if (response.data && response.data.success) {
        setConfig(response.data.config);
      }
    } catch (err) {
      showNotification(`加载配置失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 保存配置
  const saveConfig = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/settings/email-config', config);
      
      if (response.data && response.data.success) {
        showNotification('邮件配置已保存', 'success');
      } else {
        showNotification(`保存失败: ${response.data.message}`, 'error');
      }
    } catch (err) {
      showNotification(`保存配置失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 测试连接
  const testConnection = async () => {
    try {
      setTestLoading(true);
      const response = await axios.post('/api/settings/email-test', config);
      
      if (response.data && response.data.success) {
        showNotification('邮件发送测试成功！已向设置的收件人发送测试邮件', 'success');
      } else {
        showNotification(`测试失败: ${response.data.message}`, 'error');
      }
    } catch (err) {
      showNotification(`测试连接失败: ${err.message}`, 'error');
    } finally {
      setTestLoading(false);
    }
  };

  // 处理输入变化
  const handleChange = (e) => {
    const { name, value, checked, type } = e.target;
    
    setConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // 添加收件人
  const handleAddRecipient = () => {
    if (newRecipient && isValidEmail(newRecipient)) {
      if (config.recipients.includes(newRecipient)) {
        showNotification('此邮箱地址已在收件人列表中', 'warning');
        return;
      }
      
      setConfig(prev => ({
        ...prev,
        recipients: [...prev.recipients, newRecipient]
      }));
      setNewRecipient('');
    } else {
      showNotification('请输入有效的邮箱地址', 'error');
    }
  };

  // 删除收件人对话框
  const openDeleteDialog = (recipient) => {
    setRecipientToDelete(recipient);
    setDeleteDialogOpen(true);
  };

  // 确认删除收件人
  const handleDeleteRecipient = () => {
    if (recipientToDelete) {
      setConfig(prev => ({
        ...prev,
        recipients: prev.recipients.filter(r => r !== recipientToDelete)
      }));
      setDeleteDialogOpen(false);
      setRecipientToDelete(null);
    }
  };

  // 验证邮箱
  const isValidEmail = (email) => {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
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

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <EmailIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h5" component="h2">
          QQ邮箱推送设置
        </Typography>
      </Box>
      
      <FormControlLabel
        control={
          <Switch
            checked={config.enabled}
            onChange={handleChange}
            name="enabled"
            color="primary"
          />
        }
        label="启用邮件推送"
        sx={{ mb: 2 }}
      />
      
      <Divider sx={{ mb: 3 }} />
      
      <Grid container spacing={3}>
        {/* 服务器设置 */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            邮件服务器设置
          </Typography>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="SMTP服务器"
            name="smtp_server"
            value={config.smtp_server}
            onChange={handleChange}
            fullWidth
            required
            helperText="例如：smtp.qq.com"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="SMTP端口"
            name="smtp_port"
            type="number"
            value={config.smtp_port}
            onChange={handleChange}
            fullWidth
            required
            helperText="例如：587或465"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="邮箱账号"
            name="username"
            value={config.username}
            onChange={handleChange}
            fullWidth
            required
            helperText="例如：example@qq.com"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="密码/授权码"
            name="password"
            type={showPassword ? 'text' : 'password'}
            value={config.password}
            onChange={handleChange}
            fullWidth
            required
            helperText="QQ邮箱需要使用授权码而非登录密码"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="发件人名称"
            name="sender"
            value={config.sender}
            onChange={handleChange}
            fullWidth
            helperText="发送邮件时显示的发件人名称"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
            <Button
              variant="contained"
              color="secondary"
              disabled={testLoading || loading}
              onClick={testConnection}
              startIcon={testLoading ? <CircularProgress size={20} /> : <SendIcon />}
              sx={{ ml: 'auto', mt: 1 }}
            >
              {testLoading ? '测试中...' : '测试连接'}
            </Button>
          </Box>
        </Grid>
        
        {/* 收件人设置 */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            收件人设置
          </Typography>
        </Grid>
        
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
            <TextField
              label="添加收件人"
              value={newRecipient}
              onChange={(e) => setNewRecipient(e.target.value)}
              helperText="输入邮箱地址后点击添加"
              fullWidth
              sx={{ mr: 1 }}
            />
            <Button
              variant="contained"
              onClick={handleAddRecipient}
              startIcon={<AddIcon />}
              sx={{ mt: 1 }}
            >
              添加
            </Button>
          </Box>
          
          <Box sx={{ backgroundColor: 'background.paper', p: 2, borderRadius: 1, mb: 2 }}>
            {config.recipients.length > 0 ? (
              <Grid container spacing={1}>
                {config.recipients.map((recipient, index) => (
                  <Grid item key={index}>
                    <Chip
                      label={recipient}
                      onDelete={() => openDeleteDialog(recipient)}
                      color="primary"
                      variant="outlined"
                    />
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Typography variant="body2" color="text.secondary" align="center">
                尚未添加收件人
              </Typography>
            )}
          </Box>
        </Grid>
        
        {/* 高级设置 */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            高级设置
          </Typography>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Switch
                checked={config.enable_log}
                onChange={handleChange}
                name="enable_log"
                color="primary"
              />
            }
            label="启用邮件日志"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="日志保留天数"
            name="log_days"
            type="number"
            value={config.log_days}
            onChange={handleChange}
            fullWidth
            InputProps={{ inputProps: { min: 1 } }}
            disabled={!config.enable_log}
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="重试次数"
            name="retry_count"
            type="number"
            value={config.retry_count}
            onChange={handleChange}
            fullWidth
            InputProps={{ inputProps: { min: 0, max: 10 } }}
            helperText="发送失败时的重试次数"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="重试间隔(秒)"
            name="retry_delay"
            type="number"
            value={config.retry_delay}
            onChange={handleChange}
            fullWidth
            InputProps={{ inputProps: { min: 1 } }}
            helperText="重试之间的等待时间"
          />
        </Grid>
        
        {/* 日报设置 */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            日报设置
          </Typography>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Switch
                checked={config.enable_daily_report}
                onChange={handleChange}
                name="enable_daily_report"
                color="primary"
              />
            }
            label="启用每日报告"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            label="报告发送时间"
            name="daily_report_time"
            type="time"
            value={config.daily_report_time}
            onChange={handleChange}
            fullWidth
            InputLabelProps={{ shrink: true }}
            disabled={!config.enable_daily_report}
            helperText="每日发送摘要报告的时间"
          />
        </Grid>
        
        {/* 操作按钮 */}
        <Grid item xs={12}>
          <Divider sx={{ my: 2 }} />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button
              variant="outlined"
              onClick={fetchConfig}
              startIcon={<RefreshIcon />}
              sx={{ mr: 2 }}
              disabled={loading}
            >
              重置
            </Button>
            <Button
              variant="contained"
              onClick={saveConfig}
              startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
              disabled={loading}
            >
              {loading ? '保存中...' : '保存设置'}
            </Button>
          </Box>
        </Grid>
      </Grid>
      
      {/* 删除确认对话框 */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>删除收件人</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除收件人 {recipientToDelete} 吗？
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>取消</Button>
          <Button onClick={handleDeleteRecipient} color="error">
            删除
          </Button>
        </DialogActions>
      </Dialog>
      
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

export default EmailConfig; 