export const STATUS_MAP = {
  queued: { label: '排队中', type: 'info' },
  running: { label: '运行中', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' }
}

export const BOX_DEFAULTS = {
  center_x: 0,
  center_y: 0,
  center_z: 0,
  size_x: 20,
  size_y: 20,
  size_z: 20
}

export const BOX_MODE = {
  MANUAL: 'manual',
  AUTO: 'auto'
}

export const BOX_MODE_OPTIONS = [
  { label: '手动自定义盒子', value: BOX_MODE.MANUAL },
  { label: '自动预测口袋盒子', value: BOX_MODE.AUTO }
]

export const BOX_LIMITS = {
  center: { min: -2000, max: 2000 },
  size: { min: 1, max: 200 }
}

export const PARAMS_DEFAULTS = {
  engine_id: 'vina',
  exhaustiveness: 8,
  energy_range: 3.0,
  num_modes: 9,
  seed: null,
  cpu: null,
  timeout_seconds: 7200
}

export const LIGAND_ACCEPT = '.cdxml,.sdf,.mol,.mol2,.smi,.txt'
export const LIGAND_EXTENSIONS = ['.cdxml', '.sdf', '.mol', '.mol2', '.smi', '.txt']
export const RECEPTOR_ACCEPT = '.pdb,.pdbqt'
export const RECEPTOR_EXTENSIONS = ['.pdb', '.pdbqt']
export const MAX_UPLOAD_MB = 200

export const PREPROCESS_ACCEPT = '.cdxml,.sdf,.mol2,.smi,.txt,.pdbqt'
export const PREPROCESS_EXTENSIONS = ['.cdxml', '.sdf', '.mol2', '.smi', '.txt', '.pdbqt']

export const PREPROCESS_OUTPUT_FORMATS = [
  { label: 'CDXML', value: 'cdxml' },
  { label: 'SDF', value: 'sdf' },
  { label: 'MOL2', value: 'mol2' },
  { label: 'PDBQT', value: 'pdbqt' },
  { label: 'SMILES', value: 'smi' }
]

export const POSE_FORMATS = [
  { label: 'PDBQT', value: 'pdbqt' },
  { label: 'PDB', value: 'pdb' },
  { label: 'SDF', value: 'sdf' },
  { label: 'MOL2', value: 'mol2' }
]
