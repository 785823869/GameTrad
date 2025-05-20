import React from 'react';
import { Box, Paper, Typography, Divider, Grid, LinearProgress } from '@mui/material';
import { Settings as SettingsIcon } from '@mui/icons-material';

/**
 * 系统信息组件
 * @param {Object} props
 * @param {Object} props.system - 系统信息数据
 */
const SystemInfo = ({ 
  system = {
    platform: 'N/A',
    uptime: 'N/A',
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0
  }
}) => {
  // 获取资源使用状态和颜色
  const getResourceStatus = (usage) => {
    if (usage < 50) return { color: '#2e7d32', level: 'normal' };
    if (usage < 80) return { color: '#ed6c02', level: 'warning' };
    return { color: '#d32f2f', level: 'critical' };
  };

  const cpuStatus = getResourceStatus(system.cpu_usage || 0);
  const memoryStatus = getResourceStatus(system.memory_usage || 0);
  const diskStatus = getResourceStatus(system.disk_usage || 0);

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
        <SettingsIcon sx={{ color: '#1976d2', mr: 1, fontSize: 24 }} />
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          系统信息
        </Typography>
      </Box>
      <Divider sx={{ mb: 2 }} />
      
      {/* 基本系统信息 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'rgba(25, 118, 210, 0.07)',
              border: '1px solid rgba(25, 118, 210, 0.1)'
            }}
          >
            <Typography variant="body2" color="text.secondary" gutterBottom>
              平台
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {system.platform || 'N/A'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: 2, 
              borderRadius: 2, 
              bgcolor: 'rgba(46, 125, 50, 0.07)',
              border: '1px solid rgba(46, 125, 50, 0.1)'
            }}
          >
            <Typography variant="body2" color="text.secondary" gutterBottom>
              运行时间
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {system.uptime || 'N/A'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      
      {/* 资源使用率 */}
      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
        资源使用率
      </Typography>
      
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2" color="text.secondary">
            CPU使用率
          </Typography>
          <Typography variant="body2" fontWeight="medium" color={cpuStatus.color}>
            {system.cpu_usage || 0}%
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={system.cpu_usage || 0} 
          sx={{ 
            height: 8,
            borderRadius: 4,
            bgcolor: 'rgba(0, 0, 0, 0.04)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: cpuStatus.color
            }
          }}
        />
      </Box>
      
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2" color="text.secondary">
            内存使用率
          </Typography>
          <Typography variant="body2" fontWeight="medium" color={memoryStatus.color}>
            {system.memory_usage || 0}%
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={system.memory_usage || 0} 
          sx={{ 
            height: 8,
            borderRadius: 4,
            bgcolor: 'rgba(0, 0, 0, 0.04)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: memoryStatus.color
            }
          }}
        />
      </Box>
      
      <Box sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2" color="text.secondary">
            磁盘使用率
          </Typography>
          <Typography variant="body2" fontWeight="medium" color={diskStatus.color}>
            {system.disk_usage || 0}%
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={system.disk_usage || 0} 
          sx={{ 
            height: 8,
            borderRadius: 4,
            bgcolor: 'rgba(0, 0, 0, 0.04)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: diskStatus.color
            }
          }}
        />
      </Box>
    </Paper>
  );
};

export default SystemInfo; 