"""
app.py
Streamlit frontend for the Legal Document Triage Assistant.
Upload PDFs → extract text → classify → summarize → extract entities → save to Supabase.
Supports single and batch uploads, clickable history, and PDF/CSV export.
"""

import streamlit as st
import pandas as pd
from pipeline.pdf_reader import extract_text_from_pdf
from pipeline.classifier import classify_document
from pipeline.extractor import extract_entities
from pipeline.summarizer import summarize_document
from db.supabase_client import save_triage_result, get_triage_history
from export.pdf_report import generate_triage_report
from export.csv_export import export_history_as_csv

# --- Page Config ---
st.set_page_config(page_title="Legal Document Triage", page_icon="?", layout="wide")
st.title("Legal Document Triage Assistant")
st.caption("Upload legal documents (PDF) to classify them and extract key entities.")

# --- Sidebar: Clickable Triage History ---
with st.sidebar:
    st.header("Recent Triage History")
    history = get_triage_history(10)
    if history:
        for i, row in enumerate(history):
            label = row["classification"].replace("_", " ").title()
            if st.button(
                f"{row['filename']} — {label} ({row['confidence']:.0%})",
                key=f"history_{i}",
                use_container_width=True,
            ):
                st.session_state["selected_history"] = row
                st.session_state["processed_key"] = None  # Clear upload results

        st.divider()

        # CSV export for full history
        csv_str = export_history_as_csv(history)
        st.download_button(
            label="Export History as CSV",
            data=csv_str,
            file_name="triage_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.markdown("_No results yet._")


def display_single_result(classification, summary, entities):
    """Displays classification, summary, and entities for a single document."""
    # Classification
    if classification.get("classification") == "error":
        st.error(f"Classification failed: {classification['reasoning']}")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Classification")
            st.metric(label="Document Type", value=classification["classification"].replace("_", " ").title())
            st.metric(label="Confidence", value=f"{classification['confidence']:.0%}")
        with col2:
            st.subheader("Reasoning")
            st.info(classification.get("reasoning", "N/A"))

    st.divider()

    # Summary
    st.subheader("Document Summary")
    if isinstance(summary, dict) and summary.get("error"):
        st.error(f"Summarization failed: {summary['error']}")
    else:
        summary_text = summary.get("summary", summary) if isinstance(summary, dict) else summary
        st.markdown(summary_text or "_No summary available._")

    st.divider()

    # Entities
    if isinstance(entities, dict) and entities.get("error"):
        st.error(f"Entity extraction failed: {entities['error']}")
    else:
        st.subheader("Extracted Entities")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Persons**")
            persons = entities.get("persons", []) if isinstance(entities, dict) else []
            if persons:
                for person in persons:
                    st.markdown(f"- {person}")
            else:
                st.markdown("_None found_")

            st.markdown("**Dates**")
            dates = entities.get("dates", []) if isinstance(entities, dict) else []
            if dates:
                for date in dates:
                    st.markdown(f"- {date}")
            else:
                st.markdown("_None found_")

        with col2:
            st.markdown("**Locations**")
            locations = entities.get("locations", []) if isinstance(entities, dict) else []
            if locations:
                for loc in locations:
                    st.markdown(f"- {loc}")
            else:
                st.markdown("_None found_")

            st.markdown("**Offenses**")
            offenses = entities.get("offenses", []) if isinstance(entities, dict) else []
            if offenses:
                for offense in offenses:
                    st.markdown(f"- {offense}")
            else:
                st.markdown("_None found_")


def display_pdf_download(filename, classification, entities, summary_text, key_suffix=""):
    """Shows a PDF report download button."""
    pdf_bytes = generate_triage_report(
        filename=filename,
        classification=classification,
        entities=entities,
        summary=summary_text,
    )
    if pdf_bytes:
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"{filename}_report.pdf",
            mime="application/pdf",
            key=f"pdf_{key_suffix or filename}",
        )


def process_document(uploaded_file):
    """Runs the full pipeline on a single uploaded file. Returns a result dict."""
    text = extract_text_from_pdf(uploaded_file)
    if not text:
        return {"filename": uploaded_file.name, "status": "failed", "error": "No text extracted"}

    classification = classify_document(text)
    summary = summarize_document(text)
    entities = extract_entities(text)

    saved = save_triage_result(
        filename=uploaded_file.name,
        classification=classification,
        entities=entities,
        raw_text=text,
        summary=summary.get("summary", ""),
    )

    return {
        "filename": uploaded_file.name,
        "status": "success",
        "text": text,
        "classification": classification,
        "summary": summary,
        "entities": entities,
        "saved": saved,
    }


