"""Vector store management for Notion content."""
from typing import List, Optional, Dict, Any

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from .embeddings import EmbeddingManager
from ..utils.config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorStoreManager:
    """Manages vector database operations."""

    def __init__(self, collection_name: str = "notion_pages"):
        self.collection_name = collection_name
        self.embedding_manager = EmbeddingManager()
        self._vector_store = None

    @property
    def vector_store(self) -> Chroma:
        """Lazy load vector store."""
        if self._vector_store is None:
            logger.info(f"Initializing vector store: {settings.vector_db_path}")
            self._vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_manager.embeddings,
                persist_directory=str(settings.vector_db_path)
            )
        return self._vector_store

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            documents: List of LangChain Document objects.

        Returns:
            List of document IDs.
        """
        logger.info(f"Adding {len(documents)} documents to vector store")
        return self.vector_store.add_documents(documents)

    def add_page(self, page_id: str, title: str, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Add a single Notion page to the vector store.

        Args:
            page_id: Notion page ID.
            title: Page title.
            content: Page content.
            metadata: Additional metadata.

        Returns:
            Document ID.
        """
        # Delete existing if present
        self.delete_page(page_id)

        # Create document
        full_metadata = {
            "page_id": page_id,
            "title": title,
            **(metadata or {})
        }

        doc = Document(
            page_content=f"# {title}\n\n{content}",
            metadata=full_metadata
        )

        logger.info(f"Adding page to vector store: {title} ({page_id})")
        ids = self.vector_store.add_documents([doc])
        return ids[0] if ids else None

    def delete_page(self, page_id: str) -> None:
        """
        Delete a page from the vector store.

        Args:
            page_id: Notion page ID to delete.
        """
        try:
            # Get existing documents with this page_id
            results = self.vector_store.get(where={"page_id": page_id})

            if results and results.get("ids"):
                logger.info(f"Deleting page from vector store: {page_id}")
                self.vector_store.delete(ids=results["ids"])
        except Exception as e:
            logger.warning(f"Error deleting page {page_id}: {e}")

    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search for similar documents.

        Args:
            query: Search query.
            k: Number of results to return.

        Returns:
            List of similar documents.
        """
        logger.info(f"Searching vector store: '{query}' (k={k})")
        return self.vector_store.similarity_search(query, k=k)

    def search_with_score(self, query: str, k: int = 5) -> List[tuple[Document, float]]:
        """
        Search with similarity scores.

        Args:
            query: Search query.
            k: Number of results to return.

        Returns:
            List of (document, score) tuples.
        """
        logger.info(f"Searching vector store with scores: '{query}' (k={k})")
        return self.vector_store.similarity_search_with_score(query, k=k)

    def get_all_pages(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all pages in the vector store.

        Returns:
            List of page metadata dictionaries.
        """
        try:
            results = self.vector_store.get()
            if not results or not results.get("metadatas"):
                return []

            return results["metadatas"]
        except Exception as e:
            logger.error(f"Error getting all pages: {e}")
            return []

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        logger.warning("Clearing entire vector store")
        try:
            # Get all IDs
            results = self.vector_store.get()
            if results and results.get("ids"):
                self.vector_store.delete(ids=results["ids"])
                logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
