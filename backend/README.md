# CADD 本地分子对接平台 - 后端代码框架

本目录实现第三阶段交付：后端完整模块化代码框架，重点覆盖四大核心模块：

1. 分子文件解析预处理模块（cdxml / PDB ID / PDB / SDF / SMILES）
2. 对接引擎抽象调度层（BaseDockEngine + AutoDock Vina + 扩展模板）
3. PyMOL 可视化生成模块（PmlGenerator + 本地 PyMOL 唤起）
4. 任务管理持久化模块（TaskManager + 本地 JSON + 打包导出）

## 快速体验

```powershell
cd backend
pip install -r requirements.txt
python scripts/check_env.py
python scripts/demo_pipeline.py
python -m pytest tests -v
```

## 运行 FastAPI 服务

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

打开 <http://127.0.0.1:8000/docs> 查看自动生成的接口文档。

## 数据目录

所有运行期数据默认写入 `D:\Pax_2.0`，可通过环境变量 `PAX_DATA_ROOT` 覆盖。
