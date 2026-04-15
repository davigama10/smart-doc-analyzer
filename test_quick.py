"""
Teste rápido do smart-doc-analyzer.
Execute com: python test_quick.py <caminho_do_arquivo>

Exemplo:
    python test_quick.py meu_documento.pdf
    python test_quick.py imagem.png
"""

import sys
import json
from pathlib import Path

# ── permite rodar sem instalar o pacote ──
sys.path.insert(0, str(Path(__file__).parent))

from doc_analyzer import DocAnalyzer


def main():
    if len(sys.argv) < 2:
        print("Uso: python test_quick.py <caminho_do_arquivo>")
        print("Exemplo: python test_quick.py documento.pdf")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"[ERRO] Arquivo não encontrado: {file_path}")
        sys.exit(1)

    routes_config = Path(__file__).parent / "routes_example.json"
    analyzer = DocAnalyzer(routes_config=str(routes_config))

    print(f"\nAnalisando: {file_path}")
    print("=" * 50)

    try:
        profile, recommendation = analyzer.analyze_and_route(file_path)
    except Exception as e:
        print(f"[ERRO] {e}")
        sys.exit(1)

    print("\n📄 PERFIL DO DOCUMENTO")
    print(f"  Tipo do arquivo : {profile.file_type.value}")
    print(f"  Tipo detectado  : {profile.doc_type.value}")
    print(f"  Páginas         : {profile.num_pages}")
    print(f"  Tamanho         : {profile.file_size_bytes / 1024:.1f} KB")
    print(f"  Texto selecion. : {profile.has_selectable_text}")
    print(f"  Densidade texto : {profile.text_density:.0%}")
    print(f"  Densidade imag. : {profile.image_density:.0%}")
    print(f"  Tem tabelas     : {profile.has_tables}  ({profile.table_density:.0%} das páginas)")
    print(f"  Manuscrito      : {profile.is_handwritten}  (confiança: {profile.handwriting_confidence:.0%})")

    print("\n⚙️  RECOMENDAÇÃO DE PROCESSAMENTO")
    print(f"  Tier    : {recommendation.tier.value}")
    print(f"  Modelo  : {recommendation.model or '(nenhum)'}")
    print(f"  Rota    : {recommendation.route_name or 'padrão'}")
    print(f"  Motivo  : {recommendation.reason}")

    print("\n📊 MÉTRICAS BRUTAS")
    print(json.dumps(profile.raw_metrics, indent=4, ensure_ascii=False))

    print("\n" + "=" * 50)
    print("Teste concluído com sucesso.")


if __name__ == "__main__":
    main()
