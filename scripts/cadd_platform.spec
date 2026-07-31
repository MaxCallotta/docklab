# -*- mode: python ; coding: utf-8 -*-

"""CaddPlatform 单文件 exe 打包配置。"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all


ROOT = Path.cwd()


def _tree(source: Path, prefix: str) -> list:
    """把目录递归转成 PyInstaller data 条目。"""

    entries = []
    for item in sorted(source.rglob("*")):
        if not item.is_file():
            continue
        if "__pycache__" in item.parts:
            continue
        target_dir = Path(prefix) / item.relative_to(source).parent
        entries.append((str(item), str(target_dir)))
    return entries


datas: list = []
binaries: list = []
hiddenimports: list = []

for package_name in ("rdkit", "Bio", "uvicorn"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package_name)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

frontend_dist = ROOT / "frontend" / "dist"
backend_app = ROOT / "backend" / "app"
if frontend_dist.exists():
    datas += _tree(frontend_dist, "frontend/dist")
if backend_app.exists():
    datas += _tree(backend_app, "backend/app")
    requirements = ROOT / "backend" / "requirements.txt"
    if requirements.exists():
        datas.append((str(requirements), "backend"))

# 外部计算引擎：OpenBabel、AutoDock Vina、AutoDock4 / AutoGrid4
openbabel_root = Path(r"D:\openbabel\OpenBabel-3.1.1")
if openbabel_root.exists():
    datas += _tree(openbabel_root, "external/openbabel")

vina_root = Path(r"D:\autodock_vina")
for filename in ("vina.exe", "vina_split.exe", "vina_license.rtf"):
    source = vina_root / filename
    if source.exists():
        datas.append((str(source), "external/autodock_vina"))

autodock_root = Path(r"D:\autodock_tools")
for filename in (
    "autodock4.exe",
    "autogrid4.exe",
    "msvcp71.dll",
    "msvcr71.dll",
):
    source = autodock_root / filename
    if source.exists():
        datas.append((str(source), "external/autodock_tools"))

hiddenimports += [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "app.api.v1.router",
    "app.engines.registry",
    "app.chemistry.prep.registry",
]

a = Analysis(
    [str(ROOT / "scripts" / "server_entry.py")],
    pathex=[str(ROOT), str(ROOT / "backend")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CaddPlatform",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
