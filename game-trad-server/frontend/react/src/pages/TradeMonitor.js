import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  IconButton,
  Snackbar
} from '@mui/material';
import { 
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  CloudUpload as ImportIcon
} from '@mui/icons-material';
import OCRDialog from '../components/OCRDialog';

const TradeMonitor = () => {
  // CSS样式变量
  const styles = {
    borderRadius: {
      small: '4px',
      medium: '8px',
      large: '12px',
      pill: '20px'
    },
    boxShadow: {
      light: '0 2px 4px rgba(0,0,0,0.05)',
      medium: '0 4px 8px rgba(0,0,0,0.1)',
      heavy: '0 8px 16px rgba(0,0,0,0.12)'
    },
    transition: 'all 0.2s ease-in-out',
    spacing: {
      xs: 1,
      sm: 2,
      md: 3,
      lg: 4
    }
  };

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tradeItems, setTradeItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('profit_rate');
  const [sortOrder, setSortOrder] = useState('desc');
  const [formOpen, setFormOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState(null);
  const [formData, setFormData] = useState({
    item_name: '',
    quantity: 0,
    market_price: 0,
    target_price: 0,
    planned_price: 0,
    strategy: ''
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [ocrDialogOpen, setOcrDialogOpen] = useState(false);
  
  const fileInputRef = useRef();

  // 获取交易监控数据
  const fetchTradeItems = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/status/trade-monitor');
      
      if (response.data && response.data.success) {
        setTradeItems(response.data.items);
        setError(null);
      } else {
        setError('获取交易监控数据失败');
        setTradeItems([]);
      }
    } catch (err) {
      setError(`获取交易监控数据失败: ${err.message}`);
      setTradeItems([]);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    fetchTradeItems();
  }, []);

  // 处理筛选和排序
  useEffect(() => {
    // 先筛选
    let filtered = tradeItems;
    if (searchTerm) {
      filtered = tradeItems.filter(item => 
        item.item_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // 再排序
    filtered = [...filtered].sort((a, b) => {
      if (sortOrder === 'asc') {
        return a[sortBy] - b[sortBy];
      } else {
        return b[sortBy] - a[sortBy];
      }
    });
    
    setFilteredItems(filtered);
  }, [tradeItems, searchTerm, sortBy, sortOrder]);

  // 处理搜索
  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };
  
  // 处理排序方式改变
  const handleSortByChange = (event) => {
    setSortBy(event.target.value);
  };
  
  // 处理排序顺序改变
  const handleSortOrderChange = (event) => {
    setSortOrder(event.target.value);
  };

  // 格式化价格
  const formatPrice = (price) => {
    if (price === 0 || !price) return '—';
    return `¥ ${parseFloat(price).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };
  
  // 格式化百分比
  const formatPercent = (value) => {
    if (value === 0 || !value) return '0.00%';
    return `${(value * 100).toFixed(2)}%`;
  };

  // 格式化日期时间
  const formatDateTime = (dateTime) => {
    if (!dateTime) return '';
    
    const date = new Date(dateTime);
    if (isNaN(date.getTime())) return '';
    
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 打开添加记录对话框
  const handleAddItem = () => {
    setCurrentItem(null);
    setFormData({
      item_name: '',
      quantity: 0,
      market_price: 0,
      target_price: 0,
      planned_price: 0,
      strategy: ''
    });
    setFormOpen(true);
  };
  
  // 打开编辑记录对话框
  const handleEditItem = (item) => {
    setCurrentItem(item);
    setFormData({
      item_name: item.item_name,
      quantity: item.quantity,
      market_price: item.market_price,
      target_price: item.target_price || 0,
      planned_price: item.planned_price || 0,
      strategy: item.strategy || ''
    });
    setFormOpen(true);
  };
  
  // 表单字段变更处理
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };
  
  // 保存表单数据
  const handleSaveForm = async () => {
    try {
      // 构建符合trade_monitor表结构的数据
      const monitorData = {
        item_name: formData.item_name,
        quantity: parseInt(formData.quantity) || 0,
        market_price: parseFloat(formData.market_price) || 0,
        target_price: parseFloat(formData.target_price) || 0,
        planned_price: parseFloat(formData.planned_price) || 0,
        strategy: formData.strategy || '',
        monitor_time: new Date().toISOString()
      };

      // 如果是编辑现有记录，添加ID
      if (currentItem && currentItem.id) {
        monitorData.id = currentItem.id;
      }
      
      // 使用trade-monitor API
      const response = await axios.post('/api/status/trade-monitor', monitorData);
      
      if (response.data.success) {
        setFormOpen(false);
        setNotification({
          open: true,
          message: currentItem ? '记录已更新' : '记录已添加',
          severity: 'success'
        });
        fetchTradeItems();
      }
    } catch (err) {
      setNotification({
        open: true,
        message: `保存失败: ${err.message}`,
        severity: 'error'
      });
    }
  };
  
  // 打开删除对话框
  const handleDeleteItem = (item) => {
    setCurrentItem(item);
    setDeleteDialogOpen(true);
  };
  
  // 确认删除
  const handleConfirmDelete = async () => {
    try {
      const response = await axios.delete(`/api/status/trade-monitor/${currentItem.id}`);
      if (response.data.success) {
        setDeleteDialogOpen(false);
        setNotification({
          open: true,
          message: '记录已删除',
          severity: 'success'
        });
        fetchTradeItems();
      }
    } catch (err) {
      setNotification({
        open: true,
        message: `删除失败: ${err.message}`,
        severity: 'error'
      });
    }
  };
  
  // OCR相关功能
  const handleOpenOcrDialog = () => {
    setOcrDialogOpen(true);
  };
  
  const handleCloseOcrDialog = () => {
    setOcrDialogOpen(false);
  };

  // 处理OCR导入
  const handleOcrImport = (ocrResults) => {
    try {
      console.log("OCR识别结果:", ocrResults);
      
      // 检查是否收到有效数据
      if (!Array.isArray(ocrResults) || ocrResults.length === 0) {
        setNotification({
          open: true,
          message: '没有有效的OCR数据可导入',
          severity: 'warning'
        });
        return;
      }
      
      // 转换OCR结果为交易监控记录格式
      const monitorItems = ocrResults.map(item => ({
        item_name: item.item_name,
        quantity: Number(item.quantity) || 0,
        market_price: Number(item.unit_price || item.price || 0),
        target_price: 0,
        planned_price: 0,
        monitor_time: new Date().toISOString().replace('T', ' ').replace(/\.\d+Z$/, ''),
        break_even_price: 0,
        profit: 0,
        profit_rate: 0,
        strategy: item.note || '',
      }));
      
      console.log("转换后的交易监控数据:", monitorItems);
      
      // 保存到后端API
      setLoading(true);
      
      // 导入到后端 - 使用批量添加方式
      const importPromises = monitorItems.map(item => 
        axios.post('/api/status/trade-monitor', item)
      );
      
      // 批量处理所有导入请求
      Promise.all(importPromises)
        .then(responses => {
          const successCount = responses.filter(res => res.data.success).length;
          
          if (successCount > 0) {
            setNotification({
              open: true,
              message: `成功导入${successCount}条记录`,
              severity: 'success'
            });
            
            // 刷新数据
            fetchTradeItems();
          } else {
            setNotification({
              open: true,
              message: '导入失败，没有成功导入的记录',
              severity: 'error'
            });
          }
        })
        .catch(err => {
          console.error('导入OCR结果失败:', err);
          setNotification({
            open: true,
            message: `导入OCR结果失败: ${err.response?.data?.message || err.message}`,
            severity: 'error'
          });
        })
        .finally(() => {
          setLoading(false);
        });
    } catch (err) {
      console.error('处理OCR结果失败:', err);
      setNotification({
        open: true,
        message: `处理OCR结果失败: ${err.message}`,
        severity: 'error'
      });
    }
  };

  // 关闭通知
  const handleCloseNotification = () => {
    setNotification({
      ...notification,
      open: false
    });
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ 
          display: 'flex', 
          alignItems: 'center',
          fontWeight: 500,
          color: 'primary.dark'
        }}>
          <TrendingUpIcon sx={{ mr: 1, color: 'primary.main' }} />
          交易监控
        </Typography>
        <Box sx={{ 
          display: 'flex', 
          gap: styles.spacing.xs
        }}>
          <Button
            variant="outlined"
            startIcon={<ImportIcon />}
            onClick={handleOpenOcrDialog}
            color="info"
            sx={{ 
              borderRadius: styles.borderRadius.medium,
              textTransform: 'none',
              boxShadow: styles.boxShadow.light,
              transition: styles.transition
            }}
          >
            OCR导入
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleAddItem}
            color="secondary"
            sx={{ 
              borderRadius: styles.borderRadius.medium,
              textTransform: 'none',
              boxShadow: styles.boxShadow.light,
              transition: styles.transition
            }}
          >
            添加监控
          </Button>
          <Button
            variant="contained"
            startIcon={<RefreshIcon sx={{ animation: loading ? 'spin 2s linear infinite' : 'none' }} />}
            onClick={fetchTradeItems}
            disabled={loading}
            sx={{ 
              borderRadius: styles.borderRadius.medium,
              textTransform: 'none',
              boxShadow: styles.boxShadow.medium,
              transition: styles.transition,
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' }
              }
            }}
          >
            {loading ? '加载中...' : '刷新数据'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 4, borderRadius: styles.borderRadius.large, boxShadow: styles.boxShadow.medium }}>
        <Box sx={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: 2, 
          mb: 3,
          alignItems: 'center',
          pb: 2,
          borderBottom: '1px solid rgba(0,0,0,0.06)'
        }}>
          <TextField
            label="搜索物品"
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={handleSearch}
            placeholder="输入物品名称..."
            InputProps={{
              startAdornment: (
                <Box sx={{ color: 'action.active', mr: 1, mt: 0.5 }}>
                  <span role="img" aria-label="search">🔍</span>
                </Box>
              ),
            }}
            sx={{ 
              minWidth: 220,
              '& .MuiOutlinedInput-root': {
                borderRadius: '8px',
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'primary.light',
                },
              }
            }}
          />
          <FormControl size="small" sx={{ 
            minWidth: 160,
            '& .MuiOutlinedInput-root': {
              borderRadius: '8px',
            }
          }}>
            <InputLabel>排序方式</InputLabel>
            <Select
              value={sortBy}
              label="排序方式"
              onChange={handleSortByChange}
            >
              <MenuItem value="profit_rate">利润率</MenuItem>
              <MenuItem value="profit">单位利润</MenuItem>
              <MenuItem value="market_price">市场价格</MenuItem>
              <MenuItem value="quantity">库存数量</MenuItem>
              <MenuItem value="target_price">目标买入价</MenuItem>
              <MenuItem value="planned_price">计划卖出价</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ 
            minWidth: 120,
            '& .MuiOutlinedInput-root': {
              borderRadius: '8px',
            }
          }}>
            <InputLabel>排序顺序</InputLabel>
            <Select
              value={sortOrder}
              label="排序顺序"
              onChange={handleSortOrderChange}
            >
              <MenuItem value="desc">降序</MenuItem>
              <MenuItem value="asc">升序</MenuItem>
            </Select>
          </FormControl>
          {filteredItems.length > 0 && (
            <Box sx={{ 
              ml: 'auto', 
              backgroundColor: 'info.light', 
              color: 'info.dark', 
              px: 2, 
              py: 0.5, 
              borderRadius: '16px',
              fontSize: '0.875rem',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center'
            }}>
              共 {filteredItems.length} 条记录
            </Box>
          )}
        </Box>
        
        {loading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 5 }}>
            <CircularProgress size={50} thickness={4} sx={{ mb: 2 }} />
            <Typography variant="body1" color="text.secondary">加载数据中，请稍候...</Typography>
          </Box>
        ) : (
          <TableContainer sx={{ 
            maxHeight: 'calc(100vh - 380px)', 
            overflow: 'auto',
            "&::-webkit-scrollbar": {
              width: "8px",
              height: "8px"
            },
            "&::-webkit-scrollbar-track": {
              backgroundColor: "rgba(0,0,0,0.03)"
            },
            "&::-webkit-scrollbar-thumb": {
              backgroundColor: "rgba(0,0,0,0.15)",
              borderRadius: "4px",
              "&:hover": {
                backgroundColor: "rgba(0,0,0,0.3)"
              }
            }
          }}>
            <Table stickyHeader size="small" sx={{ minWidth: 650 }}>
              <TableHead>
                <TableRow>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold', 
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '13%'
                    }}
                  >
                    物品名称
                  </TableCell>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '11%'
                    }}
                  >
                    监控时间
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '7%'
                    }}
                  >
                    库存数量
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '9%'
                    }}
                  >
                    市场价格
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '9%'
                    }}
                  >
                    目标买入价
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '9%'
                    }}
                  >
                    计划卖出价
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '9%'
                    }}
                  >
                    成本价格
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '9%'
                    }}
                  >
                    单位利润
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '9%'
                    }}
                  >
                    利润率
                  </TableCell>
                  <TableCell 
                    align="center"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 16px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '10%'
                    }}
                  >
                    策略
                  </TableCell>
                  <TableCell 
                    align="center"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.paper',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      padding: '8px 10px',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '5%'
                    }}
                  >
                    操作
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredItems.length > 0 ? (
                  filteredItems.map((item, index) => (
                    <TableRow 
                      key={item.id || item.item_name}
                      sx={{ 
                        "&:nth-of-type(odd)": { 
                          backgroundColor: "rgba(0, 0, 0, 0.02)" 
                        },
                        "&:hover": {
                          backgroundColor: "rgba(25, 118, 210, 0.08)"
                        },
                        height: '48px'
                      }}
                    >
                      <TableCell component="th" scope="row" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', padding: '4px 16px' }}>
                        <Tooltip title={item.item_name} placement="top">
                          <span>{item.item_name}</span>
                        </Tooltip>
                      </TableCell>
                      <TableCell sx={{ whiteSpace: 'nowrap', padding: '4px 16px', fontSize: '0.875rem' }}>{formatDateTime(item.monitor_time)}</TableCell>
                      <TableCell align="right" sx={{ padding: '4px 16px', fontWeight: item.quantity > 0 ? 500 : 400 }}>{item.quantity}</TableCell>
                      <TableCell align="right" sx={{ padding: '4px 16px' }}>{formatPrice(item.market_price)}</TableCell>
                      <TableCell align="right" sx={{ color: item.target_price ? 'primary.dark' : 'text.secondary', fontWeight: item.target_price ? 700 : 400, padding: '4px 16px' }}>
                        {formatPrice(item.target_price || 0)}
                      </TableCell>
                      <TableCell align="right" sx={{ color: item.planned_price ? 'success.main' : 'text.secondary', fontWeight: item.planned_price ? 700 : 400, padding: '4px 16px' }}>
                        {formatPrice(item.planned_price || 0)}
                      </TableCell>
                      <TableCell align="right" sx={{ padding: '4px 16px' }}>{formatPrice(item.break_even_price)}</TableCell>
                      <TableCell align="right" sx={{ 
                        color: (item.profit || 0) > 0 ? 'success.main' : (item.profit || 0) < 0 ? 'error.main' : 'text.secondary', 
                        fontWeight: (item.profit || 0) !== 0 ? 700 : 400,
                        padding: '4px 16px'
                      }}>
                        {formatPrice(item.profit)}
                      </TableCell>
                      <TableCell align="right" sx={{ padding: '4px 16px' }}>
                        <Chip
                          label={formatPercent(item.profit_rate)}
                          size="small"
                          color={(item.profit_rate || 0) > 0 ? "success" : (item.profit_rate || 0) < 0 ? "error" : "default"}
                          sx={{
                            fontWeight: 'bold',
                            minWidth: '70px',
                            height: '24px'
                          }}
                        />
                      </TableCell>
                      <TableCell align="center" sx={{ 
                        padding: '4px 16px',
                        maxWidth: '120px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {item.strategy ? (
                          <Tooltip title={item.strategy} placement="top">
                            <span>{item.strategy}</span>
                          </Tooltip>
                        ) : '—'}
                      </TableCell>
                      <TableCell align="center" sx={{ padding: '4px 8px' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                          <Tooltip title="编辑" placement="top">
                            <IconButton color="primary" size="small" onClick={() => handleEditItem(item)} sx={{ padding: '2px' }}>
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="删除" placement="top">
                            <IconButton color="error" size="small" onClick={() => handleDeleteItem(item)} sx={{ padding: '2px' }}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={11} align="center" sx={{ py: 5 }}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 3 }}>
                        <Box sx={{ 
                          fontSize: '48px', 
                          mb: 2, 
                          opacity: 0.5, 
                          color: 'text.secondary'
                        }}>
                          📊
                        </Box>
                        <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                          暂无交易监控数据
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: '450px', textAlign: 'center' }}>
                          您可以通过"添加监控"按钮手动添加，或使用"OCR导入"功能批量导入交易数据
                        </Typography>
                        <Button 
                          variant="outlined" 
                          startIcon={<AddIcon />} 
                          onClick={handleAddItem}
                          color="primary"
                          sx={{ borderRadius: '20px', textTransform: 'none' }}
                        >
                          添加第一条监控数据
                        </Button>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
      
      {/* 添加/编辑对话框 */}
      <Dialog 
        open={formOpen} 
        onClose={() => setFormOpen(false)} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: styles.borderRadius.large,
            boxShadow: styles.boxShadow.heavy
          }
        }}
      >
        <DialogTitle sx={{ 
          pb: 1, 
          pt: 2.5,
          borderBottom: '1px solid rgba(0,0,0,0.06)',
          display: 'flex',
          alignItems: 'center'
        }}>
          {currentItem ? (
            <>
              <EditIcon sx={{ mr: 1, color: 'primary.main' }} fontSize="small" />
              编辑监控记录
            </>
          ) : (
            <>
              <AddIcon sx={{ mr: 1, color: 'secondary.main' }} fontSize="small" />
              添加监控记录
            </>
          )}
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Grid container spacing={3} sx={{ mt: 0 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="物品名称"
                name="item_name"
                value={formData.item_name}
                onChange={handleFormChange}
                fullWidth
                required
                variant="outlined"
                InputProps={{
                  sx: { borderRadius: '8px' }
                }}
                helperText="请输入完整物品名称"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="数量"
                name="quantity"
                type="number"
                value={formData.quantity}
                onChange={handleFormChange}
                fullWidth
                required
                variant="outlined"
                InputProps={{
                  sx: { borderRadius: '8px' }
                }}
                helperText="当前库存数量"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="市场价格"
                name="market_price"
                type="number"
                value={formData.market_price}
                onChange={handleFormChange}
                fullWidth
                required
                variant="outlined"
                InputProps={{
                  sx: { borderRadius: '8px' },
                  startAdornment: <Box component="span" sx={{ mr: 0.5 }}>¥</Box>
                }}
                helperText="当前市场参考价格"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="目标买入价"
                name="target_price"
                type="number"
                value={formData.target_price}
                onChange={handleFormChange}
                fullWidth
                variant="outlined"
                InputProps={{
                  sx: { borderRadius: '8px' },
                  startAdornment: <Box component="span" sx={{ mr: 0.5 }}>¥</Box>
                }}
                helperText="期望的买入价格"
                color="primary"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="计划卖出价"
                name="planned_price"
                type="number"
                value={formData.planned_price}
                onChange={handleFormChange}
                fullWidth
                variant="outlined"
                InputProps={{
                  sx: { borderRadius: '8px' },
                  startAdornment: <Box component="span" sx={{ mr: 0.5 }}>¥</Box>
                }}
                helperText="计划卖出时的目标价格"
                color="success"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="出库策略"
                name="strategy"
                value={formData.strategy}
                onChange={handleFormChange}
                fullWidth
                multiline
                rows={2}
                variant="outlined"
                InputProps={{
                  sx: { borderRadius: '8px' }
                }}
                helperText="填写出库策略、备注等信息"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid rgba(0,0,0,0.06)' }}>
          <Button 
            onClick={() => setFormOpen(false)}
            variant="outlined"
            sx={{ 
              borderRadius: '8px',
              textTransform: 'none',
              minWidth: '80px'
            }}
          >
            取消
          </Button>
          <Button 
            onClick={handleSaveForm} 
            color="primary" 
            variant="contained"
            sx={{ 
              borderRadius: '8px',
              textTransform: 'none',
              minWidth: '80px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
          >
            保存
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 删除确认对话框 */}
      <Dialog 
        open={deleteDialogOpen} 
        onClose={() => setDeleteDialogOpen(false)}
        PaperProps={{
          sx: {
            borderRadius: styles.borderRadius.large,
            boxShadow: styles.boxShadow.heavy,
            maxWidth: '400px'
          }
        }}
      >
        <DialogTitle sx={{ 
          borderBottom: '1px solid rgba(0,0,0,0.06)',
          color: 'error.main',
          display: 'flex',
          alignItems: 'center',
          pb: 1.5
        }}>
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          确认删除
        </DialogTitle>
        <DialogContent sx={{ pt: 3, pb: 2, px: 3 }}>
          <Typography variant="body1" sx={{ mb: 1 }}>
            确定要删除以下监控记录吗？
          </Typography>
          <Box sx={{ 
            p: 2, 
            backgroundColor: 'error.lighter', 
            borderRadius: '8px',
            borderLeft: '3px solid',
            borderLeftColor: 'error.main',
            mb: 1
          }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
              {currentItem?.item_name}
            </Typography>
            {currentItem?.quantity > 0 && (
              <Typography variant="body2" color="text.secondary">
                当前库存：{currentItem?.quantity} 个
              </Typography>
            )}
          </Box>
          <Typography variant="body2" color="error.main" sx={{ fontWeight: 500, mt: 2 }}>
            此操作无法撤销。
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid rgba(0,0,0,0.06)' }}>
          <Button 
            onClick={() => setDeleteDialogOpen(false)}
            variant="outlined"
            sx={{ 
              borderRadius: '8px',
              textTransform: 'none'
            }}
          >
            取消
          </Button>
          <Button 
            onClick={handleConfirmDelete} 
            color="error" 
            variant="contained"
            startIcon={<DeleteIcon />}
            sx={{ 
              borderRadius: '8px',
              textTransform: 'none',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
          >
            确认删除
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* OCR导入对话框 */}
      <OCRDialog 
        open={ocrDialogOpen} 
        onClose={handleCloseOcrDialog}
        onImport={handleOcrImport}
        title="OCR监控导入"
        type="monitor"
      />
      
      {/* 通知提示 */}
      <Snackbar
        open={notification.open}
        autoHideDuration={3000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity} 
          variant="filled"
          sx={{ 
            borderRadius: '8px', 
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            width: '100%',
            alignItems: 'center'
          }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default TradeMonitor; 