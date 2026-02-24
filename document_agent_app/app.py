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

st.title("Raw Text to Analytics Ready")


import html
import pandas as pd
import streamlit as st

def render_wrapped_table(df: pd.DataFrame, max_height_px: int = 650):
    def esc(x):
        return html.escape("" if x is None else str(x))

    rows_html = []
    for _, r in df.iterrows():
        ev = esc(r.get("Evidence", ""))
        notes = esc(r.get("Notes", ""))

        # convert newlines to <br> outside f-string expressions
        ev = ev.replace("\n", "<br>")
        notes = notes.replace("\n", "<br>")

        rows_html.append(
            "<tr>"
            f"<td class='col-type'>{esc(r.get('Signal Type',''))}</td>"
            f"<td class='col-val'>{esc(r.get('Signal Inferred / Value',''))}</td>"
            f"<td class='col-ev'>{ev}</td>"
            f"<td class='col-notes'>{notes}</td>"
            "</tr>"
        )

    table_html = f"""
    <style>
      .sig-wrap {{
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 10px;
        overflow: auto;
        max-height: {max_height_px}px;
      }}
      table.sig {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;  /* forces wrapping within set widths */
        font-size: 0.95rem;
      }}
      table.sig th, table.sig td {{
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding: 10px 12px;
        vertical-align: top;
        white-space: normal;      /* wrap */
        word-break: break-word;   /* break long words */
        overflow-wrap: anywhere;  /* extra safety */
      }}
      table.sig th {{
        position: sticky;
        top: 0;
        background: rgba(20,20,20,0.95);
        z-index: 1;
        text-align: left;
      }}
      /* column widths */
      .col-type  {{ width: 16%; }}
      .col-val   {{ width: 22%; }}
      .col-ev    {{ width: 30%; }}
      .col-notes {{ width: 32%; }}
    </style>

    <div class="sig-wrap">
      <table class="sig">
        <thead>
          <tr>
            <th class="col-type">Signal Type</th>
            <th class="col-val">Signal Inferred / Value</th>
            <th class="col-ev">Evidence</th>
            <th class="col-notes">Notes</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


## Helper code to $ sign

def fmt_currency_int(v):
    """Format an int-like value as $#,###. Returns '—' for empty."""
    if v is None or v == "" or v == []:
        return "—"
    try:
        return f"${int(v):,}"
    except Exception:
        # fall back without crashing if something unexpected comes through
        return str(v)

# with st.sidebar:
#     st.header("Settings")
#     top_k = st.slider("Top-K passages for retrieval", 3, 10, 5, 1)
#     chunk_size = st.slider("Chunk size", 600, 1800, 1200, 100)
#     chunk_overlap = st.slider("Chunk overlap", 50, 400, 150, 10)
#     st.caption("Tip: If answers feel incomplete, increase Top-K or chunk size.")

top_k = 5
chunk_size = 1200
chunk_overlap = 150

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
    # st.subheader("Process document")
    process_btn = st.button("Process", type="primary", disabled=(uploaded is None), key="btn_process_doc")

with colB:
    if st.session_state.get("processed_at"):
        st.subheader("Status")
        st.success(f"Processed: {st.session_state.doc_name}")
        st.caption(f"Pages: {len(st.session_state.pages)}")
        st.caption(f"Last processed: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.processed_at))}")

if process_btn:
    # Reset state for new doc
    st.session_state.pages = None
    st.session_state.index = None
    st.session_state.chunks = None
    st.session_state.extractions = None
    st.session_state.signals = None
    st.session_state.processed_at = None

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
        # IMPORTANT: assign immediately
        st.session_state.index = index
        st.session_state.chunks = chunks

    # HARD GUARD: if index build failed, stop
    if st.session_state.index is None:
        st.error("Index build failed; cannot run extraction/signals.")
        st.stop()

    # Kick off BOTH tasks AFTER index exists
    with st.spinner("Extracting fields..."):
        st.session_state.extractions = extract_fields(
            llm=llm,
            index=st.session_state.index,
            top_k=top_k,
        )

    with st.spinner("Deriving insights..."):
        st.session_state.signals = infer_signals(
            llm=llm,
            index=st.session_state.index,
            pages=st.session_state.pages,
            top_k=top_k,
        )

    st.session_state.processed_at = time.time()
    st.success("Done. Review results in the tabs below.")

st.divider()

tab_extract, tab_signals = st.tabs(["Extract Fields", "Derived Insights"])

processed = bool(st.session_state.get("pages")) and (
    st.session_state.get("extractions") is not None or st.session_state.get("signals") is not None
)

if st.session_state.get("index") is None:
    st.info("Upload a document and click **Process** to enable Field Extraction and Derive insights.")
    st.stop()

# -------------------------
# Q&A
# -------------------------
# if view == "Q&A (with citations)":
#     st.subheader("Ask questions about this document")

#     with st.form("qa_form", clear_on_submit=False):
#         q = st.text_input(
#             "Question",
#             placeholder="e.g., What is the settlement demand amount? What injuries are alleged?",
#             key="qa_question",
#         )
#         ask = st.form_submit_button("Answer", type="primary")

