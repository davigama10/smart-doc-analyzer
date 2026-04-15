"""
Exemplos de uso do smart-doc-analyzer.
"""

from doc_analyzer import DocAnalyzer, PDFAnalyzer, RuleBasedRouter


# ──────────────────────────────────────────────
# 1. Uso mais simples: analisar + rotear
# ──────────────────────────────────────────────

analyzer = DocAnalyzer(routes_config="routes_example.json")

profile, recommendation = analyzer.analyze_and_route("documento.pdf")

print("=== Perfil do Documento ===")
print(f"Tipo:            {profile.doc_type.value}")
print(f"Páginas:         {profile.num_pages}")
print(f"Densidade texto: {profile.text_density:.0%}")
print(f"Densidade img:   {profile.image_density:.0%}")
print(f"Tem tabelas:     {profile.has_tables}")
print(f"Manuscrito:      {profile.is_handwritten}")

print("\n=== Recomendação de Processamento ===")
print(f"Tier:    {recommendation.tier.value}")
print(f"Modelo:  {recommendation.model}")
print(f"Rota:    {recommendation.route_name}")
print(f"Motivo:  {recommendation.reason}")


# ──────────────────────────────────────────────
# 2. Apenas analisar (sem roteamento)
# ──────────────────────────────────────────────

analyzer_only = DocAnalyzer()
profile = analyzer_only.analyze("imagem.png")
print(profile.to_dict())


# ──────────────────────────────────────────────
# 3. Registrar um analisador customizado para novo formato
# ──────────────────────────────────────────────

from doc_analyzer import BaseAnalyzer, DocumentProfile, DocType, FileType, ProcessingTier
from pathlib import Path

class DocxAnalyzer(BaseAnalyzer):
    def can_analyze(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".docx"

    def analyze(self, file_path: str) -> DocumentProfile:
        # Implementação futura para Word
        return DocumentProfile(
            file_path=file_path,
            file_type=FileType.PDF,        # estender FileType quando necessário
            file_size_bytes=Path(file_path).stat().st_size,
            doc_type=DocType.NATIVE_DIGITAL,
            num_pages=1,
            has_selectable_text=True,
            text_density=1.0,
            avg_chars_per_page=1000.0,
            image_density=0.0,
            has_tables=False,
            table_density=0.0,
            is_handwritten=False,
            handwriting_confidence=0.0,
        )

analyzer.register_analyzer(DocxAnalyzer())
profile = analyzer.analyze("relatorio.docx")


# ──────────────────────────────────────────────
# 4. Roteador customizado (ex: baseado em custo/SLA)
# ──────────────────────────────────────────────

from doc_analyzer import BaseRouter, ProcessingRecommendation, ProcessingTier

class CostAwareRouter(BaseRouter):
    """Sempre prefere processamento local para reduzir custos."""

    def route(self, profile: DocumentProfile) -> ProcessingRecommendation:
        if profile.doc_type.value == "native_digital":
            return ProcessingRecommendation(
                tier=ProcessingTier.NONE,
                model=None,
                route_name="cost-aware-no-ocr",
                reason="Texto selecionável, sem custo de OCR.",
            )
        return ProcessingRecommendation(
            tier=ProcessingTier.LOCAL_LIGHT,
            model="paddle",
            route_name="cost-aware-local",
            reason="Sempre local para minimizar custos.",
        )

cost_analyzer = DocAnalyzer(router=CostAwareRouter())
profile, rec = cost_analyzer.analyze_and_route("documento.pdf")
print(rec.reason)
