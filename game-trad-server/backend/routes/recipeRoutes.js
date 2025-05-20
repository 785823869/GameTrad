const express = require('express');
const { 
  getAllRecipes, 
  getRecipeById, 
  addRecipe, 
  updateRecipe, 
  deleteRecipe 
} = require('../controllers/recipeController');

const router = express.Router();

// 获取所有配方
router.get('/', getAllRecipes);

// 获取单个配方
router.get('/:id', getRecipeById);

// 添加新配方
router.post('/', addRecipe);

// 更新配方
router.put('/:id', updateRecipe);

// 删除配方
router.delete('/:id', deleteRecipe);

module.exports = router; 