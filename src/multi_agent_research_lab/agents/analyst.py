import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = AgentName.ANALYST

    def __init__(self) -> None:
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        logger.info("Analyst running...")

        if not state.research_notes:
            state.analysis_notes = "No research notes available to analyze."
            return state

        system_prompt = (
            "You are an Analyst Agent. Your job is to take raw research notes "
            "and synthesize them into structured insights. "
            "Extract key claims, compare viewpoints, and "
            "flag any weak evidence or conflicting information. "
            "Produce clear, structured analysis notes."
        )
        user_prompt = f"Query: {state.request.query}\n\nResearch Notes:\n{state.research_notes}"

        response = self.llm.complete(system_prompt, user_prompt)
        state.analysis_notes = response.content

        state.add_trace_event(
            self.name, {"analysis_length": len(response.content), "cost_usd": response.cost_usd}
        )

        return state
