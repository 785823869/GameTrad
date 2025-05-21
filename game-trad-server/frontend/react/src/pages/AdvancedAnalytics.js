import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Box,
  Button,
  Snackbar,
  Alert,
  Breadcrumbs,
  Link,
  Paper,
  Divider
} from '@mui/material';
import { 
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import axios from 'axios';

// 导入分析图表组件
import VolumeChart from '../components/dashboard/VolumeChart';
import ProfitRankingChart from '../components/dashboard/ProfitRankingChart';
import SlowMovingItemsTable from '../components/dashboard/SlowMovingItemsTable';
import TaxSummaryChart from '../components/dashboard/TaxSummaryChart';

/**
 * 高级分析页面
 */
const AdvancedAnalytics = () => {
  // 状态
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

  // 分析数据
  const [volumeData, setVolumeData] = useState([]);
  const [profitRanking, setProfitRanking] = useState([]);
  const [slowMovingItems, setSlowMovingItems] = useState([]);
  const [taxSummary, setTaxSummary] = useState([]);
  
  // 分析参数
  const [volumePeriod, setVolumePeriod] = useState('day');
  const [profitLimit, setProfitLimit] = useState(10);
  const [slowMovingDays, setSlowMovingDays] = useState(30);
  const [taxRate, setTaxRate] = useState(5);
  const [taxChartType, setTaxChartType] = useState('doughnut');

  // 计算总结数据
  const calculateSummaryData = () => {
    return {
      totalVolume: volumeData.reduce((sum, item) => sum + item.quantity, 0),
      topProfit: profitRanking.length > 0 ? Math.max(...profitRanking.map(item => item.profit_rate)) : 0,
      slowItemsCount: slowMovingItems.length,
      totalTax: taxSummary.reduce((sum, item) => sum + item.tax_amount, 0)
    };
  };

  // 加载分析数据
  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/analytics/trade-analytics', {
        params: {
          period: volumePeriod,
          top_n: profitLimit,
          days: slowMovingDays,
          tax_rate: taxRate / 100 // 转换为小数
        }
      });

      if (response.data.success) {
        const { volume_data, profit_ranking, slow_moving_items, tax_summary } = response.data.data;
        setVolumeData(volume_data || []);
        setProfitRanking(profit_ranking || []);
        setSlowMovingItems(slow_moving_items || []);
        setTaxSummary(tax_summary || []);
      } else {
        showNotification('获取分析数据失败: ' + response.data.message, 'error');
      }
    } catch (error) {
      console.error('获取分析数据出错:', error);
      showNotification('获取分析数据出错: ' + (error.response?.data?.message || error.message), 'error');
    } finally {
      setLoading(false);
    }
  };

  // 加载单个分析数据
  const fetchVolumeData = async () => {
    try {
      const response = await axios.get('/api/analytics/volume', {
        params: { period: volumePeriod }
      });
      if (response.data.success) {
        setVolumeData(response.data.data || []);
      }
    } catch (error) {
      console.error('获取成交量数据失败:', error);
    }
  };

  const fetchProfitRanking = async () => {
    try {
      const response = await axios.get('/api/analytics/profit-ranking', {
        params: { top_n: profitLimit }
      });
      if (response.data.success) {
        setProfitRanking(response.data.data || []);
      }
    } catch (error) {
      console.error('获取利润率排行数据失败:', error);
    }
  };

  const fetchSlowMovingItems = async () => {
    try {
      const response = await axios.get('/api/analytics/slow-moving', {
        params: { days: slowMovingDays }
      });
      if (response.data.success) {
        setSlowMovingItems(response.data.data || []);
      }
    } catch (error) {
      console.error('获取滞销品数据失败:', error);
    }
  };

  const fetchTaxSummary = async () => {
    try {
      const response = await axios.get('/api/analytics/tax-summary', {
        params: { tax_rate: taxRate / 100 }
      });
      if (response.data.success) {
        setTaxSummary(response.data.data || []);
      }
    } catch (error) {
      console.error('获取交易税统计数据失败:', error);
    }
  };

  // 显示通知
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  // 关闭通知
  const handleCloseNotification = (event, reason) => {
    if (reason === 'clickaway') return;
    setNotification({ ...notification, open: false });
  };

  // 处理参数变化
  const handleVolumePeriodChange = (period) => {
    setVolumePeriod(period);
  };

  const handleProfitLimitChange = (limit) => {
    setProfitLimit(limit);
  };

  const handleSlowMovingDaysChange = (days) => {
    setSlowMovingDays(days);
  };

  const handleTaxRateChange = (rate) => {
    setTaxRate(rate);
  };

  const handleTaxChartTypeChange = (type) => {
    setTaxChartType(type);
  };

  // 初始加载和参数变化时刷新数据
  useEffect(() => {
    fetchAnalyticsData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetchVolumeData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [volumePeriod]);

  useEffect(() => {
    fetchProfitRanking();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profitLimit]);

  useEffect(() => {
    fetchSlowMovingItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slowMovingDays]);

  useEffect(() => {
    fetchTaxSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taxRate]);

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* 页面标题 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 1 }}>
            <Link color="inherit" href="/" underline="hover">
              首页
            </Link>
            <Typography color="text.primary">高级分析</Typography>
          </Breadcrumbs>
          <Typography variant="h4" component="h1" gutterBottom>
            交易高级分析
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="primary"
          startIcon={<RefreshIcon />}
          onClick={fetchAnalyticsData}
          disabled={loading}
        >
          刷新数据
        </Button>
      </Box>

      {/* 数据概览摘要 */}
      <Box sx={{ mb: 3 }}>
        <Paper
          sx={{
            p: 3,
            mb: 3,
            boxShadow: '0 3px 5px rgba(0, 0, 0, 0.05)',
            borderRadius: 2,
            background: 'linear-gradient(to right, #f5f7fa, #f8f9fb)'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 500 }}>数据概览</Typography>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={3}>
            {!loading && (
              <>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">成交量总计</Typography>
                  <Typography variant="h6">{calculateSummaryData().totalVolume || '-'}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">最高利润率</Typography>
                  <Typography variant="h6">{calculateSummaryData().topProfit || '-'}%</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">滞销品数量</Typography>
                  <Typography variant="h6">{calculateSummaryData().slowItemsCount || '-'}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">交易税总额</Typography>
                  <Typography variant="h6">¥{calculateSummaryData().totalTax?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '-'}</Typography>
                </Grid>
              </>
            )}
          </Grid>
        </Paper>
      </Box>

      {/* 高级分析图表 - 改进布局 */}
      <Grid container spacing={3}>
        {/* 第一行：主要指标 - 成交量趋势（较大区域） */}
        <Grid item xs={12} md={8}>
          <VolumeChart 
            data={volumeData} 
            loading={loading}
            period={volumePeriod}
            onPeriodChange={handleVolumePeriodChange}
          />
        </Grid>

        {/* 第一行：次要指标 - 交易税统计（较小区域） */}
        <Grid item xs={12} md={4}>
          <TaxSummaryChart 
            data={taxSummary} 
            loading={loading}
            taxRate={taxRate}
            onTaxRateChange={handleTaxRateChange}
            chartType={taxChartType}
            onChartTypeChange={handleTaxChartTypeChange}
          />
        </Grid>

        {/* 第二行：详细分析 - 滞销品分析（产品数据分析） */}
        <Grid item xs={12} md={6}>
          <SlowMovingItemsTable 
            data={slowMovingItems} 
            loading={loading}
            days={slowMovingDays}
            onDaysChange={handleSlowMovingDaysChange}
          />
        </Grid>

        {/* 第二行：详细分析 - 利润率排行（财务数据分析） */}
        <Grid item xs={12} md={6}>
          <ProfitRankingChart 
            data={profitRanking} 
            loading={loading}
            limit={profitLimit}
            onLimitChange={handleProfitLimitChange}
          />
        </Grid>
      </Grid>

      {/* 通知 */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default AdvancedAnalytics; 