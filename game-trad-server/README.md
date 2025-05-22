# GameTrad Server (游戏交易辅助工具服务端)

GameTrad Server 是一个基于Node.js构建的Web服务端应用，旨在将原有的桌面端应用的各项功能模块化、服务化，并通过Web界面提供更便捷的操作体验。它集成了图像识别(OCR)、数据管理、市场价格追踪、库存管理等多种功能，为游戏商人提供数据支持和效率工具。

## 主要功能

*   **市场价格追踪**:
    *   从DD373、7881等平台获取指定游戏的银两、女娲石等物品的实时价格。
    *   存储历史价格数据，并按15分钟等周期展示最低价格。
    *   提供价格走势图表展示。
*   **OCR图像识别**:
    *   上传游戏截图（如背包、摊位、聊天记录等）。
    *   通过OCR技术识别图片中的文字信息，辅助快速录入。
    *   支持自定义OCR识别规则以提高特定场景的识别准确率。
*   **库存管理 (简易版)**:
    *   记录物品的入库和出库信息。
    *   查看当前库存列表和交易历史。
*   **配方解析**: (待详细定义)
    *   解析游戏内物品合成配方。
*   **日志系统**:
    *   记录应用运行日志、API请求日志、错误日志等。
    *   提供日志查看界面。
*   **数据备份与恢复**: (部分实现)
    *   支持备份关键数据（如价格历史、OCR规则等）。
*   **前端界面**:
    *   使用React构建的现代化、响应式用户界面。
    *   提供数据可视化图表。
    *   统一的UI/UX体验。

## 技术栈

### 后端 (Backend)

*   **Node.js**: JavaScript 运行时环境。
*   **Express.js**: Web应用框架，用于构建API和路由。
*   **Socket.IO**: 实现实时双向通信，例如价格更新推送。
*   **Cheerio**: 用于解析HTML，辅助从网页抓取数据。
*   **Axios**: 基于Promise的HTTP客户端，用于向第三方API发送请求。
*   **Winston**: 多传输、异步日志库。
*   **fs-extra**: 增强版的文件系统操作模块。
*   **dotenv**: 用于加载环境变量。
*   **multer**: 处理 `multipart/form-data` 类型的表单数据，主要用于文件上传。
*   **Tesseract.js**: JavaScript OCR库。
*   **mysql2**: MySQL数据库驱动。
*   **lowdb/jsonfile**: 轻量级JSON文件数据库，用于存储临时或少量持久化数据（如价格历史）。

### 前端 (Frontend)

*   **React**: 用于构建用户界面的JavaScript库。
*   **React Router**: 实现前端路由。
*   **Material-UI (MUI)**: React UI框架，提供美观的组件和样式。
*   **Recharts**: React图表库，用于数据可视化。
*   **Axios**: 用于从前端向后端API发送请求。
*   **Socket.IO Client**: 用于与后端Socket.IO服务建立连接。

### 开发与构建工具

*   **npm**: Node.js包管理器。
*   **Nodemon**: 开发时自动重启Node.js应用的工具。
*   **Concurrently**: 同时运行多个npm脚本的工具。
*   **Cross-env**: 跨平台设置环境变量。
*   **ESLint**: JavaScript代码检查工具。
*   **React Scripts**: Create React App提供的脚本，用于启动、构建和测试React应用。

## 项目结构

