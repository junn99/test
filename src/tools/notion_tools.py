"""Notion API tools for LangChain agents."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from notion_client import Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..utils.config import settings
from ..utils.logger import setup_logger
from ..utils.rate_limiter import notion_rate_limiter

logger = setup_logger(__name__)


class NotionToolkit:
    """Wrapper for Notion API operations as LangChain tools."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = Client(auth=api_key or settings.notion_api_key)

    def _extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """Extract text content from Notion blocks."""
        text_parts = []

        for block in blocks:
            block_type = block.get("type")
            if block_type and block_type in block:
                content = block[block_type]

                # Handle rich text
                if "rich_text" in content:
                    for text_obj in content["rich_text"]:
                        if "plain_text" in text_obj:
                            text_parts.append(text_obj["plain_text"])

                # Handle text directly
                elif "text" in content:
                    text_parts.append(content["text"])

        return "\n".join(text_parts)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _api_call_with_rate_limit(self, func, *args, **kwargs):
        """Execute API call with rate limiting."""
        with notion_rate_limiter:
            return func(*args, **kwargs)

    @tool
    def get_all_pages(self) -> List[Dict[str, Any]]:
        """
        Retrieve all pages from the Notion workspace.

        Returns:
            List of page objects with id, title, and last_edited_time.
        """
        logger.info("Fetching all pages from Notion")
        pages = []

        try:
            # Search for all pages with rate limiting
            results = self._api_call_with_rate_limit(
                self.client.search,
                filter={"property": "object", "value": "page"}
            )

            for page in results.get("results", []):
                page_id = page["id"]

                # Extract title
                title = "Untitled"
                properties = page.get("properties", {})

                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        title_array = prop_value.get("title", [])
                        if title_array:
                            title = title_array[0].get("plain_text", "Untitled")
                        break

                pages.append({
                    "id": page_id,
                    "title": title,
                    "last_edited_time": page.get("last_edited_time"),
                    "url": page.get("url"),
                })

            logger.info(f"Retrieved {len(pages)} pages")
            return pages

        except Exception as e:
            logger.error(f"Error fetching pages: {e}")
            return []

    @tool
    def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """
        Get the full content of a specific Notion page.

        Args:
            page_id: The ID of the page to retrieve.

        Returns:
            Dictionary with page metadata and content.
        """
        logger.info(f"Fetching content for page: {page_id}")

        try:
            # Get page metadata with rate limiting
            page = self._api_call_with_rate_limit(
                self.client.pages.retrieve,
                page_id=page_id
            )

            # Get page blocks (content) with rate limiting
            blocks = self._api_call_with_rate_limit(
                self.client.blocks.children.list,
                block_id=page_id
            )
            content = self._extract_text_from_blocks(blocks.get("results", []))

            # Extract title
            title = "Untitled"
            properties = page.get("properties", {})
            for prop_name, prop_value in properties.items():
                if prop_value.get("type") == "title":
                    title_array = prop_value.get("title", [])
                    if title_array:
                        title = title_array[0].get("plain_text", "Untitled")
                    break

            return {
                "id": page_id,
                "title": title,
                "content": content,
                "last_edited_time": page.get("last_edited_time"),
                "url": page.get("url"),
            }

        except Exception as e:
            logger.error(f"Error fetching page content: {e}")
            return {"error": str(e)}

    @tool
    def get_recently_edited_pages(self, days: int = 1) -> List[Dict[str, Any]]:
        """
        Get pages edited in the last N days.

        Args:
            days: Number of days to look back (default: 1).

        Returns:
            List of recently edited pages.
        """
        logger.info(f"Fetching pages edited in last {days} days")

        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            results = self._api_call_with_rate_limit(
                self.client.search,
                filter={
                    "property": "object",
                    "value": "page"
                },
                sort={
                    "direction": "descending",
                    "timestamp": "last_edited_time"
                }
            )

            recent_pages = []
            for page in results.get("results", []):
                last_edited = datetime.fromisoformat(
                    page["last_edited_time"].replace("Z", "+00:00")
                )

                if last_edited >= cutoff_date.replace(tzinfo=last_edited.tzinfo):
                    # Extract title
                    title = "Untitled"
                    properties = page.get("properties", {})
                    for prop_name, prop_value in properties.items():
                        if prop_value.get("type") == "title":
                            title_array = prop_value.get("title", [])
                            if title_array:
                                title = title_array[0].get("plain_text", "Untitled")
                            break

                    recent_pages.append({
                        "id": page["id"],
                        "title": title,
                        "last_edited_time": page["last_edited_time"],
                        "url": page.get("url"),
                    })

            logger.info(f"Found {len(recent_pages)} recently edited pages")
            return recent_pages

        except Exception as e:
            logger.error(f"Error fetching recent pages: {e}")
            return []

    @tool
    def search_pages(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for pages containing specific text.

        Args:
            query: Search query string.

        Returns:
            List of matching pages.
        """
        logger.info(f"Searching for: {query}")

        try:
            results = self._api_call_with_rate_limit(
                self.client.search,
                query=query,
                filter={"property": "object", "value": "page"}
            )

            pages = []
            for page in results.get("results", []):
                # Extract title
                title = "Untitled"
                properties = page.get("properties", {})
                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        title_array = prop_value.get("title", [])
                        if title_array:
                            title = title_array[0].get("plain_text", "Untitled")
                        break

                pages.append({
                    "id": page["id"],
                    "title": title,
                    "last_edited_time": page.get("last_edited_time"),
                    "url": page.get("url"),
                })

            logger.info(f"Found {len(pages)} matching pages")
            return pages

        except Exception as e:
            logger.error(f"Error searching pages: {e}")
            return []

    @tool
    def get_databases(self) -> List[Dict[str, Any]]:
        """
        Get all databases in the workspace.

        Returns:
            List of database objects.
        """
        logger.info("Fetching all databases")

        try:
            results = self._api_call_with_rate_limit(
                self.client.search,
                filter={"property": "object", "value": "database"}
            )

            databases = []
            for db in results.get("results", []):
                # Extract title
                title = "Untitled Database"
                title_array = db.get("title", [])
                if title_array:
                    title = title_array[0].get("plain_text", "Untitled Database")

                databases.append({
                    "id": db["id"],
                    "title": title,
                    "url": db.get("url"),
                })

            logger.info(f"Found {len(databases)} databases")
            return databases

        except Exception as e:
            logger.error(f"Error fetching databases: {e}")
            return []

    @tool
    def create_page(self, title: str, content: str, parent_page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new Notion page.

        Args:
            title: Page title.
            content: Page content (plain text).
            parent_page_id: Optional parent page ID.

        Returns:
            Dictionary with created page info.
        """
        logger.info(f"Creating page: {title}")

        try:
            # Build page properties
            properties = {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }

            # Build children (content blocks)
            children = []
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": paragraph.strip()
                                    }
                                }
                            ]
                        }
                    })

            # Create page
            page_data = {
                "properties": properties,
                "children": children
            }

            if parent_page_id:
                page_data["parent"] = {"page_id": parent_page_id}
            else:
                # Need a parent - use workspace (this might fail without proper setup)
                logger.warning("No parent page specified - page creation may fail")
                return {"error": "parent_page_id is required"}

            page = self._api_call_with_rate_limit(
                self.client.pages.create,
                **page_data
            )

            logger.info(f"Page created: {page['id']}")
            return {
                "id": page["id"],
                "title": title,
                "url": page.get("url"),
                "created_time": page.get("created_time")
            }

        except Exception as e:
            logger.error(f"Error creating page: {e}")
            return {"error": str(e)}

    @tool
    def update_page(self, page_id: str, title: Optional[str] = None, archived: bool = False) -> Dict[str, Any]:
        """
        Update a Notion page properties.

        Args:
            page_id: Page ID to update.
            title: New title (optional).
            archived: Whether to archive the page.

        Returns:
            Dictionary with update result.
        """
        logger.info(f"Updating page: {page_id}")

        try:
            update_data = {}

            if title:
                update_data["properties"] = {
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                }

            if archived:
                update_data["archived"] = True

            if not update_data:
                return {"error": "No updates specified"}

            page = self._api_call_with_rate_limit(
                self.client.pages.update,
                page_id=page_id,
                **update_data
            )

            logger.info(f"Page updated: {page_id}")
            return {
                "id": page["id"],
                "url": page.get("url"),
                "last_edited_time": page.get("last_edited_time")
            }

        except Exception as e:
            logger.error(f"Error updating page: {e}")
            return {"error": str(e)}

    @tool
    def query_database(self, database_id: str, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Query a Notion database.

        Args:
            database_id: Database ID to query.
            filter_dict: Optional filter dictionary.

        Returns:
            List of database entries.
        """
        logger.info(f"Querying database: {database_id}")

        try:
            query_params = {}
            if filter_dict:
                query_params["filter"] = filter_dict

            results = self._api_call_with_rate_limit(
                self.client.databases.query,
                database_id=database_id,
                **query_params
            )

            entries = []
            for page in results.get("results", []):
                # Extract properties
                properties = {}
                for prop_name, prop_value in page.get("properties", {}).items():
                    prop_type = prop_value.get("type")

                    if prop_type == "title":
                        title_array = prop_value.get("title", [])
                        properties[prop_name] = title_array[0].get("plain_text", "") if title_array else ""
                    elif prop_type == "rich_text":
                        text_array = prop_value.get("rich_text", [])
                        properties[prop_name] = text_array[0].get("plain_text", "") if text_array else ""
                    elif prop_type == "number":
                        properties[prop_name] = prop_value.get("number")
                    elif prop_type == "select":
                        select_obj = prop_value.get("select")
                        properties[prop_name] = select_obj.get("name") if select_obj else None
                    elif prop_type == "date":
                        date_obj = prop_value.get("date")
                        properties[prop_name] = date_obj.get("start") if date_obj else None
                    else:
                        properties[prop_name] = str(prop_value)

                entries.append({
                    "id": page["id"],
                    "properties": properties,
                    "url": page.get("url"),
                    "last_edited_time": page.get("last_edited_time")
                })

            logger.info(f"Found {len(entries)} entries in database")
            return entries

        except Exception as e:
            logger.error(f"Error querying database: {e}")
            return []

    def get_tools(self):
        """Get all tools as a list for LangChain agent."""
        return [
            self.get_all_pages,
            self.get_page_content,
            self.get_recently_edited_pages,
            self.search_pages,
            self.get_databases,
            self.create_page,
            self.update_page,
            self.query_database,
        ]
