# 更新记录

本文件用于追溯每次模块化迭代。新增功能必须同步更新本文件并列出涉及文件。

## 模板

```markdown
## [版本号] 日期

### 新增
- 模块描述
  - 文件：路径

### 修改
- 模块描述
  - 文件：路径

### 修复
- 问题描述
  - 文件：路径
```

## [0.8.0] 2026-07-31

### 修复
- 上传文件名含非法字符或路径穿越时返回 500：增加文件名净化与统一友好错误
  - 文件：backend/app/utils/file_utils.py
  - 文件：backend/app/api/v1/endpoints/molecules.py
- OpenBabel 转换失败被包装成 500 对接引擎错误：改为 400 分子解析错误
  - 文件：backend/app/chemistry/converters/openbabel_converter.py
- 前端上传失败后文件残留导致无法重试：失败自动清空、超过数量限制时直接替换文件
  - 文件：frontend/src/components/common/FileUpload.vue
  - 文件：frontend/src/views/HomeView.vue
- 3D 预览渲染时 getModelCount 报错：改用模型序号设置样式
  - 文件：frontend/src/components/molecule/MoleculeViewer3D.vue

### 新增
- 后端补充 mol/mol2 配体预处理，前端配体上传支持 cdxml/sdf/mol/mol2/smi/txt
  - 文件：backend/app/chemistry/prep/openbabel_ligand_preprocessor.py
  - 文件：frontend/src/utils/constants.js
- 上传接口增加服务端大小限制（UPLOAD_MAX_MB）
  - 文件：backend/app/api/v1/endpoints/molecules.py
  - 文件：backend/app/core/exceptions.py

## [0.6.0] 2026-07-31

### 新增
- 部署与维护手册、跨平台启动/打包脚本
  - 文件：outputs/docs/05-deployment-maintenance.md
  - 文件：scripts/install_deps.py、run_app.py、package_app.py
- FastAPI 单进程托管前端 dist
  - 文件：backend/app/main.py

## [0.7.0] 2026-07-31

### 新增
- 最小完整 Demo 闭环脚本
  - 文件：scripts/demo_closed_loop.py
- Demo 复现文档与扩展点位总表
  - 文件：outputs/docs/06-demo-closed-loop.md

## [0.5.0] 2026-07-31

### 新增
- 统一数值响应模板与四类错误码体系
  - 文件：backend/app/core/constants.py、response.py
- 按日 JSON 日志系统与前端日志查看入口
  - 文件：backend/app/core/logging.py、frontend/src/views/SettingsView.vue

## [0.4.0] 2026-07-31

### 新增
- Vue3 + Element Plus + 3Dmol.js 五页面前端
  - 文件：frontend/src/views/*
- 文件预览、pose 导出、配置模板等配套接口
  - 文件：backend/app/api/v1/endpoints/*

## [0.3.0] 2026-07-31

### 新增
- 四大核心模块：分子预处理、引擎抽象、PyMOL、任务持久化
  - 文件：backend/app/chemistry、engines、visualization、services
