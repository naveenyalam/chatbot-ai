import logging
import httpx
from datetime import datetime
from typing import List
from app.core.config import settings
from app.services.search.base import SearchProvider, SearchResult

logger = logging.getLogger("nova-ai.search.provider")

class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic"
        }
        logger.info(f"Dispatching Tavily search request for query: {query}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.url, json=payload)
                if response.status_code != 200:
                    logger.error(f"Tavily returned error status {response.status_code}: {response.text}")
                    return []
                
                data = response.json()
                results = []
                for item in data.get("results", []):
                    results.append(SearchResult(
                        title=item.get("title", "Untitled Source"),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        source="Tavily Web Search",
                        published_at=datetime.utcnow()  # Tavily basic usually has no publish date; fallback to utcnow
                    ))
                return results
        except Exception as exc:
            logger.exception(f"HTTP error during Tavily search execution: {exc}")
            return []


class MockSearchProvider(SearchProvider):
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        logger.info(f"Running fallback MockSearchProvider for query: {query}")
        
        # Simulate realistic web search responses dynamically based on query tokens
        query_lower = query.lower()
        
        simulated_corpus = [
            {
                "title": "OpenAI Launches Advanced Reasoning Model Updates",
                "url": "https://openai.com/news/advanced-reasoning-models",
                "snippet": "OpenAI has officially launched updates to its new o1 reasoning models. The o1 models utilize advanced chain-of-thought processing to solve complex debugging and mathematical queries, yielding major benchmark improvements.",
                "source": "OpenAI Newsroom",
                "keywords": ["openai", "ai", "model", "reasoning", "coding"]
            },
            {
                "title": "Linear App Design Philosophy: Speed and Precision",
                "url": "https://linear.app/readme/design-philosophy",
                "snippet": "Linear's workspace product is built on principles of efficiency, keyboard-driven navigation, and high-fidelity rendering. The application features titanium borders and minimal layouts that allow developer teams to track issues with extreme precision.",
                "source": "Linear Readme",
                "keywords": ["linear", "design", "titanium", "layout", "speed"]
            },
            {
                "title": "Google Deepmind Announces Dynamic Intelligence Architecture",
                "url": "https://deepmind.google/discover/dynamic-intelligence",
                "snippet": "Google Deepmind researchers introduced Dynamic Intelligence systems. By applying dynamic parameter morphing, these systems adapt context prompts to fluid workflows, optimizing RAG grounding databases without resource overhead.",
                "source": "Google Deepmind Research",
                "keywords": ["deepmind", "dynamic", "intelligence", "architecture", "nova"]
            },
            {
                "title": "State of Autonomous Driving Benchmarks 2026",
                "url": "https://autonomous-reports.org/benchmarks-2026",
                "snippet": "A comprehensive review of the latest autonomous driving platforms in 2026 highlights massive leaps in vision-language models for navigation. Deep vision architectures successfully bypass edge-case hallucination issues.",
                "source": "Autonomous Reports Hub",
                "keywords": ["autonomous", "driving", "benchmarks", "car", "tesla"]
            },
            {
                "title": "W3C Document Standardizations and Web Accessibility",
                "url": "https://w3.org/TR/accessibility-standards",
                "snippet": "W3C released accessibility standards focusing on screen-reader compatibility and keyboard navigation. Standardized focus rings and responsive flexboxes ensure fluid user control across complex dashboard frames.",
                "source": "W3C Standards Council",
                "keywords": ["accessibility", "w3c", "keyboard", "focus", "aria"]
            }
        ]
        
        matches = []
        for doc in simulated_corpus:
            if any(kw in query_lower for kw in doc["keywords"]):
                matches.append(doc)
        
        # Default fallback results if no keywords match
        if not matches:
            matches = simulated_corpus[:3]
            
        results = []
        for idx, doc in enumerate(matches[:max_results]):
            results.append(SearchResult(
                title=doc["title"],
                url=doc["url"],
                snippet=doc["snippet"],
                source=doc["source"],
                published_at=datetime.utcnow()
            ))
        return results


def get_search_provider() -> SearchProvider:
    if settings.SEARCH_PROVIDER == "tavily" and settings.SEARCH_API_KEY:
        logger.info("Initializing TavilySearchProvider.")
        return TavilySearchProvider(api_key=settings.SEARCH_API_KEY)
    
    logger.info("Fallback to MockSearchProvider.")
    return MockSearchProvider()
