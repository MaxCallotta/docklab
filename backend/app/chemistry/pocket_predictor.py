"""独立口袋盒子预测工具类 PocketPredictor。

算法优先级：
1. FPocket：工业级蛋白空腔检测（需配置 FPOCKET_BIN 或加入 PATH）；
2. 内置几何空腔识别：RDKit/Biopython 解析结构 + 网格连通性分析；
3. 兜底：蛋白几何中心 + 默认 20 Å 标准盒子，不阻断用户操作。

该类与分子预处理、对接引擎模块完全隔离，替换其他口袋算法时无需
改动前后端交互代码，统一输出标准 JSON 参数。
"""

from __future__ import annotations

import logging
import math
import shutil
import subprocess
import tempfile
from collections import deque
from pathlib import Path

import numpy as np

from app.core.exceptions import RequestParamError
from app.core.paths import get_paths


CENTER_MIN = -2000.0
CENTER_MAX = 2000.0
SIZE_MIN = 20.0
SIZE_MAX = 200.0
DEFAULT_SIZE = 20.0


_POCKET_LOGGER: logging.Logger | None = None


def _pocket_logger() -> logging.Logger:
    """返回写入口袋计算日志文件的专用 Logger。"""

    global _POCKET_LOGGER
    if _POCKET_LOGGER is not None:
        return _POCKET_LOGGER
    logger = logging.getLogger("cadd.pocket")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logs_dir = get_paths().logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(logs_dir / "pocket_predictor.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    _POCKET_LOGGER = logger
    return logger


def _parse_structure(path: Path | str) -> np.ndarray:
    """从 PDB/PDBQT/SDF 中提取原子坐标数组。"""

    path = Path(path)
    if not path.exists():
        raise RequestParamError(f"结构文件不存在：{path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    coords: list[tuple[float, float, float]] = []
    suffix = path.suffix.lower()

    if suffix in {".pdb", ".ent"}:
        # 优先使用 Biopython（PDBTools 类库）解析受体结构
        try:
            from Bio.PDB import PDBParser  # noqa: PLC0415

            parser = PDBParser(QUIET=True)
            structure = parser.get_structure("receptor", str(path))
            for atom in structure.get_atoms():
                coord = atom.get_coord()
                coords.append((float(coord[0]), float(coord[1]), float(coord[2])))
            if len(coords) >= 3:
                return np.asarray(coords, dtype=float)
        except Exception:
            coords = []

    if suffix in {".pdb", ".pdbqt", ".ent"}:
        for line in text.splitlines():
            if not line.startswith(("ATOM", "HETATM")):
                continue
            try:
                coords.append(
                    (
                        float(line[30:38]),
                        float(line[38:46]),
                        float(line[46:54]),
                    )
                )
            except ValueError:
                continue
    elif suffix == ".sdf":
        lines = text.splitlines()
        index = 0
        while index < len(lines):
            if "V2000" in lines[index] or "V3000" in lines[index]:
                try:
                    atom_count = int(lines[index][:3].strip())
                except ValueError:
                    atom_count = 0
                index += 1
                for _ in range(atom_count):
                    if index >= len(lines):
                        break
                    line = lines[index]
                    try:
                        coords.append(
                            (
                                float(line[0:10]),
                                float(line[10:20]),
                                float(line[20:30]),
                            )
                        )
                    except ValueError:
                        pass
                    index += 1
                while index < len(lines) and lines[index].strip() != "$$$$":
                    index += 1
                index += 1
                continue
            index += 1
    else:
        raise RequestParamError(f"暂不支持的结构格式：{path.suffix}")

    if len(coords) < 3:
        raise RequestParamError(f"结构文件中未解析到有效原子：{path}")
    return np.asarray(coords, dtype=float)


def _detect_cavities(coords: np.ndarray, resolution: float = 1.8) -> list[dict]:
    """网格化蛋白空腔检测，返回封闭空腔列表。"""

    margin = 4.0
    mins = coords.min(axis=0) - margin
    dims = np.ceil((coords.max(axis=0) + margin - mins) / resolution).astype(int) + 1
    grid = np.zeros(tuple(int(d) for d in dims), dtype=bool)

    cell_index = np.floor((coords - mins) / resolution).astype(int)
    offsets = [
        (dx, dy, dz)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        for dz in (-1, 0, 1)
    ]
    for cx, cy, cz in cell_index:
        for dx, dy, dz in offsets:
            nx, ny, nz = int(cx + dx), int(cy + dy), int(cz + dz)
            if 0 <= nx < grid.shape[0] and 0 <= ny < grid.shape[1] and 0 <= nz < grid.shape[2]:
                grid[nx, ny, nz] = True

    free = ~grid
    visited = np.zeros(grid.shape, dtype=bool)
    neighbors = (
        (1, 0, 0),
        (-1, 0, 0),
        (0, 1, 0),
        (0, -1, 0),
        (0, 0, 1),
        (0, 0, -1),
    )

    def _flood(seed: tuple[int, int, int]) -> list[tuple[int, int, int]]:
        queue = deque([seed])
        visited[seed] = True
        cells: list[tuple[int, int, int]] = []
        while queue:
            cell = queue.popleft()
            cells.append(cell)
            for dx, dy, dz in neighbors:
                nx, ny, nz = cell[0] + dx, cell[1] + dy, cell[2] + dz
                if (
                    0 <= nx < grid.shape[0]
                    and 0 <= ny < grid.shape[1]
                    and 0 <= nz < grid.shape[2]
                    and free[nx, ny, nz]
                    and not visited[nx, ny, nz]
                ):
                    visited[nx, ny, nz] = True
                    queue.append((nx, ny, nz))
        return cells

    # 先标记与边界连通的外侧自由空间，剩余封闭连通域即为空腔
    boundary_seeds = []
    boundary = np.argwhere(free)
    for cell in boundary:
        if (
            cell[0] == 0
            or cell[1] == 0
            or cell[2] == 0
            or cell[0] == grid.shape[0] - 1
            or cell[1] == grid.shape[1] - 1
            or cell[2] == grid.shape[2] - 1
        ):
            boundary_seeds.append((int(cell[0]), int(cell[1]), int(cell[2])))
    for seed in boundary_seeds:
        if free[seed] and not visited[seed]:
            _flood(seed)

    remaining = np.argwhere(free & ~visited)
    cavities: list[dict] = []
    for cell in remaining:
        seed = (int(cell[0]), int(cell[1]), int(cell[2]))
        if visited[seed]:
            continue
        cells = _flood(seed)
        if len(cells) < 4:
            continue
        cells_array = np.asarray(cells, dtype=float)
        center = mins + (cells_array.mean(axis=0) + 0.5) * resolution
        extent = (cells_array.max(axis=0) - cells_array.min(axis=0) + 1.0) * resolution
        volume = float(len(cells)) * resolution**3
        cavities.append(
            {
                "center": center,
                "extent": extent,
                "volume": volume,
                "size_score": float(len(cells)),
            }
        )
    cavities.sort(key=lambda cavity: cavity["volume"], reverse=True)
    return cavities


class PocketPredictor:
    """蛋白结合口袋预测工具类，输出标准盒子参数。"""

    def __init__(self, fpocket_bin: str = "", grid_resolution: float = 1.8) -> None:
        self.fpocket_bin = fpocket_bin or shutil.which("fpocket") or ""
        self.grid_resolution = grid_resolution

    def predict(
        self,
        receptor_path: Path | str,
        ligand_path: Path | str | None = None,
        *,
        padding: float = 6.0,
    ) -> dict:
        """预测最优口袋盒子，返回 {center_x, center_y, center_z, size_x, size_y, size_z}。"""

        logger = _pocket_logger()
        logger.info(
            "pocket_predict_start receptor=%s ligand=%s fpocket=%s padding=%s",
            receptor_path,
            ligand_path or "-",
            self.fpocket_bin or "-",
            padding,
        )
        receptor_coords = _parse_structure(receptor_path)
        ligand_coords: np.ndarray | None = None
        ligand_extent: np.ndarray | None = None
        if ligand_path:
            try:
                ligand_coords = _parse_structure(ligand_path)
                ligand_extent = ligand_coords.max(axis=0) - ligand_coords.min(axis=0)
            except RequestParamError:
                ligand_coords = None

        warnings: list[str] = []
        if self.fpocket_bin:
            fpocket_result = self._predict_with_fpocket(
                receptor_path,
                ligand_coords=ligand_coords,
                ligand_extent=ligand_extent,
                padding=padding,
            )
            if fpocket_result is not None:
                logger.info("pocket_predict_result %s", fpocket_result)
                return fpocket_result
            warnings.append("FPocket 扫描失败，已回退到内置几何空腔识别。")

        geometry_result = self._predict_with_geometry(
            receptor_coords,
            ligand_coords=ligand_coords,
            ligand_extent=ligand_extent,
            padding=padding,
        )
        if geometry_result is not None:
            geometry_result["warnings"] = warnings
            logger.info("pocket_predict_result %s", geometry_result)
            return geometry_result

        result = self._fallback_center(receptor_coords, warnings)
        logger.info("pocket_predict_result %s", result)
        return result

    def _predict_with_fpocket(
        self,
        receptor_path: Path | str,
        *,
        ligand_coords: np.ndarray | None,
        ligand_extent: np.ndarray | None,
        padding: float,
    ) -> dict | None:
        try:
            pockets = self._run_fpocket(receptor_path)
            if not pockets:
                return None
            chosen = self._select_pocket(pockets, ligand_coords, ligand_extent)
            if chosen is None:
                return None
            return self._box_from_pocket(chosen, ligand_extent, padding, method="fpocket")
        except Exception as exc:  # noqa: BLE001
            _pocket_logger().warning("fpocket_run_failed reason=%s", exc)
            return None

    def _run_fpocket(self, receptor_path: Path | str) -> list[dict]:
        """执行 FPocket 扫描并解析输出。"""

        with tempfile.TemporaryDirectory(prefix="fpocket_") as tmp:
            work = Path(tmp)
            receptor = work / "receptor.pdb"
            shutil.copy2(receptor_path, receptor)
            subprocess.run(
                [self.fpocket_bin, "-f", str(receptor)],
                cwd=work,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            _pocket_logger().info(
                "fpocket_executed bin=%s receptor=%s",
                self.fpocket_bin,
                receptor,
            )
            output_dirs = list(work.glob("*_out")) + [work]
            for output_dir in output_dirs:
                pockets = self._parse_fpocket_output(output_dir)
                if pockets:
                    return pockets
        return []

    @staticmethod
    def _parse_fpocket_output(output_dir: Path) -> list[dict]:
        """解析 FPocket 输出目录中的口袋文件。"""

        pockets_dir = output_dir / "pockets"
        if not pockets_dir.exists():
            pockets_dir = output_dir
        pockets: list[dict] = []
        for pocket_file in sorted(pockets_dir.glob("pocket*_vert.pdb")):
            coords: list[tuple[float, float, float]] = []
            for line in pocket_file.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.startswith(("ATOM", "HETATM")):
                    continue
                try:
                    coords.append(
                        (
                            float(line[30:38]),
                            float(line[38:46]),
                            float(line[46:54]),
                        )
                    )
                except ValueError:
                    continue
            if len(coords) < 4:
                continue
            coords_array = np.asarray(coords, dtype=float)
            pockets.append(
                {
                    "center": coords_array.mean(axis=0),
                    "extent": coords_array.max(axis=0) - coords_array.min(axis=0) + 2.0,
                    "volume": float(len(coords_array)),
                    "size_score": float(len(coords_array)),
                }
            )
        return pockets

    def _predict_with_geometry(
        self,
        receptor_coords: np.ndarray,
        *,
        ligand_coords: np.ndarray | None,
        ligand_extent: np.ndarray | None,
        padding: float,
    ) -> dict | None:
        cavities = _detect_cavities(receptor_coords, self.grid_resolution)
        if not cavities:
            return None
        chosen = self._select_pocket(cavities, ligand_coords, ligand_extent)
        if chosen is None:
            return None
        return self._box_from_pocket(chosen, ligand_extent, padding, method="geometry_cavity")

    @staticmethod
    def _select_pocket(
        pockets: list[dict],
        ligand_coords: np.ndarray | None,
        ligand_extent: np.ndarray | None,
    ) -> dict | None:
        if not pockets:
            return None
        if ligand_coords is None or len(ligand_coords) < 3:
            return max(pockets, key=lambda pocket: pocket["volume"])

        ligand_centroid = ligand_coords.mean(axis=0)
        candidates = pockets
        if ligand_extent is not None:
            ligand_volume = max(float(np.prod(ligand_extent)), 1.0)
            volume_matched = [
                pocket
                for pocket in pockets
                if 0.2 * ligand_volume <= pocket["volume"] <= 12.0 * ligand_volume
            ]
            if volume_matched:
                candidates = volume_matched
        return min(
            candidates,
            key=lambda pocket: float(np.linalg.norm(pocket["center"] - ligand_centroid)),
        )

    @staticmethod
    def _box_from_pocket(
        pocket: dict,
        ligand_extent: np.ndarray | None,
        padding: float,
        *,
        method: str,
    ) -> dict:
        center = np.clip(pocket["center"], CENTER_MIN, CENTER_MAX)
        size = np.clip(pocket["extent"] + 2 * padding, SIZE_MIN, SIZE_MAX)
        if ligand_extent is not None:
            size = np.maximum(size, np.clip(ligand_extent + 2 * padding, SIZE_MIN, SIZE_MAX))
        return {
            "center_x": round(float(center[0]), 2),
            "center_y": round(float(center[1]), 2),
            "center_z": round(float(center[2]), 2),
            "size_x": round(float(size[0]), 2),
            "size_y": round(float(size[1]), 2),
            "size_z": round(float(size[2]), 2),
            "method": method,
            "pocket_count": 1,
            "warnings": [],
        }

    @staticmethod
    def _fallback_center(receptor_coords: np.ndarray, warnings: list[str] | None = None) -> dict:
        warnings = list(warnings or [])
        if not warnings:
            warnings.append("未检测到明显口袋，已使用蛋白几何中心与默认 20 Å 盒子。")
        center = np.clip(receptor_coords.mean(axis=0), CENTER_MIN, CENTER_MAX)
        return {
            "center_x": round(float(center[0]), 2),
            "center_y": round(float(center[1]), 2),
            "center_z": round(float(center[2]), 2),
            "size_x": DEFAULT_SIZE,
            "size_y": DEFAULT_SIZE,
            "size_z": DEFAULT_SIZE,
            "method": "protein_center",
            "pocket_count": 0,
            "warnings": warnings,
        }
