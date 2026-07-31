"""配体上传接口与文件名净化测试。"""

from __future__ import annotations

import dataclasses
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.core.config import get_settings
from app.core.paths import RuntimePaths
from app.utils.file_utils import sanitize_upload_filename


FIXTURES = Path(__file__).parent / "fixtures"
OBABEL = shutil.which("obabel")


class SanitizeFilenameTest(unittest.TestCase):
    """上传文件名净化逻辑。"""

    def test_strips_path_components(self) -> None:
        self.assertEqual(sanitize_upload_filename("..\\..\\evil.cdxml"), "evil.cdxml")
        self.assertEqual(sanitize_upload_filename("C:/tmp/a/b.cdxml"), "b.cdxml")

    def test_replaces_invalid_windows_chars(self) -> None:
        self.assertEqual(sanitize_upload_filename("bad:name?.cdxml"), "bad_name_.cdxml")

    def test_empty_and_none_fall_back(self) -> None:
        self.assertEqual(sanitize_upload_filename(None, default="ligand.cdxml"), "ligand.cdxml")
        self.assertEqual(sanitize_upload_filename("", default="ligand.cdxml"), "ligand.cdxml")
        self.assertEqual(sanitize_upload_filename("...", default="ligand.cdxml"), "ligand.cdxml")


@unittest.skipUnless(
    importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
    "需要安装 fastapi/httpx",
)
@unittest.skipUnless(OBABEL, "需要安装 OpenBabel")
class LigandUploadApiTest(unittest.TestCase):
    """配体上传端点：文件名净化、大小限制与格式路由。"""

    def setUp(self) -> None:
        from fastapi.testclient import TestClient
        from app.api.v1.endpoints import molecules as molecules_endpoint
        from app.main import app

        self.app = app
        self.endpoint = molecules_endpoint
        self._tmp = tempfile.TemporaryDirectory(prefix="cadd_ligand_")
        self.tmp_root = Path(self._tmp.name) / "pax"
        self.settings = dataclasses.replace(
            get_settings(),
            pax_data_root=self.tmp_root,
            upload_max_mb=200,
        )
        self.paths = RuntimePaths.from_settings(self.settings)
        self.paths.ensure_all()

        self._patch_paths = mock.patch.object(
            self.endpoint,
            "get_paths",
            side_effect=lambda: self.paths,
        )
        self._patch_settings = mock.patch.object(
            self.endpoint,
            "get_settings",
            side_effect=lambda: self.settings,
        )
        self._patch_paths.start()
        self._patch_settings.start()

    def tearDown(self) -> None:
        self._patch_paths.stop()
        self._patch_settings.stop()
        self._tmp.cleanup()

    def _upload(self, filename: str, content: bytes) -> object:
        from fastapi.testclient import TestClient

        with TestClient(self.app) as client:
            return client.post(
                "/api/v1/molecules/prepare-ligand",
                files={"file": (filename, content, "application/octet-stream")},
            )

    def test_upload_cdxml_success(self) -> None:
        resp = self._upload("methane.cdxml", (FIXTURES / "methane.cdxml").read_bytes())
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 200)
        ligand = body["data"]["ligands"][0]
        pdbqt = Path(ligand["pdbqt_path"])
        self.assertTrue(pdbqt.exists())
        self.assertTrue(pdbqt.is_relative_to(self.tmp_root))

    def test_upload_filename_traversal_is_sanitized(self) -> None:
        resp = self._upload(
            "..\\..\\escape.cdxml",
            (FIXTURES / "methane.cdxml").read_bytes(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse((self.tmp_root / "escape.cdxml").exists())
        matches = list((self.tmp_root / "tmp").rglob("escape.cdxml"))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].parent.parent, self.tmp_root / "tmp")

    def test_upload_filename_with_invalid_windows_chars(self) -> None:
        resp = self._upload(
            "bad:name?.cdxml",
            (FIXTURES / "methane.cdxml").read_bytes(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(list((self.tmp_root / "tmp").rglob("bad_name_.cdxml")))

    def test_upload_empty_cdxml_returns_parse_error(self) -> None:
        resp = self._upload("empty.cdxml", b"")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["code"], 1001)

    def test_upload_too_large_is_rejected(self) -> None:
        self.settings = dataclasses.replace(self.settings, upload_max_mb=0)
        resp = self._upload("big.cdxml", (FIXTURES / "methane.cdxml").read_bytes())
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["code"], 3004)

    def test_upload_sdf_success(self) -> None:
        resp = self._upload("ligand.sdf", (FIXTURES / "ligand.sdf").read_bytes())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["input_type"], "sdf")

    def test_upload_smiles_file_success(self) -> None:
        resp = self._upload("ligand.smi", b"CCO\n")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["input_type"], "smiles")

    def test_upload_mol2_success(self) -> None:
        mol2 = self.tmp_root / "make.mol2"
        subprocess.run([OBABEL, "-:CCO", "-O", str(mol2)], check=True, capture_output=True)
        resp = self._upload("make.mol2", mol2.read_bytes())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["input_type"], "mol2")

    def test_upload_chinese_filename_cdxml_returns_single_ligand_with_properties(self) -> None:
        """中文文件名 cdxml 应解析为单一完整配体并返回 RDKit 属性。"""

        resp = self._upload(
            "K分子.cdxml",
            (FIXTURES / "nested_fragment.cdxml").read_bytes(),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["data"]["num_molecules"], 1)
        ligand = body["data"]["ligands"][0]
        self.assertTrue(ligand["properties"])
        self.assertGreater(ligand["properties"]["heavy_atoms"], 0)


if __name__ == "__main__":
    unittest.main()
