from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ...config import settings
from ...models import Product

KB_COLLECTION = "donata_kb"
PRODUCTS_COLLECTION = "donata_products"
MANUAL_PATH = Path(__file__).resolve().parents[3] / "knowledge" / "manual-operativo.md"


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


def _persist_dir(collection: str) -> str:
    return str(Path(settings.chroma_dir) / collection)


def get_kb_store() -> Chroma:
    return Chroma(
        collection_name=KB_COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=_persist_dir(KB_COLLECTION),
    )


def get_products_store() -> Chroma:
    return Chroma(
        collection_name=PRODUCTS_COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=_persist_dir(PRODUCTS_COLLECTION),
    )


def _kb_chunk_count(store: Chroma) -> int:
    try:
        return store._collection.count()
    except Exception:
        return 0


def ingest_knowledge_base(force: bool = False) -> int:
    store = get_kb_store()
    if not force and _kb_chunk_count(store) > 0:
        return _kb_chunk_count(store)
    if force:
        store.reset_collection()
    documents = TextLoader(str(MANUAL_PATH), encoding="utf-8").load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(documents)
    if chunks:
        store.add_documents(chunks)
    return len(chunks)


def search_knowledge_base(query: str, k: int | None = None) -> list[Document]:
    store = get_kb_store()
    if _kb_chunk_count(store) == 0:
        return []
    return store.similarity_search(query, k=k or settings.rag_top_k)


def _product_to_document(product: Product) -> Document:
    parts = [product.name]
    if product.category:
        parts.append(f"Categoría: {product.category}")
    if product.description:
        parts.append(product.description)
    if product.price is not None:
        parts.append(f"Precio minorista: {product.price}")
    if product.price_mayorista is not None:
        parts.append(f"Precio mayorista: {product.price_mayorista}")
    parts.append(f"Stock: {product.stock}")
    return Document(
        page_content="\n".join(parts),
        metadata={
            "id": str(product.id),
            "name": product.name,
            "category": product.category or "",
            "price": product.price or 0,
            "price_mayorista": product.price_mayorista or 0,
            "stock": product.stock,
        },
    )


def sync_products(products: list[Product]) -> int:
    store = get_products_store()
    store.reset_collection()
    documents = [_product_to_document(p) for p in products]
    if documents:
        store.add_documents(documents)
    return len(documents)


def search_products_semantic(query: str, k: int = 5) -> list[Document]:
    store = get_products_store()
    if _kb_chunk_count(store) == 0:
        return []
    return store.similarity_search(query, k=k)


def reset_products_store() -> None:
    get_products_store().reset_collection()
