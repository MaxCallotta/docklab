"""AutoDock Vina 引擎适配器（完整实现）。"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import (
    EngineExecError,
    EngineNotFoundError,
    EngineOutputParseError,
    EngineParamError,
)
from app.models.docking import DockParams, DockPose, DockResult
from app.utils.file_utils import copy_file, ensure_dir
from app.utils.subprocess_runner import run_command

from .base import BaseDockEngine
from .registry import register_engine


@register_engine
class AutoDockVinaEngine(BaseDockEngine):
    """AutoDock Vina 1.2.x 本地对接实现。"""

    engine_id = "vina"
    engine_name = "AutoDock Vina"
    description = "AutoDock Vina 1.2 本地对接，支持 exhaustiveness / 搜索盒子 / 多构象输出"

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings)
        self._vina_bin = self.settings.engine.vina_bin or shutil.which("vina") or ""

    def _resolve_executable_path(self) -> str:
        if not self._vina_bin:
            raise EngineNotFoundError(
                "未找到 Vina 可执行程序。请安装 AutoDock Vina 并配置 VINA_BIN 环境变量。"
            )
        return self._vina_bin

    def set_params(self, params: DockParams) -> None:
        """校验并保存对接参数。"""

        if params.engine_id != self.engine_id:
            raise EngineParamError(f"参数引擎 {params.engine_id} 与当前引擎 {self.engine_id} 不一致")
        for name in ("size_x", "size_y", "size_z"):
            if float(getattr(params, name)) <= 0:
                raise EngineParamError(f"{name} 必须为正数，当前值：{getattr(params, name)}")
        if params.exhaustiveness < 1:
            raise EngineParamError("exhaustiveness 必须 >= 1")
        if params.num_modes < 1:
            raise EngineParamError("num_modes 必须 >= 1")
        if params.energy_range <= 0:
            raise EngineParamError("energy_range 必须大于 0")
        if not params.receptor_path.exists():
            raise EngineParamError(f"受体文件不存在：{params.receptor_path}")
        if not params.ligand_path.exists():
            raise EngineParamError(f"配体文件不存在：{params.ligand_path}")
        self.params = params

    def preprocess_receptor(self, receptor_path: Path, work_dir: Path) -> Path:
        """受体预处理：PDBQT 直接复用，PDB 自动去水/去杂原子后转换。"""

        prepared_dir = ensure_dir(work_dir / "prepared")
        if receptor_path.suffix.lower() == ".pdbqt":
            from app.chemistry.parsers.pdbqt_parser import PdbqtParser  # noqa: PLC0415

            PdbqtParser().parse(receptor_path)
            dst = prepared_dir / "receptor_prepared.pdbqt"
            copy_file(receptor_path, dst)
            return dst

        from app.chemistry.prep.pdb_preprocessor import PdbPreprocessor  # noqa: PLC0415

        result = PdbPreprocessor().preprocess(receptor_path, work_dir)
        if result.receptor is None or result.receptor.pdbqt_path is None:
            raise EngineExecError("受体预处理未生成 PDBQT 文件")
        return result.receptor.pdbqt_path

    def preprocess_ligand(self, ligand_path: Path, work_dir: Path) -> Path:
        """配体预处理：按输入格式路由到对应 Preprocessor。"""

        prepared_dir = ensure_dir(work_dir / "prepared")
        if ligand_path.suffix.lower() == ".pdbqt":
            from app.chemistry.parsers.pdbqt_parser import PdbqtParser  # noqa: PLC0415

            PdbqtParser().parse(ligand_path)
            dst = prepared_dir / "ligand_prepared.pdbqt"
            copy_file(ligand_path, dst)
            return dst

        from app.chemistry.prep.registry import get_preprocessor  # noqa: PLC0415
        from app.core.exceptions import FormatUnsupportedError  # noqa: PLC0415

        suffix = ligand_path.suffix.lower()
        input_type = {
            ".cdxml": "cdxml",
            ".sdf": "sdf",
            ".mol": "sdf",
            ".mol2": "sdf",
            ".txt": "smiles",
            ".smi": "smiles",
        }.get(suffix)

        if input_type is None:
            raise FormatUnsupportedError(f"不支持的配体格式：{suffix}")

        # mol/mol2 先由 OpenBabel 统一转为 SDF，再走 SDF 预处理，避免重复实现
        if input_type == "sdf" and suffix in (".mol", ".mol2"):
            from app.chemistry.converters.openbabel_converter import OpenBabelConverter  # noqa: PLC0415

            temp_sdf = prepared_dir / f"ligand_{uuid.uuid4().hex[:8]}.sdf"
            OpenBabelConverter.to_sdf(ligand_path, temp_sdf, add_h=False, gen3d=True)
            ligand_path = temp_sdf

        result = get_preprocessor(input_type, "ligand")().preprocess(ligand_path, work_dir)
        if not result.ligands or result.ligands[0].pdbqt_path is None:
            raise EngineExecError("配体预处理未生成 PDBQT 文件")
        return result.ligands[0].pdbqt_path

    def run_dock(
        self,
        receptor_pdbqt: Path,
        ligand_pdbqt: Path,
        work_dir: Path,
    ) -> Path:
        """执行 vina 对接并输出多构象 PDBQT。"""

        params = self.params
        if params is None:
            raise EngineParamError("请先调用 set_params 设置对接参数")

        output_path = work_dir / "output" / "docked_poses.pdbqt"
        ensure_dir(output_path.parent)
        command = [
            self._resolve_executable_path(),
            "--receptor", str(receptor_pdbqt),
            "--ligand", str(ligand_pdbqt),
            "--out", str(output_path),
            "--center_x", f"{params.center_x:.3f}",
            "--center_y", f"{params.center_y:.3f}",
            "--center_z", f"{params.center_z:.3f}",
            "--size_x", f"{params.size_x:.3f}",
            "--size_y", f"{params.size_y:.3f}",
            "--size_z", f"{params.size_z:.3f}",
            "--exhaustiveness", str(params.exhaustiveness),
            "--num_modes", str(params.num_modes),
            "--energy_range", f"{params.energy_range:.3f}",
        ]
        if params.seed is not None:
            command += ["--seed", str(params.seed)]
        if params.cpu is not None:
            command += ["--cpu", str(params.cpu)]

        log_path = work_dir / f"{self.engine_id}_run.log"
        result = None
        try:
            result = run_command(
                command,
                cwd=work_dir,
                timeout=params.timeout_seconds,
                friendly_name="AutoDock Vina",
            )
        except EngineExecError:
            raise
        finally:
            # 无论成功失败都保留完整日志，便于科研人员排查
            try:
                log_path.write_text(
                    "\n".join([
                        f"$ {command}",
                        "",
                        "--- stdout ---",
                        result.stdout if result is not None else "no result",
                        "",
                        "--- stderr ---",
                        result.stderr if result is not None else "no result",
                    ]),
                    encoding="utf-8",
                )
            except Exception:
                pass

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise EngineExecError("Vina 未生成对接输出文件，请检查受体/配体结构与盒子参数。")
        return output_path

    def parse_result(
        self,
        output_path: Path,
        log_path: Path | None = None,
    ) -> DockResult:
        """解析 vina 输出 PDBQT 中的 MODEL 与 VINA RESULT 打分。"""

        if not output_path.exists():
            raise EngineOutputParseError(f"对接输出文件不存在：{output_path}")

        text = output_path.read_text(encoding="utf-8", errors="replace")
        import re  # noqa: PLC0415

        remark_pattern = re.compile(
            r"REMARK\s+VINA RESULT:\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"
        )
        poses: list[DockPose] = []
        for index, match in enumerate(remark_pattern.finditer(text), start=1):
            poses.append(
                DockPose(
                    index=index,
                    affinity=float(match.group(1)),
                    rmsd_lb=float(match.group(2)),
                    rmsd_ub=float(match.group(3)),
                )
            )

        if not poses and log_path is not None and log_path.exists():
            # 部分版本打分只写入日志
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            for index, match in enumerate(remark_pattern.finditer(log_text), start=1):
                poses.append(
                    DockPose(
                        index=index,
                        affinity=float(match.group(1)),
                        rmsd_lb=float(match.group(2)),
                        rmsd_ub=float(match.group(3)),
                    )
                )

        if not poses:
            raise EngineOutputParseError(
                "无法从 Vina 输出中解析打分，请检查输出 PDBQT 是否包含 REMARK VINA RESULT 记录。"
            )

        poses.sort(key=lambda p: p.affinity)
        for index, pose in enumerate(poses, start=1):
            pose.index = index

        return DockResult(
            engine_id=self.engine_id,
            output_path=output_path,
            poses=poses,
            log_path=log_path,
        )
