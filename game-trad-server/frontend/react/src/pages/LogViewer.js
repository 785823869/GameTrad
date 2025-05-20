import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Chip,
  Grid,
  CircularProgress,
  Alert,
  IconButton,
  InputAdornment
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Search as SearchIcon
} from '@mui/icons-material';

const LOG_LEVELS = {
  ERROR: 'error',
  WARN: 'warning',
  INFO: 'info',
  DEBUG: 'default'
};

const LogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [logType, setLogType] = useState('app');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [limit, setLimit] = useState(200);
  const listRef = useRef(null);

  // 获取日志数据
  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/logs/${logType}?limit=${limit}`);
      setLogs(response.data);
      setError(null);
    } catch (err) {
      console.error('获取日志数据失败:', err);
      setError('无法加载日志数据。请检查网络连接或服务器状态。');
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    fetchLogs();
  }, [logType, limit]);

  // 过滤日志
  useEffect(() => {
    let filtered = [...logs];
    
    // 按级别过滤
    if (selectedLevel !== 'all') {
      filtered = filtered.filter(log => 
        log.level && log.level.toLowerCase() === selectedLevel.toLowerCase()
      );
    }
    
    // 按搜索词过滤
    if (searchTerm.trim() !== '') {
      filtered = filtered.filter(log => 
        (log.message && log.message.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (log.raw && log.raw.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    setFilteredLogs(filtered);
  }, [logs, selectedLevel, searchTerm]);

  // 清除过滤器
  const handleClearFilters = () => {
    setSelectedLevel('all');
    setSearchTerm('');
  };

  // 获取日志级别的样式
  const getLevelStyle = (level) => {
    if (!level) return { color: 'default' };
    
    const normalizedLevel = level.toUpperCase();
    switch (normalizedLevel) {
      case 'ERROR':
        return { color: 'error' };
      case 'WARN':
        return { color: 'warning' };
      case 'INFO':
        return { color: 'info' };
      case 'DEBUG':
        return { color: 'default' };
      default:
        return { color: 'default' };
    }
  };

  // 下载日志
  const handleDownloadLogs = () => {
    // 准备日志内容
    const content = filteredLogs.map(log => {
      if (log.raw) return log.raw;
      return `[${log.timestamp || ''}] [${log.level || ''}] ${log.message || ''}`;
    }).join('\n');
    
    // 创建下载链接
    const element = document.createElement('a');
    const file = new Blob([content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `gameTrad_${logType}_logs_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          日志查看器
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadLogs}
            disabled={loading || filteredLogs.length === 0}
            sx={{ mr: 1 }}
          >
            下载日志
          </Button>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={fetchLogs}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 4 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel id="log-type-label">日志类型</InputLabel>
              <Select
                labelId="log-type-label"
                id="log-type"
                value={logType}
                label="日志类型"
                onChange={(e) => setLogType(e.target.value)}
              >
                <MenuItem value="app">应用日志</MenuItem>
                <MenuItem value="error">错误日志</MenuItem>
                <MenuItem value="access">访问日志</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel id="log-level-label">日志级别</InputLabel>
              <Select
                labelId="log-level-label"
                id="log-level"
                value={selectedLevel}
                label="日志级别"
                onChange={(e) => setSelectedLevel(e.target.value)}
              >
                <MenuItem value="all">全部级别</MenuItem>
                <MenuItem value="error">错误</MenuItem>
                <MenuItem value="warn">警告</MenuItem>
                <MenuItem value="info">信息</MenuItem>
                <MenuItem value="debug">调试</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel id="log-limit-label">显示条数</InputLabel>
              <Select
                labelId="log-limit-label"
                id="log-limit"
                value={limit}
                label="显示条数"
                onChange={(e) => setLimit(e.target.value)}
              >
                <MenuItem value={50}>50 条</MenuItem>
                <MenuItem value={100}>100 条</MenuItem>
                <MenuItem value={200}>200 条</MenuItem>
                <MenuItem value={500}>500 条</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              placeholder="搜索日志..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: searchTerm && (
                  <InputAdornment position="end">
                    <IconButton
                      size="small"
                      onClick={() => setSearchTerm('')}
                      edge="end"
                    >
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <FilterIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  过滤条件:
                </Typography>
                {selectedLevel !== 'all' && (
                  <Chip 
                    label={`级别: ${selectedLevel}`} 
                    size="small" 
                    onDelete={() => setSelectedLevel('all')} 
                    sx={{ ml: 1 }} 
                  />
                )}
                {searchTerm && (
                  <Chip 
                    label={`搜索: ${searchTerm}`} 
                    size="small" 
                    onDelete={() => setSearchTerm('')} 
                    sx={{ ml: 1 }} 
                  />
                )}
              </Box>
              {(selectedLevel !== 'all' || searchTerm) && (
                <Button 
                  size="small" 
                  startIcon={<ClearIcon />} 
                  onClick={handleClearFilters}
                >
                  清除过滤
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ height: 'calc(100vh - 300px)', overflow: 'auto' }} ref={listRef}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : filteredLogs.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="text.secondary">没有找到匹配的日志记录</Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {filteredLogs.map((log, index) => (
              <React.Fragment key={index}>
                <ListItem sx={{ py: 1 }}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {log.timestamp && (
                          <Typography variant="body2" color="text.secondary" sx={{ mr: 2, fontFamily: 'monospace' }}>
                            {new Date(log.timestamp).toLocaleString()}
                          </Typography>
                        )}
                        {log.level && (
                          <Chip 
                            label={log.level} 
                            size="small" 
                            {...getLevelStyle(log.level)}
                            sx={{ mr: 2 }} 
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          whiteSpace: 'pre-wrap', 
                          wordBreak: 'break-all',
                          fontFamily: 'monospace',
                          ...(log.level === 'ERROR' && { color: 'error.main' })
                        }}
                      >
                        {log.message || log.raw || ''}
                      </Typography>
                    }
                  />
                </ListItem>
                {index < filteredLogs.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>
    </Container>
  );
};

export default LogViewer; 