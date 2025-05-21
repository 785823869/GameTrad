import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Grid,
  Card,
  CardMedia,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  Button
} from '@mui/material';
import {
  Delete as DeleteIcon,
  ZoomIn as ZoomInIcon,
  CloudUpload as UploadIcon
} from '@mui/icons-material';

/**
 * OCR图片预览组件
 * 用于显示多个待OCR识别的图片，支持删除和放大预览
 */
const OCRPreview = ({ images, onDelete, onAdd }) => {
  const [enlargedImage, setEnlargedImage] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  // 处理图片放大预览
  const handleZoomIn = (index) => {
    setEnlargedImage(images[index]);
    setPreviewOpen(true);
  };

  // 关闭预览
  const handleClosePreview = () => {
    setPreviewOpen(false);
    setEnlargedImage(null);
  };

  // 获取图片URL，兼容不同格式的图片数据
  const getImageUrl = (image) => {
    if (!image) return '';
    
    // 如果是字符串，直接返回（可能是URL或DataURL）
    if (typeof image === 'string') return image;
    
    // 如果是对象，检查是否有url属性
    if (typeof image === 'object') {
      // 如果有url属性，直接使用
      if (image.url) return image.url;
      
      // 如果是File或Blob对象，创建URL
      if (image instanceof File || image instanceof Blob) {
        try {
          return URL.createObjectURL(image);
        } catch (error) {
          console.error('创建图片URL失败:', error);
          return '';
        }
      }
    }
    
    // 默认情况，无法处理
    console.warn('无法处理的图片格式:', image);
    return '';
  };

  // 渲染图片网格
  const renderImageGrid = () => {
    if (!images || images.length === 0) {
      return (
        <Box 
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3,
            border: '2px dashed',
            borderColor: 'grey.300',
            borderRadius: 2,
            backgroundColor: 'grey.50',
            minHeight: 150
          }}
        >
          <UploadIcon sx={{ fontSize: 40, color: 'grey.500', mb: 1 }} />
          <Typography variant="body1" color="text.secondary" align="center">
            暂无图片，请添加或粘贴图片后在此处查看
          </Typography>
        </Box>
      );
    }

    return (
      <Grid container spacing={2}>
        {images.map((image, index) => (
          <Grid item xs={6} sm={4} md={3} key={index}>
            <Card 
              variant="outlined" 
              sx={{
                position: 'relative',
                '&:hover': {
                  boxShadow: 3,
                  '& .image-actions': {
                    opacity: 1
                  }
                }
              }}
            >
              <CardMedia
                component="img"
                height="120"
                image={getImageUrl(image)}
                alt={`OCR图片 ${index + 1}`}
                sx={{ objectFit: 'contain', backgroundColor: 'grey.100' }}
                onError={(e) => {
                  console.error('图片加载失败:', e);
                  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIiB2aWV3Qm94PSIwIDAgMjU2IDI1NiI+PHJlY3Qgd2lkdGg9IjI1NiIgaGVpZ2h0PSIyNTYiIGZpbGw9IiNGNUY1RjUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9InN5c3RlbS11aSwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzk5OSI+W+WbvueJh+WKoOi9veWksei0pe+8jOivt+aJk+aJi+edgOm7keWKqF08L3RleHQ+PC9zdmc+';
                }}
              />
              <CardActions 
                className="image-actions"
                sx={{ 
                  position: 'absolute', 
                  top: 0, 
                  right: 0, 
                  opacity: 0, 
                  transition: 'opacity 0.2s',
                  backgroundColor: 'rgba(0,0,0,0.5)',
                  borderRadius: '0 0 0 8px'
                }}
              >
                <IconButton size="small" onClick={() => handleZoomIn(index)} color="primary">
                  <ZoomInIcon fontSize="small" sx={{ color: 'white' }} />
                </IconButton>
                <IconButton size="small" onClick={() => onDelete(index)} color="error">
                  <DeleteIcon fontSize="small" sx={{ color: 'white' }} />
                </IconButton>
              </CardActions>
              <Typography variant="caption" sx={{ p: 1, display: 'block', textAlign: 'center' }}>
                图片 {index + 1}
              </Typography>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <>
      <Box sx={{ mb: 2 }}>
        <Box 
          sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 1
          }}
        >
          <Typography variant="subtitle1" fontWeight="medium">
            图片预览
          </Typography>
          <Typography variant="caption" color="text.secondary">
            已添加 {images?.length || 0} 张图片
          </Typography>
        </Box>
        
        {renderImageGrid()}
        
        {/* 图片放大预览对话框 */}
        <Dialog 
          open={previewOpen} 
          onClose={handleClosePreview}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>图片预览</DialogTitle>
          <DialogContent sx={{ textAlign: 'center', p: 2 }}>
            {enlargedImage && (
              <img
                src={getImageUrl(enlargedImage)}
                alt="放大预览"
                style={{ maxWidth: '100%', maxHeight: '70vh' }}
                onError={(e) => {
                  console.error('预览图片加载失败');
                  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIiB2aWV3Qm94PSIwIDAgMjU2IDI1NiI+PHJlY3Qgd2lkdGg9IjI1NiIgaGVpZ2h0PSIyNTYiIGZpbGw9IiNGNUY1RjUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9InN5c3RlbS11aSwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzk5OSI+W+WbvueJh+WKoOi9veWksei0pe+8jOivt+aJk+aJi+edgOm7keWKqF08L3RleHQ+PC9zdmc+';
                }}
              />
            )}
            <Box sx={{ mt: 2 }}>
              <Button onClick={handleClosePreview}>关闭</Button>
            </Box>
          </DialogContent>
        </Dialog>
      </Box>
    </>
  );
};

export default OCRPreview; 