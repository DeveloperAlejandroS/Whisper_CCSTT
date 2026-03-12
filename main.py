"""
Whisper CCSTT — Speech-to-Text CLI
Transcribe uno o varios archivos de audio usando OpenAI Whisper.

Uso:
    python main.py audio.wav
    python main.py audio.mp3 --model medium --language es
    python main.py ./audios/ --format srt --output ./resultados/
    python main.py audio.wav --format txt json srt --model large
"""

import argparse
import json
import sys
import time
from pathlib import Path

import whisper

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".ogg", ".flac", ".webm", ".mkv"}

AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]

OUTPUT_FORMATS = ["txt", "srt", "json"]


# ──────────────────────────────────────────────
# Formateadores de salida
# ──────────────────────────────────────────────

def format_txt(result: dict) -> str:
    """Texto plano con el transcript completo."""
    return result["text"].strip()


def format_json(result: dict) -> str:
    """JSON con texto, idioma detectado y segmentos con timestamps."""
    output = {
        "language":  result.get("language"),
        "text":      result["text"].strip(),
        "segments": [
            {
                "id":    seg["id"],
                "start": round(seg["start"], 3),
                "end":   round(seg["end"],   3),
                "text":  seg["text"].strip(),
            }
            for seg in result.get("segments", [])
        ],
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def _seconds_to_srt_time(seconds: float) -> str:
    """Convierte segundos a formato SRT: HH:MM:SS,mmm"""
    ms = int((seconds % 1) * 1000)
    s  = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_srt(result: dict) -> str:
    """Subtítulos en formato SRT estándar."""
    lines = []
    for i, seg in enumerate(result.get("segments", []), start=1):
        start = _seconds_to_srt_time(seg["start"])
        end   = _seconds_to_srt_time(seg["end"])
        lines.append(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n")
    return "\n".join(lines)


FORMATTERS = {
    "txt":  format_txt,
    "srt":  format_srt,
    "json": format_json,
}


# ──────────────────────────────────────────────
# Funciones de escritura
# ──────────────────────────────────────────────

def save_output(content: str, output_path: Path, fmt: str) -> None:
    """Guarda el contenido en disco."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"  💾 Guardado: {output_path}")


# ──────────────────────────────────────────────
# Transcripción
# ──────────────────────────────────────────────

def transcribe_file(
    audio_path: Path,
    model: whisper.Whisper,
    language: str | None,
    formats: list[str],
    output_dir: Path | None,
    print_text: bool = True,
) -> dict:
    """
    Transcribe un archivo de audio y guarda los resultados.

    Returns:
        El dict de resultado de Whisper.
    """
    print(f"\n🎙  Transcribiendo: {audio_path.name}")
    t0 = time.perf_counter()

    result = model.transcribe(
        str(audio_path),
        language=language,          # None = detección automática
        verbose=False,
    )

    elapsed = time.perf_counter() - t0
    detected_lang = result.get("language", "?")
    print(f"  ✅ Listo en {elapsed:.1f}s · Idioma detectado: {detected_lang}")

    if print_text:
        print(f"\n{'─' * 60}")
        print(result["text"].strip())
        print(f"{'─' * 60}")

    # Guardar en los formatos solicitados
    base_dir  = output_dir or audio_path.parent
    base_name = audio_path.stem

    for fmt in formats:
        content     = FORMATTERS[fmt](result)
        output_path = base_dir / f"{base_name}.{fmt}"
        save_output(content, output_path, fmt)

    return result


# ──────────────────────────────────────────────
# Recolección de archivos
# ──────────────────────────────────────────────

def collect_audio_files(input_path: Path) -> list[Path]:
    """
    Devuelve lista de archivos de audio a procesar.
    Acepta un archivo individual o un directorio (recursivo).
    """
    if input_path.is_file():
        if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"⚠️  Formato no soportado: {input_path.suffix}")
            print(f"   Formatos válidos: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
            sys.exit(1)
        return [input_path]

    if input_path.is_dir():
        files = sorted(
            p for p in input_path.rglob("*")
            if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            print(f"⚠️  No se encontraron archivos de audio en: {input_path}")
            sys.exit(1)
        return files

    print(f"❌ No existe: {input_path}")
    sys.exit(1)


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whisper-ccstt",
        description="Transcribe archivos de audio con OpenAI Whisper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ejemplos:
  python main.py entrevista.wav
  python main.py entrevista.wav --model medium --language es
  python main.py ./audios/ --format srt --output ./subtitulos/
  python main.py podcast.mp3 --format txt json srt --model large-v3
  python main.py reunion.wav --no-print
        """,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Archivo de audio o carpeta a transcribir.",
    )
    parser.add_argument(
        "--model", "-m",
        default="base",
        choices=AVAILABLE_MODELS,
        help="Modelo de Whisper a usar (default: base). Más grande = más preciso pero más lento.",
    )
    parser.add_argument(
        "--language", "-l",
        default=None,
        metavar="LANG",
        help="Código de idioma (ej: es, en, fr). Si se omite, Whisper lo detecta automáticamente.",
    )
    parser.add_argument(
        "--format", "-f",
        nargs="+",
        default=["txt"],
        choices=OUTPUT_FORMATS,
        dest="formats",
        metavar="FMT",
        help=f"Formato(s) de salida: {', '.join(OUTPUT_FORMATS)} (default: txt). Se pueden combinar.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directorio de salida. Si se omite, se guarda junto al audio.",
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="No imprimir el texto en consola (útil en modo lote).",
    )

    return parser


# ──────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    # Recolectar archivos
    audio_files = collect_audio_files(args.input)
    total       = len(audio_files)

    print(f"\n🔊 Whisper CCSTT")
    print(f"   Modelo:   {args.model}")
    print(f"   Idioma:   {args.language or 'auto-detect'}")
    print(f"   Formatos: {', '.join(args.formats)}")
    print(f"   Archivos: {total}")

    # Cargar modelo una sola vez (costoso en memoria)
    print(f"\n⏳ Cargando modelo '{args.model}'...")
    model = whisper.load_model(args.model)
    print(f"✅ Modelo listo.")

    # Procesar
    errors = []
    for i, audio_path in enumerate(audio_files, start=1):
        if total > 1:
            print(f"\n[{i}/{total}]", end="")
        try:
            transcribe_file(
                audio_path  = audio_path,
                model       = model,
                language    = args.language,
                formats     = args.formats,
                output_dir  = args.output,
                print_text  = not args.no_print,
            )
        except Exception as exc:
            print(f"  ❌ Error en {audio_path.name}: {exc}")
            errors.append((audio_path, exc))

    # Resumen final
    if total > 1:
        succeeded = total - len(errors)
        print(f"\n{'═' * 60}")
        print(f"✅ {succeeded}/{total} archivos transcritos correctamente.")
        if errors:
            print(f"❌ {len(errors)} error(es):")
            for path, exc in errors:
                print(f"   • {path.name}: {exc}")


if __name__ == "__main__":
    main()