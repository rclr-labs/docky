#!/usr/bin/env python3
"""
Pergunte ao Docky pelo terminal.

Uso:
    ./ask.sh "Qual a diferenca entre fluxos alternativos e casos de borda?"
    ./ask.sh --top-k 3 "O que e o modulo BASIS?"
    ./ask.sh                      # modo interativo (chat no terminal)
    ./ask.sh --json "pergunta"    # saida JSON crua

Variaveis: DOCKY_API_URL (default http://localhost:8000)
"""
import argparse
import json
import os
import sys

import httpx

API_URL = os.environ.get("DOCKY_API_URL", "http://localhost:8000")

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def fmt_ms(ms) -> str:
    if not ms:
        return "?"
    return f"{ms/1000:.1f}s" if ms >= 1000 else f"{ms:.0f}ms"


def ask(query: str, top_k: int, as_json: bool) -> None:
    try:
        with httpx.Client(timeout=320) as client:
            resp = client.post(f"{API_URL}/ask", json={"query": query, "top_k_reranked": top_k})
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        print(f"{YELLOW}✗ Nao consegui conectar na API em {API_URL}. "
              f"A stack esta de pe? (docker-compose up -d){RESET}")
        sys.exit(1)
    except httpx.ReadTimeout:
        print(f"{YELLOW}✗ A resposta demorou demais (LLM lento/cold start). Tente de novo.{RESET}")
        sys.exit(1)

    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    answer = data.get("answer", "")
    conf = data.get("confidence", 0.0) or 0.0
    sources = data.get("sources", [])

    print()
    print(f"{BOLD}💬 Resposta{RESET}")
    print(answer)
    print()

    conf_color = GREEN if conf >= 0.3 else (YELLOW if conf >= 0.05 else DIM)
    print(f"{DIM}⏱  busca {fmt_ms(data.get('retrieval_time_ms'))} · "
          f"geracao {fmt_ms(data.get('generation_time_ms'))}{RESET}   "
          f"{conf_color}confianca {conf:.2f}{RESET}")

    if sources:
        print(f"\n{BOLD}📚 Fontes{RESET} ({len(sources)})")
        for s in sources:
            name = s.get("file_name", "?")
            chunk = s.get("chunk_index")
            score = s.get("relevance_score", 0) or 0
            preview = (s.get("preview") or "").replace("\n", " ")[:110]
            print(f"  {CYAN}{name}{RESET} · chunk {chunk} · score {score:.2f}")
            if preview:
                print(f"    {DIM}{preview}...{RESET}")

    if not sources or conf < 0.02:
        print(f"\n{YELLOW}⚠ Confianca baixa: provavelmente a resposta nao esta no acervo "
              f"ingerido (ou exige mais documentos).{RESET}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pergunte ao Docky")
    parser.add_argument("question", nargs="*", help="pergunta (vazio = modo interativo)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    query = " ".join(args.question).strip()

    if query:
        ask(query, args.top_k, args.as_json)
        return

    print(f"{BOLD}Docky — modo interativo{RESET} {DIM}(Ctrl-D ou 'sair' para terminar){RESET}")
    while True:
        try:
            q = input(f"\n{CYAN}pergunta>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in ("sair", "exit", "quit"):
            break
        ask(q, args.top_k, args.as_json)


if __name__ == "__main__":
    main()
