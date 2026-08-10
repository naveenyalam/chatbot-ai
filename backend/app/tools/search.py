from typing import Dict, Any
from app.tools.base import Tool, ToolResult
from app.services.search.provider import get_search_provider

class WebSearchTool(Tool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for up-to-date information on any query."

    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        query = input_data.get("query")
        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error="Missing required 'query' input parameter."
            )
        
        max_results = input_data.get("max_results", 5)
        
        try:
            provider = get_search_provider()
            results = await provider.search(query, max_results=max_results)
            
            # Normalize list into dict payload
            serialized = [r.dict() for r in results]
            
            # Return sources list for citations mapping
            sources = [
                {
                    "title": r.title,
                    "url": r.url,
                    "domain": r.url.split("/")[2] if r.url and len(r.url.split("/")) > 2 else "web",
                    "snippet": r.snippet,
                    "published_at": r.published_at.isoformat() if r.published_at else None
                }
                for r in results
            ]
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"results": serialized},
                sources=sources
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error=str(exc)
            )
