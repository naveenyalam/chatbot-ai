from enum import Enum
from typing import Optional, List, Dict, Any

class WorkspaceMode(str, Enum):
    GENERAL = "general"
    RESEARCH = "research"
    WRITING = "writing"
    CODING = "coding"
    DOCUMENTS = "documents"
    DATA_ANALYSIS = "data-analysis"
    AGENT = "agent"

    @classmethod
    def normalize(cls, val: Optional[str]) -> Optional["WorkspaceMode"]:
        if not val or not isinstance(val, str):
            return cls.GENERAL
        
        clean = val.strip().lower().replace("_", "-").replace(" ", "-")
        
        # Alias mappings
        alias_map = {
            "chat": cls.GENERAL,
            "normal": cls.GENERAL,
            "general": cls.GENERAL,
            "general-ai": cls.GENERAL,
            "research": cls.RESEARCH,
            "deep-research": cls.RESEARCH,
            "writing": cls.WRITING,
            "draft": cls.WRITING,
            "editor": cls.WRITING,
            "coding": cls.CODING,
            "code": cls.CODING,
            "developer": cls.CODING,
            "documents": cls.DOCUMENTS,
            "document": cls.DOCUMENTS,
            "rag": cls.DOCUMENTS,
            "document-search": cls.DOCUMENTS,
            "data-analysis": cls.DATA_ANALYSIS,
            "data_analysis": cls.DATA_ANALYSIS,
            "data": cls.DATA_ANALYSIS,
            "dataset": cls.DATA_ANALYSIS,
            "agent": cls.AGENT,
            "agents": cls.AGENT,
            "task": cls.AGENT,
            "agent-workspace": cls.AGENT,
        }
        
        return alias_map.get(clean)

    @classmethod
    def get_metadata(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": cls.GENERAL.value,
                "name": "General AI",
                "description": "General multi-modal chat & reasoning assistant",
                "capabilities": ["multi-turn-chat", "explanations", "brainstorming", "general-knowledge"],
                "icon": "sparkles",
                "suggested_prompts": [
                    "Explain quantum computing in simple terms",
                    "How do I structure a modern web application?",
                    "What are the key principles of clean architecture?"
                ]
            },
            {
                "id": cls.RESEARCH.value,
                "name": "Research",
                "description": "Multi-source web & topic research with citations",
                "capabilities": ["multi-step-search", "citation-accumulation", "structured-summarization", "comparative-analysis"],
                "icon": "search",
                "suggested_prompts": [
                    "Research the advantages and disadvantages of electric vehicles.",
                    "Investigate recent breakthroughs in renewable energy technology.",
                    "Summarize the competitive landscape of LLM providers in 2026."
                ]
            },
            {
                "id": cls.WRITING.value,
                "name": "Writing",
                "description": "Professional drafting, rewriting, and tone transformation",
                "capabilities": ["drafting", "editing", "tone-adjustment", "summarization", "grammar-fix"],
                "icon": "pen-tool",
                "suggested_prompts": [
                    "Write a professional email asking my manager for leave.",
                    "Rewrite this paragraph in simple, executive English.",
                    "Draft a concise press release announcing a software update."
                ]
            },
            {
                "id": cls.CODING.value,
                "name": "Coding",
                "description": "Programming, code generation, debugging, and refactoring",
                "capabilities": ["code-generation", "debugging", "algorithm-design", "code-explanation", "refactoring"],
                "icon": "code",
                "suggested_prompts": [
                    "Write a Python program to check whether a number is prime.",
                    "Debug this code and explain why it throws a recursion error.",
                    "Refactor this JavaScript function to use async/await."
                ]
            },
            {
                "id": cls.DOCUMENTS.value,
                "name": "Documents",
                "description": "RAG document retrieval and verified context analysis",
                "capabilities": ["document-search", "vector-retrieval", "context-citation", "chunking"],
                "icon": "file-text",
                "suggested_prompts": [
                    "What are the main key points in the uploaded document?",
                    "Summarize the terms of service from the uploaded PDF.",
                    "Find the exact financial projections in the attached document."
                ]
            },
            {
                "id": cls.DATA_ANALYSIS.value,
                "name": "Data Analysis",
                "description": "CSV & JSON statistical analysis, schema detection, and trend analysis",
                "capabilities": ["dataset-parsing", "statistical-summary", "missing-value-detection", "column-profiling"],
                "icon": "bar-chart-2",
                "suggested_prompts": [
                    "Analyze this CSV dataset and provide summary statistics.",
                    "Identify top trends and outliers in the uploaded sales data.",
                    "Check for missing values and calculate averages per category."
                ]
            },
            {
                "id": cls.AGENT.value,
                "name": "Agent Workspace",
                "description": "Autonomous multi-step task execution using authorized tools",
                "capabilities": ["multi-step-planning", "tool-execution", "calculator", "code-sandbox", "web-search"],
                "icon": "bot",
                "suggested_prompts": [
                    "Calculate total project cost and research market rates for comparison.",
                    "Search for recent AI news, filter top 3 articles, and write a summary.",
                    "Run Python code to process data and generate a structured report."
                ]
            }
        ]
