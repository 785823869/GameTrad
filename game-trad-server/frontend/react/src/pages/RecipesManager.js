import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Button,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  IconButton,
  Snackbar,
  Alert,
  Chip,
  Divider,
  Grid,
  CircularProgress,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

const RecipesManager = () => {
  // 状态管理
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState('add'); // 'add', 'edit', 'delete'
  const [currentRecipe, setCurrentRecipe] = useState({
    id: '',
    name: '',
    ingredients: '',
    notes: '',
    category: '',
    profit: 0
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredRecipes, setFilteredRecipes] = useState([]);

  // 加载配方数据
  const fetchRecipes = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/recipes');
      
      // 调试日志
      console.log('API响应数据:', response.data);
      
      // 检查响应格式并获取配方数组
      const recipesArray = response.data.recipes || [];
      
      // 验证recipes是否为数组
      if (!Array.isArray(recipesArray)) {
        console.error('API返回的recipes不是数组:', recipesArray);
        setError('API返回格式错误，请联系管理员');
        setRecipes([]);
        setFilteredRecipes([]);
      } else {
        console.log('成功获取配方数组，数量:', recipesArray.length);
        setRecipes(recipesArray);
        setFilteredRecipes(recipesArray);
        setError(null);
      }
    } catch (err) {
      console.error('获取配方数据失败:', err);
      setError('无法加载配方数据。请检查网络连接或服务器状态。');
      setRecipes([]);
      setFilteredRecipes([]);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    fetchRecipes();
  }, []);

  // 搜索过滤
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredRecipes(recipes);
    } else {
      const filtered = recipes.filter(recipe => 
        recipe.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        recipe.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        recipe.ingredients.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredRecipes(filtered);
    }
    setPage(0); // 重置分页
  }, [searchTerm, recipes]);

  // 处理分页变化
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // 对话框处理
  const handleOpenDialog = (type, recipe = null) => {
    setDialogType(type);
    if (recipe) {
      setCurrentRecipe(recipe);
    } else {
      setCurrentRecipe({
        id: '',
        name: '',
        ingredients: '',
        notes: '',
        category: '',
        profit: 0
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  // 表单字段处理
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCurrentRecipe(prev => ({
      ...prev,
      [name]: name === 'profit' ? parseFloat(value) || 0 : value
    }));
  };

  // 保存配方
  const handleSaveRecipe = async () => {
    try {
      let response;
      
      if (dialogType === 'add') {
        response = await axios.post('/api/recipes', currentRecipe);
        setSnackbar({
          open: true,
          message: '配方添加成功',
          severity: 'success'
        });
      } else if (dialogType === 'edit') {
        response = await axios.put(`/api/recipes/${currentRecipe.id}`, currentRecipe);
        setSnackbar({
          open: true,
          message: '配方更新成功',
          severity: 'success'
        });
      }
      
      handleCloseDialog();
      fetchRecipes(); // 重新获取所有配方
    } catch (err) {
      console.error('保存配方失败:', err);
      setSnackbar({
        open: true,
        message: '操作失败：' + (err.response?.data?.message || err.message),
        severity: 'error'
      });
    }
  };

  // 删除配方
  const handleDeleteRecipe = async () => {
    try {
      await axios.delete(`/api/recipes/${currentRecipe.id}`);
      handleCloseDialog();
      
      // 在本地状态中移除已删除的配方
      const updatedRecipes = recipes.filter(recipe => recipe.id !== currentRecipe.id);
      setRecipes(updatedRecipes);
      setFilteredRecipes(
        searchTerm.trim() === '' 
          ? updatedRecipes 
          : updatedRecipes.filter(recipe => 
              recipe.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              recipe.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
              recipe.ingredients.toLowerCase().includes(searchTerm.toLowerCase())
            )
      );
      
      setSnackbar({
        open: true,
        message: '配方删除成功',
        severity: 'success'
      });
    } catch (err) {
      console.error('删除配方失败:', err);
      setSnackbar({
        open: true,
        message: '删除失败：' + (err.response?.data?.message || err.message),
        severity: 'error'
      });
    }
  };

  // 关闭提示条
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // 渲染加载状态
  if (loading && recipes.length === 0) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          配方管理
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog('add')}
        >
          添加配方
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ width: '100%', mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', p: 2 }}>
          <TextField
            variant="outlined"
            size="small"
            placeholder="搜索配方..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ width: 300 }}
          />
          <Button
            startIcon={<RefreshIcon />}
            onClick={fetchRecipes}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
        <Divider />
        <TableContainer>
          <Table sx={{ minWidth: 650 }}>
            <TableHead>
              <TableRow>
                <TableCell>配方名称</TableCell>
                <TableCell>分类</TableCell>
                <TableCell>材料</TableCell>
                <TableCell>利润</TableCell>
                <TableCell align="right">操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <CircularProgress size={24} sx={{ my: 2 }} />
                  </TableCell>
                </TableRow>
              ) : filteredRecipes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    未找到配方数据
                  </TableCell>
                </TableRow>
              ) : (
                filteredRecipes
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((recipe) => (
                    <TableRow key={recipe.id}>
                      <TableCell component="th" scope="row">
                        {recipe.name}
                      </TableCell>
                      <TableCell>
                        <Chip label={recipe.category} size="small" color="primary" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        {recipe.ingredients.split(',').slice(0, 3).join(', ')}
                        {recipe.ingredients.split(',').length > 3 && '...'}
                      </TableCell>
                      <TableCell>{recipe.profit}</TableCell>
                      <TableCell align="right">
                        <IconButton
                          color="primary"
                          onClick={() => handleOpenDialog('edit', recipe)}
                          size="small"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          color="error"
                          onClick={() => handleOpenDialog('delete', recipe)}
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredRecipes.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="每页行数"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
        />
      </Paper>

      {/* 添加/编辑配方对话框 */}
      <Dialog open={openDialog && ['add', 'edit'].includes(dialogType)} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogType === 'add' ? '添加新配方' : '编辑配方'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="配方名称"
                name="name"
                value={currentRecipe.name}
                onChange={handleInputChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="分类"
                name="category"
                value={currentRecipe.category}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="利润"
                name="profit"
                type="number"
                value={currentRecipe.profit}
                onChange={handleInputChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="材料"
                name="ingredients"
                value={currentRecipe.ingredients}
                onChange={handleInputChange}
                multiline
                rows={2}
                placeholder="材料1, 材料2, 材料3..."
                helperText="多个材料请用逗号分隔"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="备注"
                name="notes"
                value={currentRecipe.notes}
                onChange={handleInputChange}
                multiline
                rows={4}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button onClick={handleSaveRecipe} variant="contained" color="primary">
            保存
          </Button>
        </DialogActions>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={openDialog && dialogType === 'delete'} onClose={handleCloseDialog}>
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除配方 "{currentRecipe.name}" 吗？此操作不可撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button onClick={handleDeleteRecipe} color="error">
            删除
          </Button>
        </DialogActions>
      </Dialog>

      {/* 提示条 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default RecipesManager; 