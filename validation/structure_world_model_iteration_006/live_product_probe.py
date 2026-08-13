"""Run the sealed ITER-006 questions with a deterministic formal proposal stub."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping, Sequence

from software_world_model.ai_infrastructure.world_model_answer_strategy import (
    COMPLETE_NEGATIVE_ANSWER,
    ENTITY_CANDIDATE_RESOLUTION,
    GENERIC_QUERY_PLANNING,
    ORDERED_DIFF_EXPRESSION,
    VIEW_LIMITATION_AND_KNOWLEDGE_GAP,
)
from software_world_model.application_services.structure_view import (
    StructureViewService,
)
from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.infrastructure.file_read_set_catalog import (
    FileReadSetCatalogStore,
    RootedStructureReadBundleStore,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.interface.world_model_product import (
    JAVA_PRODUCT_STRATEGY_REF,
    WorldModelProductAnswerService,
)

from .live_evaluator import SUITE_SCHEMA


REPORT_SCHEMA = "SWM-JAVA-WORLD-MODEL-DETERMINISTIC-PRODUCT-PROBE@1"
_EXPECTED_OUTCOMES = {
    "SUPPORTED": {"SATISFIED"},
    "SUPPORTED_NEGATIVE": {"SATISFIED_SUPPORTED_NEGATIVE"},
    "ENTITY_RESOLUTION_LIMITATION": {"LIMITATION"},
    "KNOWLEDGE_GAP": {"KNOWLEDGE_GAP"},
}


class ProductProbeFailure(RuntimeError):
    """The exact deterministic Java question set did not satisfy its oracle."""


class _FormalProposalStub:
    strategy_ref = JAVA_PRODUCT_STRATEGY_REF

    def __init__(self) -> None:
        self.provider_call_count = 0
        self.network_operation_count = 0
        self.capabilities: list[str] = []

    def propose(
        self,
        *,
        case_id,
        capability,
        sealed_input,
        available_operations=(),
    ):
        del case_id, available_operations
        self.provider_call_count += 1
        self.network_operation_count += 1
        self.capabilities.append(capability)
        if capability == GENERIC_QUERY_PLANNING:
            operations = []
            for need in sealed_input["needs"]:
                index = 0 if need.endswith("left") else 1
                if need.startswith("method_inventory_"):
                    operations.append(
                        {
                            "operation": "declared_method_inventory",
                            "snapshot": sealed_input["read_set"][index],
                        }
                    )
                elif need.startswith("paths_"):
                    operations.append(
                        {
                            "operation": "all_simple_paths",
                            "snapshot": sealed_input["read_set"][index],
                            "source_ref": sealed_input["source_entity_ref"],
                            "target_ref": sealed_input["target_entity_ref"],
                        }
                    )
                else:
                    raise ProductProbeFailure(
                        f"unregistered Java planning need: {need}"
                    )
            normalized = {"operations": operations}
        elif capability == ENTITY_CANDIDATE_RESOLUTION:
            candidates = sealed_input["candidate_refs"]
            normalized = {
                "resolution_status": (
                    "NOT_FOUND"
                    if not candidates
                    else "RESOLVED"
                    if len(candidates) == 1
                    else "AMBIGUOUS"
                ),
                "candidate_refs": candidates,
                "next_operation_allowed": len(candidates) == 1,
            }
        elif capability == ORDERED_DIFF_EXPRESSION:
            normalized = {
                "direction": {
                    "base": sealed_input["base"],
                    "target": sealed_input["target"],
                },
                "added_entities": sealed_input["target_added"],
            }
        elif capability == COMPLETE_NEGATIVE_ANSWER:
            normalized = {
                "need_status": "SATISFIED_SUPPORTED_NEGATIVE",
                "claim_scope": "NO_PATH_IN_CALLS_FOR_EXACT_READ_SET",
            }
        elif capability == VIEW_LIMITATION_AND_KNOWLEDGE_GAP:
            normalized = {
                "view_result": {
                    "status": "LIMITED",
                    "code": "COVERAGE_PARTIAL",
                    "owner": "STRUCTURE_VIEW",
                },
                "need_assessment": {
                    "status": "KNOWLEDGE_GAP",
                    "code": "INSUFFICIENT_COMPLETE_COVERAGE",
                    "owner": "KNOWLEDGE_USE",
                },
            }
        else:
            raise ProductProbeFailure(
                f"unregistered deterministic capability: {capability}"
            )
        return SimpleNamespace(normalized_result=normalized)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _load_suite(path: Path) -> Mapping[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise ProductProbeFailure("held-out suite is not canonical JSON")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if (
        value.get("schema") != SUITE_SCHEMA
        or value.get("document_digest") != digest_of([SUITE_SCHEMA, core]).value
        or value.get("sealed_before_world_model_results") is not True
        or value.get("world_model_result_count_at_seal") != 0
    ):
        raise ProductProbeFailure("held-out suite seal is invalid")
    return value


def _path(root: Path, locator: str) -> Path:
    lexical = root.joinpath(*locator.split("/"))
    resolved = lexical.resolve(strict=True)
    if (
        lexical != resolved
        or not resolved.is_file()
        or resolved.is_symlink()
        or not resolved.is_relative_to(root)
    ):
        raise ProductProbeFailure("Catalog locator is not an exact Bundle file")
    return resolved


def _run_case(*, case: Mapping[str, object], catalog, bundle_root: Path):
    read_set_id = str(case["read_set_id"])
    entry = next(
        (item for item in catalog.entries if item.read_set_id.value == read_set_id),
        None,
    )
    if entry is None:
        raise ProductProbeFailure(f"{case['case_id']}: Read Set is absent")
    ordered = [
        item for item in entry.file_manifest if item.role.value == "ORDERED_ENVELOPE"
    ]
    snapshots = sorted(
        (item for item in entry.file_manifest if item.role.value == "SNAPSHOT"),
        key=lambda item: item.ordinal,
    )
    if len(ordered) != 1 or len(snapshots) != len(entry.snapshot_bindings):
        raise ProductProbeFailure(f"{case['case_id']}: Bundle manifest is invalid")
    files = FileStructureReadBundleStore()
    loaded = tuple(
        files.read_snapshot(str(_path(bundle_root, item.locator)))
        for item in snapshots
    )
    ordered_bundle, _ = files.read_ordered(
        str(_path(bundle_root, ordered[0].locator))
    )
    model = _FormalProposalStub()
    execution = WorldModelProductAnswerService(
        view=StructureViewService(ordered_bundle, loaded),
        snapshot_bundles=tuple(item[0] for item in loaded),
        model_strategy=model,
        gateway_counters=model,
    ).execute(
        request_ref=f"iter006-deterministic:{case['case_id']}",
        original_question=str(case["question"]),
        response_language="zh-CN",
        classification="INTERNAL",
        permission_digest=digest_of(
            ["ITER-006-DETERMINISTIC-PROBE@1", case["case_id"]]
        ),
    )
    execution.chain.require_valid()
    body = execution.chain.draft.body
    folded = body.casefold()
    missing = [
        token
        for token in case["required_tokens"]
        if str(token).casefold() not in folded
    ]
    forbidden = [
        token
        for token in case["forbidden_tokens"]
        if str(token).casefold() in folded
    ]
    markers = [str(item) for item in case["outcome_markers_any"]]
    marker_present = not markers or any(item.casefold() in folded for item in markers)
    outcomes = {item.outcome.value for item in execution.chain.assessment.needs}
    if (
        missing
        or forbidden
        or not marker_present
        or outcomes != _EXPECTED_OUTCOMES[str(case["expected_outcome"])]
        or execution.chain.provider_call_count != 1
        or execution.chain.network_operation_count != 1
        or len(execution.model_proposals) != 1
    ):
        raise ProductProbeFailure(
            f"{case['case_id']}: expectation failed "
            f"(missing={missing}, forbidden={forbidden}, outcomes={outcomes})"
        )
    return {
        "case_id": case["case_id"],
        "read_set_id": read_set_id,
        "expected_outcome": case["expected_outcome"],
        "assessment_outcomes": sorted(outcomes),
        "proposal_capability": model.capabilities[0],
        "simulated_formal_proposal_count": 1,
        "answer_body": body,
        "answer_digest": digest_of(body).value,
        "required_token_count": len(case["required_tokens"]),
        "missing_tokens": [],
        "forbidden_hits": [],
        "outcome_marker_present": marker_present,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--catalog-root", required=True)
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    suite = _load_suite(Path(arguments.suite).resolve(strict=True))
    bundle_root = Path(arguments.bundle_root).resolve(strict=True)
    store = RootedStructureReadBundleStore(bundle_root)
    catalogs = FileReadSetCatalogStore(
        Path(arguments.catalog_root).resolve(strict=True), store
    )
    pointer = catalogs.read_pointer()
    if pointer is None:
        raise ProductProbeFailure("Catalog pointer is absent")
    catalog = catalogs.read_catalog(pointer, verify_files=True)
    results = [
        _run_case(case=case, catalog=catalog, bundle_root=bundle_root)
        for case in suite["cases"]
    ]
    core = {
        "schema": REPORT_SCHEMA,
        "status": "PASS",
        "scope": "DETERMINISTIC_FORMAL_PROPOSAL_STUB_NO_EXTERNAL_MODEL",
        "suite_digest": suite["document_digest"],
        "catalog_digest": pointer.catalog_digest.value,
        "case_count": len(results),
        "results": results,
        "external_model_called": False,
        "production_activation": "NOT_EXECUTED",
    }
    report = {**core, "document_digest": digest_of([REPORT_SCHEMA, core]).value}
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise ProductProbeFailure("probe output already exists")
    output.write_bytes(_canonical(report))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
