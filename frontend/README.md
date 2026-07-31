# CADD 本地分子对接平台 - 前端

技术栈：Vue 3 + Element Plus + Vite + Pinia + Vue Router + 3Dmol.js。

## 开发运行

```powershell
npm install
npm run dev
```

默认端口 `5173`，开发代理将 `/api` 转发到 `http://127.0.0.1:8000`。

## 生产构建

```powershell
npm run build
```

构建产物输出到 `dist/`，由本地 Web 服务或 nginx 托管，并同源代理 `/api` 到 FastAPI。

## 页面

- `/`：首页 / 新建对接任务（三栏工作台）
- `/tasks`：任务队列与历史
- `/result/:taskId`：对接结果分析
- `/settings`：软件配置与参数模板管理
- `/help`：使用说明
