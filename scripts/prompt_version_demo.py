from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=["baseline", "candidate", "production"])
    parser.add_argument("--correlation-id", required=True)
    args = parser.parse_args()
    load_dotenv(REPO_ROOT / ".env")
    os.environ["LANGFUSE_PROMPT_LABEL"] = args.label

    from app.agent import LabAgent
    from app.tracing import get_langfuse_client

    result = LabAgent().run(
        user_id="cp2-demo-user",
        session_id="cp2-prompt-comparison",
        feature="qa",
        message="Explain why correlation IDs help incident investigation.",
        correlation_id=args.correlation_id,
    )
    get_langfuse_client().flush()
    print(
        f"label={args.label} correlation_id={args.correlation_id} "
        f"latency_ms={result.latency_ms} tokens={result.tokens_in + result.tokens_out}"
    )


if __name__ == "__main__":
    main()
