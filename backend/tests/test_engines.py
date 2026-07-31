"""对接引擎抽象与 Vina 实现测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core.exceptions import EngineNotImplementedError, EngineParamError
from app.engines.extensions.ledock import LeDockEngine
from app.engines.registry import get_engine, list_engines
from app.engines.vina import AutoDockVinaEngine
from app.models.docking import DockParams, DockResult
from app.services.pose_service import PoseService


class EngineTest(unittest.TestCase):
    """引擎注册表与参数/解析逻辑测试。"""

    def test_registry_contains_engines(self) -> None:
        """注册表应包含 vina / autodock4 / glide / ledock。"""

        ids = {item["engine_id"] for item in list_engines()}
        self.assertIn("vina", ids)
        self.assertIn("autodock4", ids)
        self.assertIn("glide", ids)
        self.assertIn("ledock", ids)

    def test_ledock_is_template(self) -> None:
        """预留引擎运行时应抛出 ENGINE_NOT_IMPLEMENTED。"""

        engine = LeDockEngine()
        with self.assertRaises(EngineNotImplementedError):
            engine.run_dock(Path("r.pdbqt"), Path("l.pdbqt"), Path("."))

    def test_vina_param_validation(self) -> None:
        """非法盒子尺寸应抛出 EngineParamError。"""

        engine = AutoDockVinaEngine()
        with tempfile.TemporaryDirectory() as tmp:
            receptor = Path(tmp) / "r.pdb"
            ligand = Path(tmp) / "l.sdf"
            receptor.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000\n")
            ligand.write_text("M  END\n")
            params = DockParams(
                engine_id="vina",
                receptor_path=receptor,
                ligand_path=ligand,
                size_x=0,
            )
            with self.assertRaises(EngineParamError):
                engine.set_params(params)

    def test_parse_result(self) -> None:
        """Vina 输出 PDBQT 打分解析。"""

        engine = AutoDockVinaEngine()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.pdbqt"
            output.write_text(
                "MODEL 1\n"
                "REMARK VINA RESULT:     -8.5      0.000      0.000\n"
                "HETATM    1  C1  LIG     1       1.000   0.000   0.000\n"
                "ENDMDL\n"
                "MODEL 2\n"
                "REMARK VINA RESULT:     -7.2      2.100      3.300\n"
                "HETATM    2  C2  LIG     1       2.000   0.000   0.000\n"
                "ENDMDL\n"
            )
            result: DockResult = engine.parse_result(output)
            self.assertEqual(len(result.poses), 2)
            self.assertAlmostEqual(result.best_pose().affinity, -8.5)

    def test_pose_extraction(self) -> None:
        """按 MODEL 提取指定构象。"""

        with tempfile.TemporaryDirectory() as tmp:
            docked = Path(tmp) / "out.pdbqt"
            docked.write_text(
                "MODEL 1\n"
                "HETATM    1  C1  LIG     1       1.000   0.000   0.000\n"
                "ENDMDL\n"
                "MODEL 2\n"
                "HETATM    2  C2  LIG     1       2.000   0.000   0.000\n"
                "ENDMDL\n"
            )
            pose = PoseService.extract_pose(docked, 2, Path(tmp) / "poses")
            text = pose.read_text(encoding="utf-8")
            self.assertIn("C2", text)
            self.assertNotIn("C1", text)


if __name__ == "__main__":
    unittest.main()
