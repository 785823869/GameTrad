const axios = require('axios');

async function testGetActiveRules() {
  try {
    // 服务器默认运行在端口5000上
    const PORT = 5000;
    console.log(`测试获取活跃OCR规则，端口: ${PORT}`);

    try {
      // 健康检查
      const healthResponse = await axios.get(`http://localhost:${PORT}/api/health`, { timeout: 5000 });
      console.log('服务器健康状态:', healthResponse.data);
      
      // 获取OCR规则
      console.log('请求活跃OCR规则...');
      const ocrResponse = await axios.get(`http://localhost:${PORT}/api/ocr-rules/stock-out/active`, { 
        timeout: 5000,
        headers: { 'Accept': 'application/json' }
      });
      
      console.log('OCR规则响应状态:', ocrResponse.status);
      if (Array.isArray(ocrResponse.data)) {
        console.log('活跃规则数量:', ocrResponse.data.length);
        if (ocrResponse.data.length > 0) {
          console.log('规则详情:', JSON.stringify(ocrResponse.data, null, 2));
        } else {
          console.log('没有找到活跃的OCR规则');
        }
      } else {
        console.log('OCR规则响应非数组:', ocrResponse.data);
      }
    } catch (error) {
      console.error(`请求失败 (端口${PORT}):`, error.message);
      
      if (error.response) {
        console.error('状态码:', error.response.status);
        console.error('响应数据:', error.response.data);
      } else if (error.request) {
        console.error('无响应，可能服务器未启动或端口错误');
        console.error('尝试创建测试规则...');
        await createTestRule(PORT);
      }
    }
  } catch (error) {
    console.error('测试过程发生错误:', error.message);
  }
}

async function createTestRule(port) {
  try {
    console.log('尝试创建测试OCR规则...');
    
    const testRule = {
      name: '测试售出规则',
      description: '用于测试的OCR规则',
      is_active: true,
      patterns: [
        { field: 'item_name', regex: '已成功售出([^（(]+)', group: 1, default_value: '' },
        { field: 'quantity', regex: '[（(](\\d+)[）)]', group: 1, default_value: '0' },
        { field: 'unit_price', regex: '售出单价[：:]\\s*(\\d+)银两', group: 1, default_value: '0' },
        { field: 'fee', regex: '手续费[：:]\\s*(\\d+)银两', group: 1, default_value: '0' },
        { field: 'total_amount', regex: '^$', group: 1, default_value: '0' }
      ]
    };
    
    const response = await axios.post(`http://localhost:${port}/api/ocr-rules/stock-out`, testRule, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('创建规则响应:', response.status);
    console.log('响应数据:', response.data);
    
    // 尝试获取创建的规则
    await testGetActiveRules();
    
  } catch (error) {
    console.error('创建规则失败:', error.message);
    if (error.response) {
      console.error('状态码:', error.response.status);
      console.error('响应数据:', error.response.data);
    }
  }
}

testGetActiveRules(); 