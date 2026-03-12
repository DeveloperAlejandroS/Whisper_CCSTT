# 🎙 Whisper CCSTT

> **C**all **C**enter **S**peech-**T**o-**T**ext — Transcripción automática de llamadas de agentes con [OpenAI Whisper](https://github.com/openai/whisper).

Herramienta CLI desarrollada para transcribir las grabaciones de llamadas del call center de forma local, sin APIs externas ni costos por uso. Procesaba archivos `.wav` individuales o carpetas completas en lote, exportando el resultado en `.txt`, `.srt` y `.json` con timestamps por segmento.

---

## Contexto del proyecto

Los agentes de call center generaban grabaciones de sus llamadas en formato `.wav` almacenadas localmente. El proceso manual de revisión era lento e inescalable — escuchar cada llamada para control de calidad, documentación o análisis tomaba el mismo tiempo que la llamada en sí.

**Whisper CCSTT** automatizó ese flujo: dado un archivo o una carpeta de grabaciones, el script transcribía todo el audio a texto en minutos, con detección automática del idioma y timestamps por segmento para ubicar momentos específicos dentro de la llamada.

### Casos de uso reales

- **Control de calidad** — revisar transcripciones en lugar de escuchar llamadas completas.
- **Documentación** — generar registros escritos de compromisos, acuerdos o quejas.
- **Análisis de texto** — alimentar pipelines de NLP, análisis de sentimiento o keyword extraction sobre el corpus de llamadas.
- **Auditoría** — buscar palabras clave en cientos de llamadas en segundos con `grep` sobre los `.txt`.

---

## Características

- 🗣 **Transcripción precisa** con los modelos Whisper de OpenAI (tiny → large-v3)
- 🌍 **Detección automática de idioma** o forzado manual (`--language es`)
- 📁 **Procesamiento en lote** — pasa una carpeta y transcribe todas las grabaciones
- 📄 **Múltiples formatos de salida** — `.txt`, `.srt` (con timestamps), `.json` (estructurado)
- ⚡ **Un modelo, muchos archivos** — el modelo se carga una sola vez en memoria
- 🛡 **Manejo de errores** — reporta fallos individuales sin detener el lote
- 🔌 **100% local** — sin red, sin API keys, sin costo por transcripción

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/Whisper_CCSTT.git
cd Whisper_CCSTT
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar ffmpeg

| Sistema | Comando |
|---|---|
| macOS | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt install ffmpeg` |
| Windows | [ffmpeg.org/download.html](https://ffmpeg.org/download.html) → agregar al PATH |

---

## Uso

### Transcribir una llamada

```bash
python main.py 300000572722447.wav
```

### Especificar modelo e idioma

```bash
python main.py 300000572722447.wav --model medium --language es
```

### Transcribir una carpeta completa de grabaciones

```bash
python main.py ./grabaciones/ --format txt --output ./transcripciones/
```

### Exportar en todos los formatos

```bash
python main.py ./grabaciones/ --format txt json srt --output ./out/
```

### Modo silencioso (solo guardar, no imprimir)

```bash
python main.py ./grabaciones/ --no-print
```

---

## Opciones

| Argumento | Corto | Descripción | Default |
|---|---|---|---|
| `input` | — | Archivo `.wav` o carpeta de grabaciones | — |
| `--model` | `-m` | Modelo Whisper (`tiny` `base` `small` `medium` `large-v3`) | `base` |
| `--language` | `-l` | Código de idioma (`es`, `en`…). Omitir = auto-detect | auto |
| `--format` | `-f` | Formato(s) de salida: `txt` `srt` `json` | `txt` |
| `--output` | `-o` | Directorio de salida | junto al audio |
| `--no-print` | — | No imprimir en consola | `False` |

---

## Modelos disponibles

| Modelo | Velocidad | Precisión | VRAM aprox. |
|---|---|---|---|
| `tiny` | ⚡⚡⚡⚡⚡ | ★☆☆☆☆ | ~1 GB |
| `base` | ⚡⚡⚡⚡ | ★★☆☆☆ | ~1 GB |
| `small` | ⚡⚡⚡ | ★★★☆☆ | ~2 GB |
| `medium` | ⚡⚡ | ★★★★☆ | ~5 GB |
| `large-v3` | ⚡ | ★★★★★ | ~10 GB |

> Para llamadas en español se recomienda `medium` — buen balance entre velocidad y precisión con acentos latinoamericanos.

---

## Formatos de salida

### `.txt` — Texto plano para búsqueda rápida
```
Buenos días, le habla Carlos de soporte técnico. ¿En qué le puedo ayudar el día de hoy?
El cliente indica que no puede acceder a su cuenta desde el día lunes...
```

### `.srt` — Con timestamps para ubicar momentos en la llamada
```
1
00:00:00,000 --> 00:00:04,200
Buenos días, le habla Carlos de soporte técnico.

2
00:00:04,200 --> 00:00:07,800
¿En qué le puedo ayudar el día de hoy?
```

### `.json` — Estructurado para pipelines de análisis
```json
{
  "language": "es",
  "text": "Buenos días, le habla Carlos de soporte técnico...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 4.2,
      "text": "Buenos días, le habla Carlos de soporte técnico."
    }
  ]
}
```

---

## Usarlo como módulo

```python
from main import transcribe_file, collect_audio_files
from pathlib import Path
import whisper

# Cargar modelo una vez
model = whisper.load_model("medium")

# Transcribir y obtener el resultado como dict
result = transcribe_file(
    audio_path = Path("300000572722447.wav"),
    model      = model,
    language   = "es",
    formats    = ["json"],
    output_dir = Path("./out/"),
    print_text = False,
)

# Usar directamente en tu pipeline
texto     = result["text"]
segmentos = result["segments"]  # lista con start, end, text
idioma    = result["language"]
```

---

## Formatos de audio soportados

`.wav` `.mp3` `.mp4` `.m4a` `.ogg` `.flac` `.webm` `.mkv`

---

## Estructura del proyecto

```
Whisper_CCSTT/
├── main.py            # CLI y módulo principal
├── requirements.txt   # Dependencias Python
└── README.md          # Documentación
```

---

## Roadmap

- [ ] Diarización de hablantes — separar agente de cliente en la transcripción
- [ ] Análisis de sentimiento sobre el corpus de llamadas
- [ ] Extracción de keywords y categorización automática
- [ ] Interfaz web básica con Flask para uso sin terminal
- [ ] Exportar a `.docx` con timestamps como comentarios

---

## Tecnologías

| | |
|---|---|
| Lenguaje | Python 3.10+ |
| Motor STT | [OpenAI Whisper](https://github.com/openai/whisper) |
| Audio | ffmpeg |
| CLI | `argparse` (stdlib) |

---

## Licencia

MIT — libre para uso personal y comercial.

---

*Desarrollado en la Universidad ECCI · Bogotá, Colombia*