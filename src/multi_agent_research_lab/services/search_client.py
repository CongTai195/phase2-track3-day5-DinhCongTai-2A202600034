import json
import logging
import urllib.parse
import urllib.request

from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Search client using Wikipedia API (no API key required)."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query using Wikipedia."""
        logger.info(f"Searching Wikipedia for: {query}")

        # We'll use the Wikipedia Action API to do a simple text search
        safe_query = urllib.parse.quote(query)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_query}&utf8=&format=json&srlimit={max_results}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MultiAgentResearchLab/1.0"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            results = []
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                snippet = (
                    item.get("snippet", "")
                    .replace('<span class="searchmatch">', "")
                    .replace("</span>", "")
                )
                page_id = item.get("pageid", "")

                # Fetch summary for better content than just snippet
                summary_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&redirects=1&pageids={page_id}&format=json"
                try:
                    s_req = urllib.request.Request(
                        summary_url, headers={"User-Agent": "MultiAgentResearchLab/1.0"}
                    )
                    with urllib.request.urlopen(s_req) as s_response:
                        s_data = json.loads(s_response.read().decode())
                        pages = s_data.get("query", {}).get("pages", {})
                        if str(page_id) in pages:
                            snippet = pages[str(page_id)].get("extract", snippet)
                except Exception as e:
                    logger.debug(f"Failed to fetch summary for {title}: {e}")

                # Limit snippet length
                if len(snippet) > 1500:
                    snippet = snippet[:1500] + "..."

                doc = SourceDocument(
                    title=title,
                    url=f"https://en.wikipedia.org/?curid={page_id}",
                    snippet=snippet,
                    metadata={"source": "Wikipedia", "pageid": page_id},
                )
                results.append(doc)
            return results
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return []
