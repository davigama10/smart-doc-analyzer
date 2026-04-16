from typing import Optional

import anthropic
from pydantic import BaseModel, Field

from .base import BaseRouter
from ..profile import DocumentProfile, ProcessingRecommendation, ProcessingTier


class _LLMRecommendation(BaseModel):
    tier: str = Field(
        description="Tier de processamento recomendado: 'none', 'local_light', 'local_heavy' ou 'cloud'."
    )
    recommended_model: Optional[str] = Field(
        None,
        description="Nome do modelo sugerido (ex: 'paddle', 'qwen3', 'deepseek', 'gemini-pro-vision'). "
                    "Null se tier for 'none'.",
    )
    reason: str = Field(
        description="Justificativa objetiva (1-2 frases) para a recomendação."
    )


_SYSTEM_PROMPT = """\
Você é um especialista em processamento de documentos, OCR e extração de dados.

Receberá as métricas de um documento extraídas automaticamente e deve recomendar
o melhor método de processamento com base nessas características.

Tiers disponíveis (do mais simples ao mais caro):
- none          → Sem OCR. PDF com texto selecionável — extração direta, sem custo.
- local_light   → Modelo local leve (PaddleOCR). Escaneados simples, boa qualidade de imagem.
- local_heavy   → Modelo local pesado. Use 'qwen3' para docs visualmente complexos/densos em imagens,
                  'deepseek' quando há muitas tabelas estruturadas.
- cloud         → Modelo cloud avançado ('gemini-pro-vision'). Apenas para manuscritos ou docs
                  que exijam capacidade de visão muito superior.

Regra de ouro: prefira sempre o tier mais simples que ainda garanta qualidade.
Justifique com base nas métricas (densidades, tipo, confiança OCR etc.).\
"""


class LLMRouter(BaseRouter):
    """
    Roteador baseado em Claude (LLM) que analisa o DocumentProfile
    e recomenda o melhor método de OCR/processamento.

    Usa o modelo claude-opus-4-6 com structured outputs + prompt caching
    no system prompt (estável entre chamadas).

    Uso:
        router = LLMRouter()                          # usa ANTHROPIC_API_KEY do ambiente
        router = LLMRouter(api_key="sk-ant-...")      # chave explícita
        rec = router.route(profile)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-6",
    ):
        """
        Args:
            api_key: Chave da API Anthropic. Se None, usa a variável de ambiente
                     ANTHROPIC_API_KEY.
            model:   Modelo Claude a ser usado. Padrão: claude-opus-4-6.
        """
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self._model = model

    def route(self, profile: DocumentProfile) -> ProcessingRecommendation:
        """
        Envia o DocumentProfile para o Claude e retorna a recomendação de processamento.

        Args:
            profile: Perfil do documento gerado pelo analisador.

        Returns:
            ProcessingRecommendation com tier, modelo e justificativa da LLM.

        Raises:
            anthropic.APIError: Em caso de falha na chamada à API.
        """
        profile_text = self._format_profile(profile)

        response = self._client.messages.parse(
            model=self._model,
            max_tokens=512,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Analise o perfil abaixo e recomende o melhor método de processamento:\n\n"
                        f"{profile_text}"
                    ),
                }
            ],
            output_format=_LLMRecommendation,
        )

        rec: _LLMRecommendation = response.parsed_output

        try:
            tier = ProcessingTier(rec.tier)
        except ValueError:
            tier = ProcessingTier.LOCAL_LIGHT

        return ProcessingRecommendation(
            tier=tier,
            model=rec.recommended_model,
            route_name="llm-router",
            reason=rec.reason,
        )

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    @staticmethod
    def _format_profile(profile: DocumentProfile) -> str:
        d = profile.to_dict()
        lines = []
        for key, value in d.items():
            if key == "raw_metrics":
                continue
            lines.append(f"  {key}: {value}")

        raw = d.get("raw_metrics", {})
        if raw:
            lines.append("  raw_metrics:")
            for k, v in raw.items():
                lines.append(f"    {k}: {v}")

        return "\n".join(lines)
