import React from 'react';
import { Typography, Divider, Grid, Paper } from '@mui/material';

/**
 * 库存统计组件
 * @param {Object} props
 * @param {number} props.itemCount - 物品总数
 * @param {number} props.totalQuantity - 库存总量
 * @param {number} props.lowStockCount - 低库存物品数量
 */
const InventoryStats = ({ 
  itemCount = 0, 
  totalQuantity = 0, 
  lowStockCount = 0 
}) => {
  return (
    <>
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
        库存统计
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Paper 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'primary.lighter', 
              textAlign: 'center',
              border: '1px solid rgba(25, 118, 210, 0.1)'
            }}
          >
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              {itemCount}
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
              border: '1px solid rgba(46, 125, 50, 0.1)'
            }}
          >
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'success.main' }}>
              {totalQuantity}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              库存总量
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'warning.lighter', 
              textAlign: 'center',
              border: '1px solid rgba(237, 108, 2, 0.1)'
            }}
          >
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
              {lowStockCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              低库存物品
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </>
  );
};

export default InventoryStats; 