import logging
from typing import List, Dict

logger = logging.getLogger("nova-ai.context")

def truncate_context_messages(messages: List[Dict[str, str]], max_chars: int = 16000) -> List[Dict[str, str]]:
    """
    Truncates a list of chat messages to fit within max_chars.
    Always preserves the system prompt (if present) and keeps the most recent messages.
    """
    system_prompt = None
    other_messages = []
    
    for msg in messages:
        if msg.get("role") == "system":
            system_prompt = msg
        else:
            other_messages.append(msg)
            
    # Calculate initial size
    char_count = len(system_prompt["content"]) if system_prompt else 0
    truncated = []
    
    # Iterate other messages from newest to oldest
    for msg in reversed(other_messages):
        msg_len = len(msg.get("content", ""))
        if char_count + msg_len > max_chars:
            logger.info(f"Context truncation: reached limit of {max_chars} chars. Truncated older messages.")
            break
        truncated.insert(0, msg)
        char_count += msg_len
        
    if system_prompt:
        truncated.insert(0, system_prompt)
        
    return truncated
