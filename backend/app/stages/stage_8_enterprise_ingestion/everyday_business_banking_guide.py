"""
Generate a clean, easy-to-understand multi-page PDF for RAG experiments.

Output:
    docs/sample_data/everyday_business_banking_guide.pdf

The content is fictional sample data for software testing, not a real bank policy.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ---------------------------------------------------------------------
# Output path: keeps the same folder structure as the original script
# ---------------------------------------------------------------------
# parents: [0] stage_8_enterprise_ingestion, [1] stages, [2] app, [3] backend -> backend/docs/sample_data
DOCS_DIR = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sample_data"
)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = DOCS_DIR / "everyday_business_banking_guide.pdf"


# ---------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------
NAVY = colors.HexColor("#244766")
BLUE = colors.HexColor("#174A7E")
TEAL = colors.HexColor("#176B5B")
TEXT = colors.HexColor("#273444")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#CBD5E1")
LIGHT = colors.HexColor("#F5F8FB")
CALLOUT_BG = colors.HexColor("#EDF5FB")
CALLOUT_BORDER = colors.HexColor("#B8D5E8")


def build_styles():
    """Create consistent typography for the entire document."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=27,
            textColor=colors.HexColor("#17324D"),
            alignment=TA_CENTER,
            spaceAfter=14,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#526579"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=BLUE,
            spaceBefore=8,
            spaceAfter=8,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=TEAL,
            spaceBefore=7,
            spaceAfter=5,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyClean",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=TEXT,
            spaceAfter=7,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallNote",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            spaceAfter=5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=TEXT,
            spaceAfter=0,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            spaceAfter=0,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#17324D"),
            backColor=CALLOUT_BG,
            borderColor=CALLOUT_BORDER,
            borderWidth=0.6,
            borderPadding=8,
            spaceBefore=4,
            spaceAfter=10,
        )
    )

    return styles


def paragraph(text, style="BodyClean"):
    """Create a paragraph using one of the document's named styles."""
    return Paragraph(text, STYLES[style])


def make_table(rows, col_widths):
    """Build a readable table with a dark header and alternating rows."""
    formatted_rows = []

    for row_index, row in enumerate(rows):
        style_name = "TableHeader" if row_index == 0 else "TableText"
        formatted_rows.append(
            [paragraph(str(cell), style_name) for cell in row]
        )

    table = Table(
        formatted_rows,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, LIGHT],
                ),
            ]
        )
    )

    return table


