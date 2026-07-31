# DockLab Backend

DockLab 后端服务基于 FastAPI 构建，负责分子文件解析与预处理、结合口袋预测、对接引擎调度、任务持久化与可视化文件生成。

## 模块结构

| 模块 | 职责 |
| --- | --- |
| `app/chemistry` | 分子解析、格式转换、受体/配体预处理与口袋预测 |
| `app/engines` | 对接引擎抽象层与 AutoDock Vina / AutoDock4 适配 |
| `app/services` | 任务管理、对接流水线、结果导出与配置持久化 |
| `app/visualization` | PyMOL/PML 可视化脚本生成 |
| `app/api` | REST API 路由、请求模型与统一响应 |

## 快速开始

```powershell
cd backend
pip install -r requirements.txt
python scripts/check_env.py
python -m pytest -q
```

启动后端服务：

```powershell
uvicorn app.main:app --reload --port 8000
```

接口文档位于 http://127.0.0.1:8000/docs 。

也可以从项目根目录使用单进程模式：

```powershell
python scripts/run_app.py --host 127.0.0.1 --port 8000
```

## 数据目录

- 默认数据目录：`%LOCALAPPDATA%\CaddPlatform\data`
- 可通过环境变量 `PAX_DATA_ROOT` 覆盖
- 任务、缓存、日志与配置统一写入数据目录
