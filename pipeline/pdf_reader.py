"""
pdf_reader.py
Extracts text from PDF files using pdfplumber.
Handles single and multi-page documents.
"""

import pdfplumber


def extract_text_from_pdf(file) -> str:
    """
    Extracts all text from a PDF file.

    Args:
        file: A file path (str) or file-like object (e.g. Streamlit UploadedFile).

    Returns:
        The full extracted text as a single string.
        Returns an empty string if no text could be extracted.
    """
    text_pages = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_pages.append(page_text)

    return "\n\n".join(text_pages)


# Quick test when running this file directly
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_reader.py <path_to_pdf>")
        sys.exit(1)

    path = sys.argv[1]
    text = extract_text_from_pdf(path)

    if text:
        print(f"Extracted {len(text)} characters from {path}\n")
        print(text[:500])
        if len(text) > 500:
            print(f"\n... ({len(text) - 500} more characters)")
    else:
        print(f"No text extracted from {path}")
