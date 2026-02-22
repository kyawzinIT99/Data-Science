import io
import math
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Register a Unicode font to support Thai, Burmese, etc.
# Fallback to standard fonts if the system font isn't found
UNICODE_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
DEFAULT_FONT = "Helvetica"
UNICODE_FONT_NAME = "ArialUnicode"

if os.path.exists(UNICODE_FONT_PATH):
    pdfmetrics.registerFont(TTFont(UNICODE_FONT_NAME, UNICODE_FONT_PATH))
    ACTIVE_FONT = UNICODE_FONT_NAME
else:
    ACTIVE_FONT = DEFAULT_FONT

from app.models.schemas import AnalysisResponse, DashboardResponse


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName=ACTIVE_FONT,
        fontSize=24,
        spaceAfter=6,
        textColor=colors.HexColor("#1e3a5f"),
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontName=ACTIVE_FONT,
        fontSize=11,
        textColor=colors.HexColor("#6b7280"),
        alignment=TA_CENTER,
        spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontName=ACTIVE_FONT,
        fontSize=14,
        textColor=colors.HexColor("#1e3a5f"),
        spaceBefore=16,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="BulletText",
        parent=styles["Normal"],
        fontName=ACTIVE_FONT,
        fontSize=10,
        leftIndent=20,
        spaceAfter=4,
        textColor=colors.HexColor("#374151"),
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        parent=styles["Normal"],
        fontName=ACTIVE_FONT,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
    ))
    return styles


def _generate_chart_image(chart: dict) -> io.BytesIO | None:
    """Render a chart dict to a PNG image buffer using matplotlib."""
    try:
        data = chart.get("data", [])
        if not data:
            return None

        fig, ax = plt.subplots(figsize=(5, 3))
        fig.patch.set_facecolor("white")
        chart_type = chart.get("chart_type", "bar")

        labels = [d.get("label", str(i)) for i, d in enumerate(data)]
        values = [float(d.get("value", 0)) for d in data]

        palette = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#6366f1"]

        if chart_type == "pie":
            ax.pie(values, labels=labels, autopct="%1.1f%%",
                   colors=palette[:len(values)], startangle=140)
        elif chart_type == "line":
            ax.plot(labels, values, marker="o", color="#8b5cf6", linewidth=2)
            ax.fill_between(range(len(values)), values, alpha=0.1, color="#8b5cf6")
            plt.xticks(rotation=45, ha="right", fontsize=8)
        elif chart_type == "scatter":
            xs = [float(d.get("x", 0)) for d in data]
            ys = [float(d.get("y", 0)) for d in data]
            ax.scatter(xs, ys, color="#10b981", alpha=0.7)
        else:
            bar_colors = palette[:len(values)]
            ax.bar(labels, values, color=bar_colors)
            plt.xticks(rotation=45, ha="right", fontsize=8)

        ax.set_title(chart.get("title", ""), fontsize=11, fontweight="bold", color="#1e3a5f")

        if chart_type != "pie":
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        plt.close("all")
        return None


