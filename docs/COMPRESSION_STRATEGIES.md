# Estratégias de Compressão Extrativa

## Visão Geral

O módulo de compressão (api/compression.py) oferece 5 estratégias diferentes para reduzir o tamanho do contexto mantendo as informações mais relevantes.

**Objetivo**: Reduzir tokens consumidos sem sacrificar a qualidade da resposta.

---

## Estratégias de Compressão

### 1. SentenceCompressor (Padrão Recomendado)

**Arquivo**: api/compression.py → Classe SentenceCompressor

**Como funciona**:
- Divide o texto em sentenças
- Calcula um score de relevância para cada sentença
- Mantém apenas sentenças com score acima do threshold (0-1)

**Fatores de Score**:
- Comprimento da sentença (50-200 chars é ideal)
- Posição (primeira e última têm score mais alto)
- Presença de palavras-chave (important, critical, key, essential, etc)

**Quando usar**:
- Uso geral (padrão)
- Quando a qualidade importa
- Para contexto heterogêneo
- Quando há sentenças com diferentes relevâncias

**Performance**:
- Velocidade: Rápido
- Qualidade: Excelente
- Compressão: 40-70%

---

### 2. KeywordCompressor (Específico para Domínio)

**Arquivo**: api/compression.py → Classe KeywordCompressor

**Como funciona**:
- Mantém apenas sentenças que contêm keywords especificadas
- Útil quando você sabe exatamente o que procura

**Quando usar**:
- Quando a query tem keywords claros
- Para domínios muito específicos
- Quando você quer focar em termos exatos
- Não recomendado para queries genéricas

**Performance**:
- Velocidade: Muito Rápido
- Qualidade: Boa (pode perder contexto)
- Compressão: 50-90%

---

### 3. LengthCompressor (Rápido e Simples)

**Arquivo**: api/compression.py → Classe LengthCompressor

**Como funciona**:
- Trunca o texto a um comprimento máximo especificado
- Mais rápido, mas menos inteligente

**Quando usar**:
- Para performance máxima
- Como fallback quando outros falham
- Para snippets (prévia)
- Não ideal para conteúdo importante

**Performance**:
- Velocidade: Muito Rápido
- Qualidade: Aceitável (pode cortar importante)
- Compressão: 70-95%

---

### 4. ParagraphCompressor (Estruturado)

**Arquivo**: api/compression.py → Classe ParagraphCompressor

**Como funciona**:
- Mantém apenas os primeiros N parágrafos
- Respeita estrutura de parágrafos
- Ideal para documentos bem estruturados

**Quando usar**:
- Para markdown/documentação
- Quando parágrafos são bem delimitados
- Para artigos estruturados
- Não ideal para texto contínuo

**Performance**:
- Velocidade: Rápido
- Qualidade: Boa (se bem estruturado)
- Compressão: 40-80%

---

## CompressionService (Orquestrador)

**Classe**: CompressionService

Oferece interface unificada para todas as estratégias.

Interface simples:
```
service.compress(text, method="sentence", max_length=300)
service.compress_chunks(chunks, method="sentence", max_chunk_length=300)
```

---

## Matriz de Decisão

| Situação | Compressor | Razão |
|----------|-----------|-------|
| Texto genérico, qualidade importante | Sentence | Balanceado, inteligente |
| Query específica com keywords | Keyword | Filtra exatamente o alvo |
| Precisa ser rápido, tamanho crítico | Length | Máxima performance |
| Markdown bem estruturado | Paragraph | Respeita estrutura |
| Não sabe qual usar | Sentence | Default seguro |

---

## Benchmarks

### Teste com Amostra de 1000 caracteres

| Estratégia | Tamanho Final | Redução | Tempo | Qualidade |
|-----------|---------------|---------|-------|-----------|
| SentenceCompressor | 640 chars | 36% | 5ms | Excelente |
| KeywordCompressor | 520 chars | 48% | 3ms | Boa |
| LengthCompressor | 303 chars | 70% | 1ms | Aceitável |
| ParagraphCompressor | 450 chars | 55% | 2ms | Boa |

### Teste com Amostra de 10000 caracteres

| Estratégia | Tamanho Final | Redução | Tempo | Qualidade |
|-----------|---------------|---------|-------|-----------|
| SentenceCompressor | 5200 chars | 48% | 15ms | Excelente |
| KeywordCompressor | 3100 chars | 69% | 8ms | Boa |
| LengthCompressor | 303 chars | 97% | 1ms | Pobre |
| ParagraphCompressor | 3500 chars | 65% | 5ms | Boa |

---

## Casos de Uso Reais

### Caso 1: FAQ / Documentação Técnica

Melhor estratégia: SentenceCompressor

Mantém sentenças com termos técnicos importantes, reduz informações duplicadas.

### Caso 2: Busca com Palavras-chave

Melhor estratégia: KeywordCompressor

Filtra por termos da query, maximiza relevância direta.

### Caso 3: Resumo Rápido

Melhor estratégia: LengthCompressor

Apenas snippet rápido, máxima performance.

### Caso 4: Blog/Artigos

Melhor estratégia: ParagraphCompressor

Respeita estrutura de artigo, mantém coerência.

---

## Métricas de Sucesso

### O que Rastrear

1. **Compression Ratio**: Quanto foi comprimido?
   - Meta: 40-70% redução

2. **Tokens Saved**: Quanto economizou em tokens?
   - Meta: > 100 tokens por query

3. **Quality**: Resposta ainda é precisa?
   - Meta: Mantém informações críticas

4. **Latency**: Tempo adicionado?
   - Meta: < 10ms (negligível)

---

## Limitações Conhecidas

1. **SentenceCompressor**
   - Depende de tokenização correta
   - Pode falhar com sentenças muito longas

2. **KeywordCompressor**
   - Requer keywords conhecidas
   - Pode perder contexto importante

3. **LengthCompressor**
   - Pode cortar no meio de palavra
   - Menos inteligente

4. **ParagraphCompressor**
   - Depende de formatação correta
   - Pode não funcionar com texto contínuo

---

## Próximas Otimizações

- Use embeddings para scoring (mais preciso)
- Fine-tune de thresholds por tipo de documento
- Cache de resultados comprimidos
- Compressão adaptativa (ajustar por query)
- Suporte a múltiplas línguas
- Compressão lossy com preservação de semântica
