from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

Runner = Callable[[str], ResearchState]


def _score_quality(query: str, answer: str | None) -> float:
    if not answer:
        return 0.0
    llm = LLMClient()
    prompt = (
        "You are an evaluator grading a research assistant's response on a scale of 0 to 10.\n"
        "Criteria:\n- Accuracy and relevance\n- Clarity and depth\n"
        "- Presence of citations/sources\n\n"
        "Respond ONLY with a single number from 0 to 10."
    )
    user_prompt = f"Query: {query}\n\nAnswer: {answer}"
    try:
        response = llm.complete(prompt, user_prompt)
        return float(response.content.strip())
    except Exception:
        return 5.0  # fallback


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, and quality."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    total_cost = 0.0
    for event in state.trace:
        cost = event.get("payload", {}).get("cost_usd")
        if cost is not None:
            total_cost += cost

    quality = _score_quality(query, state.final_answer)

    notes = "Success" if state.final_answer else "Failed"

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        quality_score=quality,
        notes=notes,
    )
    return state, metrics
