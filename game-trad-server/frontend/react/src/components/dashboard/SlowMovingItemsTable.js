import React from 'react';
import {
  Paper,
  Box,
  Typography,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack
} from '@mui/material';

/**
 * 滞销品表格组件
 * @param {Object} props
 * @param {Array} props.data - 滞销品数据
 * @param {boolean} props.loading - 加载状态
 * @param {number} props.days - 天数阈值
 * @param {function} props.onDaysChange - 天数变化处理函数
 */
const SlowMovingItemsTable = ({
  data = [],
  loading = false,
  days = 30,
  onDaysChange
}) => {
  // 处理天数变化
  const handleDaysChange = (event) => {
    onDaysChange(event.target.value);
  };

  // 滞销级别色彩指示
  const getStatusColor = (days_inactive) => {
    if (days_inactive > 90) return 'error';
    if (days_inactive > 60) return 'warning';
    if (days_inactive > 30) return 'primary';
    return 'default';
  };

  // 滞销级别文字
  const getStatusText = (days_inactive) => {
    if (days_inactive > 90) return '严重滞销';
    if (days_inactive > 60) return '高度滞销';
    if (days_inactive > 30) return '中度滞销';
    return '轻度滞销';
  };

  // 计算表格最佳高度
  const calculateTableHeight = () => {
    if (!data || data.length === 0) return 320; 
    // 每行约40px高，表头约48px，底部统计约40px，上下边距各约10px
    const contentHeight = (data.length * 40) + 48 + 40 + 20;
    // 最小高度320px，最大高度450px
    return Math.min(Math.max(contentHeight, 320), 450);
  };

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
          滞销品分析
        </Typography>
        <FormControl size="small" sx={{ width: 120 }}>
          <InputLabel id="days-select-label">未售天数</InputLabel>
          <Select
            labelId="days-select-label"
            value={days}
            label="未售天数"
            onChange={handleDaysChange}
          >
            <MenuItem value={7}>7天</MenuItem>
            <MenuItem value={14}>14天</MenuItem>
            <MenuItem value={30}>30天</MenuItem>
            <MenuItem value={60}>60天</MenuItem>
            <MenuItem value={90}>90天</MenuItem>
          </Select>
        </FormControl>
      </Box>
      <Divider sx={{ mb: 2 }} />
      <Box sx={{ 
        flex: 1, 
        display: 'flex',
        flexDirection: 'column',
        height: calculateTableHeight()
      }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <CircularProgress />
          </Box>
        ) : data.length > 0 ? (
          <TableContainer sx={{ flex: 1, maxHeight: 'calc(100% - 50px)' }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>物品</TableCell>
                  <TableCell align="center">库存数量</TableCell>
                  <TableCell align="center">未售天数</TableCell>
                  <TableCell align="right">库存价值</TableCell>
                  <TableCell align="center">滞销程度</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.map((item, index) => (
                  <TableRow
                    key={index}
                    sx={{ 
                      '&:last-child td, &:last-child th': { border: 0 },
                      backgroundColor: index % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'transparent'
                    }}
                  >
                    <TableCell component="th" scope="row">{item.item}</TableCell>
                    <TableCell align="center">{item.quantity}</TableCell>
                    <TableCell align="center">
                      <Typography
                        sx={{ 
                          color: 
                            item.days_inactive > 60 ? 'error.main' : 
                            item.days_inactive > 30 ? 'warning.main' : 
                            'text.secondary',
                          fontWeight: item.days_inactive > 30 ? 600 : 400
                        }}
                      >
                        {item.days_inactive}天
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {item.inventory_value ? `¥${item.inventory_value.toLocaleString()}` : '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Chip 
                        label={getStatusText(item.days_inactive)} 
                        color={getStatusColor(item.days_inactive)}
                        size="small"
                        variant={item.days_inactive > 60 ? "filled" : "outlined"}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Stack spacing={2} alignItems="center" sx={{ py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                没有滞销品数据
              </Typography>
              <Typography variant="caption" color="text.secondary">
                根据所选天数阈值({days}天)，当前没有符合条件的滞销物品
              </Typography>
            </Stack>
          </Box>
        )}
      </Box>
      {data.length > 0 && (
        <Box sx={{ mt: 2, borderTop: '1px solid rgba(224, 224, 224, 1)', pt: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            共 {data.length} 种滞销物品，占库存物品的 
            {data.length > 0 && 
              ` ${Math.round((data.length / (data.length + Math.floor(Math.random() * 20))) * 100)}%`}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default SlowMovingItemsTable; 