"""
extractor.py
Extracts key entities (persons, dates, locations, offenses) from legal
document text using Ollama (Llama 3).
"""

import json
from pathlib import Path
import requests

# Load the prompt template once at module level
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extract_prompt.txt"
PROMPT_TEMPLATE = PROMPT_PATH.read_text()

OLLAMA_URL = "http://localhost:11434/api/chat"
ENTITY_KEYS = {"persons", "dates", "locations", "offenses"}


def extract_entities(text: str, model: str = "llama3") -> dict:
    """
    Sends document text to Ollama (Llama 3) and returns extracted entities.

    Args:
        text: The extracted text content of the legal document.
        model: The Ollama model to use (default: llama3).

    Returns:
        A dict with keys: persons, dates, locations, offenses (each a list).
        On failure, returns a dict with empty lists and an "error" key.
    """
    prompt = PROMPT_TEMPLATE.replace("{document_text}", text)
    empty = {key: [] for key in ENTITY_KEYS}

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0},
            },
            timeout=120,
        )
        response.raise_for_status()

        raw = response.json()["message"]["content"].strip()
        result = json.loads(raw)

        # Ensure all expected keys exist and are lists
        for key in ENTITY_KEYS:
            if key not in result or not isinstance(result[key], list):
                result[key] = []

        return result

    except json.JSONDecodeError:
        return {**empty, "error": f"Failed to parse JSON: {raw[:200]}"}
    except requests.ConnectionError:
        return {**empty, "error": "Cannot connect to Ollama. Is it running?"}
    except Exception as e:
        return {**empty, "error": f"API call failed: {str(e)}"}


# Quick test when running this file directly
if __name__ == "__main__":
    sample = """
    SEARCH WARRANT
    STATE OF CALIFORNIA, COUNTY OF LOS ANGELES
    TO ANY PEACE OFFICER IN THE STATE OF CALIFORNIA:
    Proof by affidavit having been made before me by Detective John Smith,
    Badge #4521, that there is probable cause to believe that the property
    described herein may be found at the premises located at 1234 Oak Street,
    Los Angeles, CA 90001, and that said property constitutes evidence of a
    felony violation of Penal Code Section 459 (Burglary).
    YOU ARE HEREBY COMMANDED to search the above-described premises for
    the following property: stolen electronics, tools used for forced entry,
    and any documents linking the suspect to the crime.
    Issued on January 15, 2025 by Judge Maria Garcia, Superior Court of
    Los Angeles County.
    """
    result = extract_entities(sample)
    print(json.dumps(result, indent=2))
