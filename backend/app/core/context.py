import logging
import re
from typing import List, Dict

logger = logging.getLogger("nova-ai.context")

def compress_old_messages(messages: List[Dict[str, str]], keep_full_count: int = 4) -> List[Dict[str, str]]:
    """
    Compresses older messages in the history to reduce prompt size.
    Keeps the system prompt and the most recent `keep_full_count` messages intact.
    For older messages:
    - Strips large markdown code blocks (replacing them with [Code Block omitted for brevity]).
    - Truncates long text blocks to keep only the core context.
    """
    system_prompt = None
    other_messages = []
    
    for msg in messages:
        if msg.get("role") == "system":
            system_prompt = msg
        else:
            other_messages.append(msg)
            
    if len(other_messages) <= keep_full_count:
        return messages
        
    compressed = []
    compress_limit = len(other_messages) - keep_full_count
    
    for idx, msg in enumerate(other_messages):
        if idx < compress_limit:
            content = msg.get("content", "")
            # Replace markdown code blocks
            code_block_pattern = re.compile(r"```[a-zA-Z]*\n[\s\S]*?\n```")
            cleaned_content = code_block_pattern.sub("[Code Block omitted for brevity]", content)
            
            # Truncate text if still too long
            if len(cleaned_content) > 300:
                cleaned_content = cleaned_content[:300] + "... [truncated for context brevity]"
                
            compressed.append({
                "role": msg["role"],
                "content": cleaned_content
            })
        else:
            compressed.append(msg)
            
    if system_prompt:
        compressed.insert(0, system_prompt)
        
    return compressed

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
