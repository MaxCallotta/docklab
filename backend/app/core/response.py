"""统一 API 响应模板。

成功：{"code": 200, "msg": "操作描述", "data": 业务数据}
失败：{"code": 错误码, "msg": "科研友好提示", "error_detail": "原始异常详情"}
"""

from __future__ import annotations

from typing import Any

from app.core.constants import ErrorCode


def ok(data: Any = None, msg: str = "操作成功") -> dict[str, Any]:
    """构造统一成功响应。"""

    return {"code": ErrorCode.OK, "msg": msg, "data": data}


def fail(
    code: int,
    msg: str,
    error_detail: Any = None,
) -> dict[str, Any]:
    """构造统一失败响应。"""

    return {
        "code": code,
        "msg": msg,
        "data": None,
        "error_detail": error_detail or "",
    }
