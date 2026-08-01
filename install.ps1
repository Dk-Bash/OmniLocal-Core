# Instalador de OmniLocal-Core para Windows PowerShell.
# Deja todo listo para usar el asistente 100% local (sin nube, sin API keys,
# sin consumo de creditos): entorno Python + Ollama + modelo de IA local.
#
# Uso (desde la carpeta del proyecto):
#   .\install.ps1
#
# Si PowerShell bloquea la ejecucion de scripts, corre antes (una sola vez):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

$Model = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "llama3.2:3b" }

Write-Host "=================================================="
Write-Host " Instalando OmniLocal-Core en: $ProjectDir"
Write-Host "=================================================="

# 1) Entorno virtual de Python
if (-not (Test-Path "venv")) {
    Write-Host "-> Creando entorno virtual de Python..."
    python -m venv venv
}

$PyExe = Join-Path $ProjectDir "venv\Scripts\python.exe"
$PipArgs = @("-m", "pip")

Write-Host "-> Instalando dependencias de Python..."
& $PyExe -m pip install --upgrade pip -q
& $PyExe -m pip install -q -r requirements.txt

# 1.1) Interfaz grafica (React/Vite) -> se compila a archivos estaticos que sirve el backend
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if ($npmCmd) {
    Write-Host "-> Instalando y compilando la interfaz grafica..."
    Push-Location "frontend"
    npm install --silent
    npm run build --silent
    Pop-Location
} else {
    Write-Host "-> npm no esta instalado: se salta la interfaz grafica."
    Write-Host "   Instala Node.js (https://nodejs.org) y volve a correr este script para tenerla."
    Write-Host "   Mientras tanto, podes usar el asistente por consola con: venv\Scripts\python.exe app\cli.py"
}

# 2) Ollama (motor de IA local)
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaCmd) {
    Write-Host "-> Ollama no esta instalado."
    $resp = Read-Host "   Abrir la pagina de descarga ahora? (s/N)"
    if ($resp -match '^[sS]') {
        Start-Process "https://ollama.com/download/windows"
        Write-Host "   Instala Ollama desde el instalador que se descarga y despues volve a correr este script."
    } else {
        Write-Host "   Saltando instalacion de Ollama. El asistente va a funcionar igual,"
        Write-Host "   solo con la memoria local guardada, hasta que instales el modelo."
    }
}

# 3) Verificar servidor y descargar el modelo
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaCmd) {
    $running = $false
    try {
        Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null
        $running = $true
    } catch {
        $running = $false
    }

    if (-not $running) {
        Write-Host "-> Iniciando el servidor de Ollama en segundo plano..."
        Start-Process -WindowStyle Hidden -FilePath "ollama" -ArgumentList "serve"
        Start-Sleep -Seconds 2
    }

    Write-Host "-> Descargando el modelo '$Model' (una sola vez, se guarda localmente)..."
    try {
        & ollama pull $Model
    } catch {
        Write-Host "   No se pudo descargar el modelo ahora. Podes reintentar luego con: ollama pull $Model"
    }
}

Write-Host ""
Write-Host "=================================================="
Write-Host " Instalacion lista."
Write-Host " Para usarlo (interfaz grafica):"
Write-Host "   venv\Scripts\python.exe app\desktop.py"
Write-Host " Para usarlo por consola:"
Write-Host "   venv\Scripts\python.exe app\cli.py"
Write-Host "=================================================="
