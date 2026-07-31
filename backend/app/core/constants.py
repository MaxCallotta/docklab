"""全局常量定义。

职责说明：
- 错误码：前后端统一约定的标准化错误码，前端可直接映射为友好提示；
- 任务状态：任务生命周期状态机；
- 目录与格式：任务目录命名与允许上传的分子格式。
"""

from __future__ import annotations


class ErrorCode:
    """标准化数值错误码。

    分段规则：
    - 1xxx：分子处理（解析、校验、预处理）
    - 2xxx：对接软件（路径、适配器、结果解析）
    - 3xxx：文件与数据（PDB 下载、文件校验、越界访问）
    - 4xxx：参数、任务与计算执行
    """

    OK = 200

    # ---- 分子处理 1xxx ----
    MOL_PARSE_FAILED = 1001
    MOL_VALIDATION_FAILED = 1002
    FORMAT_UNSUPPORTED = 1003
    RECEPTOR_PREP_FAILED = 1004
    LIGAND_PREP_FAILED = 1005
    MOL_BATCH_SPLIT_FAILED = 1006

    # ---- 对接软件 2xxx ----
    ENGINE_NOT_FOUND = 2001
    ENGINE_NOT_IMPLEMENTED = 2002
    ENGINE_OUTPUT_PARSE_FAILED = 2003

    # ---- 文件与数据 3xxx ----
    PDB_DOWNLOAD_FAILED = 3001
    FILE_NOT_FOUND = 3002
    FILE_TYPE_INVALID = 3003
    FILE_SIZE_EXCEEDED = 3004
    FILE_ACCESS_DENIED = 3005
    EXPORT_FAILED = 3006
    NETWORK_OFFLINE = 3007

    # ---- 参数、任务与计算 4xxx ----
    ENGINE_EXEC_FAILED = 4001
    REQUEST_PARAM_INVALID = 4002
    TASK_STATE_INVALID = 4003
    TASK_NOT_FOUND = 4004
    INTERNAL_ERROR = 4005
    PYML_GENERATE_FAILED = 4006
    PYMOL_NOT_FOUND = 4007
    TEMPLATE_NOT_FOUND = 4008


class TaskStatus:
    """任务状态机常量。"""

    QUEUED = "queued"        # 排队中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败


class TaskDirName:
    """每个任务目录下的固定子目录名。"""

    INPUT = "input"        # 原始上传文件
    PREPARED = "prepared"  # 预处理后的 pdbqt / clean pdb
    WORK = "work"          # 中间文件与引擎日志
    OUTPUT = "output"      # 对接结果、打分表、pml
    EXPORT = "export"      # 用户导出文件


ALLOWED_UPLOAD_EXTENSIONS = {
    ".cdxml": "cdxml",
    ".pdb": "pdb",
    ".pdbqt": "pdbqt",
    ".sdf": "sdf",
    ".mol2": "mol2",
    ".mol": "mol",
    ".txt": "smiles",
    ".smi": "smiles",
}

PDB_ID_PATTERN = r"^[0-9][A-Za-z0-9]{3}$"

RCSB_FILE_URL_TEMPLATE = "https://files.rcsb.org/download/{pdb_id}.pdb"
