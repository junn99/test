#!/usr/bin/env python3
"""MCP Server for Notion Knowledge Agent.

This server provides Notion integration through the Model Context Protocol (MCP),
allowing Claude Desktop to interact with your Notion workspace.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.notion_tools import NotionToolkit
from src.agents.style_agent import create_style_agent
from src.agents.multi_agent import create_multi_agent_system
from src.rag.vector_store import VectorStoreManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class NotionMCPServer:
    """MCP Server for Notion Knowledge Agent."""

    def __init__(self):
        self.notion = NotionToolkit()
        self.vector_store = VectorStoreManager()
        self.multi_agent = None  # Lazy load

    async def handle_request(self, request: dict) -> dict:
        """
        Handle MCP request.

        Args:
            request: JSON-RPC request.

        Returns:
            JSON-RPC response.
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.info(f"Handling MCP request: {method}")

        try:
            if method == "tools/list":
                result = self._list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = await self._call_tool(tool_name, tool_args)
            elif method == "resources/list":
                result = self._list_resources()
            elif method == "resources/read":
                uri = params.get("uri")
                result = await self._read_resource(uri)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    def _list_tools(self) -> dict:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "search_notion",
                    "description": "Search for pages in Notion workspace",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_page",
                    "description": "Get full content of a Notion page",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "page_id": {
                                "type": "string",
                                "description": "Notion page ID"
                            }
                        },
                        "required": ["page_id"]
                    }
                },
                {
                    "name": "create_page",
                    "description": "Create a new Notion page",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Page title"
                            },
                            "content": {
                                "type": "string",
                                "description": "Page content"
                            },
                            "parent_page_id": {
                                "type": "string",
                                "description": "Parent page ID (optional)"
                            }
                        },
                        "required": ["title", "content"]
                    }
                },
                {
                    "name": "analyze_workspace",
                    "description": "Analyze Notion workspace and generate insights",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "generate_report",
                    "description": "Generate a report in user's style",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Report topic"
                            },
                            "type": {
                                "type": "string",
                                "description": "Report type (daily, weekly, monthly)",
                                "enum": ["daily", "weekly", "monthly"]
                            }
                        },
                        "required": ["topic"]
                    }
                },
                {
                    "name": "ask_agent",
                    "description": "Ask the multi-agent system a question",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Question to ask"
                            }
                        },
                        "required": ["question"]
                    }
                }
            ]
        }

    async def _call_tool(self, tool_name: str, args: dict) -> dict:
        """Call a specific tool."""
        if tool_name == "search_notion":
            query = args.get("query")
            pages = self.notion.search_pages(query=query)
            return {"content": [{"type": "text", "text": json.dumps(pages, indent=2)}]}

        elif tool_name == "get_page":
            page_id = args.get("page_id")
            page = self.notion.get_page_content(page_id=page_id)
            return {"content": [{"type": "text", "text": json.dumps(page, indent=2)}]}

        elif tool_name == "create_page":
            title = args.get("title")
            content = args.get("content")
            parent_page_id = args.get("parent_page_id")
            result = self.notion.create_page(
                title=title,
                content=content,
                parent_page_id=parent_page_id
            )
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        elif tool_name == "analyze_workspace":
            style_agent = create_style_agent()
            result = style_agent.learn_from_workspace(max_pages=20)
            summary = style_agent.get_style_summary()
            return {"content": [{"type": "text", "text": summary}]}

        elif tool_name == "generate_report":
            topic = args.get("topic")
            report_type = args.get("type", "weekly")
            style_agent = create_style_agent()
            content = style_agent.generate_content_with_style(
                topic=topic,
                content_type="report",
                length="medium"
            )
            return {"content": [{"type": "text", "text": content}]}

        elif tool_name == "ask_agent":
            question = args.get("question")
            if self.multi_agent is None:
                self.multi_agent = create_multi_agent_system()
            response = self.multi_agent.process(question)
            return {"content": [{"type": "text", "text": response}]}

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _list_resources(self) -> dict:
        """List available resources."""
        # Get all pages from vector store
        all_pages = self.vector_store.get_all_pages()

        resources = []
        for page in all_pages[:50]:  # Limit to 50
            page_id = page.get("page_id")
            title = page.get("title", "Untitled")

            resources.append({
                "uri": f"notion://page/{page_id}",
                "name": title,
                "description": f"Notion page: {title}",
                "mimeType": "text/plain"
            })

        return {"resources": resources}

    async def _read_resource(self, uri: str) -> dict:
        """Read a specific resource."""
        if not uri.startswith("notion://page/"):
            raise ValueError(f"Invalid URI: {uri}")

        page_id = uri.replace("notion://page/", "")
        page = self.notion.get_page_content(page_id=page_id)

        if "error" in page:
            raise ValueError(f"Error reading page: {page['error']}")

        content = f"# {page.get('title', 'Untitled')}\n\n{page.get('content', '')}"

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": content
                }
            ]
        }

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Notion MCP Server...")

        while True:
            try:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                request = json.loads(line)
                response = await self.handle_request(request)

                # Write response to stdout
                print(json.dumps(response), flush=True)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error in server loop: {e}")
                break

        logger.info("MCP Server stopped")


async def main():
    """Main entry point."""
    server = NotionMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