def generate_pdf_report(
    filename: str,
    analysis: AnalysisResponse,
    dashboard: DashboardResponse | None = None,
) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=50, leftMargin=50,
        topMargin=50, bottomMargin=50,
    )
    styles = _build_styles()
    story = []

    # Title
    story.append(Spacer(1, 10))
    if dashboard and dashboard.detection_profile:
        story.append(Paragraph(f"Dataset Intelligence: {dashboard.detection_profile}", ParagraphStyle(
            "ProfileBadge", parent=styles["Normal"], fontSize=8, textColor=colors.white,
            backColor=colors.HexColor("#3b82f6"), borderPadding=4, borderRadius=4, alignment=TA_CENTER
        )))
        story.append(Spacer(1, 10))

    story.append(Paragraph("Executive Business Case", styles["ReportTitle"]))
    story.append(Paragraph(f"Source file: {filename}", styles["ReportSubtitle"]))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#3b82f6"), spaceAfter=15,
    ))

    # Summary
    story.append(Paragraph("Executive Summary", styles["SectionHeading"]))
    story.append(Paragraph(analysis.summary, styles["BodyText2"]))
    story.append(Spacer(1, 8))

    # --- NEW: P&L Financials ---
    if dashboard and dashboard.profit_loss:
        story.append(Paragraph("Financial Performance", styles["SectionHeading"]))
        pl = dashboard.profit_loss
        pl_data = [
            ["Total Revenue", "Total Cost", "Net Profit", "Margin"],
            [f"${pl.total_revenue:,.2f}" if not math.isnan(pl.total_revenue) else "$0.00", 
             f"${pl.total_cost:,.2f}" if not math.isnan(pl.total_cost) else "$0.00", 
             f"${pl.total_profit:,.2f}" if hasattr(pl, "total_profit") and not math.isnan(pl.total_profit) else f"${pl.net_profit:,.2f}" if not math.isnan(pl.net_profit) else "$0.00", 
             f"{pl.margin_percentage}%" if not math.isnan(pl.margin_percentage) else "0%"]
        ]
        t = Table(pl_data, colWidths=[120, 120, 120, 120])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f1f5f9")),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # Key Insights
    story.append(Paragraph("Key Insights", styles["SectionHeading"]))
    for insight in analysis.key_insights:
        story.append(Paragraph(f"\u2022  {insight}", styles["BulletText"]))
    story.append(Spacer(1, 8))

    # Trends
    if analysis.trends:
        story.append(Paragraph("Trends", styles["SectionHeading"]))
        for trend in analysis.trends:
            story.append(Paragraph(f"\u2022  {trend}", styles["BulletText"]))
        story.append(Spacer(1, 8))

    # Recommendations / Growth Suggestions
    if dashboard and dashboard.growth_suggestions:
        story.append(Paragraph("AI Strategic Growth Plan", styles["SectionHeading"]))
        for suggestion in dashboard.growth_suggestions:
            story.append(Paragraph(f"<b>{suggestion.title}</b> (Impact: {suggestion.impact})", styles["BulletText"]))
            story.append(Paragraph(suggestion.description, styles["BulletText"]))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))
    elif analysis.recommendations:
        story.append(Paragraph("Recommendations", styles["SectionHeading"]))
        for i, rec in enumerate(analysis.recommendations, 1):
            story.append(Paragraph(f"{i}.  {rec}", styles["BulletText"]))
        story.append(Spacer(1, 8))

    # Data Statistics Table
    if analysis.data_stats:
        story.append(Paragraph("Data Statistics", styles["SectionHeading"]))
        table_data = [["Metric", "Value"]]
        for key, val in analysis.data_stats.items():
            display_val = str(val) if not isinstance(val, (dict, list)) else str(len(val))
            table_data.append([key.replace("_", " ").title(), display_val])

        table = Table(table_data, colWidths=[200, 280])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # --- NEW: Anomalies & Risk ---
    if dashboard and dashboard.anomalies:
        story.append(Paragraph("Risk & Anomaly Alerts", styles["SectionHeading"]))
        for anomaly in dashboard.anomalies:
            story.append(Paragraph(f"[ALERT] <b>{anomaly.column}</b>: {anomaly.reason} (Value: {anomaly.value} at Row {anomaly.row_index})", styles["BulletText"]))
        story.append(Spacer(1, 12))

    # --- NEW: Market Segments ---
    if dashboard and dashboard.segments:
        story.append(Paragraph("Large-Scale Market Segmentation", styles["SectionHeading"]))
        for seg in dashboard.segments:
            story.append(Paragraph(f"<b>{seg.name}</b> ({seg.size} records)", styles["BulletText"]))
            story.append(Paragraph(f"<i>Characteristics:</i> {seg.characteristics}", styles["BulletText"]))
            story.append(Paragraph(f"<i>Strategy:</i> {seg.growth_strategy}", styles["BulletText"]))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 12))

    # Charts
    if dashboard and dashboard.charts:
        story.append(PageBreak())
        story.append(Paragraph("Visual Analysis", styles["SectionHeading"]))
        story.append(Spacer(1, 8))

        for chart in dashboard.charts:
            chart_dict = chart.model_dump() if hasattr(chart, "model_dump") else chart.__dict__
            img_buf = _generate_chart_image(chart_dict)
            if img_buf:
                story.append(Image(img_buf, width=420, height=250))
                story.append(Paragraph(chart.description, styles["BulletText"]))
                story.append(Spacer(1, 16))

    # Footer
    story.append(Spacer(1, 30))
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#cbd5e1"), spaceAfter=8,
    ))
    story.append(Paragraph(
        "Generated by AI Data Analysis Platform",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER),
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
