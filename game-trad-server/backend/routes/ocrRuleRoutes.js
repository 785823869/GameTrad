/**
 * OCR规则管理路由
 */
const express = require('express');
const router = express.Router();
const { requireAuth } = require('../middleware/authMiddleware');
const ocrRuleController = require('../controllers/ocrRuleController');

/**
 * 获取入库规则列表
 * @route GET /api/ocr-rules/stock-in
 * @access 私有
 */
router.get('/stock-in', requireAuth, ocrRuleController.getStockInRules);

/**
 * 获取入库规则详情
 * @route GET /api/ocr-rules/stock-in/:id
 * @access 私有
 */
router.get('/stock-in/:id', requireAuth, ocrRuleController.getStockInRule);

/**
 * 添加入库规则
 * @route POST /api/ocr-rules/stock-in
 * @access 私有
 */
router.post('/stock-in', requireAuth, ocrRuleController.addStockInRule);

/**
 * 更新入库规则
 * @route PUT /api/ocr-rules/stock-in/:id
 * @access 私有
 */
router.put('/stock-in/:id', requireAuth, ocrRuleController.updateStockInRule);

/**
 * 删除入库规则
 * @route DELETE /api/ocr-rules/stock-in/:id
 * @access 私有
 */
router.delete('/stock-in/:id', requireAuth, ocrRuleController.deleteStockInRule);

/**
 * 测试入库规则
 * @route POST /api/ocr-rules/stock-in/test
 * @access 私有
 */
router.post('/stock-in/test', requireAuth, ocrRuleController.testStockInRule);

/**
 * 获取出库规则列表
 * @route GET /api/ocr-rules/stock-out
 * @access 私有
 */
router.get('/stock-out', requireAuth, ocrRuleController.getStockOutRules);

/**
 * 获取出库规则详情
 * @route GET /api/ocr-rules/stock-out/:id
 * @access 私有
 */
router.get('/stock-out/:id', requireAuth, ocrRuleController.getStockOutRule);

/**
 * 添加出库规则
 * @route POST /api/ocr-rules/stock-out
 * @access 私有
 */
router.post('/stock-out', requireAuth, ocrRuleController.addStockOutRule);

/**
 * 更新出库规则
 * @route PUT /api/ocr-rules/stock-out/:id
 * @access 私有
 */
router.put('/stock-out/:id', requireAuth, ocrRuleController.updateStockOutRule);

/**
 * 删除出库规则
 * @route DELETE /api/ocr-rules/stock-out/:id
 * @access 私有
 */
router.delete('/stock-out/:id', requireAuth, ocrRuleController.deleteStockOutRule);

/**
 * 测试出库规则
 * @route POST /api/ocr-rules/stock-out/test
 * @access 私有
 */
router.post('/stock-out/test', requireAuth, ocrRuleController.testStockOutRule);

/**
 * 获取监控规则列表
 * @route GET /api/ocr-rules/monitor
 * @access 私有
 */
router.get('/monitor', requireAuth, ocrRuleController.getMonitorRules);

/**
 * 获取监控规则详情
 * @route GET /api/ocr-rules/monitor/:id
 * @access 私有
 */
router.get('/monitor/:id', requireAuth, ocrRuleController.getMonitorRule);

/**
 * 添加监控规则
 * @route POST /api/ocr-rules/monitor
 * @access 私有
 */
router.post('/monitor', requireAuth, ocrRuleController.addMonitorRule);

/**
 * 更新监控规则
 * @route PUT /api/ocr-rules/monitor/:id
 * @access 私有
 */
router.put('/monitor/:id', requireAuth, ocrRuleController.updateMonitorRule);

/**
 * 删除监控规则
 * @route DELETE /api/ocr-rules/monitor/:id
 * @access 私有
 */
router.delete('/monitor/:id', requireAuth, ocrRuleController.deleteMonitorRule);

/**
 * 测试监控规则
 * @route POST /api/ocr-rules/monitor/test
 * @access 私有
 */
router.post('/monitor/test', requireAuth, ocrRuleController.testMonitorRule);

module.exports = router; 