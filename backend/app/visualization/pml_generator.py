"""PML 脚本生成器。

标准化渲染规则：
- 蛋白：卡通（螺旋/折叠双色），透明感；
- 配体：棍状 + 按元素着色；
- 结合口袋：6A 内残基透明表面；
- 氢键：黄色虚线；
- 疏水：配体非极性原子绿色球体；
- 打分：最优构象结合能 3D 标签。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.core.exceptions import PmlGenerationError
from app.utils.file_utils import ensure_dir


@dataclass
class PmlStyle:
    """PML 渲染样式参数，可按科研团队偏好调整。"""

    protein_helix_color: str = "slate"
    protein_sheet_color: str = "palecyan"
    pocket_color: str = "gray70"
    pocket_distance: float = 6.0
    surface_transparency: float = 0.35
    cartoon_transparency: float = 0.15
    hbond_dash_color: str = "yellow"
    hydrophobic_sphere_color: str = "green"
    background_color: str = "white"
    extra_commands: list[str] = field(default_factory=list)


class PmlGenerator:
    """生成标准化 PyMOL 可视化脚本。

    EXTENSION-POINT：新增渲染规则时在 render_text() 中增加命令块，
    或扩展 PmlStyle 字段；前端 MoleculeViewer3D 同步增加对应 3Dmol 样式。
    """

    def __init__(self, style: PmlStyle | None = None) -> None:
        self.style = style or PmlStyle()

    @staticmethod
    def _pml_path(path: Path | str) -> str:
        """将路径转换为 PyMOL 可读格式（统一正斜杠 + 转义引号）。"""

        return str(path).replace("\\", "/").replace('"', '\\"')

    def render_text(
        self,
        receptor_path: Path | str,
        ligand_path: Path | str,
        affinity: float | None = None,
    ) -> str:
        """生成 PML 脚本文本。"""

        receptor = self._pml_path(receptor_path)
        ligand = self._pml_path(ligand_path)
        style = self.style

        lines = [
            f"bg_color {style.background_color}",
            "",
            f'load "{receptor}", receptor',
            f'load "{ligand}", ligand',
            "",
            "hide everything",
            "show cartoon, receptor",
            f"color {style.protein_helix_color}, receptor and ss h",
            f"color {style.protein_sheet_color}, receptor and ss s",
            f"set cartoon_transparency, {style.cartoon_transparency}",
            "",
            "show sticks, ligand",
            "util.cnc ligand",
            "",
            # 口袋：受体中距配体 6A 的残基，半透明表面
            f"select pocket, receptor within {style.pocket_distance:.1f} of ligand",
            "show surface, pocket",
            f"set surface_color, {style.pocket_color}",
            f"set transparency, {style.surface_transparency}",
            "",
            # 氢键（黄色虚线）
            "distance hbonds, ligand, pocket, mode=2",
            "hide labels, hbonds",
            f"set dash_color, {style.hbond_dash_color}",
            "set dash_width, 2.5",
            "",
            # 疏水相互作用：配体非极性原子以绿色球体突出
            "select hydroph, ligand and not (elem O or elem N or elem S)",
            "show spheres, hydroph",
            "set sphere_scale, 0.18, hydroph",
            f"color {style.hydrophobic_sphere_color}, hydroph",
        ]

        if affinity is not None:
            lines += [
                "",
                f'label ligand, "Best pose  affinity = {affinity:.2f} kcal/mol"',
                "set label_color, black",
                "set label_size, 18",
            ]

        lines += ["", "zoom ligand", "orient"]
        lines += style.extra_commands
        return "\n".join(lines)

    def export_pml(
        self,
        receptor_path: Path | str,
        ligand_path: Path | str,
        output_path: Path | str,
        affinity: float | None = None,
    ) -> Path:
        """生成 .pml 文件并返回路径。"""

        output_path = Path(output_path)
        ensure_dir(output_path.parent)
        try:
            text = self.render_text(receptor_path, ligand_path, affinity)
            output_path.write_text(text, encoding="utf-8")
        except Exception as exc:
            raise PmlGenerationError(f"PML 脚本生成失败：{exc}") from exc
        return output_path
