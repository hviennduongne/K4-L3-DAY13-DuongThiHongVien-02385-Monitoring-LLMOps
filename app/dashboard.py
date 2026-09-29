from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from .logging_config import LOG_PATH


WINDOW_MINUTES = 60


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def load_recent_records(path: Path = LOG_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = _parse_ts(record.get("ts", ""))
        if timestamp is not None and timestamp >= cutoff:
            records.append(record)
    return records


def dashboard_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    requests = [item for item in records if item.get("event") == "request_received"]
    responses = [item for item in records if item.get("event") == "response_sent"]
    failures = [item for item in records if item.get("event") == "request_failed"]
    latencies = [float(item["latency_ms"]) for item in responses if item.get("latency_ms") is not None]
    ttfts = [float(item["ttft_ms"]) for item in responses if item.get("ttft_ms") is not None]
    retrievals = [item for item in records if item.get("tool_name") == "retrieval" and item.get("tool_success") is not None]
    successes = sum(item.get("tool_success") is True for item in retrievals)
    error_types: dict[str, int] = {}
    for item in failures:
        name = str(item.get("error_type") or "unknown")
        error_types[name] = error_types.get(name, 0) + 1
    costs = [float(item.get("cost_usd", 0)) for item in responses]
    qualities = [float(item["quality_score"]) for item in responses if item.get("quality_score") is not None]
    return {
        "latency": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
            "ttft_p95": _percentile(ttfts, 95),
        },
        "traffic": {"count": len(requests), "rate_per_minute": len(requests) / WINDOW_MINUTES},
        "errors": {
            "error_rate_pct": len(failures) / len(requests) * 100 if requests else 0.0,
            "breakdown": error_types,
            "retrieval_success_pct": successes / len(retrievals) * 100 if retrievals else 0.0,
        },
        "cost": {"total": sum(costs)},
        "tokens": {
            "input": sum(int(item.get("tokens_in", 0)) for item in responses),
            "output": sum(int(item.get("tokens_out", 0)) for item in responses),
        },
        "quality": {"mean": mean(qualities) if qualities else 0.0},
    }


def render_dashboard(records: list[dict[str, Any]]) -> str:
    metrics = dashboard_metrics(records)
    panels = [
        ("Latency percentiles and TTFT", "ms", "P95 ≤ 3000 ms", f"P50 {metrics['latency']['p50']:.0f} · P95 {metrics['latency']['p95']:.0f} · P99 {metrics['latency']['p99']:.0f} · TTFT P95 {metrics['latency']['ttft_p95']:.0f}"),
        ("Request traffic", "requests/min", "Rate ≥ 1 request/min", f"{metrics['traffic']['count']} requests · {metrics['traffic']['rate_per_minute']:.2f}/min"),
        ("Error rate and retrieval success", "%", "Error ≤ 2% · Retrieval ≥ 90%", f"Errors {metrics['errors']['error_rate_pct']:.2f}% · Retrieval {metrics['errors']['retrieval_success_pct']:.2f}% · Breakdown {html.escape(json.dumps(metrics['errors']['breakdown']))}"),
        ("Cost over time", "USD", "Total ≤ $2.50", f"${metrics['cost']['total']:.6f}"),
        ("Input and output tokens", "tokens", "Total by field ≤ 50,000", f"Input {metrics['tokens']['input']:,} · Output {metrics['tokens']['output']:,}"),
        ("Quality proxy", "score 0–1", "Mean ≥ 0.75", f"Mean {metrics['quality']['mean']:.3f}"),
    ]
    cards = "".join(
        f'''<section class="panel"><h2>{title}</h2><div class="value">{value}</div><div class="unit">Unit: {unit}</div><div class="threshold">SLO/threshold: {threshold}</div></section>'''
        for title, unit, threshold, value in panels
    )
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="30"><title>K4-L3A LLMOps Dashboard</title><style>
    :root {{ color-scheme: dark; font-family: Inter, system-ui, sans-serif; background:#07111f; color:#e8f0ff; }}
    body {{ margin:0; padding:22px; background:radial-gradient(circle at top right,#163054,#07111f 45%); }}
    header {{ display:flex; justify-content:space-between; align-items:end; margin-bottom:22px; }}
    h1 {{ margin:0; font-size:28px; }} .meta {{ color:#9eb3cf; text-align:right; font-size:13px; }}
    main {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
    .panel {{ min-height:130px; padding:18px; border:1px solid #294668; border-radius:14px; background:rgba(13,29,49,.92); box-shadow:0 8px 30px #0005; overflow-wrap:anywhere; }}
    h2 {{ color:#bcd3f5; font-size:16px; margin:0 0 18px; }} .value {{ font-size:20px; font-weight:700; line-height:1.35; }}
    .unit {{ color:#8fa6c4; margin-top:16px; font-size:13px; }} .threshold {{ color:#77e0a7; border-top:1px dashed #3b5c79; margin-top:12px; padding-top:12px; font-size:13px; }}
    @media(max-width:900px) {{ main {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} header {{ align-items:start; }} }}
    @media(max-width:540px) {{ main {{ grid-template-columns:1fr; }} }}
    </style></head><body><header><div><h1>K4-L3A Day 13 Monitoring &amp; LLMOps</h1><div>Source: data/logs.jsonl</div></div><div class="meta">Time range: last 60 minutes<br>Auto refresh: 30 seconds<br>{generated}</div></header><main>{cards}</main></body></html>'''
