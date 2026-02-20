from typing import List, Tuple
from langchain.schema import Document

def _format_citations(docs: List[Document]) -> List[str]:
    # Unique pages in order of appearance
    pages = []
    for d in docs:
        p = d.metadata.get("page")
        if p and p not in pages:
            pages.append(p)
    return [f"p.{p}" for p in pages]

def answer_question_with_citations(llm, index, question: str, top_k: int = 5) -> Tuple[str, List[str]]:
    docs = index.similarity_search(question, k=top_k)
    citations = _format_citations(docs)

    context = "\n\n".join([f"[p.{d.metadata.get('page')}] {d.page_content}" for d in docs])

    prompt = f"""You are an insurance document analyst.
Answer the user's question using ONLY the provided excerpts.
If the answer is not in the excerpts, say you cannot find it in the document.

Question: {question}

Excerpts:
{context}

Answer:
"""
    resp = llm.invoke(prompt)
    return str(resp.content).strip(), citations

def summarize_document(llm, pages) -> str:
    # For v1: simple hierarchical summarization (page batches)
    texts = [p["text"] for p in pages if p["text"].strip()]
    if not texts:
        return "No readable text found in the document."

    # batch to reduce token load
    batch_size = 4
    partials = []
    for i in range(0, len(texts), batch_size):
        chunk = "\n\n".join(texts[i:i+batch_size])
        prompt = f"""Summarize the following document text into:
1) One-paragraph overview
2) Key facts (bullets)
3) Damages / demand numbers (bullets)
4) Medical / injury highlights (bullets)

Text:
{chunk}
"""
        resp = llm.invoke(prompt)
        partials.append(str(resp.content).strip())

    if len(partials) == 1:
        return partials[0]

    combine_prompt = f"""Combine the partial summaries into ONE clean final summary.
Remove duplicates. Keep it concise but complete.

Partial summaries:
{chr(10).join(partials)}
"""
    final = llm.invoke(combine_prompt)
    return str(final.content).strip()
