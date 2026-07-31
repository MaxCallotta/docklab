# CADD 本地分子对接可视化科研平台

基于 Vue3 + 3Dmol.js + FastAPI + RDKit/OpenBabel 的本地分子对接平台，支持 PDB ID 下载、受体/配体文件预处理、对接盒子可视化拖拽、自动口袋预测、AutoDock Vina 对接以及 3D 结果预览。

## 功能

- 支持 PDB ID、CDXML、SDF、MOL、MOL2、SMILES 等配体输入
- 支持 PDB / PDBQT 受体输入与 PDB ID 自动下载
- 3D 画布内拖拽对接盒子中心与 8 个顶点，实时同步参数
- 一键自动预测最优口袋盒子
- AutoDock Vina / AutoDock4 对接调度
- 对接结果 3D 预览、打分表、构象导出

## 直接使用（推荐普通用户）

1. 从 GitHub Releases 下载 `CaddPlatform.exe`
2. 双击运行，程序会自动打开浏览器
3. 关闭控制台窗口即退出程序

当前 exe 为 Windows 10/11 64 位单文件版本，已内置 Python 运行环境、前端页面、RDKit、OpenBabel、AutoDock Vina 和 AutoDock4/AutoGrid4。

> 下载地址：`https://github.com/MaxCallotta/docklab/releases/latest/download/CaddPlatform.exe`

## 源码运行（开发者）

### 环境要求

- Windows 10/11 64 位
- Python 3.11
- Node.js 20+
- 源码模式需要额外安装 OpenBabel、AutoDock Vina、AutoDock4/AutoGrid4 并加入 PATH

### 前端

```powershell
cd frontend
npm install
npm run build
```

### 后端

```powershell
cd backend
pip install -r requirements.txt
cd ..
python scripts/run_app.py --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000 使用平台。

### 测试

```powershell
cd backend
python -m pytest -q
```

## 打包 exe

```powershell
python -m pip install pyinstaller
python scripts/build_standalone_windows.py
```

产物位于 `dist\CaddPlatform.exe`。

## 数据目录

- 默认数据目录：`D:\Pax_2.0`
- 可通过环境变量 `PAX_DATA_ROOT` 覆盖
- 任务、缓存、日志统一写入数据目录

## GitHub 发布

发布步骤见 [docs/GITHUB_RELEASE.md](docs/GITHUB_RELEASE.md)。
