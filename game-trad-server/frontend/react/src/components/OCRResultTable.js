import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  TextField,
  Typography,
  Box,
  Button,
  Tooltip,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  SelectAll as SelectAllIcon,
  FormatClear as ClearSelectionIcon,
  Notes as NotesIcon,
  Close as CloseIcon,
  Image as ImageIcon
} from '@mui/icons-material';

/**
 * OCR识别结果表格组件
 * 用于显示和编辑OCR识别的结果数据
 */
const OCRResultTable = ({ data, onChange, onDelete, onViewRawText }) => {
  const [editingRow, setEditingRow] = useState(null);
  const [editValues, setEditValues] = useState({});
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [rowToDelete, setRowToDelete] = useState(null);
  const [previewImage, setPreviewImage] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  // 处理编辑
  const startEditing = (index) => {
    setEditingRow(index);
    setEditValues({ ...data[index] });
  };

  // 取消编辑
  const cancelEditing = () => {
    setEditingRow(null);
    setEditValues({});
  };

  // 保存编辑
  const saveEditing = () => {
    if (editingRow !== null) {
      // 如果提供了行级更新函数，则使用它
      if (typeof onChange === 'function') {
        onChange(editingRow, editValues);
      }
      setEditingRow(null);
      setEditValues({});
    }
  };

  // 处理编辑字段的变化
  const handleEditChange = (field, value) => {
    setEditValues(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // 处理选中行的变化
  const handleRowSelect = (index) => {
    setSelectedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // 全选/取消全选
  const handleSelectAll = () => {
    if (selectedRows.size === data.length) {
      // 当前已全选，则取消全选
      setSelectedRows(new Set());
    } else {
      // 当前未全选，则全选
      setSelectedRows(new Set(data.map((_, index) => index)));
    }
  };

  // 打开删除确认对话框
  const openDeleteConfirm = (index) => {
    setRowToDelete(index);
    setConfirmDeleteOpen(true);
  };

  // 关闭删除确认对话框
  const closeDeleteConfirm = () => {
    setConfirmDeleteOpen(false);
    setRowToDelete(null);
  };

  // 确认删除
  const confirmDelete = () => {
    if (rowToDelete !== null && typeof onDelete === 'function') {
      onDelete(rowToDelete);
      closeDeleteConfirm();
    }
  };

  // 删除选中的所有行
  const deleteSelected = () => {
    if (typeof onDelete !== 'function') return;
    
    // 按照索引从大到小排序，避免删除过程中索引变化
    const indicesToDelete = Array.from(selectedRows).sort((a, b) => b - a);
    indicesToDelete.forEach(index => onDelete(index));
    setSelectedRows(new Set());
  };

  // 打开图片预览
  const handleOpenPreview = (imageUrl) => {
    setPreviewImage(imageUrl);
    setPreviewOpen(true);
  };

  // 关闭图片预览
  const handleClosePreview = () => {
    setPreviewOpen(false);
    setPreviewImage(null);
  };

  // 查看原始OCR文本
  const handleViewRawText = (rawText) => {
    if (typeof onViewRawText === 'function' && rawText) {
      onViewRawText(rawText);
    }
  };

  return (
    <>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
        <Box>
          <Tooltip title="全选/取消全选">
            <IconButton onClick={handleSelectAll}>
              {selectedRows.size === data.length ? <ClearSelectionIcon /> : <SelectAllIcon />}
            </IconButton>
          </Tooltip>
          {selectedRows.size > 0 && (
            <Tooltip title="删除选中项">
              <IconButton color="error" onClick={deleteSelected}>
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
        <Typography variant="caption" color="text.secondary">
          总计: {data.length} 条记录
        </Typography>
      </Box>

      <TableContainer component={Paper} sx={{ maxHeight: 400, overflow: 'auto' }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedRows.size > 0 && selectedRows.size < data.length}
                  checked={data.length > 0 && selectedRows.size === data.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>物品名称</TableCell>
              <TableCell align="right">数量</TableCell>
              <TableCell align="right">单价</TableCell>
              <TableCell align="right">手续费</TableCell>
              <TableCell align="right">总金额</TableCell>
              <TableCell>备注</TableCell>
              <TableCell align="center">操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length > 0 ? (
              data.map((row, index) => (
                <TableRow key={index} hover>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedRows.has(index)}
                      onChange={() => handleRowSelect(index)}
                      disabled={editingRow === index}
                    />
                  </TableCell>
                  <TableCell>
                    {editingRow === index ? (
                      <TextField
                        value={editValues.item_name || ''}
                        onChange={(e) => handleEditChange('item_name', e.target.value)}
                        fullWidth
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {row.originalImage && (
                          <IconButton 
                            size="small" 
                            onClick={() => handleOpenPreview(row.originalImage)}
                            sx={{ p: 0.5 }}
                          >
                            <ImageIcon fontSize="small" />
                          </IconButton>
                        )}
                        <Tooltip title={row.item_name}>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 150,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {row.item_name}
                          </Typography>
                        </Tooltip>
                      </Box>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {editingRow === index ? (
                      <TextField
                        type="number"
                        value={editValues.quantity || 0}
                        onChange={(e) => handleEditChange('quantity', Number(e.target.value))}
                        inputProps={{ min: 0, step: 1 }}
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      row.quantity
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {editingRow === index ? (
                      <TextField
                        type="number"
                        value={editValues.unit_price || 0}
                        onChange={(e) => handleEditChange('unit_price', Number(e.target.value))}
                        inputProps={{ min: 0, step: 0.01 }}
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      parseFloat(row.unit_price || 0).toFixed(2)
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {editingRow === index ? (
                      <TextField
                        type="number"
                        value={editValues.fee || 0}
                        onChange={(e) => handleEditChange('fee', Number(e.target.value))}
                        inputProps={{ min: 0, step: 0.01 }}
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      parseFloat(row.fee || 0).toFixed(2)
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {editingRow === index ? (
                      <TextField
                        type="number"
                        value={editValues.total_amount || 0}
                        onChange={(e) => handleEditChange('total_amount', Number(e.target.value))}
                        inputProps={{ min: 0, step: 0.01 }}
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      parseFloat(row.total_amount || 0).toFixed(2)
                    )}
                  </TableCell>
                  <TableCell>
                    {editingRow === index ? (
                      <TextField
                        value={editValues.note || ''}
                        onChange={(e) => handleEditChange('note', e.target.value)}
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      <Tooltip title={row.note || ''}>
                        <Typography
                          variant="body2"
                          sx={{
                            maxWidth: 100,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {row.note || ''}
                        </Typography>
                      </Tooltip>
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {editingRow === index ? (
                      <>
                        <Tooltip title="保存">
                          <IconButton size="small" color="primary" onClick={saveEditing}>
                            <SaveIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="取消">
                          <IconButton size="small" color="default" onClick={cancelEditing}>
                            <CancelIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </>
                    ) : (
                      <>
                        <Tooltip title="编辑">
                          <IconButton size="small" color="primary" onClick={() => startEditing(index)}>
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="删除">
                          <IconButton size="small" color="error" onClick={() => openDeleteConfirm(index)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {row.rawText && (
                          <Tooltip title="查看原始文本">
                            <IconButton size="small" color="default" onClick={() => handleViewRawText(row.rawText)}>
                              <NotesIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  暂无数据
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 删除确认对话框 */}
      <Dialog
        open={confirmDeleteOpen}
        onClose={closeDeleteConfirm}
      >
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定要删除这条OCR识别结果吗？此操作无法撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeleteConfirm}>取消</Button>
          <Button onClick={confirmDelete} color="error">删除</Button>
        </DialogActions>
      </Dialog>

      {/* 图片预览对话框 */}
      <Dialog open={previewOpen} onClose={handleClosePreview} maxWidth="md">
        <DialogTitle>
          图片预览
          <IconButton
            aria-label="close"
            onClick={handleClosePreview}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <img
            src={previewImage}
            alt="预览"
            style={{ maxWidth: '100%', maxHeight: '80vh', display: 'block', margin: '0 auto' }}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};

export default OCRResultTable; 