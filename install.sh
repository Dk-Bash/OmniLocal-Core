#!/usr/bin/env bash
# Instalador de OmniLocal-Core.
# Deja todo listo para usar el asistente 100% local (sin nube, sin API keys,
# sin consumo de créditos): entorno Python + Ollama + modelo de IA local.
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

MODEL="${OLLAMA_MODEL:-llama3.2:3b}"

echo "=================================================="
echo " Instalando OmniLocal-Core en: $PROJECT_DIR"
echo "=================================================="

# 1) Python venv
if [ ! -d "venv" ]; then
    echo "-> Creando entorno virtual de Python..."
    python3 -m venv venv
fi
source venv/bin/activate

echo "-> Instalando dependencias de Python..."
pip install --upgrade pip -q
pip install -q -r requirements.txt

# 1.1) Interfaz gráfica (React/Vite) -> se compila a archivos estáticos que sirve el backend
if command -v npm >/dev/null 2>&1; then
    echo "-> Instalando y compilando la interfaz gráfica..."
    (cd frontend && npm install --silent && npm run build --silent)
else
    echo "-> npm no está instalado: se salta la interfaz gráfica."
    echo "   Podés instalar Node.js (https://nodejs.org) y volver a correr este script para tenerla."
    echo "   Mientras tanto, podés usar el asistente por consola con: python app/cli.py"
fi

# 2) Ollama (motor de IA local)
if ! command -v ollama >/dev/null 2>&1; then
    echo "-> Ollama no está instalado."
    read -p "   ¿Instalarlo ahora? (requiere conexión a internet solo para esta descarga) [s/N] " resp
    if [[ "$resp" =~ ^[sS]$ ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "   Saltando instalación de Ollama. Podés instalarlo después desde https://ollama.com"
        echo "   El asistente va a funcionar igual, solo con la memoria local guardada, hasta que instales el modelo."
    fi
fi

# 3) Levantar Ollama si está instalado pero no corriendo, y descargar el modelo
if command -v ollama >/dev/null 2>&1; then
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "-> Iniciando el servidor de Ollama en segundo plano..."
        nohup ollama serve > /tmp/ollama.log 2>&1 &
        sleep 2
    fi

    echo "-> Descargando el modelo '$MODEL' (una sola vez, se guarda localmente)..."
    ollama pull "$MODEL" || echo "   No se pudo descargar el modelo ahora. Podés reintentar luego con: ollama pull $MODEL"
fi

echo ""
echo "=================================================="
echo " Instalación lista."
echo " Para usarlo (interfaz gráfica):"
echo "   source venv/bin/activate"
echo "   python app/desktop.py"
echo " Para usarlo por consola:"
echo "   python app/cli.py"
echo "=================================================="
