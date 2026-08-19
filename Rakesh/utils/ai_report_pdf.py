"""Build downloadable PDF files for AI maintenance reports."""

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _footer(canvas, document) -> None:
    """Draw a simple document footer on every report page."""
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(20 * mm, 14 * mm, A4[0] - 20 * mm, 14 * mm)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20 * mm, 9 * mm, "FacilityOps AI - Maintenance report")
    canvas.drawRightString(A4[0] - 20 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def build_ai_report_pdf(report_markdown: str) -> bytes:
    """Convert the structured on-screen maintenance report into a print-ready PDF."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title="AI Maintenance Report",
        author="FacilityOps AI",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=23,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F2B4D"),
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0F2B4D"),
        spaceBefore=10,
        spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=7,
    )
    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-9,
        spaceAfter=4,
    )

    story = []
    for line in report_markdown.splitlines():
        text = line.strip()
        if not text:
            story.append(Spacer(1, 3))
        elif text.startswith("# "):
            story.append(Paragraph(escape(text[2:]), title_style))
        elif text.startswith("## "):
            story.append(Paragraph(escape(text[3:]), heading_style))
        elif text.startswith("- "):
            bullet_text = escape(text[2:]).replace("**", "")
            story.append(Paragraph(f"&bull; {bullet_text}", bullet_style))
        else:
            paragraph = escape(text).replace("**", "")
            story.append(Paragraph(paragraph, body_style))

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
