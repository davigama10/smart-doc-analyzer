import tempfile
import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse

from doc_analyzer import DocAnalyzer

app = FastAPI()
analyzer = DocAnalyzer(routes_config="routes_example.json", use_ollama=True)

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Doc Analyzer</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f1f5f9;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }

    .card {
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
      padding: 40px;
      width: 100%;
      max-width: 600px;
    }

    h1 {
      font-size: 22px;
      color: #1a2e4a;
      margin-bottom: 4px;
    }

    .subtitle {
      font-size: 14px;
      color: #94a3b8;
      margin-bottom: 32px;
    }

    .upload-area {
      border: 2px dashed #cbd5e1;
      border-radius: 8px;
      padding: 32px;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.2s;
      margin-bottom: 20px;
    }

    .upload-area:hover { border-color: #2563eb; }
    .upload-area.dragover { border-color: #2563eb; background: #eff6ff; }

    .upload-area input { display: none; }

    .upload-icon { font-size: 36px; margin-bottom: 8px; }

    .upload-label {
      font-size: 14px;
      color: #64748b;
    }

    .upload-label span {
      color: #2563eb;
      font-weight: 500;
      cursor: pointer;
    }

    .file-name {
      font-size: 13px;
      color: #2563eb;
      margin-top: 8px;
      font-weight: 500;
    }

    button {
      width: 100%;
      background: #1a2e4a;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 14px;
      font-size: 15px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.2s;
    }

    button:hover { background: #2563eb; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }

    .loading {
      display: none;
      text-align: center;
      padding: 24px 0;
      color: #64748b;
      font-size: 14px;
    }

    .spinner {
      display: inline-block;
      width: 20px;
      height: 20px;
      border: 2px solid #cbd5e1;
      border-top-color: #2563eb;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      margin-right: 8px;
      vertical-align: middle;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .results { display: none; margin-top: 28px; }

    .section-title {
      font-size: 11px;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 10px;
    }

    .profile-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 20px;
    }

    .metric {
      background: #f8fafc;
      border-radius: 6px;
      padding: 10px 12px;
    }

    .metric-label { font-size: 11px; color: #94a3b8; margin-bottom: 2px; }
    .metric-value { font-size: 14px; font-weight: 600; color: #1a2e4a; }

    .rec-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .rec-card {
      border-radius: 8px;
      padding: 16px;
      border: 1px solid #e2e8f0;
    }

    .rec-card .source {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 10px;
    }

    .rec-card.rules .source { color: #2563eb; }
    .rec-card.llm   .source { color: #16a34a; }

    .tier-badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 6px;
    }

    .tier-none         { background: #f1f5f9; color: #64748b; }
    .tier-local_light  { background: #eff6ff; color: #2563eb; }
    .tier-local_heavy  { background: #fef3c7; color: #d97706; }
    .tier-cloud        { background: #fce7f3; color: #db2777; }

    .rec-model { font-size: 13px; font-weight: 600; color: #1a2e4a; margin-bottom: 4px; }
    .rec-reason { font-size: 12px; color: #64748b; line-height: 1.5; }

    .agreement {
      margin-top: 14px;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      text-align: center;
    }

    .agreement.agree    { background: #f0fdf4; color: #16a34a; }
    .agreement.disagree { background: #fff7ed; color: #d97706; }

    .error {
      display: none;
      margin-top: 16px;
      padding: 12px 16px;
      background: #fef2f2;
      color: #dc2626;
      border-radius: 8px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>Smart Doc Analyzer</h1>
    <p class="subtitle">Análise e recomendação de OCR via regras + LLM local</p>

    <div class="upload-area" id="uploadArea">
      <div class="upload-icon">📄</div>
      <div class="upload-label">
        <span onclick="document.getElementById('fileInput').click()">Clique para selecionar</span>
        ou arraste um PDF aqui
      </div>
      <div class="file-name" id="fileName"></div>
      <input type="file" id="fileInput" accept=".pdf,image/*">
    </div>

    <button id="analyzeBtn" onclick="analyze()" disabled>Analisar documento</button>

    <div class="loading" id="loading">
      <span class="spinner"></span> Analisando com Ollama, aguarde...
    </div>

    <div class="error" id="error"></div>

    <div class="results" id="results">
      <div class="section-title">Perfil do documento</div>
      <div class="profile-grid" id="profileGrid"></div>

      <div class="section-title">Recomendações de OCR</div>
      <div class="rec-grid" id="recGrid"></div>
      <div class="agreement" id="agreement"></div>
    </div>
  </div>

  <script>
    const input = document.getElementById('fileInput');
    const area  = document.getElementById('uploadArea');
    const btn   = document.getElementById('analyzeBtn');

    input.addEventListener('change', () => {
      if (input.files[0]) {
        document.getElementById('fileName').textContent = input.files[0].name;
        btn.disabled = false;
      }
    });

    area.addEventListener('dragover', e => { e.preventDefault(); area.classList.add('dragover'); });
    area.addEventListener('dragleave', () => area.classList.remove('dragover'));
    area.addEventListener('drop', e => {
      e.preventDefault();
      area.classList.remove('dragover');
      input.files = e.dataTransfer.files;
      if (input.files[0]) {
        document.getElementById('fileName').textContent = input.files[0].name;
        btn.disabled = false;
      }
    });

    async function analyze() {
      const file = input.files[0];
      if (!file) return;

      document.getElementById('loading').style.display = 'block';
      document.getElementById('results').style.display = 'none';
      document.getElementById('error').style.display = 'none';
      btn.disabled = true;

      const form = new FormData();
      form.append('file', file);

      try {
        const res = await fetch('/analyze', { method: 'POST', body: form });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || 'Erro desconhecido');

        renderResults(data);
        document.getElementById('results').style.display = 'block';
      } catch (e) {
        const err = document.getElementById('error');
        err.textContent = 'Erro: ' + e.message;
        err.style.display = 'block';
      } finally {
        document.getElementById('loading').style.display = 'none';
        btn.disabled = false;
      }
    }

    function metric(label, value) {
      return `<div class="metric"><div class="metric-label">${label}</div><div class="metric-value">${value}</div></div>`;
    }

    function renderResults(d) {
      const p = d.profile;
      document.getElementById('profileGrid').innerHTML =
        metric('Tipo',            p.doc_type) +
        metric('Páginas',         p.num_pages) +
        metric('Densidade texto', p.text_density) +
        metric('Densidade imagem',p.image_density) +
        metric('Tem tabelas',     p.has_tables ? 'Sim' : 'Não') +
        metric('Manuscrito',      p.is_handwritten ? 'Sim' : 'Não');

      function recCard(cls, source, rec) {
        const tier = rec.tier;
        return `
          <div class="rec-card ${cls}">
            <div class="source">${source}</div>
            <div class="tier-badge tier-${tier}">${tier}</div>
            <div class="rec-model">${rec.model || '—'}</div>
            <div class="rec-reason">${rec.reason}</div>
          </div>`;
      }

      document.getElementById('recGrid').innerHTML =
        recCard('rules', 'Regras', d.rule_recommendation) +
        recCard('llm',   'Ollama / ' + d.llm_model, d.llm_recommendation);

      const agree = d.rule_recommendation.tier === d.llm_recommendation.tier;
      const el = document.getElementById('agreement');
      el.className = 'agreement ' + (agree ? 'agree' : 'disagree');
      el.textContent = agree
        ? '✓ Regras e LLM concordam no tier'
        : `Divergência — Regras: ${d.rule_recommendation.tier}  ·  LLM: ${d.llm_recommendation.tier}`;
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    suffix = "." + file.filename.split(".")[-1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = analyzer.analyze_and_route_full(tmp_path)
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    finally:
        os.unlink(tmp_path)

    p = result.profile
    return {
        "profile": {
            "doc_type":       p.doc_type.value,
            "num_pages":      p.num_pages,
            "text_density":   f"{p.text_density:.0%}",
            "image_density":  f"{p.image_density:.0%}",
            "has_tables":     p.has_tables,
            "is_handwritten": p.is_handwritten,
        },
        "rule_recommendation": {
            "tier":   result.rule_recommendation.tier.value,
            "model":  result.rule_recommendation.model,
            "reason": result.rule_recommendation.reason,
        },
        "llm_recommendation": {
            "tier":   result.llm_recommendation.tier.value,
            "model":  result.llm_recommendation.model,
            "reason": result.llm_recommendation.reason,
        },
        "llm_model": analyzer._llm_router._model,
    }
