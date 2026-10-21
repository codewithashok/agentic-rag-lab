"""
STAGE 14: Distributed In-Memory Span Tracer
-------------------------------------------
Captures structured execution spans with timing, token usage,
and step status across the entire multi-agent pipeline.
"""

import time
from typing import Dict, Any, List
from contextlib import contextmanager


class PipelineTracer:
    """Collects hierarchical timing and execution telemetry."""

    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.spans: List[Dict[str, Any]] = []

    @contextmanager
    def span(self, name: str, metadata: Dict[str, Any] = None):
        """Context manager to measure latency and record step status."""
        start_time = time.perf_counter()
        span_record = {
            "name": name,
            "metadata": metadata or {},
            "status": "RUNNING",
            "start_time": start_time
        }
        try:
            yield span_record
            span_record["status"] = "SUCCESS"
        except Exception as e:
            span_record["status"] = "FAILED"
            span_record["error"] = str(e)
            raise e
        finally:
            elapsed = time.perf_counter() - start_time
            span_record["latency_ms"] = round(elapsed * 1000, 2)
            self.spans.append(span_record)

    def get_summary(self) -> Dict[str, Any]:
        """Returns consolidated trace metrics."""
        total_latency = sum(s["latency_ms"] for s in self.spans)
        return {
            "trace_id": self.trace_id,
            "total_latency_ms": round(total_latency, 2),
            "step_count": len(self.spans),
            "spans": self.spans
        }