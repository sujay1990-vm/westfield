from typing import List, Dict, Any, Optional
import re
from langchain.schema import Document
import json

from doc_pipeline.taxonomy import (
    DAMAGE_TYPES,
    LANGUAGE_INTENSITY_TERMS,
    LANGUAGE_INTENSITY_RUBRIC,
)
from doc_pipeline.schemas import SignalsResult, SignalItem

from doc_pipeline.taxonomy import SIGNALS_V1

def _find_keyword_hits(pages, keywords: list, max_hits: int = 6):
    hits = []
    kws = [k.lower() for k in keywords]
    for p in pages:
        txt = p["text"]
        low = txt.lower()
        for k in kws:
            if k in low:
                idx = low.find(k)
                start = max(0, idx - 90)
                end = min(len(txt), idx + len(k) + 140)
                snippet = txt[start:end].replace("\n", " ").strip()
                hits.append({"page": p["page"], "quote": snippet, "keyword": k})
                if len(hits) >= max_hits:
                    return hits
    return hits

def _collect_all_keywords(signal_def: dict) -> list:
    # flatten all category keywords into one list
    out = []
    for _, kws in signal_def.get("keywords", {}).items():
        out.extend(kws)
    return out


def _extract_json_object(text: str) -> str:
    if not text:
        raise ValueError("Empty LLM response")

    cleaned = str(text).strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # fast path
    try:
        json.loads(cleaned)
        return cleaned
    except Exception:
        pass

    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found. Response starts: {cleaned[:200]!r}")

    depth = 0
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = cleaned[start:i+1]
                json.loads(candidate)
                return candidate

    raise ValueError("Could not extract JSON object from response.")


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

def _infer_generic_signal(llm, index, pages, signal_name: str, top_k: int = 5):
    sig = SIGNALS_V1[signal_name]

    # 1) retrieve excerpts likely relevant
    docs = index.similarity_search(sig["query"], k=top_k)
    retrieved = "\n\n".join([f"[p.{d.metadata.get('page')}] {d.page_content}" for d in docs])

    # 2) keyword scan across whole doc for “hard evidence”
    hits = _find_keyword_hits(pages, _collect_all_keywords(sig), max_hits=8)
    hit_text = "\n".join([f"[p.{h['page']}] {h['quote']}" for h in hits]) if hits else "None found by keyword scan."

    # 3) ask LLM to choose categories strictly from evidence
    cats = sig["categories"]
    interpretation = sig.get("interpretation", {})

    if sig["type"] == "categorical_multi":
        schema_text = """Return JSON:
{
  "selected": [{"category": "<one of the categories>", "page": <int>, "quote": "<short quote>", "confidence": <0..1>}],
  "notes": "<short note>"
}"""
    else:
        schema_text = """Return JSON:
{
  "selected": {"category": "<one of the categories>", "page": <int|null>, "quote": "<short quote|null>", "confidence": <0..1>},
  "notes": "<short note>"
}"""

    prompt = f"""You are inferring the signal: {signal_name}

STRICT OUTPUT RULES:
- Output MUST be valid JSON only (no markdown).
- Choose ONLY from these categories: {cats}
- Use ONLY the evidence below. If nothing supports a category, choose the most conservative option.
- Provide short quote + page for each selection.

Evidence A (keyword hits):
{hit_text}

Evidence B (retrieved excerpts):
{retrieved}

{schema_text}
Return JSON only.
"""
    raw = str(llm.invoke(prompt).content)
    data = json.loads(_extract_json_object(raw))

    return data, interpretation



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
    dmg_raw = str(llm.invoke(dmg_prompt).content)
    dmg = json.loads(_extract_json_object(dmg_raw))


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
    tone_raw = str(llm.invoke(tone_prompt).content)
    tone = json.loads(_extract_json_object(tone_raw))


    signals.append(SignalItem(
        signal_name="Language Intensity",
        value="; ".join(tone.get("tags", [])) if tone.get("tags") else "No intensity terms detected",
        score=int(tone.get("score", 1)),
        confidence=float(tone.get("confidence", 0.6)),
        evidence_quote=tone.get("quote"),
        page=tone.get("page"),
        notes=tone.get("notes"),
    ))

    # --- Additional signals (v1 packs) ---
    for name in SIGNALS_V1.keys():
        out, interp = _infer_generic_signal(llm, index, pages, name, top_k=top_k)

        if SIGNALS_V1[name]["type"] == "categorical_multi":
            selected = out.get("selected", [])
            if selected:
                # pick first as representative evidence
                rep = selected[0]
                value = ", ".join([s["category"] for s in selected])
                notes = out.get("notes")
                signals.append(SignalItem(
                    signal_name=name,
                    value=value,
                    score=None,
                    confidence=float(rep.get("confidence", 0.6)),
                    evidence_quote=rep.get("quote"),
                    page=int(rep.get("page")) if rep.get("page") else None,
                    notes=notes
                ))
            else:
                signals.append(SignalItem(signal_name=name, value="None detected", confidence=0.5, notes=out.get("notes")))
        else:
            sel = out.get("selected", {})
            cat = sel.get("category", "No Liability Facts")
            signals.append(SignalItem(
                signal_name=name,
                value=cat,
                confidence=float(sel.get("confidence", 0.6)),
                evidence_quote=sel.get("quote"),
                page=sel.get("page"),
                notes=out.get("notes"),
            ))


    validated = SignalsResult(signals=signals)
    return {"signals": [s.model_dump() for s in validated.signals]}
