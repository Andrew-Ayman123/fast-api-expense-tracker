# Expense Tracker

## Setup

### Pre-requistes:
- Python 3.10+ Installed

### 1. Install `uv` and create a virtual environment

#### On **Linux** (Ubuntu):
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
uv --version
uv venv --python 3.12
```

#### On **Windows** (PowerShell):
```powershell
irm https://astral.sh/uv/install.ps1 | iex
uv --version
uv venv --python 3.12
```

---

### 2. Activate the virtual environment

#### On **Linux**:
```bash
source .venv/bin/activate
```

#### On **Windows** (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

---

### 3. Install dependencies

```bash
uv sync
```

---

### 4. Verify dependencies are installed

```bash
ruff --version
mypy --version
bandit --version
pre-commit --version
```

---

### 5. Install Pre-Commit hooks
```bash
pre-commit install
```

---

### 6. Ingest environment variables from `.env`

#### On **Linux**:
```bash
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | sed 's/#.*$//')
fi
```

#### On **Windows** (PowerShell):
```powershell
if (Test-Path ".env") {
    Get-Content ".env" |
        Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } |
        ForEach-Object {
            $line = ($_ -split '#')[0].Trim()  # Remove inline comments
            if ($line -match "^\s*(\w+)\s*=\s*(.+)\s*$") {
                $key = $matches[1]
                $value = $matches[2]
                Set-Item -Path "Env:$key" -Value $value
            }
        }
}
```

---

### 7. Set up Docker container for PostgreSQL

#### On **Linux**:
```bash
docker run -d \
    --name postgres-expense-tracker \
    -e POSTGRES_DB=$DATABASE_NAME \
    -e POSTGRES_USER=$DATABASE_USER \
    -e POSTGRES_PASSWORD=$DATABASE_PASSWORD \
    -p $DATABASE_PORT:5432 \
    postgres:15
```

#### On **Windows** (PowerShell):
```powershell
docker run -d `
    --name postgres-expense-tracker `
    -e POSTGRES_DB=$env:DATABASE_NAME `
    -e POSTGRES_USER=$env:DATABASE_USER `
    -e POSTGRES_PASSWORD=$env:DATABASE_PASSWORD `
    -p "$($env:DATABASE_PORT):5432" `
    postgres:15
```
---

### 8. Run database migrations

#### On **Linux**:
```bash
alembic -x url=$DATABASE_URL_ALEMBIC upgrade head
```

#### On **Windows** (PowerShell):
```powershell
alembic -x url=$env:DATABASE_URL_ALEMBIC upgrade head
```
---

### 9. Run the server

```bash
uv run run.py
```

### 10. Install VS-Code extensions (Optional)

#### On **Linux**:
```bash
cat vscode-extensions.txt | xargs -n 1 code --install-extension
```

#### On **Windows** (PowerShell):
```powershell
Get-Content vscode-extensions.txt | ForEach-Object { code --install-extension $_ }
```
---

## Contributing

- Don't use `uv pip install`, use `uv add` to add to the `pyproject.toml`