```
game-trad-server/
├── backend/                  # Node.js 后端代码
│   ├── controllers/          # 业务逻辑控制器 (例如: statusController.js, ocrController.js)
│   ├── routes/               # API 路由定义 (例如: statusRoutes.js, ocrRoutes.js)
│   ├── utils/                # 工具函数 (例如: logger.js, dbHelper.js)
│   ├── migrations/           # 数据库迁移脚本 (如果需要)
│   ├── temp/                 # 临时文件存储 (例如: silver_7881_history.json)
│   └── server.js             # Express 服务入口文件
├── frontend/                 # Web 前端代码
│   └── react/                # React 应用
│       ├── public/           # React 应用的公共静态资源 (例如: index.html, favicons)
│       ├── src/              # React 应用源码
│       │   ├── assets/       # 静态资源 (图片, 字体等)
│       │   ├── components/   # 可复用UI组件
│       │   ├── contexts/     # React Context
│       │   ├── hooks/        # 自定义React Hooks
│       │   ├── layouts/      # 页面布局组件
│       │   ├── pages/        # 页面级组件 (例如: Dashboard.js, SilverPrice.js, NvwaPrice.js)
│       │   ├── services/     # API服务调用封装
│       │   ├── styles/       # 全局样式或主题
│       │   ├── utils/        # 前端工具函数
│       │   ├── App.js        # React 应用根组件
│       │   ├── index.js      # React 应用入口
│       │   └── reportWebVitals.js
│       ├── .env              # 前端环境变量 (例如: GENERATE_SOURCEMAP=false)
│       ├── package.json      # 前端依赖和脚本
│       └── build/            # React 应用生产构建输出目录 (由 npm run build 生成)
├── public/                   # 后端 Express 应用的顶层公共静态资源 (如果需要)
├── uploads/                  # OCR等功能上传文件的存储目录 (由后端创建和使用)
├── logs/                     # 后端日志文件存储目录 (由后端创建和使用)
├── .env                      # 后端环境变量 (例如: NODE_ENV, PORT)
├── .gitignore                # Git忽略配置
├── package.json              # 项目根目录的 package.json (主要用于后端依赖和整体项目脚本)
└── README.md                 # 项目说明文档
```

## 开发环境部署与运行

### 环境要求

*   Node.js (推荐 v16.x 或 v18.x 或更高版本，与1Panel Node.js运行环境兼容)
*   npm (通常随Node.js一同安装)

### 安装步骤

1.  **克隆仓库**:
    ```bash
    git clone <repository-url>
    cd game-trad-server
    ```

2.  **安装后端依赖**:
    在项目根目录 `game-trad-server/` 下运行：
    ```bash
    npm install
    ```

3.  **安装前端依赖**:
    进入前端目录 `game-trad-server/frontend/react/` 并安装依赖：
    ```bash
    cd frontend/react
    npm install
    cd ../.. 
    ```

4.  **配置后端环境变量**:
    在项目根目录 `game-trad-server/` 下，复制 `.env.example` (如果提供) 或手动创建 `.env` 文件。至少应包含：
    ```env
    NODE_ENV=development
    PORT=5000
    # 根据需要添加数据库连接信息、API密钥等
    # DB_HOST=localhost
    # DB_USER=root
    # DB_PASSWORD=secret
    # DB_NAME=gametrad
    ```

5.  **配置前端环境变量** (可选，用于本地开发关闭SourceMap):
    在 `game-trad-server/frontend/react/` 目录下创建 `.env` 文件：
    ```env
    GENERATE_SOURCEMAP=false
    ```

### 启动服务 (本地开发)

*   **启动后端服务 (开发模式，带自动重启)**:
    在项目根目录 `game-trad-server/` 下运行：
    ```bash
    npm run server:dev 
    ```
    后端服务通常运行在 `http://localhost:5000`。

*   **启动前端开发服务**:
    在项目根目录 `game-trad-server/` 下运行 (会自动进入 `frontend/react` 目录执行)：
    ```bash
    npm run client:dev
    ```
    前端开发服务通常运行在 `http://localhost:3000` 并代理API请求到后端。

*   **同时启动前后端 (推荐)**:
    在项目根目录 `game-trad-server/` 下运行：
    ```bash
    npm run dev
    ```

## 生产环境部署 (使用1Panel)

以下是在1Panel上部署GameTrad Server的详细步骤：

### 1. 准备源代码

