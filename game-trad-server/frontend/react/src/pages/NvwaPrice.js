import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  CircularProgress,
  Alert,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  useTheme,
  alpha,
  Tabs,
  Tab,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

const NvwaPrice = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [priceData, setPriceData] = useState([]);
  const [currentPrice, setCurrentPrice] = useState({
    price: 0,
    trend: 0,
    updated: ''
  });
  const [timeRange, setTimeRange] = useState('week');
  const [selectedPlatform, setSelectedPlatform] = useState('DD373');
  const [chartType, setChartType] = useState(0);

  // 允许的平台和颜色定义
  const allowedPlatforms = ['DD373', '7881', 'all'];
  const platformColors = {
    DD373: theme.palette.primary.main,
    '7881': theme.palette.secondary.main
  };

  // 获取女娲石价格数据
  const fetchPriceData = useCallback(async (platform, range) => {
    try {
      setLoading(true);
      setError(null);
      // 调用后端API获取数据
      const response = await axios.get(`/api/status/nvwa-price?range=${range}`);
      
      if (response.data && response.data.success) {
        // 合并所有平台数据
        const platforms = ['DD373', '7881'];
        const allDates = new Set();
        platforms.forEach(p => (response.data.dates[p] || []).forEach(d => allDates.add(d)));
        const sortedDates = Array.from(allDates).sort();
        
        // 为每个日期创建数据点
        const chartData = [];
        sortedDates.forEach(date => {
          const dataPoint = { date };
          
          // 为每个平台添加价格数据
          platforms.forEach(platform => {
            const dateIndex = response.data.dates[platform]?.indexOf(date);
            if (dateIndex !== -1 && dateIndex !== undefined) {
              dataPoint[platform] = response.data.prices[platform][dateIndex];
            }
          });
          
          chartData.push(dataPoint);
        });

        // 计算移动平均线
        const processedData = calculateMovingAverages(chartData);
        setPriceData(processedData);
        
        // 设置当前价格数据
        if (response.data.current) {
          setCurrentPrice({
            price: response.data.current.price,
            trend: response.data.current.trend,
            updated: response.data.current.updated
          });
        }
      } else {
        setError('获取女娲石价格数据失败');
        setPriceData([]);
      }
    } catch (err) {
      setError(`获取女娲石价格数据失败: ${err.message}`);
      setPriceData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // 计算移动平均线
  const calculateMovingAverages = (data) => {
    if (!data || data.length === 0) return data;

    const result = [...data];
    const platforms = ['DD373', '7881'];

    // 计算各平台的7日和30日移动平均线
    platforms.forEach(platform => {
      // 计算7日移动平均线
      for (let i = 0; i < result.length; i++) {
        let sum7 = 0;
        let count7 = 0;
        let sum30 = 0;
        let count30 = 0;

        // 为7日均线计算
        for (let j = Math.max(0, i - 6); j <= i; j++) {
          if (result[j] && result[j][platform] !== undefined) {
            sum7 += result[j][platform];
            count7++;
          }
        }

        // 为30日均线计算
        for (let j = Math.max(0, i - 29); j <= i; j++) {
          if (result[j] && result[j][platform] !== undefined) {
            sum30 += result[j][platform];
            count30++;
          }
        }

        if (count7 > 0) {
          result[i][`${platform}_ma7`] = parseFloat((sum7 / count7).toFixed(2));
        }
        
        if (count30 > 0) {
          result[i][`${platform}_ma30`] = parseFloat((sum30 / count30).toFixed(2));
        }
      }
    });
    
    return result;
  };

  // 初始化加载
  useEffect(() => {
    fetchPriceData(selectedPlatform, timeRange);
  }, [selectedPlatform, timeRange, fetchPriceData]);

  // 处理时间范围改变
  const handleRangeChange = (event) => {
    setTimeRange(event.target.value);
  };
  
  // 处理平台选择改变
  const handlePlatformChange = (event) => {
    setSelectedPlatform(event.target.value);
  };
  
  // 处理图表类型改变
  const handleChartTypeChange = (event, newValue) => {
    setChartType(newValue);
  };

  // 格式化价格
  const formatPrice = (price) => {
    return `¥ ${parseFloat(price).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };
  
  // 获取趋势颜色
  const getTrendColor = (trend) => {
    if (trend > 0) return theme.palette.success.main;
    if (trend < 0) return theme.palette.error.main;
    return theme.palette.text.secondary;
  };
  
  // 获取趋势图标
  const getTrendIcon = (trend) => {
    if (trend > 0) return <TrendingUpIcon color="success" />;
    if (trend < 0) return <TrendingDownIcon color="error" />;
    return null;
  };
  
  // 获取趋势文字
  const getTrendText = (trend) => {
    if (trend > 0) return `+${trend.toFixed(2)}%`;
    if (trend < 0) return `${trend.toFixed(2)}%`;
    return '0.00%';
  };

  // 自定义图表tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Paper
          elevation={3}
          sx={{
            p: 1.5,
            backgroundColor: 'rgba(255, 255, 255, 0.96)',
            border: '1px solid rgba(0, 0, 0, 0.05)',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
          }}
        >
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
            {label}
          </Typography>
          {payload.map((entry, index) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
              <Box
                component="span"
                sx={{
                  display: 'inline-block',
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: entry.color,
                  mr: 1
                }}
              />
              <Typography variant="body2" sx={{ mr: 1 }}>
                {entry.name}:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                ¥{entry.value.toFixed(2)}
              </Typography>
            </Box>
          ))}
        </Paper>
      );
    }
    return null;
  };

  // 获取两个平台之间的价格差异
  const getPriceDifference = () => {
    if (priceData.length === 0) return { diff: 0, percentage: 0 };
    
    const latestData = priceData[priceData.length - 1];
    if (!latestData) return { diff: 0, percentage: 0 };
    
    const price1 = latestData['DD373'] || 0;
    const price2 = latestData['7881'] || 0;
    
    if (price1 === 0 || price2 === 0) return { diff: 0, percentage: 0 };
    
    const diff = price1 - price2;
    const percentage = price2 !== 0 ? (Math.abs(diff) / price2) * 100 : 0;
    
    return {
      diff: diff.toFixed(2),
      percentage: percentage.toFixed(2),
      platform1: 'DD373',
      platform2: '7881'
    };
  };

  // 计算价格波动性
  const calculateVolatility = () => {
    if (priceData.length < 2) return 0;
    
    const platform = selectedPlatform === 'all' ? 'DD373' : selectedPlatform;
    
    // 获取选定平台的价格数据
    const prices = priceData
      .filter(data => data[platform] !== undefined)
      .map(data => data[platform]);
    
    if (prices.length < 2) return 0;
    
    // 计算价格变化百分比
    const changes = [];
    for (let i = 1; i < prices.length; i++) {
      const change = (prices[i] - prices[i-1]) / prices[i-1] * 100;
      changes.push(change);
    }
    
    // 计算标准差作为波动性指标
    const mean = changes.reduce((a, b) => a + b, 0) / changes.length;
    const variance = changes.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / changes.length;
    return Math.sqrt(variance).toFixed(2);
  };

  // 获取价格趋势描述
  const getPriceTrendDescription = () => {
    if (currentPrice.trend > 1) return '上涨趋势';
    if (currentPrice.trend < -1) return '下跌趋势';
    return '价格稳定';
  };

  const volatility = calculateVolatility();
  const priceDifference = getPriceDifference();

  // 根据波动性获取建议
  const getTradingSuggestion = () => {
    const currentTrend = currentPrice.trend;
    
    if (volatility > 5) {
      return '价格波动较大，建议谨慎交易';
    } else if (currentTrend > 2) {
      return '价格上涨趋势明显，可考虑卖出获利';
    } else if (currentTrend < -2) {
      return '价格下跌趋势明显，可考虑择机买入';
    } else {
      return '价格相对稳定，可根据需求正常交易';
    }
  };

  // 计算需要显示的平台线
  const getLinesToShow = () => {
    if (selectedPlatform === 'all') {
      return ['DD373', '7881'];
    } else {
      return [selectedPlatform];
    }
  };

  const linesToShow = getLinesToShow();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', fontWeight: 'bold', color: theme.palette.primary.main }}>
          <TimelineIcon sx={{ mr: 1 }} />
          女娲石价格监控
        </Typography>
        <Box>
          <FormControl size="small" sx={{ mr: 2, minWidth: 120 }}>
            <InputLabel>时间范围</InputLabel>
            <Select
              value={timeRange}
              label="时间范围"
              onChange={handleRangeChange}
            >
              <MenuItem value="day">最近24小时</MenuItem>
              <MenuItem value="week">最近一周</MenuItem>
              <MenuItem value="month">最近一个月</MenuItem>
              <MenuItem value="year">最近一年</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ mr: 2, minWidth: 120 }}>
            <InputLabel>平台</InputLabel>
            <Select
              value={selectedPlatform}
              label="平台"
              onChange={handlePlatformChange}
              disabled={loading}
            >
              {allowedPlatforms.map(platform => (
                <MenuItem key={platform} value={platform}>
                  {platform === 'all' ? '全部' : platform}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={() => fetchPriceData(selectedPlatform, timeRange)}
            disabled={loading}
            sx={{ 
              boxShadow: 2,
              '&:hover': { boxShadow: 3 }
            }}
          >
            刷新
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4} lg={3}>
          <Card sx={{ boxShadow: 2, borderRadius: 2 }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" component="div" color="text.secondary" gutterBottom>
                当前女娲石价格
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
                  {formatPrice(currentPrice.price || 3.25)}
                </Typography>
                {getTrendIcon(currentPrice.trend)}
              </Box>
              <Typography variant="body1" sx={{ color: getTrendColor(currentPrice.trend), fontWeight: 'bold' }}>
                {getTrendText(currentPrice.trend)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                最后更新: {currentPrice.updated || '今天'}
              </Typography>
            </CardContent>
          </Card>
          
          <Card sx={{ mt: 3, boxShadow: 2, borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" component="div" sx={{ mb: 2, fontWeight: 'bold' }}>
                市场分析
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  价格趋势
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {getPriceTrendDescription()}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  价格波动率
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {volatility}%
                </Typography>
              </Box>
              {priceDifference.diff !== '0.00' && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    平台价差 (DD373 vs 7881)
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                    ¥{priceDifference.diff} ({priceDifference.percentage}%)
                  </Typography>
                </Box>
              )}
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" color="text.primary" sx={{ fontWeight: 'bold' }}>
                  交易建议:
                </Typography>
                <Typography variant="body2" color="text.primary" sx={{ fontWeight: 'medium', mt: 1 }}>
                  {getTradingSuggestion()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8} lg={9}>
          <Paper 
            sx={{ 
              p: 3, 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column', 
              borderRadius: 2, 
              boxShadow: 2 
            }}
          >
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs value={chartType} onChange={handleChartTypeChange}>
                <Tab label="价格趋势" />
                <Tab label="移动平均线" />
                <Tab label="价格区间" />
              </Tabs>
            </Box>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexGrow: 1 }}>
                <CircularProgress />
              </Box>
            ) : priceData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                {chartType === 0 && (
                  <LineChart data={priceData} margin={{ top: 30, right: 30, left: 10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                      tickLine={{ stroke: theme.palette.divider }}
                      axisLine={{ stroke: theme.palette.divider }}
                      padding={{ left: 24, right: 24 }}
                    />
                    <YAxis 
                      domain={['auto', 'auto']}
                      tick={{ fontSize: 12, fill: theme.palette.text.secondary }} 
                      tickLine={{ stroke: theme.palette.divider }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickFormatter={(value) => `¥${value.toFixed(2)}`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {linesToShow.map((platform, index) => (
                      <Line 
                        key={platform}
                        type="monotone" 
                        dataKey={platform} 
                        name={platform}
                        dot={{ r: 4 }}
                        activeDot={{ r: 7 }}
                        strokeWidth={2}
                        isAnimationActive={true}
                        stroke={platformColors[platform]}
                      />
                    ))}
                  </LineChart>
                )}
                
                {chartType === 1 && (
                  <LineChart data={priceData} margin={{ top: 30, right: 30, left: 10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
                    <XAxis dataKey="date" />
                    <YAxis 
                      domain={['auto', 'auto']}
                      tickFormatter={(value) => `¥${value.toFixed(2)}`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {selectedPlatform !== 'all' ? (
                      <>
                        <Line 
                          type="monotone" 
                          dataKey={selectedPlatform} 
                          name={`${selectedPlatform}实时价格`} 
                          stroke={theme.palette.primary.main} 
                          dot={false}
                          strokeWidth={2}
                        />
                        <Line 
                          type="monotone" 
                          dataKey={`${selectedPlatform}_ma7`} 
                          name="7日均价" 
                          stroke={theme.palette.secondary.main} 
                          dot={false}
                          strokeWidth={1.5}
                        />
                        <Line 
                          type="monotone" 
                          dataKey={`${selectedPlatform}_ma30`} 
                          name="30日均价" 
                          stroke="#ff7300" 
                          dot={false}
                          strokeWidth={1.5}
                        />
                      </>
                    ) : (
                      linesToShow.map((platform) => (
                        <Line 
                          key={platform}
                          type="monotone" 
                          dataKey={platform} 
                          name={`${platform}价格`} 
                          stroke={platformColors[platform]} 
                          dot={false}
                          strokeWidth={2}
                        />
                      ))
                    )}
                  </LineChart>
                )}
                
                {chartType === 2 && (
                  <AreaChart data={priceData} margin={{ top: 30, right: 30, left: 10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
                    <XAxis dataKey="date" />
                    <YAxis 
                      domain={['auto', 'auto']}
                      tickFormatter={(value) => `¥${value.toFixed(2)}`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {selectedPlatform === 'all' ? (
                      linesToShow.map((platform, index) => (
                        <Area 
                          key={platform}
                          type="monotone" 
                          dataKey={platform} 
                          name={`${platform}价格`} 
                          stroke={platformColors[platform]} 
                          fill={platformColors[platform]} 
                          fillOpacity={0.3} 
                        />
                      ))
                    ) : (
                      <Area 
                        type="monotone" 
                        dataKey={selectedPlatform} 
                        name={`${selectedPlatform}价格`} 
                        stroke={platformColors[selectedPlatform]} 
                        fill={platformColors[selectedPlatform]} 
                        fillOpacity={0.3} 
                      />
                    )}
                  </AreaChart>
                )}
              </ResponsiveContainer>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexGrow: 1 }}>
                <Typography variant="body1" color="text.secondary">
                  暂无数据
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      <Paper sx={{ p: 3, mt: 3, borderRadius: 2, boxShadow: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
          价格分析
        </Typography>
        <Typography variant="body1" paragraph>
          女娲石是游戏中的重要货币资源，价格波动受多种因素影响，如游戏更新、活动、玩家交易行为等。
        </Typography>
        <Typography variant="body1" paragraph>
          过去{timeRange === 'day' ? '24小时' : timeRange === 'week' ? '一周' : timeRange === 'month' ? '一个月' : '一年'}内，
          价格总体{currentPrice.trend > 1 ? '呈上升趋势' : currentPrice.trend < -1 ? '呈下降趋势' : '保持稳定'}，
          波动率为{volatility}%，
          {parseFloat(volatility) > 5 
            ? '波动较大，建议合理规划购入时机，避开价格高峰期。' 
            : '波动较小，可以根据需求进行交易。'}
        </Typography>
      </Paper>
    </Container>
  );
};

export default NvwaPrice; 