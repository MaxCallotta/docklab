"""结果报表服务：打分 CSV 与结果摘要生成。"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.core.exceptions import AppError
from app.models.docking import DockPose, DockResult
from app.utils.file_utils import ensure_dir


class ReportService:
    """生成对接打分报表与结果摘要。"""

    @staticmethod
    def write_score_csv(poses: list[DockPose], output_path: Path) -> Path:
        """按排名输出打分 CSV。"""

        ensure_dir(output_path.parent)
        with open(output_path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["rank", "affinity_kcal_mol", "rmsd_lb", "rmsd_ub"])
            for index, pose in enumerate(poses, start=1):
                writer.writerow([index, pose.affinity, pose.rmsd_lb, pose.rmsd_ub])
        return output_path

    @staticmethod
    def build_result_summary(result: DockResult) -> dict[str, Any]:
        """构建任务结果摘要（供 meta.json 持久化与前端展示）。"""

        best = result.best_pose()
        return {
            "engine_id": result.engine_id,
            "num_poses": len(result.poses),
            "poses": [pose.to_dict() for pose in result.poses],
            "best_affinity": best.affinity if best else None,
            "best_rmsd_lb": best.rmsd_lb if best else None,
            "best_rmsd_ub": best.rmsd_ub if best else None,
            "output_pdbqt": str(result.output_path),
            "score_csv": str(result.score_csv) if result.score_csv else "",
            "warnings": result.warnings,
        }

    @staticmethod
    def fail_with(code: str, message: str) -> AppError:
        """构造标准化失败对象，供调度层统一写入任务记录。"""

        return AppError(message, code=code)
