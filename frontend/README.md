# DockLab Frontend

DockLab 前端基于 Vue 3 构建，提供分子上传、3D 可视化、对接盒子交互、任务管理与结果分析界面。

## 技术栈

- Vue 3
- Vite
- Element Plus
- Pinia
- Vue Router
- 3Dmol.js

## 开发运行

```powershell
npm install
npm run dev
```

默认端口为 `5173`，开发代理将 `/api` 请求转发到 `http://127.0.0.1:8000`。

## 生产构建

```powershell
npm run build
```

构建产物输出到 `dist/`，可由本地服务或 nginx 托管，并将 `/api` 同源代理到 FastAPI 后端。

## 页面路由

- `/`：新建对接任务
- `/tasks`：任务队列与历史
- `/result/:taskId`：对接结果分析
- `/settings`：软件配置与参数模板管理
- `/help`：使用说明

更多项目说明见 [README.md](../README.md)。
