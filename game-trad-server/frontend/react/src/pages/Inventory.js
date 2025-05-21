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
  Snackbar
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  CloudDownload as ExportIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon
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
  
  // 筛选状态
  const [showZeroStock, setShowZeroStock] = useState(false);
  const [showLowStock, setShowLowStock] = useState(false);
  const [showNegativeProfit, setShowNegativeProfit] = useState(false);
  
  // 通知状态
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

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
    if (row.quantity <= 0) {
      return { bgcolor: 'error.lighter' }; // 零库存或负库存
    } else if (row.quantity < 30) {
      return { bgcolor: 'warning.lighter' }; // 低库存
    } else if (row.profit < 0) {
      return { bgcolor: 'error.lighter', opacity: 0.7 }; // 负利润
    }
    return {};
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
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            placeholder="搜索物品..."
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={handleSearchChange}
            sx={{ width: 280, mr: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          
          <FormControlLabel
            control={
              <Checkbox 
                checked={showZeroStock} 
                onChange={(e) => setShowZeroStock(e.target.checked)}
                size="small"
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
              />
            }
            label="仅显示负利润"
          />
        </Box>
        
        <Box>
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
            variant="outlined" 
            startIcon={<RefreshIcon />}
            onClick={handleRecalculate}
            sx={{ mr: 1 }}
          >
            重新计算
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            color="primary"
            onClick={handleAdd}
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
                      <TableRow 
                        key={row.id} 
                        hover
                        onContextMenu={(e) => handleRowRightClick(e, row)}
                        sx={getRowStyle(row)}
                      >
                        <TableCell component="th" scope="row">
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
                        <TableCell align="right">¥{formatNumber(row.profit)}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`${(typeof row.profitRate === 'number' ? row.profitRate.toFixed(2) : '0.00')}%`}
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
      >
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除物品 "{itemToDelete?.itemName}" 吗？此操作不可撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>取消</Button>
          <Button onClick={confirmDelete} color="error">
            删除
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 导出对话框 */}
      <Dialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
      >
        <DialogTitle>导出库存数据</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            请选择导出格式：
          </DialogContentText>
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
            <Button 
              variant={exportFormat === 'xlsx' ? 'contained' : 'outlined'}
              onClick={() => setExportFormat('xlsx')}
            >
              Excel (.xlsx)
            </Button>
            <Button 
              variant={exportFormat === 'csv' ? 'contained' : 'outlined'}
              onClick={() => setExportFormat('csv')}
            >
              CSV (.csv)
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>取消</Button>
          <Button onClick={confirmExport} color="primary">
            导出
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 通知 */}
      <Snackbar
        open={notification.open}
        autoHideDuration={5000}
        onClose={handleCloseNotification}
        message={notification.message}
      />
    </Container>
  );
};

export default Inventory; 