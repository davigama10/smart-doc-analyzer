"""
Teste da integração LLM via Ollama — roda analyze_and_route_full em um documento.

Pré-requisitos:
    1. Ollama instalado e rodando na máquina host (https://ollama.com)
    2. Modelo baixado: ollama pull llama3.2

Uso dentro do container:
    MSYS_NO_PATHCONV=1 docker compose run --rm --entrypoint python smart-doc-analyzer test_llm.py /docs/meu-arquivo.pdf

Modelo customizado:
    MSYS_NO_PATHCONV=1 docker compose run --rm --entrypoint python smart-doc-analyzer test_llm.py /docs/arquivo.pdf qwen2.5:3b
"""

import sys
from doc_analyzer import DocAnalyzer

PDF   = sys.argv[1] if len(sys.argv) > 1 else "/docs/modelo de email.pdf"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "llama3.2"

print(f"\nAnalisando: {PDF}")
print(f"Modelo Ollama: {MODEL}\n")

analyzer = DocAnalyzer(routes_config="routes_example.json", ollama_model=MODEL)
result = analyzer.analyze_and_route_full(PDF)

p = result.profile
print("=== Perfil ===")
print(f"  Tipo:             {p.doc_type.value}")
print(f"  Páginas:          {p.num_pages}")
print(f"  Densidade texto:  {p.text_density:.0%}")
print(f"  Densidade imagem: {p.image_density:.0%}")
print(f"  Tem tabelas:      {p.has_tables}")
print(f"  Manuscrito:       {p.is_handwritten}")

r = result.rule_recommendation
print("\n=== Recomendação por Regras ===")
print(f"  Tier:   {r.tier.value}")
print(f"  Modelo: {r.model}")
print(f"  Rota:   {r.route_name}")
print(f"  Motivo: {r.reason}")

l = result.llm_recommendation
print(f"\n=== Recomendação da LLM (Ollama / {MODEL}) ===")
print(f"  Tier:   {l.tier.value}")
print(f"  Modelo: {l.model}")
print(f"  Motivo: {l.reason}")

print()
if r.tier == l.tier:
    print(">> Regras e LLM concordam no tier.")
else:
    print(f">> Divergência: regras={r.tier.value}  LLM={l.tier.value}")
