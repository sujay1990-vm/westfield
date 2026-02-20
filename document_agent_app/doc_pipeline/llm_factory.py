import streamlit as st
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

def _req_secret(key: str) -> str:
    if key not in st.secrets or not str(st.secrets[key]).strip():
        raise RuntimeError(f"Missing Streamlit secret: {key}")
    return str(st.secrets[key]).strip()

def get_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        temperature=0,
        azure_endpoint=_req_secret("AZURE_CHAT_ENDPOINT"),
        openai_api_key=_req_secret("AZURE_CHAT_API_KEY"),
        openai_api_version=_req_secret("AZURE_CHAT_API_VERSION"),
        deployment_name=_req_secret("AZURE_CHAT_DEPLOYMENT"),
        model_name=_req_secret("AZURE_CHAT_MODEL"),
    )

def get_embedding_model() -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(
        azure_endpoint=_req_secret("AZURE_EMBED_ENDPOINT"),
        openai_api_key=_req_secret("AZURE_EMBED_API_KEY"),
        openai_api_version=_req_secret("AZURE_EMBED_API_VERSION"),
        deployment=_req_secret("AZURE_EMBED_DEPLOYMENT"),
        model=_req_secret("AZURE_EMBED_MODEL"),
    )
