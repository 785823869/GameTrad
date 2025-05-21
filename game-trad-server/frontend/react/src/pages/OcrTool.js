import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Paper, 
  Typography, 
  Box, 
  Button, 
  TextField,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Divider,
  CircularProgress,
  Alert,
  Snackbar,
  List,
  ListItem,
  ListItemText,
  Tab,
  Tabs,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  FormHelperText,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip
} from '@mui/material';
import { 
  CloudUpload as CloudUploadIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  PlayArrow as TestIcon,
  HelpOutline as HelpIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import OCRRuleService from '../services/OCRRuleService';
import OCRRuleHelperDialog from '../components/OCRRuleHelperDialog';

// 定义交易类型
const TRANSACTION_TYPES = {
  STOCK_IN: 'stock-in',
  STOCK_OUT: 'stock-out',
  MONITOR: 'monitor'
};

// 自定义样式的上传按钮
const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

// TabPanel组件
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ocr-tabpanel-${index}`}
      aria-labelledby={`ocr-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function OcrTool() {
  // 状态变量
  const [activeTab, setActiveTab] = useState(0);
  const [rules, setRules] = useState({
    [TRANSACTION_TYPES.STOCK_IN]: [],
    [TRANSACTION_TYPES.STOCK_OUT]: [],
    [TRANSACTION_TYPES.MONITOR]: []
  });
  const [selectedRule, setSelectedRule] = useState(null);
  const [editingRule, setEditingRule] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isHelpDialogOpen, setIsHelpDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [error, setError] = useState('');
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('info');

  // 获取当前选中的交易类型
  const getCurrentType = () => {
    switch (activeTab) {
      case 0:
        return TRANSACTION_TYPES.STOCK_IN;
      case 1:
        return TRANSACTION_TYPES.STOCK_OUT;
      case 2:
        return TRANSACTION_TYPES.MONITOR;
      default:
        return TRANSACTION_TYPES.STOCK_IN;
    }
  };

  // 获取规则列表
  const fetchRules = async () => {
    try {
      setLoading(true);
      const type = getCurrentType();
      const response = await OCRRuleService.getAllRules(type);
      
      if (response && response.success) {
        setRules(prev => ({
          ...prev,
          [type]: response.data || []
        }));
      }
    } catch (err) {
      showNotification(`获取规则列表失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Tab切换
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    setSelectedRule(null);
    setEditingRule(null);
    setTestResults(null);
  };

  // 打开新增规则对话框
  const handleAddRule = () => {
    const emptyRule = {
      name: '',
      description: '',
      is_active: true,
      patterns: getDefaultPatterns(getCurrentType()),
      type: getCurrentType()
    };
    
    setEditingRule(emptyRule);
    setIsDialogOpen(true);
  };

  // 根据规则类型获取默认模式
  const getDefaultPatterns = (type) => {
    switch (type) {
      case TRANSACTION_TYPES.STOCK_IN:
        return [
          { field: 'item_name', regex: '获得了(.+?)×', group: 1, default_value: '' },
          { field: 'quantity', regex: '×(\\d+)', group: 1, default_value: '0' },
          { field: 'unit_price', regex: '失去了银两×(\\d+)', group: 1, default_value: '0' }
        ];
      case TRANSACTION_TYPES.STOCK_OUT:
        return [
          { field: 'item_name', regex: '已成功售出([^（(]+)[（(]', group: 1, default_value: '' },
          { field: 'quantity', regex: '[（(](\\d+)[）)]', group: 1, default_value: '0' },
          { field: 'unit_price', regex: '售出单价[：:]\\s*(\\d+)银两', group: 1, default_value: '0' },
          { field: 'fee', regex: '手续费[：:]\\s*(\\d+)银两', group: 1, default_value: '0' }
        ];
      case TRANSACTION_TYPES.MONITOR:
        return [
          // 基本物品信息
          { field: 'item_name', regex: '物品[:：]\\s*([^\\n]+)', group: 1, default_value: '' },
          { field: 'quantity', regex: '数量[:：]\\s*(\\d+)', group: 1, default_value: '0' },
          { field: 'market_price', regex: '一口价[:：]\\s*(\\d+)', group: 1, default_value: '0' },
          
          // 备用格式 - 当前价格
          { field: 'market_price', regex: '当前价格[:：]\\s*(\\d+)', group: 1, default_value: '0' },
          
          // 备用字段
          { field: 'server', regex: '服务器[:：]\\s*([^\\n]+)', group: 1, default_value: '' },
          { field: 'note', regex: '备注[:：]\\s*([^\\n]+)', group: 1, default_value: '' }
        ];
      default:
        return [
          { field: '', regex: '', group: 1, default_value: '' }
        ];
    }
  };

  // 打开编辑规则对话框
  const handleEditRule = (rule) => {
    setEditingRule({...rule});
    setIsDialogOpen(true);
  };

  // 关闭规则对话框
  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setEditingRule(null);
  };

  // 打开删除确认对话框
  const handleOpenDeleteDialog = (rule) => {
    setSelectedRule(rule);
    setIsDeleteDialogOpen(true);
  };

  // 关闭删除确认对话框
  const handleCloseDeleteDialog = () => {
    setIsDeleteDialogOpen(false);
  };

  // 处理规则表单更改
  const handleRuleChange = (e) => {
    const { name, value, checked } = e.target;
    
    if (name === 'is_active') {
      setEditingRule(prev => ({
        ...prev,
        [name]: checked
      }));
    } else {
      setEditingRule(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  // 更改模式字段
  const handlePatternChange = (index, field, value) => {
    const updatedPatterns = [...editingRule.patterns];
    updatedPatterns[index] = {
      ...updatedPatterns[index],
      [field]: value
    };
    
    setEditingRule(prev => ({
      ...prev,
      patterns: updatedPatterns
    }));
  };

  // 添加模式字段
  const handleAddPattern = () => {
    const newPattern = {
      field: '',
      regex: '',
      group: 1,
      default_value: ''
    };
    
    setEditingRule(prev => ({
      ...prev,
      patterns: [...prev.patterns, newPattern]
    }));
  };

  // 删除模式字段
  const handleRemovePattern = (index) => {
    const updatedPatterns = [...editingRule.patterns];
    updatedPatterns.splice(index, 1);
    
    setEditingRule(prev => ({
      ...prev,
      patterns: updatedPatterns
    }));
  };

  // 保存规则
  const handleSaveRule = async () => {
    try {
      setLoading(true);
      const type = getCurrentType();
      
      let response;
      if (editingRule.id) {
        // 更新规则
        response = await OCRRuleService.updateRule(type, editingRule.id, editingRule);
      } else {
        // 新建规则
        response = await OCRRuleService.addRule(type, editingRule);
      }
      
      if (response && response.success) {
        showNotification(
          `规则${editingRule.id ? '更新' : '创建'}成功`,
          'success'
        );
        setIsDialogOpen(false);
        fetchRules(); // 刷新规则列表
      } else {
        showNotification(`操作失败: ${response.message}`, 'error');
      }
    } catch (err) {
      showNotification(`保存规则失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 删除规则
  const handleDeleteRule = async () => {
    if (!selectedRule) return;
    
    try {
      setLoading(true);
      const type = getCurrentType();
      const response = await OCRRuleService.deleteRule(type, selectedRule.id);
      
      if (response && response.success) {
        showNotification('规则删除成功', 'success');
        setIsDeleteDialogOpen(false);
        fetchRules(); // 刷新规则列表
      } else {
        showNotification(`删除失败: ${response.message}`, 'error');
      }
    } catch (err) {
      showNotification(`删除规则失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 处理文件选择
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // 验证文件类型
      if (!file.type.match('image.*')) {
        showNotification('请选择图片文件（JPEG, PNG, GIF）', 'error');
        return;
      }
      
      // 验证文件大小
      if (file.size > 5 * 1024 * 1024) { // 5MB
        showNotification('文件大小不能超过5MB', 'error');
        return;
      }
      
      setSelectedFile(file);
      
      // 创建预览URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(file);
      
      // 清除之前的结果
      setTestResults(null);
    }
  };

  // 测试规则
  const handleTestRule = async (rule) => {
    if (!selectedFile) {
      showNotification('请先选择一个图片文件', 'error');
      return;
    }
    
    try {
      setLoading(true);
      const type = getCurrentType();
      const response = await OCRRuleService.testRule(type, rule, selectedFile);
      
      if (response && response.success) {
        setTestResults(response.data);
        showNotification('规则测试成功', 'success');
      } else {
        showNotification(`测试失败: ${response.message}`, 'error');
      }
    } catch (err) {
      showNotification(`规则测试失败: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 显示通知
  const showNotification = (message, severity = 'info') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setOpenSnackbar(true);
  };

  // 关闭通知
  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };

  // 打开帮助对话框
  const handleOpenHelpDialog = () => {
    setIsHelpDialogOpen(true);
  };

  // 关闭帮助对话框
  const handleCloseHelpDialog = () => {
    setIsHelpDialogOpen(false);
  };

  // 组件挂载和Tab切换时加载规则
  useEffect(() => {
    fetchRules();
  }, [activeTab]);

  // 初始化预设规则
  useEffect(() => {
    const initializeDefaultRules = async () => {
      try {
        // 检查交易监控规则是否为空，如果为空则创建预设规则
        const monitorResponse = await OCRRuleService.getAllRules(TRANSACTION_TYPES.MONITOR);
        if (monitorResponse && monitorResponse.success && (!monitorResponse.data || monitorResponse.data.length === 0)) {
          // 创建预设规则
          await createDefaultMonitorRules();
        }
      } catch (err) {
        console.error('初始化预设规则失败:', err);
      }
    };

    // 尝试初始化默认规则
    initializeDefaultRules();
  }, []);

  // 创建默认交易监控规则
  const createDefaultMonitorRules = async () => {
    const defaultRules = [
      // 标准摆摊格式
      {
        name: '摆摊界面格式',
        description: '适用于游戏摆摊界面的OCR识别规则',
        is_active: true,
        type: TRANSACTION_TYPES.MONITOR,
        patterns: [
          { field: 'item_name', regex: '物品[:：]\\s*([^\\n]+)', group: 1, default_value: '' },
          { field: 'quantity', regex: '数量[:：]\\s*(\\d+)', group: 1, default_value: '0' },
          { field: 'market_price', regex: '一口价[:：]\\s*(\\d+)', group: 1, default_value: '0' },
          { field: 'note', regex: '备注[:：]\\s*([^\\n]+)', group: 1, default_value: '' }
        ]
      },
      
      // 寄售行界面格式
      {
        name: '寄售行格式',
        description: '适用于游戏寄售行界面的OCR识别规则',
        is_active: true,
        type: TRANSACTION_TYPES.MONITOR,
        patterns: [
          { field: 'item_name', regex: '名称[:：]\\s*([^\\n]+)', group: 1, default_value: '' },
          { field: 'quantity', regex: '数量[:：]\\s*(\\d+)\\s', group: 1, default_value: '0' },
          { field: 'market_price', regex: '售价[:：]\\s*(\\d+)\\s', group: 1, default_value: '0' },
          { field: 'server', regex: '服务器[:：]\\s*([^\\n]+)', group: 1, default_value: '' }
        ]
      },
      
      // 价格监控格式
      {
        name: '价格监控格式',
        description: '适用于游戏价格监控界面的OCR识别规则',
        is_active: true,
        type: TRANSACTION_TYPES.MONITOR,
        patterns: [
          { field: 'item_name', regex: '([^\\d\\s][^\\n]+?)\\s+?\\d+', group: 1, default_value: '' },
          { field: 'market_price', regex: '当前价格[：:]\\s*(\\d+)', group: 1, default_value: '0' },
          { field: 'quantity', regex: '库存[：:]\\s*(\\d+)', group: 1, default_value: '0' }
        ]
      },
      
      // 通用表格格式
      {
        name: '表格提取格式',
        description: '适用于表格形式的物品价格列表',
        is_active: true,
        type: TRANSACTION_TYPES.MONITOR,
        patterns: [
          { field: 'item_name', regex: '^\\s*([^\\d\\n]+?)\\s+\\d', group: 1, default_value: '' },
          { field: 'quantity', regex: '^\\s*[^\\d\\n]+?\\s+(\\d+)\\s+\\d', group: 1, default_value: '0' },
          { field: 'market_price', regex: '^\\s*[^\\d\\n]+?\\s+\\d+\\s+(\\d+)', group: 1, default_value: '0' }
        ]
      }
    ];

    try {
      // 逐个添加默认规则
      for (const rule of defaultRules) {
        await OCRRuleService.addRule(TRANSACTION_TYPES.MONITOR, rule);
      }
      console.log('默认交易监控规则创建成功');
    } catch (err) {
      console.error('创建默认规则失败:', err);
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        OCR识别规则配置
      </Typography>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="body1">
          配置不同交易类型的OCR识别规则，支持正则表达式和字段映射。
        </Typography>
        <Button 
          startIcon={<HelpIcon />}
          onClick={handleOpenHelpDialog}
        >
          帮助
        </Button>
      </Box>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="OCR规则类型">
          <Tab label="入库管理" />
          <Tab label="出库管理" />
          <Tab label="交易监控" />
        </Tabs>
      </Box>
      
      {/* 规则列表和测试区域 */}
      <Grid container spacing={3}>
        {/* 规则列表 */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">规则列表</Typography>
              <Button 
                variant="contained" 
                color="primary" 
                startIcon={<AddIcon />}
                onClick={handleAddRule}
              >
                添加规则
              </Button>
            </Box>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : rules[getCurrentType()].length > 0 ? (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>规则名称</TableCell>
                      <TableCell>描述</TableCell>
                      <TableCell align="center">状态</TableCell>
                      <TableCell align="center">操作</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {rules[getCurrentType()].map((rule) => (
                      <TableRow key={rule.id}>
                        <TableCell>{rule.name}</TableCell>
                        <TableCell>{rule.description}</TableCell>
                        <TableCell align="center">
                          {rule.is_active ? (
                            <Typography variant="body2" color="success.main">启用</Typography>
                          ) : (
                            <Typography variant="body2" color="text.disabled">禁用</Typography>
                          )}
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title="测试规则">
                            <IconButton 
                              color="primary"
                              onClick={() => handleTestRule(rule)}
                            >
                              <TestIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="编辑规则">
                            <IconButton 
                              color="primary"
                              onClick={() => handleEditRule(rule)}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="删除规则">
                            <IconButton 
                              color="error"
                              onClick={() => handleOpenDeleteDialog(rule)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box sx={{ py: 4, textAlign: 'center' }}>
                <Typography variant="body1" color="text.secondary">
                  暂无规则，请点击"添加规则"创建新规则
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* 测试区域 */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              规则测试
            </Typography>
            
            <Box sx={{ mb: 3, border: '1px dashed grey', borderRadius: 1, p: 2 }}>
              {previewUrl ? (
                <Box sx={{ textAlign: 'center' }}>
                  <img 
                    src={previewUrl} 
                    alt="预览" 
                    style={{ maxWidth: '100%', maxHeight: 200, marginBottom: 16 }}
                  />
                  <Box>
                    <Button 
                      variant="outlined" 
                      component="label"
                    >
                      更换图片
                      <VisuallyHiddenInput 
                        type="file" 
                        onChange={handleFileChange}
                        accept="image/*" 
                      />
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                  <Typography variant="body1" gutterBottom>
                    选择图片进行规则测试
                  </Typography>
                  <Button 
                    variant="contained" 
                    component="label"
                  >
                    上传图片
                    <VisuallyHiddenInput 
                      type="file" 
                      onChange={handleFileChange}
                      accept="image/*" 
                    />
                  </Button>
                </Box>
              )}
            </Box>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                <CircularProgress />
              </Box>
            ) : testResults ? (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  测试结果:
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    原始文本:
                  </Typography>
                  <TextField
                    multiline
                    rows={4}
                    fullWidth
                    variant="outlined"
                    value={testResults.rawText || ''}
                    InputProps={{ readOnly: true }}
                  />
                </Box>
                
                <Typography variant="subtitle2" gutterBottom>
                  解析字段:
                </Typography>
                
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>字段名</TableCell>
                        <TableCell>值</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(testResults.parsed || {}).map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell>{key}</TableCell>
                          <TableCell>{String(value)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  上传图片并选择规则进行测试
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      {/* 规则编辑对话框 */}
      <Dialog 
        open={isDialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingRule?.id ? '编辑规则' : '新建规则'}
        </DialogTitle>
        <DialogContent dividers>
          {editingRule && (
            <Grid container spacing={2}>
              {/* 基本信息 */}
              <Grid item xs={12} sm={6}>
                <TextField
                  name="name"
                  label="规则名称"
                  value={editingRule.name}
                  onChange={handleRuleChange}
                  fullWidth
                  required
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      name="is_active"
                      checked={editingRule.is_active}
                      onChange={handleRuleChange}
                      color="primary"
                    />
                  }
                  label="启用规则"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  name="description"
                  label="规则描述"
                  value={editingRule.description}
                  onChange={handleRuleChange}
                  fullWidth
                  multiline
                  rows={2}
                  margin="normal"
                />
              </Grid>
              
              {/* 模式列表 */}
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  字段匹配模式
                </Typography>
                
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>字段名</TableCell>
                        <TableCell>正则表达式</TableCell>
                        <TableCell>组序号</TableCell>
                        <TableCell>默认值</TableCell>
                        <TableCell align="center">操作</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {editingRule.patterns.map((pattern, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <TextField
                              value={pattern.field}
                              onChange={(e) => handlePatternChange(index, 'field', e.target.value)}
                              size="small"
                              fullWidth
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              value={pattern.regex}
                              onChange={(e) => handlePatternChange(index, 'regex', e.target.value)}
                              size="small"
                              fullWidth
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              value={pattern.group}
                              onChange={(e) => handlePatternChange(index, 'group', e.target.value)}
                              size="small"
                              type="number"
                              inputProps={{ min: 1 }}
                              style={{ width: '80px' }}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              value={pattern.default_value}
                              onChange={(e) => handlePatternChange(index, 'default_value', e.target.value)}
                              size="small"
                              fullWidth
                            />
                          </TableCell>
                          <TableCell align="center">
                            <IconButton 
                              size="small" 
                              color="error"
                              onClick={() => handleRemovePattern(index)}
                              disabled={editingRule.patterns.length <= 1}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                
                <Box sx={{ mt: 2, textAlign: 'right' }}>
                  <Button 
                    startIcon={<AddIcon />}
                    onClick={handleAddPattern}
                  >
                    添加字段
                  </Button>
                </Box>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button 
            onClick={handleSaveRule}
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            disabled={loading}
          >
            {loading ? '保存中...' : '保存'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 删除确认对话框 */}
      <Dialog
        open={isDeleteDialogOpen}
        onClose={handleCloseDeleteDialog}
      >
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <Typography>
            确定要删除规则 "{selectedRule?.name}" 吗？此操作无法撤销。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>取消</Button>
          <Button 
            onClick={handleDeleteRule}
            variant="contained" 
            color="error"
          >
            删除
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 通知 */}
      <Snackbar open={openSnackbar} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
      
      {/* 帮助对话框 */}
      <OCRRuleHelperDialog 
        open={isHelpDialogOpen} 
        onClose={handleCloseHelpDialog}
        transactionType={getCurrentType()}
      />
    </Box>
  );
}

export default OcrTool; 