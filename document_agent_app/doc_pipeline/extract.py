import json
import re
from typing import Dict, Any, List
from langchain.schema import Document

from doc_pipeline.schemas import ExtractionResult, ExtractionFields


def _to_bool(v: Any):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    if s in {"true", "yes", "y", "1"}:
        return True
    if s in {"false", "no", "n", "0"}:
        return False
    # If model put text like "ACDF at C5–C6", interpret as True (it found evidence)
    # But only for surgery/treatment flags; caller controls usage.
    return None

def _to_number(v: Any):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v)
    # Extract first numeric token, allow commas and $.
    m = re.search(r"[-+]?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)", s)
    if not m:
        return None
    num = m.group(1).replace(",", "")
    try:
        return float(num)
    except:
        return None

def normalize_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(fields)

    # booleans
    for k in ["surgery_performed", "surgery_recommended", "future_treatment_claimed", "permanency_claimed"]:
        out[k] = _to_bool(out.get(k))

    # numeric
    for k in ["past_medical", "future_medical", "past_lost_wages", "future_loss_earnings", "settlement_demand_amount"]:
        out[k] = _to_number(out.get(k))

    return out


def _extract_json_object(text: str) -> str:
    """
    Extract the first valid JSON object from a string.
    Handles code fences and leading/trailing commentary.
    """
    if not text:
        raise ValueError("Empty LLM response")

    # Strip code fences if present
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # Fast path: already valid JSON
    try:
        json.loads(cleaned)
        return cleaned
    except Exception:
        pass

    # Find first {...} block using a crude but effective brace scan
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in response. Response starts with: {cleaned[:120]!r}")

    depth = 0
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = cleaned[start : i + 1]
                # Validate
                json.loads(candidate)
                return candidate

    raise ValueError("Could not extract a complete JSON object from response.")


def extract_fields(llm, index, top_k: int = 5) -> Dict[str, Any]:
    # Retrieve broad context for extraction
    docs: List[Document] = index.similarity_search(
        "claimant plaintiff defendant insured carrier claim number policy number date of loss injuries treatment damages settlement demand deadline court venue",
        k=top_k,
    )

    context = "\n\n".join([f"[p.{d.metadata.get('page')}] {d.page_content}" for d in docs])

    prompt = f"""You are extracting structured fields from an insurance demand letter / complaint.

STRICT OUTPUT RULES:
- Output MUST be valid JSON.
- Output MUST be a single JSON object.
- Do NOT include markdown, code fences, or extra commentary.

If a field is unknown, use null (or [] for injuries_list).

Return JSON with exactly this shape:
{{
  "fields": {{
    "claimant_name": null,
    "defendant_name": null,
    "insured_name": null,
    "carrier_name": null,
    "claim_number": null,
    "policy_number": null,
    "case_number": null,
    "venue_court": null,
    "jurisdiction_state": null,
    "date_of_loss": null,
    "loss_location_city_state": null,
    "accident_type": null,
    "injuries_list": [],
    "surgery_performed": null,
    "surgery_recommended": null,
    "future_treatment_claimed": null,
    "permanency_claimed": null,
    "past_medical": null,
    "future_medical": null,
    "past_lost_wages": null,
    "future_loss_earnings": null,
    "settlement_demand_amount": null,
    "plaintiff_attorney_name": null,
    "plaintiff_firm": null,
    "demand_date": null,
    "response_deadline": null
  }},
  "evidence": [
    {{"page": 1, "quote": "short quote copied from excerpts"}}
  ]
}}

Excerpts (use ONLY these):
{context}
"""
    resp = llm.invoke(prompt)
    raw = str(resp.content).strip()

    json_str = _extract_json_object(raw)
    data = json.loads(json_str)

    # Validate with pydantic (strict-ish)
    validated = ExtractionResult(
        fields=ExtractionFields(**data["fields"]),
        evidence=data.get("evidence", []),
    )

    return {
        "fields": validated.fields.model_dump(),
        "evidence": [e.model_dump() for e in validated.evidence],
    }
