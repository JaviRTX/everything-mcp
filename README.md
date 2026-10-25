# ⚡ Everything MCP Server

> Servidor **Model Context Protocol (MCP)** para Windows que conecta agentes de IA (**Claude Desktop**, **Antigravity**, **Cursor**, etc.) con el motor de indexación ultrarrápido de **voidtools Everything**.

Busca cualquier archivo o carpeta entre millones de ficheros en **milisegundos** aprovechando el índice en memoria de Everything a través de IPC nativo, **sin abrir puertos de red ni comprometer datos privados**.

---

## 🌟 Características Principales

- ⚡ **Velocidad Extrema (NTFS IPC)**: Búsquedas instantáneas en discos duros locales y externos indexados por Everything (< 20 ms).
- 🚀 **Auto-Arranque Silencioso**: Si Everything no está abierto al realizar una búsqueda, el servidor lo detecta y lo inicia automáticamente en segundo plano (`-startup`).
- 🔒 **Privacidad Total y Zero-Leak**:
  - No requiere APIs externas, llaves ni archivos `.env`.
  - Sin servidores HTTP abiertos ni exposición en red local.
- 🛡️ **Win32 Desktop Bridging**: Resuelve automáticamente el aislamiento de ventanas/desktops en agentes autónomos (`WinSta0\Default`), garantizando compatibilidad tanto en escritorios interactivos como en sandboxes de agentes.
- 🧰 **Herramientas Optimizadas para LLMs**:
  - Salida formateada en Markdown conciso y token-eficiente con metadatos (tamaño legible, fechas ISO, indicador de directorio).
  - Compatible con la sintaxis avanzada de Everything (extensiones múltiples, rangos de fechas, tamaños, regex y operadores booleanos).

---

## 🛠️ Herramientas Expuestas (MCP Tools)

| Herramienta | Descripción | Parámetros Clave |
| :--- | :--- | :--- |
| `everything_search` | Búsqueda general con toda la potencia de la sintaxis de Everything | `query`, `max_results`, `path`, `files_only`, `folders_only`, `sort` |
| `everything_find_file` | Localizador directo de archivos por nombre o patrón comodín | `filename`, `path`, `max_results` |
| `everything_find_folder` | Localizador directo de directorios | `folder_name`, `path`, `max_results` |
| `everything_recent_files` | Archivos modificados en las últimas N horas | `hours`, `extension`, `path`, `max_results` |
| `everything_status` | Diagnóstico de salud y versión del motor Everything | Ninguno |

---

## 🚀 Requisitos Previos

1. **Windows 10/11 (64-bit)**.
2. **voidtools Everything** instalado en el equipo ([descargar de voidtools.com](https://www.voidtools.com/)).
3. **Python 3.10+** (o el gestor ultrarrápido **uv**).

---

## 📦 Instalación y Puesta en Marcha

### Opción 1: Con `uv` (Recomendado)

```powershell
# Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd everything-mcp

# Crear entorno e instalar dependencias
uv venv
uv pip install --system-certs "mcp[cli]>=1.0.0"
```

### Opción 2: Con Python estándar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "mcp[cli]>=1.0.0"
```

---

## ⚙️ Configuración en Clientes MCP

> [!NOTE]
> Reemplaza `<RUTA_A_TU_REPOSITORIO>` por la ruta absoluta de tu equipo donde hayas clonado este proyecto (por ejemplo: `C:\\dev\\everything-mcp` o `D:\\repos\\everything-mcp`).

### 1. Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`)

Añade el servidor a tu bloque `mcpServers`:

```json
{
  "mcpServers": {
    "everything": {
      "command": "uv",
      "args": [
        "--directory",
        "<RUTA_A_TU_REPOSITORIO>",
        "run",
        "python",
        "-m",
        "everything_mcp.server"
      ]
    }
  }
}
```

*(Si utilizas el entorno virtual directo sin `uv` global):*

```json
{
  "mcpServers": {
    "everything": {
      "command": "<RUTA_A_TU_REPOSITORIO>\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "everything_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "<RUTA_A_TU_REPOSITORIO>\\src"
      }
    }
  }
}
```

### 2. Antigravity / Cursor / VS Code (`mcp.json`)

```json
{
  "servers": {
    "everything": {
      "command": "<RUTA_A_TU_REPOSITORIO>\\.venv\\Scripts\\python.exe",
      "args": ["-m", "everything_mcp.server"],
      "env": {
        "PYTHONPATH": "<RUTA_A_TU_REPOSITORIO>\\src"
      }
    }
  }
}
```

---

## 💡 Ejemplos de Consultas Útiles para el Agente

- **Por extensión**: `ext:pdf;docx balance`
- **Por tamaño**: `size:>500MB` o `size:small` (<100 KB)
- **Por fecha**: `dm:today` o `dm:last2hours`
- **En una carpeta específica**: `path:"C:\Mis Documentos" *.py`
- **Exclusiones**: `*.log !temp`
- **Expresiones Regulares**: `regex:^IMG_[0-9]{4}\.png`

---

## 🧪 Pruebas Rápidas

Para comprobar el correcto funcionamiento local:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe tests\test_searcher.py
```

---

## 📄 Licencia

- **Everything MCP Server**: Licencia MIT &copy; 2026 JaviRTX. Permite copia, modificación, distribución y uso libre.
- **voidtools Everything**: Licencia MIT &copy; voidtools. Gratuito para uso personal y comercial.
