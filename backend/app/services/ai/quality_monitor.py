import logging
from typing import List, Dict, Any
from app.core.metrics import AI_QUALITY_GROUNDING_SCORE

logger = logging.getLogger("nova-ai.quality-monitor")

class AIQualityMonitor:
    """
    Evaluates response grounding scores, hallucination indicators, and prompt injection
    isolation without storing private user prompts or sensitive text payloads.
    """
    
    @staticmethod
    def calculate_grounding_score(response_text: str, context_chunks: List[str]) -> float:
        """
        Calculates n-gram token overlap grounding score between AI response and RAG context.
        """
        if not response_text or not context_chunks:
            return 0.0
            
        combined_context = " ".join(context_chunks).lower()
        response_words = [w.lower().strip(".,!?()[]") for w in response_text.split() if len(w) > 3]
        
        if not response_words:
            return 1.0
            
        grounded_count = sum(1 for w in response_words if w in combined_context)
        score = min(1.0, max(0.0, grounded_count / len(response_words)))
        
        # Record metric
        AI_QUALITY_GROUNDING_SCORE.observe(score)
        return score

    @staticmethod
    def detect_hallucination(response_text: str, context_chunks: List[str], threshold: float = 0.3) -> bool:
        """
        Detects potential hallucination if grounding score falls below threshold when context was provided.
        """
        if not context_chunks:
            return False  # Zero context provided, general knowledge response
        score = AIQualityMonitor.calculate_grounding_score(response_text, context_chunks)
        is_hallucination = score < threshold
        if is_hallucination:
            logger.warning(f"Potential hallucination detected (Grounding Score: {score:.2f})")
        return is_hallucination

    @staticmethod
    def verify_refusal_correctness(response_text: str, has_retrieved_context: bool) -> bool:
        """
        Verifies that unanswerable/missing context queries result in appropriate refusal messages.
        """
        refusal_phrases = [
            "information not found",
            "not mentioned in the retrieved documents",
            "cannot answer based on the provided context",
            "no relevant documents"
        ]
        text_lower = response_text.lower()
        contains_refusal = any(phrase in text_lower for phrase in refusal_phrases)
        
        if not has_retrieved_context:
            return contains_refusal
        return not contains_refusal

    @staticmethod
    def verify_prompt_injection_isolation(formatted_prompt: str) -> bool:
        """
        Verifies that retrieved context chunks are strictly wrapped in quote boundaries.
        """
        has_start_tag = "<retrieved_context>" in formatted_prompt or "<context>" in formatted_prompt
        has_end_tag = "</retrieved_context>" in formatted_prompt or "</context>" in formatted_prompt
        return has_start_tag and has_end_tag
