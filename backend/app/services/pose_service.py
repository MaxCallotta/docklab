"""构象提取与格式导出服务。"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import EngineOutputParseError
from app.utils.file_utils import ensure_dir

from ..chemistry.converters.openbabel_converter import OpenBabelConverter


class PoseService:
    """从对接输出 PDBQT 中按 MODEL 提取指定构象。"""

    @staticmethod
    def extract_pose(docked_pdbqt: Path, pose_index: int, out_dir: Path) -> Path:
        """提取 pose_index 对应的 MODEL 块并写入文件。"""

        ensure_dir(out_dir)
        text = docked_pdbqt.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        target = f"MODEL {pose_index}"

        start = None
        for i, line in enumerate(lines):
            if line.strip() == target:
                start = i
                break
        if start is None:
            raise EngineOutputParseError(f"输出中不存在构象 {pose_index}。")

        block: list[str] = []
        for line in lines[start + 1 :]:
            if line.strip().startswith("ENDMDL"):
                block.append("ENDMDL")
                break
            block.append(line)
        if not block:
            raise EngineOutputParseError(f"构象 {pose_index} 内容为空。")

        output = out_dir / f"pose_{pose_index:03d}.pdbqt"
        output.write_text("\n".join(block) + "\n", encoding="utf-8")
        return output

    @staticmethod
    def convert_pose(pose_pdbqt: Path, target_format: str, out_dir: Path) -> Path:
        """将 PDBQT 构象转换为 pdb/sdf/mol2（通过 OpenBabel）。"""

        ensure_dir(out_dir)
        output = out_dir / f"{pose_pdbqt.stem}.{target_format}"
        OpenBabelConverter.convert(pose_pdbqt, output)
        return output