*   确保你的项目代码已经提交到Git仓库 (如 GitHub, Gitee)。
*   或者，将整个 `game-trad-server` 项目文件夹（包含后端和已构建的前端）打包成 `.zip` 文件。

### 2. 服务器环境准备

*   在1Panel中，确保你已经安装了合适的 **Node.js运行环境** (例如 v18.x 或 v20.x)。
    *   路径: `1Panel -> 应用 -> 运行环境 -> 添加运行环境`。

### 3. 构建前端静态文件 (关键步骤)

在将代码部署到服务器 **之前**，或者在服务器上获取代码之后执行此步骤。

*   进入前端目录:
    ```bash
    cd game-trad-server/frontend/react
    ```
*   **安装前端依赖 (如果服务器是全新环境)**:
    ```bash
    npm install 
    ```
*   **执行构建命令**:
    ```bash
    npm run build
    ```
    这会在 `game-trad-server/frontend/react/` 目录下生成一个 `build` 文件夹，其中包含了所有生产环境所需的前端静态文件。后端服务将配置为从这里提供文件。

### 4. 上传代码到服务器

*   **通过Git**:
    *   在1Panel的 `应用 -> 应用商店` 中，可以找到并安装 "Git" 或 "Gitea" 等工具来拉取代码。
    *   或者直接在服务器终端中使用 `git clone`。将代码克隆到1Panel应用通常期望的目录，例如 `/opt/1panel/apps/你的应用名/game-trad-server/`。
*   **通过文件上传**:
    *   将打包好的 `.zip` 文件上传到服务器的目标路径 (例如 `/opt/1panel/apps/你的应用名/`) 并解压。确保解压后的目录结构是 `.../你的应用名/game-trad-server/`。

### 5. 在1Panel中创建Node.js应用

1.  **进入1Panel面板。**
2.  **导航到 `应用 -> 应用列表 -> 创建应用`。**
3.  **选择 `Node.js 项目` (或类似的名称)。**
4.  **填写应用信息**:
    *   **名称**: 例如 `GameTrad` 或 `game-trad-server`。
    *   **运行目录 (源码目录)**: 指向你服务器上 `game-trad-server` 项目的 **根目录** (即包含 `backend`、`frontend`、`package.json` 的那一层)。例如: `/opt/1panel/apps/GameTrad/game-trad-server`。
    *   **Node.js 版本**: 选择与你项目兼容且之前已安装的Node.js版本 (例如 20.10.0)。
    *   **启动命令**: 设置为 `npm start`。
        *   *解释*: 我们已经在项目根目录的 `package.json` 的 `scripts.start` 中配置了 `NODE_ENV=production node backend/server.js`，所以这里直接用 `npm start` 即可。
    *   **安装依赖命令**: 可以留空，或填写 `npm install --production`。建议在部署前或通过SSH手动在项目根目录运行 `npm install --production` 以确保只安装生产依赖。
    *   **端口**: 填写后端服务监听的端口，默认为 `5000` (与 `backend/server.js` 和根目录 `.env` 文件中的 `PORT` 配置一致)。1Panel会自动处理端口映射。
    *   **CPU/内存限制**: 根据服务器资源配置。
    *   **环境变量**:
        *   **关键**: 确保 `NODE_ENV` 环境变量被设置为 `production`。由于我们已将其包含在 `npm start` 脚本中，这里通常不需要额外添加。但如果遇到问题，可以尝试在此处显式添加：
            *   变量名: `NODE_ENV`
            *   变量值: `production`
        *   根据需要添加其他环境变量，例如数据库连接信息 (如果 `.env` 文件因安全原因未上传到服务器)。

5.  **确认并创建应用。**

### 6. 配置反向代理 (可选但推荐)

为了使用域名访问，并可能启用HTTPS：

