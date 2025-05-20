import React from 'react';
import { Box, Paper, Typography, Divider, Grid } from '@mui/material';
import { TrendingUp as TrendingUpIcon } from '@mui/icons-material';

/**
 * 行情概览组件
 * @param {Object} props
 * @param {string} props.marketStatus - 市场状态
 * @param {string} props.silverPrice - 银两行情
 * @param {string} props.nvwaPrice - 女娲石行情
 */
const MarketOverview = ({ 
  marketStatus = '加载中...', 
  silverPrice = '加载中...', 
  nvwaPrice = '加载中...' 
}) => {
  return (
    <Paper 
      sx={{ 
        p: 3, 
        mb: 3,
        boxShadow: '0 6px 12px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04)',
        border: '1px solid rgba(226, 232, 240, 0.7)',
        borderRadius: 3
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <TrendingUpIcon sx={{ color: '#ed6c02', mr: 1, fontSize: 24 }} />
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          行情概览
        </Typography>
      </Box>
      <Divider sx={{ mb: 3 }} />
      <Box sx={{ mb: 3 }}>
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ 
            mb: 1.5, 
            fontWeight: 'bold', 
            color: '#2c3e50',
            fontSize: '1.1rem',
            textAlign: 'center',
            p: 1.5,
            borderRadius: 2,
            bgcolor: 'rgba(0, 0, 0, 0.03)'
          }}
        >
          {marketStatus}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mb: 2 }}>
          交易日期：{new Date().toLocaleDateString()}
        </Typography>
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'rgba(2, 136, 209, 0.07)',
              border: '1px solid rgba(2, 136, 209, 0.1)'
            }}
          >
            <Typography variant="body2" color="text.secondary" gutterBottom>
              银两行情
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#0288d1' }}>
              {silverPrice}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'rgba(237, 108, 2, 0.07)',
              border: '1px solid rgba(237, 108, 2, 0.1)'
            }}
          >
            <Typography variant="body2" color="text.secondary" gutterBottom>
              女娲石行情
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#ed6c02' }}>
              {nvwaPrice}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default MarketOverview; 