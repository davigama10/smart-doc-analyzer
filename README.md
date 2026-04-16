# smart-doc-analyzer

Biblioteca Python que analisa documentos (PDF e imagens), classifica seu tipo e recomenda automaticamente o melhor método de OCR — combinando um mecanismo de regras configurável com uma LLM local via Ollama.

---

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/download)

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/davigama10/smart-doc-analyzer.git
cd smart-doc-analyzer
```

### 2. Baixe o modelo LLM

```bash
ollama pull llama3.2
```

### 3. Crie o arquivo de ambiente

```bash
cp .env.example .env
```

> O `.env` não precisa de nenhuma variável para uso com Ollama.

### 4. Suba o container

```bash
docker compose up --build
```

A aplicação estará disponível em **http://localhost:8000**

---

## Como usar

### Interface Web

Acesse **http://localhost:8000** no navegador, faça upload de um PDF e veja as recomendações.

### API (JSON)

```bash
curl.exe -X POST http://localhost:8000/analyze -F "file=@seu-documento.pdf"
```

Resposta:

```json
{
  "profile": {
    "doc_type": "native_digital",
    "num_pages": 1,
    "text_density": "100%",
    "image_density": "100%",
    "has_tables": false,
    "is_handwritten": false
  },
  "rule_recommendation": {
    "tier": "local_light",
    "model": "paddle",
    "reason": "PDF nativo digital com imagens embutidas — OCR leve para extrair texto das imagens."
  },
  "llm_recommendation": {
    "tier": "local_light",
    "model": "paddle",
    "reason": "Documentos escaneados simples, boa qualidade"
  },
  "llm_model": "llama3.2"
}
```

---

## Tiers de processamento

| Tier | Quando usar | Modelo sugerido |
|---|---|---|
| `none` | PDF com texto selecionável, sem OCR necessário | — |
| `local_light` | Escaneados simples, boa qualidade | PaddleOCR |
| `local_heavy` | Escaneados complexos ou com muitas tabelas | Qwen3 / DeepSeek |
| `cloud` | Manuscritos ou documentos muito complexos | Gemini Pro Vision |

---

## Configuração de rotas

As regras de roteamento ficam em `routes_example.json` e podem ser editadas sem rebuild. Cada rota define condições sobre o perfil do documento e uma recomendação de processamento.

---

## Estrutura do projeto

```
smart-doc-analyzer/
├── app.py                        # API FastAPI + frontend web
├── doc_analyzer/
│   ├── core.py                   # DocAnalyzer — ponto de entrada
│   ├── profile.py                # DocumentProfile e tipos
│   ├── analyzers/
│   │   ├── pdf.py                # PDFAnalyzer
│   │   └── image.py              # ImageAnalyzer
│   └── router/
│       ├── rule_based.py         # RuleBasedRouter (JSON)
│       └── ollama_router.py      # OllamaRouter (LLM local via Ollama)
├── routes_example.json           # Configuração de rotas
├── Dockerfile
└── docker-compose.yml
```
