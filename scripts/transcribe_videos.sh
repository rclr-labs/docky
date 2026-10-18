#!/bin/bash
# Transcrever videos do acervo PITQA (exports de Meet/Zoom) para .vtt usando
# mlx-whisper com aceleracao Apple Silicon. Roda no Mac host (ADR-0001:
# ingestao e offline; a VPS/container so recebe o indice pronto).
#
# Comportamento:
#   - Varre a pasta recursivamente por videos (.mp4 .m4a .mov .mkv .webm)
#   - Se ja existir um .vtt com o mesmo nome ao lado (ex: export do Zoom),
#     PULA a transcricao (aproveita a transcricao pronta da plataforma).
#   - Caso contrario, transcreve com Whisper (PT) e salva o .vtt ao lado.
#
# Uso:
#   ./scripts/transcribe_videos.sh <pasta-com-videos> [modelo]
#   modelo padrao: mlx-community/whisper-large-v3-turbo (rapido e preciso em PT)

set -e

FOLDER="${1:?Uso: ./scripts/transcribe_videos.sh <pasta> [modelo]}"
MODEL="${2:-mlx-community/whisper-large-v3-turbo}"

if [ ! -d "$FOLDER" ]; then
  echo "Erro: pasta nao encontrada: $FOLDER"
  exit 1
fi

command -v mlx_whisper >/dev/null || { echo "mlx_whisper nao instalado: pip3 install mlx-whisper"; exit 1; }

total=0; skipped=0; done_count=0; failed=0

find "$FOLDER" -type f \( -iname "*.mp4" -o -iname "*.m4a" -o -iname "*.mov" -o -iname "*.mkv" -o -iname "*.webm" \) -print0 |
while IFS= read -r -d "" video; do
  total=$((total+1))
  dir="$(dirname "$video")"
  base="$(basename "$video")"
  stem="${base%.*}"
  vtt="$dir/$stem.vtt"

  if [ -f "$vtt" ]; then
    echo "SKIP (vtt ja existe): $base"
    skipped=$((skipped+1))
    continue
  fi

  echo "TRANSCREVENDO: $base"
  if mlx_whisper "$video" \
      --model "$MODEL" \
      --language pt \
      --task transcribe \
      --output-format vtt \
      --output-dir "$dir" \
      --output-name "$stem" \
      --verbose False; then
    echo "  OK -> $vtt"
    done_count=$((done_count+1))
  else
    echo "  FALHOU: $base"
    failed=$((failed+1))
  fi
done

echo ""
echo "Transcricao concluida. Agora ingira a pasta com:"
echo "  ./ingest_folder.sh <pasta-copiada-para-data/raw>"
