"""Serve the exact product browser assets for the ITER-005 V-002 copy audit.

This is not a product-validation launcher and cannot answer questions.  It gives
the exact ``WorldModelBrowserApplication`` a bounded static runner so a human
can inspect the product-owned Coverage wording without activating a model.
"""

from __future__ import annotations

import argparse
import json
from wsgiref.simple_server import WSGIRequestHandler, make_server

from software_world_model.interface.world_model_browser import (
    PublicRunnerError,
    WorldModelBrowserApplication,
)


class _CopyAuditRunner:
    def health(self) -> dict[str, object]:
        return {
            "status": "READY",
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "accepted_product_commit": "copy-audit",
            "production_activation": "NOT_EXECUTED",
        }

    def datasets(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "id": "COPY_AUDIT_R1_R2",
                "label": "V-002 exact Coverage copy",
                "snapshot_count": 2,
                "coverage": (
                    "reactor child membership, POM-local direct internal "
                    "dependency, exact A/B diff"
                ),
            },
        )

    def ask(self, *, request_id: str, dataset_id: str, question: str):
        raise PublicRunnerError(
            "COPY_AUDIT_ONLY",
            "V-002 copy audit does not activate the answer path",
            status="409 Conflict",
        )

    def citation(self, *, request_id: str, result_id: str):
        raise PublicRunnerError(
            "COPY_AUDIT_ONLY",
            "V-002 copy audit has no Citation Store",
            status="404 Not Found",
        )


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55125)
    arguments = parser.parse_args()
    if arguments.host != "127.0.0.1" or not 1 <= arguments.port <= 65_535:
        raise ValueError("copy audit server requires a valid 127.0.0.1 port")
    application = WorldModelBrowserApplication(_CopyAuditRunner())
    with make_server(
        arguments.host,
        arguments.port,
        application,
        handler_class=_QuietHandler,
    ) as server:
        print(
            json.dumps(
                {
                    "status": "ready",
                    "url": f"http://{arguments.host}:{arguments.port}/",
                    "purpose": "V-002_COPY_AUDIT_ONLY",
                    "production_activation": "NOT_EXECUTED",
                },
                sort_keys=True,
            ),
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
