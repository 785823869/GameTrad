import React, { useState, useRef, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Stepper,
  Step,
  StepLabel,
  Typography,
  LinearProgress,
  Divider,
  IconButton,
  Alert,
  Paper,
  Tabs,
  Tab,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  CloudUpload as UploadIcon,
  PhotoCamera as CameraIcon,
  ContentPaste as PasteIcon
} from '@mui/icons-material';
import OCRPreview from './OCRPreview';
import OCRResultTable from './OCRResultTable';
import OCRService from '../services/OCRService';

const TabPanel = (props) => {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ocr-tabpanel-${index}`}
      aria-labelledby={`ocr-tab-${index}`}
      {...other}
      style={{ height: '100%' }}
    >
      {value === index && (
        <Box sx={{ height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
};

// 增加原始OCR文本显示对话框组件
const RawTextDialog = ({ open, onClose, rawText }) => (
  <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
    <DialogTitle>
      OCR原始识别文本
      <IconButton
        aria-label="close"
        onClick={onClose}
        sx={{ position: 'absolute', right: 8, top: 8 }}
      >
        <CloseIcon />
      </IconButton>
    </DialogTitle>
    <DialogContent dividers>
      <Paper variant="outlined" sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
        <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
          {rawText || '无识别文本'}
        </Typography>
      </Paper>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>关闭</Button>
    </DialogActions>
  </Dialog>
);

/**
 * OCR对话框组件
 * 提供完整的OCR识别流程，包括图片选择、预览、识别和结果编辑
 */
const OCRDialog = ({ open, onClose, onImport, title = "OCR识别导入", type = "in" }) => {
  // 步骤状态
  const [activeStep, setActiveStep] = useState(0);
  
  // 图片状态
  const [images, setImages] = useState([]);
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const fileInputRef = useRef(null);
  
  // 识别结果状态
  const [recognizing, setRecognizing] = useState(false);
  const [ocrResults, setOcrResults] = useState([]);
  const [currentOcrIndex, setCurrentOcrIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  
  // 原始OCR文本查看
  const [showRawText, setShowRawText] = useState(false);
  const [currentRawText, setCurrentRawText] = useState('');
  
  // 重置状态
  useEffect(() => {
    if (!open) {
      // 对话框关闭时，重置所有状态
      setActiveStep(0);
      setImages([]);
      setOcrResults([]);
      setCurrentOcrIndex(0);
      setProgress(0);
      setError(null);
      setShowRawText(false);
    }
  }, [open]);

  // 创建一个备用方法，使用FileReader处理图片
  const readImageAsDataURL = (file) => {
    return new Promise((resolve, reject) => {
      if (!(file instanceof Blob)) {
        reject(new Error('无效的文件对象'));
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target && typeof event.target.result === 'string') {
          resolve(event.target.result);
        } else {
          reject(new Error('读取文件失败'));
        }
      };
      reader.onerror = (error) => {
        reject(error);
      };
      reader.readAsDataURL(file);
    });
  };

  // 处理粘贴事件（修改为使用粘贴事件）
  const handlePasteEvent = (event) => {
    event.preventDefault();
    if (!event.clipboardData) {
      setError('浏览器不支持访问剪贴板数据');
      return;
    }

    // 检查是否有图片数据
    if (event.clipboardData.files && event.clipboardData.files.length > 0) {
      const files = Array.from(event.clipboardData.files);
      const imageFiles = files.filter(file => file.type.startsWith('image/'));
      
      if (imageFiles.length === 0) {
        setError('剪贴板中没有图片');
        return;
      }

      // 处理图片文件
      imageFiles.forEach(async (file) => {
        try {
          // 尝试创建URL对象
          let url;
          try {
            url = URL.createObjectURL(file);
          } catch (urlError) {
            console.error('URL.createObjectURL失败，使用FileReader代替:', urlError);
            // 使用FileReader作为备用方法
            url = await readImageAsDataURL(file);
          }

          // 更新图片列表
          setImages(prev => [...prev, { file, url }]);
          setError(null);
        } catch (fileError) {
          console.error('处理粘贴图片失败:', fileError);
          setError('处理粘贴的图片失败: ' + fileError.message);
        }
      });
    } else {
      // 尝试从clipboardData.items获取图片
      const items = Array.from(event.clipboardData.items || []);
      let foundImage = false;

      items.forEach(item => {
        if (item.type.startsWith('image/')) {
          foundImage = true;
          const file = item.getAsFile();
          if (!file) {
            console.error('无法获取粘贴的图片文件');
            return;
          }

          // 安全处理图片
          try {
            const url = URL.createObjectURL(file);
            setImages(prev => [...prev, { file, url }]);
            setError(null);
          } catch (urlError) {
            console.error('URL.createObjectURL失败:', urlError);
            // 使用FileReader作为备用方法
            readImageAsDataURL(file)
              .then(dataUrl => {
                setImages(prev => [...prev, { file, url: dataUrl }]);
                setError(null);
              })
              .catch(error => {
                console.error('FileReader读取图片失败:', error);
                setError('无法处理粘贴的图片');
              });
          }
        }
      });

      if (!foundImage) {
        setError('剪贴板中没有图片');
      }
    }
  };

  // 添加粘贴事件监听器
  useEffect(() => {
    if (open) {
      window.addEventListener('paste', handlePasteEvent);
    }
    return () => {
      window.removeEventListener('paste', handlePasteEvent);
    };
  }, [open]);

  // 修改粘贴按钮点击事件
  const handlePasteButtonClick = () => {
    // 提示用户粘贴
    setError('请按Ctrl+V或Command+V粘贴图片');
  };

  // 处理文件选择
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    // 验证是否为图片
    const validImageFiles = files.filter(file => 
      file.type.startsWith('image/')
    );
    
    if (validImageFiles.length === 0) {
      setError('请选择有效的图片文件');
      return;
    }
    
    // 转换文件为URL和预览图
    const newImages = validImageFiles.map(file => ({
      file,
      url: URL.createObjectURL(file)
    }));
    
    setImages(prevImages => [...prevImages, ...newImages]);
    setError(null);
    
    // 重置文件输入，允许选择相同文件
    event.target.value = '';
  };
  
  // 删除图片
  const handleDeleteImage = (index) => {
    setImages(prevImages => {
      const newImages = [...prevImages];
      // 释放URL对象
      URL.revokeObjectURL(newImages[index].url);
      newImages.splice(index, 1);
      return newImages;
    });
  };
  
  // 开始OCR识别
  const handleRecognize = async () => {
    if (images.length === 0) {
      setError('请先添加图片');
      return;
    }
    
    setRecognizing(true);
    setProgress(0);
    setOcrResults([]);
    setError(null);
    
    const total = images.length;
    let completed = 0;
    let allResults = [];
    let errors = [];
    
    // 顺序处理每个图片
    for (let i = 0; i < images.length; i++) {
      setCurrentOcrIndex(i);
      const image = images[i];
      
      try {
        // 调用OCR服务
        const response = await OCRService.recognizeImage(image.file);
        
        if (response.success && response.data) {
          // 处理数据，确保单价正确计算
          const processedData = { ...response.data };
          
          // 安全转换数值字段
          const quantity = typeof processedData.quantity === 'string' ? 
            parseInt(processedData.quantity, 10) : processedData.quantity;
          
          const unitPrice = typeof processedData.unit_price === 'string' ? 
            parseFloat(processedData.unit_price) : (processedData.unit_price || 0);
          
          const fee = typeof processedData.fee === 'string' ? 
            parseFloat(processedData.fee) : (processedData.fee || 0);
          
          const totalAmount = typeof processedData.total_amount === 'string' ? 
            parseFloat(processedData.total_amount) : (processedData.total_amount || 0);
          
          // 如果单价为0但有总金额和数量，计算单价
          if (unitPrice === 0 && totalAmount > 0 && quantity > 0) {
            processedData.unit_price = (totalAmount + fee) / quantity;
            processedData.price = processedData.unit_price; // 同时更新price字段
            console.log(`OCR识别-计算单价: (${totalAmount} + ${fee}) / ${quantity} = ${processedData.unit_price}`);
          }
          
          // 添加图片和原始文本信息
          allResults.push({
            ...processedData,
            originalImage: image.url,
            rawText: response.rawText || '无原始识别文本'
          });
        } else {
          errors.push(`图片 ${i + 1}: ${response.message || '识别失败'}`);
        }
      } catch (error) {
        console.error('OCR识别错误:', error);
        errors.push(`图片 ${i + 1}: 识别出错 - ${error.message || '未知错误'}`);
      }
      
      completed++;
      const newProgress = Math.round((completed / total) * 100);
      setProgress(newProgress);
    }
    
    setOcrResults(allResults);
    setRecognizing(false);
    
    if (allResults.length > 0) {
      if (errors.length > 0) {
        setError(`部分图片识别失败: ${errors.join('; ')}`);
      }
      setActiveStep(1);
    } else {
      setError(`所有图片识别失败: ${errors.join('; ')}`);
    }
  };
  
  // 处理导入
  const handleImport = () => {
    // 防止重复点击或数据为空
    if (recognizing || ocrResults.length === 0) {
      return;
    }

    // 启用调试模式
    const DEBUG = true;
    if (DEBUG) console.log(`即将导入的OCR结果: ${JSON.stringify(ocrResults)}`);

    // 根据导入类型执行不同的导入逻辑
    try {
      if (DEBUG) console.log(`导入类型: ${type}`);

      // 生成唯一请求ID用于跟踪
      const requestId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
      if (DEBUG) console.log(`生成唯一请求ID: ${requestId}`);

      // 确保所有数据都有正确的类型并且去重
      const uniqueItemMap = new Map();
      
      ocrResults.forEach(result => {
        // 跳过已有ID的记录（可能是之前导入成功的响应数据）
        if (result.id) {
          console.warn(`OCRDialog: 跳过已有ID的记录: ${result.id}, 避免重复导入`);
          return;
        }
        
        // 安全解析数值
        const quantity = typeof result.quantity === 'string' ? parseInt(result.quantity, 10) : result.quantity;
        const unitPrice = typeof result.unit_price === 'string' ? parseFloat(result.unit_price) : (result.unit_price || 0);
        const fee = typeof result.fee === 'string' ? parseFloat(result.fee) : (result.fee || 0);
        const totalAmount = typeof result.total_amount === 'string' ? parseFloat(result.total_amount) : (result.total_amount || 0);
        
        // 如果单价为0但有总金额和数量，计算单价
        let calculatedUnitPrice = unitPrice;
        if (calculatedUnitPrice === 0 && totalAmount > 0 && quantity > 0) {
          calculatedUnitPrice = (totalAmount + fee) / quantity;
          console.log(`计算单价: (${totalAmount} + ${fee}) / ${quantity} = ${calculatedUnitPrice}`);
        }
        
        // 创建一个唯一键，基于物品名、数量、单价
        // 不考虑手续费作为唯一性标识
        const itemKey = `${result.item_name}_${quantity}_${totalAmount}`;
        
        // 如果这个键已经存在，检查是否有不同的手续费
        if (uniqueItemMap.has(itemKey)) {
          console.warn(`发现可能重复的记录: ${itemKey}, 使用单一版本以避免重复导入`);
          
          // 更新策略：使用手续费最高的记录
          const existingItem = uniqueItemMap.get(itemKey);
          const existingFee = typeof existingItem.fee === 'string' 
            ? parseFloat(existingItem.fee) : (existingItem.fee || 0);
          
          const newFee = typeof result.fee === 'string'
            ? parseFloat(result.fee) : (result.fee || 0);
            
          if (newFee > existingFee) {
            console.log(`替换记录，使用手续费更高的版本: ${newFee} > ${existingFee}`);
            // 存储处理过的数据
            uniqueItemMap.set(itemKey, {
              ...result,
              quantity: quantity,
              unit_price: calculatedUnitPrice,
              price: calculatedUnitPrice, // 同时更新price字段以保持一致
              fee: newFee,
              total_amount: totalAmount > 0 ? totalAmount : (quantity * calculatedUnitPrice - newFee),
              // 添加请求跟踪ID
              _requestId: requestId
            });
          }
        } else {
          // 存储处理过的数据
          uniqueItemMap.set(itemKey, {
            ...result,
            quantity: quantity,
            unit_price: calculatedUnitPrice,
            price: calculatedUnitPrice, // 同时更新price字段以保持一致
            fee: fee,
            total_amount: totalAmount > 0 ? totalAmount : (quantity * calculatedUnitPrice - fee),
            // 添加请求跟踪ID
            _requestId: requestId
          });
        }
      });
      
      // 转换回数组
      const processedResults = Array.from(uniqueItemMap.values());

      if (DEBUG) {
        console.log(`去重后的数据: ${JSON.stringify(processedResults)}`);
        console.log(`原始数据数量: ${ocrResults.length}, 去重后数量: ${processedResults.length}`);
      }
      
      // 如果处理后没有数据，显示错误并退出
      if (processedResults.length === 0) {
        console.warn("OCRDialog: 处理后没有有效数据可导入");
        setError("没有有效数据可导入");
        return;
      }
      
      // 检查过滤后的数据是否与原始数据量差异很大
      if (processedResults.length < ocrResults.length * 0.5 && ocrResults.length > 1) {
        // 如果过滤掉了超过一半的数据，显示警告但继续处理有效数据
        console.warn(`OCRDialog: 过滤掉了${ocrResults.length - processedResults.length}条数据，可能是重复或无效数据`);
        setError(`已过滤${ocrResults.length - processedResults.length}条可能重复或无效的数据`);
        // 不返回，继续处理有效数据
      }

      // 设置加载状态 - 防止重复提交
      setRecognizing(true);
      setError(null);
      
      // 添加防抖保护，如果短时间内多次点击，只执行最后一次
      if (window._ocrImportTimeout) {
        clearTimeout(window._ocrImportTimeout);
        console.log('取消之前的导入请求');
      }
      
      // 使用setTimeout增加防抖，避免多次快速点击
      window._ocrImportTimeout = setTimeout(() => {
        // 使用OCRService导入数据
        OCRService.importOCRResults(type, processedResults, requestId)
          .then(response => {
            setRecognizing(false);
            
            if (DEBUG) console.log(`导入响应: ${JSON.stringify(response)}`);
            
            if (response && response.success) {
              // 修复onImport回调，传递原始数据而不仅是布尔值
              // 同时确保有成功导入的记录时才调用
              if (onImport && typeof onImport === 'function') {
                // 检查是否有成功导入的记录
                const successCount = response.results?.success || 0;
                if (successCount > 0) {
                  console.log(`调用onImport回调，导入成功 ${successCount} 条记录`);
                  // 传递导入响应给回调，确保前端可以正确处理
                  onImport(response);
                } else {
                  console.warn('导入成功但没有记录被添加，可能是重复数据');
                  setError('没有新记录被添加，可能是重复数据');
                  return; // 不关闭对话框，显示错误信息
                }
              }
              
              // 关闭对话框
              onClose();
            } else {
              // 显示错误信息
              const errorMsg = response?.message || '导入失败，请检查数据并重试';
              console.error(`OCR导入错误: ${errorMsg}`);
              setError(errorMsg);
            }
          })
          .catch(err => {
            setRecognizing(false);
            const errorMsg = err?.response?.data?.message || err.message || '导入过程中发生错误';
            console.error(`OCR导入异常: ${errorMsg}`, err);
            setError(`导入失败: ${errorMsg}`);
          });
      }, 100); // 100ms的防抖延迟
    } catch (err) {
      setRecognizing(false);
      console.error('OCR导入处理异常:', err);
      setError(`导入处理异常: ${err.message}`);
    }
  };
  
  // 处理结果编辑
  const handleResultChange = (index, updatedData) => {
    setOcrResults(prev => {
      const newResults = [...prev];
      newResults[index] = {
        ...newResults[index],
        ...updatedData
      };
      return newResults;
    });
  };
  
  // 处理结果删除
  const handleResultDelete = (index) => {
    setOcrResults(prev => {
      const newResults = [...prev];
      newResults.splice(index, 1);
      return newResults;
    });
  };
  
  // 显示原始OCR文本
  const handleShowRawText = (rawText) => {
    setCurrentRawText(rawText);
    setShowRawText(true);
  };
  
  // 关闭原始OCR文本对话框
  const handleCloseRawText = () => {
    setShowRawText(false);
  };
  
  // 渲染OCR结果表格
  const renderResultsTable = () => {
    if (ocrResults.length === 0) {
      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', pt: 3, pb: 3 }}>
          <Typography variant="body1" color="text.secondary">
            没有OCR识别结果
          </Typography>
        </Box>
      );
    }
    
    return (
      <OCRResultTable 
        data={ocrResults} 
        onChange={handleResultChange}
        onDelete={handleResultDelete}
        onViewRawText={handleShowRawText}
      />
    );
  };
  
  // 步骤内容
  const getStepContent = (step) => {
    switch (step) {
      case 0: // 图片选择和预览
        return (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                onClick={() => fileInputRef.current?.click()}
                startIcon={<UploadIcon />}
              >
                选择图片
              </Button>
              <Button
                variant="outlined"
                onClick={handlePasteButtonClick}
                startIcon={<PasteIcon />}
              >
                从剪贴板粘贴
              </Button>
              <input
                type="file"
                accept="image/*"
                multiple
                hidden
                ref={fileInputRef}
                onChange={handleFileSelect}
              />
              
              {images.length > 0 && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleRecognize}
                  disabled={recognizing}
                  startIcon={recognizing ? <CircularProgress size={20} /> : null}
                >
                  {recognizing ? `识别中 (${currentOcrIndex + 1}/${images.length})` : '开始识别'}
                </Button>
              )}
            </Box>
            
            {recognizing && (
              <Box sx={{ width: '100%', mb: 2 }}>
                <LinearProgress variant="determinate" value={progress} />
                <Typography variant="caption" color="text.secondary" align="center" sx={{ display: 'block', mt: 1 }}>
                  处理中... {progress}%
                </Typography>
              </Box>
            )}
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <OCRPreview 
              images={images} 
              onDelete={handleDeleteImage}
              onAdd={() => fileInputRef.current?.click()}
            />
          </Box>
        );
        
      case 1: // OCR结果编辑
        return (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {error && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {renderResultsTable()}
          </Box>
        );
        
      default:
        return '未知步骤';
    }
  };
  
  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            height: '80vh',
            display: 'flex',
            flexDirection: 'column'
          }
        }}
      >
        <DialogTitle>
          {title}
          <IconButton
            aria-label="close"
            onClick={onClose}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent dividers sx={{ p: 2, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          <Stepper activeStep={activeStep} sx={{ pt: 1, pb: 3 }}>
            <Step>
              <StepLabel>选择图片</StepLabel>
            </Step>
            <Step>
              <StepLabel>编辑结果</StepLabel>
            </Step>
          </Stepper>
          
          <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
            {getStepContent(activeStep)}
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={onClose}>取消</Button>
          {activeStep === 1 && (
            <Button 
              onClick={handleImport} 
              variant="contained" 
              color="primary"
              disabled={ocrResults.length === 0}
            >
              导入数据
            </Button>
          )}
        </DialogActions>
      </Dialog>
      
      <RawTextDialog
        open={showRawText}
        onClose={handleCloseRawText}
        rawText={currentRawText}
      />
    </>
  );
};

export default OCRDialog; 