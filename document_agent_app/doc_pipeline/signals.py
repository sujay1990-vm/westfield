from typing import List, Dict, Any, Optional
import re
from langchain.schema import Document

from doc_pipeline.taxonomy import (
    DAMAGE_TYPES,
    LANGUAGE_INTENSITY_TERMS,
    LANGUAGE_INTENSITY_RUBRIC,
)
from doc_pipeline.schemas import SignalsResult, SignalItem

def _regex_evidence_from_pages(pages, terms: List[str], max_hits: int = 6):
    hits = []
    for p in pages:
        text_l = p["text"].lower()
        for t in terms:
            if t in text_l:
                # grab a short surrounding snippet
                idx = text_l.find(t)
                start = max(0, idx - 80)
                end = min(len(p["text"]), idx + len(t) + 120)
                snippet = p["text"][start:end].replace("\n", " ").strip()
                hits.append({"page": p["page"], "quote": snippet})
                if len(hits) >= max_hits:
                    return hits
    return hits

def infer_signals(llm, index, pages, top_k: int = 5) -> Dict[str, Any]:
    signals: List[SignalItem] = []

    # ----------------------------
    # Damage Types (evidence-first)
    # ----------------------------
    # Get evidence excerpts that likely mention damages categories
    dmg_docs: List[Document] = index.similarity_search(
        "damages compensatory punitive treble attorneys fees emotional distress future earnings regulatory penalties statutory",
        k=top_k,
    )
    dmg_context = "\n\n".join([f"[p.{d.metadata.get('page')}] {d.page_content}" for d in dmg_docs])

    dmg_prompt = f"""You are inferring damage types demanded/claimed from a document.
Use ONLY the excerpts. Identify which of these labels are present:
{DAMAGE_TYPES}

Rules:
- Only mark a label present if the document explicitly demands/claims it OR clearly states it.
- Provide one short evidence quote and page number for each label you mark present.
- If not present, do not include it.

Return JSON with:
{{
  "present": [
    {{"label": "<one of the labels>", "page": <int>, "quote": "<short quote>", "confidence": <0..1>}}
  ],
  "notes": "<1-2 sentence overall>"
}}

Excerpts:
{dmg_context}

Return JSON only.
"""
    import json
    dmg_raw = llm.invoke(dmg_prompt).content
    dmg = json.loads(dmg_raw)

    # Aggregate to one signal item summarizing multi-label outcome
    present_labels = [x["label"] for x in dmg.get("present", [])]
    # pick top evidence as representative
    top_ev = dmg["present"][0] if dmg.get("present") else None

    signals.append(SignalItem(
        signal_name="Damage Types",
        value=", ".join(present_labels) if present_labels else "None detected",
        score=None,
        confidence=float(top_ev.get("confidence", 0.6)) if top_ev else 0.6,
        evidence_quote=top_ev.get("quote") if top_ev else None,
        page=int(top_ev.get("page")) if top_ev else None,
        notes=dmg.get("notes"),
    ))

    # ----------------------------
    # Language Intensity (hybrid evidence-first)
    # ----------------------------
    # First: cheap deterministic evidence scan
    term_hits = _regex_evidence_from_pages(pages, LANGUAGE_INTENSITY_TERMS, max_hits=6)

    # Second: retrieve broader “tone” context
    tone_docs: List[Document] = index.similarity_search(
        "willful reckless malicious pattern and practice systemic failure bad faith demand deadline govern yourselves accordingly",
        k=top_k,
    )
    tone_context = "\n\n".join([f"[p.{d.metadata.get('page')}] {d.page_content}" for d in tone_docs])
    hit_context = "\n".join([f"[p.{h['page']}] {h['quote']}" for h in term_hits]) if term_hits else "None found by term scan."

    tone_prompt = f"""You are scoring language intensity in an insurance demand letter / complaint.

Rubric:
{LANGUAGE_INTENSITY_RUBRIC}

Use ONLY the evidence below.
Return JSON:
{{
  "score": <0-4>,
  "tags": [<subset of: {LANGUAGE_INTENSITY_TERMS}>],
  "page": <int or null>,
  "quote": "<best supporting quote or null>",
  "confidence": <0..1>,
  "notes": "<short reasoning>"
}}

Evidence A (term hits):
{hit_context}

Evidence B (retrieved excerpts):
{tone_context}

Return JSON only.
"""
    tone_raw = llm.invoke(tone_prompt).content
    tone = json.loads(tone_raw)

    signals.append(SignalItem(
        signal_name="Language Intensity",
        value="; ".join(tone.get("tags", [])) if tone.get("tags") else "No intensity terms detected",
        score=int(tone.get("score", 1)),
        confidence=float(tone.get("confidence", 0.6)),
        evidence_quote=tone.get("quote"),
        page=tone.get("page"),
        notes=tone.get("notes"),
    ))

    validated = SignalsResult(signals=signals)
    return {"signals": [s.model_dump() for s in validated.signals]}
