<template>
  <div class="page-shell help-page">
    <h2 class="page-title">{{ $t('使用说明') }}</h2>
    <el-collapse v-model="active">
      <el-collapse-item :title="$t('如何从 ChemDraw 导出 cdxml 小分子文件')" name="cdxml">
        <ol class="help-list">
          <li>{{ $t('在 ChemDraw 中绘制目标小分子结构（或粘贴 SMILES 自动绘图）。') }}</li>
          <li>{{ $t('菜单选择「文件 → 另存为」。') }}</li>
          <li>{{ $t('文件类型选择「CDXML 文件」或 ChemDraw XML，命名为英文/数字。') }}</li>
          <li>{{ $t('在平台首页左侧「上传 cdxml」中导入，系统会自动补氢、计算电荷并生成 PDBQT。') }}</li>
        </ol>
      </el-collapse-item>

      <el-collapse-item :title="$t('如何获取 RCSB PDB ID')" name="pdbid">
        <ol class="help-list">
          <li>{{ $t('打开 RCSB PDB 官网（www.rcsb.org）。') }}</li>
          <li>{{ $t('按蛋白名称、UniProt ID 或文献检索目标结构。') }}</li>
          <li>{{ $t('进入结构详情页，地址栏或页面顶部可看到 4 位 PDB ID，例如 1a4w。') }}</li>
          <li>{{ $t('在本平台受体输入区填写该 ID，系统会从 RCSB 单向下载并自动去水、去杂原子。') }}</li>
        </ol>
      </el-collapse-item>

      <el-collapse-item :title="$t('环境安装指南')" name="autodock">
        <ol class="help-list">
          <li>{{ $t('从 AutoDock 官网下载对应 Windows / macOS / Linux 版本。') }}</li>
          <li>{{ $t('解压后记录 vina.exe 路径；AutoDock 4：记录 autodock4.exe 与 autogrid4.exe 路径。') }}</li>
          <li>{{ $t('在「软件配置」页填写可执行文件路径并保存。') }}</li>
          <li>{{ $t('配置 OpenBabel 3.x 路径，用于 cdxml 解析与格式转换。') }}</li>
          <li>{{ $t('建议将程序目录加入系统 PATH，平台会自动探测。') }}</li>
        </ol>
      </el-collapse-item>

      <el-collapse-item :title="$t('可视化操作说明')" name="pymol">
        <ol class="help-list">
          <li>{{ $t('在结果分析页点击「生成 PML 脚本」，系统输出标准化渲染脚本。') }}</li>
          <li>{{ $t('点击「唤起本地 PyMOL」，自动打开受体卡通、配体棍棒、氢键虚线与口袋表面视图。') }}</li>
          <li>{{ $t('可在 PyMOL 中继续调整颜色、透明度与视角，并导出图片或会话文件。') }}</li>
        </ol>
      </el-collapse-item>

      <el-collapse-item :title="$t('批量对接使用教程')" name="batch">
        <ol class="help-list">
          <li>{{ $t('多分子 cdxml 文件会自动拆分为多个独立配体。') }}</li>
          <li>{{ $t('SMILES 输入支持每行一个分子，自动生成批量配体。') }}</li>
          <li>{{ $t('批量任务队列由本地调度服务依次执行，任务列表实时显示进度。') }}</li>
          <li>{{ $t('结果按任务独立目录存储，可一键打包下载全部文件。') }}</li>
        </ol>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const active = ref(['cdxml', 'pdbid'])
</script>

<style scoped>
.help-page {
  max-width: 1000px;
}

.help-list {
  margin: 0;
  padding-left: 20px;
  line-height: 2;
}
</style>
