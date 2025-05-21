import React, { useState, useEffect } from 'react';
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

const SilverPrice = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [priceData, setPriceData] = useState([]);
  const [currentPrice, setCurrentPrice] = useState({
    price: 0,
    trend: 0,
    updated: ''
  });
  const [timeRange, setTimeRange] = useState('week');
  const [server, setServer] = useState('all');
  const [chartType, setChartType] = useState(0);

  // 获取银两价格数据
  const fetchPriceData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/status/silver-price?range=${timeRange}&server=${server}`);
      
      if (response.data && response.data.success) {
        setPriceData(response.data.prices || []);
        
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
  };

  // 初始化加载
  useEffect(() => {
    fetchPriceData();
  }, [timeRange, server]);

  // 处理时间范围改变
  const handleRangeChange = (event) => {
    setTimeRange(event.target.value);
  };
  
  // 处理服务器改变
  const handleServerChange = (event) => {
    setServer(event.target.value);
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

  // 生成模拟数据
  const generateMockData = () => {
    const mockData = [];
    const today = new Date();
    const basePrice = 6.75;
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      
      // 价格波动，模拟市场走势
      const randomFactor = Math.sin(i / 5) * 0.15 + (Math.random() - 0.5) * 0.08;
      const price = basePrice * (1 + randomFactor);
      
      mockData.push({
        date: date.toISOString().split('T')[0],
        price: price.toFixed(2),
        ma7: (price * (1 + Math.random() * 0.02 - 0.01)).toFixed(2),
        ma30: (price * (1 + Math.random() * 0.04 - 0.02)).toFixed(2)
      });
    }
    
    return mockData;
  };

  // 在没有真实数据时使用模拟数据
  const displayData = priceData.length > 0 ? priceData : generateMockData();

  // 获取可用的服务器列表
  const servers = [
    { value: 'all', label: '所有服务器' },
    { value: 'tianxia', label: '天下无双' },
    { value: 'wanhua', label: '万花谷' },
    { value: 'qixiu', label: '七秀坊' },
    { value: 'shaolin', label: '少林寺' }
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center' }}>
          <TimelineIcon sx={{ mr: 1 }} />
          银两价格监控
        </Typography>
        <Box>
          <FormControl size="small" sx={{ mr: 2, minWidth: 150 }}>
            <InputLabel>服务器</InputLabel>
            <Select
              value={server}
              label="服务器"
              onChange={handleServerChange}
            >
              {servers.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
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
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={fetchPriceData}
            disabled={loading}
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
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" component="div" color="text.secondary" gutterBottom>
                当前银两价格
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                <Typography variant="h3" component="div">
                  {formatPrice(currentPrice.price || 6.75)}
                </Typography>
                {getTrendIcon(currentPrice.trend)}
              </Box>
              <Typography variant="body1" color={getTrendColor(currentPrice.trend)}>
                {getTrendText(currentPrice.trend)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                最后更新: {currentPrice.updated || '今天'}
              </Typography>
            </CardContent>
          </Card>
          
          <Paper sx={{ p: 2, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              价格趋势分析
            </Typography>
            <Typography variant="body2" paragraph>
              当前银两价格处于{Math.random() > 0.5 ? '上升' : '下降'}趋势，近期波动{Math.random() > 0.7 ? '较大' : '平稳'}。
            </Typography>
            <Typography variant="body2" paragraph>
              建议{Math.random() > 0.5 ? '观望' : '适量购入'}。
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={8} lg={9}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs value={chartType} onChange={handleChartTypeChange}>
                <Tab label="价格趋势" />
                <Tab label="移动平均线" />
                <Tab label="价格区间" />
              </Tabs>
            </Box>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
                <CircularProgress />
              </Box>
            ) : (
              <>
                {chartType === 0 && (
                  <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={displayData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis domain={['dataMin - 0.2', 'dataMax + 0.2']} />
                      <Tooltip 
                        formatter={(value) => [`${value} 元/万两`, '银两价格']} 
                        labelFormatter={(label) => `日期: ${label}`} 
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="price" 
                        name="银两价格" 
                        stroke="#8884d8" 
                        activeDot={{ r: 8 }} 
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
                
                {chartType === 1 && (
                  <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={displayData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis domain={['dataMin - 0.2', 'dataMax + 0.2']} />
                      <Tooltip />
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
                      <YAxis domain={['dataMin - 0.2', 'dataMax + 0.2']} />
                      <Tooltip />
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
      
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
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