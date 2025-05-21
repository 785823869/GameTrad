import React, { useState, useEffect, useRef } from 'react';
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
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Snackbar,
  Divider,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  CloudUpload as ImportIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  ContentCopy as CopyIcon,
  FileUpload as UploadIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import axios from 'axios';
import StockInService from '../services/StockInService';

const StockIn = () => {
  // 状态
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stockInData, setStockInData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [totalCost, setTotalCost] = useState(0);
  const [totalItems, setTotalItems] = useState(0);
  
  // 添加/编辑表单状态
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    id: null,
    itemName: '',
    quantity: '',
    cost: '',
    avgCost: '',
    note: ''
  });
  const [formErrors, setFormErrors] = useState({});
  
  // OCR导入对话框状态
  const [ocrDialogOpen, setOcrDialogOpen] = useState(false);
  const [ocrImage, setOcrImage] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState(null);
  const fileInputRef = useRef(null);
  
  // 右键菜单状态
  const [contextMenu, setContextMenu] = useState(null);
  
  // 消息通知状态
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // 获取入库数据
  useEffect(() => {
    fetchStockInData();
  }, []);
  
  // 筛选数据
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredData(stockInData);
    } else {
      const lowercasedFilter = searchTerm.toLowerCase();
      const filtered = stockInData.filter(item => 
        item.itemName.toLowerCase().includes(lowercasedFilter)
      );
      setFilteredData(filtered);
    }
    
    // 计算统计数据
    calculateStats();
  }, [searchTerm, stockInData]);
  
  // 获取入库数据
  const fetchStockInData = async () => {
    setLoading(true);
    try {
      const data = await StockInService.getAll();
      console.log("从API获取的原始数据:", data);
      
      // 检查数据是否是数组，并且不为空
      if (!Array.isArray(data)) {
        console.error("API返回的数据不是数组:", data);
        throw new Error("API返回的数据格式不正确");
      }
      
      // 格式化响应数据
      const formattedData = data.map(item => {
        // 先记录原始项目数据用于调试
        console.log("处理单条记录:", item);
        
        // 安全地处理日期
        let transactionTime;
        try {
          // 检查日期字段是否存在且不为null
          if (item.transaction_time) {
            transactionTime = new Date(item.transaction_time);
            if (isNaN(transactionTime.getTime())) {
              console.warn("无效日期格式:", item.transaction_time);
              transactionTime = new Date(); // 如果无效，使用当前日期作为后备
            }
          } else {
            console.warn("记录缺少事务时间:", item);
            transactionTime = new Date();
          }
        } catch (error) {
          console.error("日期解析错误:", error, "原始值:", item.transaction_time);
          transactionTime = new Date(); // 处理任何潜在错误
        }
        
        // 确保物品名称不为空，但不使用"未知物品"作为默认值，因为API可能已经返回了这个值
        const itemName = (item.item_name && item.item_name !== "未知物品") 
          ? item.item_name 
          : `未命名物品_${Math.random().toString(36).substr(2, 5)}`;
        
        // 更安全地解析数值
        let quantity = 0;
        try {
          quantity = item.quantity !== null && item.quantity !== undefined ? Number(item.quantity) : 0;
          if (isNaN(quantity)) quantity = 0;
        } catch (e) {
          console.error("数量解析错误:", e);
        }
        
        let cost = 0;
        try {
          cost = item.cost !== null && item.cost !== undefined ? Number(item.cost) : 0;
          if (isNaN(cost)) cost = 0;
        } catch (e) {
          console.error("成本解析错误:", e);
        }
        
        // 均价始终根据数量和成本计算
        let avgCost = 0;
        if (quantity > 0 && cost > 0) {
          avgCost = cost / quantity;
        }
        
        // 检查是否使用了错误的字段命名
        // 后端可能使用snake_case，而非前端期望的camelCase
        if (item.itemName && !item.item_name) {
          console.warn("检测到可能的字段命名不一致: itemName而不是item_name");
        }
        
        return {
          id: item.id || Math.random().toString(36).substr(2, 9),
          itemName: itemName,
          transactionTime: transactionTime,
          quantity: quantity,
          cost: cost,
          avgCost: avgCost,
          deposit: Number(item.deposit) || 0,
          note: item.note || ''
        };
      });
      
      console.log("格式化后的数据:", formattedData);
      setStockInData(formattedData);
      setError(null);
      showNotification('数据加载成功', 'success');
    } catch (err) {
      console.error('获取入库数据失败:', err);
      setError('无法加载入库数据。请检查网络连接或稍后再试。');
      showNotification('数据加载失败', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // 计算统计数据
  const calculateStats = () => {
    if (!filteredData || filteredData.length === 0) {
      setTotalCost(0);
      setTotalItems(0);
      return;
    }
    
    const cost = filteredData.reduce((sum, item) => sum + (Number(item.cost) || 0), 0);
    const items = filteredData.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0);
    
    setTotalCost(cost);
    setTotalItems(items);
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
  
  // 打开添加对话框
  const handleOpenAddDialog = () => {
    setFormData({
      id: null,
      itemName: '',
      quantity: '',
      cost: '',
      avgCost: '',
      note: ''
    });
    setFormErrors({});
    setIsEditing(false);
    setFormDialogOpen(true);
  };
  
  // 打开编辑对话框
  const handleOpenEditDialog = (item) => {
    setFormData({
      id: item.id,
      itemName: item.itemName,
      quantity: item.quantity,
      cost: item.cost,
      avgCost: item.avgCost,
      note: item.note || ''
    });
    setFormErrors({});
    setIsEditing(true);
    setFormDialogOpen(true);
    setContextMenu(null);
  };
  
  // 关闭表单对话框
  const handleCloseFormDialog = () => {
    setFormDialogOpen(false);
    setFormData({
      id: null,
      itemName: '',
      quantity: '',
      cost: '',
      avgCost: '',
      note: ''
    });
    setFormErrors({});
  };
  
  // 表单字段变更
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // 如果是数量或成本变更，自动计算均价
    if (name === 'quantity' || name === 'cost') {
      const quantity = name === 'quantity' ? parseFloat(value) || 0 : parseFloat(formData.quantity) || 0;
      const cost = name === 'cost' ? parseFloat(value) || 0 : parseFloat(formData.cost) || 0;
      
      if (quantity > 0) {
        const avgCost = cost / quantity;
        setFormData(prev => ({
          ...prev,
          [name]: value,
          avgCost: avgCost.toFixed(2)
        }));
      } else {
        setFormData(prev => ({
          ...prev,
          [name]: value,
          avgCost: '0.00'
        }));
      }
    }
  };
  
  // 验证表单
  const validateForm = () => {
    const errors = {};
    
    if (!formData.itemName.trim()) {
      errors.itemName = '物品名称不能为空';
    }
    
    if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
      errors.quantity = '数量必须大于0';
    }
    
    if (!formData.cost || parseFloat(formData.cost) <= 0) {
      errors.cost = '成本必须大于0';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  // 提交表单
  const handleSubmitForm = async () => {
    if (!validateForm()) return;
    
    // 确保均价是计算值，不能由用户提交
    const quantity = parseInt(formData.quantity);
    const cost = parseFloat(formData.cost);
    const avgCost = quantity > 0 ? cost / quantity : 0;
    
    // 确保字段名与后端接口一致
    const data = {
      item_name: formData.itemName.trim(),
      quantity: quantity,
      cost: cost,
      avg_cost: avgCost, // 使用计算得到的均价
      note: formData.note || ''
    };
    
    console.log("提交的表单数据:", data);
    
    try {
      let response;
      
      if (isEditing) {
        // 编辑模式
        response = await StockInService.update(formData.id, data);
      } else {
        // 添加模式
        response = await StockInService.add(data);
      }
      
      if (response.success) {
        handleCloseFormDialog();
        fetchStockInData();
        showNotification(isEditing ? '入库记录已更新' : '入库记录已添加', 'success');
      }
    } catch (err) {
      console.error(isEditing ? '更新入库记录失败:' : '添加入库记录失败:', err);
      showNotification(isEditing ? '更新入库记录失败' : '添加入库记录失败', 'error');
    }
  };
  
  // 打开删除对话框
  const handleOpenDeleteDialog = (item) => {
    setSelectedItem(item);
    setDeleteDialogOpen(true);
    setContextMenu(null);
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
      const response = await StockInService.delete(selectedItem.id);
      
      if (response.success) {
        setStockInData(prevData => prevData.filter(item => item.id !== selectedItem.id));
        showNotification('入库记录已删除', 'success');
      } else {
        showNotification('删除入库记录失败', 'error');
      }
      
      handleCloseDeleteDialog();
    } catch (err) {
      console.error('删除入库记录失败:', err);
      setError('删除入库记录失败。请稍后再试。');
      showNotification('删除入库记录失败', 'error');
      handleCloseDeleteDialog();
    }
  };
  
  // 数字格式化
  const formatNumber = (num) => {
    // 检查值是否有效
    if (num === undefined || num === null || isNaN(Number(num))) {
      return '0.00';
    }
    
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };
  
  // 日期格式化
  const formatDate = (date) => {
    try {
      // 检查参数是否有效
      if (!date) {
        return '无效日期';
      }
      
      // 尝试创建一个有效的Date对象
      const validDate = date instanceof Date && !isNaN(date) 
        ? date 
        : new Date(date);
      
      // 检查日期是否有效
      if (isNaN(validDate.getTime())) {
        return '无效日期';
      }
      
      // 格式化日期
      return new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).format(validDate);
    } catch (error) {
      console.error('日期格式化错误:', error);
      return '无效日期';
    }
  };
  
  // 处理刷新
  const handleRefresh = () => {
    fetchStockInData();
  };
  
  // 处理右键菜单
  const handleContextMenu = (event, item) => {
    event.preventDefault();
    setSelectedItem(item);
    setContextMenu({
      mouseX: event.clientX - 2,
      mouseY: event.clientY - 4,
    });
  };
  
  // 关闭右键菜单
  const handleCloseContextMenu = () => {
    setContextMenu(null);
  };
  
  // 复制物品名称
  const handleCopyItemName = () => {
    if (selectedItem) {
      navigator.clipboard.writeText(selectedItem.itemName);
      showNotification('物品名称已复制到剪贴板', 'info');
      handleCloseContextMenu();
    }
  };
  
  // 打开OCR导入对话框
  const handleOpenOcrDialog = () => {
    setOcrImage(null);
    setOcrResult(null);
    setOcrDialogOpen(true);
  };
  
  // 关闭OCR导入对话框
  const handleCloseOcrDialog = () => {
    setOcrDialogOpen(false);
    setOcrImage(null);
    setOcrResult(null);
  };
  
  // 选择图片文件
  const handleSelectFile = (event) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setOcrImage(file);
    }
  };
  
  // 点击上传按钮
  const handleClickUpload = () => {
    fileInputRef.current?.click();
  };
  
  // 进行OCR识别
  const handleOcrRecognize = async () => {
    if (!ocrImage) return;
    
    setOcrLoading(true);
    try {
      // 创建表单数据
      const formData = new FormData();
      formData.append('image', ocrImage);
      
      // 调用OCR API
      const response = await axios.post('/api/ocr/recognize', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data && response.data.success) {
        setOcrResult(response.data.result);
        showNotification('OCR识别成功', 'success');
      } else {
        showNotification('OCR识别失败', 'error');
      }
    } catch (err) {
      console.error('OCR识别失败:', err);
      showNotification('OCR识别处理出错', 'error');
    } finally {
      setOcrLoading(false);
    }
  };
  
  // 导入OCR结果
  const handleImportOcrResult = async () => {
    if (!ocrResult) return;
    
    try {
      const response = await StockInService.importOcr([ocrResult]);
      
      if (response.success) {
        handleCloseOcrDialog();
        fetchStockInData();
        showNotification(`成功导入${response.results.success}条记录`, 'success');
      } else {
        showNotification('导入OCR结果失败', 'error');
      }
    } catch (err) {
      console.error('导入OCR结果失败:', err);
      showNotification('导入OCR结果失败', 'error');
    }
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

  return (
    <Container maxWidth="xl" sx={{ mt: 3, mb: 4 }}>
      {/* 页面标题和描述 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary.main">
          入库管理
        </Typography>
        <Typography variant="body1" color="text.secondary">
          管理物品入库记录，记录入库成本和数量
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
              入库记录数
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="primary.main">
              {filteredData.length}
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
              入库物品总数
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="success.main">
              {totalItems && !isNaN(totalItems) ? totalItems.toLocaleString() : '0'}
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
              总成本
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" color="warning.main">
              ¥{formatNumber(totalCost)}
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
            onClick={handleOpenOcrDialog}
            sx={{ mr: 1 }}
          >
            OCR导入
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={handleOpenAddDialog}
            color="primary"
          >
            添加入库
          </Button>
        </Box>
      </Box>
      
      {/* 入库表格 */}
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
              <Table stickyHeader aria-label="入库记录表格">
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
                      入库时间
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
                      花费
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
                      均价
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
                        width: '15%'
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
                        width: '10%'
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
                        onContextMenu={(e) => handleContextMenu(e, row)}
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
                          <Tooltip title={row.itemName || '未知物品'} placement="top">
                            <span>{row.itemName || '未知物品'}</span>
                          </Tooltip>
                        </TableCell>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatDate(row.transactionTime)}</TableCell>
                        <TableCell align="right">{row.quantity !== undefined && row.quantity !== null ? row.quantity.toLocaleString() : 0}</TableCell>
                        <TableCell align="right" sx={{ color: 'warning.main', fontWeight: 500 }}>¥{formatNumber(row.cost || 0)}</TableCell>
                        <TableCell align="right" sx={{ color: 'primary.main', fontWeight: 500 }}>¥{formatNumber(row.avgCost || 0)}</TableCell>
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
                              onClick={() => handleOpenEditDialog(row)}
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
                      <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                        {searchTerm ? "没有找到匹配的入库记录" : "暂无入库数据"}
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
      
      {/* 右键菜单 */}
      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        <MenuItem onClick={handleCopyItemName}>
          <ListItemIcon>
            <CopyIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>复制物品名称</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleOpenEditDialog(selectedItem)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>编辑入库记录</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => handleOpenDeleteDialog(selectedItem)} sx={{ color: 'error.main' }}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>删除入库记录</ListItemText>
        </MenuItem>
      </Menu>
      
      {/* 添加/编辑表单对话框 */}
      <Dialog open={formDialogOpen} onClose={handleCloseFormDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{isEditing ? "编辑入库记录" : "添加入库记录"}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                name="itemName"
                label="物品名称"
                fullWidth
                value={formData.itemName}
                onChange={handleFormChange}
                error={!!formErrors.itemName}
                helperText={formErrors.itemName}
                required
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                name="quantity"
                label="数量"
                type="number"
                fullWidth
                value={formData.quantity}
                onChange={handleFormChange}
                error={!!formErrors.quantity}
                helperText={formErrors.quantity}
                required
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                name="cost"
                label="成本"
                type="number"
                fullWidth
                value={formData.cost}
                onChange={handleFormChange}
                error={!!formErrors.cost}
                helperText={formErrors.cost}
                InputProps={{
                  startAdornment: <InputAdornment position="start">¥</InputAdornment>,
                }}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                name="avgCost"
                label="均价"
                type="number"
                fullWidth
                value={formData.avgCost}
                onChange={handleFormChange}
                InputProps={{
                  startAdornment: <InputAdornment position="start">¥</InputAdornment>,
                  readOnly: true,
                }}
                disabled
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                name="note"
                label="备注"
                fullWidth
                multiline
                rows={2}
                value={formData.note}
                onChange={handleFormChange}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseFormDialog}>取消</Button>
          <Button onClick={handleSubmitForm} variant="contained" color="primary">
            {isEditing ? "更新" : "添加"}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 删除确认对话框 */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCloseDeleteDialog}
      >
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除 {selectedItem?.itemName} 的入库记录吗？此操作无法撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>取消</Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            删除
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* OCR导入对话框 */}
      <Dialog open={ocrDialogOpen} onClose={handleCloseOcrDialog} maxWidth="md" fullWidth>
        <DialogTitle>OCR识别导入</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Box sx={{ p: 2, border: '1px dashed #ccc', borderRadius: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
                {ocrImage ? (
                  <Box sx={{ width: '100%', textAlign: 'center' }}>
                    <img 
                      src={URL.createObjectURL(ocrImage)} 
                      alt="OCR识别图片" 
                      style={{ maxWidth: '100%', maxHeight: 300, objectFit: 'contain' }} 
                    />
                    <Typography variant="caption" color="text.secondary">
                      {ocrImage.name}
                    </Typography>
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center' }}>
                    <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                    <Typography variant="body1" color="text.secondary" gutterBottom>
                      点击上传图片进行OCR识别
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      支持PNG、JPG格式图片
                    </Typography>
                  </Box>
                )}
              </Box>
              <input 
                type="file" 
                accept="image/*" 
                style={{ display: 'none' }} 
                ref={fileInputRef}
                onChange={handleSelectFile}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
                <Button 
                  variant="outlined" 
                  onClick={handleClickUpload}
                  startIcon={<UploadIcon />}
                >
                  {ocrImage ? '重新上传图片' : '上传图片'}
                </Button>
                <Button 
                  variant="contained" 
                  onClick={handleOcrRecognize}
                  startIcon={<RefreshIcon />}
                  disabled={!ocrImage || ocrLoading}
                >
                  开始识别
                </Button>
              </Box>
            </Grid>
            
            {ocrLoading && (
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <CircularProgress size={24} />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                    正在进行OCR识别...
                  </Typography>
                </Box>
              </Grid>
            )}
            
            {ocrResult && (
              <Grid item xs={12}>
                <Paper sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    识别结果:
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">物品名称:</Typography>
                      <Typography variant="body1">{ocrResult.item_name}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">数量:</Typography>
                      <Typography variant="body1">{ocrResult.quantity}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">花费:</Typography>
                      <Typography variant="body1">¥{ocrResult.cost}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">均价:</Typography>
                      <Typography variant="body1">¥{(ocrResult.cost / ocrResult.quantity).toFixed(2)}</Typography>
                    </Grid>
                  </Grid>
                  <Button 
                    variant="contained" 
                    color="success" 
                    fullWidth 
                    sx={{ mt: 2 }}
                    onClick={handleImportOcrResult}
                    startIcon={<SaveIcon />}
                  >
                    导入识别结果
                  </Button>
                </Paper>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseOcrDialog}>关闭</Button>
        </DialogActions>
      </Dialog>
      
      {/* 消息通知 */}
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

export default StockIn; 