import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  TextField, 
  Button, 
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Divider,
  CircularProgress,
  InputAdornment,
  Autocomplete,
  Chip
} from '@mui/material';
import {
  Save as SaveIcon,
  Add as AddIcon,
  CameraAlt as CameraIcon,
  ArrowBack as BackIcon,
  ArrowForward as NextIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const NewTrade = () => {
  const navigate = useNavigate();
  
  // 交易状态数据
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [items, setItems] = useState([]);
  
  // 表单数据
  const [formData, setFormData] = useState({
    tradeType: 'in', // 'in' 或 'out'
    itemName: '',
    quantity: '',
    price: '',
    totalAmount: '',
    fee: '0',
    note: '',
    tradeTime: new Date().toISOString().slice(0, 16),
    images: []
  });
  
  // 获取物品列表
  useEffect(() => {
    const fetchItems = async () => {
      try {
        const response = await axios.get('/api/items');
        setItems(response.data || []);
      } catch (err) {
        console.error('获取物品列表失败:', err);
      }
    };
    fetchItems();
  }, []);
  
  // 步骤标题
  const steps = ['选择交易类型', '填写交易信息', '确认与提交'];
  
  // 处理步骤导航
  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };
  
  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };
  
  // 处理表单更改
  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // 特殊处理数量和价格，自动计算总金额
    if (name === 'quantity' || name === 'price') {
      const quantity = name === 'quantity' ? parseFloat(value) || 0 : parseFloat(formData.quantity) || 0;
      const price = name === 'price' ? parseFloat(value) || 0 : parseFloat(formData.price) || 0;
      const fee = parseFloat(formData.fee) || 0;
      
      // 计算总金额 (出库时减去手续费)
      const totalAmount = formData.tradeType === 'out' 
        ? (quantity * price - fee).toFixed(2)
        : (quantity * price).toFixed(2);
        
      setFormData({
        ...formData,
        [name]: value,
        totalAmount
      });
    } else if (name === 'fee' && formData.tradeType === 'out') {
      // 如果修改手续费，重新计算总金额
      const quantity = parseFloat(formData.quantity) || 0;
      const price = parseFloat(formData.price) || 0;
      const fee = parseFloat(value) || 0;
      const totalAmount = (quantity * price - fee).toFixed(2);
      
      setFormData({
        ...formData,
        fee: value,
        totalAmount
      });
    } else if (name === 'tradeType') {
      // 切换交易类型时重新计算总金额并重置一些字段
      const quantity = parseFloat(formData.quantity) || 0;
      const price = parseFloat(formData.price) || 0;
      const fee = parseFloat(formData.fee) || 0;
      const totalAmount = value === 'out' 
        ? (quantity * price - fee).toFixed(2)
        : (quantity * price).toFixed(2);
        
      setFormData({
        ...formData,
        [name]: value,
        totalAmount
      });
    } else {
      // 普通字段直接更新
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };
  
  // 处理自动完成组件选择
  const handleItemSelect = (event, newValue) => {
    setFormData({
      ...formData,
      itemName: newValue
    });
  };
  
  // 处理图片上传
  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      // 这里可以添加图片预览或处理逻辑
      setFormData({
        ...formData,
        images: [...formData.images, ...files]
      });
    }
  };
  
  // 移除已上传图片
  const handleRemoveImage = (index) => {
    const newImages = [...formData.images];
    newImages.splice(index, 1);
    setFormData({
      ...formData,
      images: newImages
    });
  };
  
  // 提交表单
  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 构建提交数据
      const submitData = {
        ...formData,
        tradeTime: new Date(formData.tradeTime).toISOString(),
        quantity: parseInt(formData.quantity, 10),
        price: parseFloat(formData.price),
        totalAmount: parseFloat(formData.totalAmount),
        fee: parseFloat(formData.fee)
      };
      
      // 处理图片上传（如需要）
      if (formData.images.length > 0) {
        // 这里可以添加图片上传逻辑
      }
      
      // 发送请求到相应端点
      const endpoint = formData.tradeType === 'in' ? '/api/stock-in' : '/api/stock-out';
      const response = await axios.post(endpoint, submitData);
      
      setSuccess(true);
      
      // 3秒后跳转到相应页面
      setTimeout(() => {
        navigate(formData.tradeType === 'in' ? '/stock-in' : '/stock-out');
      }, 3000);
      
    } catch (err) {
      console.error('提交交易失败:', err);
      setError(err.response?.data?.message || '提交交易失败，请稍后再试');
    } finally {
      setLoading(false);
    }
  };
  
  // 验证当前步骤是否可进行下一步
  const isStepValid = () => {
    switch (activeStep) {
      case 0:
        // 第一步只需选择交易类型
        return !!formData.tradeType;
      case 1:
        // 第二步需要填写物品名称、数量和价格
        return !!formData.itemName && 
               !!formData.quantity && 
               parseFloat(formData.quantity) > 0 && 
               !!formData.price && 
               parseFloat(formData.price) > 0;
      default:
        return true;
    }
  };
  
  // 渲染步骤内容
  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              选择交易类型
            </Typography>
            <Grid container spacing={3} sx={{ mt: 2 }}>
              <Grid item xs={12} sm={6}>
                <Paper 
                  sx={{ 
                    p: 3, 
                    textAlign: 'center',
                    cursor: 'pointer',
                    border: formData.tradeType === 'in' ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    borderRadius: 2,
                    transition: 'all 0.3s',
                    '&:hover': {
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
                    }
                  }}
                  onClick={() => handleChange({ target: { name: 'tradeType', value: 'in' } })}
                >
                  <Box sx={{ mb: 2 }}>
                    <AddIcon sx={{ fontSize: 48, color: '#2e7d32' }} />
                  </Box>
                  <Typography variant="h5" component="div" gutterBottom>
                    入库
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    添加物品到库存，记录成本和数量
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Paper 
                  sx={{ 
                    p: 3, 
                    textAlign: 'center',
                    cursor: 'pointer',
                    border: formData.tradeType === 'out' ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    borderRadius: 2,
                    transition: 'all 0.3s',
                    '&:hover': {
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
                    }
                  }}
                  onClick={() => handleChange({ target: { name: 'tradeType', value: 'out' } })}
                >
                  <Box sx={{ mb: 2 }}>
                    <BackIcon sx={{ fontSize: 48, color: '#d32f2f', transform: 'rotate(180deg)' }} />
                  </Box>
                  <Typography variant="h5" component="div" gutterBottom>
                    出库
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    从库存中出售物品，记录收入和利润
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        );
      case 1:
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              填写{formData.tradeType === 'in' ? '入库' : '出库'}信息
            </Typography>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Autocomplete
                  value={formData.itemName}
                  onChange={handleItemSelect}
                  options={items}
                  freeSolo
                  renderInput={(params) => (
                    <TextField 
                      {...params} 
                      label="物品名称" 
                      required
                      fullWidth
                      variant="outlined"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="数量"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleChange}
                  required
                  fullWidth
                  type="number"
                  inputProps={{ min: 1 }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label={formData.tradeType === 'in' ? '单价(成本)' : '单价(售价)'}
                  name="price"
                  value={formData.price}
                  onChange={handleChange}
                  required
                  fullWidth
                  type="number"
                  inputProps={{ step: 0.01, min: 0 }}
                  variant="outlined"
                  InputProps={{
                    startAdornment: <InputAdornment position="start">¥</InputAdornment>,
                  }}
                />
              </Grid>
              {formData.tradeType === 'out' && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="手续费"
                    name="fee"
                    value={formData.fee}
                    onChange={handleChange}
                    fullWidth
                    type="number"
                    inputProps={{ step: 0.01, min: 0 }}
                    variant="outlined"
                    InputProps={{
                      startAdornment: <InputAdornment position="start">¥</InputAdornment>,
                    }}
                  />
                </Grid>
              )}
              <Grid item xs={12} sm={formData.tradeType === 'out' ? 6 : 12}>
                <TextField
                  label="总金额"
                  name="totalAmount"
                  value={formData.totalAmount}
                  onChange={handleChange}
                  fullWidth
                  type="number"
                  inputProps={{ step: 0.01, min: 0 }}
                  variant="outlined"
                  InputProps={{
                    startAdornment: <InputAdornment position="start">¥</InputAdornment>,
                    readOnly: true
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="交易时间"
                  name="tradeTime"
                  value={formData.tradeTime}
                  onChange={handleChange}
                  fullWidth
                  type="datetime-local"
                  variant="outlined"
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="备注"
                  name="note"
                  value={formData.note}
                  onChange={handleChange}
                  fullWidth
                  multiline
                  rows={3}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ mt: 1, mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    添加图片(可选)
                  </Typography>
                  <Button
                    variant="outlined"
                    component="label"
                    startIcon={<CameraIcon />}
                  >
                    上传图片
                    <input
                      type="file"
                      hidden
                      accept="image/*"
                      multiple
                      onChange={handleImageUpload}
                    />
                  </Button>
                </Box>
                {formData.images.length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
                    {formData.images.map((image, index) => (
                      <Chip
                        key={index}
                        label={image.name}
                        onDelete={() => handleRemoveImage(index)}
                      />
                    ))}
                  </Box>
                )}
              </Grid>
            </Grid>
          </Box>
        );
      case 2:
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              确认{formData.tradeType === 'in' ? '入库' : '出库'}信息
            </Typography>
            <Paper sx={{ p: 3, mt: 2, backgroundColor: '#f9f9f9', borderRadius: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    交易类型
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.tradeType === 'in' ? '入库' : '出库'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    物品名称
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.itemName}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    数量
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.quantity}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    单价
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    ¥{parseFloat(formData.price).toFixed(2)}
                  </Typography>
                </Grid>
                {formData.tradeType === 'out' && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      手续费
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      ¥{parseFloat(formData.fee).toFixed(2)}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    总金额
                  </Typography>
                  <Typography variant="body1" fontWeight="bold" gutterBottom>
                    ¥{parseFloat(formData.totalAmount).toFixed(2)}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    交易时间
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {new Date(formData.tradeTime).toLocaleString()}
                  </Typography>
                </Grid>
                {formData.note && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      备注
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {formData.note}
                    </Typography>
                  </Grid>
                )}
                {formData.images.length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      上传图片
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      已上传 {formData.images.length} 张图片
                    </Typography>
                  </Grid>
                )}
              </Grid>
              
              {/* 成功或错误信息 */}
              {success && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  交易已成功保存！3秒后跳转到{formData.tradeType === 'in' ? '入库' : '出库'}管理页面。
                </Alert>
              )}
              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </Paper>
          </Box>
        );
      default:
        return '未知步骤';
    }
  };
  
  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 8 }}>
      {/* 页面标题 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary.main">
          新建交易
        </Typography>
        <Typography variant="body1" color="text.secondary">
          录入新的交易信息，管理物品入库或出库
        </Typography>
      </Box>
      
      {/* 步骤指示器 */}
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      {/* 主内容区 */}
      <Paper 
        elevation={0} 
        sx={{ 
          borderRadius: 2, 
          overflow: 'hidden',
          border: '1px solid #e0e0e0'
        }}
      >
        {getStepContent(activeStep)}
        <Divider />
        
        {/* 按钮区域 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', p: 2 }}>
          <Button
            variant="outlined"
            onClick={activeStep === 0 ? () => navigate(-1) : handleBack}
            startIcon={<BackIcon />}
          >
            {activeStep === 0 ? '返回' : '上一步'}
          </Button>
          <Box>
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                color="primary"
                onClick={handleSubmit}
                disabled={loading || success || !isStepValid()}
                startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
              >
                {loading ? '提交中...' : '保存交易'}
              </Button>
            ) : (
              <Button
                variant="contained"
                color="primary"
                onClick={handleNext}
                disabled={!isStepValid()}
                endIcon={<NextIcon />}
              >
                下一步
              </Button>
            )}
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default NewTrade; 