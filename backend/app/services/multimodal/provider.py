import base64
import io
import logging
import httpx
from PIL import Image
from app.core.config import settings
from app.services.multimodal.base import MultimodalProvider

logger = logging.getLogger("nova-ai.multimodal.provider")

class OpenAIVisionProvider(MultimodalProvider):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def analyze(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        # Convert bytes to base64 data url
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{base64_image}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": settings.VISION_MODEL or "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        url = f"{self.base_url}/chat/completions"
        logger.info(f"Dispatching OpenAI Vision request to {url} using model {settings.VISION_MODEL}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"OpenAI Vision returned error status {response.status_code}: {response.text}")
                    return "NOVA couldn't complete the image analysis due to a provider API error."
                
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "No analysis content returned.")
                return "No analysis content returned."
        except Exception as exc:
            logger.exception(f"HTTP exception during vision analysis: {exc}")
            return "NOVA couldn't complete the image analysis due to a network connection error."


class MockVisionProvider(MultimodalProvider):
    async def analyze(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        logger.info("Executing MockVisionProvider analysis.")
        
        # Analyze image dimension metrics using Pillow
        width, height = 0, 0
        img_format = "UNKNOWN"
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                width, height = img.size
                img_format = img.format or "UNKNOWN"
        except Exception as err:
            logger.error(f"Failed to read image bytes via Pillow: {err}")
            
        prompt_lower = prompt.lower()
        
        # Create a dynamic mock response based on the prompt keywords and Pillow metadata
        if "diagram" in prompt_lower or "architecture" in prompt_lower:
            analysis_text = (
                f"### Image Analysis (Simulated)\n\n"
                f"I have inspected the uploaded **{img_format}** image (dimensions: `{width}x{height}` pixels).\n\n"
                f"This image appears to represent a technical software architecture diagram:\n"
                f"- **Frontend Interface**: Linked via a stateful client layer to dynamic router endpoints.\n"
                f"- **Orchestration Layer**: Implements a pipeline router separating normal, RAG, search, and research flows.\n"
                f"- **Data Infrastructure**: Powered by PostgreSQL database storage with pgvector vector extensions.\n\n"
                f"The diagram highlights a clean unidirectional flow from user prompts down to final citations."
            )
        elif "chart" in prompt_lower or "graph" in prompt_lower or "data" in prompt_lower:
            analysis_text = (
                f"### Image Analysis (Simulated)\n\n"
                f"I have inspected the uploaded **{img_format}** image (dimensions: `{width}x{height}` pixels).\n\n"
                f"This image shows a line graph tracking system performance metrics:\n"
                f"- **X-Axis**: Represents elapsed time intervals (seconds/steps).\n"
                f"- **Y-Axis**: Measures response latency (milliseconds).\n"
                f"- **Data Trend**: Displays a sharp latency dip from 240ms down to 45ms immediately following database query indexing.\n\n"
                f"The chart validates the efficiency gains of structured vector caching."
            )
        elif "text" in prompt_lower or "read" in prompt_lower or "screenshot" in prompt_lower:
            analysis_text = (
                f"### Image Analysis (Simulated)\n\n"
                f"I have inspected the uploaded **{img_format}** image (dimensions: `{width}x{height}` pixels).\n\n"
                f"The text extracted from this screenshot reads:\n"
                f"> *\"NOVA AI Architecture: Adapt, Ground, and Stream. Nova AI Core Platform v10.0.0\"*\n\n"
                f"No other readable text blocks were identified in the image background."
            )
        else:
            analysis_text = (
                f"### Image Analysis (Simulated)\n\n"
                f"I have inspected the uploaded **{img_format}** image (dimensions: `{width}x{height}` pixels).\n\n"
                f"**Prompt**: *\"{prompt}\"*\n\n"
                f"This image shows a high-fidelity visual layout. The visual hierarchy utilizes deep navy colors, glassmorphism panels, and a titanium outline, aligning with the visual identity of NOVA AI."
            )
            
        return analysis_text


def get_multimodal_provider() -> MultimodalProvider:
    if settings.AI_API_KEY:
        logger.info("Initializing OpenAIVisionProvider.")
        return OpenAIVisionProvider(api_key=settings.AI_API_KEY, base_url=settings.AI_BASE_URL)
    
    logger.info("Fallback to MockVisionProvider.")
    return MockVisionProvider()
