# smart-doc-analyzer

Biblioteca Python que analisa documentos (PDF e imagens), classifica seu tipo e recomenda automaticamente o melhor método de OCR — combinando um mecanismo de regras configurável com uma LLM local via Ollama.

---

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

> O Ollama roda como container — não é necessário instalá-lo na máquina.

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/davigama10/smart-doc-analyzer.git
cd smart-doc-analyzer
```

### 2. Crie o arquivo de ambiente

```bash
cp .env.example .env
```

> O `.env` não precisa de nenhuma variável para uso com Ollama.

### 3. Suba os containers

```bash
docker compose up --build
```

> O modelo `llama3.2` é baixado automaticamente na primeira execução.

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

## Campos do perfil (`profile`)

| Campo | Tipo | O que significa |
|---|---|---|
| `doc_type` | string | Classificação do documento (ver tabela abaixo) |
| `num_pages` | inteiro | Número total de páginas do arquivo |
| `text_density` | percentual | Proporção de páginas com texto selecionável (>50 caracteres). `100%` = todas as páginas têm texto embutido |
| `image_density` | percentual | Proporção de páginas que contêm pelo menos uma imagem embutida no PDF. `100%` = todas as páginas têm imagem |
| `has_tables` | booleano | `true` se pelo menos uma tabela foi detectada na estrutura do PDF |
| `is_handwritten` | booleano | `true` se o documento parece manuscrito — detectado quando a média de palavras reconhecidas por OCR é inferior a 10 ou a confiança média do Tesseract é inferior a 60% |

### Valores de `doc_type`

| Valor | Significado | Critério |
|---|---|---|
| `native_digital` | PDF gerado digitalmente com texto selecionável | ≥80% das páginas com texto **e** ≥500 chars/página em média |
| `scanned` | Documento escaneado (imagem) | ≥80% das páginas com imagem **e** <100 chars/página |
| `hybrid` | Misto de texto e imagens | ≥40% das páginas com imagem **e** ≥40% com texto |
| `image_based` | Majoritariamente imagens, sem ser escaneado puro | ≥60% das páginas com imagem |
| `minimal_text` | Texto presente mas muito esparso | Texto detectado com <200 chars/página em média |
| `handwritten` | Manuscrito | Detectado por baixa confiança ou poucos tokens via OCR |

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
