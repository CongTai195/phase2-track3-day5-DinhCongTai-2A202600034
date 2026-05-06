"""Tracing hooks."""

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from langsmith import trace


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context augmented with LangSmith."""
    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}

    with trace(name, "chain", inputs=attributes) as run_tree:
        try:
            yield span
            run_tree.end(outputs=span)
        except Exception as e:
            run_tree.end(error=str(e))
            raise
        finally:
            span["duration_seconds"] = perf_counter() - started
