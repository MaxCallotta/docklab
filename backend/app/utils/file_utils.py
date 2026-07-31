"""文件系统通用工具函数。"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path, PureWindowsPath
from typing import Iterator


def ensure_dir(path: Path | str) -> Path:
    """创建目录并返回 Path 对象。"""

    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


_ILLEGAL_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_upload_filename(filename: str | None, *, default: str = "upload") -> str:
    """将上传文件名规范化为安全文件名，防止路径穿越与 Windows 非法字符。"""

    if not filename:
        return default
    name = PureWindowsPath(filename.replace("\\", "/")).name.strip()
    name = _ILLEGAL_FILENAME_CHARS.sub("_", name).strip(" .")
    if not name:
        return default
    if len(name) > 200:
        stem, dot, suffix = name.partition(".")
        if dot:
            max_stem = 199 - len(suffix)
            if max_stem > 0:
                name = f"{stem[:max_stem]}{dot}{suffix}"
            else:
                name = name[:200]
        else:
            name = name[:200]
    return name


def copy_file(src: Path | str, dst: Path | str) -> Path:
    """复制文件，自动创建目标目录。"""

    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def save_bytes(data: bytes, dst: Path | str) -> Path:
    """将上传字节流保存到磁盘。"""

    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    return dst


def read_text_smart(path: Path | str) -> str:
    """智能读取文本文件，避免编码差异导致乱码。"""

    path = Path(path)
    for encoding in ("utf-8", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1", errors="replace")


def iter_sdf_records(sdf_path: Path | str) -> Iterator[str]:
    """按 $$$$ 分隔符迭代 SDF 记录，供多分子拆分使用。"""

    sdf_path = Path(sdf_path)
    current: list[str] = []
    for line in sdf_path.read_text(encoding="utf-8", errors="replace").splitlines():
        current.append(line)
        if line.strip() == "$$$$":
            yield "\n".join(current)
            current = []
    if current and any(line.strip() for line in current):
        yield "\n".join(current)


def split_sdf_records(sdf_path: Path | str, out_dir: Path | str, prefix: str = "molecule") -> list[Path]:
    """将多分子 SDF 拆分为独立文件，返回文件列表。"""

    out_dir = ensure_dir(out_dir)
    records = list(iter_sdf_records(sdf_path))
    paths: list[Path] = []
    for index, record in enumerate(records, start=1):
        dst = out_dir / f"{prefix}_{index:03d}.sdf"
        dst.write_text(record + "\n", encoding="utf-8")
        paths.append(dst)
    return paths


def make_zip(source_dir: Path | str, zip_path: Path | str) -> Path:
    """将目录压缩为 zip 文件，返回 zip 路径。"""

    source_dir, zip_path = Path(source_dir), Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(source_dir))
    return zip_path
