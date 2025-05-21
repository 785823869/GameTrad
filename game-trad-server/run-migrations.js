/**
 * 数据库迁移运行器
 * 执行所有必要的数据库迁移
 */

const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

console.log('开始执行数据库迁移...');

// 迁移脚本目录
const migrationsDir = path.join(__dirname, 'backend', 'migrations');

// 确保迁移目录存在
if (!fs.existsSync(migrationsDir)) {
  console.log(`创建迁移目录: ${migrationsDir}`);
  fs.mkdirSync(migrationsDir, { recursive: true });
}

// 获取所有迁移脚本文件
const migrationFiles = fs.readdirSync(migrationsDir)
  .filter(file => file.endsWith('.js'))
  .sort();

if (migrationFiles.length === 0) {
  console.log('没有找到迁移脚本文件');
  process.exit(0);
}

console.log(`找到${migrationFiles.length}个迁移脚本:`);
migrationFiles.forEach(file => console.log(` - ${file}`));

// 执行迁移
let successCount = 0;
let failCount = 0;

migrationFiles.forEach(file => {
  const filePath = path.join(migrationsDir, file);
  console.log(`\n执行迁移: ${file}`);
  
  try {
    // 运行迁移脚本
    execSync(`node ${filePath}`, { stdio: 'inherit' });
    console.log(`✓ 迁移脚本 ${file} 执行成功`);
    successCount++;
  } catch (error) {
    console.error(`✗ 迁移脚本 ${file} 执行失败`);
    failCount++;
  }
});

// 输出结果摘要
console.log('\n迁移执行完成:');
console.log(`✓ 成功: ${successCount}`);
console.log(`✗ 失败: ${failCount}`);

process.exit(failCount > 0 ? 1 : 0); 