"""分子预处理工具箱核心管理器。

本模块与对接引擎、任务调度完全解耦，负责：
- 上传文件会话管理
- 批次并发处理调度
- 单分子状态与结果持久化
- 结果文件下载与批量打包
- 过期临时数据自动清理
"""

from __future__ import annotations

import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from filelock import FileLock

from app.chemistry.converters.openbabel_converter import OpenBabelConverter
from app.chemistry.converters.rdkit_converter import RdkItConverter
from app.core.config import get_settings
from app.core.paths import get_paths
from app.utils.atomic_json import read_json, write_json_atomic
from app.utils.file_utils import ensure_dir, make_zip, sanitize_upload_filename


ALLOWED_PREPROCESS_EXTENSIONS = {
    ".cdxml": "cdxml",
    ".sdf": "sdf",
    ".mol2": "mol2",
    ".smi": "smiles",
    ".txt": "smiles",
    ".pdbqt": "pdbqt",
}

OUTPUT_FORMATS = {"cdxml", "sdf", "mol2", "pdbqt", "smi"}


class PreprocessManager:
    """无状态管理器，通过本地 JSON 元数据维护会话与批次。"""

    def __init__(self, root: Path | None = None) -> None:
        self.root = ensure_dir(root or get_paths().preprocess_dir)
        self.sessions_dir = ensure_dir(self.root / "sessions")
        self.batches_dir = ensure_dir(self.root / "batches")
        self._cleanup_expired()

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def _batch_path(self, batch_id: str) -> Path:
        return self.batches_dir / f"{batch_id}.json"

    def _cleanup_expired(self) -> None:
        """删除超过配置保留时长的本地临时数据。"""

        settings = get_settings()
        cutoff = time.time() - settings.preprocess_cleanup_hours * 3600
        for directory in (self.sessions_dir, self.batches_dir):
            for item in directory.iterdir():
                try:
                    if item.is_dir() and item.stat().st_mtime < cutoff:
                        shutil.rmtree(item, ignore_errors=True)
                    elif item.is_file() and item.stat().st_mtime < cutoff:
                        item.unlink(missing_ok=True)
                except OSError:
                    continue

    def create_session(self) -> str:
        """创建上传会话并返回 session_id。"""

        session_id = uuid.uuid4().hex
        session_dir = ensure_dir(self.sessions_dir / session_id)
        write_json_atomic(
            self._session_path(session_id),
            {"session_id": session_id, "dir": str(session_dir), "files": [], "created_at": time.time()},
        )
        return session_id

    def add_file(self, session_id: str, filename: str, data: bytes) -> dict[str, Any]:
        """保存单个上传文件并登记到会话元数据。"""

        session = self._read_session(session_id)
        safe_name = sanitize_upload_filename(filename, default="molecule.sdf")
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_PREPROCESS_EXTENSIONS:
            from app.core.exceptions import FileTypeInvalidError
            raise FileTypeInvalidError(f"不允许预处理该文件类型：{suffix}")

        file_id = uuid.uuid4().hex
        session_dir = Path(session["dir"])
        source_path = session_dir / f"{file_id}{suffix}"
        source_path.write_bytes(data)

        record = {
            "file_id": file_id,
            "filename": safe_name,
            "format": ALLOWED_PREPROCESS_EXTENSIONS[suffix],
            "size": len(data),
            "source_path": str(source_path),
        }
        session["files"].append(record)
        self._write_session(session_id, session)
        return record

    def submit_batch(
        self,
        session_id: str,
        file_ids: list[str],
        options: dict[str, Any],
        output_format: str,
    ) -> str:
        """创建批次并异步执行处理，立即返回 batch_id。"""

        if output_format not in OUTPUT_FORMATS:
            from app.core.exceptions import RequestParamError
            raise RequestParamError(f"不支持预处理输出格式：{output_format}")

        session = self._read_session(session_id)
        files_by_id = {item["file_id"]: item for item in session["files"]}
        selected: list[dict[str, Any]] = []
        for file_id in file_ids:
            item = files_by_id.get(file_id)
            if item is None:
                from app.core.exceptions import RequestParamError
                raise RequestParamError(f"上传文件不存在：{file_id}")
            selected.append(item)

        batch_id = uuid.uuid4().hex
        batch_dir = ensure_dir(self.batches_dir / batch_id)
        output_dir = ensure_dir(batch_dir / "output")
        work_dir = ensure_dir(batch_dir / "work")
        batch = {
            "batch_id": batch_id,
            "session_id": session_id,
            "status": "running",
            "output_format": output_format,
            "options": options,
            "output_dir": str(output_dir),
            "created_at": time.time(),
            "items": [
                {
                    "file_id": item["file_id"],
                    "filename": item["filename"],
                    "format": item["format"],
                    "source_path": item["source_path"],
                    "status": "queued",
                    "output_name": "",
                    "output_path": "",
                    "properties": {},
                    "error": "",
                }
                for item in selected
            ],
        }
        write_json_atomic(self._batch_path(batch_id), batch)

        thread = threading.Thread(
            target=self._run_batch,
            args=(batch_id,),
            daemon=True,
        )
        thread.start()
        return batch_id

    def _run_batch(self, batch_id: str) -> None:
        """并发执行批次中的全部分子处理任务。"""

        batch = self._read_batch(batch_id)
        settings = get_settings()

        def process(item: dict[str, Any]) -> None:
            self._update_item(batch_id, item["file_id"], {"status": "processing"})
            try:
                output = self._process_one(batch_id, item)
                self._update_item(
                    batch_id,
                    item["file_id"],
                    {
                        "status": "success",
                        "output_name": output["name"],
                        "output_path": output["path"],
                        "properties": output["properties"],
                    },
                )
            except Exception as exc:
                self._update_item(
                    batch_id,
                    item["file_id"],
                    {"status": "failed", "error": str(exc) or exc.__class__.__name__},
                )

        with ThreadPoolExecutor(max_workers=max(1, settings.preprocess_concurrency)) as pool:
            list(pool.map(process, batch["items"]))

        batch = self._read_batch(batch_id)
        batch["status"] = "completed"
        self._write_batch(batch_id, batch)

    def _process_one(self, batch_id: str, item: dict[str, Any]) -> dict[str, Any]:
        """处理单个分子并返回输出文件信息。"""

        batch = self._read_batch(batch_id)
        options = batch.get("options", {})
        output_format = batch.get("output_format", "sdf")
        source_path = Path(item["source_path"])
        work_dir = ensure_dir(Path(batch["output_dir"]).parent / "work" / item["file_id"])

        intermediate = work_dir / "intermediate.sdf"
        OpenBabelConverter.to_sdf(
            source_path,
            intermediate,
            add_h=bool(options.get("add_hydrogens", False)),
            gen3d=True,
        )

        if options.get("remove_salts"):
            desalted = work_dir / "desalted.sdf"
            RdkItConverter.remove_salts(intermediate, desalted)
            intermediate = desalted

        if options.get("remove_duplicates"):
            deduped = work_dir / "deduped.sdf"
            RdkItConverter.remove_duplicates(intermediate, deduped)
            intermediate = deduped

        if options.get("enable_conformations"):
            settings = get_settings()
            num_confs = max(1, min(int(options.get("num_conformations", 1)), settings.preprocess_max_conformations))
            conformed = work_dir / "conformations.sdf"
            RdkItConverter.generate_conformations(intermediate, conformed, num_confs)
            intermediate = conformed

        properties: dict[str, Any] = {}
        if options.get("compute_properties"):
            properties = RdkItConverter.compute_properties(intermediate)

        output_path = Path(batch["output_dir"]) / f"{item['file_id']}.{output_format}"
        if output_format == "pdbqt":
            OpenBabelConverter.to_pdbqt_ligand(
                intermediate,
                output_path,
                ph=float(options.get("ph", 7.4)),
            )
        else:
            OpenBabelConverter.convert_with_options(
                intermediate,
                output_path,
                add_h=bool(options.get("add_hydrogens", False)),
                compute_charges=bool(options.get("compute_gasteiger", False)),
                gen3d=bool(options.get("enable_conformations", False)),
            )

        stem = Path(item["filename"]).stem
        return {
            "name": f"{stem}.{output_format}",
            "path": str(output_path),
            "properties": properties,
        }

    def status(self, batch_id: str) -> dict[str, Any]:
        """返回批次状态与每个分子的处理结果。"""

        batch = self._read_batch(batch_id)
        if batch["status"] == "running" and all(
            item["status"] in ("success", "failed") for item in batch["items"]
        ):
            batch["status"] = "completed"
            self._write_batch(batch_id, batch)
        return batch

    def resolve_download(self, file_id: str) -> Path:
        """按 file_id 查找输出文件，未处理时回退到上传源文件。"""

        for batch_path in self.batches_dir.glob("*.json"):
            batch = read_json(batch_path, default={})
            for item in batch.get("items", []):
                if item.get("file_id") == file_id and item.get("output_path"):
                    path = Path(item["output_path"])
                    if path.exists():
                        return path

        for session_path in self.sessions_dir.glob("*.json"):
            session = read_json(session_path, default={})
            for item in session.get("files", []):
                if item.get("file_id") == file_id:
                    path = Path(item["source_path"])
                    if path.exists():
                        return path

        from app.core.exceptions import FileNotFoundAppError
        raise FileNotFoundAppError(f"预处理文件不存在：{file_id}")

    def make_batch_zip(self, batch_id: str) -> Path:
        """打包批次输出目录为 zip 文件。"""

        batch = self._read_batch(batch_id)
        output_dir = Path(batch["output_dir"])
        zip_path = output_dir.parent / f"{batch_id}.zip"
        return make_zip(output_dir, zip_path)

    def _read_session(self, session_id: str) -> dict[str, Any]:
        path = self._session_path(session_id)
        data = read_json(path, default={})
        if not data:
            from app.core.exceptions import FileNotFoundAppError
            raise FileNotFoundAppError(f"上传会话不存在：{session_id}")
        return data

    def _write_session(self, session_id: str, data: dict[str, Any]) -> None:
        write_json_atomic(self._session_path(session_id), data)

    def _read_batch(self, batch_id: str) -> dict[str, Any]:
        path = self._batch_path(batch_id)
        data = read_json(path, default={})
        if not data:
            from app.core.exceptions import FileNotFoundAppError
            raise FileNotFoundAppError(f"预处理批次不存在：{batch_id}")
        return data

    def _write_batch(self, batch_id: str, data: dict[str, Any]) -> None:
        write_json_atomic(self._batch_path(batch_id), data)

    def _update_item(self, batch_id: str, file_id: str, patch: dict[str, Any]) -> None:
        """原子更新批次内单个分子的状态。"""

        path = self._batch_path(batch_id)
        lock = FileLock(f"{path}.lock")
        with lock:
            batch = read_json(path, default={})
            for item in batch.get("items", []):
                if item.get("file_id") == file_id:
                    item.update(patch)
                    break
            write_json_atomic(path, batch)
