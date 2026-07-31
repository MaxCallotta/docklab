# FAQ

## 其他用户如何访问平台？

`127.0.0.1` 是本机地址。每个用户需要下载 exe 并在自己电脑上运行，然后访问自己电脑上的 `http://127.0.0.1:8000`。

## 需要预先安装 AutoDock 或 OpenBabel 吗？

使用 exe 不需要。exe 已内置 Python、RDKit、OpenBabel、AutoDock Vina 与 AutoDock4。

源码运行模式需要自行安装这些工具，并配置到 PATH 或 `engines.json`。

## 数据保存在哪里？

默认保存在 `%LOCALAPPDATA%\CaddPlatform\data`，可通过 `PAX_DATA_ROOT` 环境变量修改。

## 输入 PDB ID 时需要联网吗？

需要。程序会从 RCSB PDB 下载蛋白结构；直接上传受体文件则不需要联网。

## 如何让局域网内其他设备访问？

使用 `--host 0.0.0.0` 启动服务，其他设备访问服务器的局域网 IP 地址。

## 如何反馈问题？

通过 GitHub Issues 提交问题，并附带版本号、操作系统、输入文件和日志。
