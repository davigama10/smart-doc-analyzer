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

RUN pip install --no-cache-dir \
    PyPDF2>=3.0.0 \
    pdfplumber>=0.10.0 \
    pypdfium2>=4.0.0 \
    pytesseract>=0.3.10 \
    opencv-python-headless>=4.8.0 \
    numpy>=1.24.0 \
    Pillow>=10.0.0

# Diretório onde o usuário vai montar os documentos para teste
VOLUME ["/docs"]

CMD ["python", "test_quick.py"]
