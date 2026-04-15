from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class DocType(str, Enum):
    """Tipo de documento baseado na análise de conteúdo."""
    NATIVE_DIGITAL = "native_digital"   # PDF com texto embutido (nativo digital)
    SCANNED = "scanned"                 # Documento escaneado (predominantemente imagem)
    HYBRID = "hybrid"                   # Misto de texto e imagens
    HANDWRITTEN = "handwritten"         # Manuscrito
    IMAGE_BASED = "image_based"         # Majoritariamente imagens
    MINIMAL_TEXT = "minimal_text"       # Texto muito esparso


class FileType(str, Enum):
    """Tipo de arquivo."""
    PDF = "pdf"
    IMAGE = "image"   # PNG, JPG, TIFF, BMP, WEBP


class ProcessingTier(str, Enum):
    """
    Tier de processamento recomendado, do mais simples ao mais caro.

    - NONE:        Sem OCR necessário (texto já selecionável)
    - LOCAL_LIGHT: Modelo local leve suficiente (ex: PaddleOCR)
    - LOCAL_HEAVY: Modelo local pesado necessário (ex: DeepSeek, Qwen)
    - CLOUD:       Modelo de nuvem recomendado (documento complexo)
    """
    NONE = "none"
    LOCAL_LIGHT = "local_light"
    LOCAL_HEAVY = "local_heavy"
    CLOUD = "cloud"


@dataclass
class ProcessingRecommendation:
    """Recomendação de processamento retornada pelo roteador."""
    tier: ProcessingTier
    model: Optional[str]          # Nome do modelo sugerido (ex: "paddle", "qwen3")
    route_name: Optional[str]     # Nome da rota que deu match
    reason: str                   # Justificativa legível


@dataclass
class DocumentProfile:
    """
    Perfil padronizado de um documento após análise.
    Independente do formato de origem (PDF, imagem, etc.).
    """

    # --- Arquivo ---
    file_path: str
    file_type: FileType
    file_size_bytes: int

    # --- Classificação ---
    doc_type: DocType
    num_pages: int

    # --- Texto ---
    has_selectable_text: bool
    text_density: float           # 0.0–1.0: proporção de páginas com texto
    avg_chars_per_page: float

    # --- Imagens ---
    image_density: float          # 0.0–1.0: proporção de páginas com imagens

    # --- Tabelas ---
    has_tables: bool
    table_density: float          # 0.0–1.0: proporção de páginas com tabelas

    # --- Manuscrito ---
    is_handwritten: bool
    handwriting_confidence: float  # 0.0–1.0 (1.0 = certamente manuscrito)

    # --- Métricas brutas ---
    # Preserva todos os valores calculados para roteamento customizado
    raw_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_type": self.file_type.value,
            "file_size_bytes": self.file_size_bytes,
            "doc_type": self.doc_type.value,
            "num_pages": self.num_pages,
            "has_selectable_text": self.has_selectable_text,
            "text_density": round(self.text_density, 4),
            "avg_chars_per_page": round(self.avg_chars_per_page, 2),
            "image_density": round(self.image_density, 4),
            "has_tables": self.has_tables,
            "table_density": round(self.table_density, 4),
            "is_handwritten": self.is_handwritten,
            "handwriting_confidence": round(self.handwriting_confidence, 4),
            "raw_metrics": self.raw_metrics,
        }
