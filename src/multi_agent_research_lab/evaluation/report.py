from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown."""
    lines = [
        "# Benchmark Report",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality (0-10) | Notes |",
        "|---|---:|---:|---:|---|",
    ]

    for item in metrics:
        cost = f"${item.estimated_cost_usd:.4f}" if item.estimated_cost_usd is not None else "N/A"
        quality = f"{item.quality_score:.1f}/10" if item.quality_score is not None else "N/A"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f}s | {cost} | {quality} | {item.notes} |"
        )

    return "\n".join(lines) + "\n"
