#!/usr/bin/env python3
"""
Validacao da ingestao do Docky.

Duas checagens:
  1. INVENTARIO  - o que esta de fato no Qdrant: chunks por arquivo, tipos,
                   anomalias (chunks vazios/minusculos, duplicatas exatas,
                   colisao de doc_id entre arquivos diferentes).
  2. RECUPERACAO - roda um conjunto de perguntas conhecidas (YAML) e verifica:
                     - o arquivo esperado aparece no top-k?
                     - alguma palavra-chave obrigatoria aparece nos chunks?
                   Opcionalmente (--ask), roda o pipeline RAG completo e
                   verifica se a resposta do LLM contem as palavras-chave.

Uso (no host, com a stack de pe):
    python3 scripts/validate_ingestion.py
    python3 scripts/validate_ingestion.py --cases tests/validation/retrieval_cases.yml
    python3 scripts/validate_ingestion.py --ask            # inclui respostas do LLM (lento)
    python3 scripts/validate_ingestion.py --top-k 3

Ou dentro do container:
    docker exec docky-api-1 python3 /app/scripts/validate_ingestion.py

Variaveis de ambiente:
    DOCKY_API_URL   default http://localhost:8000
    DOCKY_QDRANT_URL default http://localhost:6333  (usado pelo inventario)
"""
import argparse
import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict

import httpx

def _default_qdrant_url() -> str:
    """Host: localhost:6333. Container: usa settings/env ou o hostname do servico."""
    if os.environ.get("DOCKY_QDRANT_URL"):
        return os.environ["DOCKY_QDRANT_URL"]
    if os.environ.get("QDRANT_URL"):
        return os.environ["QDRANT_URL"]
    try:  # dentro do container, aproveita a config da propria API
        from api.config import settings
        return settings.QDRANT_URL
    except Exception:
        return "http://localhost:6333"


API_URL = os.environ.get("DOCKY_API_URL", "http://localhost:8000")
QDRANT_URL = _default_qdrant_url()
COLLECTION = os.environ.get("QDRANT_COLLECTION_NAME", "docky_documents")
# Fallbacks tentados quando o Qdrant padrao nao responde
QDRANT_FALLBACKS = ["http://qdrant:6333", "http://localhost:6333"]

def norm(s: str) -> str:
    """NFC + lowercase: evita falha por composicao Unicode (macOS usa NFD)."""
    return unicodedata.normalize("NFC", s or "").lower()


OK = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"


# ---------------------------------------------------------------- inventario

