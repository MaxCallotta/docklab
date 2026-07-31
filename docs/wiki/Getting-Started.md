# Getting Started

## 使用 exe

1. 从 GitHub Releases 下载 `CaddPlatform.exe`
2. 双击运行
3. 浏览器自动打开 `http://127.0.0.1:8000`
4. 上传受体与配体，或输入 PDB ID 下载受体
5. 使用左侧参数面板设置盒子，或点击“自动生成口袋盒子”
6. 提交对接并查看打分、构象与 3D 结果

## 数据目录

- 默认数据目录：`%LOCALAPPDATA%\CaddPlatform\data`
- 可通过 `PAX_DATA_ROOT` 环境变量修改
- 任务、日志、缓存统一写入数据目录

## 网络说明

`127.0.0.1` 仅代表当前电脑。每个用户需要在自己电脑上运行 exe，并访问自己电脑上的本地地址。输入 PDB ID 时需要联网从 RCSB 下载结构。

如需局域网共享同一实例：

```powershell
python scripts/run_app.py --host 0.0.0.0 --port 8000
```

其他设备访问服务器的局域网 IP 地址。
