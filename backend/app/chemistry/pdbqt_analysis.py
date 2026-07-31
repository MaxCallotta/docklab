"""PDBQT 轻量几何分析工具（纯标准库）。"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import EngineOutputParseError


def centroid_of_pdbqt(path: Path) -> dict[str, float]:
    """计算 PDBQT 原子坐标质心，供前端盒子默认定位使用。"""

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                xs.append(float(line[30:38]))
                ys.append(float(line[38:46]))
                zs.append(float(line[46:54]))
            except ValueError:
                continue
    if not xs:
        raise EngineOutputParseError(f"PDBQT 无有效原子坐标：{path}")
    return {
        "x": round(sum(xs) / len(xs), 3),
        "y": round(sum(ys) / len(ys), 3),
        "z": round(sum(zs) / len(zs), 3),
    }
