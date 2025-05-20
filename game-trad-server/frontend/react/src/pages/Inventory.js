import React, { useState, useEffect } from 'react';
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
  TablePagination,
  TextField,
  InputAdornment,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Grid
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  CloudDownload as ExportIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import axios from 'axios';

const Inventory = () => {
  // 状态管理
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [inventoryData, setInventoryData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);
  const [totalValue, setTotalValue] = useState(0);

  // 页面加载时获取库存数据
  useEffect(() => {
    fetchInventoryData();
  }, []);

  // 过滤数据
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredData(inventoryData);
    } else {
      const lowercasedFilter = searchTerm.toLowerCase();
      const filtered = inventoryData.filter(item => 
        item.itemName.toLowerCase().includes(lowercasedFilter)
      );
      setFilteredData(filtered);
    }
  }, [searchTerm, inventoryData]);

  // 获取库存数据
  const fetchInventoryData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/inventory');
      
      // 格式化响应数据
      const formattedData = response.data.map(item => ({
        id: item.id || Math.random().toString(36).substr(2, 9),
        itemName: item.item_name,
        quantity: item.quantity,
        avgPrice: item.avg_price,
        breakEvenPrice: item.break_even_price,
        sellingPrice: item.selling_price,
        profit: item.profit,
        profitRate: item.profit_rate,
        totalProfit: item.total_profit,
        inventoryValue: item.inventory_value
      }));
      
      setInventoryData(formattedData);
      
      // 计算统计数据
      setTotalItems(formattedData.length);
      setTotalValue(formattedData.reduce((sum, item) => sum + item.inventoryValue, 0));
      
      setError(null);
    } catch (err) {
      console.error('获取库存数据失败:', err);
      setError('无法加载库存数据。请检查网络连接或稍后再试。');
    } finally {
      setLoading(false);
    }
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

  // 数字格式化
  const formatNumber = (num) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };

  // 导出库存数据
  const handleExport = () => {
    // 此处实现导出功能
    alert('导出功能将在后续实现');
  };

  // 处理刷新
  const handleRefresh = () => {
    fetchInventoryData();
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 3, mb: 4 }}>
      {/* 页面标题和描述 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary.main">
          库存管理
        </Typography>
        <Typography variant="body1" color="text.secondary">
          管理您的游戏物品库存，查看库存价值和利润数据
        </Typography>
      </Box>

      {/* 统计卡片 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
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
              物品总数
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="primary.main">
              {totalItems}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
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
              总库存量
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="success.main">
              {filteredData.reduce((sum, item) => sum + item.quantity, 0).toLocaleString()}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
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
              总利润额
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="error.main">
              ¥{formatNumber(filteredData.reduce((sum, item) => sum + item.totalProfit, 0))}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
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
              库存价值
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="warning.main">
              ¥{formatNumber(totalValue)}
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
            startIcon={<FilterIcon />}
            sx={{ mr: 1 }}
          >
            筛选
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<ExportIcon />}
            onClick={handleExport}
            sx={{ mr: 1 }}
          >
            导出
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            sx={{ mr: 1 }}
          >
            刷新
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            color="primary"
          >
            添加物品
          </Button>
        </Box>
      </Box>

      {/* 库存表格 */}
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
                    <TableCell align="right">库存数量</TableCell>
                    <TableCell align="right">入库均价</TableCell>
                    <TableCell align="right">保本均价</TableCell>
                    <TableCell align="right">出库均价</TableCell>
                    <TableCell align="right">利润</TableCell>
                    <TableCell align="right">利润率</TableCell>
                    <TableCell align="right">成交利润</TableCell>
                    <TableCell align="right">库存价值</TableCell>
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
                        <TableCell align="right">{row.quantity.toLocaleString()}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.avgPrice)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.breakEvenPrice)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.sellingPrice)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.profit)}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`${row.profitRate.toFixed(2)}%`}
                            size="small"
                            color={row.profitRate > 0 ? "success" : row.profitRate < 0 ? "error" : "default"}
                          />
                        </TableCell>
                        <TableCell align="right">¥{formatNumber(row.totalProfit)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.inventoryValue)}</TableCell>
                      </TableRow>
                    ))}
                  {filteredData.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9} align="center" sx={{ py: 3 }}>
                        {searchTerm ? "没有找到匹配的物品" : "暂无库存数据"}
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
    </Container>
  );
};

export default Inventory; 