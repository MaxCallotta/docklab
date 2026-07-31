# DockLab 推广指南

## 项目定位

DockLab 是一个本地优先、开箱即用、面向科研用户的分子对接与 3D 可视化平台。推广时重点强调：

- 下载 exe 即可使用，无需安装 Python、RDKit、OpenBabel 或 AutoDock
- 本地计算，数据不离开用户电脑
- 3D 交互调盒与自动口袋预测兼顾便捷和精度
- 适合教学、组会演示、课程设计与药物筛选研究

## 目标用户

- 计算化学与药物设计研究生
- 结构生物学研究人员
- 化学信息学 / 生物信息学开发者
- 高校教师与课题组

## 内容资产清单

- 2-5 分钟中文演示视频
- 2-5 分钟英文演示视频
- 一份“上传配体到对接结果”的图文教程
- 一份 1OHV 示例任务，包含打分表和 3D 截图
- 一份常见问题文档（Wiki FAQ）
- 一个可以直接复制的 Citation

## 推荐平台

### 科研社区

- Reddit：`r/bioinformatics`、`r/comp_chem`、`r/chemistry`
- ResearchGate
- bioRxiv / chemRxiv
- Journal of Open Source Software（JOSS）
- 计算化学与药物设计相关会议

### 中文平台

- 知乎专栏
- 微信公众号
- B站
- CSDN
- 掘金
- 开源中国 / Gitee
- 小木虫

### 开发者平台

- GitHub Discussions
- GitHub Topics
- Awesome Cheminformatics
- Awesome Molecular Docking
- Awesome Bioinformatics
- Docker Hub
- Gitee 镜像

## 30 天推广计划

第 1 周：完成演示视频、教程、示例任务和 Citation。

第 2 周：在 GitHub Discussions 发布路线图，申请加入 Awesome 列表，发布英文介绍到 Reddit。

第 3 周：发布中文教程到知乎、CSDN、掘金，同步到 B站视频。

第 4 周：参加开源社区活动、收集用户反馈，发布 v0.9 路线图并持续迭代。

## Citation 与 Zenodo

仓库已提供 `CITATION.cff`，用户写论文时可以直接引用。

Zenodo 接入步骤：

1. 登录 https://zenodo.org
2. 进入 GitHub 设置页面，将 `MCXDL/docklab` 仓库授权给 Zenodo
3. 在 Zenodo 中选择该仓库并启用 Webhook
4. 之后每次创建 GitHub Release，Zenodo 会自动生成 DOI
5. 将 DOI 写入 README 或论文引用中
