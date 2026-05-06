import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = AgentName.WRITER

    def __init__(self) -> None:
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        logger.info("Writer running...")

        if not state.analysis_notes and not state.research_notes:
            state.final_answer = "I could not find enough information to answer the query."
            return state

        system_prompt = (
            "You are a Writer Agent. Your job is to synthesize research notes "
            "and analysis into a clear, comprehensive final answer for the user.\n"
            f"The target audience is: {state.request.audience}.\n"
            "Include inline citations if possible based on the source titles."
        )
        user_prompt = (
            f"Query: {state.request.query}\n\n"
            f"Research Notes:\n{state.research_notes}\n\n"
            f"Analysis Notes:\n{state.analysis_notes}\n\n"
            "Please write the final response."
        )

        response = self.llm.complete(system_prompt, user_prompt)
        state.final_answer = response.content

        state.add_trace_event(
            self.name, {"answer_length": len(response.content), "cost_usd": response.cost_usd}
        )

        return state
