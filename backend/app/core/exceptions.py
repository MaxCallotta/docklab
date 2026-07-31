"""统一异常体系。

设计原则：
- 所有业务异常继承 AppError；
- AppError 携带标准化错误码、面向科研用户的友好提示、调试详情；
- API 层统一捕获并转换为 JSON 响应，前端无需解析原始终端输出。
"""

from __future__ import annotations

from typing import Any

from app.core.constants import ErrorCode


class AppError(Exception):
    """业务异常基类。"""

    code = ErrorCode.INTERNAL_ERROR
    http_status = 400

    def __init__(
        self,
        message: str = "",
        *,
        code: str | None = None,
        details: Any = None,
        http_status: int | None = None,
    ) -> None:
        self.message = message or self.__class__.__doc__ or "未知错误"
        if code is not None:
            self.code = code
        self.details = details
        if http_status is not None:
            self.http_status = http_status
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为前端可直接解析的标准失败响应结构。"""

        return {
            "code": self.code,
            "msg": self.message,
            "data": None,
            "error_detail": self.details or "",
        }


class FormatUnsupportedError(AppError):
    """不支持的文件格式。"""

    code = ErrorCode.FORMAT_UNSUPPORTED


class FileNotFoundAppError(AppError):
    """文件不存在。"""

    code = ErrorCode.FILE_NOT_FOUND


class FileTypeInvalidError(AppError):
    """文件类型校验失败。"""

    code = ErrorCode.FILE_TYPE_INVALID


class FileSizeExceededError(AppError):
    """上传文件超过大小限制。"""

    code = ErrorCode.FILE_SIZE_EXCEEDED


class MoleculeParseError(AppError):
    """分子文件解析失败（破损文件、无分子、OpenBabel 报错等）。"""

    code = ErrorCode.MOL_PARSE_FAILED


class MoleculeValidationError(AppError):
    """分子结构合法性校验失败。"""

    code = ErrorCode.MOL_VALIDATION_FAILED


class PdbDownloadError(AppError):
    """RCSB PDB 下载失败。"""

    code = ErrorCode.PDB_DOWNLOAD_FAILED


class ReceptorPrepError(AppError):
    """受体预处理失败。"""

    code = ErrorCode.RECEPTOR_PREP_FAILED


class LigandPrepError(AppError):
    """配体预处理失败。"""

    code = ErrorCode.LIGAND_PREP_FAILED


class EngineNotFoundError(AppError):
    """对接引擎可执行程序未找到或路径无效。"""

    code = ErrorCode.ENGINE_NOT_FOUND
    http_status = 500


class EngineNotImplementedError(AppError):
    """预留引擎适配器尚未实现。"""

    code = ErrorCode.ENGINE_NOT_IMPLEMENTED


class EngineParamError(AppError):
    """对接参数校验失败。"""

    code = ErrorCode.REQUEST_PARAM_INVALID


class EngineExecError(AppError):
    """对接软件进程执行失败。"""

    code = ErrorCode.ENGINE_EXEC_FAILED
    http_status = 500

    def __init__(
        self,
        message: str = "",
        *,
        command: list[str] | None = None,
        returncode: int | None = None,
        stdout: str = "",
        stderr: str = "",
        code: str | None = None,
        details: Any = None,
        http_status: int | None = None,
    ) -> None:
        self.command = command or []
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            message,
            code=code,
            details=details or {"returncode": returncode, "stderr": stderr[-2000:]},
            http_status=http_status,
        )


class EngineOutputParseError(AppError):
    """对接结果文件解析失败。"""

    code = ErrorCode.ENGINE_OUTPUT_PARSE_FAILED


class TaskNotFoundError(AppError):
    """任务不存在。"""

    code = ErrorCode.TASK_NOT_FOUND
    http_status = 404


class TaskStateError(AppError):
    """任务状态不允许当前操作（如运行中删除、非失败任务重启）。"""

    code = ErrorCode.TASK_STATE_INVALID


class PmlGenerationError(AppError):
    """PML 脚本生成失败。"""

    code = ErrorCode.PYML_GENERATE_FAILED


class PymolNotFoundError(AppError):
    """本地未找到 PyMOL 可执行程序。"""

    code = ErrorCode.PYMOL_NOT_FOUND
    http_status = 500


class NetworkError(AppError):
    """本地网络请求失败（仅允许 RCSB PDB 拉取）。"""

    code = ErrorCode.NETWORK_OFFLINE


class RequestParamError(AppError):
    """请求参数校验失败。"""

    code = ErrorCode.REQUEST_PARAM_INVALID
