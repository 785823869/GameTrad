import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  CloudUpload as ImportIcon,
  Delete as DeleteIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import StockOutService from '../services/StockOutService';  // 引入服务
import { Link } from 'react-router-dom';

const StockOut = () => {
  // 状态
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stockOutData, setStockOutData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [totalIncome, setTotalIncome] = useState(0);
  const [totalQuantity, setTotalQuantity] = useState(0);
  
  // 获取出库数据
  useEffect(() => {
    fetchStockOutData();
  }, []);
  
  // 筛选数据
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredData(stockOutData);
    } else {
      const lowercasedFilter = searchTerm.toLowerCase();
      const filtered = stockOutData.filter(item => 
        item.itemName.toLowerCase().includes(lowercasedFilter)
      );
      setFilteredData(filtered);
    }
    
    // 计算统计数据
    calculateStats();
  }, [searchTerm, stockOutData]);
  
  // 获取出库数据
  const fetchStockOutData = async () => {
    setLoading(true);
    try {
      console.log('正在请求出库数据...');
      const data = await StockOutService.getAll();
      console.log('出库API响应:', data);
      
      if (!data) {
        console.error('API响应中没有data字段');
        setStockOutData([]);
        setError('无法加载出库数据：服务器返回空数据。');
        return;
      }
      
      // 检查响应数据是否为数组
      if (!Array.isArray(data)) {
        console.error('API返回的数据不是数组格式:', data);
        setStockOutData([]);
        setError('无法加载出库数据：数据格式不正确。');
        return;
      }
      
      // 格式化响应数据，增强数据处理和验证
      const formattedData = data.map((item, index) => {
        // 记录处理的数据
        console.log(`处理出库记录 ${index}:`, item);
        
        // 检查是否是有效对象
        if (!item) {
          console.error(`第${index}项数据无效`);
          return null;
        }
        
        // 安全地处理ID
        const id = item.id || Math.random().toString(36).substr(2, 9);
        
        // 确保物品名称不为空
        let itemName;
        // 处理数组或对象格式的数据
        if (Array.isArray(item)) {
          itemName = item[1] || '';
        } else {
          itemName = item.item_name || item.itemName || '';
        }
        // 如果物品名称为空，使用占位符
        if (!itemName) {
          itemName = `物品_${Math.random().toString(36).substr(2, 5)}`;
        }
        
        // 安全地处理日期
        let transactionTime;
        try {
          const rawDate = Array.isArray(item) ? item[2] : item.transaction_time;
          if (rawDate instanceof Date) {
            transactionTime = rawDate;
          } else if (typeof rawDate === 'string') {
            transactionTime = new Date(rawDate);
            if (isNaN(transactionTime.getTime())) {
              console.warn(`无效日期格式: ${rawDate}`);
              transactionTime = new Date();
            }
          } else {
            transactionTime = new Date();
          }
        } catch (err) {
          console.error(`日期解析错误: ${err.message}`);
          transactionTime = new Date();
        }
        
        // 安全地获取数值字段
        let quantity, unitPrice, fee, totalAmount;
        
        // 处理数量
        try {
          quantity = Array.isArray(item) ? 
            Number(item[3] || 0) : 
            Number(item.quantity || 0);
          if (isNaN(quantity)) quantity = 0;
        } catch (e) {
          console.error(`数量解析错误:`, e);
          quantity = 0;
        }
        
        // 处理单价
        try {
          unitPrice = Array.isArray(item) ? 
            Number(item[4] || 0) : 
            Number(item.unit_price || 0);
          if (isNaN(unitPrice)) unitPrice = 0;
        } catch (e) {
          console.error(`单价解析错误:`, e);
          unitPrice = 0;
        }
        
        // 处理手续费
        try {
          fee = Array.isArray(item) ? 
            Number(item[5] || 0) : 
            Number(item.fee || 0);
          if (isNaN(fee)) fee = 0;
        } catch (e) {
          console.error(`手续费解析错误:`, e);
          fee = 0;
        }
        
        // 处理总金额 - 总金额 = 数量 * 单价 - 手续费
        try {
          totalAmount = Array.isArray(item) ? 
            Number(item[6] || 0) : 
            Number(item.total_amount || 0);
          if (isNaN(totalAmount)) {
            // 如果总金额无效但有其他数据，计算总金额
            totalAmount = quantity * unitPrice - fee;
          }
        } catch (e) {
          console.error(`总金额解析错误:`, e);
          totalAmount = 0;
        }
        
        // 处理备注
        const note = Array.isArray(item) ? 
          (item[9] || '') : 
          (item.note || '');
        
        return {
          id,
          itemName,
          transactionTime,
          quantity,
          unitPrice,
          fee,
          totalAmount,
          note
        };
      }).filter(item => item !== null);  // 过滤掉无效数据
      
      console.log('格式化后的出库数据:', formattedData);
      setStockOutData(formattedData);
      setError(null);
    } catch (err) {
      console.error('获取出库数据失败:', err);
      
      // 详细的错误日志
      if (err.response) {
        console.error('服务器响应:', err.response.status, err.response.data);
      } else if (err.request) {
        console.error('请求已发送但未收到响应:', err.request);
      } else {
        console.error('请求配置错误:', err.message);
      }
      
      setStockOutData([]);
      setError('无法加载出库数据。请检查网络连接或稍后再试。');
    } finally {
      setLoading(false);
    }
  };
  
  // 计算统计数据
  const calculateStats = () => {
    if (!filteredData || filteredData.length === 0) {
      setTotalIncome(0);
      setTotalQuantity(0);
      return;
    }
    
    const income = filteredData.reduce((sum, item) => sum + (Number(item.totalAmount) || 0), 0);
    const quantity = filteredData.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0);
    
    setTotalIncome(income);
    setTotalQuantity(quantity);
  };
  
  // 处理搜索
  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };
  
  // 处理分页
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  // 处理每页行数变化
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // 打开删除对话框
  const handleOpenDeleteDialog = (item) => {
    setSelectedItem(item);
    setDeleteDialogOpen(true);
  };
  
  // 关闭删除对话框
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setSelectedItem(null);
  };
  
  // 确认删除
  const handleConfirmDelete = async () => {
    if (!selectedItem) return;
    
    try {
      const response = await StockOutService.delete(selectedItem.id);
      if (response.success) {
        setStockOutData(prevData => prevData.filter(item => item.id !== selectedItem.id));
        handleCloseDeleteDialog();
      } else {
        setError('删除出库记录失败。请稍后再试。');
      }
    } catch (err) {
      console.error('删除出库记录失败:', err);
      setError('删除出库记录失败。请稍后再试。');
    }
  };
  
  // 数字格式化
  const formatNumber = (num) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };
  
  // 日期格式化
  const formatDate = (date) => {
    return new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(date);
  };
  
  // 处理刷新
  const handleRefresh = () => {
    fetchStockOutData();
  };
  
  // OCR导入处理
  const handleOcrImport = () => {
    // OCR导入功能将在后端完成
    alert('OCR导入功能将在后续实现');
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 3, mb: 4 }}>
      {/* 页面标题和描述 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary.main">
          出库管理
        </Typography>
        <Typography variant="body1" color="text.secondary">
          管理物品出库记录，记录销售收入和利润
        </Typography>
      </Box>
      
      {/* 统计卡片 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper 
            sx={{ 
              p: 3, 
              textAlign: 'center',
              height: '100%',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.1)',
              borderRadius: 2
            }}
          >
            <Typography variant="subtitle1" color="text.secondary" gutterBottom>
              总销售额
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="primary.main">
              ¥{formatNumber(totalIncome)}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper 
            sx={{ 
              p: 3, 
              textAlign: 'center',
              height: '100%',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.1)',
              borderRadius: 2
            }}
          >
            <Typography variant="subtitle1" color="text.secondary" gutterBottom>
              总出库数量
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="success.main">
              {totalQuantity.toLocaleString()}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      
      {/* 操作栏 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <TextField
          placeholder="搜索物品..."
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={handleSearchChange}
          sx={{ width: 280 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            sx={{ mr: 1 }}
          >
            刷新
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<ImportIcon />}
            onClick={handleOcrImport}
            sx={{ mr: 1 }}
          >
            OCR导入
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            component={Link}
            to={{
              pathname: "/new-trade",
              state: { tradeType: 'out' }
            }}
            color="primary"
          >
            添加出库
          </Button>
        </Box>
      </Box>
      
      {/* 出库表格 */}
      <Paper sx={{ 
        width: '100%', 
        overflow: 'hidden', 
        borderRadius: 2, 
        boxShadow: '0 4px 14px rgba(0, 0, 0, 0.1)',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {error ? (
          <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
        ) : loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
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
              <Table stickyHeader aria-label="出库记录表格">
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
                      出库时间
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
                      数量
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
                      单价
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
                      手续费
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
                      总金额
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
                        width: '10%'
                      }}
                    >
                      备注
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
                      操作
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredData
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((row, index) => (
                      <TableRow 
                        key={row.id} 
                        hover
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
                          <Tooltip title={row.itemName} placement="top">
                            <span>{row.itemName}</span>
                          </Tooltip>
                        </TableCell>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatDate(row.transactionTime)}</TableCell>
                        <TableCell align="right">{row.quantity.toLocaleString()}</TableCell>
                        <TableCell align="right" sx={{ color: 'text.primary', fontWeight: 500 }}>¥{formatNumber(row.unitPrice)}</TableCell>
                        <TableCell align="right" sx={{ color: 'warning.main', fontWeight: 500 }}>¥{formatNumber(row.fee)}</TableCell>
                        <TableCell align="right" sx={{ color: 'success.main', fontWeight: 500 }}>¥{formatNumber(row.totalAmount)}</TableCell>
                        <TableCell sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {row.note && (
                            <Tooltip title={row.note} placement="top">
                              <span>{row.note}</span>
                            </Tooltip>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title="编辑">
                            <IconButton 
                              size="small" 
                              color="primary"
                              sx={{
                                backgroundColor: 'rgba(25, 118, 210, 0.08)',
                                '&:hover': {
                                  backgroundColor: 'rgba(25, 118, 210, 0.16)',
                                }
                              }}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="删除">
                            <IconButton 
                              size="small" 
                              color="error"
                              onClick={() => handleOpenDeleteDialog(row)}
                              sx={{
                                ml: 1,
                                backgroundColor: 'rgba(211, 47, 47, 0.08)',
                                '&:hover': {
                                  backgroundColor: 'rgba(211, 47, 47, 0.16)',
                                }
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  {filteredData.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9} align="center" sx={{ py: 3 }}>
                        {searchTerm ? "没有找到匹配的出库记录" : "暂无出库数据"}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={filteredData.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              labelRowsPerPage="每页行数:"
              labelDisplayedRows={({ from, to, count }) => `${from}-${to} / 共${count}项`}
              sx={{
                borderTop: '1px solid rgba(224, 224, 224, 1)',
                backgroundColor: '#FAFAFA'
              }}
            />
          </>
        )}
      </Paper>
      
      {/* 删除确认对话框 */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCloseDeleteDialog}
      >
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除 {selectedItem?.itemName} 的出库记录吗？此操作无法撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog} color="primary">
            取消
          </Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            删除
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default StockOut; 