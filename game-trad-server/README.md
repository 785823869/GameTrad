# GameTrad Server

基于Node.js的GameTrad服务器端应用，将原Python GUI功能转换为Web服务。

## 项目结构

```
game-trad-server/
├── backend/        # Node.js 后端
│   ├── controllers/ # 功能控制器
│   ├── routes/     # API路由
│   ├── utils/      # 工具函数
│   └── server.js   # 服务入口
├── frontend/       # Web前端
│   └── react/      # React前端应用
├── public/         # 静态资源
├── config/         # 配置文件
├── .env            # 环境变量
└── README.md       # 项目说明
```

## 功能模块

- **OCR图像识别**: 上传图片并返回识别结果
- **日志系统**: 记录和查看应用日志
- **路径解析**: 解析文件路径
- **配方解析**: 解析配方内容
- **更新功能**: 检查和触发在线更新

## 安装和使用

### 环境要求
- Node.js 14.x 或更高版本
- npm 6.x 或更高版本

### 安装步骤

1. 克隆仓库
```
git clone <repository-url>
cd game-trad-server
```

2. 安装依赖
```
npm install
cd frontend/react
npm install
cd ../..
```

3. 配置环境变量
```
cp .env.example .env
```
根据需要修改.env文件中的配置。

4. 启动服务
```
# 启动后端服务
npm run dev

# 启动前端服务
npm run client

# 或同时启动前后端
npm run dev:all
```

5. 访问应用
打开浏览器访问 http://localhost:3000

## API接口

- `POST /api/ocr`: 上传图片并返回OCR识别结果
- `GET /api/logs`: 获取日志列表
- `GET /api/logs/:id`: 获取指定日志详情
- `POST /api/update/check`: 检查更新
- `POST /api/update/trigger`: 触发更新
- `GET /api/recipes`: 获取配方列表
- `POST /api/recipes`: 创建新配方
- `GET /api/status`: 获取服务状态信息

## 许可证

本项目仅供学习和参考使用，版权归原作者所有。 