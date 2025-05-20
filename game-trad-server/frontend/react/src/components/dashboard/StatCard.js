import React from 'react';
import { Box, Card, CardContent, Typography } from '@mui/material';
import { ArrowUpward as ArrowUpIcon, ArrowDownward as ArrowDownIcon } from '@mui/icons-material';

/**
 * 统计卡片组件
 * @param {Object} props
 * @param {string} props.title - 卡片标题
 * @param {number} props.value - 显示值
 * @param {number} props.growth - 环比增长率
 * @param {React.ReactNode} props.icon - 图标组件
 * @param {string} props.iconBgColor - 图标背景色
 * @param {string} props.iconShadowColor - 图标阴影色
 * @param {function} props.formatter - 格式化函数
 */
const StatCard = ({ 
  title, 
  value, 
  growth = 0, 
  icon, 
  iconBgColor = '#2e7d32', 
  iconShadowColor = 'rgba(46, 125, 50, 0.3)',
  formatter = (val) => val
}) => {
  return (
    <Card 
      sx={{ 
        height: '100%', 
        background: 'linear-gradient(135deg, #ffffff, #f8fafc)',
        boxShadow: '0 8px 16px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.05)',
        border: '1px solid rgba(226, 232, 240, 0.8)',
        overflow: 'visible',
        position: 'relative',
        '&:hover': {
          boxShadow: '0 12px 20px rgba(0, 0, 0, 0.08), 0 3px 6px rgba(0, 0, 0, 0.05)',
        },
        transition: 'all 0.3s ease'
      }}
    >
      <Box 
        sx={{ 
          width: 60, 
          height: 60, 
          borderRadius: '16px', 
          position: 'absolute', 
          top: -15, 
          right: 30, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          backgroundColor: iconBgColor,
          boxShadow: `0 6px 10px ${iconShadowColor}`,
          transform: 'rotate(10deg)',
          zIndex: 1
        }}
      >
        {icon}
      </Box>
      <CardContent sx={{ position: 'relative', zIndex: 0, pt: 3, pb: 2.5 }}>
        <Typography variant="subtitle1" component="div" color="text.secondary" sx={{ mb: 1 }}>
          {title}
        </Typography>
        <Typography variant="h3" component="div" sx={{ mb: 1.5, fontWeight: 'bold' }}>
          {formatter(value)}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {growth > 0 ? (
            <ArrowUpIcon sx={{ color: 'success.main', fontSize: 18 }} />
          ) : (
            <ArrowDownIcon sx={{ color: 'error.main', fontSize: 18 }} />
          )}
          <Typography 
            variant="subtitle2" 
            color={growth > 0 ? 'success.main' : 'error.main'}
            sx={{ fontWeight: 'bold', mr: 1 }}
          >
            {growth >= 0 ? '+' : ''}{growth}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            月环比
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default StatCard; 