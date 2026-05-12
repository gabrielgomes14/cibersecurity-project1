import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from data.controls import TEMA_LABELS, TEMAS, Controle
from logic.action_plan import AcaoPlano
from logic.models import Avaliacao
from logic.scoring import (
    RESPOSTA_NAO_AVALIADO,
    STATUS_COLORS,
    resumo_tema,
    score_geral,
    status_individual,
    status_label,
)

_PRIMARY = colors.HexColor("#1d4ed8")
_INK = colors.HexColor("#0f172a")
_MUTED = colors.HexColor("#475569")
_BORDER = colors.HexColor("#cbd5e1")
_BG_LIGHT = colors.HexColor("#f1f5f9")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo", parent=base["Title"], fontSize=22, textColor=_INK, spaceAfter=4),
        "subtitulo": ParagraphStyle("subtitulo", parent=base["Normal"], fontSize=11, textColor=_MUTED, spaceAfter=14),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=14, textColor=_PRIMARY, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, textColor=_INK, leading=14),
        "cell": ParagraphStyle("cell", parent=base["Normal"], fontSize=9, textColor=_INK, leading=12),
        "cell_muted": ParagraphStyle("cell_muted", parent=base["Normal"], fontSize=9, textColor=_MUTED, leading=12),
    }


def _barra(score: float, largura_cm: float = 8.0) -> Table:
    largura = largura_cm * cm
    preenchido = max(0.01, min(score / 100.0, 1.0)) * largura
    cor = colors.HexColor(STATUS_COLORS[status_label(score)])
    t = Table(
        [[""]],
        colWidths=[largura],
        rowHeights=[0.5 * cm],
    )
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _BG_LIGHT),
            ("LINEBELOW", (0, 0), (-1, -1), 0, colors.white),
            ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
        ])
    )
    fg = Table(
        [[""]],
        colWidths=[preenchido],
        rowHeights=[0.5 * cm],
    )
    fg.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), cor)]))
    container = Table([[fg, ""]], colWidths=[preenchido, largura - preenchido], rowHeights=[0.5 * cm])
    container.setStyle(
        TableStyle([
            ("BACKGROUND", (1, 0), (1, 0), _BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    return container


def _badge_status(label: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    cor = colors.HexColor(STATUS_COLORS.get(label, STATUS_COLORS[RESPOSTA_NAO_AVALIADO]))
    return Paragraph(f'<font color="{cor.hexval()}"><b>{label}</b></font>', styles["cell"])


def gerar_pdf(
    controles: list[Controle],
    avaliacoes: dict[str, Avaliacao],
    acoes: list[AcaoPlano],
    organizacao: str = "Organização",
    ponderado: bool = True,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="Relatório ISO/IEC 27002:2022",
        author="Diagnóstico de Conformidade",
    )
    s = _styles()
    flow: list[object] = []

    flow.append(Paragraph("Relatório de Conformidade — ISO/IEC 27002:2022", s["titulo"]))
    flow.append(Paragraph(f"{organizacao} · Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", s["subtitulo"]))

    todos_ids = [c.id for c in controles]
    score_total = score_geral(avaliacoes, todos_ids, ponderado=ponderado)
    avaliados = sum(1 for c in controles if avaliacoes.get(c.id, Avaliacao()).status)

    flow.append(Paragraph("Sumário Executivo", s["h2"]))
    cabecalho = Table(
        [
            [
                Paragraph(f"<b>{score_total:.1f}%</b>", s["body"]),
                _barra(score_total, 10),
                Paragraph(f"<b>{status_label(score_total)}</b>", s["body"]),
            ]
        ],
        colWidths=[2.0 * cm, 11.0 * cm, 4.0 * cm],
    )
    cabecalho.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    flow.append(cabecalho)
    flow.append(Spacer(1, 0.3 * cm))
    flow.append(Paragraph(
        f"Foram avaliados <b>{avaliados}</b> de <b>{len(controles)}</b> controles. "
        f"Critério de pontuação: {'ponderado por criticidade' if ponderado else 'simples'}.",
        s["body"],
    ))

    flow.append(Paragraph("Resultado por Tema", s["h2"]))
    linhas_tema: list[list[object]] = [["Tema", "Score", "Status", "Conformes", "Parciais", "Não Conf.", "N/A"]]
    for tema_id, tema_controles in TEMAS.items():
        ids = [c.id for c in tema_controles]
        r = resumo_tema(avaliacoes, tema_id, ids, ponderado=ponderado)
        linhas_tema.append([
            Paragraph(TEMA_LABELS[tema_id], s["cell"]),
            Paragraph(f"{r.score:.1f}%", s["cell"]),
            _badge_status(status_label(r.score), s),
            Paragraph(str(r.conformes), s["cell"]),
            Paragraph(str(r.parciais), s["cell"]),
            Paragraph(str(r.nao_conformes), s["cell"]),
            Paragraph(str(r.na), s["cell"]),
        ])
    tabela_temas = Table(linhas_tema, colWidths=[5 * cm, 2 * cm, 3 * cm, 2 * cm, 2 * cm, 2 * cm, 1.5 * cm])
    tabela_temas.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _BG_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.25, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    flow.append(tabela_temas)

    flow.append(Paragraph("Plano de Ação Prioritário", s["h2"]))
    if not acoes:
        flow.append(Paragraph("Nenhuma ação pendente — todos os controles estão conformes ou não aplicáveis.", s["body"]))
    else:
        linhas_acoes: list[list[object]] = [["Controle", "Título", "Status", "Prioridade", "Responsável", "Prazo"]]
        for a in acoes[:40]:
            linhas_acoes.append([
                Paragraph(a.controle_id, s["cell"]),
                Paragraph(a.titulo, s["cell"]),
                _badge_status(a.status, s),
                Paragraph(a.prioridade, s["cell"]),
                Paragraph(a.responsavel or "—", s["cell_muted"]),
                Paragraph(a.prazo or "—", s["cell_muted"]),
            ])
        tabela_acoes = Table(linhas_acoes, colWidths=[1.6 * cm, 6.5 * cm, 2.4 * cm, 2 * cm, 2.5 * cm, 2.4 * cm])
        tabela_acoes.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _BG_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.25, _BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        flow.append(tabela_acoes)
        if len(acoes) > 40:
            flow.append(Spacer(1, 0.2 * cm))
            flow.append(Paragraph(f"Mostrando 40 de {len(acoes)} ações. Exporte o CSV para a lista completa.", s["cell_muted"]))

    flow.append(PageBreak())
    flow.append(Paragraph("Detalhamento Completo dos Controles", s["h2"]))
    cabecalho_det: list[list[object]] = [["Controle", "Título", "Status", "Criticidade"]]
    for c in controles:
        av = avaliacoes.get(c.id, Avaliacao())
        label = status_individual(av if av.status else None)
        cabecalho_det.append([
            Paragraph(c.id, s["cell"]),
            Paragraph(c.titulo, s["cell"]),
            _badge_status(label, s),
            Paragraph(av.criticidade if av.status else "—", s["cell_muted"]),
        ])
    tabela_det = Table(cabecalho_det, colWidths=[1.8 * cm, 9.5 * cm, 3.2 * cm, 2.5 * cm], repeatRows=1)
    tabela_det.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _BG_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.25, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    flow.append(tabela_det)

    flow.append(Spacer(1, 0.5 * cm))
    flow.append(Paragraph(
        "Documento gerado automaticamente. Resultados refletem auto-avaliação e não substituem auditoria independente.",
        s["cell_muted"],
    ))

    doc.build(flow)
    return buffer.getvalue()