# --- Display History Item (when clicked from sidebar) ---
selected = st.session_state.get("selected_history")

# --- File Upload (supports multiple files) ---
uploaded_files = st.file_uploader(
    "Upload PDF documents",
    type=["pdf"],
    accept_multiple_files=True,
)

# --- Process Uploaded Files ---
if uploaded_files:
    # Clear history selection when new files are uploaded
    st.session_state["selected_history"] = None
    selected = None

    file_key = "_".join(f.name for f in uploaded_files)
    if st.session_state.get("processed_key") != file_key:
        results = []
        total = len(uploaded_files)
        progress = st.progress(0, text="Starting...")

        for i, uploaded_file in enumerate(uploaded_files):
            progress.progress(
                i / total,
                text=f"Processing {uploaded_file.name} ({i + 1}/{total})...",
            )
            result = process_document(uploaded_file)
            results.append(result)

        progress.progress(1.0, text=f"All {total} document(s) processed.")
        st.session_state["processed_key"] = file_key
        st.session_state["results"] = results
    else:
        results = st.session_state["results"]

    # --- Batch Summary Table (only for multiple files) ---
    if len(results) > 1:
        st.divider()
        st.subheader("Batch Results Summary")

        table_data = []
        for r in results:
            if r["status"] == "success":
                table_data.append({
                    "Filename": r["filename"],
                    "Type": r["classification"].get("classification", "error").replace("_", " ").title(),
                    "Confidence": f"{r['classification'].get('confidence', 0):.0%}",
                    "Persons": len(r["entities"].get("persons", [])),
                    "Locations": len(r["entities"].get("locations", [])),
                    "Offenses": len(r["entities"].get("offenses", [])),
                })
            else:
                table_data.append({
                    "Filename": r["filename"],
                    "Type": "FAILED",
                    "Confidence": "-",
                    "Persons": "-",
                    "Locations": "-",
                    "Offenses": "-",
                })

        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    # --- Detailed Results ---
    for idx, r in enumerate(results):
        if r["status"] == "failed":
            if len(results) > 1:
                with st.expander(f"{r['filename']} — FAILED"):
                    st.error(r["error"])
            else:
                st.error(f"Could not extract text from {r['filename']}. It may be a scanned image.")
            continue

        summary_text = r["summary"].get("summary", "") if isinstance(r["summary"], dict) else r["summary"]

        if len(results) > 1:
            with st.expander(f"{r['filename']} — {r['classification'].get('classification', 'error').replace('_', ' ').title()}"):
                if st.toggle("Show extracted text", key=f"text_{r['filename']}"):
                    st.text(r["text"])
                display_single_result(r["classification"], r["summary"], r["entities"])
                display_pdf_download(r["filename"], r["classification"], r["entities"], summary_text, key_suffix=f"batch_{idx}")
                if r["saved"].get("error"):
                    st.warning(f"Failed to save: {r['saved']['error']}")
                else:
                    st.success("Saved to database.")
        else:
            with st.expander("Extracted Text", expanded=False):
                st.text(r["text"])
            st.divider()
            display_single_result(r["classification"], r["summary"], r["entities"])
            display_pdf_download(r["filename"], r["classification"], r["entities"], summary_text, key_suffix=f"single_{idx}")
            if r["saved"].get("error"):
                st.warning(f"Results displayed but failed to save: {r['saved']['error']}")
            else:
                st.success("Results saved to database.")

# --- Show Selected History Item ---
elif selected:
    st.divider()
    st.subheader(f"Past Result: {selected['filename']}")

    # Build dicts from the stored Supabase row
    classification = {
        "classification": selected.get("classification", ""),
        "confidence": selected.get("confidence", 0.0),
        "reasoning": selected.get("reasoning", ""),
    }
    entities = {
        "persons": selected.get("persons", []),
        "dates": selected.get("dates", []),
        "locations": selected.get("locations", []),
        "offenses": selected.get("offenses", []),
    }
    summary_text = selected.get("summary", "")

    display_single_result(classification, {"summary": summary_text}, entities)

    # PDF download for history item
    display_pdf_download(selected["filename"], classification, entities, summary_text, key_suffix="history")

    st.caption(f"Processed on: {selected.get('created_at', 'N/A')}")
