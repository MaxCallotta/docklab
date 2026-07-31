"""FastAPI 端点冒烟测试。"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from app.services.config_service import ConfigService
from app.services.task_manager import TaskManager


@unittest.skipUnless(
    importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
    "需要安装 fastapi/httpx",
)
class ApiSmokeTest(unittest.TestCase):
    """健康检查与任务创建端点测试。"""

    def test_health(self) -> None:
        """健康检查返回 ok。"""

        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/v1/system/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["status"], "ok")

    def test_create_task(self) -> None:
        """创建任务端点返回任务 ID。"""

        from fastapi.testclient import TestClient

        from app.main import app
        from app.api.v1.deps import get_task_manager

        with tempfile.TemporaryDirectory(prefix="cadd_api_") as tmp:
            def override() -> TaskManager:
                return TaskManager(tasks_root=Path(tmp))

            app.dependency_overrides[get_task_manager] = override
            try:
                with TestClient(app) as client:
                    response = client.post(
                        "/api/v1/tasks",
                        json={"name": "api 测试任务", "engine_id": "vina"},
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.json()["data"]["task_id"])
            finally:
                app.dependency_overrides.clear()

    def test_template_config_endpoints(self) -> None:
        """参数模板保存/查询/删除端点。"""

        from fastapi.testclient import TestClient

        from app.api.v1.deps import get_config_service
        from app.core.paths import RuntimePaths
        from app.main import app

        with tempfile.TemporaryDirectory(prefix="cadd_cfg_") as tmp:
            paths = RuntimePaths.from_settings(
                __import__("app.core.config", fromlist=["get_settings"]).get_settings()
            )
            import dataclasses

            temp_paths = dataclasses.replace(paths, root=Path(tmp), config_dir=Path(tmp) / "config")
            temp_paths.ensure_all()

            def override() -> ConfigService:
                return ConfigService(paths=temp_paths)

            app.dependency_overrides[get_config_service] = override
            try:
                with TestClient(app) as client:
                    saved = client.post(
                        "/api/v1/system/templates",
                        json={"name": "test-template", "params": {"engine_id": "vina"}},
                    )
                    self.assertEqual(saved.status_code, 200)
                    listed = client.get("/api/v1/system/templates").json()
                    self.assertEqual(listed["data"]["templates"][0]["name"], "test-template")
                    deleted = client.delete("/api/v1/system/templates/test-template")
                    self.assertEqual(deleted.status_code, 200)
            finally:
                app.dependency_overrides.clear()

    def test_logs_endpoint(self) -> None:
        """日志查看端点返回统一响应。"""

        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/v1/system/logs")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["code"], 200)
            self.assertIsInstance(response.json()["data"]["entries"], list)

    def test_docking_endpoint_converts_string_paths(self) -> None:
        """对接接口应把字符串路径转换为 Path 后再交给引擎。"""

        from fastapi.testclient import TestClient

        from app.api.v1.deps import get_docking_service, get_task_manager
        from app.models.docking import DockPose, DockResult
        from app.main import app

        captured: dict = {}

        class StubDockingService:
            def run_docking(self, task, params):
                captured["receptor"] = params.receptor_path
                captured["ligand"] = params.ligand_path
                return DockResult(
                    engine_id="vina",
                    output_path=Path("docked_poses.pdbqt"),
                    poses=[DockPose(index=1, affinity=-5.0)],
                )

        with tempfile.TemporaryDirectory(prefix="cadd_dock_") as tmp:
            manager = TaskManager(tasks_root=Path(tmp))

            def override_manager() -> TaskManager:
                return manager

            def override_docking() -> StubDockingService:
                return StubDockingService()

            app.dependency_overrides[get_task_manager] = override_manager
            app.dependency_overrides[get_docking_service] = override_docking
            try:
                with TestClient(app) as client:
                    task = manager.create_task("dock 测试", engine_id="vina")
                    response = client.post(
                        "/api/v1/docking/run",
                        json={
                            "task_id": task.task_id,
                            "engine_id": "vina",
                            "receptor_path": r"D:\tmp\receptor.pdbqt",
                            "ligand_path": r"D:\tmp\ligand.pdbqt",
                        },
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertIsInstance(captured["receptor"], Path)
                    self.assertIsInstance(captured["ligand"], Path)
            finally:
                app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
