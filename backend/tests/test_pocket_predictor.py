"""独立口袋盒子预测工具类测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from app.chemistry.pocket_predictor import PocketPredictor, _detect_cavities


FIXTURES = Path(__file__).parent / "fixtures"


def write_pdb(path: Path, coords: list[tuple[float, float, float]]) -> None:
    """写入最小化 PDB 原子文件。"""

    lines = []
    for index, coord in enumerate(coords, start=1):
        lines.append(
            f"ATOM{index:7d}  C   REC A   1{coord[0]:12.3f}{coord[1]:8.3f}{coord[2]:8.3f}"
            f"  1.00  0.00           C"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cube_shell_coords(half: float = 10.0, step: float = 2.0) -> list[tuple[float, float, float]]:
    """生成空心立方体壳层原子坐标，内部为封闭空腔。"""

    coords: list[tuple[float, float, float]] = []
    positions = [p for p in range(-int(half), int(half) + 1, int(step))]
    for value in positions:
        for a in positions:
            for b in positions:
                coords.append((float(-half), float(a), float(b)))
                coords.append((float(half), float(a), float(b)))
                coords.append((float(a), float(-half), float(b)))
                coords.append((float(a), float(half), float(b)))
                coords.append((float(a), float(b), float(-half)))
                coords.append((float(a), float(b), float(half)))
    return coords


class PocketPredictorTest(unittest.TestCase):
    """标准 JSON 输出、空腔识别与兜底逻辑测试。"""

    def test_standard_json_output(self) -> None:
        """返回标准盒子参数 JSON。"""

        result = PocketPredictor().predict(FIXTURES / "receptor.pdb")
        for key in (
            "center_x",
            "center_y",
            "center_z",
            "size_x",
            "size_y",
            "size_z",
            "method",
            "warnings",
        ):
            self.assertIn(key, result)
        for axis in ("x", "y", "z"):
            self.assertGreaterEqual(result[f"center_{axis}"], -2000)
            self.assertLessEqual(result[f"center_{axis}"], 2000)
            self.assertGreaterEqual(result[f"size_{axis}"], 20)
            self.assertLessEqual(result[f"size_{axis}"], 200)
        self.assertIn(result["method"], {"fpocket", "geometry_cavity", "protein_center"})

    def test_hollow_cube_cavity_detection(self) -> None:
        """空心立方体应识别出中心空腔。"""

        coords = cube_shell_coords()
        cavities = _detect_cavities(np.asarray(coords, dtype=float))
        self.assertTrue(cavities)
        center = cavities[0]["center"]
        self.assertLess(float(np_max_abs(center)), 2.5)

    def test_ligand_compatible_cavity_selection(self) -> None:
        """配体位于空腔内时，输出盒心应接近配体质心。"""

        with tempfile.TemporaryDirectory(prefix="cadd_pocket_") as tmp:
            receptor = Path(tmp) / "receptor.pdb"
            ligand = Path(tmp) / "ligand.sdf"
            write_pdb(receptor, cube_shell_coords())
            ligand.write_text(
                "lig\n  RDKit\n\n  1  0  0  0  0  0  0  0  0  0999 V2000\n"
                "    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
                "M  END\n$$$$\n",
                encoding="utf-8",
            )
            result = PocketPredictor().predict(receptor, ligand)
            self.assertEqual(result["method"], "geometry_cavity")
            self.assertLess(abs(result["center_x"]), 2.5)
            self.assertLess(abs(result["center_y"]), 2.5)
            self.assertLess(abs(result["center_z"]), 2.5)

    def test_fallback_protein_center(self) -> None:
        """无明显空腔时返回蛋白几何中心 + 20 Å 标准盒。"""

        with tempfile.TemporaryDirectory(prefix="cadd_pocket_") as tmp:
            receptor = Path(tmp) / "tiny.pdb"
            write_pdb(receptor, [(1.0, 1.0, 1.0), (4.0, 1.0, 1.0), (1.0, 4.0, 1.0)])
            result = PocketPredictor().predict(receptor)
            self.assertEqual(result["method"], "protein_center")
            self.assertEqual(result["size_x"], 20.0)
            self.assertIn("未检测到明显口袋", result["warnings"][0])

    def test_fpocket_output_parser(self) -> None:
        """解析 FPocket 顶点 PDB 输出。"""

        with tempfile.TemporaryDirectory(prefix="cadd_fpocket_") as tmp:
            out_dir = Path(tmp) / "receptor_out"
            pockets_dir = out_dir / "pockets"
            pockets_dir.mkdir(parents=True)
            write_pdb(pockets_dir / "pocket1_vert.pdb", [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)])
            pockets = PocketPredictor._parse_fpocket_output(out_dir)
            self.assertEqual(len(pockets), 1)
            self.assertLess(float(abs(pockets[0]["center"][0] - 0.5)), 0.1)

    def test_fpocket_unavailable_falls_back(self) -> None:
        """FPocket 二进制不可用时自动回退，不抛错。"""

        predictor = PocketPredictor(fpocket_bin="not-exists-fpocket")
        result = predictor.predict(FIXTURES / "receptor.pdb")
        self.assertIn(result["method"], {"geometry_cavity", "protein_center"})


def np_max_abs(values) -> float:
    """返回数组各元素绝对值最大值（测试辅助）。"""

    return max(abs(float(v)) for v in values)


if __name__ == "__main__":
    unittest.main()
