from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import WorkspaceMetadata, WorkspaceChatRequest
from app.workspaces.base import BaseWorkspace
from app.services.data_analysis_service import analyze_dataset, format_dataset_summary_for_llm
from app.services.workspace_prompts import get_workspace_prompt


class DataAnalysisWorkspace(BaseWorkspace):
    @property
    def mode(self) -> WorkspaceMode:
        return WorkspaceMode.DATA_ANALYSIS

    @property
    def metadata(self) -> WorkspaceMetadata:
        return WorkspaceMetadata(
            id=WorkspaceMode.DATA_ANALYSIS.value,
            name="Data Analysis",
            description="CSV & JSON statistical profiling, missing value detection, schema detection, and trend analysis",
            capabilities=["dataset-parsing", "statistical-summary", "missing-value-detection", "column-profiling"],
            icon="bar-chart-2",
            supported_tools=["calculator", "code_execution"],
            allowed_attachments=["csv", "json"],
            suggested_prompts=[
                "Analyze this CSV dataset and provide summary statistics.",
                "Identify top trends and outliers in the uploaded sales data.",
                "Check for missing values and calculate averages per category."
            ]
        )

    def validate_request(self, req: WorkspaceChatRequest) -> List[str]:
        warnings = []
        user_text = req.message or (req.messages[-1].content if req.messages else "")
        has_attachment = bool(req.attachments and len(req.attachments) > 0)
        has_csv_text = bool("," in user_text and "\n" in user_text)
        
        if not has_attachment and not has_csv_text:
            warnings.append("For best results, attach a CSV/JSON file or paste tabular data.")
        return warnings

    async def execute_stream(
        self,
        request_id: str,
        user_id: str,
        conversation_id: Optional[str],
        messages: List[Dict[str, str]],
        req: WorkspaceChatRequest,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        user_msg = req.message or (messages[-1]["content"] if messages else "")
        data_content = ""

        if req.attachments:
            for att in req.attachments:
                if att.get("content"):
                    data_content += "\n" + att["content"]

        if not data_content and ("," in user_msg and "\n" in user_msg):
            data_content = user_msg

        if data_content:
            yield {"type": "status", "value": "analyzing", "query": "Profiling dataset metrics & statistics..."}
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

            system_prompt = get_workspace_prompt("data-analysis") + f"\n\n{summary_text}"
            style_instructions = ""
            if req.response_style == "concise":
                style_instructions += "\n- Write in a highly concise, direct manner. Use short bullet points and omit fluff."
            elif req.response_style == "detailed":
                style_instructions += "\n- Provide a highly in-depth, detailed explanation with full context."
            if req.response_tone == "friendly":
                style_instructions += "\n- Keep your tone warm, friendly, and conversational."
            elif req.response_tone == "technical":
                style_instructions += "\n- Maintain a strictly academic, professional, and code-heavy tone."
            if style_instructions:
                system_prompt += f"\n\n### RESPONSE STYLE & TONE GUIDELINES{style_instructions}"

            enhanced_messages = [{"role": "system", "content": system_prompt}] + messages

            from app.services.model_router import model_router
            async for chunk in model_router.stream(enhanced_messages, purpose="fast", temperature=req.temperature):
                yield {"type": "text", "value": chunk}
        else:
            from app.agents.manager import agent_manager
            async for event in agent_manager.execute(
                request_id=request_id,
                user_id=user_id,
                conversation_id=conversation_id,
                messages=messages,
                mode=self.mode.value,
                document_ids=req.document_ids or [],
                model_alias=req.model,
                temperature=req.temperature,
                db=db,
                response_style=req.response_style,
                response_tone=req.response_tone,
                semantic_chunk_limit=req.semantic_chunk_limit,
                similarity_filtering=req.similarity_filtering
            ):
                yield event
