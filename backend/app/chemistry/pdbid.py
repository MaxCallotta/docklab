"""RCSB PDB ID 处理器。

隐私边界：仅当用户显式输入 PDB ID 时，单向拉取 RCSB 公开蛋白结构；
用户上传的私有分子文件永不外发。
"""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from app.core.constants import RCSB_FILE_URL_TEMPLATE
from app.core.exceptions import PdbDownloadError
from app.utils.file_utils import ensure_dir
from app.utils.validators import validate_pdb_id


class PdbIdDownloader:
    """PDB ID -> 本地 PDB 文件下载器（带本地缓存）。"""

    def __init__(self, cache_dir: Path, timeout: int = 30) -> None:
        self.cache_dir = ensure_dir(cache_dir)
        self.timeout = timeout

    def download(self, pdb_id: str) -> Path:
        """下载并缓存 PDB 文件，返回本地路径。"""

        pdb_id = validate_pdb_id(pdb_id)
        cached = self.cache_dir / f"{pdb_id}.pdb"
        if cached.exists() and cached.stat().st_size > 0:
            return cached

        url = RCSB_FILE_URL_TEMPLATE.format(pdb_id=pdb_id.upper())
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                content = response.read()
        except urllib.error.HTTPError as exc:
            raise PdbDownloadError(
                f"RCSB 返回错误（{exc.code}）：PDB ID {pdb_id} 可能不存在。"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise PdbDownloadError(
                f"无法连接 RCSB，请检查网络。仅此操作为单向公开数据拉取，不会上传任何本地分子。"
            ) from exc

        # PDB 文件的 ATOM 记录可能出现在较长的 HEADER/REMARK 之后，检查前 2000 行
        if not content or not any(line.startswith(b"ATOM") for line in content.splitlines()[:2000]):
            raise PdbDownloadError(f"下载的 PDB 文件不包含有效原子记录：{pdb_id}")

        cached.write_bytes(content)
        return cached
