import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

logger = logging.getLogger(__name__)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = AgentName.RESEARCHER

    def __init__(self) -> None:
        self.search_client = SearchClient()
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        logger.info(f"Researcher running for query: {state.request.query}")

        # 1. Search for documents
        sources = self.search_client.search(
            state.request.query, max_results=state.request.max_sources
        )
        state.sources.extend(sources)

        if not sources:
            logger.warning("No sources found.")
            state.research_notes = "No sources were found for this query."
            state.add_trace_event(self.name, {"sources_count": 0, "status": "no_results"})
            return state

        sources_text = "\n\n".join(
            [f"Source {i + 1}: {doc.title}\n{doc.snippet}" for i, doc in enumerate(sources)]
        )

        # 3. Create research notes
        system_prompt = (
            "You are a Researcher Agent. Your task is to extract relevant facts "
            "and information from the provided sources based on the user's query.\n"
            "Produce concise, bulleted research notes. Do not write a final essay, just notes."
        )
        user_prompt = f"Query: {state.request.query}\n\nSources:\n{sources_text}"

        response = self.llm.complete(system_prompt, user_prompt)
        state.research_notes = response.content

        state.add_trace_event(
            self.name,
            {
                "sources_count": len(sources),
                "notes_length": len(response.content),
                "cost_usd": response.cost_usd,
            },
        )

        return state
