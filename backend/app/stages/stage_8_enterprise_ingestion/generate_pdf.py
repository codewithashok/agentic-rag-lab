"""
Generates a realistic multi-page enterprise PDF:
'corporate_treasury_policy.pdf'
Includes clauses, tiered fee tables, cut-off schedules, and compliance triggers.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

DOCS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "sample_data"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = DOCS_DIR / "corporate_treasury_policy.pdf"


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=14
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=14,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    story = []

    # --- PAGE 1: Corporate Treasury & Settlement Policy ---
    story.append(Paragraph("Nexus Global Bank — Corporate Treasury & Settlement Agreement", title_style))
    story.append(Paragraph("Document Ref: NGB-TR-2026-V4 | Classification: Highly Confidential Commercial", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Section 1: Scope of Operations and Entity Governance", h1_style))
    story.append(Paragraph(
        "This Corporate Treasury and Settlement Agreement governs commercial cash management, domestic Real-Time "
        "Gross Settlement (RTGS), Automated Clearing House (ACH) transactions, and international cross-border SWIFT "
        "transfers executed by corporate account holders. Account holders maintain fiduciary liability for dual-custody "
        "authorization tokens. Access control mandates role-based segregation between transaction initiators and transaction approvers.",
        body_style
    ))

    story.append(Paragraph("Section 2: Daily Transaction Volume and Single-Transfer Limits", h1_style))
    story.append(Paragraph(
        "Commercial clients are categorized into three operational risk tiers based on average quarterly liquidity balance. "
        "Single-transaction limits apply strictly to unverified automated API flows. Transfers exceeding single-transaction limits "
        "require asynchronous secondary approval by a corporate officer with Grade-7 administrative signing power.",
        body_style
    ))

    # Tier Table
    tier_data = [
        ["Risk Tier", "Quarterly Balance", "Daily Outbound Limit", "Single Wire API Cap", "Required Signers"],
        ["Tier 1 - Standard", "INR 10M - 50M", "INR 25,000,000", "INR 5,000,000", "1 Authorized Officer"],
        ["Tier 2 - Premium", "INR 50M - 250M", "INR 100,000,000", "INR 20,000,000", "2 Dual-Key Officers"],
        ["Tier 3 - Enterprise", "INR 250M+", "INR 500,000,000", "INR 75,000,000", "2 Officers + Board Token"]
    ]
    t1 = Table(tier_data, colWidths=[100, 105, 115, 110, 100])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t1)
    story.append(Spacer(1, 14))

    # --- PAGE 2: Settlement Windows & Fee Schedules ---
    story.append(PageBreak())
    story.append(Paragraph("Section 3: Clearing Cut-Off Schedules & Processing Windows", h1_style))
    story.append(Paragraph(
        "All transactions submitted to the payment gateway are queued and executed against Reserve Bank clearing schedules. "
        "Payment instructions submitted after the declared cut-off are held in escrow status and processed at 08:00 AM IST "
        "on the subsequent banking business day.",
        body_style
    ))

    cutoff_data = [
        ["Channel Type", "Currency", "Processing Window (IST)", "Same-Day Cut-Off", "Batch Frequency"],
        ["Domestic RTGS", "INR", "07:00 to 18:00", "16:30 IST", "Continuous Real-Time"],
        ["NEFT Commercial", "INR", "24x7 Round-the-Clock", "N/A (Batch-wise)", "Half-Hourly Batches"],
        ["SWIFT Outbound", "USD / EUR / GBP", "09:00 to 17:00", "14:00 IST", "Hourly Batches"],
        ["ACH Bulk Payroll", "INR", "08:00 to 16:00", "13:00 IST", "Twice Daily (11:00 & 15:00)"]
    ]
    t2 = Table(cutoff_data, colWidths=[95, 80, 125, 105, 125])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t2)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Section 4: Comprehensive Fee Schedules & FX Margins", h1_style))
    story.append(Paragraph(
        "Commercial clients incur processing fees calculated monthly against consolidated transaction manifests. "
        "Cross-border SWIFT transfers carry a mandatory fixed intermediary communication fee of INR 750 plus variable "
        "foreign exchange markup as defined below. High-value transactions exceeding INR 100,000,000 enjoy zero domestic RTGS levy.",
        body_style
    ))

    fee_data = [
        ["Transaction Type", "Slab Range", "Standard Tariff", "Enterprise Rebate"],
        ["Domestic RTGS", "Up to INR 5,000,000", "INR 25 per transfer", "Waived for Tier 3"],
        ["Domestic RTGS", "Above INR 5,000,000", "INR 45 per transfer", "Waived for Tier 2 & 3"],
        ["SWIFT International", "Any amount", "INR 750 + 0.18% FX spread", "Fixed INR 500 flat fee"],
        ["ACH Bulk Payroll Return", "Per failed transaction", "INR 150 administrative charge", "No waiver permitted"]
    ]
    t3 = Table(fee_data, colWidths=[120, 140, 130, 140])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#047857")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t3)

    # --- PAGE 3: Compliance, AML & Sanctions ---
    story.append(PageBreak())
    story.append(Paragraph("Section 5: Anti-Money Laundering (AML) & Suspicious Transaction Reporting", h1_style))
    story.append(Paragraph(
        "Under the Financial Intelligence Unit (FIU-IND) statutory mandates, Nexus Global Bank enforces automated real-time "
        "screening of all beneficiary names against OFAC, UN Sanctions, and domestic designated entities databases. "
        "Transactions flagged with sanction match confidence exceeding 85% are automatically quarantined into 'AML_FREEZE' state.",
        body_style
    ))
    story.append(Paragraph(
        "Quarantined transactions cannot be released via API or ordinary branch operations. Release requires an authenticated "
        "Source of Funds Certificate (SFC) and explicit digital clearance from the Chief Compliance Officer within 48 business hours. "
        "If documentation is not furnished within 7 calendar days, funds are impounded and reported via Suspicious Transaction Report (STR).",
        body_style
    ))

    story.append(Paragraph("Section 6: Dispute Arbitration and Fraud Investigation Windows", h1_style))
    story.append(Paragraph(
        "Commercial clients must notify Nexus Global Bank in writing regarding unauthorized wire debits within exactly 24 hours "
        "of ledger debit notification. Notices delivered after 24 hours forfeit immediate conditional re-crediting rights. "
        "Disputed funds under investigation are isolated in non-interest-bearing suspense accounts pending resolution.",
        body_style
    ))

    doc.build(story)
    print(f"Enterprise PDF successfully generated at: {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()