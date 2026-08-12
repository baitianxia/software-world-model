"""Deterministic adapter probe for a randomized ITER-005 dynamic Catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from software_world_model.infrastructure.file_read_set_catalog import (
    FileReadSetCatalogStore,
    RootedStructureReadBundleStore,
)
from software_world_model.interface.world_model_http import (
    DynamicCatalogWorldModelRunner,
    SqliteAuthorityStateProbe,
)


SCHEMA = "SWM-WORLD-MODEL-DETERMINISTIC-ADAPTER-PROBE@1"
_DIGEST = "sha256:" + "a" * 64
_RESULT_ID = "structure_view_result_" + "b" * 32


class _Executor:
    def __init__(self, commit: str, tree: str) -> None:
        self.commit = commit
        self.tree = tree
        self.calls: list[dict[str, object]] = []

    def health(self) -> Mapping[str, object]:
        return {
            "status": "ready",
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_status": "CANDIDATE",
            "evaluation_subject_commit": self.commit,
            "evaluation_subject_tree": self.tree,
            "evaluation_grant_digest": _DIGEST,
            "deterministic_qualification_digest": _DIGEST,
            "held_out_suite_digest": _DIGEST,
            "independent_evaluator_digest": _DIGEST,
            "startup_preflight_digest": _DIGEST,
            "startup_receipt_digest": _DIGEST,
            "stage_manifest_digest": _DIGEST,
            "launcher_manifest_digest": _DIGEST,
            "provider_subject_digest": _DIGEST,
            "gateway_authorization_receipt_digest": _DIGEST,
            "dispatch_policy": "ONE_CALL_PER_QUESTION_NO_HIDDEN_RETRY",
            "production_activation": "NOT_EXECUTED",
        }

    def execute(self, *, request_id, read_set, question):
        registration = read_set.registration
        self.calls.append(
            {
                "request_id": request_id,
                "read_set_id": registration.read_set_id.value,
                "snapshot_count": len(read_set.snapshot_bundles),
                "ordered_bundle": str(read_set.ordered_bundle),
            }
        )
        return {
            "request_id": request_id,
            "read_set_id": registration.read_set_id.value,
            "question": question,
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_status": "CANDIDATE",
            "evaluation_subject_commit": self.commit,
            "evaluation_subject_tree": self.tree,
            "page_digest": _DIGEST,
            "page": {
                "mode": "WORLD_MODEL",
                "environment": "EVALUATION_ONLY",
                "evaluation_only": True,
                "implementation_commit": self.commit,
                "request": {"original_question": question},
                "read_binding": {
                    "read_set_digest": registration.read_set_digest.value,
                    "snapshots": [
                        {"snapshot_id": item.snapshot_id.value}
                        for item in registration.snapshot_bindings
                    ],
                },
                "authority_chain": {
                    "stages": [
                        {"stage": f"STAGE_{index}"} for index in range(10)
                    ]
                },
                "answer": {"body": "deterministic adapter probe", "claims": []},
            },
            "citations": [
                {
                    "result_id": _RESULT_ID,
                    "seal_digest": _DIGEST,
                    "projection_digest": _DIGEST,
                    "url": (
                        f"/v1/world-model/requests/{request_id}/"
                        f"citations/{_RESULT_ID}"
                    ),
                }
            ],
            "execution": {
                "attempt_count": 1,
                "provider_call_count": 1,
                "network_operation_count": 1,
                "selective_retry_count": 0,
                "source_access_count": 0,
                "evidence_payload_access_count": 0,
            },
            "production_activation": "NOT_EXECUTED",
        }

    def citation(self, *, request_id, result_id):
        return {
            "request_id": request_id,
            "result_id": result_id,
            "seal_digest": _DIGEST,
            "projection_digest": _DIGEST,
            "environment": "EVALUATION_ONLY",
            "network_operation_count": 0,
            "answer_return_port": False,
            "citation_projection": {"citations": []},
            "production_activation": "NOT_EXECUTED",
        }


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _document(core: Mapping[str, object]) -> dict[str, object]:
    digest = "sha256:" + hashlib.sha256(_canonical([SCHEMA, core])).hexdigest()
    return {**core, "document_digest": digest}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--catalog-root", required=True)
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--implementation-tree", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    database = Path(arguments.database).resolve(strict=True)
    catalog_root = Path(arguments.catalog_root).resolve(strict=True)
    bundle_root = Path(arguments.bundle_root).resolve(strict=True)
    bundle_store = RootedStructureReadBundleStore(bundle_root)
    executor = _Executor(
        arguments.implementation_commit,
        arguments.implementation_tree,
    )
    probe = SqliteAuthorityStateProbe(database)
    runner = DynamicCatalogWorldModelRunner(
        catalog_store=FileReadSetCatalogStore(catalog_root, bundle_store),
        bundle_store=bundle_store,
        executor=executor,
        authority_probe=probe,
    )
    before = probe.capture()
    datasets = runner.datasets()
    if not datasets or {int(item["snapshot_count"]) for item in datasets} != {1, 2}:
        raise RuntimeError("dynamic Catalog lacks exact single/ordered Read Sets")
    public: list[dict[str, object]] = []
    forbidden_paths = (str(database), str(catalog_root), str(bundle_root))
    for index, dataset in enumerate(datasets, start=1):
        encoded = json.dumps(dataset, ensure_ascii=False)
        if any(path in encoded for path in forbidden_paths):
            raise RuntimeError("public dataset leaked a trusted path")
        question = f"deterministic adapter probe {index}"
        result = runner.ask(
            request_id=f"slice2-probe-{index}",
            dataset_id=str(dataset["read_set_id"]),
            question=question,
        )
        if (
            result.get("read_set_id") != dataset["read_set_id"]
            or result.get("authority_fence", {}).get("unchanged") is not True
        ):
            raise RuntimeError("dynamic adapter result binding failed")
        runner.citation(request_id=f"slice2-probe-{index}", result_id=_RESULT_ID)
        public.append(
            {
                "read_set_id": dataset["read_set_id"],
                "snapshot_count": dataset["snapshot_count"],
                "source_revisions": dataset["source_revisions"],
                "catalog_digest": dataset["catalog_digest"],
            }
        )
    after = probe.capture()
    if after != before:
        raise RuntimeError("deterministic adapter probe mutated authority state")
    core = {
        "schema": SCHEMA,
        "status": "PASS",
        "scope": "ADAPTER_ONLY_NO_MODEL_NO_OS_PREFLIGHT",
        "datasets": public,
        "question_count": len(public),
        "authority_before": before.public_value(),
        "authority_after": after.public_value(),
        "authority_unchanged": True,
        "external_model_called": False,
        "production_activation": "NOT_EXECUTED",
    }
    report = _document(core)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise RuntimeError("adapter probe output already exists")
    output.write_bytes(_canonical(report))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
