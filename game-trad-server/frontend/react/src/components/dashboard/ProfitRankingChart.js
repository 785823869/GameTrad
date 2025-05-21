import React, { useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Divider, 
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Stack
} from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// 注册Chart.js组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

/**
 * 利润率排行图表组件
 * @param {Object} props
 * @param {Array} props.data - 利润率排行数据
 * @param {boolean} props.loading - 加载状态
 * @param {number} props.limit - 显示数量限制
 * @param {function} props.onLimitChange - 限制变化处理函数
 */
const ProfitRankingChart = ({ 
  data = [], 
  loading = false,
  limit = 10,
  onLimitChange
}) => {
  // 数字格式化函数 - 与Inventory.js保持一致
  const formatNumber = (num) => {
    if (num === undefined || num === null || isNaN(num)) return '0.00';
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };

  // 调试输出
  useEffect(() => {
    if (data && data.length > 0) {
      console.log('利润率排行数据:', JSON.stringify(data, null, 2));
    }
  }, [data]);

  // 处理数据以适合图表显示
  const prepareChartData = () => {
    if (!data || data.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }
    
    // 确保数据中的profit_rate是数值类型并且格式正确
    const normalizedData = data.map(item => {
      // 处理profit_rate可能的各种情况
      let profitRate;
      if (typeof item.profit_rate === 'string') {
        // 移除可能的百分号并解析为浮点数
        profitRate = parseFloat(item.profit_rate.replace('%', ''));
      } else if (typeof item.profit_rate === 'number') {
        profitRate = item.profit_rate;
      } else {
        profitRate = 0;
      }

      // 不再进行特殊处理，直接使用API返回的利润率
      // 移除之前的100%修正逻辑，相信后端数据
      
      return {
        ...item,
        profit_rate: profitRate
      };
    }).filter(item => !isNaN(item.profit_rate)); // 过滤掉NaN值
    
    if (normalizedData.length === 0) {
      console.error('没有有效的利润率数据');
      return {
        labels: [],
        datasets: []
      };
    }

    // 按利润率排序数据
    const sortedData = [...normalizedData].sort((a, b) => b.profit_rate - a.profit_rate);
    console.log('排序后数据:', sortedData.map(item => ({
      item: item.item,
      profit_rate: item.profit_rate.toFixed(2) + '%'
    })));
    
    // 限制显示数量
    const limitedData = sortedData.slice(0, Math.min(limit, sortedData.length));
    
    // 准备图表数据
    const labels = limitedData.map(item => item.item);
    
    // 确保所有数据都是有效数字
    const profitRateData = limitedData.map(item => {
      const value = parseFloat(item.profit_rate);
      return isNaN(value) ? 0 : value;
    });
    
    // 根据利润率设置颜色
    const backgroundColors = limitedData.map(item => {
      const profitRate = item.profit_rate;
      if (profitRate >= 50) return 'rgba(76, 175, 80, 0.8)'; // 高利润 - 绿色
      if (profitRate >= 20) return 'rgba(255, 193, 7, 0.8)'; // 中等利润 - 黄色
      if (profitRate >= 0) return 'rgba(3, 169, 244, 0.8)';  // 低利润 - 蓝色
      return 'rgba(244, 67, 54, 0.8)'; // 亏损 - 红色
    });
    
    return {
      labels,
      datasets: [
        {
          label: '利润率 (%)',
          data: profitRateData,
          backgroundColor: backgroundColors,
          borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
          borderWidth: 1,
          barThickness: 20,
          minBarLength: 5
        }
      ]
    };
  };

  // 计算x轴范围
  const calculateAxisRange = () => {
    if (!data || data.length === 0) return { min: -20, max: 50 };
    
    let minValue = 0, maxValue = 50;
    
    try {
      // 确保获取格式化后的值进行计算
      const values = data.map(item => {
        if (typeof item.profit_rate === 'string') {
          return parseFloat(item.profit_rate.replace('%', ''));
        }
        return Number(item.profit_rate);
      }).filter(val => !isNaN(val));
      
      if (values.length > 0) {
        minValue = Math.min(...values);
        maxValue = Math.max(...values);
        
        // 为负值添加额外空间
        if (minValue < 0) {
          minValue = Math.floor(minValue * 1.2);
        }
        
        // 为正值添加额外空间
        if (maxValue > 0) {
          maxValue = Math.ceil(maxValue * 1.2);
        }
        
        // 确保最小范围
        if (maxValue < 50) maxValue = 50;
        if (minValue > -20 && minValue < 0) minValue = -20;
      }
    } catch (error) {
      console.error('计算轴范围错误:', error);
    }
    
    return { min: minValue, max: maxValue };
  };

  // 图表配置
  const axisRange = calculateAxisRange();
  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        left: 20,
        right: 20,
        top: 10,
        bottom: 10
      }
    },
    scales: {
      x: {
        beginAtZero: false, // 允许负值
        min: axisRange.min,
        max: axisRange.max,
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          callback: function(value) {
            return formatNumber(value) + '%';
          },
          // 确保显示0刻度线
          includeBounds: true
        }
      },
      y: {
        grid: {
          display: false
        },
        // 确保所有标签都显示
        afterFit: function(scaleInstance) {
          if (scaleInstance.width < 120) {
            scaleInstance.width = 120;
          }
        }
      }
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#2c3e50',
        bodyColor: '#2c3e50',
        borderColor: 'rgba(0, 0, 0, 0.1)',
        borderWidth: 1,
        padding: 12,
        bodyFont: {
          size: 12
        },
        titleFont: {
          size: 13,
          weight: 'bold'
        },
        callbacks: {
          label: function(context) {
            const itemName = context.label;
            const item = data.find(d => d.item === itemName);
            const profitRate = formatNumber(context.parsed.x);
            
            if (item) {
              return [
                `利润率: ${profitRate}%`,
                `销售总额: ¥${formatNumber(item.total_sales || 0)}`,
                `利润: ¥${formatNumber(item.profit || 0)}`
              ];
            } else {
              return [`利润率: ${profitRate}%`];
            }
          }
        }
      }
    }
  };

  // 自动调整图表高度
  const calculateChartHeight = () => {
    if (!data || data.length === 0) return 320;
    // 每个数据项至少需要50px高度，但确保最小高度为320px
    return Math.max(data.length * 50, 320);
  };

  // 准备图表数据
  const chartData = data && data.length > 0 ? prepareChartData() : null;
  const hasValidData = chartData && chartData.labels.length > 0;

  return (
    <Paper 
      sx={{ 
        p: 3, 
        mb: 3,
        boxShadow: '0 6px 12px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04)',
        border: '1px solid rgba(226, 232, 240, 0.7)',
        borderRadius: 3,
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          利润率排行榜
        </Typography>
        <FormControl size="small" sx={{ width: 100 }}>
          <InputLabel id="limit-select-label">显示数量</InputLabel>
          <Select
            labelId="limit-select-label"
            value={limit}
            label="显示数量"
            onChange={(e) => onLimitChange(e.target.value)}
          >
            <MenuItem value={5}>Top 5</MenuItem>
            <MenuItem value={10}>Top 10</MenuItem>
            <MenuItem value={15}>Top 15</MenuItem>
            <MenuItem value={20}>Top 20</MenuItem>
          </Select>
        </FormControl>
      </Box>
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: data && data.length > 0 ? 'flex-start' : 'center'
      }}>
        {loading ? (
          <CircularProgress />
        ) : data && data.length > 0 ? (
          <>
            {data.length === 1 && (
              <Alert severity="info" sx={{ width: '100%', mb: 2 }}>
                当前仅有一项数据，图表可能显示不平衡
              </Alert>
            )}
            <Box sx={{ width: '100%', height: calculateChartHeight() }}>
              {hasValidData ? (
                <Bar data={chartData} options={options} />
              ) : (
                <Alert severity="warning" sx={{ width: '100%', mt: 2 }}>
                  图表数据处理异常，请检查数据格式
                </Alert>
              )}
            </Box>
          </>
        ) : (
          <Stack spacing={2} alignItems="center" sx={{ py: 4 }}>
            <Typography variant="body1" color="text.secondary">
              暂无利润率数据
            </Typography>
            <Typography variant="caption" color="text.secondary">
              添加交易记录后将在此显示利润率排行
            </Typography>
          </Stack>
        )}
      </Box>
    </Paper>
  );
};

export default ProfitRankingChart; 