#     if ask:
#         if not q.strip():
#             st.warning("Type a question first.")
#         else:
#             with st.spinner("Retrieving evidence + generating answer..."):
#                 answer, citations = answer_question_with_citations(
#                     llm=llm,
#                     index=st.session_state.index,
#                     question=q,
#                     top_k=top_k,
#                 )
#             st.session_state.qa_history.append(
#                 {"question": q, "answer": answer, "citations": citations}
#             )

#     if st.session_state.qa_history:
#         st.markdown("### History")
#         for item in reversed(st.session_state.qa_history[-10:]):
#             st.markdown(f"**Q:** {item['question']}")
#             st.markdown(f"**A:** {item['answer']}")
#             if item["citations"]:
#                 st.caption("Citations: " + "; ".join(item["citations"]))
#             st.divider()

# # -------------------------
# # Summary
# # -------------------------
# elif view == "Summarize":
#     st.subheader("Generate a clean summary")
#     if st.session_state.summary is None:
#         if st.button("Create summary", type="primary"):
#             with st.spinner("Summarizing document..."):
#                 summary_text = summarize_document(
#                     llm=llm,
#                     pages=st.session_state.pages,
#                 )
#             st.session_state.summary = summary_text

#     if st.session_state.summary:
#         st.text_area(
#                 "Summary",
#                 value=st.session_state.summary,
#                 height=650,          # increase as you like (e.g., 600–900)
#                 label_visibility="collapsed",
#             )
#         st.download_button(
#             "Download summary.txt",
#             data=to_txt_bytes(st.session_state.summary),
#             file_name="summary.txt",
#             mime="text/plain",
#         )

# -------------------------
# Extraction
# -------------------------
with tab_extract:
    if not processed:
        st.stop()

    fields = st.session_state.extractions["fields"] if st.session_state.extractions else {}
    st.markdown("### Extracted fields")

    pretty_rows = []
    CURRENCY_FIELDS = {
        "medical_expenses_till_date", "projected_medical_cost",
        "lost_wages", "future_loss_earnings", "settlement_demand_amount"
    }

    for k, v in fields.items():
        if v is None or v == "" or v == []:
            continue

        if k in CURRENCY_FIELDS:
            v_disp = fmt_currency_int(v)
        elif isinstance(v, list):
            v_disp = ", ".join([str(x) for x in v])
        else:
            v_disp = str(v)

        pretty_rows.append({"Field": k.replace("_", " ").title(), "Value": v_disp})

    if pretty_rows:
        df_view = pd.DataFrame(pretty_rows)
        st.data_editor(
            df_view,
            use_container_width=True,
            hide_index=True,
            height=650,
            disabled=True,
            column_config={
                "Field": st.column_config.TextColumn("Field", width="small"),
                "Value": st.column_config.TextColumn("Value", width="large"),
            },
        )
    else:
        st.info("No fields found.")

    with st.expander("Show raw JSON"):
        st.json(fields)

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
with tab_signals:
    if not processed:
        st.stop()

    sig_obj = st.session_state.signals or {}
    signals = sig_obj.get("signals", []) or []

    st.markdown("### Derived Insights")

    rows = []
    for s in signals:
        if not isinstance(s, dict):
            continue

        name = (s.get("signal_name") or "").strip()
        value = (s.get("value") or "").strip()
        notes = (s.get("notes") or "").strip()
        quote = (s.get("evidence_quote") or "").strip()

        # Skip empty items -> eliminates empty rows
        if not (name or value or notes or quote):
            continue

        meta = []
        if s.get("page") is not None:
            meta.append(f"p.{s['page']}")
        if s.get("score") is not None:
            meta.append(f"score={s['score']}")
        if s.get("confidence") is not None:
            c = s["confidence"]
            meta.append(f"conf={c:.2f}" if isinstance(c, (int, float)) else f"conf={c}")

        evidence = quote
        if meta:
            evidence = (evidence + "\n" if evidence else "") + f"({ ' | '.join(meta) })"

        rows.append({
            "Signal Type": name,
            "Signal Inferred / Value": value,
            "Evidence": evidence,
            "Notes": notes,
        })

    df_sig_view = pd.DataFrame(rows)

    if df_sig_view.empty:
        st.info("No signals found.")
        st.stop()
    
    render_wrapped_table(df_sig_view, max_height_px=650)

    # # dynamic height so you don't see "empty rows" below the data
    # n = len(df_sig_view)
    # ROW_PX = 30       # approx row height
    # HEADER_PX = 38    # header height
    # PAD_PX = 12
    # height_px = min(650, HEADER_PX + PAD_PX + (n + 1) * ROW_PX)  # +1 gives a bit of breathing room
    # height_px = max(200, height_px)  # don't get too tiny

    # st.data_editor(
    # df_sig_view,
    # use_container_width=True,
    # hide_index=True,
    # height=height_px,
    # disabled=True,
    # column_config={
    #     "Signal Type": st.column_config.TextColumn("Signal Type", width="small"),
    #     "Signal Inferred / Value": st.column_config.TextColumn("Signal Inferred / Value", width="large"),
    #     "Evidence": st.column_config.TextColumn("Evidence", width="large"),
    #     "Notes": st.column_config.TextColumn("Notes", width="large"),
    #         },
    #     )

    st.download_button(
        "Download signals.csv",
        data=to_csv_bytes(df_sig_view),
        file_name="signals.csv",
        mime="text/csv",
    )