import React from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Divider, 
  Button,
  CircularProgress,
  ButtonGroup,
  Tooltip
} from '@mui/material';
import { Bar } from 'react-chartjs-2';

/**
 * 成交量趋势图组件
 * @param {Object} props
 * @param {Array} props.data - 成交量数据
 * @param {string} props.period - 当前选中周期
 * @param {boolean} props.loading - 加载状态
 * @param {function} props.onPeriodChange - 周期变化处理函数
 */
const VolumeChart = ({ 
  data = [], 
  period = 'day', 
  loading = false,
  onPeriodChange
}) => {
  // 处理数据以适合图表显示
  const prepareChartData = () => {
    if (!data || data.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }

    // 按日期分组
    const groupedByDate = {};
    data.forEach(item => {
      if (!groupedByDate[item.date]) {
        groupedByDate[item.date] = {};
      }
      groupedByDate[item.date][item.item] = item.quantity;
    });

    // 获取所有唯一的物品名称
    const allItems = [...new Set(data.map(item => item.item))];
    
    // 获取所有日期并按升序排序
    const dates = Object.keys(groupedByDate).sort();

    // 为每个物品创建数据集
    const datasets = allItems.map((item, index) => {
      // 随机但一致的颜色
      const hue = (index * 137) % 360;
      
      return {
        label: item,
        data: dates.map(date => groupedByDate[date][item] || 0),
        backgroundColor: `hsla(${hue}, 70%, 50%, 0.7)`,
        borderColor: `hsl(${hue}, 70%, 40%)`,
        borderWidth: 1
      };
    });

    return {
      labels: dates,
      datasets
    };
  };

  // 图表配置
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        stacked: true,
        grid: {
          display: false
        }
      },
      y: {
        stacked: true,
        beginAtZero: true
      }
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          boxWidth: 12,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#2c3e50',
        bodyColor: '#2c3e50',
        borderColor: 'rgba(0, 0, 0, 0.1)',
        borderWidth: 1,
        padding: 12,
        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
        bodyFont: {
          size: 12
        },
        titleFont: {
          size: 13,
          weight: 'bold'
        }
      }
    }
  };

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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          成交量趋势
        </Typography>
        <ButtonGroup size="small" variant="outlined">
          <Tooltip title="按日统计">
            <Button 
              onClick={() => onPeriodChange('day')}
              variant={period === 'day' ? 'contained' : 'outlined'}
            >
              日
            </Button>
          </Tooltip>
          <Tooltip title="按周统计">
            <Button 
              onClick={() => onPeriodChange('week')}
              variant={period === 'week' ? 'contained' : 'outlined'}
            >
              周
            </Button>
          </Tooltip>
          <Tooltip title="按月统计">
            <Button 
              onClick={() => onPeriodChange('month')}
              variant={period === 'month' ? 'contained' : 'outlined'}
            >
              月
            </Button>
          </Tooltip>
        </ButtonGroup>
      </Box>
      <Divider sx={{ mb: 3 }} />
      <Box sx={{ height: 380, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {loading ? (
          <CircularProgress />
        ) : data.length > 0 ? (
          <Bar data={prepareChartData()} options={options} />
        ) : (
          <Typography variant="body2" color="text.secondary">
            暂无成交量数据
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default VolumeChart; 