from __future__ import annotations

from app.dashboard import dashboard_metrics, render_dashboard


def test_dashboard_has_exactly_six_runtime_panels() -> None:
    rendered = render_dashboard([])

    assert rendered.count('class="panel"') == 6
    assert "Time range: last 60 minutes" in rendered
    assert "Auto refresh: 30 seconds" in rendered
    assert rendered.count("SLO/threshold:") == 6


def test_dashboard_calculates_all_six_metric_groups() -> None:
    records = [
        {"event": "request_received"},
        {
            "event": "response_sent",
            "latency_ms": 100,
            "ttft_ms": 25,
            "tool_name": "retrieval",
            "tool_success": True,
            "cost_usd": 0.01,
            "tokens_in": 10,
            "tokens_out": 20,
            "quality_score": 0.8,
        },
    ]

    metrics = dashboard_metrics(records)

    assert set(metrics) == {"latency", "traffic", "errors", "cost", "tokens", "quality"}
    assert metrics["latency"]["p95"] == 100
    assert metrics["errors"]["retrieval_success_pct"] == 100
    assert metrics["cost"]["total"] == 0.01
    assert metrics["tokens"] == {"input": 10, "output": 20}
    assert metrics["quality"]["mean"] == 0.8
