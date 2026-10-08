import asyncio

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_ollama import ChatOllama

from ...config import settings
from . import vector_store

RAG_PROMPT = ChatPromptTemplate.from_template(
    """Sos el asistente operativo de Donata, un negocio de alfombras y textiles.
Respondé la pregunta del usuario usando EXCLUSIVAMENTE el contexto provisto.
Si la respuesta no está en el contexto, respondé que no tenés esa información.
No inventes datos ni precios. Respondé en español, de forma breve y clara.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""
)


def format_docs(documents: list[Document]) -> str:
    return "\n\n".join(document.page_content for document in documents)


def get_llm(temperature: float | None = None) -> ChatOllama:
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.llm_temperature if temperature is None else temperature,
        num_ctx=settings.ollama_num_ctx,
    )


def build_rag_chain() -> Runnable:
    retriever = vector_store.get_kb_store().as_retriever(search_kwargs={"k": settings.rag_top_k})
    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | get_llm(temperature=0)
        | StrOutputParser()
    )


def answer_question(question: str) -> str:
    return build_rag_chain().invoke(question)


async def answer_question_async(question: str) -> str:
    return await asyncio.to_thread(answer_question, question)


def consultar_documentacion(pregunta: str) -> str:
    documents = vector_store.search_knowledge_base(pregunta)
    if not documents:
        return "No encontré información en el manual operativo para esa consulta."
    return answer_question(pregunta)
