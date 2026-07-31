<p align="center">
  <img src="docs/assets/docklab-logo.svg" alt="DockLab Logo" width="140">
</p>

<h1 align="center">DockLab</h1>

<p align="center">
  <strong>Local Molecular Docking &amp; Visualization Platform</strong>
</p>

<p align="center">
  中文版：<a href="README.md">README.md</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/Version-0.8.0-1f6feb?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-2ea44f?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Node.js-20%2B-339933?style=flat-square&logo=nodedotjs&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/Frontend-Vue%203-42b883?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square" alt="PRs Welcome">
</p>

## Overview

DockLab is a local-first molecular docking platform built for drug discovery and computational chemistry research. It integrates molecular structure preprocessing, binding pocket prediction, docking parameter control, and interactive 3D result visualization into a reproducible and traceable scientific workflow. By combining automated pocket detection with manual 3D box adjustment, DockLab lowers the barrier to high-quality docking while preserving full control over calculation parameters.

## Key Strengths

- **Local-first and data-controlled**: All computations run locally. Molecular data and task records never depend on external cloud services, which is important for confidentiality and research compliance.
- **End-to-end automation**: From PDB ID retrieval, format conversion, adding hydrogens and removing water, to pocket prediction, docking, scoring, and pose export, the platform supports the entire workflow.
- **Interactive docking box**: Drag the box center and vertex handles directly in the 3D protein-ligand scene, with bidirectional synchronization to the parameter panel.
- **Automated pocket prediction**: Built-in geometry-based cavity detection with optional FPocket integration for industrial-grade pocket identification, while retaining manual fine-tuning.
- **Modular architecture**: Frontend, backend services, pocket prediction, and docking engines are fully decoupled for maintainability, testing, and extension.
- **Professional parameters preserved**: Random seeds, CPU allocation, search depth, and timeout controls remain fully available without compromising precision.

## Features

| Module | Capability |
| --- | --- |
| Molecule input | PDB ID, CDXML, SDF, MOL, MOL2, SMILES |
| Receptor preparation | Water/heteroatom removal, PDBQT generation |
| 3D visualization | Protein cartoon, ligand poses, docking box rendering |
| Docking box | Manual coordinates, canvas dragging, automated pocket prediction |
| Docking engines | AutoDock Vina, AutoDock4/AutoGrid4 extension interface |
| Result analysis | Multi-pose scoring, RMSD, CSV reports, pose export |
| Task management | Local persistence, restart, batch delete, archive download |

## Technology Stack

- Frontend: Vue 3, Vite, Element Plus, 3Dmol.js, Pinia
- Backend: FastAPI, Uvicorn, Pydantic
- Molecular computing: RDKit, Biopython, OpenBabel
- Docking: AutoDock Vina, AutoDock4 / AutoGrid4
- Pocket prediction: Built-in geometry cavity detection with optional FPocket

## Quick Start

### End Users (Windows)

Download `CaddPlatform.exe` from [GitHub Releases](https://github.com/MCXDL/docklab/releases), double-click to launch, and the platform will open automatically in your browser.

- Supports Windows 10/11 64-bit
- The exe bundles the Python runtime, frontend, RDKit, OpenBabel, and docking engines
- No pre-installation of Python, RDKit, OpenBabel, AutoDock Vina, or AutoDock4 is required
- Default data directory: `%LOCALAPPDATA%\CaddPlatform\data`
- The data directory can be customized with the `PAX_DATA_ROOT` environment variable

## Access Notes

`127.0.0.1` is the loopback address of the machine running the program. Each user runs the exe on their own computer and opens http://127.0.0.1:8000 locally.

To share a single instance over a local network, start the service with `--host 0.0.0.0` and let other devices access the server's LAN IP address.

### Developers

#### Requirements

- Windows 10/11 64-bit (recommended)
- Python 3.11+
- Node.js 20+
- Source mode requires OpenBabel, AutoDock Vina, and AutoDock4/AutoGrid4 installed locally

#### Frontend

```powershell
cd frontend
npm install
npm run build
```

#### Backend

```powershell
cd backend
pip install -r requirements.txt
cd ..
python scripts/run_app.py --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 to use the platform.

#### Tests

```powershell
cd backend
python -m pytest -q
```

## Packaging

```powershell
python -m pip install pyinstaller
python scripts/build_standalone_windows.py
```

The executable is generated at `dist\CaddPlatform.exe`. To bundle OpenBabel, AutoDock Vina, and AutoDock4/AutoGrid4 into the exe, place the tool directories under `tools/` or set `OPENBABEL_DIR`, `VINA_DIR`, and `AUTODOCK_TOOLS_DIR`.

## Project Structure

```text
docklab/
├── backend/       # FastAPI backend and molecular computing modules
├── frontend/      # Vue3 frontend and 3D interaction UI
├── scripts/       # Startup, test, packaging, and demo scripts
├── docs/          # Release and maintenance documentation
└── dist/          # Local build artifacts (not committed)
```

## Release and Contribution

See [docs/GITHUB_RELEASE.md](docs/GITHUB_RELEASE.md) for release instructions. Issues and pull requests are welcome.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and [SECURITY.md](SECURITY.md) for security reporting.

## License

This project is licensed under the [MIT License](LICENSE).
