"""对接参数与结果 DTO。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DockParams:
    """对接参数，覆盖 Vina/AutoDock4 等引擎的通用参数。"""

    engine_id: str
    receptor_path: Path
    ligand_path: Path
    center_x: float = 0.0
    center_y: float = 0.0
    center_z: float = 0.0
    size_x: float = 20.0
    size_y: float = 20.0
    size_z: float = 20.0
    exhaustiveness: int = 8
    num_modes: int = 9
    energy_range: float = 3.0
    seed: int | None = None
    cpu: int | None = None
    timeout_seconds: int = 7200
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转为 JSON 可序列化字典。"""

        data = {
            "engine_id": self.engine_id,
            "receptor_path": str(self.receptor_path),
            "ligand_path": str(self.ligand_path),
            "center_x": self.center_x,
            "center_y": self.center_y,
            "center_z": self.center_z,
            "size_x": self.size_x,
            "size_y": self.size_y,
            "size_z": self.size_z,
            "exhaustiveness": self.exhaustiveness,
            "num_modes": self.num_modes,
            "energy_range": self.energy_range,
            "seed": self.seed,
            "cpu": self.cpu,
            "timeout_seconds": self.timeout_seconds,
            "extra": self.extra,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DockParams":
        """从字典恢复参数对象。"""

        return cls(
            engine_id=str(data.get("engine_id", "")),
            receptor_path=Path(str(data.get("receptor_path", ""))),
            ligand_path=Path(str(data.get("ligand_path", ""))),
            center_x=float(data.get("center_x", 0.0)),
            center_y=float(data.get("center_y", 0.0)),
            center_z=float(data.get("center_z", 0.0)),
            size_x=float(data.get("size_x", 20.0)),
            size_y=float(data.get("size_y", 20.0)),
            size_z=float(data.get("size_z", 20.0)),
            exhaustiveness=int(data.get("exhaustiveness", 8)),
            num_modes=int(data.get("num_modes", 9)),
            energy_range=float(data.get("energy_range", 3.0)),
            seed=int(data["seed"]) if data.get("seed") is not None else None,
            cpu=int(data["cpu"]) if data.get("cpu") is not None else None,
            timeout_seconds=int(data.get("timeout_seconds", 7200)),
            extra=dict(data.get("extra") or {}),
        )


@dataclass
class DockPose:
    """单个对接构象。"""

    index: int
    affinity: float
    rmsd_lb: float = 0.0
    rmsd_ub: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转为 JSON 可序列化字典。"""

        return {
            "index": self.index,
            "affinity": self.affinity,
            "rmsd_lb": self.rmsd_lb,
            "rmsd_ub": self.rmsd_ub,
        }


@dataclass
class DockResult:
    """对接结果。"""

    engine_id: str
    output_path: Path
    poses: list[DockPose] = field(default_factory=list)
    log_path: Path | None = None
    score_csv: Path | None = None
    warnings: list[str] = field(default_factory=list)

    def best_pose(self) -> DockPose | None:
        """返回打分最优构象。"""

        return self.poses[0] if self.poses else None
