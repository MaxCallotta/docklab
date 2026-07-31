"""最小完整 Demo：cdxml -> PDB ID 下载 -> Vina 对接 -> PML -> CSV -> ZIP。

用法：
    python scripts/demo_closed_loop.py --pdb-id 1CRN --root D:\\Pax_2.0
    python scripts/demo_closed_loop.py --open-pymol   # 额外唤起本地 PyMOL

说明：
- 测试 PDB ID 使用 1CRN（已验证 RCSB 可下载）；1ABC 在 RCSB 中不存在（HTTP 404）；
- 演示任务保留在数据根目录 tasks 下，可用 --clean 清理。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.constants import TaskStatus  # noqa: E402
from app.models.docking import DockParams  # noqa: E402
from app.services.docking_service import DockingService  # noqa: E402
from app.services.molecule_service import MoleculeService  # noqa: E402
from app.services.pymol_service import PymolService  # noqa: E402
from app.services.task_manager import TaskManager  # noqa: E402


FIXTURE_CDXML = BACKEND_DIR / "tests" / "fixtures" / "methane.cdxml"


def centroid(pdbqt: Path) -> tuple[float, float, float]:
    """读取 PDBQT 原子坐标质心，作为演示盒子中心。"""

    xs, ys, zs = [], [], []
    for line in pdbqt.read_text(encoding="utf-8", errors="replace").splitlines():
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
    """执行完整闭环演示。"""

    parser = argparse.ArgumentParser(description="CADD 平台闭环 Demo")
    parser.add_argument("--pdb-id", default="1CRN", help="RCSB PDB ID，默认 1CRN")
    parser.add_argument("--root", default=None, help="数据根目录，默认 D:\\Pax_2.0")
    parser.add_argument("--clean", action="store_true", help="演示结束后删除任务")
    parser.add_argument("--open-pymol", action="store_true", help="演示结束后唤起本地 PyMOL")
    args = parser.parse_args()

    if args.root:
        os.environ["PAX_DATA_ROOT"] = args.root

    manager = TaskManager()
    molecule_service = MoleculeService()
    docking_service = DockingService(task_manager=manager)
    pymol_service = PymolService(task_manager=manager)

    task = manager.create_task(f"closed_loop_demo_{args.pdb_id}", engine_id="vina")
    task_id = task.task_id
    task_dir = manager.task_dir(task_id)
    work_dir = task_dir / "work"

    print(f"[1/8] 创建任务：{task_id}")
    cdxml_path = manager.save_input_file(
        task_id, "methane.cdxml", FIXTURE_CDXML.read_bytes()
    )

    print("[2/8] cdxml 配体预处理 -> PDBQT")
    ligand_result = molecule_service.prepare_ligand(cdxml_path, work_dir)
    ligand_pdbqt = ligand_result.primary_path
    print(f"      配体 PDBQT：{ligand_pdbqt}")

    print(f"[3/8] 从 RCSB 下载 PDB ID {args.pdb_id} 并预处理受体")
    receptor_result = molecule_service.prepare_receptor_from_pdb_id(args.pdb_id, work_dir)
    receptor_pdbqt = receptor_result.primary_path
    assert receptor_result.receptor is not None
    print(
        f"      受体原子：{receptor_result.receptor.atom_count_before} -> "
        f"{receptor_result.receptor.atom_count_after}"
    )

    cx, cy, cz = centroid(ligand_pdbqt)
    params = DockParams(
        engine_id="vina",
        receptor_path=receptor_pdbqt,
        ligand_path=ligand_pdbqt,
        center_x=cx,
        center_y=cy,
        center_z=cz,
        size_x=30.0,
        size_y=30.0,
        size_z=30.0,
        exhaustiveness=4,
        num_modes=5,
        energy_range=3.0,
        timeout_seconds=1800,
    )

    print(f"[4/8] 提交 Vina 对接（盒子中心 {cx:.2f},{cy:.2f},{cz:.2f}）")
    result = docking_service.run_docking(task, params)
    best = result.best_pose()
    print(f"      完成，最优打分：{best.affinity if best else 'N/A'} kcal/mol")

    task = manager.get_task(task_id)
    print("[5/8] 生成 PyMOL PML 脚本")
    pml_path = pymol_service.generate_pml_for_task(
        task,
        affinity=best.affinity if best else None,
    )
    print(f"      PML：{pml_path}")

    print("[6/8] 导出打分 CSV")
    csv_path = task_dir / "output" / "scores.csv"
    print(f"      CSV：{csv_path}（{csv_path.stat().st_size} bytes）")

    print("[7/8] 打包下载全部结果")
    zip_path = manager.export_task(task_id)
    print(f"      ZIP：{zip_path}")

    if args.open_pymol:
        print("[8/8] 唤起本地 PyMOL")
        pid = pymol_service.open_in_pymol(task)
        print(f"      PyMOL 进程 PID：{pid}")
    else:
        print("[8/8] 跳过 PyMOL 唤起（使用 --open-pymol 开启）")

    summary = {
        "task_id": task_id,
        "pdb_id": args.pdb_id,
        "status": manager.get_task(task_id).status,
        "best_affinity": best.affinity if best else None,
        "pml": str(pml_path),
        "csv": str(csv_path),
        "zip": str(zip_path),
        "preview": f"http://127.0.0.1:8000/api/v1/tasks/{task_id}/files/output/docked_poses.pdbqt",
        "task_record": str(task_dir / "meta.json"),
    }
    print("\n=== 闭环演示完成 ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.clean:
        manager.delete_task(task_id)
        print("演示任务已清理。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
