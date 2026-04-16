"""
Gera o relatório PDF da POC smart-doc-analyzer — versão objetiva.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import date

OUTPUT = "Relatorio_POC_SmartDocAnalyzer.pdf"

AZUL   = colors.HexColor("#1a2e4a")
AZUL2  = colors.HexColor("#2563eb")
AZULC  = colors.HexColor("#dbeafe")
CINZAC = colors.HexColor("#f1f5f9")
CINZAT = colors.HexColor("#374151")
BRANCO = colors.white

S_TITULO = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=20, textColor=BRANCO, alignment=TA_CENTER, leading=26)
S_SUB    = ParagraphStyle("sub",    fontName="Helvetica",      fontSize=11, textColor=colors.HexColor("#bfdbfe"), alignment=TA_CENTER, leading=16)
S_SEC    = ParagraphStyle("sec",    fontName="Helvetica-Bold", fontSize=12, textColor=AZUL, spaceBefore=14, spaceAfter=4)
S_CORPO  = ParagraphStyle("corpo",  fontName="Helvetica",      fontSize=10, textColor=CINZAT, leading=14, spaceAfter=3)
S_CODE   = ParagraphStyle("code",   fontName="Courier",        fontSize=9,  textColor=AZUL, backColor=CINZAC, leading=13, leftIndent=10, rightIndent=10, spaceBefore=1, spaceAfter=1)
S_TH     = ParagraphStyle("th",     fontName="Helvetica-Bold", fontSize=9,  textColor=BRANCO, alignment=TA_CENTER, leading=12)
S_TD     = ParagraphStyle("td",     fontName="Helvetica",      fontSize=9,  textColor=CINZAT, leading=12)
S_TDCEN  = ParagraphStyle("tdcen",  fontName="Helvetica",      fontSize=9,  textColor=CINZAT, alignment=TA_CENTER, leading=12)


def hr():
    return HRFlowable(width="100%", thickness=0.8, color=AZULC, spaceAfter=5, spaceBefore=2)


def tabela(cabecalhos, linhas, col_widths, centrar_colunas=None):
    centrar_colunas = centrar_colunas or []
    data = []
    data.append([Paragraph(c, S_TH) for c in cabecalhos])
    for row in linhas:
        data.append([
            Paragraph(str(cell), S_TDCEN if i in centrar_colunas else S_TD)
            for i, cell in enumerate(row)
        ])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  AZUL),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BRANCO, CINZAC]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
        title="Relatório POC — smart-doc-analyzer", author="Davi Gama",
    )
    e = []

    # ── Capa ──────────────────────────────────────────────────────────────────
    capa = Table([
        [Paragraph("smart-doc-analyzer", S_TITULO)],
        [Paragraph("POC — Mecanismo de Classificação e Roteamento de Documentos", S_SUB)],
        [Paragraph(f"Equipe devs e analistas Acellerai  ·  Abril 2026", S_SUB)],
    ], colWidths=[16.5*cm])
    capa.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), AZUL),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
    ]))
    e.append(capa)
    e.append(Spacer(1, 0.5*cm))

    # ── Objetivo ──────────────────────────────────────────────────────────────
    e.append(Paragraph("Objetivo", S_SEC))
    e.append(hr())
    e.append(Paragraph(
        "Biblioteca Python que analisa um documento (PDF ou imagem), extrai métricas objetivas "
        "e decide automaticamente qual modelo de processamento usar — evitando custo desnecessário "
        "com modelos pesados e garantindo qualidade onde necessário.",
        S_CORPO,
    ))
    e.append(Spacer(1, 0.3*cm))

    # ── Fluxo ─────────────────────────────────────────────────────────────────
    e.append(Paragraph("Fluxo de Funcionamento", S_SEC))
    e.append(hr())

    passos = [
        ["1", "Recebe o arquivo",        "PDF ou imagem (PNG, JPG, TIFF…)"],
        ["2", "Seleciona o analisador",  "PDFAnalyzer para .pdf · ImageAnalyzer para imagens"],
        ["3", "Extrai métricas",         "Densidade de texto/imagem/tabelas · Detecção de manuscrito via Tesseract OCR"],
        ["4", "Classifica o tipo",       "native_digital · scanned · hybrid · handwritten · image_based · minimal_text"],
        ["5", "Monta o DocumentProfile", "Estrutura padronizada com todas as métricas (independente do formato)"],
        ["6", "Roteia pelo JSON",        "Avalia as regras em ordem de prioridade; retorna tier + modelo sugerido"],
        ["7", "Retorna resultado",       "ProcessingRecommendation: tier · model · route_name · reason"],
    ]
    e.append(tabela(["#", "Etapa", "Detalhe"], passos, [1.0*cm, 4.0*cm, 11.5*cm], centrar_colunas=[0]))
    e.append(Spacer(1, 0.4*cm))

    # ── Tipos de Documento ────────────────────────────────────────────────────
    e.append(Paragraph("Tipos de Documento Detectados", S_SEC))
    e.append(hr())
    tipos = [
        ["native_digital", "PDF com texto embutido e selecionável",          "texto ≥ 80% pág. e ≥ 500 chars/pág."],
        ["scanned",        "Documento físico escaneado",                     "imagem ≥ 80% pág. e < 100 chars/pág."],
        ["hybrid",         "Mix de texto nativo e imagens",                  "imagem ≥ 40% e texto ≥ 40%"],
        ["handwritten",    "Manuscrito",                                      "média de palavras OCR < 10 ou confiança < 60%"],
        ["image_based",    "Documento majoritariamente composto por imagens","imagem ≥ 60%"],
        ["minimal_text",   "Texto muito esparso",                            "algum texto, mas < 200 chars/pág."],
    ]
    e.append(tabela(["Tipo", "Descrição", "Critério"], tipos, [3.0*cm, 5.5*cm, 8.0*cm]))
    e.append(Spacer(1, 0.4*cm))

    # ── Tiers ─────────────────────────────────────────────────────────────────
    e.append(Paragraph("Tiers de Processamento", S_SEC))
    e.append(hr())
    tiers = [
        ["none",        "Zero",  "PDF nativo sem imagens — texto já extraível",      "—"],
        ["local_light", "Baixo", "Escaneados simples",                               "PaddleOCR"],
        ["local_heavy", "Médio", "Escaneados complexos, tabelas densas",             "Qwen3 / DeepSeek"],
        ["cloud",       "Alto",  "Manuscritos / docs que exigem visão avançada",     "Gemini Pro Vision"],
    ]
    e.append(tabela(["Tier", "Custo", "Quando usar", "Modelo"], tiers,
                    [2.5*cm, 2.0*cm, 7.5*cm, 4.5*cm], centrar_colunas=[1]))
    e.append(Spacer(1, 0.4*cm))

    # ── Rotas ─────────────────────────────────────────────────────────────────
    e.append(Paragraph("Rotas Configuradas (routes_example.json)", S_SEC))
    e.append(hr())
    e.append(Paragraph(
        "Regras avaliadas em ordem de prioridade — a primeira que satisfaz todas as condições vence. "
        "Configurável via JSON, sem alterar código.",
        S_CORPO,
    ))
    e.append(Spacer(1, 0.2*cm))
    rotas = [
        ["1", "manuscrito-cloud",                "is_handwritten = true",            "cloud → Gemini Pro Vision"],
        ["2", "nativo-digital-sem-ocr",           "native_digital, sem imagens",      "none → (sem OCR)"],
        ["3", "nativo-digital-com-imagens",       "native_digital, com imagens",      "local_light → PaddleOCR"],
        ["4", "escaneado-complexo",               "scanned/image_based, img ≥ 70%",   "local_heavy → Qwen3"],
        ["5", "hibrido-com-tabelas",              "hybrid, tabelas ≥ 30%",            "local_heavy → DeepSeek"],
        ["6", "escaneado-simples",                "scanned/hybrid/minimal_text",      "local_light → PaddleOCR"],
        ["—", "default (fallback)",               "nenhuma rota compatível",          "local_light → PaddleOCR"],
    ]
    e.append(tabela(["Pri.", "Rota", "Condição", "Resultado"], rotas,
                    [1.2*cm, 4.3*cm, 5.5*cm, 5.5*cm], centrar_colunas=[0]))
    e.append(Spacer(1, 0.4*cm))

    # ── Exemplo de uso ────────────────────────────────────────────────────────
    e.append(Paragraph("Exemplo de Uso", S_SEC))
    e.append(hr())
    for linha in [
        "from doc_analyzer import DocAnalyzer",
        "",
        "analyzer = DocAnalyzer(routes_config='routes.json')",
        "profile, rec = analyzer.analyze_and_route('documento.pdf')",
        "",
        "# profile.doc_type.value  →  'scanned'",
        "# rec.tier.value          →  'local_heavy'",
        "# rec.model               →  'qwen3'",
        "# rec.reason              →  'Documento escaneado com alta densidade de imagens'",
    ]:
        e.append(Paragraph(linha if linha else "&nbsp;", S_CODE))
    e.append(Spacer(1, 0.4*cm))

    # ── Stack técnica ─────────────────────────────────────────────────────────
    e.append(Paragraph("Stack Técnica", S_SEC))
    e.append(hr())
    stack = [
        ["PyPDF2 + pdfplumber",       "Extração de texto, imagens e tabelas de PDFs"],
        ["pypdfium2 + OpenCV",        "Renderização de páginas em 300 DPI + pré-processamento (binarização Otsu)"],
        ["Tesseract OCR (pytesseract)","Detecção de manuscrito via confiança e contagem de palavras"],
        ["Pillow + NumPy",            "Leitura de imagens e cálculos estatísticos"],
    ]
    e.append(tabela(["Biblioteca", "Uso"], stack, [5.0*cm, 11.5*cm]))
    e.append(Spacer(1, 0.4*cm))

    # ── Repositório ───────────────────────────────────────────────────────────
    e.append(hr())
    rodape = Table([[
        Paragraph(
            f"Equipe devs e analistas Acellerai  ·  github.com/davigama10/smart-doc-analyzer  ·  {date.today().strftime('%d/%m/%Y')}",
            ParagraphStyle("rod", fontName="Helvetica", fontSize=8,
                           textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER),
        )
    ]], colWidths=[16.5*cm])
    e.append(rodape)

    doc.build(e)
    print(f"PDF gerado: {OUTPUT}")


if __name__ == "__main__":
    build()
