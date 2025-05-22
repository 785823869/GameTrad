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
  Tabs,
  Tab
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
import { useTheme } from '@mui/material/styles';

const SilverPrice = () => {
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

  const allowedPlatforms = ['DD373', '7881', 'all'];
  const platformColors = {
    DD373: '#8884d8',
    '7881': '#82ca9d'
  };

  const fetchPriceData = useCallback(async (platform, range) => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/status/silver-price?range=${range}`);
      if (response.data && response.data.success) {
        let chartData = [];
        // 合并所有平台数据
        const platforms = ['DD373', '7881'];
        const allDates = new Set();
        platforms.forEach(p => (response.data.dates[p] || []).forEach(d => allDates.add(d)));
        const sortedDates = Array.from(allDates).sort();
        sortedDates.forEach(date => {
          const point = { date };
          platforms.forEach(p => {
            const idx = response.data.dates[p]?.indexOf(date);
            if (idx !== undefined && idx !== -1) point[p] = response.data.prices[p][idx];
          });
          chartData.push(point);
        });
        setPriceData(chartData);
        // 设置当前价格数据
        if (response.data.current) {
          setCurrentPrice({
            price: response.data.current.price,
            trend: response.data.current.trend,
            updated: response.data.current.updated
          });
        }
        setError(null);
      } else {
        setError('获取银两价格数据失败');
        setPriceData([]);
      }
    } catch (err) {
      setError(`获取银两价格数据失败: ${err.message}`);
      setPriceData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPriceData(selectedPlatform, timeRange);
  }, [selectedPlatform, timeRange, fetchPriceData]);

  // 处理时间范围改变
  const handleRangeChange = (event) => {
    setTimeRange(event.target.value);
  };
  
  // 处理平台改变
  const handlePlatformChange = (event) => {
    setSelectedPlatform(event.target.value);
  };
  
  // 处理图表类型改变
  const handleChartTypeChange = (event, newValue) => {
    setChartType(newValue);
  };

  // 格式化价格 - 调整为显示银两单位
  const formatPrice = (price) => {
    return `¥ ${parseFloat(price).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };
  
  // 获取趋势颜色
  const getTrendColor = (trend) => {
    if (trend > 0) return 'success.main';
    if (trend < 0) return 'error.main';
    return 'text.secondary';
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

  // 生成符合银两价格范围的模拟数据 (0.2-1元/万两)
  const generateMockData = () => {
    const mockData = [];
    const today = new Date();
    const basePrice = 0.38; // 典型银两价格约0.38元/万两
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      
      // 价格波动，模拟市场走势
      const randomFactor = Math.sin(i / 5) * 0.15 + (Math.random() - 0.5) * 0.08;
      const price = basePrice * (1 + randomFactor);
      
      mockData.push({
        date: date.toISOString().split('T')[0],
        price: parseFloat(price.toFixed(4)),
        ma7: parseFloat((price * (1 + Math.random() * 0.02 - 0.01)).toFixed(4)),
        ma30: parseFloat((price * (1 + Math.random() * 0.04 - 0.02)).toFixed(4))
      });
    }
    
    return mockData;
  };

  // 在没有真实数据时使用模拟数据
  let displayData = priceData.length > 0 ? priceData : generateMockData();
  let linesToShow = [];
  if (selectedPlatform === 'all') {
    linesToShow = ['DD373', '7881'];
  } else {
    linesToShow = [selectedPlatform];
  }

  // 获取价格趋势描述
  const getPriceTrendDescription = () => {
    if (currentPrice.trend > 1) return '上涨趋势';
    if (currentPrice.trend < -1) return '下跌趋势';
    return '价格稳定';
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
  
  // 根据波动性获取建议
  const getTradingSuggestion = () => {
    const volatility = calculateVolatility();
    if (parseFloat(volatility) > 5) {
      return '价格波动较大，建议谨慎交易';
    } else if (currentPrice.trend > 2) {
      return '价格上涨趋势明显，可考虑卖出获利';
    } else if (currentPrice.trend < -2) {
      return '价格下跌趋势明显，可考虑择机买入';
    } else {
      return '价格相对稳定，可根据需求正常交易';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', fontWeight: 'bold', color: theme?.palette?.primary?.main }}>
          <TimelineIcon sx={{ mr: 1 }} />
          银两价格监控
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
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
            >
              {allowedPlatforms.map(option => (
                <MenuItem key={option} value={option}>
                  {option === 'all' ? '全部' : option}
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
                当前银两价格
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
                  {formatPrice(currentPrice.price || 0.38)}
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
                  {calculateVolatility()}%
                </Typography>
              </Box>
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
          <Paper sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 2, boxShadow: 2 }}>
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
            ) : (
              <>
                {chartType === 0 && (
                  <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={displayData} margin={{ top: 30, right: 30, left: 10, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis domain={['dataMin - 0.05', 'dataMax + 0.05']} tickFormatter={v => v.toFixed(2)} />
                      <Tooltip
                        formatter={(value, name) => [`${value} 元/万两`, name === 'DD373' ? 'DD373' : name === '7881' ? '7881' : name]}
                        labelFormatter={label => `日期: ${label}`}
                      />
                      <Legend />
                      {linesToShow.map(platform => (
                        <Line
                          key={platform}
                          type="monotone"
                          dataKey={platform}
                          name={platform}
                          stroke={platformColors[platform]}
                          dot={{ r: 4 }}
                          activeDot={{ r: 7 }}
                          strokeWidth={2}
                          isAnimationActive={true}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                )}
                
                {chartType === 1 && (
                  <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={displayData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis domain={['dataMin - 0.05', 'dataMax + 0.05']} />
                      <Tooltip 
                        formatter={(value) => [`${value} 元/万两`, `银两价格`]}
                        labelFormatter={(label) => `日期: ${label}`}
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="price" 
                        name="实时价格" 
                        stroke="#8884d8" 
                        dot={false} 
                      />
                      <Line 
                        type="monotone" 
                        dataKey="ma7" 
                        name="7日均价" 
                        stroke="#82ca9d" 
                        dot={false} 
                      />
                      <Line 
                        type="monotone" 
                        dataKey="ma30" 
                        name="30日均价" 
                        stroke="#ff7300" 
                        dot={false} 
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
                
                {chartType === 2 && (
                  <ResponsiveContainer width="100%" height={350}>
                    <AreaChart data={displayData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis domain={['dataMin - 0.05', 'dataMax + 0.05']} />
                      <Tooltip 
                        formatter={(value) => [`${value} 元/万两`, `银两价格`]}
                        labelFormatter={(label) => `日期: ${label}`}
                      />
                      <Legend />
                      <Area 
                        type="monotone" 
                        dataKey="price" 
                        name="银两价格" 
                        stroke="#8884d8" 
                        fill="#8884d8" 
                        fillOpacity={0.3} 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      <Paper sx={{ p: 3, mt: 3, borderRadius: 2, boxShadow: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
          银两价格说明
        </Typography>
        <Typography variant="body1" paragraph>
          银两是游戏中的主要货币，价格受多种因素影响，包括游戏更新、活动、玩家交易行为等。
        </Typography>
        <Typography variant="body1">
          价格数据每小时更新一次，移动平均线可帮助分析长期价格趋势，为交易决策提供参考。不同服务器的价格可能存在差异。
        </Typography>
      </Paper>
    </Container>
  );
};

export default SilverPrice; 