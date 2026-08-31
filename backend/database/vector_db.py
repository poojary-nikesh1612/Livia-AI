"""database/vector_db.py: Live similarity search query function."""

import logging
from typing import Any

from langchain_cloudflare import CloudflareWorkersAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

from database.session import engine

logger = logging.getLogger(__name__)

embeddings = CloudflareWorkersAIEmbeddings(
    model_name="@cf/baai/bge-base-en-v1.5",
)

pg_engine = PGEngine.from_engine(engine)
vector_store: PGVectorStore | None = None


async def get_vector_store() -> PGVectorStore:
    """Create the PGVectorStore lazily on the active event loop."""
    global vector_store

    if vector_store is None:
        vector_store = await PGVectorStore.create(
            engine=pg_engine,
            embedding_service=embeddings,
            table_name="paddy_diseases",
        )

    return vector_store


async def search_disease_by_symptoms(
    symptoms_query: str, valid_stage: str, k: int = 5
) -> list[dict[str, Any]]:
    """
    Performs a semantic vector search to diagnose a disease based on farmer symptoms.
    Returns the top 'k' closest matches.
    """
    if not valid_stage:
        return []

    try:
        store = await get_vector_store()
        docs = await store.asimilarity_search(
            symptoms_query,
            k=k,
            filter={
                "valid_stages": {"$like": f'%"{valid_stage}"%'}
            },
        )

        results = []
        for doc in docs:
            results.append({"content": doc.page_content, "metadata": doc.metadata})
        return results

    except Exception:
        logger.exception("Vector search failed")
        return []
