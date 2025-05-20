const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');

// 配方文件路径
const recipesFilePath = path.join(__dirname, '../../config/recipes.json');

// 确保配方文件存在
const ensureRecipesFile = async () => {
  await fs.ensureDir(path.dirname(recipesFilePath));
  
  if (!await fs.pathExists(recipesFilePath)) {
    await fs.writeJson(recipesFilePath, { recipes: [] }, { spaces: 2 });
  }
  
  return recipesFilePath;
};

/**
 * 解析配方文本
 * @param {string} recipeText - 配方文本
 * @returns {Object} - 解析后的配方对象
 */
const parseRecipe = (recipeText) => {
  // 这里模拟Python配方解析功能
  logger.info('解析配方内容');
  
  try {
    // 示例解析逻辑，实际应根据原Python代码逻辑实现
    const lines = recipeText.split('\n').filter(line => line.trim());
    
    // 解析配方名称
    const nameMatch = lines[0].match(/^(.+?)(?:\s*\(|$)/);
    const name = nameMatch ? nameMatch[1].trim() : '未知配方';
    
    // 解析原料
    const ingredients = [];
    const resultItems = [];
    
    let inIngredients = true;
    
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // 检测是否已经到产出部分
      if (line.includes('产出:') || line.includes('结果:')) {
        inIngredients = false;
        continue;
      }
      
      // 解析物品和数量
      const itemMatch = line.match(/(.+?)\s*[xX×]\s*(\d+)/);
      if (itemMatch) {
        const item = {
          name: itemMatch[1].trim(),
          quantity: parseInt(itemMatch[2], 10)
        };
        
        if (inIngredients) {
          ingredients.push(item);
        } else {
          resultItems.push(item);
        }
      }
    }
    
    return {
      name,
      ingredients,
      results: resultItems,
      raw: recipeText,
      createdAt: new Date().toISOString()
    };
  } catch (error) {
    logger.error(`配方解析错误: ${error.message}`);
    throw new Error(`配方解析失败: ${error.message}`);
  }
};

/**
 * 获取所有配方
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getAllRecipes = async (req, res) => {
  try {
    await ensureRecipesFile();
    const { recipes } = await fs.readJson(recipesFilePath);
    
    res.status(200).json({
      success: true,
      count: recipes.length,
      recipes
    });
  } catch (error) {
    logger.error(`获取配方失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取配方失败',
      error: error.message
    });
  }
};

/**
 * 获取单个配方
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.getRecipeById = async (req, res) => {
  try {
    await ensureRecipesFile();
    const { recipes } = await fs.readJson(recipesFilePath);
    const recipe = recipes.find(r => r.id === req.params.id);
    
    if (!recipe) {
      return res.status(404).json({
        success: false,
        message: '配方未找到'
      });
    }
    
    res.status(200).json({
      success: true,
      recipe
    });
  } catch (error) {
    logger.error(`获取配方失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '获取配方失败',
      error: error.message
    });
  }
};

/**
 * 添加新配方
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.addRecipe = async (req, res) => {
  try {
    const { name, recipeText } = req.body;
    
    if (!recipeText) {
      return res.status(400).json({
        success: false,
        message: '请提供配方内容'
      });
    }
    
    // 解析配方
    const parsedRecipe = parseRecipe(recipeText);
    const recipeId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    
    // 保存到配方文件
    await ensureRecipesFile();
    const data = await fs.readJson(recipesFilePath);
    
    const newRecipe = {
      id: recipeId,
      ...parsedRecipe,
      name: name || parsedRecipe.name
    };
    
    data.recipes.push(newRecipe);
    await fs.writeJson(recipesFilePath, data, { spaces: 2 });
    
    logger.info(`添加新配方: ${newRecipe.name}`);
    res.status(201).json({
      success: true,
      message: '配方添加成功',
      recipe: newRecipe
    });
  } catch (error) {
    logger.error(`添加配方失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '添加配方失败',
      error: error.message
    });
  }
};

/**
 * 更新配方
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.updateRecipe = async (req, res) => {
  try {
    const { name, recipeText } = req.body;
    const { id } = req.params;
    
    if (!id) {
      return res.status(400).json({
        success: false,
        message: '请提供配方ID'
      });
    }
    
    // 读取现有配方
    await ensureRecipesFile();
    const data = await fs.readJson(recipesFilePath);
    const recipeIndex = data.recipes.findIndex(r => r.id === id);
    
    if (recipeIndex === -1) {
      return res.status(404).json({
        success: false,
        message: '配方未找到'
      });
    }
    
    // 更新配方
    let updatedRecipe = { ...data.recipes[recipeIndex] };
    
    if (recipeText) {
      // 如果提供了新的配方文本，重新解析
      const parsedRecipe = parseRecipe(recipeText);
      updatedRecipe = {
        ...updatedRecipe,
        ...parsedRecipe,
        raw: recipeText
      };
    }
    
    if (name) {
      updatedRecipe.name = name;
    }
    
    updatedRecipe.updatedAt = new Date().toISOString();
    
    // 保存更新
    data.recipes[recipeIndex] = updatedRecipe;
    await fs.writeJson(recipesFilePath, data, { spaces: 2 });
    
    logger.info(`更新配方: ${updatedRecipe.name}`);
    res.status(200).json({
      success: true,
      message: '配方更新成功',
      recipe: updatedRecipe
    });
  } catch (error) {
    logger.error(`更新配方失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '更新配方失败',
      error: error.message
    });
  }
};

/**
 * 删除配方
 * @param {Object} req - 请求对象
 * @param {Object} res - 响应对象
 */
exports.deleteRecipe = async (req, res) => {
  try {
    const { id } = req.params;
    
    // 读取现有配方
    await ensureRecipesFile();
    const data = await fs.readJson(recipesFilePath);
    const recipeIndex = data.recipes.findIndex(r => r.id === id);
    
    if (recipeIndex === -1) {
      return res.status(404).json({
        success: false,
        message: '配方未找到'
      });
    }
    
    // 记录要删除的配方名称
    const recipeName = data.recipes[recipeIndex].name;
    
    // 删除配方
    data.recipes.splice(recipeIndex, 1);
    await fs.writeJson(recipesFilePath, data, { spaces: 2 });
    
    logger.info(`删除配方: ${recipeName}`);
    res.status(200).json({
      success: true,
      message: '配方删除成功'
    });
  } catch (error) {
    logger.error(`删除配方失败: ${error.message}`);
    res.status(500).json({
      success: false,
      message: '删除配方失败',
      error: error.message
    });
  }
}; 