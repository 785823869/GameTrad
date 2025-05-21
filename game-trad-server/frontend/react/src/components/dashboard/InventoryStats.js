import React from 'react';
import { 
  Typography, 
  Divider, 
  Grid, 
  Paper, 
  Box, 
  Button,
  LinearProgress,
  Tooltip
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  TrendingDown as LowStockIcon,
  TrendingUp as HighStockIcon,
  Warning as WarningIcon,
  ArrowForward as ArrowIcon
} from '@mui/icons-material';
import { Link } from 'react-router-dom';

/**
 * 库存统计组件
 * @param {Object} props
 * @param {number} props.itemCount - 物品总数
 * @param {number} props.totalQuantity - 库存总量
 * @param {number} props.lowStockCount - 低库存物品数量
 * @param {number} props.totalValue - 库存总价值
 * @param {number} props.zeroStockCount - 零库存物品数量
 */
const InventoryStats = ({ 
  itemCount = 0, 
  totalQuantity = 0, 
  lowStockCount = 0,
  totalValue = 0,
  zeroStockCount = 0
}) => {
  // 计算低库存比例
  const lowStockPercentage = itemCount > 0 ? (lowStockCount / itemCount) * 100 : 0;
  
  // 格式化金额
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };
  
  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          库存统计
        </Typography>
        <Button 
          component={Link} 
          to="/inventory" 
          size="small" 
          endIcon={<ArrowIcon />}
        >
          查看详情
        </Button>
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Paper 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'primary.lighter', 
              textAlign: 'center',
              border: '1px solid rgba(25, 118, 210, 0.1)',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center'
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
              <InventoryIcon color="primary" />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              {itemCount.toLocaleString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              物品总数
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={6}>
          <Paper 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'success.lighter', 
              textAlign: 'center',
              border: '1px solid rgba(46, 125, 50, 0.1)',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center'
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
              <HighStockIcon color="success" />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'success.main' }}>
              {totalQuantity.toLocaleString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              库存总量
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={6}>
          <Paper 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'warning.lighter', 
              textAlign: 'center',
              border: '1px solid rgba(237, 108, 2, 0.1)',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center'
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
              <LowStockIcon color="warning" />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
              {lowStockCount.toLocaleString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              低库存物品
            </Typography>
            
            <Tooltip title={`${lowStockPercentage.toFixed(1)}% 的物品库存不足`}>
              <LinearProgress 
                variant="determinate" 
                value={lowStockPercentage} 
                color="warning" 
                sx={{ mt: 1, height: 4, borderRadius: 2 }}
              />
            </Tooltip>
          </Paper>
        </Grid>
        
        <Grid item xs={6}>
          <Paper 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'error.lighter', 
              textAlign: 'center',
              border: '1px solid rgba(211, 47, 47, 0.1)',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center'
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
              <WarningIcon color="error" />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'error.main' }}>
              {zeroStockCount.toLocaleString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              零库存物品
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Paper 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'info.lighter', 
              textAlign: 'center',
              border: '1px solid rgba(2, 136, 209, 0.1)'
            }}
          >
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'info.main' }}>
              {formatCurrency(totalValue)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              库存总价值
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </>
  );
};

export default InventoryStats; 