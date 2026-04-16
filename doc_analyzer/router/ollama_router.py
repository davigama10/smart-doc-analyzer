import json
from typing import Optional

import ollama as _ollama
from pydantic import BaseModel, Field

from .base import BaseRouter
from ..profile import DocumentProfile, ProcessingRecommendation, ProcessingTier


class _OllamaRecommendation(BaseModel):
    tier: str = Field(
        description="Tier de processamento: 'none', 'local_light', 'local_heavy' ou 'cloud'."
    )
    recommended_model: Optional[str] = Field(
        None,
        description="Modelo sugerido: 'paddle', 'qwen3', 'deepseek' ou null se tier for 'none'.",
    )
    reason: str = Field(
        description="Justificativa objetiva (1-2 frases) para a recomendação."
    )


_SYSTEM_PROMPT = """\
Você é um especialista em OCR e processamento de documentos.

Receberá métricas extraídas de um documento e deve recomendar o melhor método de processamento.

Tiers disponíveis (do mais simples ao mais caro):
- none         → Sem OCR. PDF com texto selecionável — extração direta.
- local_light  → OCR leve (paddle). Documentos escaneados simples, boa qualidade.
- local_heavy  → OCR pesado. Use 'qwen3' para imagens densas, 'deepseek' para tabelas.
- cloud        → Modelo cloud avançado. Apenas para manuscritos complexos.

Prefira sempre o tier mais simples que ainda garanta qualidade.
Responda APENAS com o JSON solicitado, sem texto adicional.\
"""


class OllamaRouter(BaseRouter):
    """
    Roteador baseado em Ollama (LLM local, gratuito).

    Requer Ollama rodando na máquina host (https://ollama.com).
    Dentro do Docker, usa host.docker.internal para alcançar o host.

    Uso:
        router = OllamaRouter()                           # modelo padrão: llama3.2
        router = OllamaRouter(model="qwen2.5:3b")         # modelo menor/mais rápido
        router = OllamaRouter(host="http://localhost:11434")  # fora do Docker
    """

    def __init__(
        self,
        model: str = "llama3.2",
        host: str = "http://host.docker.internal:11434",
    ):
        """
        Args:
            model: Modelo Ollama a usar. Precisa estar baixado (ollama pull <model>).
                   Sugestões: llama3.2, qwen2.5:3b, mistral, gemma3:4b
            host:  URL do servidor Ollama.
                   Dentro do Docker: http://host.docker.internal:11434 (padrão)
                   Fora do Docker:   http://localhost:11434
        """
        self._model = model
        self._client = _ollama.Client(host=host)

    def route(self, profile: DocumentProfile) -> ProcessingRecommendation:
        """
        Envia o DocumentProfile para o Ollama e retorna a recomendação.

        Raises:
            ollama.ResponseError: Se o modelo não estiver disponível.
            ConnectionError: Se o Ollama não estiver rodando.
        """
        profile_text = self._format_profile(profile)
        schema = _OllamaRecommendation.model_json_schema()

        response = self._client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Analise o perfil abaixo e recomende o melhor método de processamento:\n\n"
                        f"{profile_text}"
                    ),
                },
            ],
            format=schema,
            options={"temperature": 0},
        )

        raw = response.message.content
        data = json.loads(raw)
        rec = _OllamaRecommendation(**data)

        try:
            tier = ProcessingTier(rec.tier)
        except ValueError:
            tier = ProcessingTier.LOCAL_LIGHT

        # Fallback: se a LLM não sugeriu modelo, usa o padrão do tier
        _default_models = {
            ProcessingTier.LOCAL_LIGHT: "paddle",
            ProcessingTier.LOCAL_HEAVY: "qwen3",
            ProcessingTier.CLOUD: "gemini-pro-vision",
        }
        model = rec.recommended_model or _default_models.get(tier)

        return ProcessingRecommendation(
            tier=tier,
            model=model,
            route_name=f"ollama-router ({self._model})",
            reason=rec.reason,
        )

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
