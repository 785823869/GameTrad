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
      const response = await axios.get('/api/transactions');
      
      if (response.data) {
        setTradeItems(response.data);
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
    return `¥ ${parseFloat(price).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };
  
  // 格式化百分比
  const formatPercent = (value) => {
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
      // 转换表单数据为交易记录格式
      const transactionData = {
        transaction_type: 'monitor', // 特定的类型标识这是监控记录
        item_name: formData.item_name,
        quantity: parseInt(formData.quantity) || 0,
        price: parseFloat(formData.market_price) || 0,
        target_price: parseFloat(formData.target_price) || 0,
        planned_price: parseFloat(formData.planned_price) || 0,
        note: formData.strategy || '',
        platform: '', // 可选平台信息
        transaction_time: new Date().toISOString()
      };
      
      let response;
      if (currentItem && currentItem.id) {
        // 更新现有记录
        response = await axios.put(`/api/transactions/${currentItem.id}`, transactionData);
      } else {
        // 添加新记录
        response = await axios.post('/api/transactions', transactionData);
      }
      
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
      
      // 导入到后端
      axios.post('/api/transactions/import', monitorItems)
        .then(response => {
          console.log("导入响应:", response.data);
          
          if (response.data.success) {
            // 添加到现有数据
            setTradeItems(prev => {
              // 检查响应中有处理结果
              const newItems = response.data.results?.processed_records || monitorItems;
              
              // 将服务器处理的结果格式化为前端所需的格式
              const formattedItems = newItems.map(item => ({
                id: item.id,
                item_name: item.item_name,
                quantity: Number(item.quantity) || 0,
                market_price: Number(item.unit_price || item.price || item.market_price || 0),
                target_price: 0,
                planned_price: 0,
                monitor_time: new Date(),
                break_even_price: 0,
                profit: 0,
                profit_rate: 0,
                strategy: item.note || '',
              }));
              
              return [...formattedItems, ...prev];
            });
            
            setNotification({
              open: true,
              message: `成功导入${response.data.results?.success || monitorItems.length}条记录`,
              severity: 'success'
            });
            
            // 刷新数据
            fetchTradeItems();
          } else {
            setNotification({
              open: true,
              message: response.data.message || '导入失败，服务器返回错误',
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
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center' }}>
          <TrendingUpIcon sx={{ mr: 1 }} />
          交易监控
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<ImportIcon />}
            onClick={handleOpenOcrDialog}
            sx={{ mr: 1 }}
          >
            OCR导入
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleAddItem}
            sx={{ mr: 1 }}
          >
            添加监控
          </Button>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={fetchTradeItems}
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
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
          <TextField
            label="搜索物品"
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={handleSearch}
            sx={{ minWidth: 200 }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
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
          <FormControl size="small" sx={{ minWidth: 120 }}>
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
        </Box>
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer sx={{ 
            maxHeight: 'calc(100vh - 380px)', 
            overflow: 'auto',
            "&::-webkit-scrollbar": {
              width: "10px",
              height: "10px"
            },
            "&::-webkit-scrollbar-track": {
              backgroundColor: "rgba(0,0,0,0.05)"
            },
            "&::-webkit-scrollbar-thumb": {
              backgroundColor: "rgba(0,0,0,0.15)",
              borderRadius: "4px",
              "&:hover": {
                backgroundColor: "rgba(0,0,0,0.3)"
              }
            }
          }}>
            <Table stickyHeader sx={{ minWidth: 650 }}>
              <TableHead>
                <TableRow>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold', 
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '15%'
                    }}
                  >
                    物品名称
                  </TableCell>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '12%'
                    }}
                  >
                    监控时间
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '8%'
                    }}
                  >
                    库存数量
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '10%'
                    }}
                  >
                    市场价格
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '10%'
                    }}
                  >
                    目标买入价
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '10%'
                    }}
                  >
                    计划卖出价
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '10%'
                    }}
                  >
                    成本价格
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '10%'
                    }}
                  >
                    单位利润
                  </TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '10%'
                    }}
                  >
                    利润率
                  </TableCell>
                  <TableCell 
                    align="center"
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
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
                      backgroundColor: 'background.default',
                      borderBottom: '2px solid',
                      borderBottomColor: 'primary.light',
                      position: 'sticky',
                      top: 0,
                      zIndex: 10,
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      width: '10%'
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
                          backgroundColor: "rgba(0, 0, 0, 0.04)"
                        }
                      }}
                    >
                      <TableCell component="th" scope="row" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        <Tooltip title={item.item_name} placement="top">
                          <span>{item.item_name}</span>
                        </Tooltip>
                      </TableCell>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatDateTime(item.monitor_time)}</TableCell>
                      <TableCell align="right">{item.quantity}</TableCell>
                      <TableCell align="right">{formatPrice(item.market_price)}</TableCell>
                      <TableCell align="right" sx={{ color: 'text.primary', fontWeight: 500 }}>
                        {formatPrice(item.target_price || 0)}
                      </TableCell>
                      <TableCell align="right" sx={{ color: 'success.main', fontWeight: 500 }}>
                        {formatPrice(item.planned_price || 0)}
                      </TableCell>
                      <TableCell align="right">{formatPrice(item.break_even_price)}</TableCell>
                      <TableCell align="right" sx={{ 
                        color: (item.profit || 0) >= 0 ? 'success.main' : 'error.main', 
                        fontWeight: 500 
                      }}>
                        {formatPrice(item.profit)}
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={formatPercent(item.profit_rate)}
                          size="small"
                          color={(item.profit_rate || 0) > 0 ? "success" : (item.profit_rate || 0) < 0 ? "error" : "default"}
                          sx={{
                            fontWeight: 'bold',
                            minWidth: '70px'
                          }}
                        />
                      </TableCell>
                      <TableCell align="center">{item.strategy || '—'}</TableCell>
                      <TableCell align="center">
                        <IconButton color="primary" size="small" onClick={() => handleEditItem(item)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton color="error" size="small" onClick={() => handleDeleteItem(item)}>
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={10} align="center">暂无数据</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
      
      {/* 添加/编辑对话框 */}
      <Dialog open={formOpen} onClose={() => setFormOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{currentItem ? '编辑监控记录' : '添加监控记录'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="物品名称"
                name="item_name"
                value={formData.item_name}
                onChange={handleFormChange}
                fullWidth
                required
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
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormOpen(false)}>取消</Button>
          <Button onClick={handleSaveForm} color="primary" variant="contained">
            保存
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          确定要删除 {currentItem?.item_name} 的监控记录吗？此操作无法撤销。
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>取消</Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            删除
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
        message={notification.message}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      />
    </Container>
  );
};

export default TradeMonitor; 