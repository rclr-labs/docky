#!/bin/bash
# Ingerir todos os documentos (.md, .txt, .json, .yaml) de uma pasta no Docky.
# Roda dentro do container docky-api-1, onde o SearchService ja aponta pro Qdrant certo.
#
# Uso:
#   ./ingest_folder.sh <pasta-dentro-do-container>
#
# Exemplo (pasta ja copiada para data/raw, que esta montada como volume):
#   ./ingest_folder.sh data/raw

set -e

if [ -z "$1" ]; then
  echo "Uso: ./ingest_folder.sh <pasta>"
  echo "Exemplo: ./ingest_folder.sh data/raw"
  exit 1
fi

FOLDER="$1"
CONTAINER="docky-api-1"

cat > /tmp/_docky_ingest_folder.py << PYEOF
import asyncio
import sys
import uuid
from pathlib import Path

from ingest.ingestors import DocumentIngestor
from api.search import SearchService

FOLDER = "$FOLDER"
EXTENSIONS = [".md", ".txt", ".json", ".yaml", ".yml", ".pptx", ".vtt", ".srt"]

async def main():
    folder = Path(FOLDER)
    if not folder.is_dir():
        print(f"Erro: pasta nao encontrada dentro do container: {FOLDER}")
        sys.exit(1)

    files = [f for ext in EXTENSIONS for f in folder.rglob(f"*{ext}") if f.is_file()]
    if not files:
        print("Nenhum arquivo encontrado")
        sys.exit(1)

    print(f"Encontrados: {len(files)} arquivo(s)\n")

    ingestor = DocumentIngestor(SearchService())
    ok, fail = 0, 0

    for f in files:
        doc_id = str(uuid.uuid4())  # doc_id UNICO por arquivo - nunca reusar entre arquivos
        print(f"Ingerindo: {f}...", end=" ", flush=True)
        try:
            result = await ingestor.ingest(str(f), doc_id=doc_id)
            if result.status == "success":
                print(f"OK ({result.chunks_indexed} chunks)")
                ok += 1
            else:
                print(f"FALHOU: {result.error_message}")
                fail += 1
        except Exception as e:
            print(f"ERRO: {e}")
            fail += 1

    print(f"\nConcluido: {ok} ok, {fail} falha(s), de {len(files)} arquivo(s)")

asyncio.run(main())
PYEOF

echo "Copiando script para o container $CONTAINER..."
docker cp /tmp/_docky_ingest_folder.py "$CONTAINER:/app/_docky_ingest_folder.py"

echo "Ingerindo pasta '$FOLDER' dentro do container..."
echo "=================================================="
docker exec "$CONTAINER" python3 /app/_docky_ingest_folder.py

rm -f /tmp/_docky_ingest_folder.py

