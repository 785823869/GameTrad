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
import axios from 'axios';
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
  const [totalProfit, setTotalProfit] = useState(0);
  
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
      const response = await axios.get('/api/stock-out');
      
      // 格式化响应数据
      const formattedData = response.data.map(item => ({
        id: item.id || Math.random().toString(36).substr(2, 9),
        itemName: item.item_name,
        transactionTime: new Date(item.transaction_time),
        quantity: item.quantity,
        unitPrice: item.unit_price,
        fee: item.fee,
        totalAmount: item.total_amount,
        profit: item.profit,
        profitRate: item.profit_rate,
        note: item.note || ''
      }));
      
      setStockOutData(formattedData);
      setError(null);
    } catch (err) {
      console.error('获取出库数据失败:', err);
      setError('无法加载出库数据。请检查网络连接或稍后再试。');
    } finally {
      setLoading(false);
    }
  };
  
  // 计算统计数据
  const calculateStats = () => {
    const income = filteredData.reduce((sum, item) => sum + item.totalAmount, 0);
    const quantity = filteredData.reduce((sum, item) => sum + item.quantity, 0);
    const profit = filteredData.reduce((sum, item) => sum + (item.profit || 0), 0);
    
    setTotalIncome(income);
    setTotalQuantity(quantity);
    setTotalProfit(profit);
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
      await axios.delete(`/api/stock-out/${selectedItem.id}`);
      setStockOutData(prevData => prevData.filter(item => item.id !== selectedItem.id));
      handleCloseDeleteDialog();
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
        <Grid item xs={12} md={4}>
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
        <Grid item xs={12} md={4}>
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
        <Grid item xs={12} md={4}>
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
              总利润
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="error.main">
              ¥{formatNumber(totalProfit)}
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
      <Paper sx={{ width: '100%', overflow: 'hidden', borderRadius: 2, boxShadow: '0 4px 14px rgba(0, 0, 0, 0.1)' }}>
        {error ? (
          <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
        ) : loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <TableContainer sx={{ maxHeight: 'calc(100vh - 380px)' }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>物品名称</TableCell>
                    <TableCell>出库时间</TableCell>
                    <TableCell align="right">数量</TableCell>
                    <TableCell align="right">单价</TableCell>
                    <TableCell align="right">手续费</TableCell>
                    <TableCell align="right">总金额</TableCell>
                    <TableCell align="right">利润</TableCell>
                    <TableCell align="right">利润率</TableCell>
                    <TableCell>备注</TableCell>
                    <TableCell align="right">操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredData
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((row) => (
                      <TableRow key={row.id} hover>
                        <TableCell component="th" scope="row">
                          {row.itemName}
                        </TableCell>
                        <TableCell>{formatDate(row.transactionTime)}</TableCell>
                        <TableCell align="right">{row.quantity.toLocaleString()}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.unitPrice)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.fee)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.totalAmount)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.profit || 0)}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`${(row.profitRate || 0).toFixed(2)}%`}
                            size="small"
                            color={(row.profitRate || 0) > 0 ? "success" : (row.profitRate || 0) < 0 ? "error" : "default"}
                          />
                        </TableCell>
                        <TableCell>{row.note}</TableCell>
                        <TableCell align="right">
                          <Tooltip title="编辑">
                            <IconButton size="small" color="primary">
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="删除">
                            <IconButton 
                              size="small" 
                              color="error"
                              onClick={() => handleOpenDeleteDialog(row)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  {filteredData.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={10} align="center" sx={{ py: 3 }}>
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