# Development Guide

## 环境要求

- Windows 10/11 64 位
- Python 3.11+
- Node.js 20+

## 安装依赖

```powershell
python scripts/install_deps.py
```

## 前端开发

```powershell
cd frontend
npm install
npm run dev
```

默认访问 `http://localhost:5173`。

## 后端开发

```powershell
cd backend
python -m pytest -q
uvicorn app.main:app --reload --port 8000
```

## 单进程运行

```powershell
python scripts/run_app.py --host 127.0.0.1 --port 8000
```

## 打包 exe

```powershell
python -m pip install pyinstaller
python scripts/build_standalone_windows.py
```

如需内置外部引擎，将工具目录放入 `tools/`，或设置 `OPENBABEL_DIR`、`VINA_DIR`、`AUTODOCK_TOOLS_DIR`。
