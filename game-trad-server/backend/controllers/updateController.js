const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');

// GitHub仓库URL
const githubRepoUrl = process.env.GITHUB_REPO_URL || 'https://github.com/785823869/GameTrad/releases';
// GitHub API URL
const githubApiUrl = 'https://api.github.com/repos/785823869/GameTrad/releases/latest';

// 保存更新状态的文件
const updateStatusPath = path.join(__dirname, '../../config/update_status.json');

// 确保更新状态文件存在
const ensureUpdateStatusFile = async () => {
  await fs.ensureDir(path.dirname(updateStatusPath));
  
  if (!await fs.pathExists(updateStatusPath)) {
    const initialStatus = {
      lastChecked: null,
      currentVersion: '1.3.1',
      availableVersion: null,
      updateAvailable: false,
      updateUrl: null,
      updateStatus: 'idle',
      downloadProgress: 0,
      installProgress: 0,
      error: null
    };
    
    await fs.writeJson(updateStatusPath, initialStatus, { spaces: 2 });
  }
  
  return updateStatusPath;
};

/**
 * 获取当前更新状态
 * @returns {Promise<Object>} - 更新状态对象
 */
const getUpdateStatus = async () => {
  await ensureUpdateStatusFile();
  return await fs.readJson(updateStatusPath);
};

/**
 * 更新状态信息
 * @param {Object} statusUpdate - 要更新的状态字段
 * @returns {Promise<Object>} - 更新后的状态对象
 */
const updateStatus = async (statusUpdate) => {
  const currentStatus = await getUpdateStatus();
  const newStatus = { ...currentStatus, ...statusUpdate };
  await fs.writeJson(updateStatusPath, newStatus, { spaces: 2 });
  return newStatus;
};

/**
 * 检查GitHub上的最新版本
 * @returns {Promise<Object>} - 最新版本信息
 */
const checkGitHubVersion = async () => {
  try {
    // 实际项目中应使用GitHub API
    // 这里使用mock数据进行模拟
    const mockLatestVersion = {
      tag_name: 'v1.3.2',
      name: '游戏交易系统 v1.3.2',
      body: '## 更新内容\n\n- 修复了仪表盘显示问题\n- 优化数据导入功能\n- 提升系统稳定性',
      published_at: '2023-11-20T08:00:00Z',
      assets: [
        {
          name: 'GameTrad_Setup_1.3.2.exe',
          browser_download_url: `${githubRepoUrl}/download/v1.3.2/GameTrad_Setup_1.3.2.exe`
        }
      ]
    };
    
    // 模拟API响应延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 记录检查结果
    logger.info(`检查更新完成，最新版本: ${mockLatestVersion.tag_name}`);
    
    return mockLatestVersion;
  } catch (error) {
    logger.error(`检查更新失败: ${error.message}`);
    throw new Error(`检查更新失败: ${error.message}`);
  }
};

/**
 * 比较版本号
 * @param {string} v1 - 版本1
 * @param {string} v2 - 版本2
 * @returns {number} - 如果v1大于v2，返回1；如果v1小于v2，返回-1；如果相等，返回0
 */
const compareVersions = (v1, v2) => {
  const v1Parts = v1.replace(/^v/, '').split('.').map(Number);
  const v2Parts = v2.replace(/^v/, '').split('.').map(Number);
  
  for (let i = 0; i < Math.max(v1Parts.length, v2Parts.length); i++) {
    const v1Part = v1Parts[i] || 0;
    const v2Part = v2Parts[i] || 0;
    
    if (v1Part > v2Part) return 1;
    if (v1Part < v2Part) return -1;
  }
  
  return 0;
};

