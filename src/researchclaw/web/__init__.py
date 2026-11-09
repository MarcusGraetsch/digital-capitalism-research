"""Web search, crawling, and content extraction layer.

Provides unified access to:
- **BatchScraper**: concurrent batch fetching + Markdown extraction (httpx + trafilatura)
- **Crawl4AI**: Web page → Markdown extraction
- **Tavily**: AI-native web search API
- **scholarly**: Google Scholar search
- **PDF extraction**: Full-text from PDF files

Public API
----------
- ``WebSearchAgent`` — orchestrates all web capabilities
- ``BatchScraper`` — free batch scraper, no API key required
- ``WebCrawler`` — Crawl4AI wrapper
- ``WebSearchClient`` — Tavily search wrapper
- ``GoogleScholarClient`` — scholarly wrapper
- ``PDFExtractor`` — PDF text extraction
"""

from researchclaw.web.batch_scraper import BatchScraper
from researchclaw.web.crawler import WebCrawler
from researchclaw.web.search import WebSearchClient
from researchclaw.web.scholar import GoogleScholarClient
from researchclaw.web.pdf_extractor import PDFExtractor
from researchclaw.web.agent import WebSearchAgent

__all__ = [
    "BatchScraper",
    "WebCrawler",
    "WebSearchClient",
    "GoogleScholarClient",
    "PDFExtractor",
    "WebSearchAgent",
]
