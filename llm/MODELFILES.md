# Modelfiles Ollama com Prefix Caching

## Visão Geral

Dois Modelfiles otimizados para Docky, cada um com diferentes características de performance:

- **Modelfile.phi**: Phi-3.5-mini (mais rápido, menos memória)
- **Modelfile.qwen**: Qwen2.5-3B (maior contexto, melhor qualidade)

## Características Compartilhadas

### Prefix Caching (KV Cache)

O cache de prefixo reduz a computação ao manter chaves e valores (K,V) para tokens processados:

- **num_batch**: Controla quantos tokens são processados em paralelo
  - Phi: 128 (balance entre speed e memória)
  - Qwen: 256 (maior capacity)

- **num_predict**: Limite máximo de tokens a gerar
  - Phi: 512 (respostas concisas)
  - Qwen: 1024 (respostas mais detalhadas)

### Compactação de Prompts

O system prompt foi reduzido ao essencial:
- Apenas instruções diretas
- Sem exemplos nos prompts
- Foco em clareza e concisão

### Hiperparâmetros

| Parâmetro | Phi | Qwen | Efeito |
|-----------|-----|------|--------|
| temperature | 0.3 | 0.3 | Determinístico, foco em relevância |
| top_p | 0.9 | 0.95 | Núcleo de distribuição de probabilidade |
| num_ctx | 4096 | 8192 | Tamanho máximo da janela de contexto |

## Como Usar

### Build de Modelo Custom

```bash
# Phi-3.5-mini
ollama create docky-phi -f ./llm/Modelfile.phi

# Qwen2.5-3B
ollama create docky-qwen -f ./llm/Modelfile.qwen
```

### Teste Local

```bash
# Testar Phi
ollama run docky-phi "What is RAG?"

# Testar Qwen
ollama run docky-qwen "What is RAG?"
```

### Usar no .env

```env
# Para Phi
OLLAMA_MODEL=docky-phi

# Para Qwen (melhor qualidade)
OLLAMA_MODEL=docky-qwen
```

## Performance Esperada

### Phi-3.5-mini
- **Latência**: ~200-400ms por resposta
- **Memória**: 3-4GB RAM
- **Throughput**: 5-10 req/s
- **Qualidade**: Adequada para respostas curtas

### Qwen2.5-3B
- **Latência**: ~400-800ms por resposta
- **Memória**: 5-6GB RAM
- **Throughput**: 3-5 req/s
- **Qualidade**: Melhor compreensão e formatação

## Otimizações Futuras

- [ ] Quantização (4-bit) para reduzir memória
- [ ] LoRA fine-tuning para domínio específico
- [ ] Speculative decoding para parallelização
- [ ] Dynamic prompt compression baseada em token count
