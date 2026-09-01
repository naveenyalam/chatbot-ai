from enum import Enum
from typing import Optional

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
