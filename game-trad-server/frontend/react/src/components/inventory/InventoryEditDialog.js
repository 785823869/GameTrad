import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  InputAdornment,
  Typography,
  Box
} from '@mui/material';

/**
 * 库存编辑对话框组件
 * 
 * @param {Object} props - 组件属性
 * @param {boolean} props.open - 对话框是否打开
 * @param {function} props.onClose - 关闭对话框的回调函数
 * @param {Object} props.item - 当前编辑的物品（如果是编辑模式）
 * @param {function} props.onSave - 保存物品的回调函数
 */
const InventoryEditDialog = ({ open, onClose, item, onSave }) => {
  // 表单状态
  const [formData, setFormData] = useState({
    id: '',
    itemName: '',
    quantity: 0,
    avgPrice: 0,
    breakEvenPrice: 0,
    sellingPrice: 0
  });
  
  // 表单错误状态
  const [errors, setErrors] = useState({});
  
  // 当item变化时，更新表单数据
  useEffect(() => {
    if (item) {
      setFormData({
        id: item.id || '',
        itemName: item.itemName || '',
        quantity: item.quantity || 0,
        avgPrice: item.avgPrice || 0,
        breakEvenPrice: item.breakEvenPrice || 0,
        sellingPrice: item.sellingPrice || 0
      });
    } else {
      // 如果没有item，则重置表单
      setFormData({
        id: '',
        itemName: '',
        quantity: 0,
        avgPrice: 0,
        breakEvenPrice: 0,
        sellingPrice: 0
      });
    }
    
    // 重置错误
    setErrors({});
  }, [item, open]);
  
  // 处理输入变化
  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // 对于数字字段，转换为数字
    if (['quantity', 'avgPrice', 'breakEvenPrice', 'sellingPrice'].includes(name)) {
      setFormData({
        ...formData,
        [name]: parseFloat(value) || 0
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
    
    // 清除该字段的错误
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: null
      });
    }
  };
  
  // 验证表单
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.itemName.trim()) {
      newErrors.itemName = '物品名称不能为空';
    }
    
    if (formData.quantity < 0) {
      newErrors.quantity = '库存数量不能为负数';
    }
    
    if (formData.avgPrice < 0) {
      newErrors.avgPrice = '入库均价不能为负数';
    }
    
    if (formData.breakEvenPrice < 0) {
      newErrors.breakEvenPrice = '保本均价不能为负数';
    }
    
    if (formData.sellingPrice < 0) {
      newErrors.sellingPrice = '出库均价不能为负数';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // 处理保存
  const handleSave = () => {
    if (validateForm()) {
      onSave(formData);
    }
  };
  
  // 计算预估利润和利润率
  const profit = formData.sellingPrice - formData.breakEvenPrice;
  const profitRate = formData.breakEvenPrice > 0 
    ? ((formData.sellingPrice - formData.breakEvenPrice) / formData.breakEvenPrice) * 100 
    : 0;
  
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>
        {item && item.id ? '编辑物品' : '添加物品'}
      </DialogTitle>
      
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              name="itemName"
              label="物品名称"
              value={formData.itemName}
              onChange={handleChange}
              fullWidth
              error={!!errors.itemName}
              helperText={errors.itemName}
              required
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              name="quantity"
              label="库存数量"
              type="number"
              value={formData.quantity}
              onChange={handleChange}
              fullWidth
              error={!!errors.quantity}
              helperText={errors.quantity}
              InputProps={{
                inputProps: { min: 0 }
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              name="avgPrice"
              label="入库均价"
              type="number"
              value={formData.avgPrice}
              onChange={handleChange}
              fullWidth
              error={!!errors.avgPrice}
              helperText={errors.avgPrice}
              InputProps={{
                startAdornment: <InputAdornment position="start">¥</InputAdornment>,
                inputProps: { min: 0, step: 0.01 }
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              name="breakEvenPrice"
              label="保本均价"
              type="number"
              value={formData.breakEvenPrice}
              onChange={handleChange}
              fullWidth
              error={!!errors.breakEvenPrice}
              helperText={errors.breakEvenPrice}
              InputProps={{
                startAdornment: <InputAdornment position="start">¥</InputAdornment>,
                inputProps: { min: 0, step: 0.01 }
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              name="sellingPrice"
              label="出库均价"
              type="number"
              value={formData.sellingPrice}
              onChange={handleChange}
              fullWidth
              error={!!errors.sellingPrice}
              helperText={errors.sellingPrice}
              InputProps={{
                startAdornment: <InputAdornment position="start">¥</InputAdornment>,
                inputProps: { min: 0, step: 0.01 }
              }}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ 
              p: 2, 
              bgcolor: 'background.default', 
              borderRadius: 1,
              border: '1px solid',
              borderColor: 'divider'
            }}>
              <Typography variant="subtitle1" gutterBottom>
                预估数据
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    预估利润:
                  </Typography>
                  <Typography variant="body1" color={profit >= 0 ? 'success.main' : 'error.main'}>
                    ¥{profit.toFixed(2)}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    预估利润率:
                  </Typography>
                  <Typography variant="body1" color={profitRate >= 0 ? 'success.main' : 'error.main'}>
                    {profitRate.toFixed(2)}%
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    预估库存价值:
                  </Typography>
                  <Typography variant="body1">
                    ¥{(formData.quantity * formData.avgPrice).toFixed(2)}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSave} variant="contained" color="primary">
          保存
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default InventoryEditDialog; 