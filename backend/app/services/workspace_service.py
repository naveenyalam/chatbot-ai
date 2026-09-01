"""
Workspace Service — Central orchestration layer for all NOVA AI workspace modes.

Responsibilities:
- Validate workspace mode enum & reject invalid strings with HTTP 422
- Map workspace mode to dedicated system prompts, tool permissions, and workflows
- Perform real data analysis for DATA_ANALYSIS workspace mode
- Route execution to appropriate agents (Research, Document, Task, Chat)
- Emit consistent streaming SSE events
"""

import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.workspace_mode import WorkspaceMode
from app.services.workspace_prompts import get_workspace_prompt
from app.services.data_analysis_service import analyze_dataset, format_dataset_summary_for_llm
from app.agents.manager import agent_manager

logger = logging.getLogger("nova-ai.services.workspace")


class WorkspaceService:
    """
    Central Orchestrator for Workspace Modes.
    """

    @staticmethod
    def validate_workspace(workspace_str: Optional[str]) -> WorkspaceMode:
        """
        Validate and normalize workspace mode string.
        Raises HTTP 422 Unprocessable Entity if an unrecognized mode string is provided.
        """
        if not workspace_str:
            return WorkspaceMode.GENERAL

        normalized = WorkspaceMode.normalize(workspace_str)
        if normalized is None:
            logger.warning(f"Invalid workspace mode requested: '{workspace_str}'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "INVALID_WORKSPACE_MODE",
                    "message": f"Workspace mode '{workspace_str}' is invalid.",
                    "valid_modes": [m.value for m in WorkspaceMode]
                }
            )
        return normalized

    async def execute_workspace_chat(
        self,
        request_id: str,
        user_id: str,
        conversation_id: Optional[str],
        messages: List[Dict[str, str]],
        workspace_mode_raw: Optional[str],
        document_ids: Optional[List[str]],
        attachments: Optional[List[Dict[str, Any]]],
        model_alias: Optional[str],
        temperature: float,
        db: Session,
        response_style: Optional[str] = None,
        response_tone: Optional[str] = None,
        semantic_chunk_limit: Optional[int] = None,
        similarity_filtering: Optional[bool] = None,
        language: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main execution flow routing the chat request to the specific workspace engine.
        """
        mode_enum = self.validate_workspace(workspace_mode_raw)
        logger.info(f"[{request_id}] Executing workspace mode: {mode_enum.value} for user={user_id}")

        # Check for data analysis workflow if DATA_ANALYSIS mode selected or CSV content attached
        user_msg = messages[-1]["content"] if messages else ""
        
        # If DATA_ANALYSIS mode and CSV text / attachment is present, perform exact statistical calculation
        if mode_enum == WorkspaceMode.DATA_ANALYSIS:
            data_content = ""
            if attachments:
                for att in attachments:
                    if att.get("content"):
                        data_content += "\n" + att["content"]
            
            # Check for inline CSV snippet if no attachment
            if not data_content and ("," in user_msg and "\n" in user_msg):
                data_content = user_msg

            if data_content:
                yield {"type": "status", "value": "analyzing", "query": "Profiling tabular dataset & calculating metrics..."}
                analysis = analyze_dataset(data_content)
                summary_text = format_dataset_summary_for_llm(analysis)
                
                yield {
                    "type": "tool_result",
                    "tool": "data_analysis",
                    "success": True,
                    "data": {
                        "row_count": analysis.get("row_count", 0),
                        "column_count": analysis.get("column_count", 0),
                        "columns": [c["name"] for c in analysis.get("columns", [])]
                    },
                    "label": "Dataset Profiling Complete"
                }

                from app.services.workspace_prompts import get_multilingual_prompt
                user_msg = messages[-1]["content"] if messages else ""
                multilingual_prompt = get_multilingual_prompt(user_msg, language)
                system_instruction = f"{multilingual_prompt}\n\n{get_workspace_prompt('data-analysis')}\n\n{summary_text}"
                enhanced_messages = [{"role": "system", "content": system_instruction}] + messages
                
                # Stream response via model_router
                from app.services.model_router import model_router
                async for chunk in model_router.stream(enhanced_messages, purpose="fast", temperature=temperature):
                    yield {"type": "text", "value": chunk}
                return

        # For all other modes, route through AgentManager with normalized mode_enum
        async for event in agent_manager.execute(
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            messages=messages,
            mode=mode_enum.value,
            document_ids=document_ids or [],
            model_alias=model_alias,
            temperature=temperature,
            db=db,
            response_style=response_style,
            response_tone=response_tone,
            semantic_chunk_limit=semantic_chunk_limit,
            similarity_filtering=similarity_filtering,
            language=language
        ):
            yield event


workspace_service = WorkspaceService()
