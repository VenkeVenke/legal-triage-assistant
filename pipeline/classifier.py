"""
classifier.py
Classifies legal document text into one of five categories
using Ollama (Llama 3): warrant, complaint, police_report, subpoena, other.
"""

import json
from pathlib import Path
import requests

# Load the prompt template once at module level
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "triage_prompt.txt"
PROMPT_TEMPLATE = PROMPT_PATH.read_text()

OLLAMA_URL = "http://localhost:11434/api/chat"
VALID_CATEGORIES = {"warrant", "complaint", "police_report", "subpoena", "other"}


def classify_document(text: str, model: str = "llama3") -> dict:
    """
    Sends document text to Ollama (Llama 3) and returns a classification result.

    Args:
        text: The extracted text content of the legal document.
        model: The Ollama model to use (default: llama3).

    Returns:
        A dict with keys: classification, confidence, reasoning.
        On failure, returns a dict with classification="error" and details.
    """
    prompt = PROMPT_TEMPLATE.replace("{document_text}", text)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",  # Forces Ollama to return clean JSON
                "options": {"temperature": 0.0},
            },
            timeout=120,
        )
        response.raise_for_status()

        raw = response.json()["message"]["content"].strip()
        result = json.loads(raw)

        # Validate the response structure
        if result.get("classification") not in VALID_CATEGORIES:
            return {
                "classification": "error",
                "confidence": 0.0,
                "reasoning": f"Invalid category returned: {result.get('classification')}",
            }

        return result

    except json.JSONDecodeError:
        return {
            "classification": "error",
            "confidence": 0.0,
            "reasoning": f"Failed to parse model response as JSON: {raw[:200]}",
        }
    except requests.ConnectionError:
        return {
            "classification": "error",
            "confidence": 0.0,
            "reasoning": "Cannot connect to Ollama. Is it running? (ollama serve)",
        }
    except Exception as e:
        return {
            "classification": "error",
            "confidence": 0.0,
            "reasoning": f"API call failed: {str(e)}",
        }


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
    """
    result = classify_document(sample)
    print(json.dumps(result, indent=2))
