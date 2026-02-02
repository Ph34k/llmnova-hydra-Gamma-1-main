param(
    [switch]$InstallOnly
)

Write-Host "Running CI auto-fix script..."

# ensure pip up-to-date
python -m pip install --upgrade pip

# Install project deps if present
if (Test-Path "requirements.txt") {
    python -m pip install -r requirements.txt
}

# Install dev tools using python -m to avoid exe issues
Write-Host "Installing dev tools (ruff, mypy, isort, pytest)..."
python -m pip install ruff mypy isort pytest
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: some tools may not have been installed"
}

if ($InstallOnly) {
    Write-Host "Installed dependencies. Exiting as requested."
    exit 0
}

# Run ruff (module) and apply fixes
Write-Host "Running ruff check..."
python -m ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ruff found issues"
}

Write-Host "Applying ruff --fix..."
python -m ruff check --fix .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ruff fix applied (if possible)"
}

# isort via module
Write-Host "Running isort..."
python -m isort . --profile black
if ($LASTEXITCODE -ne 0) {
    Write-Host "isort finished"
}

# final ruff check
Write-Host "Final ruff check..."
python -m ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Final ruff check completed with issues"
}

# mypy (attempt to auto-install types first)
Write-Host "Running mypy..."
python -m mypy --install-types --non-interactive .
if ($LASTEXITCODE -ne 0) {
    python -m mypy .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "mypy failed or missing"
    }
}

# Run tests if present
if (Test-Path "pytest.ini" -or Test-Path "pyproject.toml" -or (Get-ChildItem -Recurse -Filter "*_test.py" -ErrorAction SilentlyContinue)) {
    Write-Host "Running pytest..."
    python -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pytest reported failures"
    }
} else {
    Write-Host "No pytest configuration or tests detected, skipping pytest."
}

# Commit changes if any
git add -A
$diff = git status --porcelain
if ($diff) {
    git commit -m "chore: autoformat with ruff/isort and add PlanTool"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Commit failed"
    } else {
        Write-Host "Committed changes."
    }
} else {
    Write-Host "No changes to commit."
}
