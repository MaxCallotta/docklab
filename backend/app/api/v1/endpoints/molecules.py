"""分子端点：配体/受体上传准备、PDB ID 下载。"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse

from app.chemistry.pdbqt_analysis import centroid_of_pdbqt
from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    FileNotFoundAppError,
    FileSizeExceededError,
    FileTypeInvalidError,
    LigandPrepError,
    ReceptorPrepError,
    RequestParamError,
)
from app.core.paths import get_paths
from app.core.response import ok
from app.services.molecule_service import MoleculeService
from app.utils.file_utils import sanitize_upload_filename, save_bytes

from ..deps import get_molecule_service
from ..schemas.molecule import SmilesRequest


logger = logging.getLogger("cadd.api.molecules")


router = APIRouter(prefix="/molecules", tags=["molecules"])


async def _save_upload(
    file: UploadFile,
    tmp_dir: Path,
    *,
    default_name: str,
    label: str,
) -> Path:
    """读取上传文件并落盘：校验大小、净化文件名，避免非法字符与路径穿越。"""

    data = await file.read()
    settings = get_settings()
    max_bytes = settings.upload_max_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise FileSizeExceededError(f"文件大小超过 {settings.upload_max_mb} MB 限制")
    filename = sanitize_upload_filename(file.filename, default=default_name)
    logger.info("upload_%s filename=%s size=%s", label, file.filename, len(data))
    return save_bytes(data, tmp_dir / filename)


def _dump_preprocess(result) -> dict:
    """将预处理结果转为 API 响应。"""

    def _centroid(path: Path | None) -> dict | None:
        if path is None or not path.exists():
            return None
        try:
            return centroid_of_pdbqt(path)
        except Exception:
            return None

    return {
        "input_type": result.input_type,
        "role": result.role,
        "num_molecules": result.num_molecules,
        "ligands": [
            {
                "index": lig.index,
                "name": lig.name,
                "sdf_path": str(lig.sdf_path) if lig.sdf_path else "",
                "pdbqt_path": str(lig.pdbqt_path) if lig.pdbqt_path else "",
                "smiles": lig.smiles,
                "properties": lig.properties,
                "centroid": _centroid(lig.pdbqt_path),
            }
            for lig in result.ligands
        ],
        "receptor": {
            "clean_pdb": str(result.receptor.clean_pdb_path),
            "pdbqt": str(result.receptor.pdbqt_path),
            "atom_count_before": result.receptor.atom_count_before,
            "atom_count_after": result.receptor.atom_count_after,
        }
        if result.receptor
        else None,
        "warnings": result.warnings,
    }


@router.post("/prepare-ligand")
async def prepare_ligand(
    file: UploadFile = File(...),
    service: MoleculeService = Depends(get_molecule_service),
) -> dict:
    """上传配体文件（cdxml/sdf/smiles/mol2），返回预处理结果。"""

    tmp_dir = get_paths().tmp_dir / uuid.uuid4().hex
    tmp_dir.mkdir(parents=True, exist_ok=True)
    source = await _save_upload(file, tmp_dir, default_name="ligand.cdxml", label="ligand")
    try:
        result = service.prepare_ligand(source, tmp_dir)
    except AppError:
        raise
    except Exception as exc:
        raise LigandPrepError(f"配体预处理失败：{exc}") from exc
    return ok(_dump_preprocess(result), "配体预处理完成")


@router.post("/prepare-smiles")
def prepare_smiles(
    request: SmilesRequest,
    service: MoleculeService = Depends(get_molecule_service),
) -> dict:
    """SMILES 字符串直接生成配体（RDKit/OpenBabel 自动构象与加氢）。"""

    tmp_dir = get_paths().tmp_dir / uuid.uuid4().hex
    tmp_dir.mkdir(parents=True, exist_ok=True)
    source = tmp_dir / "smiles.smi"
    source.write_text(request.smiles, encoding="utf-8")
    result = service.prepare_ligand(source, tmp_dir)
    return ok(_dump_preprocess(result), "SMILES 配体生成完成")


@router.get("/preview")
def preview_file(
    path: str = Query(..., description="Pax 数据根目录下的本地文件路径"),
) -> FileResponse:
    """安全预览 Pax 数据根目录内的结构文件（禁止越界读取）。"""

    pax_root = get_paths().root.resolve()
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(pax_root):
        raise RequestParamError("预览路径超出本地数据目录范围。")
    if resolved.suffix.lower() not in {".pdb", ".pdbqt", ".sdf", ".mol2", ".pml", ".csv"}:
        raise FileTypeInvalidError(f"不允许预览该文件类型：{resolved.suffix}")
    if not resolved.exists():
        raise FileNotFoundAppError(f"预览文件不存在：{resolved}")
    return FileResponse(resolved)


@router.post("/prepare-receptor")
async def prepare_receptor(
    pdb_id: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    service: MoleculeService = Depends(get_molecule_service),
) -> dict:
    """受体准备：PDB ID 自动下载，或上传本地 PDB/PDBQT。"""

    if pdb_id:
        work = get_paths().tmp_dir / uuid.uuid4().hex
        work.mkdir(parents=True, exist_ok=True)
        try:
            result = service.prepare_receptor_from_pdb_id(pdb_id, work)
        except AppError:
            raise
        except Exception as exc:
            raise ReceptorPrepError(f"受体预处理失败：{exc}") from exc
        return ok(_dump_preprocess(result), "受体预处理完成")

    if file is None:
        raise RequestParamError("必须提供 pdb_id 或上传 PDB/PDBQT 文件")

    tmp_dir = get_paths().tmp_dir / uuid.uuid4().hex
    tmp_dir.mkdir(parents=True, exist_ok=True)
    source = await _save_upload(file, tmp_dir, default_name="receptor.pdb", label="receptor")
    try:
        result = service.prepare_receptor_from_file(source, tmp_dir)
    except AppError:
        raise
    except Exception as exc:
        raise ReceptorPrepError(f"受体预处理失败：{exc}") from exc
    return ok(_dump_preprocess(result), "受体预处理完成")
