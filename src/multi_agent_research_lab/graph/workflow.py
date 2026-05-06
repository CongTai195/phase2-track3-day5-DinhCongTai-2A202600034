import logging
from typing import Any

from langgraph.graph import END, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()
        self.graph: Any = self.build()

    def build(self) -> Any:
        """Create a LangGraph graph."""
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node(AgentName.SUPERVISOR, self.supervisor.run)
        workflow.add_node(AgentName.RESEARCHER, self.researcher.run)
        workflow.add_node(AgentName.ANALYST, self.analyst.run)
        workflow.add_node(AgentName.WRITER, self.writer.run)
        workflow.add_node(AgentName.CRITIC, self.critic.run)

        # Set entry point
        workflow.set_entry_point(AgentName.SUPERVISOR)

        # Add edges back to supervisor
        workflow.add_edge(AgentName.RESEARCHER, AgentName.SUPERVISOR)
        workflow.add_edge(AgentName.ANALYST, AgentName.SUPERVISOR)
        workflow.add_edge(AgentName.WRITER, AgentName.SUPERVISOR)
        workflow.add_edge(AgentName.CRITIC, AgentName.SUPERVISOR)

        # Add conditional edges from supervisor
        def route_from_supervisor(state: ResearchState) -> str:
            # The supervisor appends the next route to state.route_history
            if not state.route_history:
                return END
            last_route = state.route_history[-1]
            if last_route == "done":
                return END
            return last_route

        workflow.add_conditional_edges(
            AgentName.SUPERVISOR,
            route_from_supervisor,
            {
                AgentName.RESEARCHER: AgentName.RESEARCHER,
                AgentName.ANALYST: AgentName.ANALYST,
                AgentName.WRITER: AgentName.WRITER,
                AgentName.CRITIC: AgentName.CRITIC,
                END: END,
            },
        )

        return workflow.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        logger.info(f"Starting workflow for query: {state.request.query}")

        # Invoke the graph. Since ResearchState is a Pydantic model, LangGraph handles it.
        # However, LangGraph might require dict if not properly typed,
        # but StateGraph(ResearchState) usually works.
        # Wait, LangGraph 0.2 `StateGraph` requires passing the object. Let's run it.
        result_dict = self.graph.invoke(state)

        # LangGraph returns the final state (can be dict or the ResearchState object)
        if isinstance(result_dict, ResearchState):
            return result_dict
        return ResearchState.model_validate(result_dict)
