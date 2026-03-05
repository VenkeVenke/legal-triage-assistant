"""
csv_export.py
Exports triage history as a CSV string for download.
"""

import csv
import io


def export_history_as_csv(history: list) -> str:
    """
    Converts a list of triage result dicts (from Supabase) to a CSV string.

    Args:
        history: List of row dicts from get_triage_history().

    Returns:
        A CSV string ready for st.download_button.
    """
    if not history:
        return ""

    output = io.StringIO()
    fieldnames = [
        "filename", "classification", "confidence", "reasoning",
        "summary", "persons", "dates", "locations", "offenses", "created_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for row in history:
        writer.writerow({
            "filename": row.get("filename", ""),
            "classification": row.get("classification", ""),
            "confidence": row.get("confidence", 0.0),
            "reasoning": row.get("reasoning", ""),
            "summary": row.get("summary", ""),
            "persons": "; ".join(row.get("persons", [])),
            "dates": "; ".join(row.get("dates", [])),
            "locations": "; ".join(row.get("locations", [])),
            "offenses": "; ".join(row.get("offenses", [])),
            "created_at": row.get("created_at", ""),
        })

    return output.getvalue()
