"""分子预处理工具箱端点测试。"""

from __future__ import annotations

import importlib.util
import tempfile
import time
import unittest
from pathlib import Path


@unittest.skipUnless(
    importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
    "需要安装 fastapi/httpx",
)
class PreprocessApiTest(unittest.TestCase):
    """上传、运行、状态与下载端点的完整流程测试。"""

    def test_upload_run_download_flow(self) -> None:
        """上传 SDF 后处理并下载结果。"""

        from fastapi.testclient import TestClient

        from app.main import app
        from app.preprocess.manager import PreprocessManager
        from app.preprocess.router import get_manager

        fixture = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "ligand.sdf"
        )

        with tempfile.TemporaryDirectory(prefix="cadd_preprocess_") as tmp:
            manager = PreprocessManager(root=Path(tmp) / "preprocess")

            def override() -> PreprocessManager:
                return manager

            app.dependency_overrides[get_manager] = override
            try:
                with TestClient(app) as client:
                    with fixture.open("rb") as fh:
                        upload = client.post(
                            "/api/preprocess/upload",
                            files=[("files", ("ligand.sdf", fh, "application/octet-stream"))],
                        )
                    self.assertEqual(upload.status_code, 200)
                    upload_data = upload.json()["data"]
                    session_id = upload_data["session_id"]
                    file_id = upload_data["files"][0]["file_id"]

                    run = client.post(
                        "/api/preprocess/run",
                        json={
                            "session_id": session_id,
                            "file_ids": [file_id],
                            "options": {
                                "add_hydrogens": True,
                                "compute_properties": True,
                                "enable_conformations": True,
                                "num_conformations": 2,
                            },
                            "output_format": "sdf",
                        },
                    )
                    self.assertEqual(run.status_code, 200)
                    batch_id = run.json()["data"]["batch_id"]

                    status = None
                    for _ in range(60):
                        status = client.get(f"/api/preprocess/status/{batch_id}").json()["data"]
                        if status["status"] == "completed":
                            break
                        time.sleep(0.2)

                    self.assertEqual(status["items"][0]["status"], "success")
                    self.assertIn("molecular_weight", status["items"][0]["properties"])

                    download = client.get(
                        f"/api/preprocess/download/{file_id}/result.sdf",
                    )
                    self.assertEqual(download.status_code, 200)

                    batch_zip = client.get(f"/api/preprocess/download/batch/{batch_id}")
                    self.assertEqual(batch_zip.status_code, 200)
            finally:
                app.dependency_overrides.clear()
