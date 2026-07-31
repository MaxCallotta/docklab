"""TaskManager 持久化模块单元测试。"""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from app.core.constants import TaskStatus
from app.core.exceptions import TaskNotFoundError, TaskStateError
from app.services.task_manager import TaskManager


class TaskManagerTest(unittest.TestCase):
    """任务生命周期测试。"""

    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="cadd_tasks_"))
        self.manager = TaskManager(tasks_root=self.tmp_root)

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_create_and_query(self) -> None:
        """创建任务后可查询且目录完整。"""

        record = self.manager.create_task("测试任务", engine_id="vina")
        task_dir = self.manager.task_dir(record.task_id)
        for sub in ("input", "prepared", "work", "output", "export"):
            self.assertTrue((task_dir / sub).is_dir())
        self.assertEqual(self.manager.get_task(record.task_id).status, TaskStatus.QUEUED)

    def test_status_update_and_restart(self) -> None:
        """失败任务可重启。"""

        record = self.manager.create_task("失败任务")
        self.manager.update_status(
            record.task_id,
            TaskStatus.FAILED,
            error_code="MOL_PARSE_FAILED",
            error_message="解析失败",
        )
        self.assertEqual(self.manager.get_task(record.task_id).status, TaskStatus.FAILED)

        restarted = self.manager.restart_task(record.task_id)
        self.assertEqual(restarted.status, TaskStatus.QUEUED)
        self.assertEqual(restarted.error_code, "")

    def test_running_task_cannot_delete(self) -> None:
        """运行中任务禁止删除。"""

        record = self.manager.create_task("运行中")
        self.manager.update_status(record.task_id, TaskStatus.RUNNING)
        with self.assertRaises(TaskStateError):
            self.manager.delete_task(record.task_id)

    def test_export_zip_contains_meta(self) -> None:
        """打包导出包含 meta.json。"""

        record = self.manager.create_task("导出任务")
        zip_path = self.manager.export_task(record.task_id, export_dir=self.tmp_root / "exports")
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        self.assertTrue(any(name.endswith("meta.json") for name in names))

    def test_missing_task_raises(self) -> None:
        """查询不存在任务抛出统一异常。"""

        with self.assertRaises(TaskNotFoundError):
            self.manager.get_task("0" * 32)


if __name__ == "__main__":
    unittest.main()
