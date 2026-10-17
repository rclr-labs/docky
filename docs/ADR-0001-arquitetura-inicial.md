# ADR-0001: Arquitetura inicial do Docky

## Status
Aceito

## Contexto
Precisamos de um chatbot de IA para responder perguntas sobre a documentação de uma aplicação,
com baixo custo de tokens, rodando em VPS sem GPU.

## Decisão
- RAG com roteamento por tipo de dado (markdown, API spec, código, tabelas, PDF, imagem, transcrição).
- Embeddings e re-rank locais e leves (bge-small-en-v1.5, bge-reranker-base).
- LLM de resposta: modelo pequeno local servido via Ollama (Phi-3.5-mini ou Qwen2.5-3B).
- Vector DB: Qdrant, self-hosted via Docker.
- Ingestão roda offline; a VPS de produção recebe apenas o índice pronto (snapshot do Qdrant).

## Consequências
- Custo operacional baixo (sem custo por token de API externa).
- Latência de resposta maior que modelos cloud grandes, aceitável para Q&A de documentação.
- Qualidade de raciocínio multi-step é menor que modelos frontier; mitigado por re-rank agressivo
  e compressão de contexto antes do prompt final.
