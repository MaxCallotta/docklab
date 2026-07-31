# GitHub 发布指南

## 1. 初始化仓库

在项目目录执行：

```powershell
cd D:\Pax_2.0\cadd-3d
git init
git add .
git commit -m "chore: init cadd platform repository"
git branch -M main
git remote add origin https://github.com/MaxCallotta/docklab.git
git push -u origin main
```

## 2. 创建版本标签

```powershell
git tag v0.8.0
git push origin v0.8.0
```

## 3. 创建 GitHub Release

1. 打开 GitHub 仓库页面
2. 进入 Releases，点击 `Draft a new release`
3. 选择刚推送的标签，例如 `v0.8.0`
4. 上传 exe 附件：`D:\Pax_2.0\cadd-3d\dist\CaddPlatform.exe`
5. 填写发布说明后发布

## 4. 更新 README 下载地址

将 README 中的占位地址替换为实际地址：

```text
https://github.com/MaxCallotta/docklab/releases/latest/download/CaddPlatform.exe
```

## 发布说明模板

```markdown
## v0.8.0

- 下载 `CaddPlatform.exe`，双击即可运行
- 支持对接盒子可视化拖拽
- 支持自动口袋盒子预测
- 内置 RDKit / OpenBabel / AutoDock Vina / AutoDock4
```

## 注意事项

- 不要提交 `build`、`dist`、`node_modules`、`packaging-venv` 等大目录，`.gitignore` 已默认排除
- `CaddPlatform.exe` 没有数字签名，其他用户首次运行可能被 SmartScreen 或杀毒软件拦截，需要选择“仍要运行”
- 当前 exe 仅支持 Windows 10/11 64 位
- 用户机器没有 `D:\Pax_2.0` 时，exe 会自动使用 `%LOCALAPPDATA%\CaddPlatform\data` 作为数据目录
- 输入 PDB ID 下载蛋白时需要联网，直接上传受体文件则不需要
