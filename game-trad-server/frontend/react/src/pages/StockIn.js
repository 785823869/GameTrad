import React, { useState, useEffect, useCallback } from 'react';
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
  CircularProgress,
  Alert,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Snackbar,
  Divider,
  Checkbox,
  Badge,
  FormControlLabel,
  Collapse,
  Card,
  CardContent,
  Slider,
  Stack
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  CloudUpload as ImportIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  ContentCopy as CopyIcon,
  DeleteSweep as DeleteSweepIcon,
  FilterList as FilterIcon,
  FilterAlt as FilterAltIcon,
  ClearAll as ClearAllIcon,
  CalendarMonth as CalendarIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import StockInService from '../services/StockInService';
import OCRDialog from '../components/OCRDialog';
import OCRService from '../services/OCRService';

const StockIn = () => {
  // 调试模式常量
  const DEBUG = true;

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
  
  // 右键菜单状态
  const [contextMenu, setContextMenu] = useState(null);
  
  // 消息通知状态
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // 多选相关状态
  const [selected, setSelected] = useState([]);
  const [batchDeleteDialogOpen, setBatchDeleteDialogOpen] = useState(false);
  
  // 高级筛选相关状态
  const [showFilter, setShowFilter] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: {
      start: null,
      end: null
    },
    quantityRange: [0, 100000],   // 更宽松的数量范围
    costRange: [0, 10000000],     // 更宽松的成本范围
    avgCostRange: [0, 100000],    // 更宽松的均价范围
    hasNote: false
  });
  const [activeFilterCount, setActiveFilterCount] = useState(0);
  
  // 计算统计数据 - 接受可选的已筛选数据参数
  const calculateStats = useCallback((data = filteredData) => {
    if (!data || data.length === 0) {
      setTotalCost(0);
      setTotalItems(0);
      return;
    }
    
    const cost = data.reduce((sum, item) => sum + (Number(item.cost) || 0), 0);
    const items = data.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0);
    
    setTotalCost(cost);
    setTotalItems(items);
  }, [filteredData]);
  
  // 获取入库数据
  const fetchStockInData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await StockInService.getAll();
      console.log("从API获取的原始数据:", data);
      console.log("原始数据类型:", typeof data);
      console.log("原始数据是否为数组:", Array.isArray(data));
      console.log("原始数据长度:", data.length);
      
      // 如果有数据，查看第一条记录的结构
      if (Array.isArray(data) && data.length > 0) {
        console.log("第一条记录结构:", JSON.stringify(data[0]));
        console.log("第一条记录字段:", Object.keys(data[0]));
      }
      
      // 检查数据是否是数组，并且不为空
      if (!Array.isArray(data)) {
        console.error("API返回的数据不是数组:", data);
        throw new Error("API返回的数据格式不正确");
      }
      
      // 格式化响应数据
      const formattedData = data.map((item, index) => {
        // 先记录原始项目数据用于调试
        console.log(`处理记录 ${index} (ID=${item.id}):`, JSON.stringify(item));
        
        // 安全地处理日期
        let transactionTime;
        try {
          // 检查日期字段是否存在且不为null
          if (item.transaction_time) {
            transactionTime = new Date(item.transaction_time);
            if (isNaN(transactionTime.getTime())) {
              console.warn(`记录 ${index}: 无效日期格式:`, item.transaction_time);
              transactionTime = new Date(); // 如果无效，使用当前日期作为后备
            } else {
              console.log(`记录 ${index}: 日期转换成功:`, transactionTime);
            }
          } else {
            console.warn(`记录 ${index}: 缺少事务时间:`, item);
            transactionTime = new Date();
          }
        } catch (error) {
          console.error(`记录 ${index}: 日期解析错误:`, error, "原始值:", item.transaction_time);
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
          if (isNaN(quantity)) {
            console.warn(`记录 ${index}: 数量解析失败, 原始值:`, item.quantity);
            quantity = 0;
          } else {
            console.log(`记录 ${index}: 数量解析成功:`, quantity);
          }
        } catch (e) {
          console.error(`记录 ${index}: 数量解析错误:`, e);
        }
        
        let cost = 0;
        try {
          cost = item.cost !== null && item.cost !== undefined ? Number(item.cost) : 0;
          if (isNaN(cost)) {
            console.warn(`记录 ${index}: 成本解析失败, 原始值:`, item.cost);
            cost = 0;
          } else {
            console.log(`记录 ${index}: 成本解析成功:`, cost);
          }
        } catch (e) {
          console.error(`记录 ${index}: 成本解析错误:`, e);
        }
        
        // 从后端获取均价或者计算均价
        let avgCost = 0;
        if (item.avg_cost !== undefined && item.avg_cost !== null) {
          // 如果后端提供了均价，直接使用
          avgCost = Number(item.avg_cost);
          console.log(`记录 ${index}: 使用后端提供的均价:`, avgCost);
        } else if (quantity > 0 && cost > 0) {
          // 否则自己计算
          avgCost = cost / quantity;
          console.log(`记录 ${index}: 本地计算均价:`, avgCost);
        }
        
        // 检查是否使用了错误的字段命名
        // 后端可能使用snake_case，而非前端期望的camelCase
        if (item.itemName && !item.item_name) {
          console.warn(`记录 ${index}: 检测到可能的字段命名不一致: itemName而不是item_name`);
        }
        
        if (item.avg_cost !== undefined) {
          console.log(`记录 ${index}: 后端提供的均价:`, item.avg_cost);
        }
        
        const result = {
          id: item.id || Math.random().toString(36).substr(2, 9),
          itemName: itemName,
          transactionTime: transactionTime,
          quantity: quantity,
          cost: cost,
          avgCost: avgCost,
          deposit: Number(item.deposit) || 0,
          note: item.note || ''
        };
        
        console.log(`记录 ${index}: 转换结果:`, result);
        return result;
      });
      
      console.log("格式化后的数据:", formattedData);
      console.log("格式化后数据长度:", formattedData.length);
      
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
  }, []);
  
  // 筛选数据
  useEffect(() => {
    // 应用所有筛选条件
    if (DEBUG) {
      console.log('开始应用筛选条件...');
      console.log('原始数据数量:', stockInData.length);
      console.log('当前筛选条件:', filters);
    }
    
    let filtered = stockInData;
    
    // 基本搜索筛选 - 物品名称
    if (searchTerm.trim() !== '') {
      const lowercasedFilter = searchTerm.toLowerCase();
      filtered = filtered.filter(item => 
        item.itemName.toLowerCase().includes(lowercasedFilter)
      );
      if (DEBUG) console.log(`应用名称搜索后数据数量: ${filtered.length}`);
    }
    
    // 高级筛选 - 日期范围
    if (filters.dateRange.start || filters.dateRange.end) {
      if (DEBUG) console.log('应用日期筛选...');
      filtered = filtered.filter(item => {
        const itemDate = new Date(item.transactionTime);
        
        if (filters.dateRange.start && filters.dateRange.end) {
          return itemDate >= filters.dateRange.start && itemDate <= filters.dateRange.end;
        } else if (filters.dateRange.start) {
          return itemDate >= filters.dateRange.start;
        } else if (filters.dateRange.end) {
          return itemDate <= filters.dateRange.end;
        }
        
        return true;
      });
      if (DEBUG) console.log(`应用日期筛选后数据数量: ${filtered.length}`);
    }
    
    // 高级筛选 - 数量范围
    if (DEBUG) console.log('应用数量筛选, 范围:', filters.quantityRange);
    filtered = filtered.filter(item => 
      item.quantity >= filters.quantityRange[0] && 
      item.quantity <= filters.quantityRange[1]
    );
    if (DEBUG) console.log(`应用数量筛选后数据数量: ${filtered.length}`);
    
    // 高级筛选 - 成本范围
    if (DEBUG) console.log('应用成本筛选, 范围:', filters.costRange);
    filtered = filtered.filter(item => 
      item.cost >= filters.costRange[0] && 
      item.cost <= filters.costRange[1]
    );
    if (DEBUG) console.log(`应用成本筛选后数据数量: ${filtered.length}`);
    
    // 高级筛选 - 均价范围
    if (DEBUG) console.log('应用均价筛选, 范围:', filters.avgCostRange);
    filtered = filtered.filter(item => 
      item.avgCost >= filters.avgCostRange[0] && 
      item.avgCost <= filters.avgCostRange[1]
    );
    if (DEBUG) console.log(`应用均价筛选后数据数量: ${filtered.length}`);
    
    // 高级筛选 - 备注筛选
    if (filters.hasNote) {
      filtered = filtered.filter(item => 
        item.note && item.note.trim() !== ''
      );
      if (DEBUG) console.log(`应用备注筛选后数据数量: ${filtered.length}`);
    }
    
    console.log("应用筛选后的数据数量:", filtered.length);
    setFilteredData(filtered);
    
    // 计算统计数据
    calculateStats(filtered);
    
    // 计算活跃筛选器数量
    let count = 0;
    if (filters.dateRange.start || filters.dateRange.end) count++;
    if (filters.quantityRange[0] > 0 || filters.quantityRange[1] < 100000) count++;
    if (filters.costRange[0] > 0 || filters.costRange[1] < 10000000) count++;
    if (filters.avgCostRange[0] > 0 || filters.avgCostRange[1] < 100000) count++;
    if (filters.hasNote) count++;
    
    setActiveFilterCount(count);
    
    if (DEBUG) {
      console.log('筛选完成, 活跃筛选数量:', count);
      if (filtered.length > 0) {
        console.log('筛选后的第一条记录:', filtered[0]);
      } else {
        console.log('筛选后没有记录!');
      }
    }
    
  }, [searchTerm, stockInData, filters, DEBUG, calculateStats]);
  
  // 获取入库数据
  useEffect(() => {
    fetchStockInData();
  }, [fetchStockInData]);
  
  // 处理搜索
  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };
  
  // 处理高级筛选开关
  const toggleFilter = () => {
    setShowFilter(!showFilter);
  };
  
  // 处理日期筛选变更
  const handleDateFilterChange = (type, date) => {
    setFilters(prev => ({
      ...prev,
      dateRange: {
        ...prev.dateRange,
        [type]: date
      }
    }));
    setPage(0);
  };
  
  // 处理范围筛选变更
  const handleRangeFilterChange = (type, value) => {
    setFilters(prev => ({
      ...prev,
      [type]: value
    }));
    setPage(0);
  };
  
  // 处理备注筛选变更
  const handleNoteFilterChange = (event) => {
    setFilters(prev => ({
      ...prev,
      hasNote: event.target.checked
    }));
    setPage(0);
  };
  
  // 重置所有筛选条件
  const resetFilters = () => {
    setFilters({
      dateRange: {
        start: null,
        end: null
      },
      quantityRange: [0, 100000],
      costRange: [0, 10000000],
      avgCostRange: [0, 100000],
      hasNote: false
    });
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
  
  // 多选功能 - 处理单个项目选择
  const handleSelect = (event, id) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected = [];

    if (selectedIndex === -1) {
      // 如果未选中，则添加到选中列表
      newSelected = [...selected, id];
    } else {
      // 如果已选中，则从选中列表中移除
      newSelected = selected.filter(itemId => itemId !== id);
    }

    setSelected(newSelected);
  };

  // 多选功能 - 处理全选/取消全选
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      // 获取当前页的所有项目ID
      const currentPageIds = filteredData
        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
        .map(item => item.id);
      setSelected(currentPageIds);
    } else {
      setSelected([]);
    }
  };

  // 多选功能 - 检查项目是否被选中
  const isSelected = (id) => selected.indexOf(id) !== -1;

  // 多选功能 - 打开批量删除对话框
  const handleOpenBatchDeleteDialog = () => {
    if (selected.length === 0) {
      showNotification('请先选择要删除的记录', 'warning');
      return;
    }
    setBatchDeleteDialogOpen(true);
  };

  // 多选功能 - 关闭批量删除对话框
  const handleCloseBatchDeleteDialog = () => {
    setBatchDeleteDialogOpen(false);
  };

  // 多选功能 - 确认批量删除
  const handleConfirmBatchDelete = async () => {
    try {
      const DEBUG = false;
      
      if (DEBUG) console.log(`准备批量删除${selected.length}条记录...`);
      
      // 创建删除操作的Promise数组
      const deletePromises = [];
      const failedIds = [];
      
      for (const id of selected) {
        try {
          const deletePromise = StockInService.delete(id)
            .catch(err => {
              console.error(`删除ID=${id}的记录失败:`, err);
              failedIds.push(id);
              return { success: false, id };
            });
          
          deletePromises.push(deletePromise);
        } catch (e) {
          console.error(`为ID=${id}创建删除请求失败:`, e);
          failedIds.push(id);
        }
      }
      
      // 等待所有删除操作完成
      if (deletePromises.length > 0) {
        await Promise.all(deletePromises);
      }
      
      // 从前端状态中移除所有已选记录
      setStockInData(prevData => prevData.filter(item => !selected.includes(item.id)));
      
      // 显示操作结果
      if (failedIds.length === 0) {
        showNotification(`成功删除${selected.length}条记录`, 'success');
      } else {
        showNotification(`删除操作部分成功，${failedIds.length}条记录删除失败`, 'warning');
      }
      
      // 清空选中状态
      setSelected([]);
      handleCloseBatchDeleteDialog();
      
    } catch (err) {
      console.error('批量删除操作失败:', err);
      showNotification('批量删除操作失败，请重试', 'error');
      handleCloseBatchDeleteDialog();
    }
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
    setSelected([]); // 刷新时清空选中状态
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
  
  // 处理OCR导入
  const handleOcrImport = async (ocrResults) => {
    try {
      // 处理OCR导入结果
      console.log("准备写入的有效OCR数据:", ocrResults);
      
      // 调用API导入数据
      const response = await OCRService.importOCRResults('in', ocrResults);
      
      if (response.success) {
        // 成功导入后刷新数据
        await fetchStockInData();
        showNotification(`${response.message || `成功导入${ocrResults.length}条记录`}`, 'success');
      } else {
        throw new Error(response.message || '导入失败');
      }
    } catch (err) {
      console.error('导入OCR结果失败:', err);
      showNotification('导入OCR结果失败: ' + (err.message || err), 'error');
    }
  };
  
  // 打开OCR导入对话框
  const handleOpenOcrDialog = () => {
    setOcrDialogOpen(true);
  };
  
  // 关闭OCR导入对话框
  const handleCloseOcrDialog = () => {
    setOcrDialogOpen(false);
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
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
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
          <Button
            size="small"
            variant="outlined"
            color={activeFilterCount > 0 ? "primary" : "inherit"}
            startIcon={activeFilterCount > 0 ? <Badge badgeContent={activeFilterCount} color="primary"><FilterAltIcon /></Badge> : <FilterIcon />}
            onClick={toggleFilter}
            sx={{ ml: 1 }}
          >
            高级筛选
          </Button>
        </Box>
        <Box>
          {/* 批量删除按钮 */}
          {selected.length > 0 && (
            <Button 
              variant="outlined" 
              color="error"
              startIcon={<DeleteSweepIcon />}
              onClick={handleOpenBatchDeleteDialog}
              sx={{ mr: 1 }}
            >
              删除选中 ({selected.length})
            </Button>
          )}
          
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
      
      {/* 高级筛选面板 */}
      <Collapse in={showFilter} sx={{ mb: 2 }}>
        <Card variant="outlined">
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold" color="primary">
                高级筛选
              </Typography>
              <Button 
                size="small" 
                variant="outlined" 
                startIcon={<ClearAllIcon />}
                onClick={resetFilters}
              >
                重置筛选
              </Button>
            </Box>
            
            <Grid container spacing={3}>
              {/* 日期范围筛选 */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <CalendarIcon fontSize="small" sx={{ mr: 1 }} />
                  日期范围
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <DatePicker 
                    label="开始日期" 
                    value={filters.dateRange.start}
                    onChange={(date) => handleDateFilterChange('start', date)}
                    renderInput={(params) => <TextField {...params} size="small" fullWidth />}
                    maxDate={filters.dateRange.end || undefined}
                  />
                  <DatePicker 
                    label="结束日期" 
                    value={filters.dateRange.end}
                    onChange={(date) => handleDateFilterChange('end', date)}
                    renderInput={(params) => <TextField {...params} size="small" fullWidth />}
                    minDate={filters.dateRange.start || undefined}
                  />
                </Stack>
              </Grid>
              
              {/* 备注筛选 */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  其他筛选
                </Typography>
                <FormControlLabel
                  control={
                    <Checkbox 
                      checked={filters.hasNote} 
                      onChange={handleNoteFilterChange}
                      size="small"
                    />
                  }
                  label="仅显示有备注的记录"
                />
              </Grid>
              
              {/* 数量范围筛选 */}
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" gutterBottom>
                  数量范围: {filters.quantityRange[0]} - {filters.quantityRange[1]}
                </Typography>
                <Slider
                  value={filters.quantityRange}
                  onChange={(e, newValue) => handleRangeFilterChange('quantityRange', newValue)}
                  valueLabelDisplay="auto"
                  min={0}
                  max={100000}
                />
              </Grid>
              
              {/* 成本范围筛选 */}
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" gutterBottom>
                  成本范围: ¥{filters.costRange[0]} - ¥{filters.costRange[1]}
                </Typography>
                <Slider
                  value={filters.costRange}
                  onChange={(e, newValue) => handleRangeFilterChange('costRange', newValue)}
                  valueLabelDisplay="auto"
                  min={0}
                  max={10000000}
                  step={1000}
                />
              </Grid>
              
              {/* 均价范围筛选 */}
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" gutterBottom>
                  均价范围: ¥{filters.avgCostRange[0]} - ¥{filters.avgCostRange[1]}
                </Typography>
                <Slider
                  value={filters.avgCostRange}
                  onChange={(e, newValue) => handleRangeFilterChange('avgCostRange', newValue)}
                  valueLabelDisplay="auto"
                  min={0}
                  max={100000}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Collapse>
      
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
                    {/* 多选复选框列 */}
                    <TableCell
                      padding="checkbox"
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
                        width: '48px'
                      }}
                    >
                      <Checkbox
                        indeterminate={
                          selected.length > 0 && 
                          selected.length < filteredData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).length
                        }
                        checked={
                          filteredData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).length > 0 &&
                          selected.length === filteredData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).length
                        }
                        onChange={handleSelectAll}
                        inputProps={{ 'aria-label': '全选' }}
                      />
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
                    .map((row, index) => {
                      const isItemSelected = isSelected(row.id);
                      
                      return (
                        <TableRow 
                          key={row.id} 
                          hover 
                          selected={isItemSelected}
                          onContextMenu={(e) => handleContextMenu(e, row)}
                          sx={{ 
                            "&:nth-of-type(odd)": { 
                              backgroundColor: "rgba(0, 0, 0, 0.02)" 
                            },
                            "&:hover": {
                              backgroundColor: "rgba(0, 0, 0, 0.04)"
                            },
                            // 为选中的行添加高亮样式
                            ...(isItemSelected && {
                              backgroundColor: "rgba(25, 118, 210, 0.08)",
                              "&:nth-of-type(odd)": { 
                                backgroundColor: "rgba(25, 118, 210, 0.12)" 
                              },
                              "&:hover": {
                                backgroundColor: "rgba(25, 118, 210, 0.16)"
                              }
                            })
                          }}
                        >
                          {/* 复选框单元格 */}
                          <TableCell padding="checkbox">
                            <Checkbox
                              checked={isItemSelected}
                              onChange={(event) => handleSelect(event, row.id)}
                              inputProps={{ 'aria-labelledby': `enhanced-table-checkbox-${index}` }}
                            />
                          </TableCell>
                          
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
                      );
                    })}
                  {filteredData.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ py: 3 }}>
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
      
      {/* 批量删除确认对话框 */}
      <Dialog
        open={batchDeleteDialogOpen}
        onClose={handleCloseBatchDeleteDialog}
      >
        <DialogTitle>批量删除确认</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除选中的 {selected.length} 条入库记录吗？此操作无法撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseBatchDeleteDialog} color="primary">
            取消
          </Button>
          <Button onClick={handleConfirmBatchDelete} color="error" variant="contained">
            批量删除
          </Button>
        </DialogActions>
      </Dialog>
      
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
      
      {/* OCR导入对话框 - 替换旧的对话框 */}
      <OCRDialog 
        open={ocrDialogOpen} 
        onClose={handleCloseOcrDialog}
        onImport={handleOcrImport}
        title="OCR入库导入"
        type="in"
      />
      
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