
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


def safe_text(value):
    """Escape untrusted text before inserting it into a PDF."""
    return escape(str(value if value is not None else ""))


def generate_pdf_report(report: dict) -> bytes:
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=(595.28, 841.89),
        rightMargin=45,
        leftMargin=45,
        topMargin=48,
        bottomMargin=48,
        title="VeriFlow AI - Verification Report",
        author="VeriFlow AI",
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="VFTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=29,
        textColor=colors.HexColor("#243B87"),
        alignment=TA_CENTER,
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        name="VFHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#243B87"),
        spaceBefore=18,
        spaceAfter=9,
    ))

    styles.add(ParagraphStyle(
        name="VFBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=15,
        spaceAfter=8,
        wordWrap="CJK",
    ))

    styles.add(ParagraphStyle(
        name="VFSmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#526078"),
        spaceAfter=6,
        wordWrap="CJK",
    ))

    story = []

    story.append(Paragraph(
        "VeriFlow AI",
        styles["VFTitle"],
    ))

    story.append(Paragraph(
        "Multi-Agent Evidence Verification Report",
        styles["VFBody"],
    ))

    story.append(Spacer(1, 15))

    story.append(Paragraph(
        "Claim Under Investigation",
        styles["VFHeading"],
    ))

    story.append(Paragraph(
        safe_text(report.get("claim", "Not provided")),
        styles["VFBody"],
    ))

    verdict = report.get("verdict", "UNKNOWN")

    story.append(Paragraph(
        "Preliminary Verdict",
        styles["VFHeading"],
    ))

    story.append(Paragraph(
        f"<b>{safe_text(verdict.replace('_', ' '))}</b>",
        styles["VFBody"],
    ))

    story.append(Paragraph(
        safe_text(report.get("summary", "")),
        styles["VFBody"],
    ))

    counts = report.get("evidence_counts", {})

    metrics = [
        ["Supporting", "Contradicting", "Insufficient"],
        [
            str(counts.get("supports", 0)),
            str(counts.get("contradicts", 0)),
            str(counts.get("insufficient", 0)),
        ],
    ]

    table = Table(
        metrics,
        colWidths=[165, 165, 165],
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#E9EEFF")),
        ("TEXTCOLOR", (0, 0), (-1, -1),
         colors.HexColor("#17233B")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (-1, -1), 0.5,
         colors.HexColor("#CCD5EA")),
    ]))

    story.append(Spacer(1, 12))
    story.append(table)

    story.append(Paragraph(
        "Evidence and Sources",
        styles["VFHeading"],
    ))

    evidence = report.get("evidence", [])

    if not evidence:
        story.append(Paragraph(
            "No evidence was retrieved.",
            styles["VFBody"],
        ))

    for index, item in enumerate(evidence, 1):
        title = safe_text(
            item.get("title") or "Untitled Source"
        )
        stance = safe_text(
            item.get("stance") or "INSUFFICIENT"
        )
        reason = safe_text(item.get("reason", ""))
        quote = safe_text(item.get("quote", ""))
        url = safe_text(item.get("url", ""))

        blocks = [
            Paragraph(
                f"<b>{index}. {title}</b>",
                styles["VFBody"],
            ),
            Paragraph(
                f"<b>Assessment:</b> {stance}",
                styles["VFSmall"],
            ),
            Paragraph(
                f"<b>Reason:</b> {reason}",
                styles["VFSmall"],
            ),
        ]

        if quote:
            blocks.append(Paragraph(
                f"<b>Quotation:</b> {quote}",
                styles["VFSmall"],
            ))

        blocks.append(Paragraph(
            "<b>Exact quote match:</b> "
            + (
                "Yes"
                if item.get("quote_verified") is True
                else "No"
            ),
            styles["VFSmall"],
        ))

        if url:
            blocks.append(Paragraph(
                f"<b>Source URL:</b> {url}",
                styles["VFSmall"],
            ))

        blocks.append(Spacer(1, 10))

        story.append(KeepTogether(blocks))

    story.append(Paragraph(
        "Important Limitations",
        styles["VFHeading"],
    ))

    story.append(Paragraph(
        "This report contains preliminary AI-generated "
        "assessments based on retrieved source excerpts. "
        "A matching quotation does not establish that "
        "the claim is factually correct. Sources and "
        "reasoning may contain errors. Independent "
        "human review is recommended.",
        styles["VFBody"],
    ))

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
