"""Embedding generation for Notion content."""
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings

from ..utils.config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingManager:
    """Manages embeddings for Notion content."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self._embeddings = None

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """Lazy load embeddings model."""
        if self._embeddings is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        return self._embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.

        Args:
            texts: List of text documents to embed.

        Returns:
            List of embedding vectors.
        """
        logger.info(f"Embedding {len(texts)} documents")
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query.

        Args:
            text: Query text to embed.

        Returns:
            Embedding vector.
        """
        return self.embeddings.embed_query(text)
