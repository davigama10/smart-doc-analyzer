from pathlib import Path
from typing import Dict, Any

import PyPDF2
import pdfplumber
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from PIL import Image
import pypdfium2 as pdfium

from .base import BaseAnalyzer
from ..profile import DocumentProfile, DocType, FileType, ProcessingTier

PDF_EXTENSIONS = {".pdf"}


class PDFAnalyzer(BaseAnalyzer):
    """
    Analisador de arquivos PDF.

    Detecta: tipo do documento, densidade de texto/imagem/tabelas,
    presença de manuscrito, e monta o DocumentProfile padronizado.
    """

    def can_analyze(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in PDF_EXTENSIONS

    def analyze(self, file_path: str) -> DocumentProfile:
        path = Path(file_path)

        file_size = path.stat().st_size
        content = self._analyze_content(path)
        handwriting = self._detect_handwriting(path)
        tables = self._analyze_tables(path)

        num_pages = content["num_pages"]
        pages_with_tables = len(tables.get("pages_with_tables", []))
        table_density = (pages_with_tables / num_pages) if num_pages > 0 else 0.0

        doc_type = self._classify_doc_type(
            text_density=content["text_density"],
            image_density=content["image_density"],
            avg_chars=content["avg_chars_per_page"],
            is_handwritten=handwriting["is_handwritten"],
        )

        return DocumentProfile(
            file_path=str(path.absolute()),
            file_type=FileType.PDF,
            file_size_bytes=file_size,
            doc_type=doc_type,
            num_pages=num_pages,
            has_selectable_text=content["text_density"] > 0,
            text_density=content["text_density"],
            avg_chars_per_page=content["avg_chars_per_page"],
            image_density=content["image_density"],
            has_tables=tables.get("has_tables", False),
            table_density=round(table_density, 4),
            is_handwritten=handwriting["is_handwritten"],
            handwriting_confidence=handwriting["confidence"],
            raw_metrics={
                "pages_with_text": content["pages_with_text"],
                "pages_with_images": content["pages_with_images"],
                "pages_with_tables": pages_with_tables,
                "total_tables": tables.get("total_tables", 0),
                "has_forms": content["has_forms"],
                "has_annotations": content["has_annotations"],
                "ocr_avg_confidence": handwriting.get("ocr_avg_confidence", 0.0),
                "ocr_avg_words": handwriting.get("ocr_avg_words", 0),
                "handwriting_reasons": handwriting.get("reasons", []),
            },
        )

    # ------------------------------------------------------------------
    # Análise de conteúdo
    # ------------------------------------------------------------------

    def _analyze_content(self, path: Path) -> Dict[str, Any]:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            pages_with_text = 0
            pages_with_images = 0
            total_chars = 0
            has_forms = False
            has_annotations = False

            for page in reader.pages:
                try:
                    text = page.extract_text() or ""
                    if len(text.strip()) > 50:
                        pages_with_text += 1
                        total_chars += len(text.strip())
                except Exception:
                    pass

                try:
                    resources = page.get("/Resources", {})
                    xobjects = resources.get("/XObject", {})
                    if hasattr(xobjects, "get_object"):
                        xobjects = xobjects.get_object()
                    for obj_key in xobjects:
                        if xobjects[obj_key].get("/Subtype") == "/Image":
                            pages_with_images += 1
                            break
                except Exception:
                    pass

                try:
                    if "/Annots" in page:
                        has_annotations = True
                    if "/AcroForm" in reader.trailer.get("/Root", {}):
                        has_forms = True
                except Exception:
                    pass

        avg_chars = total_chars / total_pages if total_pages > 0 else 0.0
        text_density = pages_with_text / total_pages if total_pages > 0 else 0.0
        image_density = pages_with_images / total_pages if total_pages > 0 else 0.0

        return {
            "num_pages": total_pages,
            "pages_with_text": pages_with_text,
            "pages_with_images": pages_with_images,
            "text_density": round(text_density, 4),
            "image_density": round(image_density, 4),
            "avg_chars_per_page": round(avg_chars, 2),
            "has_forms": has_forms,
            "has_annotations": has_annotations,
        }

    # ------------------------------------------------------------------
    # Detecção de manuscrito
    # ------------------------------------------------------------------

    def _detect_handwriting(self, path: Path) -> Dict[str, Any]:
        try:
            pdf = pdfium.PdfDocument(str(path))
            max_pages = min(5, len(pdf))
            confs, words = [], []

            for i in range(max_pages):
                page = pdf[i]
                bitmap = page.render(scale=300 / 72)
                pil_img = bitmap.to_pil()

                img = np.array(pil_img)
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                data = pytesseract.image_to_data(
                    processed,
                    lang="por",
                    output_type=Output.DICT,
                    config="--oem 3 --psm 6",
                )
                page_confs = [int(c) for c in data["conf"] if c != "-1"]
                if page_confs:
                    confs.append(float(np.mean(page_confs)))
                    words.append(len(page_confs))
                else:
                    confs.append(0.0)
                    words.append(0)

            avg_conf = float(np.mean(confs)) if confs else 0.0
            avg_words = int(np.mean(words)) if words else 0
            is_handwritten = avg_words < 10 or avg_conf < 60

            # Confiança normalizada: quanto menor a conf do Tesseract → mais manuscrito
            confidence = round(1.0 - min(avg_conf / 100.0, 1.0), 4) if is_handwritten else 0.0

            reasons = []
            if avg_words < 10:
                reasons.append(f"Poucas palavras detectadas (média: {avg_words})")
            if avg_conf < 60:
                reasons.append(f"Baixa confiança OCR (média: {avg_conf:.1f}%)")

            return {
                "is_handwritten": is_handwritten,
                "confidence": confidence,
                "ocr_avg_confidence": round(avg_conf, 2),
                "ocr_avg_words": avg_words,
                "reasons": reasons,
            }

        except Exception as e:
            return {
                "is_handwritten": False,
                "confidence": 0.0,
                "ocr_avg_confidence": 0.0,
                "ocr_avg_words": 0,
                "reasons": [f"Erro na detecção: {str(e)}"],
            }

    # ------------------------------------------------------------------
    # Análise de tabelas
    # ------------------------------------------------------------------

    def _analyze_tables(self, path: Path) -> Dict[str, Any]:
        try:
            result = {"has_tables": False, "total_tables": 0, "pages_with_tables": []}
            with pdfplumber.open(path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    if tables:
                        result["has_tables"] = True
                        result["total_tables"] += len(tables)
                        result["pages_with_tables"].append(page_num)
            return result
        except Exception:
            return {"has_tables": False, "total_tables": 0, "pages_with_tables": []}

    # ------------------------------------------------------------------
    # Classificação do tipo de documento
    # ------------------------------------------------------------------

    def _classify_doc_type(
        self,
        text_density: float,
        image_density: float,
        avg_chars: float,
        is_handwritten: bool,
    ) -> DocType:
        if is_handwritten:
            return DocType.HANDWRITTEN

        if text_density >= 0.8 and avg_chars >= 500:
            return DocType.NATIVE_DIGITAL

        if image_density >= 0.8 and avg_chars < 100:
            return DocType.SCANNED

        if image_density >= 0.4 and text_density >= 0.4:
            return DocType.HYBRID

        if text_density > 0 and avg_chars < 200:
            return DocType.MINIMAL_TEXT

        if image_density >= 0.6:
            return DocType.IMAGE_BASED

        return DocType.HYBRID
