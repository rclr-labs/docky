# Docky

Chatbot de documentação com RAG otimizado para baixo consumo de tokens, rodando em VPS com modelo LLM local pequeno.

## Visão geral

Docky responde perguntas sobre a documentação de uma aplicação (markdown, specs de API, código-fonte,
tabelas, PDFs, diagramas e transcrições) usando um pipeline de RAG (Retrieval-Augmented Generation)
desenhado para minimizar tokens em cada etapa — da indexação à resposta final.

## Arquitetura

```
Pergunta do usuário
   │
   ▼
[Roteamento por tipo de dado]   (filtro de metadados antes da busca vetorial)
   │
   ▼
[Busca vetorial: top 15-20]      (Qdrant + bge-small-en-v1.5)
   │
   ▼
[Re-rank → top 3-5]              (bge-reranker-base, local)
   │
   ▼
[Compressão extrativa]           (reduz cada chunk ao trecho relevante)
   │
   ▼
[Prompt compacto + cache de prefixo]
   │
   ▼
[LLM local pequeno]  (Phi-3.5-mini / Qwen2.5-3B via Ollama) → resposta
```

## Stack

- **Orquestração**: LlamaIndex (Python)
- **Vector DB**: Qdrant
- **Embeddings**: bge-small-en-v1.5
- **Re-rank**: bge-reranker-base
- **LLM**: Phi-3.5-mini ou Qwen2.5-3B, servido via Ollama
- **Backend**: FastAPI
- **Deploy**: Docker Compose, VPS sem GPU

## Estrutura de pastas

```
docky/
├── ingest/           # pipeline de ingestão por tipo de dado
│   └── loaders/      # 1 loader por tipo (markdown, openapi, código, tabelas, pdf, imagem, transcrição)
├── api/               # backend FastAPI (busca → rerank → prompt → LLM)
├── llm/               # Modelfile / configs do Ollama
├── data/
│   ├── raw/           # documentação original (entrada)
│   └── processed/     # chunks processados / snapshots do índice
├── docs/              # documentação do próprio projeto (ADRs, decisões)
└── docker-compose.yml # Ollama + Qdrant + API
```

## Tipos de dados suportados

- Markdown/texto (guias, tutoriais, FAQs)
- Especificação de API (OpenAPI/Swagger)
- Código-fonte / docstrings
- Tabelas estruturadas (CSV, planilhas)
- PDFs
- Imagens/diagramas (via legenda gerada por vision LLM)
- Transcrições (vídeo/áudio via Whisper)

## Status

Projeto em fase inicial de estruturação. Em desenvolvimento via software factory.
