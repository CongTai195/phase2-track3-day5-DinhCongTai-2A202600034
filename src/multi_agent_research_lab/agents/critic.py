import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self) -> None:
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        logger.info("Critic running...")

        if not state.final_answer or not state.research_notes:
            return state

        system_prompt = (
            "You are a Critic Agent. Your job is to review a research assistant's final answer "
            "against the raw research notes to check for hallucinations, missing citations, "
            "and factual inaccuracies.\n"
            "Provide a brief critique and a score from 0-10 on accuracy."
        )
        user_prompt = (
            f"Research Notes:\n{state.research_notes}\n\n"
            f"Final Answer:\n{state.final_answer}\n\n"
            "Please provide your critique."
        )

        response = self.llm.complete(system_prompt, user_prompt)

        state.add_trace_event(
            self.name,
            {
                "critique": response.content,
                "cost_usd": response.cost_usd,
            },
        )

        return state
