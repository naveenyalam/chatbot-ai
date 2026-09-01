import re
from typing import Tuple

IMAGE_INTENT_PATTERNS = [
    # Rule 1: Verb + Media Noun (image, picture, photo, illustration, artwork, etc.)
    r"^(?:please\s+)?(?:generate|create|make|draw|paint|show(?:\s+me)?|render|produce|give\s+me)\s+(?:an?\s+)?(?:ai\s+)?(?:beautiful|realistic|futuristic|detailed|hd|high\s+quality|3d|digital|stunning|scenic)?\s*(?:image|picture|photo|photograph|illustration|artwork|painting|graphic|drawing|render|visual|scenery)\s*(?:of|showing|with|for|depicting|featuring)?\s+(.+)$",
    
    # Rule 2: Direct Creation verb + adjective + subject (e.g. "create a beautiful house...")
    r"^(?:please\s+)?(?:generate|create|make|draw|paint)\s+(?:a|an)\s+(?:beautiful|realistic|futuristic|detailed|stunning|cyberpunk|scenic|watercolor)\s+(.+)$",
    
    # Rule 3: Draw / Paint verbs directly (e.g. "draw a robot working in a smart farm")
    r"^(?:please\s+)?(?:draw|paint|render)\s+(?:a|an|the)?\s*(.+)$",
    
    # Rule 4: Direct "image of" / "picture of" / "photo of"
    r"^(?:an?\s+)?(?:image|picture|photo|illustration|artwork|painting)\s+(?:of|showing|with|for|depicting)\s+(.+)$",
    
    # Rule 5: Slash command /image
    r"^\/image\s+(.+)$",
]

TEXT_EXCLUSIONS = [
    "code", "how to", "how does", "how do", "what is", "explain", "why", "tutorial", "function", "script",
    "library", "algorithm", "python", "javascript", "react", "html", "css", "api", "difference", "compare"
]

def detect_image_intent(prompt: str) -> Tuple[bool, str]:
    """
    Detects if the user prompt is requesting AI image generation.
    Returns a tuple of (is_image_intent, extracted_image_prompt).
    """
    if not prompt or not prompt.strip():
        return False, prompt

    clean_prompt = prompt.strip()
    lowered = clean_prompt.lower()

    # Exclude standard text programming, questions, or code requests that mention images casually
    if any(ex in lowered for ex in TEXT_EXCLUSIONS):
        if any(kw in lowered for kw in ["how", "code", "what", "explain", "why", "tutorial", "difference"]):
            return False, clean_prompt

    # If prompt ends with question mark and starts with question words, treat as normal text Q&A
    if clean_prompt.endswith("?") and re.match(r"^(?:how|what|why|where|when|can|could|would|is|are|do|does)\b", lowered):
        return False, clean_prompt

    for pattern in IMAGE_INTENT_PATTERNS:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if len(extracted) > 2:
                original_extracted = clean_prompt[match.start(1):match.end(1)].strip()
                return True, original_extracted if original_extracted else extracted

    return False, clean_prompt

