"""
Rolling latency instrumentation (Phase 4).

Records end-to-end pipeline timing (capture → send) and exposes
percentile stats for the /debug/latency endpoint.

Usage:
    from latency_monitor import record_latency, get_latency_stats
"""
import time
from collections import deque

_latencies: deque = deque(maxlen=500)   # ring buffer, newest at right


def record_latency(captured_at_ms: float, sent_at_ms: float | None = None) -> None:
    """
    Record one round-trip sample.

    Parameters
    ----------
    captured_at_ms : float  — performance.now() value attached by the frontend
                              (milliseconds, arbitrary epoch)
    sent_at_ms     : float  — server wall-clock time in ms when the feedback
                              emit was called; defaults to now() if omitted
    """
    if sent_at_ms is None:
        sent_at_ms = time.time() * 1000
    total_ms = sent_at_ms - captured_at_ms
    # Sanity-guard: ignore impossible values (clock skew, reconnect artefacts)
    if 0 < total_ms < 10_000:
        _latencies.append(total_ms)


def get_latency_stats() -> dict | None:
    """Return p50/p95/p99/max/mean over the rolling window, or None if empty."""
    if not _latencies:
        return None
    data = sorted(_latencies)
    n = len(data)

    def pct(p):
        idx = min(int(n * p / 100), n - 1)
        return round(data[idx], 1)

    return {
        "p50":     pct(50),
        "p95":     pct(95),
        "p99":     pct(99),
        "max":     round(data[-1], 1),
        "mean":    round(sum(data) / n, 1),
        "samples": n,
    }
