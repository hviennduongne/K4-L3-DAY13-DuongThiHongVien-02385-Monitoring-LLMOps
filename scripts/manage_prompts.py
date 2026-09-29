from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langfuse import get_client


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PROMPT_NAME = "day13-chat"
V1 = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
V2 = (
    "Answer concisely using only the supplied docs.\n"
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
)


def prompt_versions(client) -> dict[int, object]:
    response = client.api.prompts.list(name=PROMPT_NAME, limit=100)
    version_numbers = {
        version
        for item in response.data
        if item.name == PROMPT_NAME
        for version in item.versions
    }
    return {
        version: client.get_prompt(
            PROMPT_NAME,
            version=version,
            type="text",
            cache_ttl_seconds=0,
        )
        for version in version_numbers
    }


def initialize(client) -> tuple[int, int]:
    versions = prompt_versions(client)
    if versions:
        raise RuntimeError(
            f"{PROMPT_NAME} already has versions {sorted(versions)}; refusing to create duplicates"
        )
    v1 = client.create_prompt(
        name=PROMPT_NAME,
        type="text",
        prompt=V1,
        labels=["baseline", "production"],
        commit_message="CP2 baseline prompt",
    )
    v2 = client.create_prompt(
        name=PROMPT_NAME,
        type="text",
        prompt=V2,
        labels=["candidate"],
        commit_message="CP2 candidate: concise, docs-only instruction",
    )
    return int(v1.version), int(v2.version)


def set_production(client, version: int) -> None:
    versions = prompt_versions(client)
    if version not in versions:
        raise RuntimeError(f"Prompt version {version} does not exist")
    labels = [label for label in versions[version].labels if label != "latest"]
    if "production" not in labels:
        labels.append("production")
    client.update_prompt(name=PROMPT_NAME, version=version, new_labels=labels)
    client.clear_prompt_cache()


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["initialize", "promote", "rollback", "status"])
    args = parser.parse_args()
    client = get_client()
    if not client.auth_check():
        raise RuntimeError("Langfuse authentication failed")

    if args.action == "initialize":
        v1, v2 = initialize(client)
        print(f"Created {PROMPT_NAME}: v{v1}=baseline,production; v{v2}=candidate")
    elif args.action == "promote":
        set_production(client, 2)
        print(f"Promoted {PROMPT_NAME} production -> v2")
    elif args.action == "rollback":
        set_production(client, 1)
        print(f"Rolled back {PROMPT_NAME} production -> v1")

    current = prompt_versions(client)
    print("Prompt labels:", [(version, item.labels) for version, item in sorted(current.items())])


if __name__ == "__main__":
    main()
