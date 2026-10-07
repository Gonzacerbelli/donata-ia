from app.models import Product
from app.services.llm import rag, vector_store


def test_format_docs_joins_content():
    from langchain_core.documents import Document

    docs = [Document(page_content="uno"), Document(page_content="dos")]
    assert rag.format_docs(docs) == "uno\n\ndos"


def test_ingest_and_search_knowledge_base():
    count = vector_store.ingest_knowledge_base()
    assert count > 0
    results = vector_store.search_knowledge_base("¿cómo se calculan los precios mayoristas?")
    assert results
    joined = " ".join(d.page_content for d in results).lower()
    assert "mayorista" in joined


def test_products_semantic_sync_and_search():
    products = [
        Product(
            provider_id="507f1f77bcf86cd799439011",
            name="Alfombra persa roja",
            category="alfombras",
            price=45000,
            price_mayorista=38000,
            stock=4,
        ),
        Product(
            provider_id="507f1f77bcf86cd799439011",
            name="Cortina de lino",
            category="cortinas",
            price=12000,
            stock=20,
        ),
    ]
    count = vector_store.sync_products(products)
    assert count == 2
    results = vector_store.search_products_semantic("alfombra para el living", k=1)
    assert results
    assert "alfombra" in results[0].page_content.lower()


def test_consultar_documentacion_without_documents(monkeypatch):
    monkeypatch.setattr(vector_store, "search_knowledge_base", lambda *a, **k: [])
    reply = rag.consultar_documentacion("¿cuál es la capital de Francia?")
    assert "No encontré información" in reply
