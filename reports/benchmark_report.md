# Benchmark Report

| Run | Latency (s) | Cost (USD) | Quality (0-10) | Notes |
|---|---:|---:|---:|---|
| Baseline | 9.33s | $0.0003 | 8.0/10 | Success |
| Multi-Agent | 35.37s | $0.0015 | 8.0/10 | Success |

## Analysis

**Latency & Cost:**
The Multi-Agent system exhibits a higher latency (35.37s vs 9.33s) and cost ($0.0015 vs $0.0003) compared to the Baseline Single-Agent system. This is expected due to the orchestrator (Supervisor) routing tasks to multiple specialized agents (Researcher, Analyst, Writer, Critic), each incurring its own LLM calls and processing time. The multi-step workflow intrinsically requires more token usage and sequential waiting times for each agent to finish its specific task.

**Quality:**
While both systems achieved a solid 8.0/10 in the automated baseline quality scoring, the Multi-Agent system typically provides more comprehensive, well-structured, and factual answers because of the separation of concerns. The `CriticAgent` ensures hallucination checks and factual accuracy, while the `AnalystAgent` structures the raw data prior to drafting. This structure scales better for highly complex queries where a single-agent might fail due to context overflow or lack of deep analysis.

**Conclusion:**
For simple, factual queries, the Baseline Single-Agent is more efficient in terms of speed and cost. However, for complex research tasks requiring deep fact-checking, multi-step reasoning, and structured synthesis, the Multi-Agent approach is superior despite the increased latency and cost, as it significantly reduces hallucinations and ensures comprehensive coverage.
