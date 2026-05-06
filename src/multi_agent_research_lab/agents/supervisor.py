import logging

from pydantic import BaseModel, Field

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class RouteDecision(BaseModel):
    next_agent: str = Field(
        description="The next agent to route to: 'researcher', 'analyst', "
        "'writer', 'critic', or 'done'."
    )
    reasoning: str = Field(description="Why this agent was chosen based on the current state.")


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = AgentName.SUPERVISOR

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        logger.info(f"Supervisor evaluating state (iteration {state.iteration})")

        if state.iteration >= self.settings.max_iterations:
            logger.warning("Max iterations reached. Forcing done.")
            state.record_route("done")
            state.add_trace_event(self.name, {"decision": "done", "reason": "max_iterations"})
            return state

        system_prompt = (
            "You are a Supervisor Agent coordinating a research workflow. "
            "Your job is to route to the correct next agent based on the current state.\n"
            "Options: 'researcher', 'analyst', 'writer', 'done'.\n\n"
            "- Route to 'researcher' if you need to gather information (e.g. no sources yet).\n"
            "- Route to 'analyst' if sources are gathered but not analyzed.\n"
            "- Route to 'writer' if analysis is complete but final answer is not written.\n"
            "- Route to 'done' ONLY if the final answer is complete and satisfactory."
        )

        user_prompt = (
            f"Query: {state.request.query}\n"
            f"Sources count: {len(state.sources)}\n"
            f"Has research notes: {bool(state.research_notes)}\n"
            f"Has analysis notes: {bool(state.analysis_notes)}\n"
            f"Has final answer: {bool(state.final_answer)}\n\n"
            "Decide the next step."
        )

        response = self.llm.complete(system_prompt, user_prompt, response_format=RouteDecision)
        decision: RouteDecision = response.content

        # Fallback in case LLM goes rogue
        next_route = decision.next_agent.lower()
        if next_route not in ["researcher", "analyst", "writer", "done"]:
            logger.error(f"Invalid route chosen: {next_route}. Forcing done.")
            next_route = "done"

        logger.info(f"Supervisor decided to route to: {next_route} (Reason: {decision.reasoning})")
        state.record_route(next_route)
        state.add_trace_event(
            self.name,
            {
                "decision": next_route,
                "reason": decision.reasoning,
                "cost_usd": response.cost_usd,
            },
        )

        return state
