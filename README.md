# Expense Tracker

## Setup

### 1. Install `uv` and create a virtual environment

#### On **Linux** (Ubuntu):
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
uv --version
uv venv
```

#### On **Windows** (PowerShell):
```powershell
irm https://astral.sh/uv/install.ps1 | iex
uv --version
uv venv
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
uv pip install .
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

### 5. Ingest environment variables from `.env`

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
        Where-Object { $_ -notmatch '^#' -and $_ -ne '' } |
        ForEach-Object {
            $line = ($_ -split '#')[0].Trim()  # Remove inline comments
            if ($line -match "^\s*(\w+)\s*=\s*(.+)\s*$") {
                $env:$($matches[1]) = $matches[2]
            }
        }
}
```

---

### 6. Set up Docker container for PostgreSQL

#### On **Linux**:
```bash
docker run -d \
    --name postgres-todo \
    -e POSTGRES_DB=$DATABASE_NAME \
    -e POSTGRES_USER=$DATABASE_USER \
    -e POSTGRES_PASSWORD=$DATABASE_PASSWORD \
    -p $DATABASE_PORT:5432 \
    postgres:15
```

#### On **Windows** (PowerShell):
```powershell
docker run -d `
    --name postgres-todo `
    -e POSTGRES_DB=$env:DATABASE_NAME `
    -e POSTGRES_USER=$env:DATABASE_USER `
    -e POSTGRES_PASSWORD=$env:DATABASE_PASSWORD `
    -p "$($env:DATABASE_PORT):5432" `
    postgres:15
```
---

### 7. Run database migrations

```bash
alembic -x url=$DATABASE_URL_ALEMBIC upgrade head
```

---

### 8. Run the server

```bash
uv run run.py
```