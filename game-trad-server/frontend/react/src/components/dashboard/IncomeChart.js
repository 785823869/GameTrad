import React from 'react';
import { Box, Paper, Typography, Divider } from '@mui/material';
import { Bar } from 'react-chartjs-2';

/**
 * 收入情况图表组件
 * @param {Object} props
 * @param {Array} props.months - 月份标签
 * @param {Array} props.values - 收入数据
 * @param {number} props.total - 总收入
 * @param {function} props.formatter - 格式化函数
 */
const IncomeChart = ({ 
  months = [], 
  values = [], 
  total = 0, 
  formatter = value => value 
}) => {
  // 准备图表数据
  const chartData = {
    labels: months,
    datasets: [
      {
        label: '月收入',
        data: values,
        backgroundColor: 'rgba(53, 162, 235, 0.8)',
        borderRadius: 4,
      },
    ],
  };

  return (
    <Paper 
      sx={{ 
        p: 3, 
        boxShadow: '0 6px 12px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04)',
        border: '1px solid rgba(226, 232, 240, 0.7)',
        borderRadius: 3
      }}
    >
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
        收入情况
      </Typography>
      <Divider sx={{ mb: 3 }} />
      <Box sx={{ mb: 1, textAlign: 'right' }}>
        <Typography variant="subtitle2" color="text.secondary">
          总收入: <span style={{ fontWeight: 'bold', color: '#2e7d32' }}>${formatter(total)}</span>
        </Typography>
      </Box>
      <Box sx={{ height: 250 }}>
        <Bar 
          data={chartData} 
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false,
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
                },
                callbacks: {
                  label: function(context) {
                    return `收入: $${context.raw}`;
                  }
                }
              },
            },
            scales: {
              y: {
                beginAtZero: true,
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
                  }
                }
              },
            },
            animation: {
              duration: 800,
              easing: 'easeOutQuart'
            },
            barThickness: 18,
          }}
        />
      </Box>
    </Paper>
  );
};

export default IncomeChart; 