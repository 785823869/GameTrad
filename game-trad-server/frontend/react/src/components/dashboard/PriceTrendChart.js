import React from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Divider, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Button,
  CircularProgress 
} from '@mui/material';
import { Line } from 'react-chartjs-2';

/**
 * 价格趋势图组件
 * @param {Object} props
 * @param {Array} props.items - 物品列表
 * @param {string} props.selectedItem - 当前选中物品
 * @param {string} props.period - 当前选中周期
 * @param {Array} props.trendData - 价格趋势数据
 * @param {boolean} props.loading - 加载状态
 * @param {function} props.onItemChange - 物品变化处理函数
 * @param {function} props.onPeriodChange - 周期变化处理函数
 */
const PriceTrendChart = ({ 
  items = [], 
  selectedItem = '', 
  period = 'day', 
  trendData = [], 
  loading = false,
  onItemChange,
  onPeriodChange
}) => {
  // 准备图表数据
  const prepareChartData = () => {
    // 如果没有数据，返回基本结构
    if (!trendData || trendData.length === 0) {
      return {
        labels: [],
        datasets: [{
          label: '价格趋势',
          data: [],
          borderColor: 'rgba(53, 162, 235, 1)',
          backgroundColor: 'rgba(53, 162, 235, 0.2)',
          tension: 0.4,
          fill: true
        }]
      };
    }
    
    // 提取日期标签和价格
    const labels = trendData.map(item => item.dateLabel || item.date.split('T')[0]);
    const prices = trendData.map(item => item.price);
    
    return {
      labels,
      datasets: [{
        label: `${selectedItem} 价格趋势`,
        data: prices,
        borderColor: 'rgba(53, 162, 235, 1)',
        backgroundColor: 'rgba(53, 162, 235, 0.2)',
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: 'rgba(53, 162, 235, 1)',
      }]
    };
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
          物品价格趋势
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120, mr: 1 }}>
            <InputLabel id="item-select-label">选择物品</InputLabel>
            <Select
              labelId="item-select-label"
              value={selectedItem}
              onChange={onItemChange}
              label="选择物品"
            >
              {items.map((item) => (
                <MenuItem key={item} value={item}>{item}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Box sx={{ 
            display: 'flex', 
            borderRadius: 2,
            overflow: 'hidden',
            boxShadow: '0 2px 6px rgba(0, 0, 0, 0.08)',
          }}>
            <Button 
              variant={period === 'day' ? 'contained' : 'text'} 
              onClick={() => onPeriodChange('day')}
              sx={{ 
                minWidth: 40, 
                py: 0.5, 
                borderRadius: 0,
                background: period === 'day' ? 
                  'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)' : 'transparent',
              }}
            >
              日
            </Button>
            <Button 
              variant={period === 'week' ? 'contained' : 'text'} 
              onClick={() => onPeriodChange('week')}
              sx={{ 
                minWidth: 40, 
                py: 0.5, 
                borderRadius: 0,
                background: period === 'week' ? 
                  'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)' : 'transparent',
              }}
            >
              周
            </Button>
            <Button 
              variant={period === 'month' ? 'contained' : 'text'} 
              onClick={() => onPeriodChange('month')}
              sx={{ 
                minWidth: 40, 
                py: 0.5, 
                borderRadius: 0,
                background: period === 'month' ? 
                  'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)' : 'transparent',
              }}
            >
              月
            </Button>
          </Box>
        </Box>
      </Box>
      <Divider sx={{ mb: 3 }} />
      <Box sx={{ height: 320, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {loading ? (
          <CircularProgress />
        ) : trendData.length > 0 ? (
          <Line 
            data={prepareChartData()} 
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: true,
                  position: 'top',
                  labels: {
                    usePointStyle: true,
                    boxWidth: 6,
                    font: {
                      size: 12
                    }
                  }
                },
                tooltip: {
                  mode: 'index',
                  intersect: false,
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
                  },
                  callbacks: {
                    label: function(context) {
                      return `价格: $${context.raw}`;
                    }
                  }
                },
              },
              scales: {
                y: {
                  beginAtZero: false,
                  grid: {
                    drawBorder: false,
                    color: 'rgba(0, 0, 0, 0.04)',
                  },
                  ticks: {
                    font: {
                      size: 11
                    }
                  }
                },
                x: {
                  grid: {
                    display: false,
                  },
                  ticks: {
                    font: {
                      size: 11
                    },
                    maxRotation: 45,
                    minRotation: 45
                  }
                },
              },
              animation: {
                duration: 800,
                easing: 'easeOutQuart'
              },
              elements: {
                line: {
                  tension: 0.4
                },
                point: {
                  radius: 3,
                  hoverRadius: 6,
                  borderWidth: 2,
                  hoverBorderWidth: 2,
                  hoverBorderColor: 'white',
                }
              }
            }}
          />
        ) : (
          <Typography color="text.secondary">
            {selectedItem ? `没有找到 ${selectedItem} 的价格数据` : '请选择一个物品查看价格趋势'}
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default PriceTrendChart; 