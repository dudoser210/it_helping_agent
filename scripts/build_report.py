"""Render docs/REPORT.md to a polished PDF with Cyrillic fonts."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "REPORT.md"
OUTPUT = ROOT / "output" / "IT_Helping_Agent_Report.pdf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def normalize(text: str) -> str:
    return text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2011", "-").replace("→", "->")


def inline(text: str) -> str:
    text = html.escape(normalize(text))
    text = re.sub(r"`([^`]+)`", r'<font name="DejaVuSansMono">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(https?://[^\s<]+)", r'<link href="\1" color="#2563EB">\1</link>', text)
    return text


pdfmetrics.registerFont(TTFont("DejaVuSans", FONT))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_BOLD))
pdfmetrics.registerFont(TTFont("DejaVuSansMono", FONT_MONO))

base = getSampleStyleSheet()
styles = {
    "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="DejaVuSans", fontSize=8.9,
                           leading=12.6, textColor=colors.HexColor("#24324A"), spaceAfter=6),
    "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="DejaVuSans-Bold", fontSize=19,
                         leading=23, textColor=colors.HexColor("#0F2A5F"), spaceBefore=10, spaceAfter=9),
    "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="DejaVuSans-Bold", fontSize=13.5,
                         leading=17, textColor=colors.HexColor("#1D4ED8"), spaceBefore=12, spaceAfter=7,
                         keepWithNext=True),
    "h3": ParagraphStyle("H3", parent=base["Heading3"], fontName="DejaVuSans-Bold", fontSize=10.5,
                         leading=14, textColor=colors.HexColor("#0F2A5F"), spaceBefore=8, spaceAfter=5,
                         keepWithNext=True),
    "code": ParagraphStyle("Code", parent=base["Code"], fontName="DejaVuSansMono", fontSize=7.4,
                           leading=10, leftIndent=8, rightIndent=8, borderColor=colors.HexColor("#CBD5E1"),
                           borderWidth=.5, borderPadding=7, backColor=colors.HexColor("#F8FAFC"), spaceAfter=8),
    "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="DejaVuSans", fontSize=7.5,
                              leading=10, textColor=colors.HexColor("#64748B")),
}


def footer(canvas, doc):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#D8E1EE"))
    canvas.line(20 * mm, 15 * mm, width - 20 * mm, 15 * mm)
    canvas.setFont("DejaVuSans", 7.5)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(20 * mm, 9 * mm, "IT Helping Agent - отчёт по проекту")
    canvas.drawRightString(width - 20 * mm, 9 * mm, str(doc.page))
    canvas.restoreState()


def make_table(rows: list[list[str]]) -> Table:
    count = len(rows[0])
    available = A4[0] - 40 * mm
    widths = [available / count] * count
    pdata = [[Paragraph(inline(cell), styles["caption"] if r else ParagraphStyle(
        "TableHead", parent=styles["caption"], fontName="DejaVuSans-Bold", textColor=colors.white
    )) for cell in row] for r, row in enumerate(rows)]
    table = Table(pdata, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def parse_markdown(text: str):
    lines = normalize(text).splitlines()
    story = []
    paragraph: list[str] = []
    bullets: list[str] = []
    numbered: list[str] = []
    table_rows: list[list[str]] = []
    code: list[str] = []
    in_code = False

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            story.append(Paragraph(inline(" ".join(x.strip() for x in paragraph)), styles["body"]))
            paragraph = []

    def flush_lists():
        nonlocal bullets, numbered
        for items, kind in ((bullets, "bullet"), (numbered, "1")):
            if items:
                story.append(ListFlowable(
                    [ListItem(Paragraph(inline(x), styles["body"]), leftIndent=12) for x in items],
                    bulletType=kind, start="1", leftIndent=18, bulletFontName="DejaVuSans",
                    bulletFontSize=8, spaceAfter=5,
                ))
        bullets, numbered = [], []

    def flush_table():
        nonlocal table_rows
        if table_rows:
            usable = [row for row in table_rows if not all(re.fullmatch(r":?-{3,}:?", c) for c in row)]
            if len(usable) >= 2:
                story.extend([Spacer(1, 3), make_table(usable), Spacer(1, 8)])
            table_rows = []

    for line in lines:
        if line.startswith("```"):
            flush_paragraph(); flush_lists(); flush_table()
            if in_code:
                story.append(Paragraph("<br/>".join(html.escape(x or " ") for x in code), styles["code"]))
                code = []
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph(); flush_lists()
            table_rows.append([cell.strip() for cell in line.strip("|").split("|")])
            continue
        flush_table()
        if not line.strip():
            flush_paragraph(); flush_lists()
        elif line == "---":
            flush_paragraph(); flush_lists(); story.append(Spacer(1, 4))
        elif line.startswith("### "):
            flush_paragraph(); flush_lists(); story.append(Paragraph(inline(line[4:]), styles["h3"]))
        elif line.startswith("## "):
            flush_paragraph(); flush_lists(); story.append(Paragraph(inline(line[3:]), styles["h2"]))
        elif line.startswith("# "):
            flush_paragraph(); flush_lists(); story.append(Paragraph(inline(line[2:]), styles["h1"]))
        elif re.match(r"^- ", line):
            flush_paragraph(); bullets.append(line[2:])
        elif re.match(r"^\d+\. ", line):
            flush_paragraph(); numbered.append(re.sub(r"^\d+\. ", "", line))
        else:
            paragraph.append(line)
    flush_paragraph(); flush_lists(); flush_table()
    return story


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm, title="IT Helping Agent",
        author="Учебный проект",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=footer)])

    cover = [
        Spacer(1, 30 * mm),
        Paragraph("IT HELPDESK AGENT", ParagraphStyle(
            "Cover", parent=styles["h1"], alignment=TA_CENTER, fontSize=28, leading=34,
            textColor=colors.HexColor("#123A8C"), spaceAfter=12)),
        Paragraph("Мультиагентная система обработки заявок сотрудников", ParagraphStyle(
            "Subtitle", parent=styles["body"], alignment=TA_CENTER, fontSize=14, leading=20,
            textColor=colors.HexColor("#475569"))),
        Spacer(1, 22 * mm),
        Table([
            [Paragraph("Локальная LLM", styles["caption"]), Paragraph("Ollama + Qwen3.5", styles["caption"])],
            [Paragraph("Архитектура", styles["caption"]), Paragraph("Supervisor + specialists + critic", styles["caption"])],
            [Paragraph("Изоляция", styles["caption"]), Paragraph("Hardened Docker Compose", styles["caption"])],
            [Paragraph("Observability", styles["caption"]), Paragraph("Prometheus + Grafana + OTel + Jaeger", styles["caption"])],
        ], colWidths=[48 * mm, 88 * mm], style=TableStyle([
            ("BOX", (0, 0), (-1, -1), .7, colors.HexColor("#93C5FD")),
            ("INNERGRID", (0, 0), (-1, -1), .35, colors.HexColor("#DBEAFE")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EFF6FF")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("PADDING", (0, 0), (-1, -1), 8),
        ])),
        Spacer(1, 35 * mm),
        Paragraph("Автор(ы): ____________________", ParagraphStyle("Meta", parent=styles["body"], alignment=TA_CENTER)),
        Paragraph("Версия 1.0 · 2026", ParagraphStyle("Meta2", parent=styles["caption"], alignment=TA_CENTER)),
        PageBreak(),
    ]
    raw = SOURCE.read_text(encoding="utf-8")
    body_start = raw.find("## 1.")
    story = cover + parse_markdown(raw[body_start:])
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
