# Contributing to DockLab

Thank you for considering contributing to DockLab. This document outlines the preferred workflow for reporting issues, proposing features, and submitting code changes.

## Reporting Issues

- Use the GitHub issue tracker to report bugs or request features.
- Include the DockLab version, operating system, and relevant logs when reporting a bug.
- Provide a minimal reproduction case when possible.

## Development Workflow

1. Fork the repository and create a feature branch.
2. Keep changes focused on a single concern.
3. Run the backend tests before submitting:

```powershell
cd backend
python -m pytest -q
```

4. For frontend changes, build the production bundle:

```powershell
cd frontend
npm install
npm run build
```

5. Submit a pull request with a clear description of the change.

## Code Style

- Backend: follow the existing FastAPI and Python conventions in the repository.
- Frontend: follow the existing Vue 3 and JavaScript conventions.
- Keep user-facing messages concise and professional.
- Avoid introducing machine-specific absolute paths.

## Commit Guidelines

- Use clear, imperative commit messages.
- Reference related issues where applicable.
- Keep commits small and reviewable.
