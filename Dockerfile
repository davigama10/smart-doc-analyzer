FROM python:3.11-slim

# Dependências de sistema: Tesseract + idioma PT + OpenCV + utilitários PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY doc_analyzer/ ./doc_analyzer/
COPY routes_example.json ./
COPY test_quick.py ./
COPY test_llm.py ./
COPY app.py ./

RUN pip install --no-cache-dir \
    PyPDF2>=3.0.0 \
    pdfplumber>=0.10.0 \
    pypdfium2>=4.0.0 \
    pytesseract>=0.3.10 \
    opencv-python-headless>=4.8.0 \
    numpy>=1.24.0 \
    Pillow>=10.0.0 \
    pydantic>=2.0.0 \
    ollama>=0.3.0 \
    fastapi>=0.110.0 \
    uvicorn>=0.29.0 \
    python-multipart>=0.0.9

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
