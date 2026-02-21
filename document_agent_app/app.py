import io
import time
import pandas as pd
import streamlit as st

from doc_pipeline.llm_factory import get_llm, get_embedding_model
from doc_pipeline.pdf_parse import parse_pdf_to_pages
from doc_pipeline.index import build_faiss_index
from doc_pipeline.rag import answer_question_with_citations, summarize_document
from doc_pipeline.extract import extract_fields
from doc_pipeline.signals import infer_signals
from doc_pipeline.export import (
    to_csv_bytes,
    to_txt_bytes,
)

st.set_page_config(page_title="Insurance Document Agent", layout="wide")

st.title("Insurance Document Agent (PDF → Q&A / Summary / Extraction / Signals)")

with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Top-K passages for retrieval", 3, 10, 5, 1)
    chunk_size = st.slider("Chunk size", 600, 1800, 1200, 100)
    chunk_overlap = st.slider("Chunk overlap", 50, 400, 150, 10)
    st.caption("Tip: If answers feel incomplete, increase Top-K or chunk size.")

# Session init
for k in [
    "doc_name", "pages", "index", "chunks",
    "summary", "extractions", "signals", "qa_history",
    "processed_at"
]:
    st.session_state.setdefault(k, None)

st.session_state.setdefault("qa_history", [])

# Upload
uploaded = st.file_uploader("Upload a PDF (BI demand letter, complaint, report, etc.)", type=["pdf"])

colA, colB = st.columns([1, 1], gap="large")

with colA:
    st.subheader("1) Process document")
    process_btn = st.button("Process PDF", type="primary", disabled=(uploaded is None))

with colB:
    if st.session_state.processed_at:
        st.subheader("Status")
        st.success(f"Processed: {st.session_state.doc_name}")
        st.caption(f"Pages: {len(st.session_state.pages)} | Chunks: {len(st.session_state.chunks)}")
        st.caption(f"Last processed: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.processed_at))}")

if process_btn:
    # Reset state for new doc
    st.session_state.pages = None
    st.session_state.index = None
    st.session_state.chunks = None
    st.session_state.summary = None
    st.session_state.extractions = None
    st.session_state.signals = None
    st.session_state.qa_history = []

    llm = get_llm()
    emb = get_embedding_model()

    pdf_bytes = uploaded.read()
    st.session_state.doc_name = uploaded.name

    with st.spinner("Parsing PDF into per-page text..."):
        pages = parse_pdf_to_pages(io.BytesIO(pdf_bytes))
        st.session_state.pages = pages

    with st.spinner("Chunking + embedding + building per-document index..."):
        index, chunks = build_faiss_index(
            pages=pages,
            embedding_model=emb,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        st.session_state.index = index
        st.session_state.chunks = chunks

    st.session_state.processed_at = time.time()
    st.success("Document processed. Use the tabs below.")

st.divider()

if not st.session_state.index:
    st.info("Upload a PDF and click **Process PDF** to enable Q&A, Summary, Extraction, and Signals.")
    st.stop()

llm = get_llm()

# --- Controlled navigation (doesn't jump on rerun) ---
if "active_view" not in st.session_state:
    st.session_state.active_view = "Q&A (with citations)"

view = st.radio(
    "Mode",
    ["Q&A (with citations)", "Summarize", "Extract Fields", "Infer Signals"],
    horizontal=True,
    key="active_view",
    label_visibility="collapsed",
)

# -------------------------
# Q&A
# -------------------------
if view == "Q&A (with citations)":
    st.subheader("Ask questions about this document")

    with st.form("qa_form", clear_on_submit=False):
        q = st.text_input(
            "Question",
            placeholder="e.g., What is the settlement demand amount? What injuries are alleged?",
            key="qa_question",
        )
        ask = st.form_submit_button("Answer", type="primary")

    if ask:
        if not q.strip():
            st.warning("Type a question first.")
        else:
            with st.spinner("Retrieving evidence + generating answer..."):
                answer, citations = answer_question_with_citations(
                    llm=llm,
                    index=st.session_state.index,
                    question=q,
                    top_k=top_k,
                )
            st.session_state.qa_history.append(
                {"question": q, "answer": answer, "citations": citations}
            )

    if st.session_state.qa_history:
        st.markdown("### History")
        for item in reversed(st.session_state.qa_history[-10:]):
            st.markdown(f"**Q:** {item['question']}")
            st.markdown(f"**A:** {item['answer']}")
            if item["citations"]:
                st.caption("Citations: " + "; ".join(item["citations"]))
            st.divider()

# -------------------------
# Summary
# -------------------------
elif view == "Summarize":
    st.subheader("Generate a clean summary")
    if st.session_state.summary is None:
        if st.button("Create summary", type="primary"):
            with st.spinner("Summarizing document..."):
                summary_text = summarize_document(
                    llm=llm,
                    pages=st.session_state.pages,
                )
            st.session_state.summary = summary_text

    if st.session_state.summary:
        st.text_area(
                "Summary",
                value=st.session_state.summary,
                height=650,          # increase as you like (e.g., 600–900)
                label_visibility="collapsed",
            )
        st.download_button(
            "Download summary.txt",
            data=to_txt_bytes(st.session_state.summary),
            file_name="summary.txt",
            mime="text/plain",
        )

# -------------------------
# Extraction
# -------------------------
elif view == "Extract Fields":
    st.subheader("Field extraction (strict schema, evidence-backed)")

    if st.session_state.extractions is None:
        if st.button("Extract fields", type="primary"):
            with st.spinner("Extracting fields..."):
                result = extract_fields(
                    llm=llm,
                    index=st.session_state.index,
                    top_k=top_k,
                )
            st.session_state.extractions = result

    if st.session_state.extractions:
        fields = st.session_state.extractions["fields"]
        evidence = st.session_state.extractions.get("evidence", [])

        st.markdown("### Extracted fields")
        st.json(fields)

        if evidence:
            st.markdown("### Evidence (high-signal quotes)")
            for ev in evidence[:10]:
                st.markdown(f"- **p.{ev['page']}** — {ev['quote']}")

        df = pd.DataFrame([fields])
        st.download_button(
            "Download extractions.csv",
            data=to_csv_bytes(df),
            file_name="extractions.csv",
            mime="text/csv",
        )

# -------------------------
# Signals
# -------------------------
elif view == "Infer Signals":
    st.subheader("Signal inference (evidence-first taxonomy)")

    # Keep user on this view after click (important)
    if st.session_state.signals is None:
        if st.button("Infer signals", type="primary"):
            with st.spinner("Inferring signals..."):
                sig = infer_signals(
                    llm=llm,
                    index=st.session_state.index,
                    pages=st.session_state.pages,
                    top_k=top_k,
                )
            st.session_state.signals = sig

    if st.session_state.signals:
        st.markdown("### Signals")
        st.json(st.session_state.signals)

        rows = []
        for s in st.session_state.signals["signals"]:
            rows.append({
                "signal_name": s["signal_name"],
                "value": s["value"],
                "score": s.get("score"),
                "confidence": s.get("confidence"),
                "evidence_quote": s.get("evidence_quote"),
                "page": s.get("page"),
                "notes": s.get("notes"),
            })
        df_sig = pd.DataFrame(rows)

        st.download_button(
            "Download signals.csv",
            data=to_csv_bytes(df_sig),
            file_name="signals.csv",
            mime="text/csv",
        )