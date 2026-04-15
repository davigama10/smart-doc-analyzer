from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from PIL import Image

from .base import BaseAnalyzer
from ..profile import DocumentProfile, DocType, FileType

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


class ImageAnalyzer(BaseAnalyzer):
    """
    Analisador de arquivos de imagem standalone (PNG, JPG, TIFF, BMP, WEBP).

    Trata a imagem como um documento de 1 página e detecta:
    presença de texto, manuscrito, resolução e complexidade visual.
    """

    def can_analyze(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in IMAGE_EXTENSIONS

    def analyze(self, file_path: str) -> DocumentProfile:
        path = Path(file_path)
        file_size = path.stat().st_size

        img_info = self._analyze_image(path)
        text_info = self._analyze_text(path)

        is_handwritten = text_info["avg_words"] < 10 or text_info["avg_conf"] < 60
        handwriting_confidence = round(1.0 - min(text_info["avg_conf"] / 100.0, 1.0), 4) if is_handwritten else 0.0

        has_text = text_info["avg_words"] >= 5
        text_density = 1.0 if has_text else 0.0
        avg_chars = text_info["char_count"]

        doc_type = self._classify_doc_type(
            has_text=has_text,
            avg_chars=avg_chars,
            is_handwritten=is_handwritten,
            is_complex=img_info["is_complex"],
        )

        return DocumentProfile(
            file_path=str(path.absolute()),
            file_type=FileType.IMAGE,
            file_size_bytes=file_size,
            doc_type=doc_type,
            num_pages=1,
            has_selectable_text=False,  # imagens nunca têm texto selecionável
            text_density=text_density,
            avg_chars_per_page=avg_chars,
            image_density=1.0,           # a imagem inteira é a "página"
            has_tables=False,            # detecção de tabelas em imagens não suportada ainda
            table_density=0.0,
            is_handwritten=is_handwritten,
            handwriting_confidence=handwriting_confidence,
            raw_metrics={
                "width_px": img_info["width"],
                "height_px": img_info["height"],
                "dpi_estimate": img_info["dpi_estimate"],
                "color_mode": img_info["color_mode"],
                "is_complex": img_info["is_complex"],
                "ocr_avg_confidence": text_info["avg_conf"],
                "ocr_avg_words": text_info["avg_words"],
                "char_count": text_info["char_count"],
            },
        )

    # ------------------------------------------------------------------
    # Análise visual da imagem
    # ------------------------------------------------------------------

    def _analyze_image(self, path: Path) -> Dict[str, Any]:
        try:
            img = Image.open(path)
            width, height = img.size
            color_mode = img.mode

            # DPI pode estar nos metadados EXIF
            dpi_info = img.info.get("dpi", (72, 72))
            dpi_estimate = int(dpi_info[0]) if isinstance(dpi_info, tuple) else 72

            # Complexidade visual: desvio padrão dos pixels (imagens com muito conteúdo têm alto desvio)
            img_array = np.array(img.convert("L"))
            std_dev = float(np.std(img_array))
            is_complex = std_dev > 40

            return {
                "width": width,
                "height": height,
                "dpi_estimate": dpi_estimate,
                "color_mode": color_mode,
                "is_complex": is_complex,
            }
        except Exception:
            return {
                "width": 0,
                "height": 0,
                "dpi_estimate": 72,
                "color_mode": "unknown",
                "is_complex": False,
            }

    # ------------------------------------------------------------------
    # Análise de texto via Tesseract
    # ------------------------------------------------------------------

    def _analyze_text(self, path: Path) -> Dict[str, Any]:
        try:
            img = cv2.imread(str(path))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            data = pytesseract.image_to_data(
                processed,
                lang="por",
                output_type=Output.DICT,
                config="--oem 3 --psm 6",
            )

            page_confs = [int(c) for c in data["conf"] if c != "-1"]
            text = pytesseract.image_to_string(processed, lang="por")
            char_count = len(text.strip())

            avg_conf = float(np.mean(page_confs)) if page_confs else 0.0
            avg_words = len(page_confs)

            return {
                "avg_conf": round(avg_conf, 2),
                "avg_words": avg_words,
                "char_count": char_count,
            }
        except Exception:
            return {"avg_conf": 0.0, "avg_words": 0, "char_count": 0}

    # ------------------------------------------------------------------
    # Classificação
    # ------------------------------------------------------------------

    def _classify_doc_type(
        self,
        has_text: bool,
        avg_chars: float,
        is_handwritten: bool,
        is_complex: bool,
    ) -> DocType:
        if is_handwritten:
            return DocType.HANDWRITTEN
        if has_text and avg_chars >= 200:
            return DocType.SCANNED
        if has_text and avg_chars < 200:
            return DocType.MINIMAL_TEXT
        if is_complex:
            return DocType.IMAGE_BASED
        return DocType.SCANNED
