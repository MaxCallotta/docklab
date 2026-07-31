"""本地配置与参数模板持久化服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.paths import get_paths
from app.utils.atomic_json import read_json, write_json_atomic
from app.utils.file_utils import ensure_dir


class ConfigService:
    """将软件路径、全局默认值、参数模板保存到 D:\\Pax_2.0\\config。"""

    def __init__(self, paths=None) -> None:
        self.paths = paths or get_paths()
        ensure_dir(self.paths.config_dir)

    def _settings_path(self):
        return self.paths.config_dir / "settings.json"

    def _templates_path(self):
        return self.paths.config_dir / "templates.json"

    def get_settings(self) -> dict[str, Any]:
        """读取用户配置。"""

        return read_json(self._settings_path(), default={})

    def save_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        """合并保存用户配置。"""

        current = self.get_settings()
        merged = {**current, **payload}
        write_json_atomic(self._settings_path(), merged)
        return merged

    def list_templates(self) -> list[dict[str, Any]]:
        """返回全部参数模板。"""

        data = read_json(self._templates_path(), default={"templates": []})
        return data.get("templates", [])

    def save_template(self, name: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """按名称保存/覆盖参数模板。"""

        templates = [item for item in self.list_templates() if item.get("name") != name]
        templates.append(
            {
                "name": name,
                "params": params,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        write_json_atomic(self._templates_path(), {"templates": templates})
        return templates

    def delete_template(self, name: str) -> list[dict[str, Any]]:
        """删除参数模板。"""

        templates = [item for item in self.list_templates() if item.get("name") != name]
        write_json_atomic(self._templates_path(), {"templates": templates})
        return templates
