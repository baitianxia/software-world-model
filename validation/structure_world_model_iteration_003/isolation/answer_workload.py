#!/usr/bin/env python3
"""Bundle-only G2 workload executed inside the answer Seatbelt process."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat

from software_world_model.application_services.citation_projection import (
    citation_seal_for_result,
)
from software_world_model.application_services.structure_view import (
    EntityResolutionStatus,
    StructureEntityArgument,
    StructureViewResult,
    StructureViewService,
)
from software_world_model.cross_cutting import StableId, canonical_json_bytes
from software_world_model.infrastructure.file_citation_observation_store import (
    structure_view_result_seal_payload,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.knowledge_engine.structure import (
    EntityType,
    RelationPredicate,
)


FORBIDDEN_PAYLOAD_KEYS = {
    "artifact_bytes",
    "excerpt",
    "observation",
    "provider_input",
    "source_bytes",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a1-b-envelope", required=True)
    parser.add_argument("--b-a2-envelope", required=True)
    parser.add_argument("--a1-bundle", required=True)
    parser.add_argument("--b-bundle", required=True)
    parser.add_argument("--a2-bundle", required=True)
    parser.add_argument("--identity-envelope", required=True)
    parser.add_argument("--identity-a-bundle", required=True)
    parser.add_argument("--identity-b-bundle", required=True)
    parser.add_argument("--query-report-output", required=True)
    parser.add_argument("--citation-seal-output", required=True)
    return parser


def _service(
    store: FileStructureReadBundleStore,
    envelope_path: str,
    bundle_paths: tuple[str, ...],
) -> tuple[StructureViewService, tuple[object, ...]]:
    envelope, _ = store.read_ordered(envelope_path)
    loaded = tuple(store.read_snapshot(path) for path in bundle_paths)
    return StructureViewService(envelope, loaded), tuple(item[0] for item in loaded)


def _unique(
    service: StructureViewService,
    snapshot_id: StableId,
    mention: str,
    *,
    entity_type: EntityType,
    canonical_ga: str | None = None,
) -> tuple[StructureEntityArgument, StructureViewResult]:
    result = service.entity_candidates(
        snapshot_id=snapshot_id,
        mention=mention,
        entity_type=entity_type,
        canonical_ga=canonical_ga,
    )
    if result.payload["resolution_status"] != EntityResolutionStatus.UNIQUE.value:
        raise RuntimeError(f"expected unique candidate for {mention!r}")
    return StructureEntityArgument.from_unique_candidate(result), result


def _mall_results(
    ab: StructureViewService,
    ba2: StructureViewService,
    a1: object,
    b: object,
    a2: object,
) -> tuple[dict[str, StructureViewResult], StructureViewResult]:
    results: dict[str, StructureViewResult] = {}
    inventories: dict[str, StructureViewResult] = {}
    for name, service, bundle in (
        ("a1", ab, a1),
        ("b", ab, b),
        ("a2", ba2, a2),
    ):
        system, candidate = _unique(
            service,
            bundle.snapshot_id,
            "mall",
            entity_type=EntityType.SOFTWARE_SYSTEM,
        )
        results[f"candidate-{name}-system"] = candidate
        inventory = service.child_module_inventory(system=system)
        inventories[name] = inventory
        results[f"inventory-{name}"] = inventory

        admin, admin_candidate = _unique(
            service,
            bundle.snapshot_id,
            "mall-admin",
            entity_type=EntityType.MAVEN_MODULE,
        )
        common, common_candidate = _unique(
            service,
            bundle.snapshot_id,
            "mall-common",
            entity_type=EntityType.MAVEN_MODULE,
        )
        results[f"candidate-{name}-admin"] = admin_candidate
        results[f"candidate-{name}-common"] = common_candidate
        results[f"paths-{name}-admin-common"] = service.all_simple_paths(
            source=admin,
            target=common,
            predicate=RelationPredicate.DEPENDS_ON,
        )

    b_admin = StructureEntityArgument.from_unique_candidate(
        results["candidate-b-admin"]
    )
    b_search, search_candidate = _unique(
        ab,
        b.snapshot_id,
        "mall-search",
        entity_type=EntityType.MAVEN_MODULE,
    )
    results["candidate-b-search"] = search_candidate
    results["zero-path-b-admin-search"] = ab.path_exists(
        source=b_admin,
        target=b_search,
        predicate=RelationPredicate.DEPENDS_ON,
    )
    b_system = StructureEntityArgument.from_unique_candidate(
        results["candidate-b-system"]
    )
    b_security, security_candidate = _unique(
        ab,
        b.snapshot_id,
        "mall-security",
        entity_type=EntityType.MAVEN_MODULE,
    )
    results["candidate-b-security"] = security_candidate
    results["root-negative-b-security"] = ab.path_exists(
        source=b_system,
        target=b_security,
        predicate=RelationPredicate.DEPENDS_ON,
    )
    results["diff-a1-b"] = ab.ordered_snapshot_diff(
        base_snapshot_id=a1.snapshot_id,
        target_snapshot_id=b.snapshot_id,
    )
    results["diff-b-a2"] = ba2.ordered_snapshot_diff(
        base_snapshot_id=b.snapshot_id,
        target_snapshot_id=a2.snapshot_id,
    )
    return results, inventories["b"]


def _identity_results(
    service: StructureViewService,
    snapshot_id: StableId,
) -> dict[str, StructureViewResult]:
    results: dict[str, StructureViewResult] = {}
    ambiguous = service.entity_candidates(
        snapshot_id=snapshot_id,
        mention="common-lib",
        entity_type=EntityType.MAVEN_MODULE,
    )
    if ambiguous.payload["resolution_status"] != EntityResolutionStatus.AMBIGUOUS.value:
        raise RuntimeError("same-name common-lib candidates were not ambiguous")
    if ambiguous.payload["candidate_count"] != 2:
        raise RuntimeError("same-name common-lib candidate count was not exactly two")
    results["common-lib-ambiguous"] = ambiguous
    resolved: dict[str, StructureEntityArgument] = {}
    for label, ga in (
        ("shared", "org.example.shared:common-lib"),
        ("legacy", "org.example.legacy:common-lib"),
    ):
        argument, candidate = _unique(
            service,
            snapshot_id,
            "common-lib",
            entity_type=EntityType.MAVEN_MODULE,
            canonical_ga=ga,
        )
        resolved[label] = argument
        results[f"common-lib-{label}-exact-ga"] = candidate
    billing, billing_candidate = _unique(
        service,
        snapshot_id,
        "billing",
        entity_type=EntityType.MAVEN_MODULE,
        canonical_ga="org.example.services:billing",
    )
    results["billing-unique"] = billing_candidate
    shared_path = service.path_exists(
        source=billing,
        target=resolved["shared"],
        predicate=RelationPredicate.DEPENDS_ON,
    )
    legacy_path = service.path_exists(
        source=billing,
        target=resolved["legacy"],
        predicate=RelationPredicate.DEPENDS_ON,
    )
    if not shared_path.payload["exists"]:
        raise RuntimeError("billing did not depend on exact shared common-lib")
    if legacy_path.payload["exists"] or not legacy_path.payload[
        "negative_conclusion_supported"
    ]:
        raise RuntimeError("billing-to-legacy complete negative was not established")
    results["billing-to-shared-path"] = shared_path
    results["billing-to-legacy-path"] = legacy_path
    return results


def _payload_audit(value: object) -> dict[str, object]:
    observed: set[str] = set()

    def collect(item: object) -> None:
        if isinstance(item, dict):
            observed.update(item)
            for nested in item.values():
                collect(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                collect(nested)

    collect(value)
    forbidden = sorted(observed & FORBIDDEN_PAYLOAD_KEYS)
    if forbidden:
        raise RuntimeError(f"View output contains forbidden payload keys: {forbidden}")
    return {
        "status": "PASS",
        "forbidden_keys": sorted(FORBIDDEN_PAYLOAD_KEYS),
        "found_forbidden_keys": forbidden,
        "excerpt_digest_present": "excerpt_digest" in observed,
    }


def _write_new(path_text: str, payload: bytes) -> None:
    path = Path(path_text)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("workload output path must be canonical and absolute")
    parent = path.parent.resolve(strict=True)
    if parent != path.parent or parent.is_symlink() or not parent.is_dir():
        raise ValueError("workload output parent must be a canonical directory")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            view = view[os.write(descriptor, view) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if not stat.S_ISREG(path.lstat().st_mode) or path.is_symlink():
        raise RuntimeError("workload output is not a regular file")


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    store = FileStructureReadBundleStore()
    ab, (a1, b) = _service(
        store,
        arguments.a1_b_envelope,
        (arguments.a1_bundle, arguments.b_bundle),
    )
    ba2, (loaded_b, a2) = _service(
        store,
        arguments.b_a2_envelope,
        (arguments.b_bundle, arguments.a2_bundle),
    )
    if loaded_b != b:
        raise RuntimeError("ordered mall Bundle sets disagree on exact B")
    identity, (identity_a, _identity_b) = _service(
        store,
        arguments.identity_envelope,
        (arguments.identity_a_bundle, arguments.identity_b_bundle),
    )
    mall, citation_result = _mall_results(ab, ba2, a1, b, a2)
    identity_results = _identity_results(identity, identity_a.snapshot_id)
    report = {
        "schema": "iteration-003-g2-answer-workload@1",
        "role": "answer",
        "mall_results": {
            name: result.canonical_value() for name, result in sorted(mall.items())
        },
        "identity_results": {
            name: result.canonical_value()
            for name, result in sorted(identity_results.items())
        },
    }
    report["payload_audit"] = _payload_audit(report)
    seal = citation_seal_for_result(citation_result)
    _write_new(
        arguments.query_report_output,
        canonical_json_bytes(report),
    )
    _write_new(
        arguments.citation_seal_output,
        canonical_json_bytes(structure_view_result_seal_payload(seal)),
    )
    print(
        canonical_json_bytes(
            {
                "status": "PASS",
                "query_result_count": len(mall) + len(identity_results),
                "citation_result_id": citation_result.result_id.value,
                "citation_seal_digest": seal.digest.value,
            }
        ).decode("utf-8")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