1.  **在1Panel中导航到 `网站 -> 网站列表 -> 创建网站`。**
2.  **选择 `反向代理` 类型。**
3.  **主域名**: 输入你希望用于访问应用的域名 (例如 `gametrad.yourdomain.com`)。
4.  **目标URL**: 填写 `http://127.0.0.1:5000` (其中 `5000` 是你在Node.js应用中设置的端口)。
5.  **根据需要配置SSL证书 (HTTPS)。**
6.  **保存配置。**

### 7. 确认 `.env` 文件

*   确保在服务器上 `game-trad-server` 的根目录下存在 `.env` 文件，并且其内容正确，至少包含：
    ```env
    NODE_ENV=production
    PORT=5000 
    # 以及任何生产环境所需的数据库连接等敏感信息
    ```
    **注意**: 如果你担心将包含敏感信息的 `.env` 文件提交到Git仓库，推荐的做法是在部署到服务器后，在服务器上**手动创建或复制**这个 `.env` 文件到项目根目录。1Panel的Node.js运行环境通常会加载项目根目录下的 `.env` 文件。

### 8. 启动与日志检查

*   在1Panel中启动你的Node.js应用。
*   查看应用日志，确保 `NODE_ENV` 被识别为 `production`，并且没有启动错误。
    ```
    [DEBUG] Current NODE_ENV: production
    Server running on port 5000
    INFO: 服务器启动成功，监听端口 5000
    INFO: 数据库连接成功
    ```
*   通过配置的域名或 `服务器IP:映射端口` 访问应用。

## API 接口 (部分列表，待完善)

所有API路径以 `/api` 开头。

### 状态与价格

*   `GET /api/status/server-status`: 获取服务器基本状态和时间。
*   `GET /api/status/silver-price?range=<range>&server=<server>`: 获取银两价格。
    *   `range`: `day`, `week`, `month`, `year`
    *   `server`: `DD373`, `7881`, `all`
*   `GET /api/status/nvwa-price?range=<range>&server=<server>`: 获取女娲石价格。
    *   `range`: `day`, `week`, `month`, `year`
    *   `server`: `DD373`, `7881`, `all`

### OCR

*   `POST /api/ocr/upload`: 上传图片进行OCR识别。
    *   请求体: `multipart/form-data`，包含名为 `image` 的文件。
*   `GET /api/ocr-rules`: 获取OCR识别规则列表。
*   `POST /api/ocr-rules`: 创建新的OCR识别规则。
*   `PUT /api/ocr-rules/:id`: 更新指定的OCR识别规则。
*   `DELETE /api/ocr-rules/:id`: 删除指定的OCR识别规则。

### 库存 (示例)

*   `GET /api/inventory`: 获取库存列表。
*   `POST /api/stock-in`: 添加入库记录。
*   `POST /api/stock-out`: 添加出库记录。
*   `GET /api/transactions`: 获取交易记录。

### 日志

*   `GET /api/logs`: 获取日志条目。
*   `GET /api/logs/clear`: 清除日志。

### 配方 (示例)

*   `GET /api/recipes`: 获取配方列表。
*   `POST /api/recipes`: 创建新配方。

### 其他

*   `GET /api/backup/settings`: 获取备份设置。
*   `POST /api/backup/trigger`: 触发备份。
*   `GET /api/settings/email`: 获取邮件配置。
*   `POST /api/settings/email`: 更新邮件配置。

## 注意事项与未来展望

*   **安全性**: 对于生产环境，务必考虑API的安全性，例如输入验证、身份认证、权限控制等。
*   **数据库**: 当前价格历史等数据存储在JSON文件中，对于大规模或高并发场景，建议迁移到更专业的数据库系统（如MySQL, PostgreSQL, MongoDB）。项目中已包含 `mysql2` 依赖，可以作为后续扩展方向。
*   **错误处理**: 进一步完善全局错误处理和API响应格式。
*   **测试**: 添加单元测试和集成测试以保证代码质量。
*   **模块完善**: 细化并完善库存管理、配方解析等模块的功能。

## 许可证

本项目仅供学习和参考使用。 