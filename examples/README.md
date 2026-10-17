# Exemplos de Uso - Document Ingestor

Exemplos de como usar o DocumentIngestor para carregar e indexar documentos.

## Pré-requisitos

- Qdrant rodando e acessível
- Variáveis de ambiente configuradas (QDRANT_URL, EMBEDDING_MODEL, etc)

## Exemplos

### 1. Ingestão Simples ([01_simple_ingest.py](./01_simple_ingest.py))

Ingestar um documento único e verificar o resultado.

```bash
python examples/01_simple_ingest.py
```

**Saída:**
```
Status: success
Arquivo: README.md
Chunks indexados: 15
```

### 2. Ingestão em Batch ([02_batch_ingest.py](./02_batch_ingest.py))

Ingestar múltiplos documentos de um diretório.

```bash
python examples/02_batch_ingest.py
```

**Saída:**
```
Encontrados 12 documentos

Resumo da ingestão:
  Sucesso: 12/12
  Total de chunks: 184
```

### 3. Ingestão + Busca ([03_ingest_and_search.py](./03_ingest_and_search.py))

Ingestar um documento e depois fazer busca com re-ranking.

```bash
python examples/03_ingest_and_search.py
```

**Saída:**
```
✅ Ingestado: guide.md
   Chunks: 8

Buscando: Como usar o sistema?

Resultados (3):

[1] Score: 0.821
    Arquivo: guide.md
    Preview: Bem-vindo ao guide. Este documento...

[2] Score: 0.754
    Arquivo: README.md
    Preview: Este projeto implementa um sistema...

[3] Score: 0.698
    Arquivo: api.md
    Preview: A API oferece os seguintes endpoints...
```

### 4. Múltiplos Formatos ([04_multiple_formats.py](./04_multiple_formats.py))

Demonstra suporte para diferentes tipos de arquivo.

```bash
python examples/04_multiple_formats.py
```

**Saída:**
```
Formatos suportados: .txt, .md, .json, .yaml, .yml

Ingestando: README.txt
  ✅ 3 chunks

Ingestando: docs/guide.md
  ✅ 12 chunks

Ingestando: api/openapi.json
  ✅ 5 chunks

Ingestando: api/swagger.yaml
  ✅ 5 chunks
```

## Formatos Suportados

- **.txt** - Arquivos de texto simples
- **.md** - Markdown com preservação de estrutura
- **.json** - OpenAPI/Swagger JSON
- **.yaml/.yml** - OpenAPI/Swagger YAML

## Informações sobre Chunks

Cada formato tem sua estratégia de chunking:

- **Texto**: Chunking genérico por tamanho
- **Markdown**: Chunking estruturado por seções/headings
- **OpenAPI**: Um chunk por operação (endpoint)

## Metadados

Cada chunk armazenado inclui:

- `file_name` - Nome do arquivo original
- `file_path` - Caminho completo do arquivo
- `file_type` - Extensão do arquivo
- `file_size` - Tamanho em bytes
- `chunk_index` - Índice do chunk dentro do documento
- `doc_id` - ID único do documento
- `section` - Seção (para Markdown)
- `heading_hierarchy` - Hierarquia de headings (para Markdown)
- `api_title` - Título da API (para OpenAPI)
- `api_version` - Versão da API (para OpenAPI)

## Customização

### Tamanho de Chunks

```python
result = await ingestor.ingest(
    file_path="document.md",
    chunk_size=1024,      # Aumentar tamanho
    chunk_overlap=100,    # Aumentar overlap
)
```

### ID Customizado

```python
result = await ingestor.ingest(
    file_path="guide.md",
    doc_id="my-custom-id-123",
)
```

## Tratamento de Erros

```python
results = await ingestor.ingest_batch(file_paths)

for result in results:
    if result.status == "error":
        print(f"❌ {result.file_name}: {result.error_message}")
    else:
        print(f"✅ {result.file_name}: {result.chunks_indexed} chunks")
```

## Performance

- **Markdown**: ~1-5ms por chunk (parsing + embedding)
- **OpenAPI**: ~2-8ms por operação
- **Texto**: ~1-3ms por chunk
- **Batch**: Processamento paralelo recomendado para >10 documentos
