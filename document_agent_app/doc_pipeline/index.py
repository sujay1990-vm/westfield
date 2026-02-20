from typing import List, Dict, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import FAISS

def build_faiss_index(
    pages: List[Dict],
    embedding_model,
    chunk_size: int = 1200,
    chunk_overlap: int = 150,
) -> Tuple[FAISS, List[Document]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    docs: List[Document] = []
    for p in pages:
        page_no = p["page"]
        text = p["text"]
        if not text.strip():
            continue
        chunks = splitter.split_text(text)
        for j, ch in enumerate(chunks):
            docs.append(
                Document(
                    page_content=ch,
                    metadata={"page": page_no, "chunk": j},
                )
            )

    index = FAISS.from_documents(docs, embedding_model)
    return index, docs
