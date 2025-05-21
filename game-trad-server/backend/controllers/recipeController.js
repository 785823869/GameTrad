const fs = require('fs-extra');
const path = require('path');
const logger = require('../utils/logger');
const db = require('../utils/db');

// 配方文件路径 - 保留作为备份
const recipesFilePath = path.join(__dirname, '../../config/recipes.json');

// 确保配方文件存在
const ensureRecipesFile = async () => {
  await fs.ensureDir(path.dirname(recipesFilePath));
  
  if (!await fs.pathExists(recipesFilePath)) {
    await fs.writeJson(recipesFilePath, { recipes: [] }, { spaces: 2 });
  }
  
  return recipesFilePath;
};

// 确保数据库中有recipes表
const ensureRecipesTable = async () => {
  try {
    // 检查表是否存在
    const checkTableQuery = `
      SELECT COUNT(*) as count 
      FROM information_schema.tables 
      WHERE table_schema = '${db.dbConfig.database}' 
      AND table_name = 'recipes'
    `;
    
    const result = await db.fetchOne(checkTableQuery);
    
    if (!result || result.count === 0) {
      // 创建表
      const createTableQuery = `
        CREATE TABLE recipes (
          id VARCHAR(36) PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          ingredients JSON,
          results JSON,
          raw TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `;
      
      await db.execute(createTableQuery);
      logger.info('创建recipes表成功');
    }
  } catch (error) {
    logger.error(`确保recipes表存在失败: ${error.message}`);
  }
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
    await ensureRecipesTable();
    
    // 从数据库获取所有配方
    const query = `SELECT * FROM recipes ORDER BY created_at DESC`;
    const recipes = await db.fetchAll(query);
    
    // 解析JSON字段
    const formattedRecipes = recipes.map(recipe => ({
      ...recipe,
      ingredients: JSON.parse(recipe.ingredients || '[]'),
      results: JSON.parse(recipe.results || '[]')
    }));
    
    res.status(200).json({
      success: true,
      count: formattedRecipes.length,
      recipes: formattedRecipes
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
    await ensureRecipesTable();
    
    // 从数据库获取指定配方
    const query = `SELECT * FROM recipes WHERE id = ?`;
    const recipe = await db.fetchOne(query, [req.params.id]);
    
    if (!recipe) {
      return res.status(404).json({
        success: false,
        message: '配方未找到'
      });
    }
    
    // 解析JSON字段
    const formattedRecipe = {
      ...recipe,
      ingredients: JSON.parse(recipe.ingredients || '[]'),
      results: JSON.parse(recipe.results || '[]')
    };
    
    res.status(200).json({
      success: true,
      recipe: formattedRecipe
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
    
    await ensureRecipesTable();
    
    // 解析配方
    const parsedRecipe = parseRecipe(recipeText);
    const recipeId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    
    // 保存到数据库
    const query = `
      INSERT INTO recipes (id, name, ingredients, results, raw, created_at)
      VALUES (?, ?, ?, ?, ?, NOW())
    `;
    
    const params = [
      recipeId,
      name || parsedRecipe.name,
      JSON.stringify(parsedRecipe.ingredients),
      JSON.stringify(parsedRecipe.results),
      recipeText
    ];
    
    await db.execute(query, params);
    
    // 获取插入的配方
    const newRecipe = await db.fetchOne(`SELECT * FROM recipes WHERE id = ?`, [recipeId]);
    
    // 解析JSON字段
    const formattedRecipe = {
      ...newRecipe,
      ingredients: JSON.parse(newRecipe.ingredients || '[]'),
      results: JSON.parse(newRecipe.results || '[]')
    };
    
    logger.info(`添加新配方: ${formattedRecipe.name}`);
    
    // 备份到文件
    try {
      await ensureRecipesFile();
      const data = await fs.readJson(recipesFilePath);
      data.recipes.push(formattedRecipe);
      await fs.writeJson(recipesFilePath, data, { spaces: 2 });
    } catch (backupError) {
      logger.warn(`备份配方到文件失败: ${backupError.message}`);
    }
    
    res.status(201).json({
      success: true,
      message: '配方添加成功',
      recipe: formattedRecipe
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
    
    await ensureRecipesTable();
    
    // 检查配方是否存在
    const existingRecipe = await db.fetchOne(`SELECT * FROM recipes WHERE id = ?`, [id]);
    
    if (!existingRecipe) {
      return res.status(404).json({
        success: false,
        message: '配方未找到'
      });
    }
    
    // 如果提供了配方文本，则重新解析
    let parsedRecipe = null;
    if (recipeText) {
      parsedRecipe = parseRecipe(recipeText);
    }
    
    // 更新配方
    const query = `
      UPDATE recipes 
      SET 
        name = ?,
        ingredients = ?,
        results = ?,
        raw = ?
      WHERE id = ?
    `;
    
    const params = [
      name || (parsedRecipe ? parsedRecipe.name : existingRecipe.name),
      parsedRecipe ? JSON.stringify(parsedRecipe.ingredients) : existingRecipe.ingredients,
      parsedRecipe ? JSON.stringify(parsedRecipe.results) : existingRecipe.results,
      recipeText || existingRecipe.raw,
      id
    ];
    
    await db.execute(query, params);
    
    // 获取更新后的配方
    const updatedRecipe = await db.fetchOne(`SELECT * FROM recipes WHERE id = ?`, [id]);
    
    // 解析JSON字段
    const formattedRecipe = {
      ...updatedRecipe,
      ingredients: JSON.parse(updatedRecipe.ingredients || '[]'),
      results: JSON.parse(updatedRecipe.results || '[]')
    };
    
    logger.info(`更新配方: ${formattedRecipe.name}`);
    
    // 备份到文件
    try {
      await ensureRecipesFile();
      const data = await fs.readJson(recipesFilePath);
      const index = data.recipes.findIndex(r => r.id === id);
      
      if (index !== -1) {
        data.recipes[index] = formattedRecipe;
      } else {
        data.recipes.push(formattedRecipe);
      }
      
      await fs.writeJson(recipesFilePath, data, { spaces: 2 });
    } catch (backupError) {
      logger.warn(`备份配方到文件失败: ${backupError.message}`);
    }
    
    res.status(200).json({
      success: true,
      message: '配方更新成功',
      recipe: formattedRecipe
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