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
  Grid,
  Menu,
  MenuItem,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControlLabel,
  Checkbox,
  Tooltip,
  Snackbar,
  Card,
  CardContent,
  Divider,
  useTheme,
  alpha,
  Fade
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  CloudDownload as ExportIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Inventory as InventoryIcon,
  TrendingUp as TrendingUpIcon,
  Money as MoneyIcon,
  AccountBalance as AccountBalanceIcon
} from '@mui/icons-material';
import axios from 'axios';

// 导入自定义组件
import InventoryMenu from '../components/inventory/InventoryMenu';
import InventoryEditDialog from '../components/inventory/InventoryEditDialog';

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
  
  // 右键菜单状态
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  
  // 编辑对话框状态
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);
  
  // 删除确认对话框状态
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  
  // 导出对话框状态
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('xlsx');
  
  // 筛选状态 - 设置showZeroStock默认为true
  const [showZeroStock, setShowZeroStock] = useState(true);
  const [showLowStock, setShowLowStock] = useState(false);
  const [showNegativeProfit, setShowNegativeProfit] = useState(false);
  
  // 通知状态
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // 获取主题
  const theme = useTheme();

  // 页面加载时获取库存数据
  useEffect(() => {
    fetchInventoryData();
  }, []);

  // 过滤数据
  useEffect(() => {
    if (inventoryData.length === 0) {
      setFilteredData([]);
      return;
    }
    
    let filtered = [...inventoryData];
    
    // 搜索过滤
    if (searchTerm.trim() !== '') {
      const lowercasedFilter = searchTerm.toLowerCase();
      filtered = filtered.filter(item => 
        item.itemName.toLowerCase().includes(lowercasedFilter)
      );
    }
    
    // 筛选条件
    if (!showZeroStock) {
      filtered = filtered.filter(item => item.quantity > 0);
    }
    
    if (showLowStock) {
      filtered = filtered.filter(item => item.quantity > 0 && item.quantity < 30);
    }
    
    if (showNegativeProfit) {
      filtered = filtered.filter(item => item.profit < 0);
    }
    
    setFilteredData(filtered);
    
    // 更新统计数据
    setTotalItems(filtered.length);
    setTotalValue(filtered.reduce((sum, item) => sum + item.inventoryValue, 0));
  }, [searchTerm, inventoryData, showZeroStock, showLowStock, showNegativeProfit]);

  // 获取库存数据
  const fetchInventoryData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/inventory');
      
      // 格式化响应数据
      const formattedData = response.data.map(item => ({
        id: item.id || Math.random().toString(36).substr(2, 9),
        itemName: item.item_name,
        quantity: Number(item.quantity) || 0,
        avgPrice: Number(item.avg_price) || 0,
        breakEvenPrice: Number(item.break_even_price) || 0,
        sellingPrice: Number(item.selling_price) || 0,
        profit: Number(item.profit) || 0,
        profitRate: Number(item.profit_rate) || 0,
        totalProfit: Number(item.total_profit) || 0,
        inventoryValue: Number(item.inventory_value) || 0
      }));
      
      setInventoryData(formattedData);
      
      // 计算统计数据
      setTotalItems(formattedData.length);
      setTotalValue(formattedData.reduce((sum, item) => sum + item.inventoryValue, 0));
      
      setError(null);
      
      // 显示成功通知
      showNotification('库存数据加载成功', 'success');
    } catch (err) {
      console.error('获取库存数据失败:', err);
      setError('无法加载库存数据。请检查网络连接或稍后再试。');
      
      // 显示错误通知
      showNotification('获取库存数据失败', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 重新计算库存
  const recalculateInventory = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/inventory/recalculate');
      
      if (response.data.success) {
        // 更新库存数据
        const formattedData = response.data.inventory.map(item => ({
          id: item.id || Math.random().toString(36).substr(2, 9),
          itemName: item.item_name,
          quantity: Number(item.quantity) || 0,
          avgPrice: Number(item.avg_price) || 0,
          breakEvenPrice: Number(item.break_even_price) || 0,
          sellingPrice: Number(item.selling_price) || 0,
          profit: Number(item.profit) || 0,
          profitRate: Number(item.profit_rate) || 0,
          totalProfit: Number(item.total_profit) || 0,
          inventoryValue: Number(item.inventory_value) || 0
        }));
        
        setInventoryData(formattedData);
        
        // 显示成功通知
        showNotification('库存数据已重新计算', 'success');
      } else {
        throw new Error(response.data.message || '重新计算库存失败');
      }
    } catch (err) {
      console.error('重新计算库存失败:', err);
      
      // 显示错误通知
      showNotification('重新计算库存失败', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 删除库存项目
  const deleteInventoryItem = async (id) => {
    try {
      const response = await axios.delete(`/api/inventory/${id}`);
      
      if (response.data.success) {
        // 从库存数据中移除该项目
        const updatedData = inventoryData.filter(item => item.id !== id);
        setInventoryData(updatedData);
        
        // 显示成功通知
        showNotification('物品已删除', 'success');
      } else {
        throw new Error(response.data.message || '删除物品失败');
      }
    } catch (err) {
      console.error('删除物品失败:', err);
      
      // 显示错误通知
      showNotification('删除物品失败', 'error');
    }
  };
  
  // 导出库存数据
  const exportInventory = async (format) => {
    try {
      const response = await axios.get(`/api/inventory/export?format=${format}`);
      
      if (response.data.success) {
        // 打开下载链接
        window.open(response.data.downloadUrl, '_blank');
        
        // 显示成功通知
        showNotification(`库存数据已导出为${format.toUpperCase()}格式`, 'success');
      } else {
        throw new Error(response.data.message || '导出库存数据失败');
      }
    } catch (err) {
      console.error('导出库存数据失败:', err);
      
      // 显示错误通知
      showNotification('导出库存数据失败', 'error');
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
  
  // 处理表格行右键点击
  const handleRowRightClick = (event, item) => {
    event.preventDefault();
    setContextMenu({
      top: event.clientY,
      left: event.clientX
    });
    setSelectedItem(item);
  };
  
  // 处理右键菜单关闭
  const handleContextMenuClose = () => {
    setContextMenu(null);
    setSelectedItem(null);
  };
  
  // 处理复制物品名称
  const handleCopyName = (item) => {
    navigator.clipboard.writeText(item.itemName)
      .then(() => {
        showNotification('物品名称已复制到剪贴板', 'success');
      })
      .catch(err => {
        console.error('复制失败:', err);
        showNotification('复制物品名称失败', 'error');
      });
  };
  
  // 处理删除物品
  const handleDelete = (item) => {
    setItemToDelete(item);
    setDeleteDialogOpen(true);
  };
  
  // 确认删除物品
  const confirmDelete = () => {
    if (itemToDelete) {
      deleteInventoryItem(itemToDelete.id);
      setDeleteDialogOpen(false);
      setItemToDelete(null);
    }
  };
  
  // 处理编辑物品
  const handleEdit = (item) => {
    setEditItem(item);
    setEditDialogOpen(true);
  };
  
  // 处理添加物品
  const handleAdd = () => {
    setEditItem(null);
    setEditDialogOpen(true);
  };
  
  // 处理保存物品
  const handleSaveItem = (formData) => {
    // TODO: 实现保存物品的API调用
    console.log('保存物品:', formData);
    setEditDialogOpen(false);
  };
  
  // 处理刷新物品数据
  const handleRefreshItem = (item) => {
    // TODO: 实现刷新单个物品的API调用
    console.log('刷新物品:', item);
  };
  
  // 处理导出
  const handleExport = () => {
    setExportDialogOpen(true);
  };
  
  // 确认导出
  const confirmExport = () => {
    exportInventory(exportFormat);
    setExportDialogOpen(false);
  };
  
  // 处理刷新
  const handleRefresh = () => {
    fetchInventoryData();
  };
  
  // 处理重新计算
  const handleRecalculate = () => {
    recalculateInventory();
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
    setNotification({
      ...notification,
      open: false
    });
  };
  
  // 获取行样式
  const getRowStyle = (row) => {
    // 移除高亮背景色，仅保留警告图标
    return {};
  };

  // 渲染统计卡片
  const renderStatCard = (title, value, icon, color) => (
    <Card 
      sx={{ 
        height: '100%',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
        borderRadius: 3,
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 6px 24px rgba(0, 0, 0, 0.1)',
        }
      }}
    >
      <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" color="text.secondary" fontWeight="medium">
            {title}
          </Typography>
          <Box sx={{ 
            backgroundColor: alpha(color, 0.12), 
            borderRadius: '50%', 
            p: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {icon}
          </Box>
        </Box>
        <Typography variant="h4" fontWeight="bold" color={color}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="xl" sx={{ mt: { xs: 2, sm: 4 }, mb: { xs: 4, sm: 6 } }}>
      {/* 页面标题和描述 */}
      <Box sx={{ mb: { xs: 3, sm: 5 }, display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2 }}>
        <InventoryIcon sx={{ fontSize: { xs: 30, sm: 36 }, color: 'primary.main', mr: { xs: 0, sm: 2 } }} />
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" color="primary.main">
            库存管理
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
            管理您的游戏物品库存，查看库存价值和利润数据
          </Typography>
        </Box>
      </Box>

      {/* 统计卡片 */}
      <Fade in={!loading} timeout={800}>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            {renderStatCard(
              "物品总数", 
              totalItems, 
              <InventoryIcon fontSize="medium" sx={{ color: theme.palette.primary.main }} />,
              theme.palette.primary.main
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderStatCard(
              "总库存量", 
              filteredData.reduce((sum, item) => sum + item.quantity, 0).toLocaleString(), 
              <TrendingUpIcon fontSize="medium" sx={{ color: theme.palette.success.main }} />,
              theme.palette.success.main
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderStatCard(
              "总利润额", 
              `¥${formatNumber(filteredData.reduce((sum, item) => sum + item.totalProfit, 0))}`, 
              <MoneyIcon fontSize="medium" sx={{ color: theme.palette.error.main }} />,
              theme.palette.error.main
            )}
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            {renderStatCard(
              "库存价值", 
              `¥${formatNumber(totalValue)}`, 
              <AccountBalanceIcon fontSize="medium" sx={{ color: theme.palette.warning.main }} />,
              theme.palette.warning.main
            )}
          </Grid>
        </Grid>
      </Fade>

      {/* 操作栏 */}
      <Paper 
        elevation={0} 
        sx={{ 
          p: { xs: 1.5, sm: 2 }, 
          mb: 3, 
          display: 'flex', 
          flexDirection: { xs: 'column', md: 'row' },
          justifyContent: 'space-between', 
          alignItems: { xs: 'stretch', md: 'center' },
          gap: 2,
          backgroundColor: alpha(theme.palette.primary.main, 0.03),
          border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
          borderRadius: 2
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'stretch', sm: 'center' }, 
          gap: 2,
          width: { xs: '100%', md: 'auto' }
        }}>
          <TextField
            placeholder="搜索物品..."
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={handleSearchChange}
            sx={{ 
              width: { xs: '100%', sm: 280 },
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                backgroundColor: 'white'
              }
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap',
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 1 
          }}>
            <FormControlLabel
              control={
                <Checkbox 
                  checked={showZeroStock} 
                  onChange={(e) => setShowZeroStock(e.target.checked)}
                  size="small"
                  color="primary"
                />
              }
              label="显示零库存"
              sx={{ mr: 1 }}
            />
            
            <FormControlLabel
              control={
                <Checkbox 
                  checked={showLowStock} 
                  onChange={(e) => setShowLowStock(e.target.checked)}
                  size="small"
                  color="warning"
                />
              }
              label="仅显示低库存"
              sx={{ mr: 1 }}
            />
            
            <FormControlLabel
              control={
                <Checkbox 
                  checked={showNegativeProfit} 
                  onChange={(e) => setShowNegativeProfit(e.target.checked)}
                  size="small"
                  color="error"
                />
              }
              label="仅显示负利润"
            />
          </Box>
        </Box>
        
        <Box sx={{ 
          display: 'flex', 
          gap: 1, 
          flexWrap: 'wrap',
          justifyContent: { xs: 'flex-start', md: 'flex-end' }
        }}>
          <Button 
            variant="outlined" 
            startIcon={<ExportIcon />}
            onClick={handleExport}
            sx={{ borderRadius: 2 }}
          >
            导出
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            sx={{ borderRadius: 2 }}
          >
            刷新
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />}
            onClick={handleRecalculate}
            sx={{ borderRadius: 2 }}
          >
            重新计算
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            color="primary"
            onClick={handleAdd}
            sx={{ 
              borderRadius: 2,
              boxShadow: '0 4px 12px rgba(25, 118, 210, 0.2)',
              '&:hover': {
                boxShadow: '0 6px 16px rgba(25, 118, 210, 0.3)',
              }
            }}
          >
            添加物品
          </Button>
        </Box>
      </Paper>

      {/* 库存表格 */}
      <Paper 
        sx={{ 
          width: '100%', 
          overflow: 'hidden', 
          borderRadius: 3, 
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
          transition: 'box-shadow 0.3s',
          '&:hover': {
            boxShadow: '0 6px 24px rgba(0, 0, 0, 0.12)',
          }
        }}
      >
        {error ? (
          <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
        ) : loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <TableContainer sx={{ maxHeight: { xs: 'calc(100vh - 450px)', md: 'calc(100vh - 380px)' }, overflowX: 'auto' }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow sx={{ 
                    '& th': { 
                      fontWeight: 'bold',
                      backgroundColor: alpha(theme.palette.primary.main, 0.04)
                    } 
                  }}>
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
                      <TableRow 
                        key={row.id} 
                        hover
                        onContextMenu={(e) => handleRowRightClick(e, row)}
                        sx={{
                          transition: 'background-color 0.2s',
                          cursor: 'default'
                        }}
                      >
                        <TableCell component="th" scope="row" sx={{ fontWeight: 500 }}>
                          {row.quantity <= 0 && (
                            <Tooltip title="零库存或负库存">
                              <WarningIcon 
                                fontSize="small" 
                                color="error" 
                                sx={{ verticalAlign: 'middle', mr: 0.5 }}
                              />
                            </Tooltip>
                          )}
                          {row.quantity > 0 && row.quantity < 30 && (
                            <Tooltip title="低库存">
                              <WarningIcon 
                                fontSize="small" 
                                color="warning" 
                                sx={{ verticalAlign: 'middle', mr: 0.5 }}
                              />
                            </Tooltip>
                          )}
                          {row.itemName}
                        </TableCell>
                        <TableCell align="right">{row.quantity.toLocaleString()}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.avgPrice)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.breakEvenPrice)}</TableCell>
                        <TableCell align="right">¥{formatNumber(row.sellingPrice)}</TableCell>
                        <TableCell 
                          align="right"
                          sx={{ 
                            color: row.profit >= 0 ? theme.palette.success.main : theme.palette.error.main,
                            fontWeight: 500
                          }}
                        >
                          ¥{formatNumber(row.profit)}
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`${(typeof row.profitRate === 'number' ? row.profitRate.toFixed(2) : '0.00')}%`}
                            size="small"
                            color={row.profitRate > 0 ? "success" : row.profitRate < 0 ? "error" : "default"}
                            sx={{ 
                              fontWeight: 'bold',
                              boxShadow: '0 2px 5px rgba(0,0,0,0.08)'
                            }}
                          />
                        </TableCell>
                        <TableCell 
                          align="right"
                          sx={{ 
                            color: row.totalProfit >= 0 ? theme.palette.success.main : theme.palette.error.main,
                            fontWeight: 500
                          }}
                        >
                          ¥{formatNumber(row.totalProfit)}
                        </TableCell>
                        <TableCell 
                          align="right"
                          sx={{ fontWeight: 'bold' }}
                        >
                          ¥{formatNumber(row.inventoryValue)}
                        </TableCell>
                      </TableRow>
                    ))}
                  {filteredData.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9} align="center" sx={{ py: 5 }}>
                        <Box sx={{ 
                          display: 'flex', 
                          flexDirection: 'column', 
                          alignItems: 'center', 
                          gap: 2,
                          p: 3
                        }}>
                          <InventoryIcon sx={{ fontSize: 48, color: alpha(theme.palette.text.secondary, 0.5) }} />
                          <Typography variant="h6" color="text.secondary">
                            {searchTerm ? "没有找到匹配的物品" : "暂无库存数据"}
                          </Typography>
                          {searchTerm && (
                            <Button 
                              variant="outlined" 
                              size="small" 
                              onClick={() => setSearchTerm('')}
                              sx={{ mt: 1 }}
                            >
                              清除搜索
                            </Button>
                          )}
                        </Box>
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
                borderTop: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                  marginBottom: 0,
                }
              }}
            />
          </>
        )}
      </Paper>
      
      {/* 右键菜单 */}
      <InventoryMenu
        anchorPosition={contextMenu}
        open={Boolean(contextMenu)}
        onClose={handleContextMenuClose}
        selectedItem={selectedItem}
        onCopyName={handleCopyName}
        onDelete={handleDelete}
        onEdit={handleEdit}
        onRefreshItem={handleRefreshItem}
      />
      
      {/* 编辑对话框 */}
      <InventoryEditDialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        item={editItem}
        onSave={handleSaveItem}
      />
      
      {/* 删除确认对话框 */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        PaperProps={{ 
          sx: { 
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
            width: { xs: '90%', sm: 'auto' },
            maxWidth: { xs: '90%', sm: '450px' }
          } 
        }}
      >
        <DialogTitle sx={{ pb: 1 }}>确认删除</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除物品 "{itemToDelete?.itemName}" 吗？此操作不可撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button 
            onClick={() => setDeleteDialogOpen(false)}
            sx={{ borderRadius: 2 }}
          >
            取消
          </Button>
          <Button 
            onClick={confirmDelete} 
            color="error"
            variant="contained"
            sx={{ 
              borderRadius: 2,
              boxShadow: '0 4px 12px rgba(211, 47, 47, 0.2)',
              '&:hover': {
                boxShadow: '0 6px 16px rgba(211, 47, 47, 0.3)',
              }
            }}
          >
            删除
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 导出对话框 */}
      <Dialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        PaperProps={{ 
          sx: { 
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
            width: { xs: '90%', sm: 'auto' },
            maxWidth: { xs: '90%', sm: '450px' }
          } 
        }}
      >
        <DialogTitle sx={{ pb: 1 }}>导出库存数据</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 3 }}>
            请选择导出格式：
          </DialogContentText>
          <Box sx={{ 
            display: 'flex', 
            flexDirection: { xs: 'column', sm: 'row' },
            justifyContent: 'center', 
            gap: 2 
          }}>
            <Button 
              variant={exportFormat === 'xlsx' ? 'contained' : 'outlined'}
              onClick={() => setExportFormat('xlsx')}
              sx={{ 
                minWidth: { xs: '100%', sm: 120 },
                borderRadius: 2,
                boxShadow: exportFormat === 'xlsx' ? '0 4px 12px rgba(25, 118, 210, 0.2)' : 'none'
              }}
            >
              Excel (.xlsx)
            </Button>
            <Button 
              variant={exportFormat === 'csv' ? 'contained' : 'outlined'}
              onClick={() => setExportFormat('csv')}
              sx={{ 
                minWidth: { xs: '100%', sm: 120 },
                borderRadius: 2,
                boxShadow: exportFormat === 'csv' ? '0 4px 12px rgba(25, 118, 210, 0.2)' : 'none'
              }}
            >
              CSV (.csv)
            </Button>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button 
            onClick={() => setExportDialogOpen(false)}
            sx={{ borderRadius: 2 }}
          >
            取消
          </Button>
          <Button 
            onClick={confirmExport} 
            color="primary"
            variant="contained"
            sx={{ 
              borderRadius: 2,
              boxShadow: '0 4px 12px rgba(25, 118, 210, 0.2)',
              '&:hover': {
                boxShadow: '0 6px 16px rgba(25, 118, 210, 0.3)',
              }
            }}
          >
            导出
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 通知 */}
      <Snackbar
        open={notification.open}
        autoHideDuration={5000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        sx={{
          maxWidth: { xs: '90%', sm: '400px' },
          right: { xs: '5%', sm: 24 },
          bottom: { xs: '5%', sm: 24 }
        }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity} 
          sx={{ 
            width: '100%',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
            borderRadius: 2
          }}
          variant="filled"
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Inventory; 