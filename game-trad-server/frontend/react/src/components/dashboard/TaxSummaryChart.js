import React from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Divider, 
  CircularProgress, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Grid,
  Stack
} from '@mui/material';
import { Pie, Doughnut } from 'react-chartjs-2';

/**
 * 交易税统计图表组件
 * @param {Object} props
 * @param {Array} props.data - 交易税统计数据
 * @param {boolean} props.loading - 加载状态
 * @param {number} props.taxRate - 交易税率(%)
 * @param {function} props.onTaxRateChange - 税率变化处理函数
 * @param {string} props.chartType - 图表类型 'pie' 或 'doughnut'
 * @param {function} props.onChartTypeChange - 图表类型变化处理函数
 */
const TaxSummaryChart = ({ 
  data = [], 
  loading = false,
  taxRate = 5,
  onTaxRateChange,
  chartType = 'doughnut',
  onChartTypeChange
}) => {
  // 处理数据以适合图表显示
  const prepareChartData = () => {
    if (!data || data.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }

    // 获取前8项，其余归为"其他"
    let topItems = [...data].sort((a, b) => b.tax_amount - a.tax_amount).slice(0, 8);
    let otherItems = data.length > 8 ? data.slice(8) : [];
    
    // 如果有"其他"项，汇总它们
    let chartItems = [...topItems];
    if (otherItems.length > 0) {
      const otherTaxAmount = otherItems.reduce((sum, item) => sum + item.tax_amount, 0);
      chartItems.push({
        item: '其他',
        tax_amount: otherTaxAmount
      });
    }
    
    // 准备图表数据
    const labels = chartItems.map(item => item.item);
    const taxData = chartItems.map(item => parseFloat(item.tax_amount).toFixed(2));
    
    // 生成颜色
    const backgroundColors = chartItems.map((_, index) => {
      // 使用HSL颜色模型生成不同的颜色
      const hue = (index * 137) % 360; // 黄金比例旋转以获得良好的颜色分布
      return `hsla(${hue}, 70%, 60%, 0.7)`;
    });
    
    return {
      labels,
      datasets: [
        {
          data: taxData,
          backgroundColor: backgroundColors,
          borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
          borderWidth: 1
        }
      ]
    };
  };

  // 计算总交易税
  const calculateTotalTax = () => {
    if (!data || data.length === 0) return 0;
    return data.reduce((sum, item) => sum + item.tax_amount, 0);
  };

  // 图表配置
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          boxWidth: 10,
          font: {
            size: 10
          }
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
        },
        callbacks: {
          label: function(context) {
            const value = parseFloat(context.raw).toFixed(2);
            const percentage = ((value / calculateTotalTax()) * 100).toFixed(1);
            return `${context.label}: ¥${value} (${percentage}%)`;
          }
        }
      }
    }
  };

  // 使用的图表组件
  const ChartComponent = chartType === 'pie' ? Pie : Doughnut;

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
          交易税统计
        </Typography>
        <Stack direction="row" spacing={1}>
          <FormControl size="small" sx={{ minWidth: 80 }}>
            <InputLabel id="tax-rate-label">税率</InputLabel>
            <Select
              labelId="tax-rate-label"
              value={taxRate}
              label="税率"
              onChange={(e) => onTaxRateChange(e.target.value)}
            >
              <MenuItem value={3}>3%</MenuItem>
              <MenuItem value={5}>5%</MenuItem>
              <MenuItem value={10}>10%</MenuItem>
              <MenuItem value={15}>15%</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 90 }}>
            <InputLabel id="chart-type-label">图表</InputLabel>
            <Select
              labelId="chart-type-label"
              value={chartType}
              label="图表"
              onChange={(e) => onChartTypeChange(e.target.value)}
            >
              <MenuItem value={'pie'}>饼图</MenuItem>
              <MenuItem value={'doughnut'}>环形图</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </Box>
      <Divider sx={{ mb: 2 }} />

      <Grid container spacing={1} sx={{ flexGrow: 1 }}>
        <Grid item xs={12}>
          <Box sx={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {loading ? (
              <CircularProgress />
            ) : data.length > 0 ? (
              <ChartComponent data={prepareChartData()} options={options} />
            ) : (
              <Typography variant="body2" color="text.secondary">
                暂无交易税数据
              </Typography>
            )}
          </Box>
        </Grid>
        <Grid item xs={12}>
          <Box sx={{ textAlign: 'center', mt: 1 }}>
            <Typography variant="body1" color="text.primary" sx={{ fontWeight: 'medium' }}>
              总交易税: <span style={{ color: '#1976d2' }}>
                ¥{calculateTotalTax().toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              基于税率 {taxRate}% 计算
            </Typography>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default TaxSummaryChart; 