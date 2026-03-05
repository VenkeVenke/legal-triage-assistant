"""
pdf_report.py
Generates a PDF triage report for a single document using fpdf2.
"""

from fpdf import FPDF


def generate_triage_report(
    filename: str,
    classification: dict,
    entities: dict,
    summary: str = "",
) -> bytes:
    """
    Generates a formatted PDF report for a single triage result.

    Args:
        filename: The document filename.
        classification: Dict with classification, confidence, reasoning.
        entities: Dict with persons, dates, locations, offenses lists.
        summary: Plain-English summary of the document.

    Returns:
        PDF file content as bytes for st.download_button.
        Returns empty bytes on failure.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Legal Document Triage Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)

        # Filename
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"Document: {filename}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Classification
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Classification", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        cls_label = classification.get("classification", "N/A").replace("_", " ").title()
        confidence = classification.get("confidence", 0.0)
        pdf.cell(0, 8, f"Type: {cls_label}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Confidence: {confidence:.0%}", new_x="LMARGIN", new_y="NEXT")
        pdf.multi_cell(0, 8, f"Reasoning: {classification.get('reasoning', 'N/A')}")
        pdf.ln(3)

        # Summary
        if summary:
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "Summary", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 8, summary)
            pdf.ln(3)

        # Entities
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Extracted Entities", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)

        for label, key in [("Persons", "persons"), ("Dates", "dates"),
                           ("Locations", "locations"), ("Offenses", "offenses")]:
            items = entities.get(key, [])
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, f"{label}:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            if items:
                for item in items:
                    pdf.cell(0, 7, f"  - {item}", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(0, 7, "  None found", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        return bytes(pdf.output())

    except Exception:
        return b""
