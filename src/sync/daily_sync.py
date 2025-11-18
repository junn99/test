"""Daily synchronization of Notion content to vector database."""
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..tools.notion_tools import NotionToolkit
from ..rag.vector_store import VectorStoreManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DailySync:
    """Handles daily synchronization between Notion and vector database."""

    def __init__(self):
        self.notion = NotionToolkit()
        self.vector_store = VectorStoreManager()

    def sync_recent_changes(self, days: int = 1) -> Dict[str, Any]:
        """
        Sync pages modified in the last N days.

        Args:
            days: Number of days to look back.

        Returns:
            Dictionary with sync statistics.
        """
        logger.info(f"Starting daily sync for last {days} days")
        start_time = datetime.now()

        try:
            # Get recently edited pages
            recent_pages = self.notion.get_recently_edited_pages(days=days)

            stats = {
                "total_pages_checked": len(recent_pages),
                "pages_updated": 0,
                "pages_failed": 0,
                "start_time": start_time.isoformat(),
                "errors": []
            }

            # Update each page in vector store
            for page_info in recent_pages:
                try:
                    page_id = page_info["id"]
                    logger.info(f"Syncing page: {page_info['title']} ({page_id})")

                    # Get full page content
                    page_data = self.notion.get_page_content(page_id=page_id)

                    if "error" in page_data:
                        logger.error(f"Failed to fetch page {page_id}: {page_data['error']}")
                        stats["pages_failed"] += 1
                        stats["errors"].append({
                            "page_id": page_id,
                            "error": page_data["error"]
                        })
                        continue

                    # Add/update in vector store
                    self.vector_store.add_page(
                        page_id=page_data["id"],
                        title=page_data["title"],
                        content=page_data["content"],
                        metadata={
                            "last_edited_time": page_data["last_edited_time"],
                            "url": page_data["url"],
                            "synced_at": datetime.now().isoformat()
                        }
                    )

                    stats["pages_updated"] += 1
                    logger.info(f"Successfully synced: {page_data['title']}")

                except Exception as e:
                    logger.error(f"Error syncing page {page_info.get('id', 'unknown')}: {e}")
                    stats["pages_failed"] += 1
                    stats["errors"].append({
                        "page_id": page_info.get("id"),
                        "error": str(e)
                    })

            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            stats["end_time"] = end_time.isoformat()
            stats["duration_seconds"] = duration

            logger.info(
                f"Sync completed: {stats['pages_updated']} updated, "
                f"{stats['pages_failed']} failed, "
                f"duration: {duration:.2f}s"
            )

            return stats

        except Exception as e:
            logger.error(f"Sync failed with error: {e}")
            return {
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }

    def full_sync(self) -> Dict[str, Any]:
        """
        Perform a full sync of all pages in workspace.

        Returns:
            Dictionary with sync statistics.
        """
        logger.info("Starting full workspace sync")
        start_time = datetime.now()

        try:
            # Get all pages
            all_pages = self.notion.get_all_pages()

            stats = {
                "total_pages": len(all_pages),
                "pages_synced": 0,
                "pages_failed": 0,
                "start_time": start_time.isoformat(),
                "errors": []
            }

            for page_info in all_pages:
                try:
                    page_id = page_info["id"]
                    logger.info(f"Syncing page: {page_info['title']} ({page_id})")

                    # Get full content
                    page_data = self.notion.get_page_content(page_id=page_id)

                    if "error" in page_data:
                        stats["pages_failed"] += 1
                        stats["errors"].append({
                            "page_id": page_id,
                            "error": page_data["error"]
                        })
                        continue

                    # Add to vector store
                    self.vector_store.add_page(
                        page_id=page_data["id"],
                        title=page_data["title"],
                        content=page_data["content"],
                        metadata={
                            "last_edited_time": page_data["last_edited_time"],
                            "url": page_data["url"],
                            "synced_at": datetime.now().isoformat()
                        }
                    )

                    stats["pages_synced"] += 1

                except Exception as e:
                    logger.error(f"Error syncing page {page_info.get('id')}: {e}")
                    stats["pages_failed"] += 1
                    stats["errors"].append({
                        "page_id": page_info.get("id"),
                        "error": str(e)
                    })

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            stats["end_time"] = end_time.isoformat()
            stats["duration_seconds"] = duration

            logger.info(
                f"Full sync completed: {stats['pages_synced']} synced, "
                f"{stats['pages_failed']} failed, "
                f"duration: {duration:.2f}s"
            )

            return stats

        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            return {
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }


def run_daily_sync(days: int = 1) -> Dict[str, Any]:
    """
    Convenience function to run daily sync.

    Args:
        days: Number of days to look back.

    Returns:
        Sync statistics.
    """
    sync = DailySync()
    return sync.sync_recent_changes(days=days)


def run_full_sync() -> Dict[str, Any]:
    """
    Convenience function to run full sync.

    Returns:
        Sync statistics.
    """
    sync = DailySync()
    return sync.full_sync()
