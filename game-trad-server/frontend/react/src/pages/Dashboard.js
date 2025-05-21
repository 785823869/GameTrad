import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Container, 
  Grid, 
  Paper,
  Typography,
  Box,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  Button
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  AttachMoney as MoneyIcon,
  AccountBalance as BalanceIcon
} from '@mui/icons-material';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';

// 导入自定义组件
import StatCard from '../components/dashboard/StatCard';
import PriceTrendChart from '../components/dashboard/PriceTrendChart';
import IncomeChart from '../components/dashboard/IncomeChart';
import MarketOverview from '../components/dashboard/MarketOverview';
import ItemRanking from '../components/dashboard/ItemRanking';
import SystemInfo from '../components/dashboard/SystemInfo';
import InventoryStats from '../components/dashboard/InventoryStats';

// 注册Chart.js组件
ChartJS.register(
  ArcElement, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  PointElement, 
  LineElement, 
  Title, 
  Tooltip, 
  Legend,
  Filler
);

// 默认交易数据（在API数据加载前使用）
const defaultTradingData = {
  summary: {
    totalProfit: 0,
    profitGrowth: 0,
    totalAssets: 0,
    assetGrowth: 0,
    marketStatus: '加载中...',
    silverPrice: '加载中...',
    nvwaPrice: '加载中...'
  },
  itemTrends: [],
  itemRanking: [],
  incomeData: {
    months: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'],
    values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    total: 0
  },
  inventoryStats: {
    itemCount: 0,
    totalQuantity: 0,
    totalValue: 0,
    lowStockCount: 0
  }
};

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tradingData, setTradingData] = useState(defaultTradingData);
  const [statusData, setStatusData] = useState({
    system: {},
    statistics: {
      recipes: 0,
      logs: 0,
      updates: 0,
      ocr_jobs: 0
    },
    recent_activity: []
  });
  
  // 物品价格趋势相关状态
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItem, setSelectedItem] = useState('');
  const [pricePeriod, setPricePeriod] = useState('day');
  const [itemsList, setItemsList] = useState([]);
  const [priceTrendData, setPriceTrendData] = useState([]);
  const [loadingPriceData, setLoadingPriceData] = useState(false);

  // 加载仪表盘数据
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/status/dashboard');
      
      // 提取API返回的数据
      const { system, statistics, recent_activity, trading } = response.data;
      
      // 更新状态数据
      setStatusData({
        system,
        statistics,
        recent_activity
      });
      
      // 更新交易数据（如果API返回）
      if (trading) {
        setTradingData(trading);
      }
      
      setError(null);
    } catch (err) {
      console.error('获取仪表盘数据失败:', err);
      setError('无法加载仪表盘数据。请检查网络连接或稍后再试。');
    } finally {
      setLoading(false);
    }
  };
  
  // 加载物品列表
  const fetchItems = async () => {
    try {
      const response = await axios.get('/api/status/items');
      if (response.data.success && response.data.items) {
        setItemsList(response.data.items);
        // 如果有物品，默认选择第一个
        if (response.data.items.length > 0 && !selectedItem) {
          setSelectedItem(response.data.items[0]);
        }
      }
    } catch (err) {
      console.error('获取物品列表失败:', err);
    }
  };
  
  // 加载物品价格趋势
  const fetchItemPriceTrend = async (itemName, period) => {
    if (!itemName) return;
    
    try {
      setLoadingPriceData(true);
      const response = await axios.get(`/api/status/item-price-trend/${itemName}?period=${period}`);
      
      if (response.data.success && response.data.data) {
        setPriceTrendData(response.data.data);
      } else {
        setPriceTrendData([]);
      }
    } catch (err) {
      console.error(`获取物品 ${itemName} 价格趋势失败:`, err);
      setPriceTrendData([]);
    } finally {
      setLoadingPriceData(false);
    }
  };

  // 初始加载
  useEffect(() => {
    fetchDashboardData();
    fetchItems();
    
    // 设置定时更新 - 每30秒刷新一次
    const intervalId = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(intervalId);
  }, []);
  
  // 当选择物品或周期变化时，加载价格趋势
  useEffect(() => {
    if (selectedItem) {
      fetchItemPriceTrend(selectedItem, pricePeriod);
    }
  }, [selectedItem, pricePeriod]);

  // 处理物品搜索
  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };
  
  // 处理选择物品
  const handleItemChange = (event) => {
    setSelectedItem(event.target.value);
  };
  
  // 处理周期变化
  const handlePeriodChange = (period) => {
    setPricePeriod(period);
  };
  
  // 手动刷新数据
  const handleRefresh = () => {
    fetchDashboardData();
    if (selectedItem) {
      fetchItemPriceTrend(selectedItem, pricePeriod);
    }
  };

  // 格式化数字
  const formatNumber = (num) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };

  if (loading && Object.keys(statusData.system).length === 0) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      {/* 页面标题和刷新按钮 */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 3,
        pb: 2,
        borderBottom: '1px solid rgba(0, 0, 0, 0.06)'
      }}>
        <Typography 
          variant="h4" 
          component="div" 
          sx={{ 
            fontWeight: 700, 
            background: 'linear-gradient(45deg, #1976d2, #4dabf5)',
            backgroundClip: 'text',
            color: 'transparent',
            WebkitBackgroundClip: 'text'
          }}
        >
          交易系统仪表盘
        </Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          variant="contained"
          onClick={handleRefresh}
          sx={{ 
            height: 42,
            px: 2,
            boxShadow: '0 4px 10px rgba(25, 118, 210, 0.25)',
            background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
          }}
        >
          刷新数据
        </Button>
      </Box>
      
      {/* 主布局 */}
      <Grid container spacing={3}>
        {/* 左侧主要内容区域 */}
        <Grid item xs={12} lg={8}>
          {/* 顶部统计卡片 */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            {/* 总利润卡片 */}
            <Grid item xs={12} md={6}>
              <StatCard 
                title="总利润"
                value={tradingData.summary.totalProfit}
                growth={tradingData.summary.profitGrowth}
                icon={<MoneyIcon sx={{ color: '#ffffff', fontSize: 32 }} />}
                iconBgColor="#2e7d32"
                iconShadowColor="rgba(46, 125, 50, 0.3)"
                formatter={(val) => `$${formatNumber(val)}`}
              />
            </Grid>
            
            {/* 总资产价值卡片 */}
            <Grid item xs={12} md={6}>
              <StatCard 
                title="总资产价值"
                value={tradingData.summary.totalAssets}
                growth={tradingData.summary.assetGrowth}
                icon={<BalanceIcon sx={{ color: '#ffffff', fontSize: 32 }} />}
                iconBgColor="#0288d1"
                iconShadowColor="rgba(2, 136, 209, 0.3)"
                formatter={(val) => `$${formatNumber(val)}`}
              />
            </Grid>
          </Grid>
          
          {/* 价格趋势图 */}
          <PriceTrendChart 
            items={itemsList}
            selectedItem={selectedItem}
            period={pricePeriod}
            trendData={priceTrendData}
            loading={loadingPriceData}
            onItemChange={handleItemChange}
            onPeriodChange={handlePeriodChange}
          />
          
          {/* 收入情况图表 */}
          <IncomeChart 
            months={tradingData.incomeData.months}
            values={tradingData.incomeData.values}
            total={tradingData.incomeData.total}
            formatter={formatNumber}
          />
        </Grid>
        
        {/* 右侧边栏 */}
        <Grid item xs={12} lg={4}>
          {/* 行情概览卡片 */}
          <MarketOverview 
            marketStatus={tradingData.summary.marketStatus}
            silverPrice={tradingData.summary.silverPrice}
            nvwaPrice={tradingData.summary.nvwaPrice}
          />
          
          {/* 物品排名表 */}
          <ItemRanking 
            items={tradingData.itemRanking}
            searchTerm={searchTerm}
            onSearch={handleSearch}
          />
          
          {/* 系统信息和库存统计 */}
          <Grid container spacing={3}>
            {/* 系统信息 */}
            <Grid item xs={12}>
              <Paper 
                sx={{ 
                  p: 3, 
                  boxShadow: '0 6px 12px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04)',
                  border: '1px solid rgba(226, 232, 240, 0.7)',
                  borderRadius: 3
                }}
              >
                <SystemInfo system={statusData.system} />
                <InventoryStats 
                  itemCount={tradingData.inventoryStats?.itemCount || 0}
                  totalQuantity={tradingData.inventoryStats?.totalQuantity || 0}
                  lowStockCount={tradingData.inventoryStats?.lowStockCount || 0}
                  totalValue={tradingData.inventoryStats?.totalValue || 0}
                  zeroStockCount={tradingData.inventoryStats?.zeroStockCount || 0}
                />
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard; 