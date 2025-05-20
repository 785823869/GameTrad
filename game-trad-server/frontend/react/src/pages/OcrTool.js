import React, { useState } from 'react';
import axios from 'axios';
import { 
  Paper, 
  Typography, 
  Box, 
  Button, 
  TextField,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Divider,
  CircularProgress,
  Alert,
  Snackbar,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// 自定义样式的上传按钮
const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

function OcrTool() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [history, setHistory] = useState([]);

  // 处理文件选择
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // 验证文件类型
      if (!file.type.match('image.*')) {
        setError('请选择图片文件（JPEG, PNG, GIF）');
        setOpenSnackbar(true);
        return;
      }
      
      // 验证文件大小
      if (file.size > 5 * 1024 * 1024) { // 5MB
        setError('文件大小不能超过5MB');
        setOpenSnackbar(true);
        return;
      }
      
      setSelectedFile(file);
      
      // 创建预览URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(file);
      
      // 清除之前的结果
      setResults(null);
      setError('');
    }
  };

  // 处理OCR识别请求
  const handleOcrProcess = async () => {
    if (!selectedFile) {
      setError('请先选择一个图片文件');
      setOpenSnackbar(true);
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      
      const response = await axios.post('/api/ocr', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.success) {
        setResults(response.data);
        
        // 添加到历史记录
        setHistory(prev => [
          {
            id: Date.now(),
            imageUrl: response.data.imageUrl,
            result: response.data.rawText,
            timestamp: new Date().toISOString()
          },
          ...prev
        ].slice(0, 10)); // 保留最近10条记录
      } else {
        throw new Error(response.data.message || '识别失败');
      }
    } catch (err) {
      setError(err.message || '识别过程发生错误');
      setOpenSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  // 加载历史记录
  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/ocr/history');
      if (response.data.success) {
        setHistory(response.data.history);
      }
    } catch (err) {
      setError('加载历史记录失败');
      setOpenSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  // 处理Snackbar关闭
  const handleCloseSnackbar = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpenSnackbar(false);
  };

  // 组件挂载时加载历史记录
  React.useEffect(() => {
    loadHistory();
  }, []);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        OCR图像识别
      </Typography>
      <Typography variant="body1" paragraph>
        上传图片进行文本识别，支持JPEG、PNG格式。
      </Typography>
      
      <Grid container spacing={3}>
        {/* 上传区域 */}
        <Grid item xs={12} md={6}>
          <Paper 
            elevation={3} 
            sx={{ 
              p: 3, 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              minHeight: 300,
              justifyContent: 'center'
            }}
          >
            {previewUrl ? (
              <Box sx={{ width: '100%', textAlign: 'center' }}>
                <img 
                  src={previewUrl} 
                  alt="预览" 
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: 250,
                    marginBottom: 16
                  }}
                />
                <Box sx={{ mt: 2 }}>
                  <Button 
                    variant="outlined" 
                    component="label"
                    sx={{ mr: 1 }}
                  >
                    更换图片
                    <VisuallyHiddenInput 
                      type="file" 
                      onChange={handleFileChange}
                      accept="image/*" 
                    />
                  </Button>
                  <Button 
                    variant="contained" 
                    onClick={handleOcrProcess}
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : null}
                  >
                    {loading ? '处理中...' : '开始识别'}
                  </Button>
                </Box>
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center' }}>
                <CloudUploadIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" gutterBottom>
                  点击下方按钮选择图片
                </Typography>
                <Button 
                  variant="contained" 
                  component="label"
                >
                  选择图片
                  <VisuallyHiddenInput 
                    type="file" 
                    onChange={handleFileChange}
                    accept="image/*" 
                  />
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* 识别结果区域 */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, minHeight: 300 }}>
            <Typography variant="h6" gutterBottom>
              识别结果
            </Typography>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                <CircularProgress />
              </Box>
            ) : results ? (
              <Box>
                <TextField
                  label="原始识别文本"
                  multiline
                  rows={4}
                  value={results.rawText}
                  fullWidth
                  variant="outlined"
                  margin="normal"
                  InputProps={{
                    readOnly: true,
                  }}
                />
                
                <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                  解析结果:
                </Typography>
                
                <Card variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    {Object.entries(results.parsed).map(([key, value]) => (
                      <Box key={key} sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          {key}:
                        </Typography>
                        <Typography variant="body1">
                          {value}
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
                <Typography variant="body1" color="text.secondary">
                  上传图片并点击"开始识别"获取结果
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* 历史记录 */}
        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              历史记录
            </Typography>
            
            {history.length > 0 ? (
              <List>
                {history.map((item) => (
                  <React.Fragment key={item.id}>
                    <ListItem alignItems="flex-start">
                      <Box sx={{ display: 'flex', width: '100%' }}>
                        <Box sx={{ width: 100, mr: 2 }}>
                          <img 
                            src={item.imageUrl} 
                            alt="历史图片" 
                            style={{ width: '100%', height: 'auto' }} 
                          />
                        </Box>
                        <ListItemText
                          primary={new Date(item.timestamp).toLocaleString()}
                          secondary={
                            <React.Fragment>
                              <Typography
                                component="span"
                                variant="body2"
                                color="text.primary"
                              >
                                识别结果
                              </Typography>
                              {` — ${item.result}`}
                            </React.Fragment>
                          }
                        />
                      </Box>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                暂无历史记录
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      <Snackbar open={openSnackbar} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default OcrTool; 