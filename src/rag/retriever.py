"""Retrieval system for Notion content."""
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from .vector_store import VectorStoreManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class NotionRetriever(BaseRetriever):
    """Custom retriever for Notion content."""

    vector_store_manager: VectorStoreManager
    k: int = 5
    score_threshold: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Retrieve relevant documents.

        Args:
            query: Search query.
            run_manager: Callback manager.

        Returns:
            List of relevant documents.
        """
        if self.score_threshold is not None:
            # Use score threshold filtering
            results = self.vector_store_manager.search_with_score(query, k=self.k)
            return [doc for doc, score in results if score >= self.score_threshold]
        else:
            # Simple similarity search
            return self.vector_store_manager.search(query, k=self.k)


def create_retriever(k: int = 5, score_threshold: Optional[float] = None) -> NotionRetriever:
    """
    Create a Notion retriever instance.

    Args:
        k: Number of documents to retrieve.
        score_threshold: Minimum similarity score (optional).

    Returns:
        NotionRetriever instance.
    """
    vector_store_manager = VectorStoreManager()

    return NotionRetriever(
        vector_store_manager=vector_store_manager,
        k=k,
        score_threshold=score_threshold
    )
