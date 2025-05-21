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
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem
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
 * 交易OCR对话框组件
 * 提供完整的交易OCR识别流程，包括图片选择、预览、识别和结果编辑
 */
const TransactionOCRDialog = ({ open, onClose, onImport, title = "交易OCR识别导入" }) => {
  // 步骤状态
  const [activeStep, setActiveStep] = useState(0);
  
  // 图片状态
  const [images, setImages] = useState([]);
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const fileInputRef = useRef(null);
  
  // 识别结果状态
  const [recognizing, setRecognizing] = useState(false);
  const [ocrResults, setOcrResults] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  
  // 交易类型（买入/卖出）
  const [transactionType, setTransactionType] = useState('buy');
  
  // 交易平台
  const [platform, setPlatform] = useState('');
  
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
      setCurrentIndex(0);
      setProgress(0);
      setError(null);
      setShowRawText(false);
      setTransactionType('buy');
      setPlatform('');
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

  // 处理粘贴事件
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
    
    // 顺序处理每个图片
    for (let i = 0; i < images.length; i++) {
      setCurrentIndex(i);
      const image = images[i];
      try {
        const response = await OCRService.recognizeImage(image.file);
        
        if (response.success && response.data) {
          // 处理数据，确保单价字段被正确处理
          const processedData = { ...response.data };
          
          // 安全转换数值字段
          const quantity = typeof processedData.quantity === 'string' ? 
            parseInt(processedData.quantity, 10) : (processedData.quantity || 0);
          
          // 处理单价 - 可能来自unit_price或price字段
          let unitPrice = 0;
          if (processedData.unit_price !== undefined) {
            unitPrice = typeof processedData.unit_price === 'string' ? 
              parseFloat(processedData.unit_price) : processedData.unit_price;
          } else if (processedData.price !== undefined) {
            unitPrice = typeof processedData.price === 'string' ?
              parseFloat(processedData.price) : processedData.price;
          }
          
          // 计算总金额
          const fee = typeof processedData.fee === 'string' ? 
            parseFloat(processedData.fee) : (processedData.fee || 0);
          
          let totalAmount = typeof processedData.total_amount === 'string' ? 
            parseFloat(processedData.total_amount) : (processedData.total_amount || 0);
          
          // 如果单价为0但有总金额和数量，计算单价
          if (unitPrice === 0 && totalAmount > 0 && quantity > 0) {
            unitPrice = (totalAmount + fee) / quantity;
            console.log(`TransactionOCRDialog: 计算单价 = (${totalAmount} + ${fee}) / ${quantity} = ${unitPrice}`);
          } 
          // 如果总金额为0但有单价和数量，计算总金额
          else if (totalAmount === 0 && unitPrice > 0 && quantity > 0) {
            totalAmount = (quantity * unitPrice) - fee;
            console.log(`TransactionOCRDialog: 计算总金额 = (${quantity} * ${unitPrice}) - ${fee} = ${totalAmount}`);
          }
          
          // 添加交易特定字段，确保单价和总金额字段正确
          const enhancedData = {
            ...processedData,
            transaction_type: transactionType,
            platform: platform,
            unit_price: unitPrice,
            price: unitPrice, // 同时更新price字段以保持一致
            fee: fee,
            total_amount: totalAmount,
            quantity: quantity,
            originalImage: image.url,
            rawText: response.rawText || '无原始识别文本'
          };
          
          console.log(`TransactionOCRDialog: 处理后的OCR数据:`, enhancedData);
          
          allResults.push(enhancedData);
        } else {
          console.warn(`图片 ${i + 1} 识别失败:`, response.message || '未知错误');
        }
      } catch (error) {
        console.error(`图片 ${i + 1} 处理出错:`, error);
      }
      
      completed++;
      const newProgress = Math.round((completed / total) * 100);
      setProgress(newProgress);
    }
    
    if (allResults.length > 0) {
      setOcrResults(allResults);
      setActiveStep(1);
    } else {
      setError('所有图片都识别失败');
    }
    
    setRecognizing(false);
  };
  
  // 处理导入
  const handleImport = () => {
    if (ocrResults.length === 0) {
      setError('没有OCR结果可导入');
      return;
    }
    
    // 添加日志记录
    console.log('TransactionOCRDialog: 准备导入交易数据');
    console.log('TransactionOCRDialog: 原始OCR结果数量:', ocrResults.length);
    
    // 验证数据结构字段是否符合接口要求
    const validResults = ocrResults.filter(result => {
      // 记录每个数据项用于调试
      console.log('TransactionOCRDialog: 处理OCR结果项:', result);
      
      // 验证必需字段
      if (!result.item_name || !result.quantity || (!result.price && result.price !== 0)) {
        console.warn('TransactionOCRDialog: 跳过无效数据，缺少必要字段:', result);
        return false;
      }
      
      // 确保数量和价格是有效的数字且大于0
      const quantity = parseFloat(result.quantity);
      const price = parseFloat(result.price);
      
      const isValid = !isNaN(quantity) && quantity > 0 && !isNaN(price) && price >= 0;
      if (!isValid) {
        console.warn('TransactionOCRDialog: 跳过无效数据，无效的数量或价格:', result);
      }
      
      return isValid;
    });
    
    if (validResults.length === 0) {
      setError('没有有效的OCR数据可导入');
      return;
    }
    
    // 处理每条OCR结果为交易格式
    const formattedResults = validResults.map(result => {
      // 基础格式转换
      const processedResult = {
        transaction_type: result.transaction_type || transactionType,
        item_name: result.item_name,
        quantity: parseFloat(result.quantity),
        // 确保单价字段正确
        unit_price: parseFloat(result.unit_price || result.price || 0),
        price: parseFloat(result.unit_price || result.price || 0),
        // 确保fee是数字
        fee: result.fee ? parseFloat(result.fee) : 0,
        // 添加平台信息
        platform: result.platform || platform,
        // 添加MySQL兼容格式的交易时间 (YYYY-MM-DD HH:MM:SS)
        transaction_time: (() => {
          const now = new Date();
          const year = now.getFullYear();
          const month = String(now.getMonth() + 1).padStart(2, '0');
          const day = String(now.getDate()).padStart(2, '0');
          const hours = String(now.getHours()).padStart(2, '0');
          const minutes = String(now.getMinutes()).padStart(2, '0');
          const seconds = String(now.getSeconds()).padStart(2, '0');
          return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        })(),
        // 添加备注
        note: result.note || '通过OCR导入'
      };
      
      // 计算金额 = 数量 * 价格 - 手续费
      const quantity = processedResult.quantity;
      const price = processedResult.price;
      const fee = processedResult.fee;
      
      // 计算总金额
      processedResult.total_amount = (quantity * price) - fee;
      
      console.log('TransactionOCRDialog: 计算金额: 数量:' + quantity + 
                ' 价格:' + price + 
                ' 手续费:' + fee + 
                ' 总金额:' + processedResult.total_amount);
      
      return processedResult;
    });
    
    console.log('TransactionOCRDialog: 最终导入的有效数据数量:', formattedResults.length);
    console.log('TransactionOCRDialog: 准备导入的有效OCR数据:', formattedResults);
    
    // 调用API导入交易记录
    const importTransaction = async (data) => {
      try {
        const response = await fetch('/api/transactions/import', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(data)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP错误! 状态: ${response.status}`);
        }
        
        return await response.json();
      } catch (error) {
        console.error('导入交易记录失败:', error);
        throw error;
      }
    };
    
    // 调用导入函数
    importTransaction(formattedResults)
      .then(response => {
        console.log('TransactionOCRDialog: API返回的响应:', response);
        
        // 检查API返回的详细错误信息
        if (response && response.results && response.results.errors && response.results.errors.length > 0) {
          // 提取具体错误信息
          const errorMessages = response.results.errors.join('; ');
          
          // 如果有错误但同时也有成功的记录，显示警告而非错误
          if (response?.results?.success > 0) {
            setError(`警告: ${errorMessages}`);
          } else {
            // 全部失败的情况
            setError(`导入失败: ${errorMessages}`);
          }
          return;
        }
        
        // 处理成功/失败计数
        const successCount = response?.results?.success || 0;
        const failedCount = response?.results?.failed || 0;
        
        if (successCount > 0 && failedCount === 0) {
          onClose();
          if (typeof onImport === 'function') {
            onImport(response);
          }
        } else if (successCount > 0 && failedCount > 0) {
          setError(`部分导入成功: ${successCount}条成功，${failedCount}条失败`);
        } else if (successCount === 0 && failedCount > 0) {
          setError(`导入失败: 所有${failedCount}条记录均未能导入`);
        }
      })
      .catch(error => {
        console.error('TransactionOCRDialog: 导入出错:', error);
        
        // 提取错误信息
        let errorMessage = '导入失败';
        if (error.response && error.response.data) {
          if (error.response.data.message) {
            errorMessage = error.response.data.message;
          }
          
          // 检查是否有更详细的错误信息
          if (error.response.data.error) {
            errorMessage += `: ${error.response.data.error}`;
          }
        }
        
        setError(errorMessage);
      });
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
  
  // 处理交易类型变化
  const handleTransactionTypeChange = (event) => {
    setTransactionType(event.target.value);
    
    // 更新所有OCR结果的交易类型
    if (ocrResults.length > 0) {
      setOcrResults(prev => 
        prev.map(result => ({
          ...result,
          transaction_type: event.target.value
        }))
      );
    }
  };
  
  // 处理平台变化
  const handlePlatformChange = (event) => {
    setPlatform(event.target.value);
    
    // 更新所有OCR结果的平台
    if (ocrResults.length > 0) {
      setOcrResults(prev => 
        prev.map(result => ({
          ...result,
          platform: event.target.value
        }))
      );
    }
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
        // 交易特定字段
        showTransactionFields={true}
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
                  {recognizing ? `识别中 (${currentIndex + 1}/${images.length})` : '开始识别'}
                </Button>
              )}
            </Box>
            
            <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
              <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                <InputLabel id="transaction-type-label">交易类型</InputLabel>
                <Select
                  labelId="transaction-type-label"
                  value={transactionType}
                  onChange={handleTransactionTypeChange}
                  label="交易类型"
                >
                  <MenuItem value="buy">买入</MenuItem>
                  <MenuItem value="sell">卖出</MenuItem>
                  <MenuItem value="exchange">交换</MenuItem>
                  <MenuItem value="gift">赠送</MenuItem>
                  <MenuItem value="other">其他</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                <InputLabel id="platform-label">交易平台</InputLabel>
                <Select
                  labelId="platform-label"
                  value={platform}
                  onChange={handlePlatformChange}
                  label="交易平台"
                >
                  <MenuItem value="">无</MenuItem>
                  <MenuItem value="淘宝">淘宝</MenuItem>
                  <MenuItem value="闲鱼">闲鱼</MenuItem>
                  <MenuItem value="微信">微信</MenuItem>
                  <MenuItem value="Steam">Steam</MenuItem>
                  <MenuItem value="其他">其他</MenuItem>
                </Select>
              </FormControl>
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
            <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
              <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                <InputLabel id="transaction-type-edit-label">交易类型</InputLabel>
                <Select
                  labelId="transaction-type-edit-label"
                  value={transactionType}
                  onChange={handleTransactionTypeChange}
                  label="交易类型"
                >
                  <MenuItem value="buy">买入</MenuItem>
                  <MenuItem value="sell">卖出</MenuItem>
                  <MenuItem value="exchange">交换</MenuItem>
                  <MenuItem value="gift">赠送</MenuItem>
                  <MenuItem value="other">其他</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                <InputLabel id="platform-edit-label">交易平台</InputLabel>
                <Select
                  labelId="platform-edit-label"
                  value={platform}
                  onChange={handlePlatformChange}
                  label="交易平台"
                >
                  <MenuItem value="">无</MenuItem>
                  <MenuItem value="淘宝">淘宝</MenuItem>
                  <MenuItem value="闲鱼">闲鱼</MenuItem>
                  <MenuItem value="微信">微信</MenuItem>
                  <MenuItem value="Steam">Steam</MenuItem>
                  <MenuItem value="其他">其他</MenuItem>
                </Select>
              </FormControl>
            </Box>
            
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

export default TransactionOCRDialog; 