def add_page_footer(canvas, doc):
    """Draw a consistent footer and page number on every page."""
    canvas.saveState()

    canvas.setStrokeColor(colors.HexColor("#D7E0E8"))
    canvas.setLineWidth(0.6)
    canvas.line(
        0.62 * inch,
        0.45 * inch,
        7.88 * inch,
        0.45 * inch,
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        0.62 * inch,
        0.28 * inch,
        "Everyday Business Banking Guide | Fictional RAG sample",
    )
    canvas.drawRightString(
        7.88 * inch,
        0.28 * inch,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def build_story():
    """Create the document content in reading order."""
    story = []

    # -----------------------------------------------------------------
    # Page 1: Introduction and payment limits
    # -----------------------------------------------------------------
    story.extend(
        [
            Spacer(1, 0.25 * inch),
            paragraph("Everyday Business Banking Guide", "CoverTitle"),
            paragraph(
                "A plain-language sample document for learning and testing "
                "Retrieval-Augmented Generation (RAG)",
                "Subtitle",
            ),
            Spacer(1, 0.1 * inch),
            paragraph(
                "<b>About this guide</b><br/>"
                "This guide explains common business-banking payment rules "
                "in everyday language. It covers payment limits, processing "
                "times, fees, and what happens when a payment looks "
                "suspicious. The bank and figures in this document are "
                "fictional and are provided only as sample data for "
                "software testing.",
                "Callout",
            ),
            paragraph("1. What is this guide about?", "Section"),
            paragraph(
                "A business bank account helps a company receive money, "
                "pay suppliers, run payroll, and send money to other "
                "countries. Banks set rules to reduce mistakes and fraud. "
                "These rules can include how much money a company can send, "
                "who must approve a payment, when payments are processed, "
                "and what fees apply."
            ),
            paragraph("2. Who can approve a payment?", "Section"),
            paragraph(
                "Companies should separate the person who creates a "
                "payment from the person who approves it. This helps "
                "prevent one person from sending money without a second "
                "person checking it. Larger payments may need approval "
                "from two authorized officers or an additional senior "
                "approver."
            ),
            paragraph("3. Example payment limits", "Section"),
            paragraph(
                "The fictional bank in this example uses three account "
                "levels. A company’s level depends on the average amount "
                "of money it keeps in the account. The limits below apply "
                "to automated payments that have not completed additional "
                "verification."
            ),
            make_table(
                [
                    [
                        "Account level",
                        "Average balance",
                        "Maximum total sent per day",
                        "Maximum single automated transfer",
                        "Who must approve?",
                    ],
                    [
                        "Standard",
                        "INR 10 million to 50 million",
                        "INR 25 million",
                        "INR 5 million",
                        "One authorized officer",
                    ],
                    [
                        "Premium",
                        "INR 50 million to 250 million",
                        "INR 100 million",
                        "INR 20 million",
                        "Two authorized officers",
                    ],
                    [
                        "Enterprise",
                        "More than INR 250 million",
                        "INR 500 million",
                        "INR 75 million",
                        "Two officers plus a board-level approval token",
                    ],
                ],
                [
                    0.82 * inch,
                    1.12 * inch,
                    1.25 * inch,
                    1.28 * inch,
                    1.55 * inch,
                ],
            ),
            Spacer(1, 8),
            paragraph(
                "<b>Example:</b> If a Standard account tries to send "
                "INR 6 million in one automated transfer, it is above the "
                "INR 5 million single-transfer limit. The company must use "
                "the required additional approval process before the "
                "transfer can proceed."
            ),
            PageBreak(),
        ]
    )

    # -----------------------------------------------------------------
    # Page 2: Processing times and fees
    # -----------------------------------------------------------------
    story.extend(
        [
            paragraph("4. When are payments processed?", "Section"),
            paragraph(
                "A payment’s arrival time depends on the payment method "
                "and when the company submits it. If a payment misses the "
                "same-day cut-off time, it may be processed on the next "
                "banking business day. A banking business day normally "
                "excludes weekends and bank holidays."
            ),
            make_table(
                [
                    [
                        "Payment method",
                        "Typical processing hours (India time)",
                        "Same-day cut-off",
                        "How processing works",
                    ],
                    [
                        "Domestic RTGS",
                        "7:00 AM to 6:00 PM",
                        "4:30 PM",
                        "Processed individually in real time during the service window",
                    ],
                    [
                        "NEFT business payment",
                        "Available 24 hours",
                        "No single cut-off; batch processing applies",
                        "Processed in scheduled batches",
                    ],
                    [
                        "International SWIFT transfer",
                        "9:00 AM to 5:00 PM",
                        "2:00 PM",
                        "Processed in hourly batches during the service window",
                    ],
                    [
                        "Bulk payroll file",
                        "8:00 AM to 4:00 PM",
                        "1:00 PM",
                        "Two batches, scheduled around 11:00 AM and 3:00 PM",
                    ],
                ],
                [
                    1.15 * inch,
                    1.45 * inch,
                    1.25 * inch,
                    2.17 * inch,
                ],
            ),
            Spacer(1, 7),
            paragraph(
                "<b>Example:</b> A company submits an international transfer "
                "at 3:00 PM. The sample cut-off is 2:00 PM, so the payment "
                "may not be processed until the next banking business day. "
                "Submitting a payment does not guarantee that the recipient "
                "receives it immediately."
            ),
            paragraph("5. What fees might apply?", "Section"),
            paragraph(
                "The bank may charge a fee for processing a payment. "
                "International transfers may also include a foreign-exchange "
                "(FX) margin, which means the exchange rate offered by the "
                "bank may differ from the market rate. Fees can depend on "
                "the payment method, amount, and account level."
            ),
            make_table(
                [
                    [
                        "Payment type",
                        "Amount or situation",
                        "Standard fee",
                        "Possible discount or exception",
                    ],
                    [
                        "Domestic RTGS",
                        "Up to INR 5 million",
                        "INR 25 per transfer",
                        "No fee for Enterprise accounts",
                    ],
                    [
                        "Domestic RTGS",
                        "Above INR 5 million",
                        "INR 45 per transfer",
                        "No fee for Premium and Enterprise accounts",
                    ],
                    [
                        "International SWIFT",
                        "Any amount",
                        "INR 750 plus a 0.18% FX margin",
                        "Enterprise accounts pay a fixed INR 500 transfer fee; FX margin may still apply",
                    ],
                    [
                        "Bulk payroll return",
                        "Each failed payment",
                        "INR 150 per failed payment",
                        "No waiver in this sample policy",
                    ],
                ],
                [
                    1.12 * inch,
                    1.3 * inch,
                    1.55 * inch,
                    2.05 * inch,
                ],
            ),
            Spacer(1, 7),
            paragraph(
                "<b>Important:</b> A fee waiver does not necessarily mean "
                "every cost is removed. A fixed transfer fee and a "
                "foreign-exchange margin are different charges. Always "
                "check which charge the waiver covers.",
                "Callout",
            ),
            PageBreak(),
        ]
    )

    # -----------------------------------------------------------------
    # Page 3: Suspicious payments and disputes
    # -----------------------------------------------------------------
    story.extend(
        [
            paragraph(
                "6. What happens if a payment looks suspicious?", "Section"
            ),
            paragraph(
                "Banks check payments to help identify fraud, money "
                "laundering, and payments involving restricted people or "
                "organizations. A payment may be stopped temporarily if "
                "the screening system finds a strong possible match. A "
                "match is a warning to investigate; it does not "
                "automatically prove that the customer has done something "
                "wrong."
            ),
            paragraph(
                "In this sample policy, a match score above 85% puts the "
                "payment into a temporary review status called "
                "<b>AML_FREEZE</b>. While it is in this status, the customer "
                "cannot release the payment through the normal API or "
                "branch process."
            ),
            paragraph(
                "To request a review, the company must provide a Source of "
                "Funds Certificate. In plain language, this is evidence "
                "showing where the money came from. The bank’s Chief "
                "Compliance Officer must approve the release. The sample "
                "policy says this review should happen within 48 business "
                "hours. If the requested documents are not provided within "
                "7 calendar days, the bank may hold the funds and submit a "
                "Suspicious Transaction Report (STR) to the appropriate "
                "authority."
            ),
            paragraph(
                "7. What should a company do if it sees an unauthorized payment?",
                "Section",
            ),
            paragraph(
                "If a company notices a payment it did not approve, it "
                "should contact the bank in writing immediately and keep "
                "the payment reference, date, amount, and supporting "
                "evidence. This sample policy asks customers to report "
                "unauthorized wire debits within 24 hours of the debit "
                "notification."
            ),
            paragraph(
                "Reporting after 24 hours may affect whether the company "
                "receives an immediate temporary credit while the case is "
                "investigated. The bank may place the disputed money in a "
                "separate holding account while it reviews the evidence. "
                "A temporary credit is not the same as a final decision "
                "that the bank will cover the loss."
            ),
            paragraph("8. Quick examples", "Section"),
            make_table(
                [
                    ["Situation", "What it means", "What to do"],
                    [
                        "A payment is above the account’s single-transfer limit",
                        "The payment needs the required extra approval.",
                        "Ask the authorized approver to review it before resubmitting.",
                    ],
                    [
                        "A payment is submitted after the cut-off",
                        "It may be processed on the next banking business day.",
                        "Check the payment status and tell the recipient about the likely delay.",
                    ],
                    [
                        "The bank flags a possible sanctions match",
                        "The payment is paused for a compliance review.",
                        "Provide the requested source-of-funds documents and wait for formal clearance.",
                    ],
                    [
                        "An unfamiliar debit appears on the account",
                        "The payment may be unauthorized.",
                        "Contact the bank in writing immediately and retain evidence.",
                    ],
                    [
                        "A payroll payment fails",
                        "The recipient may not have received the money.",
                        "Review the failure reason, correct the details, and check any applicable return fee.",
                    ],
                ],
                [1.55 * inch, 2.0 * inch, 2.47 * inch],
            ),
            PageBreak(),
        ]
    )

    # -----------------------------------------------------------------
    # Page 4: FAQs and glossary, useful for retrieval testing
    # -----------------------------------------------------------------
    story.extend(
        [
            paragraph("9. Frequently asked questions", "Section"),
            paragraph(
                "<b>Q: Can one employee create and approve the same payment?</b><br/>"
                "A: The sample policy expects separation between the person "
                "who creates a payment and the person who approves it. "
                "The required number of approvers depends on the account "
                "level and payment amount."
            ),
            paragraph(
                "<b>Q: If I send money after the cut-off, is it lost?</b><br/>"
                "A: No. In this sample policy, a payment submitted after "
                "the cut-off is held and processed at 8:00 AM India time "
                "on the next banking business day. Actual timing can depend "
                "on holidays and the payment network."
            ),
            paragraph(
                "<b>Q: What does an FX margin mean?</b><br/>"
                "A: It is the difference between the exchange rate used "
                "for the customer’s transfer and a reference market rate. "
                "It is separate from a fixed transfer fee."
            ),
            paragraph(
                "<b>Q: What does AML_FREEZE mean?</b><br/>"
                "A: It is a temporary status used when a payment has a "
                "strong possible match during anti-money-laundering or "
                "sanctions screening. The payment stays on hold until the "
                "bank completes its review and gives the required clearance."
            ),
            paragraph(
                "<b>Q: How quickly should an unauthorized payment be reported?</b><br/>"
                "A: The sample policy says within 24 hours of the debit "
                "notification. The safest practical step is to contact "
                "the bank immediately when the payment is discovered."
            ),
            paragraph(
                "<b>Q: Does a suspicious-payment alert prove fraud?</b><br/>"
                "A: No. It indicates that the payment needs further review. "
                "The bank must assess the information and documents before "
                "deciding what to do."
            ),
            paragraph("10. Key terms in simple language", "Section"),
            make_table(
                [
                    ["Term", "Plain-language meaning"],
                    [
                        "RTGS",
                        "A way to transfer money between banks, often used for high-value payments.",
                    ],
                    [
                        "NEFT",
                        "A bank transfer service that processes payments in batches.",
                    ],
                    [
                        "SWIFT",
                        "A messaging network banks use to coordinate many international payments.",
                    ],
                    [
                        "Cut-off time",
                        "The latest time a payment can be submitted to be considered for that day’s processing.",
                    ],
                    [
                        "Dual approval",
                        "Two authorized people must approve a payment.",
                    ],
                    [
                        "AML",
                        "Anti-money laundering: checks intended to detect and prevent money laundering.",
                    ],
                    [
                        "Sanctions screening",
                        "Checking whether a person or organization appears on a restricted-party list.",
                    ],
                    [
                        "Source of Funds Certificate",
                        "Documents explaining where the money for a transaction came from.",
                    ],
                    [
                        "STR",
                        "Suspicious Transaction Report: a report submitted when a transaction raises a required level of suspicion.",
                    ],
                ],
                [1.55 * inch, 4.47 * inch],
            ),
            Spacer(1, 10),
            paragraph(
                "Document status: Fictional sample for RAG development and "
                "testing. It is not legal, financial, or banking advice and "
                "does not describe the actual rules of any real bank.",
                "SmallNote",
            ),
        ]
    )

    return story


def build_pdf():
    """Generate the PDF file."""
    global STYLES
    STYLES = build_styles()

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=0.62 * inch,
        leftMargin=0.62 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title="Everyday Business Banking Guide",
        author="RAG Sample Document Generator",
        subject="Plain-language fictional banking policy for RAG testing",
    )

    story = build_story()
    doc.build(
        story,
        onFirstPage=add_page_footer,
        onLaterPages=add_page_footer,
    )

    print(f"PDF successfully generated at: {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()