def fetch_all_points(client: httpx.Client) -> list[dict]:
    points, offset = [], None
    while True:
        body = {"limit": 500, "with_payload": True, "with_vector": False}
        if offset is not None:
            body["offset"] = offset
        res = client.post(f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll", json=body).json()["result"]
        points.extend(res["points"])
        offset = res.get("next_page_offset")
        if offset is None:
            break
    return points


def resolve_qdrant_url() -> str:
    """Retorna a primeira URL do Qdrant que responder."""
    candidates = [QDRANT_URL] + [u for u in QDRANT_FALLBACKS if u != QDRANT_URL]
    for url in candidates:
        try:
            with httpx.Client(timeout=5) as c:
                if c.get(f"{url}/collections").status_code == 200:
                    return url
        except Exception:
            continue
    return QDRANT_URL


def run_inventory() -> tuple[bool, dict]:
    print("=" * 78)
    print("1) INVENTARIO DO INDICE")
    print("=" * 78)

    qdrant = resolve_qdrant_url()
    global QDRANT_URL
    QDRANT_URL = qdrant
    with httpx.Client(timeout=60) as client:
        try:
            info = client.get(f"{qdrant}/collections/{COLLECTION}").json()["result"]
        except Exception as e:
            print(f"{FAIL} Qdrant inacessivel em {qdrant}: {e}")
            return False, {}
        points = fetch_all_points(client)

    total = info.get("points_count", 0)
    print(f"Collection '{COLLECTION}': {total} chunks indexados, "
          f"vetores dim={info['config']['params']['vectors']['size']}")
    print()

    if not points:
        print(f"{FAIL} Nenhum chunk indexado.")
        return False, {"points": []}

    by_file = defaultdict(list)
    for p in points:
        by_file[p["payload"].get("file_name", "<sem file_name>")].append(p["payload"])

    print(f"{'ARQUIVO':<58} {'CHUNKS':>6} {'TIPO':>6} {'CHARS':>8}")
    print("-" * 78)
    for fname in sorted(by_file):
        pls = by_file[fname]
        ftype = pls[0].get("file_type", "?")
        chars = sum(len(p.get("chunk_text", "")) for p in pls)
        print(f"{fname[:56]:<58} {len(pls):>6} {str(ftype):>6} {chars:>8}")
    print()

    problems, warnings = [], []

    # anomalias por arquivo
    for fname, pls in by_file.items():
        empty = sum(1 for p in pls if not p.get("chunk_text", "").strip())
        tiny = sum(1 for p in pls if 0 < len(p.get("chunk_text", "").strip()) < 20)
        if empty:
            problems.append(f"{fname}: {empty} chunk(s) vazio(s)")
        if tiny:
            warnings.append(f"{fname}: {tiny} chunk(s) com <20 chars (provavel titulo solto)")

    # duplicatas exatas
    texts = Counter(p["payload"].get("chunk_text", "") for p in points)
    dup_groups = {t: c for t, c in texts.items() if c > 1 and t.strip()}
    if dup_groups:
        warnings.append(f"{len(dup_groups)} chunk(s) de texto identico aparecem mais de uma vez "
                        f"(re-ingestao repetida?)")

    # colisao de doc_id entre arquivos diferentes
    doc_id_files = defaultdict(set)
    for p in points:
        doc_id_files[p["payload"].get("doc_id", "?")].add(p["payload"].get("file_name", "?"))
    collisions = {d: f for d, f in doc_id_files.items() if len(f) > 1}
    if collisions:
        problems.append(f"{len(collisions)} doc_id(s) compartilhado(s) entre arquivos diferentes "
                        f"(chunks podem ter se sobrescrito na indexacao)")

    # distribuição por tipo
    print("Por tipo:", dict(Counter(p["payload"].get("file_type", "?") for p in points)))
    print()

    for w in warnings:
        print(f"{WARN} {w}")
    for p_ in problems:
        print(f"{FAIL} {p_}")
    if not warnings and not problems:
        print(f"{OK} Inventario integro.")
    print()

    return not problems, {"points": points, "by_file": by_file}


# ---------------------------------------------------------------- recuperacao

def load_cases(path: str) -> list[dict]:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("cases", [])


def run_retrieval(cases: list[dict], top_k: int, ask: bool) -> bool:
    print("=" * 78)
    print(f"2) RECUPERACAO - {len(cases)} caso(s), top_k={top_k}"
          + (" + respostas do LLM" if ask else ""))
    print("=" * 78)

    all_ok = True
    with httpx.Client(timeout=300) as client:
        for case in cases:
            cid = case.get("id", case["query"][:30])
            query = case["query"]
            expect_files = case.get("expect_any_files", [])
            keywords = [norm(k) for k in case.get("expect_keywords", [])]

            try:
                resp = client.post(f"{API_URL}/search",
                                   json={"query": query, "top_k_reranked": top_k}).json()
            except Exception as e:
                print(f"{FAIL} [{cid}] erro na busca: {e}")
                all_ok = False
                continue

            results = resp.get("results", [])
            got_files = [r.get("file_name", "?") for r in results]
            joined = norm(" ".join(r.get("content", "") for r in results))
            top_score = max((r.get("score", 0) for r in results), default=0)

            file_ok = (not expect_files) or any(
                norm(exp) in norm(got) for exp in expect_files for got in got_files
            )
            kw_ok = (not keywords) or any(k in joined for k in keywords)

            status = OK if (file_ok and kw_ok) else FAIL
            if not (file_ok and kw_ok):
                all_ok = False

            print(f"{status} [{cid}] top_score={top_score:.3f} | {query[:60]}")
            if not file_ok:
                print(f"      arquivo esperado {expect_files} nao apareceu; veio: {got_files}")
            if not kw_ok:
                print(f"      palavras-chave {keywords} ausentes nos chunks recuperados")

            if ask:
                try:
                    ans = client.post(f"{API_URL}/ask", json={"query": query}).json()
                except Exception as e:
                    print(f"      {FAIL} /ask erro: {e}")
                    all_ok = False
                    continue
                answer = norm(ans.get("answer") or "")
                conf = ans.get("confidence")
                if keywords:
                    ok_ans = any(k in answer for k in keywords)
                else:
                    ok_ans = bool(ans.get("sources"))
                mark = OK if ok_ans else FAIL
                if not ok_ans:
                    all_ok = False
                print(f"      {mark} resposta (conf={conf:.3f}): {ans.get('answer','')[:110]}...")
            print()

    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Validacao da ingestao do Docky")
    parser.add_argument("--cases", default="tests/validation/retrieval_cases.yml",
                        help="arquivo YAML com os casos de recuperacao")
    parser.add_argument("--top-k", type=int, default=5, help="resultados finais por busca")
    parser.add_argument("--ask", action="store_true", help="rodar tambem o pipeline RAG completo (lento)")
    parser.add_argument("--skip-inventory", action="store_true")
    args = parser.parse_args()

    inventory_ok = True
    if not args.skip_inventory:
        inventory_ok, _ = run_inventory()

    retrieval_ok = True
    if os.path.exists(args.cases):
        cases = load_cases(args.cases)
        retrieval_ok = run_retrieval(cases, args.top_k, args.ask)
    else:
        print(f"{WARN} Arquivo de casos nao encontrado: {args.cases} (pulando recuperacao)")

    print("=" * 78)
    ok = inventory_ok and retrieval_ok
    print(f"{OK if ok else FAIL} RESULTADO FINAL: "
          f"inventario={'ok' if inventory_ok else 'FALHOU'}, "
          f"recuperacao={'ok' if retrieval_ok else 'FALHOU'}")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())