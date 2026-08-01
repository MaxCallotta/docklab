# 更新记录

本文档用于记录 DockLab 的模块化迭代历史，按版本号倒序排列。

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

### 新增
- 3D 对接盒子可视化拖拽与参数双向同步
  - 文件：frontend/src/components/molecule/BoxDrag.vue、MoleculeViewer3D.vue
- 自动口袋盒子预测接口与前端一键生成入口
  - 文件：backend/app/chemistry/pocket_predictor.py
  - 文件：backend/app/api/v1/endpoints/docking.py
- 单文件 exe 打包配置与 GitHub Release 发布支持
  - 文件：scripts/cadd_platform.spec、build_standalone_windows.py
- 后端补充 mol/mol2 配体预处理，前端配体上传支持 cdxml/sdf/mol/mol2/smi/txt
  - 文件：backend/app/chemistry/prep/openbabel_ligand_preprocessor.py
  - 文件：frontend/src/utils/constants.js
- 上传接口增加服务端大小限制（UPLOAD_MAX_MB）
  - 文件：backend/app/api/v1/endpoints/molecules.py
  - 文件：backend/app/core/exceptions.py
- 中英双语项目 README
  - 文件：README.md、README.en.md
- 前端中英文界面切换与 i18n 语言包
  - 文件：frontend/src/i18n/index.js、frontend/src/components/layout/AppLayout.vue
- 前端黑蓝深色科技主题，统一面板、表格、表单与 3D 预览配色
  - 文件：frontend/src/styles/index.css、frontend/src/App.vue、frontend/src/components/molecule/MoleculeViewer3D.vue
- 深空轻奢视觉细化：玻璃拟态卡片、渐变按钮、圆角输入、Tab/下拉动效、3D 盒子呼吸光效
  - 文件：frontend/src/styles/index.css、frontend/src/components/molecule/BoxDrag.vue、frontend/src/views/HomeView.vue
- 补充英文提示翻译：盒子拖拽边界限制、顶点调整尺寸、盒体移动提示
  - 文件：frontend/src/i18n/index.js
- 新增后端消息英文翻译器，覆盖预处理、对接、PDB、任务、引擎等提示
  - 文件：frontend/src/utils/backendMessages.js、frontend/src/api/http.js、frontend/src/views/HomeView.vue、frontend/src/views/ResultView.vue
- 新建任务页左侧栏加宽，右侧预览区新增悬浮式 3D 视图控制与盒子快捷操作栏
  - 文件：frontend/src/views/HomeView.vue、frontend/src/components/molecule/MoleculeViewer3D.vue、frontend/src/components/config/BoxConfigPanel.vue
- 新增独立「分子预处理工具箱」页面与 `/api/preprocess` 后端接口
  - 文件：frontend/src/views/PreprocessView.vue、frontend/src/components/preprocess/*、backend/app/preprocess/*

### 修改
- 移除代码与文档中的本机硬编码路径，数据目录默认为用户级目录
  - 文件：backend/app/core/config.py、scripts/run_app.py、README.md
- 统一版本号为 0.8.0
  - 文件：backend/app/__init__.py、frontend/package.json、frontend/package-lock.json
- 前端生产构建拆包优化，将 Vue、Element Plus、3Dmol 等依赖拆分为独立缓存块
  - 文件：frontend/vite.config.js
- README 增加专属 SVG 图标、居中标题与项目徽章
  - 文件：docs/assets/docklab-logo.svg、README.md、README.en.md
- 新增 Citation、Zenodo 元数据与推广指南
  - 文件：CITATION.cff、.zenodo.json、docs/PROMOTION.md

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

## [0.7.0] 2026-07-31

### 新增
- 最小完整 Demo 闭环脚本
  - 文件：scripts/demo_closed_loop.py
- Demo 复现文档与扩展点位总表
  - 文件：outputs/docs/06-demo-closed-loop.md

## [0.6.0] 2026-07-31

### 新增
- 部署与维护手册、跨平台启动/打包脚本
  - 文件：outputs/docs/05-deployment-maintenance.md
  - 文件：scripts/install_deps.py、run_app.py、package_app.py
- FastAPI 单进程托管前端 dist
  - 文件：backend/app/main.py

## [0.5.0] 2026-07-31

### 新增
- 统一数值响应模板与四类错误码体系
  - 文件：backend/app/core/constants.py、response.py
- 按日 JSON 日志系统与前端日志查看入口
  - 文件：backend/app/core/logging.py、frontend/src/views/SettingsView.vue

## [0.4.0] 2026-07-31

### 新增
- Vue3 + Element Plus + 3Dmol.js 包含五个页面的前端应用
  - 文件：frontend/src/views/*
- 文件预览、pose 导出、配置模板等配套接口
  - 文件：backend/app/api/v1/endpoints/*

## [0.3.0] 2026-07-31

### 新增
- 四大核心模块：分子预处理、引擎抽象、PyMOL、任务持久化
  - 文件：backend/app/chemistry、engines、visualization、services
