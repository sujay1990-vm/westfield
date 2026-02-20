from typing import Dict, Any, List
from doc_pipeline.schemas import ExtractionResult, ExtractionFields
from langchain.schema import Document

def extract_fields(llm, index, top_k: int = 5) -> Dict[str, Any]:
    # Retrieve broad context for extraction
    docs: List[Document] = index.similarity_search(
        "demand letter claim number policy number date of loss injuries treatment damages settlement demand deadline court venue",
        k=top_k,
    )

    context = "\n\n".join([f"[p.{d.metadata.get('page')}] {d.page_content}" for d in docs])

    prompt = f"""You are extracting structured fields from an insurance bodily injury demand letter / complaint.
Use ONLY the provided excerpts. If unknown, set null / empty list.
Return JSON that matches this schema exactly.

Schema fields:
- claimant_name (string or null)
- defendant_name (string or null)
- insured_name (string or null)
- carrier_name (string or null)
- claim_number (string or null)
- policy_number (string or null)
- case_number (string or null)
- venue_court (string or null)
- jurisdiction_state (string or null)
- date_of_loss (string or null)
- loss_location_city_state (string or null)
- accident_type (string or null)
- injuries_list (array of strings)
- surgery_performed (boolean or null)
- surgery_recommended (boolean or null)
- future_treatment_claimed (boolean or null)
- permanency_claimed (boolean or null)
- past_medical (string or null)
- future_medical (string or null)
- past_lost_wages (string or null)
- future_loss_earnings (string or null)
- settlement_demand_amount (string or null)
- plaintiff_attorney_name (string or null)
- plaintiff_firm (string or null)
- demand_date (string or null)
- response_deadline (string or null)

Also include an "evidence" array with up to 8 items: {{page:int, quote:string}}.
Quotes must be short and copied from the excerpts.

Excerpts:
{context}

Return JSON only.
"""
    raw = llm.invoke(prompt).content

    # Robust parse: rely on pydantic validation after JSON load
    import json
    data = json.loads(raw)
    validated = ExtractionResult(
        fields=ExtractionFields(**data["fields"]),
        evidence=data.get("evidence", []),
    )
    return {"fields": validated.fields.model_dump(), "evidence": [e.model_dump() for e in validated.evidence]}
