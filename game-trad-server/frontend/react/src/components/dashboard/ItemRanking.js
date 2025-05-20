import React from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Divider, 
  TextField, 
  InputAdornment, 
  TableContainer, 
  Table, 
  TableHead, 
  TableBody, 
  TableRow, 
  TableCell 
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

/**
 * 物品排名组件
 * @param {Object} props
 * @param {Array} props.items - 物品排名数据
 * @param {string} props.searchTerm - 搜索关键词
 * @param {function} props.onSearch - 搜索处理函数
 */
const ItemRanking = ({ 
  items = [], 
  searchTerm = '', 
  onSearch 
}) => {
  // 过滤排名数据
  const filteredItems = items.filter(item => 
    searchTerm === '' || item.item.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
          物品排名
        </Typography>
        <TextField
          placeholder="搜索物品..."
          size="small"
          value={searchTerm}
          onChange={onSearch}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" sx={{ color: 'text.secondary' }} />
              </InputAdornment>
            ),
          }}
          sx={{ 
            width: '150px',
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              '& fieldset': {
                borderColor: 'rgba(0, 0, 0, 0.1)',
              },
              '&:hover fieldset': {
                borderColor: 'primary.main',
              },
            }
          }}
        />
      </Box>
      <Divider sx={{ mb: 3 }} />
      <TableContainer sx={{ maxHeight: 280, overflow: 'auto' }}>
        <Table size="small" sx={{ minWidth: '100%' }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600, fontSize: '0.775rem' }}>物品</TableCell>
              <TableCell align="center" sx={{ fontWeight: 600, fontSize: '0.775rem' }}>库存量</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, fontSize: '0.775rem' }}>涨跌幅</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredItems.length > 0 ? (
              filteredItems.map((item) => (
                <TableRow 
                  key={item.item}
                  sx={{ 
                    '&:last-child td, &:last-child th': { border: 0 },
                    '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.02)' }
                  }}
                >
                  <TableCell component="th" scope="row" sx={{ fontSize: '0.775rem' }}>
                    {item.item}
                  </TableCell>
                  <TableCell align="center" sx={{ fontSize: '0.775rem' }}>{item.amount}</TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      color: item.change >= 0 ? 'success.main' : 'error.main',
                      fontWeight: 'bold',
                      fontSize: '0.775rem'
                    }}
                  >
                    {item.change >= 0 ? '+' : ''}{item.change.toFixed(1)}%
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={3} align="center" sx={{ py: 6 }}>
                  {searchTerm ? '未找到匹配项' : '暂无数据'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default ItemRanking; 