/**
 * 检查更新
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.checkUpdate = async (req, res) => {
  try {
    const currentStatus = await getUpdateStatus();
    
    // 检查GitHub上的最新版本
    const latestRelease = await checkGitHubVersion();
    const latestVersion = latestRelease.tag_name;
    const currentVersion = `v${currentStatus.currentVersion}`;
    
    // 比较版本
    const updateAvailable = compareVersions(latestVersion, currentVersion) > 0;
    
    // 更新状态
    const newStatus = await updateStatus({
      lastChecked: new Date().toISOString(),
      availableVersion: latestVersion.replace(/^v/, ''),
      updateAvailable,
      updateUrl: updateAvailable ? latestRelease.assets[0].browser_download_url : null,
      updateStatus: updateAvailable ? 'available' : 'up-to-date',
      error: null
    });
    
    res.status(200).json({
      success: true,
      updateAvailable,
      currentVersion: currentVersion.replace(/^v/, ''),
      latestVersion: latestVersion.replace(/^v/, ''),
      releaseNotes: latestRelease.body,
      publishDate: latestRelease.published_at,
      downloadUrl: updateAvailable ? latestRelease.assets[0].browser_download_url : null,
      status: newStatus
    });
  } catch (error) {
    logger.error(`检查更新失败: ${error.message}`);
    
    // 更新状态为错误
    await updateStatus({
      updateStatus: 'error',
      error: error.message
    });
    
    res.status(500).json({
      success: false,
      message: '检查更新失败',
      error: error.message
    });
  }
};

/**
 * 模拟下载更新
 * @returns {Promise<boolean>} - 下载是否成功
 */
const simulateDownload = async () => {
  // 模拟下载进度更新
  for (let progress = 0; progress <= 100; progress += 10) {
    await updateStatus({ downloadProgress: progress, updateStatus: 'downloading' });
    await new Promise(resolve => setTimeout(resolve, 500)); // 模拟下载延迟
  }
  
  return true;
};

/**
 * 模拟安装更新
 * @returns {Promise<boolean>} - 安装是否成功
 */
const simulateInstall = async () => {
  // 模拟安装进度更新
  for (let progress = 0; progress <= 100; progress += 20) {
    await updateStatus({ installProgress: progress, updateStatus: 'installing' });
    await new Promise(resolve => setTimeout(resolve, 500)); // 模拟安装延迟
  }
  
  // 更新完成后，将当前版本更新为最新版本
  const status = await getUpdateStatus();
  await updateStatus({
    currentVersion: status.availableVersion,
    updateStatus: 'completed',
    installProgress: 100
  });
  
  return true;
};

/**
 * 下载更新
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.downloadUpdate = async (req, res) => {
  try {
    const status = await getUpdateStatus();
    
    if (!status.updateAvailable) {
      return res.status(400).json({
        success: false,
        message: '没有可用的更新'
      });
    }
    
    // 更新状态为下载中
    await updateStatus({
      updateStatus: 'downloading',
      downloadProgress: 0,
      error: null
    });
    
    // 模拟下载过程
    await simulateDownload();
    
    // 下载完成
    await updateStatus({
      updateStatus: 'downloaded',
      downloadProgress: 100
    });
    
    res.status(200).json({
      success: true,
      message: '更新下载完成',
      status: await getUpdateStatus()
    });
  } catch (error) {
    logger.error(`下载更新失败: ${error.message}`);
    
    // 更新状态为错误
    await updateStatus({
      updateStatus: 'error',
      error: error.message
    });
    
    res.status(500).json({
      success: false,
      message: '下载更新失败',
      error: error.message
    });
  }
};

/**
 * 安装更新
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.installUpdate = async (req, res) => {
  try {
    const status = await getUpdateStatus();
    
    if (status.updateStatus !== 'downloaded') {
      return res.status(400).json({
        success: false,
        message: '更新尚未下载完成'
      });
    }
    
    // 更新状态为安装中
    await updateStatus({
      updateStatus: 'installing',
      installProgress: 0,
      error: null
    });
    
    // 模拟安装过程
    await simulateInstall();
    
    res.status(200).json({
      success: true,
      message: '更新安装完成',
      status: await getUpdateStatus()
    });
  } catch (error) {
    logger.error(`安装更新失败: ${error.message}`);
    
    // 更新状态为错误
    await updateStatus({
      updateStatus: 'error',
      error: error.message
    });
    
    res.status(500).json({
      success: false,
      message: '安装更新失败',
      error: error.message
    });
  }
};

/**
 * 获取更新状态
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getStatus = async (req, res) => {
  try {
    const status = await getUpdateStatus();
    
    res.status(200).json({
      success: true,
      status
    });
  } catch (error) {
    logger.error(`获取更新状态失败: ${error.message}`);
    
    res.status(500).json({
      success: false,
      message: '获取更新状态失败',
      error: error.message
    });
  }
}; 