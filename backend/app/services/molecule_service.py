"""分子服务：配体/受体的解析与预处理编排。"""

from __future__ import annotations

from pathlib import Path

from app.chemistry.pdbid import PdbIdDownloader
from app.chemistry.prep.registry import get_preprocessor
from app.core.config import get_settings
from app.core.paths import get_paths
from app.models.molecule import PreprocessResult
from app.utils.validators import validate_extension


class MoleculeService:
    """负责将上传文件/PDB ID 转换为标准化预处理结果。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.paths = get_paths()

    def prepare_ligand(self, source: Path, work_dir: Path) -> PreprocessResult:
        """配体预处理：按后缀自动路由到对应 Preprocessor。"""

        input_type = validate_extension(source.name)
        preprocessor = get_preprocessor(input_type, "ligand")()
        return preprocessor.preprocess(source, work_dir)

    def prepare_receptor_from_file(self, source: Path, work_dir: Path) -> PreprocessResult:
        """受体预处理：PDB / PDBQT 文件。"""

        validate_extension(source.name)
        preprocessor = get_preprocessor("pdb", "receptor")()
        return preprocessor.preprocess(source, work_dir)

    def prepare_receptor_from_pdb_id(self, pdb_id: str, work_dir: Path) -> PreprocessResult:
        """受体预处理：RCSB PDB ID 下载 + 去水/去杂原子。"""

        downloader = PdbIdDownloader(self.paths.pdb_cache_dir)
        pdb_path = downloader.download(pdb_id)
        return self.prepare_receptor_from_file(pdb_path, work_dir)
