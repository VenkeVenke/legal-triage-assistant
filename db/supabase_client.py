"""
supabase_client.py
Handles all Supabase operations: saving triage results and fetching history.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client once at module level
_url = os.getenv("SUPABASE_URL")
_key = os.getenv("SUPABASE_KEY")

if not _url or not _key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase: Client = create_client(_url, _key)


def save_triage_result(
    filename: str,
    classification: dict,
    entities: dict,
    raw_text: str,
    summary: str = "",
) -> dict:
    """
    Saves a triage result (classification + entities) to Supabase.

    Args:
        filename: The uploaded PDF filename.
        classification: Dict with classification, confidence, reasoning.
        entities: Dict with persons, dates, locations, offenses lists.
        raw_text: The full extracted text from the PDF.

    Returns:
        The inserted row as a dict, or a dict with "error" key on failure.
    """
    row = {
        "filename": filename,
        "classification": classification.get("classification", "error"),
        "confidence": classification.get("confidence", 0.0),
        "reasoning": classification.get("reasoning", ""),
        "persons": entities.get("persons", []),
        "dates": entities.get("dates", []),
        "locations": entities.get("locations", []),
        "offenses": entities.get("offenses", []),
        "raw_text": raw_text,
        "summary": summary,
    }

    try:
        result = supabase.table("triage_results").insert(row).execute()
        return result.data[0] if result.data else row
    except Exception as e:
        return {"error": f"Failed to save to Supabase: {str(e)}"}


def get_triage_history(limit: int = 20) -> list:
    """
    Fetches recent triage results from Supabase, newest first.

    Args:
        limit: Max number of results to return (default: 20).

    Returns:
        A list of triage result dicts, or an empty list on failure.
    """
    try:
        result = (
            supabase.table("triage_results")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data if result.data else []
    except Exception:
        return []


# Quick test when running this file directly
if __name__ == "__main__":
    # Test save
    test_classification = {
        "classification": "warrant",
        "confidence": 1.0,
        "reasoning": "Test entry",
    }
    test_entities = {
        "persons": ["John Smith"],
        "dates": ["January 15, 2025"],
        "locations": ["Los Angeles, CA"],
        "offenses": ["Burglary"],
    }

    print("Saving test result...")
    saved = save_triage_result("test.pdf", test_classification, test_entities, "test text")
    if "error" in saved:
        print(f"Error: {saved['error']}")
    else:
        print(f"Saved: {saved['id']}")

    # Test fetch
    print("\nFetching history...")
    history = get_triage_history(5)
    print(f"Found {len(history)} results")
    for row in history:
        print(f"  - {row['filename']}: {row['classification']} ({row['confidence']})")
