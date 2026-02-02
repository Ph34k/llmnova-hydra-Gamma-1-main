CI/CD Guide
===========

This document explains the supplied GitHub Actions workflows and how to configure them for this repo.

Workflows added
--------------

- `.github/workflows/backend-ci.yml` — Runs backend tests and (optionally) builds + pushes a Docker image when registry secrets are present.
- `.github/workflows/frontend-ci.yml` — Installs, builds and runs frontend tests for `NovaLLM/frontend` or `hydra-frontend` if present.

Secrets and configuration
-------------------------

The backend Docker job expects the following repository secrets (optional):

- `REGISTRY_URL` — e.g. `ghcr.io` or `docker.io/your-namespace`
- `REGISTRY_USERNAME` — registry username
- `REGISTRY_PASSWORD` — registry token/password
- `IMAGE_NAME` — image name to tag/push (e.g. `my-org/hydra-backend`)

If these secrets are not set, the Docker build&push step is skipped. This keeps the CI safe to run without credentials.

How to enable pushes to registry
--------------------------------

1. Add the secrets in your repository settings: Settings → Secrets and variables → Actions → New repository secret.
2. The workflow will trigger on push to branches affecting the `hydra-backend` path and will push the built image as `${{ secrets.REGISTRY_URL }}/${{ secrets.IMAGE_NAME }}:latest`.

Tips for a professional pipeline
--------------------------------

- Split tests into fast unit tests and slower integration tests and run them in parallel.
- Add caching for Python packages and Node dependencies to speed up builds.
- Pin action versions (`uses: actions/checkout@v4`) to stable major versions.
- Protect main branches with required status checks using these CI jobs.

Local testing of workflows (recommended)
--------------------------------------

You can run the test commands locally in the repo root:

```powershell
cd hydra-backend/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

And for frontend (if present):

```powershell
cd NovaLLM/frontend # or hydra-frontend
# install using pnpm if pnpm-lock.yaml present else npm ci
if (Test-Path pnpm-lock.yaml) { pnpm install } elseif (Test-Path package-lock.json) { npm ci } else { npm install }
npm run build
npm test
```

Follow-ups
---------

- If you want I can:
  - Add caching to workflows (actions/cache) for Python and Node deps.
  - Split the test matrix into multiple jobs (fast/slow), run coverage, and upload coverage reports.
  - Add a deployment workflow (staging/production) triggered manually or on merges to `main`.
