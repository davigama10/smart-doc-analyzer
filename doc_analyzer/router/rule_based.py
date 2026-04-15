import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base import BaseRouter
from ..profile import DocumentProfile, ProcessingRecommendation, ProcessingTier


class RuleBasedRouter(BaseRouter):
    """
    Roteador baseado em regras configuráveis via arquivo JSON.

    Cada regra define condições sobre o DocumentProfile e, quando satisfeitas,
    retorna uma recomendação de processamento. As regras são avaliadas em ordem
    de prioridade (menor número = maior prioridade).

    Formato do arquivo JSON:
    {
        "routes": [
            {
                "name": "nome-da-rota",
                "priority": 1,
                "conditions": {
                    "doc_type": ["scanned", "hybrid"],
                    "image_density_min": 0.5,
                    "image_density_max": 1.0,
                    "text_density_min": 0.0,
                    "text_density_max": 1.0,
                    "table_density_min": 0.0,
                    "avg_chars_per_page_min": 0,
                    "avg_chars_per_page_max": 99999,
                    "is_handwritten": true,
                    "file_type": ["pdf", "image"],
                    "file_size_min_bytes": 0,
                    "file_size_max_bytes": 999999999
                },
                "recommendation": {
                    "tier": "local_heavy",
                    "model": "qwen3",
                    "reason": "Documento escaneado complexo requer modelo vision"
                }
            }
        ],
        "default": {
            "tier": "local_light",
            "model": "paddle",
            "reason": "Fallback padrão"
        }
    }
    """

    def __init__(self, config_path: str):
        """
        Args:
            config_path: Caminho para o arquivo JSON de configuração de rotas.
        """
        self._config = self._load_config(config_path)
        self._routes: List[Dict[str, Any]] = sorted(
            self._config.get("routes", []),
            key=lambda r: r.get("priority", 999),
        )
        self._default: Dict[str, Any] = self._config.get("default", {
            "tier": "local_light",
            "model": None,
            "reason": "Nenhuma rota compatível. Usando padrão.",
        })

    # ------------------------------------------------------------------
    # Roteamento principal
    # ------------------------------------------------------------------

    def route(self, profile: DocumentProfile) -> ProcessingRecommendation:
        for route in self._routes:
            if self._matches(profile, route.get("conditions", {})):
                rec = route["recommendation"]
                return ProcessingRecommendation(
                    tier=ProcessingTier(rec["tier"]),
                    model=rec.get("model"),
                    route_name=route.get("name"),
                    reason=rec.get("reason", ""),
                )

        return ProcessingRecommendation(
            tier=ProcessingTier(self._default.get("tier", "local_light")),
            model=self._default.get("model"),
            route_name=None,
            reason=self._default.get("reason", "Rota padrão"),
        )

    # ------------------------------------------------------------------
    # Avaliação de condições
    # ------------------------------------------------------------------

    def _matches(self, profile: DocumentProfile, conditions: Dict[str, Any]) -> bool:
        checks = {
            "doc_type":                 lambda: profile.doc_type.value in conditions["doc_type"],
            "file_type":                lambda: profile.file_type.value in conditions["file_type"],
            "is_handwritten":           lambda: profile.is_handwritten == conditions["is_handwritten"],
            "has_tables":               lambda: profile.has_tables == conditions["has_tables"],
            "has_selectable_text":      lambda: profile.has_selectable_text == conditions["has_selectable_text"],
            "image_density_min":        lambda: profile.image_density >= conditions["image_density_min"],
            "image_density_max":        lambda: profile.image_density <= conditions["image_density_max"],
            "text_density_min":         lambda: profile.text_density >= conditions["text_density_min"],
            "text_density_max":         lambda: profile.text_density <= conditions["text_density_max"],
            "table_density_min":        lambda: profile.table_density >= conditions["table_density_min"],
            "table_density_max":        lambda: profile.table_density <= conditions["table_density_max"],
            "avg_chars_per_page_min":   lambda: profile.avg_chars_per_page >= conditions["avg_chars_per_page_min"],
            "avg_chars_per_page_max":   lambda: profile.avg_chars_per_page <= conditions["avg_chars_per_page_max"],
            "file_size_min_bytes":      lambda: profile.file_size_bytes >= conditions["file_size_min_bytes"],
            "file_size_max_bytes":      lambda: profile.file_size_bytes <= conditions["file_size_max_bytes"],
            "num_pages_min":            lambda: profile.num_pages >= conditions["num_pages_min"],
            "num_pages_max":            lambda: profile.num_pages <= conditions["num_pages_max"],
            "handwriting_confidence_min": lambda: profile.handwriting_confidence >= conditions["handwriting_confidence_min"],
        }

        for key, check in checks.items():
            if key in conditions:
                try:
                    if not check():
                        return False
                except Exception:
                    return False

        return True

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def add_route(self, route: Dict[str, Any]) -> None:
        """Adiciona uma rota em tempo de execução e reordena por prioridade."""
        self._routes.append(route)
        self._routes.sort(key=lambda r: r.get("priority", 999))

    def list_routes(self) -> List[Dict[str, Any]]:
        """Retorna todas as rotas carregadas."""
        return list(self._routes)
