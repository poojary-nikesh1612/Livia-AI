"""ai_core/chains/reranker_chain.py"""

from langchain_cloudflare import CloudflareWorkersAIReranker
from langchain_core.runnables import RunnableLambda


async def run_cloudflare_reranker(inputs: dict) -> list[dict]:
    """
    Reranks candidate chunks using the official LangChain Cloudflare integration.
    """
    query = inputs["query"]
    chunks = inputs["chunks"]

    # Initialize the Reranker
    reranker = CloudflareWorkersAIReranker(model_name="@cf/baai/bge-reranker-base")

    # Extract raw strings for the reranker
    texts = [chunk["content"] for chunk in chunks]

    # Perform async reranking
    # Returns a list of RerankResult objects (with .index, .score, .text)
    rerank_results = await reranker.arerank(query=query, documents=texts)

    # Map the RerankResult objects back to chunk format
    reranked_chunks = []
    for res in rerank_results:
        idx = res.index
        score = res.score

        original_chunk = chunks[idx]

        reranked_chunks.append(
            {
                "content": original_chunk["content"],
                "metadata": {**original_chunk["metadata"], "relevance_score": score},
            }
        )

    return reranked_chunks


# Export as a native Langchain LCEL component
cloudflare_reranker_chain = RunnableLambda(run_cloudflare_reranker)
