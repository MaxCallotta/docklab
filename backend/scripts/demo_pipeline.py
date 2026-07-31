"""端到端示例脚本：cdxml 配体 -> PDB 受体 -> Vina 对接 -> PML -> 任务持久化。

用法：
    python scripts/demo_pipeline.py --root D:\\Pax_2.0

说明：
- 默认使用 D:\\Pax_2.0 作为运行数据根目录；
- 未安装 Vina 时自动跳过实际对接，仅演示预处理/可视化/持久化链路。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.constants import TaskStatus  # noqa: E402
from app.core.paths import get_paths  # noqa: E402
from app.models.docking import DockParams  # noqa: E402
from app.services.docking_service import DockingService  # noqa: E402
from app.services.molecule_service import MoleculeService  # noqa: E402
from app.services.pymol_service import PymolService  # noqa: E402
from app.services.task_manager import TaskManager  # noqa: E402


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def _centroid_from_pdbqt(path: Path) -> tuple[float, float, float]:
    """从 PDBQT 原子坐标估算质心，作为演示用盒子中心。"""

    xs, ys, zs = [], [], []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                xs.append(float(line[30:38]))
                ys.append(float(line[38:46]))
                zs.append(float(line[46:54]))
            except ValueError:
                continue
    if not xs:
        return 0.0, 0.0, 0.0
    return sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)


def main() -> int:
    """运行演示流水线。"""

    parser = argparse.ArgumentParser(description="CADD 后端模块演示")
    parser.add_argument("--root", default=None, help="运行数据根目录（默认 D:\\Pax_2.0）")
    parser.add_argument("--clean", action="store_true", help="演示结束后删除演示任务")
    args = parser.parse_args()

    import os

    if args.root:
        os.environ["PAX_DATA_ROOT"] = args.root

    paths = get_paths()
    manager = TaskManager()
    molecule_service = MoleculeService()
    docking_service = DockingService(task_manager=manager)
    pymol_service = PymolService(task_manager=manager)

    task = manager.create_task("demo_cdxml_to_vina", engine_id="vina")
    task_id = task.task_id
    task_dir = manager.task_dir(task_id)
    print(f"[1/6] 创建演示任务: {task_id}")

    cdxml_path = manager.save_input_file(
        task_id, "methane.cdxml", (FIXTURES_DIR / "methane.cdxml").read_bytes()
    )
    pdb_path = manager.save_input_file(
        task_id, "receptor.pdb", (FIXTURES_DIR / "receptor.pdb").read_bytes()
    )

    work_dir = task_dir / "work"
    print("[2/6] cdxml 配体预处理 (OpenBabel + 加氢 + Gasteiger + PDBQT)")
    ligand_result = molecule_service.prepare_ligand(cdxml_path, work_dir)
    ligand_pdbqt = ligand_result.primary_path
    print(f"      配体 PDBQT: {ligand_pdbqt}")

    print("[3/6] PDB 受体预处理 (去水 + 去杂原子 + PDBQT)")
    receptor_result = molecule_service.prepare_receptor_from_file(pdb_path, work_dir)
    receptor_pdbqt = receptor_result.primary_path
    assert receptor_result.receptor is not None
    print(
        f"      受体原子 {receptor_result.receptor.atom_count_before} -> "
        f"{receptor_result.receptor.atom_count_after}"
    )

    vina_bin = shutil.which("vina")
    result = None
    if vina_bin and ligand_pdbqt and receptor_pdbqt:
        cx, cy, cz = _centroid_from_pdbqt(ligand_pdbqt)
        params = DockParams(
            engine_id="vina",
            receptor_path=receptor_pdbqt,
            ligand_path=ligand_pdbqt,
            center_x=cx,
            center_y=cy,
            center_z=cz,
            size_x=20.0,
            size_y=20.0,
            size_z=20.0,
            exhaustiveness=4,
            num_modes=5,
            energy_range=3.0,
            timeout_seconds=1800,
        )
        print(f"[4/6] Vina 对接 (盒子中心 {cx:.2f},{cy:.2f},{cz:.2f})")
        result = docking_service.run_docking(task, params)
        print(f"      完成，最优打分: {result.best_pose().affinity if result.best_pose() else 'N/A'}")
        task = manager.get_task(task_id)
    else:
        manager.update_status(
            task_id,
            TaskStatus.COMPLETED,
            result_summary={"skipped": "vina 未安装，仅演示预处理链路"},
            output_files={
                "receptor_pdbqt": str(receptor_pdbqt),
                "ligand_pdbqt": str(ligand_pdbqt),
            },
            warnings=["未检测到 Vina，跳过实际对接。"],
        )
        print("[4/6] 未检测到 Vina，跳过实际对接（其余模块继续演示）")
        task = manager.get_task(task_id)

    print("[5/6] 生成 PyMOL PML 脚本")
    pml_path = pymol_service.generate_pml_for_task(
        task,
        affinity=result.best_pose().affinity if result and result.best_pose() else None,
    )
    print(f"      PML: {pml_path}")

    print("[6/6] 打包导出全部结果")
    zip_path = manager.export_task(task_id)
    print(f"      ZIP: {zip_path}")

    summary = {
        "task_id": task_id,
        "status": manager.get_task(task_id).status,
        "pml": str(pml_path),
        "export_zip": str(zip_path),
        "best_affinity": result.best_pose().affinity if result and result.best_pose() else None,
    }
    print("\n=== 演示摘要 ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.clean:
        manager.delete_task(task_id)
        print("演示任务已清理。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
