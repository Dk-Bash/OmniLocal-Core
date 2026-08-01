# OmniLocal-Core

Sistema de inteligencia local modular. Guarda memoria y conocimiento propios,
y responde preguntas usando un modelo de IA que corre 100% en tu máquina
(vía [Ollama](https://ollama.com)) — sin internet después de instalado, sin
API keys, sin depender de ninguna IA externa ni consumir créditos por uso.

Versión: 0.1.0

## Interfaz

Tiene dos formas de usarlo:

- **Interfaz gráfica** (`app/desktop.py`): una ventana de escritorio nativa
  con historial de charlas, panel de memoria/conocimiento y fuentes locales
  — todo servido por un backend local, sin abrir el navegador ni salir a
  internet.
- **Consola** (`app/cli.py`): un chat de texto plano, más liviano, útil para
  probar rápido o si no tenés Node.js instalado para compilar la interfaz
  gráfica.

## Cómo funciona el asistente

Cada vez que le preguntás algo:

1. Primero busca en su propia memoria/conocimiento guardado. Si ya sabe la
   respuesta, la devuelve directo — **no usa el modelo de IA en ese caso**.
2. Si no la tiene, arma el contexto que sí tiene guardado y se lo pasa al
   modelo local para que razone la respuesta (RAG).
3. Esa respuesta nueva queda guardada como memoria. La próxima vez que
   preguntes algo parecido, alcanza con el paso 1: así el sistema aprende
   con el uso y depende cada vez menos del modelo.

También podés indexar carpetas de texto/notas propias ("Fuentes Locales" en
el panel derecho) para que su contenido quede disponible como conocimiento.

## Instalación

Requisitos: Python 3.12+, [Node.js](https://nodejs.org) (para compilar la
interfaz gráfica; si no lo tenés, el instalador sigue funcionando y podés
usar la consola), y opcionalmente [Ollama](https://ollama.com) para que el
asistente pueda razonar preguntas nuevas (sin él, sigue funcionando solo con
lo que le enseñes explícitamente).

**Linux / macOS / WSL / Git Bash:**
```bash
./install.sh
```

**Windows (PowerShell nativo, sin WSL):**
```powershell
# Si PowerShell bloquea scripts, corré esto una sola vez:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

Esto crea un entorno virtual, instala las dependencias de Python, compila la
interfaz gráfica, y si querés, instala Ollama y descarga el modelo local
(por defecto `llama3.2:3b`, configurable en `.env`, ver `.env.example`).

## Uso

**Windows:** doble clic en `iniciar.bat` (después de instalar), o:
```powershell
venv\Scripts\python.exe app\desktop.py    # interfaz gráfica
venv\Scripts\python.exe app\cli.py        # consola
```

**Linux / macOS / WSL / Git Bash:**
```bash
source venv/bin/activate
python app/desktop.py    # interfaz gráfica
python app/cli.py        # consola
```

Comandos dentro del chat de consola:

```text
/recordar <texto>   -> guarda algo en la memoria local
/memorias           -> muestra las últimas memorias guardadas
/estado              -> estado del motor y del modelo de IA local
/salir               -> cierra el programa
```

Cualquier otra cosa que escribas se trata como una pregunta.

## Estructura del Proyecto (resumen)

```text
OmniLocal-Core/
│
├── app/
│   ├── desktop.py       <- interfaz gráfica (ventana nativa + backend)
│   ├── cli.py           <- interfaz de consola
│   ├── main.py
│   ├── config.py
│   └── core/engine.py   <- núcleo: memoria, conocimiento, retrieval
│
├── webapp/               <- backend HTTP (FastAPI) que expone el asistente
├── frontend/              <- interfaz gráfica (React + Vite + Tailwind)
├── local_ai/              <- capa de IA local (Ollama, asistente RAG, ingestión de archivos)
├── database/
├── memory/ knowledge/ retrieval/ context/ personalization/
├── maintenance_*/         <- ciclo de auto-mantenimiento y gobernanza del sistema
├── omnilocal_runtime/      <- capa de ejecución autónoma de más alto nivel
├── tests/
├── install.sh / install.ps1 / iniciar.bat
├── requirements.txt
└── README.md
```

## Correr los tests

```bash
source venv/bin/activate
pytest -q
```
