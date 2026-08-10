import logging
from typing import Dict, Any
from app.tools.base import Tool, ToolResult
from app.services.retrieval_service import retrieve_relevant_chunks

logger = logging.getLogger("nova-ai.tools.document-search")

class DocumentSearchTool(Tool):
    @property
    def name(self) -> str:
        return "document_search"

    @property
    def description(self) -> str:
        return "Search within the user's uploaded documents for semantic information matching a query."

    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        query = input_data.get("query", "").strip()
        user_id = input_data.get("user_id")
        db = input_data.get("db")
        document_ids = input_data.get("document_ids")

        if not query:
            return ToolResult(tool_name=self.name, success=False, data={}, error="Query is required.")
            
        # Security validation: Enforce authenticated user context
        if not user_id:
            logger.error("DocumentSearchTool called without an authenticated user_id context.")
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error="Unauthorized: Document search requires authenticated user context."
            )
            
        if not db:
            logger.error("DocumentSearchTool called without db session.")
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error="Database session is missing or invalid."
            )

        try:
            # retrieve_relevant_chunks strictly filters by user_id internally
            chunks = await retrieve_relevant_chunks(
                db=db,
                user_id=user_id,
                query=query,
                top_k=5,
                document_ids=document_ids
            )
            
            results = []
            citations = []
            for idx, chunk in enumerate(chunks):
                results.append({
                    "content": chunk["content"],
                    "filename": chunk["original_filename"],
                    "page": chunk["metadata"].get("page", 1),
                    "score": chunk["score"]
                })
                citations.append({
                    "index": idx + 1,
                    "filename": chunk["original_filename"],
                    "page": chunk["metadata"].get("page", 1),
                    "content": chunk["content"]
                })

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"results": results},
                sources=citations
            )
        except Exception as e:
            logger.exception(f"DocumentSearchTool retrieval failure: {e}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error=f"Document search retrieval failed: {e}"
            )
