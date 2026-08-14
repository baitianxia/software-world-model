"""Freeze and self-test the visible ITER-007 frontend/no-payload oracles.

This module is readiness evidence, not a product parser.  It compares the
selected tree-sitter Java frontend with the JDK compiler tree API on the public
development corpus and exercises preservation/leakage checks on a deliberately
small typed reference projection.
"""

from __future__ import annotations

from importlib.metadata import distribution
from pathlib import Path
import argparse
import base64
import binascii
import gzip
import hashlib
import json
import re
import subprocess
import tempfile
from typing import Any
import zlib

from tree_sitter import Language, Parser
import tree_sitter_java

from software_world_model.application_services.java_static_call import (
    JavaSourceEvidenceMetadata,
    JavaStaticCallInput,
    evaluate_java_static_calls,
)
from software_world_model.application_services.maven_structure import GitEntryMetadata
from software_world_model.cross_cutting import Digest, StableId, digest_of
from software_world_model.knowledge_engine.structure import (
    RelationPredicate,
    StructureEvidence,
)


ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parents[1]
DEVELOPMENT_ROOT = ROOT / "fixtures" / "development"
JAVA_SOURCE = (
    DEVELOPMENT_ROOT
    / "src"
    / "main"
    / "java"
    / "dev"
    / "acme"
    / "auth"
    / "LoginService.java"
)
JAVAC_ORACLE = ROOT / "oracle" / "JavacAstOracle.java"
NO_PAYLOAD_POLICY = ROOT / "oracle" / "no_payload_policy.json"

EXPECTED_COMPONENTS = (
    (
        "tree-sitter",
        "0.25.2",
        "sha256:86952fb273226021793f76c972d782b66c308d3ef8d20a4df4dd5ad6d31ec45c",
    ),
    (
        "tree-sitter-java",
        "0.23.5",
        "sha256:33106942ffed3b3df935320ac8ac9499e453ce66730a2130ba81b2dffef7c9dc",
    ),
)
EXPECTED_FRONTEND_DIGEST = (
    "sha256:45b49edd3dbaaec472533c13a4a6d1e3e0eab6a3be2d1529685bdca5560e65b3"
)
TREE_SITTER_KIND = {
    "class_declaration": "CLASS",
    "method_declaration": "METHOD",
    "if_statement": "IF",
    "method_invocation": "METHOD_INVOCATION",
    "return_statement": "RETURN",
    "throw_statement": "THROW",
}
SOURCE_TOKEN = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*|\d+|\S")
METHOD_REF = re.compile(
    r"^[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*"
    r"#[A-Za-z_$][A-Za-z0-9_$]*\([A-Za-z0-9_$.,\[\]]*\)$"
)
TYPE_REF = re.compile(
    r"^[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*$"
)
ATOM_REF = re.compile(r"^atom:(?:branch|call|return|throw):[0-9]+$")
SLOT_REF = re.compile(r"^slot:[A-Za-z_$][A-Za-z0-9_$]*$")
SUPPORT_REF = re.compile(r"^support:[0-9]+$")
FEATURE_TOKEN = re.compile(r"^[a-z][a-z0-9]{0,31}$")
SUPPORT_LOCATOR = re.compile(
    r"^(?P<path>[A-Za-z0-9_./-]+)#bytes=(?P<start>[0-9]+)-"
    r"(?P<end>[0-9]+);kind=[a-z0-9-]+$"
)
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
MAXIMUM_PROJECTION_JSON_BYTES = 16 * 1024
MAXIMUM_METHOD_REF_LENGTH = 256
MAXIMUM_TYPE_REF_LENGTH = 192
MAXIMUM_IDENTIFIER_SEGMENT_LENGTH = 64
MAXIMUM_ATOM_REF_LENGTH = 32
MAXIMUM_SLOT_REF_LENGTH = 80
REFERENCE_SOURCE_PATH = "src/main/java/dev/acme/auth/LoginService.java"
REFERENCE_METHOD = "dev.acme.auth.LoginService#authenticate(boolean)"
REFERENCE_RECORD_METHOD = "dev.acme.auth.LoginService#recordFailure()"
REFERENCE_SESSION_METHOD = "dev.acme.auth.LoginService#issueSession()"
REQUIRED_CLAIMS = (
    "invalid-credentials-controls-record-and-throw",
    "issue-session-call-result-is-returned-in-source-order",
    "legacy-calls-preserved",
)


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_digest(value: object) -> str:
    return _sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )


def _runtime_fileset_digest(name: str) -> str:
    package = distribution(name)
    entries: list[dict[str, object]] = []
    for item in sorted(package.files or (), key=str):
        relative = str(item)
        if (
            "__pycache__/" in relative
            or relative.endswith("/RECORD")
            or relative.endswith("/INSTALLER")
            or relative.endswith("/REQUESTED")
        ):
            continue
        path = Path(package.locate_file(item))
        if path.is_file():
            content = path.read_bytes()
            entries.append(
                {
                    "path": relative,
                    "size": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    return _canonical_digest(
        {"distribution": name, "version": package.version, "files": entries}
    )


def _frontend_identity() -> dict[str, object]:
    components: list[dict[str, object]] = []
    for name, expected_version, expected_digest in EXPECTED_COMPONENTS:
        actual = distribution(name)
        if actual.version != expected_version:
            raise RuntimeError(f"{name} version drift: {actual.version}")
        actual_digest = _runtime_fileset_digest(name)
        if actual_digest != expected_digest:
            raise RuntimeError(f"{name} runtime fileset drift: {actual_digest}")
        components.append(
            {
                "distribution": name,
                "version": actual.version,
                "runtime_fileset_digest": actual_digest,
            }
        )
    language = Language(tree_sitter_java.language())
    if language.abi_version != 14:
        raise RuntimeError(f"tree-sitter Java ABI drift: {language.abi_version}")
    identity = {
        "frontend_ref": "TREE_SITTER_JAVA_FRONTEND@1",
        "language_abi": language.abi_version,
        "components": components,
    }
    digest = _canonical_digest(identity)
    if digest != EXPECTED_FRONTEND_DIGEST:
        raise RuntimeError(f"combined frontend identity drift: {digest}")
    return {**identity, "offline_artifact_digest": digest}


def _tree_sitter_records(source: bytes) -> tuple[tuple[str, int, int], ...]:
    parser = Parser(Language(tree_sitter_java.language()))
    tree = parser.parse(source)
    if tree.root_node.has_error:
        raise RuntimeError("tree-sitter reported a parse error")
    records: list[tuple[str, int, int]] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        mapped = TREE_SITTER_KIND.get(node.type)
        if mapped is not None:
            records.append((mapped, node.start_byte, node.end_byte))
        stack.extend(reversed(node.children))
    return tuple(sorted(records, key=lambda value: (value[1], value[2], value[0])))


def _jdk_identity() -> dict[str, str]:
    javac = subprocess.run(
        ["javac", "-version"],
        check=True,
        capture_output=True,
        text=True,
    )
    version = (javac.stdout or javac.stderr).strip()
    if version != "javac 21.0.8":
        raise RuntimeError(f"JDK canonicalization Oracle drift: {version}")
    return {"javac_version": version, "source_release": "17"}


def _javac_records(source: Path) -> tuple[tuple[str, int, int], ...]:
    with tempfile.TemporaryDirectory(prefix="iter-007-javac-oracle-") as directory:
        subprocess.run(
            ["javac", "--release", "17", "-d", directory, str(JAVAC_ORACLE)],
            check=True,
            capture_output=True,
            text=True,
        )
        completed = subprocess.run(
            ["java", "-cp", directory, "JavacAstOracle", str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
    records: list[tuple[str, int, int]] = []
    for line in completed.stdout.splitlines():
        kind, start, end = line.split("\t")
        records.append((kind, int(start), int(end)))
    return tuple(sorted(records, key=lambda value: (value[1], value[2], value[0])))


def _source_manifest_digest() -> str:
    entries: list[dict[str, object]] = []
    for path in sorted(item for item in DEVELOPMENT_ROOT.rglob("*") if item.is_file()):
        content = path.read_bytes()
        entries.append(
            {
                "path": path.relative_to(DEVELOPMENT_ROOT).as_posix(),
                "size": len(content),
                "sha256": _sha256(content),
            }
        )
    return _canonical_digest(
        {"schema": "ITER-007-VISIBLE-DEVELOPMENT-CORPUS@1", "entries": entries}
    )


def _stable(kind: str, value: str) -> StableId:
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[-32:]
    return StableId(f"{kind}_{suffix}")


def _content_digest(payload: bytes) -> Digest:
    return Digest(_sha256(payload))


def _legacy_call_targets() -> tuple[dict[str, object], ...]:
    pairs = tuple(
        (path.relative_to(DEVELOPMENT_ROOT).as_posix(), path.read_bytes())
        for path in sorted(DEVELOPMENT_ROOT.rglob("*.java"))
    )
    revision = "visible-development"
    source_context_id = _stable("source_context", revision)
    entries = {
        path: GitEntryMetadata(
            mode="100644",
            object_type="blob",
            object_id=hashlib.sha1(payload).hexdigest(),
        )
        for path, payload in pairs
    }
    evidence = {
        path: JavaSourceEvidenceMetadata(
            artifact_id=_stable("source_artifact", f"{revision}:{path}"),
            source_context_id=source_context_id,
            artifact_content_digest=_content_digest(payload),
            locator=path,
        )
        for path, payload in pairs
    }
    tree_excerpt = "\n".join(
        json.dumps(
            {
                "is_symlink": metadata.is_symlink,
                "mode": metadata.mode,
                "object_id": metadata.object_id,
                "path": path,
                "type": metadata.object_type,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for path, metadata in sorted(entries.items())
    )
    tree_payload = tree_excerpt.encode("utf-8")
    tree_evidence = StructureEvidence.create(
        artifact_id=_stable("source_artifact", f"tree:{revision}"),
        source_context_id=source_context_id,
        byte_start=0,
        byte_end=len(tree_payload),
        locator=f"git-tree:{revision}:all",
        excerpt=tree_excerpt,
        artifact_content_digest=_content_digest(tree_payload),
    )
    result = evaluate_java_static_calls(
        JavaStaticCallInput(
            owning_scope_id=_stable("scope", revision),
            source_binding_id=_stable("binding", revision),
            source_revision=revision,
            knowledge_context_digest=digest_of(
                {"source_revision": revision, "profile": "java-static-call"}
            ),
            source_bytes=dict(pairs),
            git_entries=entries,
            source_evidence=evidence,
            tree_evidence=(tree_evidence,),
            logical_source_root="src/main/java",
        )
    )
    signatures = {}
    for method in result.methods:
        fields = method.root.root_fields
        parameters = ",".join(str(value) for value in fields["parameter_types"])
        signatures[method.root_id] = (
            f"{fields['declaring_type_qualified_name']}#"
            f"{fields['method_name']}({parameters})"
        )
    evidence_by_id = {item.evidence_id: item for item in result.evidence}
    records: list[dict[str, object]] = []
    for relation in result.relations:
        if relation.root.predicate is not RelationPredicate.CALLS:
            continue
        support = tuple(
            sorted(
                (
                    {
                        "locator": evidence_by_id[evidence_id].locator,
                        "byte_start": evidence_by_id[evidence_id].byte_start,
                        "byte_end": evidence_by_id[evidence_id].byte_end,
                        "excerpt_digest": evidence_by_id[evidence_id].excerpt_digest.value,
                        "artifact_content_digest": evidence_by_id[
                            evidence_id
                        ].artifact_content_digest.value,
                    }
                    for evidence_id in relation.state.evidence_references
                ),
                key=lambda item: str(item["locator"]),
            )
        )
        records.append(
            {
                "caller_method_ref": signatures[
                    relation.root.subject.entity_root_id
                ],
                "callee_method_ref": signatures[
                    relation.root.object.entity_root_id
                ],
                "predicate": relation.root.predicate.value,
                "modality": relation.root.observation_modality.value,
                "call_site_count": relation.state.predicate_state_payload_fields[
                    "call_site_count"
                ],
                "source_revision": relation.state.source_revision,
                "support": support,
            }
        )
    return tuple(
        sorted(
            records,
            key=lambda item: (
                str(item["caller_method_ref"]),
                str(item["callee_method_ref"]),
            ),
        )
    )


def _fragment_ranges(source: bytes, fragment: bytes) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    offset = 0
    while True:
        start = source.find(fragment, offset)
        if start < 0:
            return tuple(ranges)
        ranges.append((start, start + len(fragment)))
        offset = start + len(fragment)


def _support_record(
    source: bytes,
    *,
    ordinal: int,
    byte_start: int,
    byte_end: int,
    kind: str,
) -> dict[str, object]:
    observation = source[byte_start:byte_end].decode("utf-8")
    return {
        "support_ref": f"support:{ordinal}",
        "source_revision": "visible-development",
        "locator": (
            f"{REFERENCE_SOURCE_PATH}#bytes={byte_start}-{byte_end};kind={kind}"
        ),
        "byte_start": byte_start,
        "byte_end": byte_end,
        "observation_digest": digest_of(observation).value,
        "artifact_content_digest": _content_digest(source).value,
    }


def _reference_supports() -> list[dict[str, object]]:
    source = JAVA_SOURCE.read_bytes()
    branch = _fragment_ranges(source, b"!credentialsValid")
    records = _fragment_ranges(source, b"recordFailure()")
    thrown = _fragment_ranges(source, b"throw new IllegalStateException();")
    sessions = _fragment_ranges(source, b"issueSession()")
    returned = _fragment_ranges(source, b"return issueSession();")
    if not (
        len(branch) == 1
        and len(records) == 3
        and len(thrown) == 1
        and len(sessions) == 2
        and len(returned) == 1
    ):
        raise RuntimeError("visible reference support fragments drifted")
    fragments = (
        (*branch[0], "java-source-semantics-branch"),
        (*records[0], "java-static-call-site"),
        (*records[1], "java-static-call-site"),
        (*thrown[0], "java-source-semantics-throw"),
        (*sessions[0], "java-static-call-site"),
        (*returned[0], "java-source-semantics-return"),
    )
    return [
        _support_record(
            source,
            ordinal=ordinal,
            byte_start=start,
            byte_end=end,
            kind=kind,
        )
        for ordinal, (start, end, kind) in enumerate(fragments)
    ]


def _reference_projection() -> dict[str, object]:
    method = REFERENCE_METHOD
    record = REFERENCE_RECORD_METHOD
    session = REFERENCE_SESSION_METHOD
    return {
        "schema": "JAVA-SOURCE-SEMANTICS-REFERENCE-PROJECTION@1",
        "profile_ref": "JAVA_SOURCE_SEMANTICS@1",
        "method_ref": method,
        "disposition": "SEMANTICS_COMPLETE",
        "feature_tokens": [
            "authenticate",
            "credentials",
            "failure",
            "issue",
            "login",
            "record",
            "service",
            "session",
            "valid",
        ],
        "atoms": [
            {
                "atom_ref": "atom:branch:0",
                "kind": "BRANCH",
                "operator": "NOT",
                "operand_ref": "slot:credentialsValid",
                "source_order": 0,
                "support_refs": ["support:0"],
            },
            {
                "atom_ref": "atom:call:1",
                "kind": "CALL_SITE",
                "target_method_ref": record,
                "controlled_by": "atom:branch:0",
                "branch_polarity": "TRUE",
                "source_order": 1,
                "support_refs": ["support:1"],
            },
            {
                "atom_ref": "atom:call:2",
                "kind": "CALL_SITE",
                "target_method_ref": record,
                "controlled_by": "atom:branch:0",
                "branch_polarity": "TRUE",
                "source_order": 2,
                "support_refs": ["support:2"],
            },
            {
                "atom_ref": "atom:throw:3",
                "kind": "THROW",
                "exception_type_ref": "java.lang.IllegalStateException",
                "controlled_by": "atom:branch:0",
                "branch_polarity": "TRUE",
                "source_order": 3,
                "support_refs": ["support:3"],
            },
            {
                "atom_ref": "atom:call:4",
                "kind": "CALL_SITE",
                "target_method_ref": session,
                "source_order": 4,
                "support_refs": ["support:4"],
            },
            {
                "atom_ref": "atom:return:5",
                "kind": "RETURN",
                "value_ref": "atom:call:4",
                "source_order": 5,
                "support_refs": ["support:5"],
            },
        ],
        "legacy_calls": [
            {
                "caller_method_ref": method,
                "callee_method_ref": record,
                "predicate": "CALLS",
                "modality": "JAVA_SOURCE_STATIC_CALL@1",
                "call_site_count": 2,
                "source_revision": "visible-development",
                "support_refs": ["support:1", "support:2"],
            },
            {
                "caller_method_ref": method,
                "callee_method_ref": session,
                "predicate": "CALLS",
                "modality": "JAVA_SOURCE_STATIC_CALL@1",
                "call_site_count": 1,
                "source_revision": "visible-development",
                "support_refs": ["support:4"],
            },
        ],
        "supports": _reference_supports(),
        "claim_support": [
            {
                "claim_ref": REQUIRED_CLAIMS[0],
                "support_refs": ["support:0", "support:1", "support:2", "support:3"],
            },
            {
                "claim_ref": REQUIRED_CLAIMS[1],
                "support_refs": ["support:4", "support:5"],
            },
            {
                "claim_ref": REQUIRED_CLAIMS[2],
                "support_refs": ["support:1", "support:2", "support:4"],
            },
        ],
    }


def _assert_preservation(projection: dict[str, object]) -> tuple[str, ...]:
    atoms = projection.get("atoms")
    calls = projection.get("legacy_calls")
    if not isinstance(atoms, list) or not isinstance(calls, list):
        raise RuntimeError("reference projection omits typed atoms or legacy calls")
    by_ref = {
        item.get("atom_ref"): item
        for item in atoms
        if isinstance(item, dict) and isinstance(item.get("atom_ref"), str)
    }
    branch = by_ref.get("atom:branch:0")
    record = by_ref.get("atom:call:1")
    repeated_record = by_ref.get("atom:call:2")
    thrown = by_ref.get("atom:throw:3")
    session = by_ref.get("atom:call:4")
    returned = by_ref.get("atom:return:5")
    if not (
        isinstance(branch, dict)
        and branch.get("operator") == "NOT"
        and branch.get("operand_ref") == "slot:credentialsValid"
        and isinstance(record, dict)
        and record.get("controlled_by") == "atom:branch:0"
        and record.get("branch_polarity") == "TRUE"
        and isinstance(repeated_record, dict)
        and repeated_record.get("controlled_by") == "atom:branch:0"
        and repeated_record.get("branch_polarity") == "TRUE"
        and isinstance(thrown, dict)
        and thrown.get("controlled_by") == "atom:branch:0"
        and thrown.get("exception_type_ref") == "java.lang.IllegalStateException"
    ):
        raise RuntimeError("invalid-credentials branch claim is not reconstructable")
    if not (
        isinstance(session, dict)
        and isinstance(returned, dict)
        and returned.get("value_ref") == session.get("atom_ref")
        and int(session.get("source_order", -1)) < int(returned.get("source_order", -1))
    ):
        raise RuntimeError("session call/return source-order claim is not reconstructable")
    targets = {
        (
            item.get("caller_method_ref"),
            item.get("callee_method_ref"),
            item.get("predicate"),
            item.get("modality"),
            item.get("call_site_count"),
            item.get("source_revision"),
            tuple(item.get("support_refs", ())),
        )
        for item in calls
        if isinstance(item, dict)
    }
    if targets != {
        (
            REFERENCE_METHOD,
            REFERENCE_RECORD_METHOD,
            "CALLS",
            "JAVA_SOURCE_STATIC_CALL@1",
            2,
            "visible-development",
            ("support:1", "support:2"),
        ),
        (
            REFERENCE_METHOD,
            REFERENCE_SESSION_METHOD,
            "CALLS",
            "JAVA_SOURCE_STATIC_CALL@1",
            1,
            "visible-development",
            ("support:4",),
        ),
    }:
        raise RuntimeError("legacy CALLS claim is not reconstructable")
    claim_support = projection.get("claim_support")
    if not isinstance(claim_support, list):
        raise RuntimeError("reference projection omits claim Support")
    supported_claims = tuple(
        item.get("claim_ref")
        for item in claim_support
        if isinstance(item, dict) and item.get("support_refs")
    )
    if supported_claims != REQUIRED_CLAIMS:
        raise RuntimeError("reference projection claim Support is incomplete")
    return REQUIRED_CLAIMS


def _iter_items(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _iter_items(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_items(item)


def _exact_keys(value: object, expected: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeError(f"{label} has fields outside its exact allowlist")
    return value


def _require_ref(
    value: object,
    pattern: re.Pattern[str],
    label: str,
    *,
    maximum_length: int,
) -> str:
    if (
        not isinstance(value, str)
        or len(value) > maximum_length
        or pattern.fullmatch(value) is None
    ):
        raise RuntimeError(f"{label} is not canonical")
    identifier_segments = re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", value)
    if any(len(segment) > MAXIMUM_IDENTIFIER_SEGMENT_LENGTH for segment in identifier_segments):
        raise RuntimeError(f"{label} contains an over-budget identifier segment")
    return value


def _validate_reference_projection(projection: dict[str, object]) -> None:
    root = _exact_keys(
        projection,
        {
            "schema",
            "profile_ref",
            "method_ref",
            "disposition",
            "feature_tokens",
            "atoms",
            "legacy_calls",
            "supports",
            "claim_support",
        },
        "reference projection",
    )
    if root["schema"] != "JAVA-SOURCE-SEMANTICS-REFERENCE-PROJECTION@1":
        raise RuntimeError("reference projection schema drift")
    if root["profile_ref"] != "JAVA_SOURCE_SEMANTICS@1":
        raise RuntimeError("reference projection profile drift")
    if len(json.dumps(projection, ensure_ascii=False, separators=(",", ":")).encode()) > MAXIMUM_PROJECTION_JSON_BYTES:
        raise RuntimeError("reference projection exceeds the frozen byte budget")
    _require_ref(
        root["method_ref"],
        METHOD_REF,
        "projection method_ref",
        maximum_length=MAXIMUM_METHOD_REF_LENGTH,
    )
    if root["disposition"] != "SEMANTICS_COMPLETE":
        raise RuntimeError("reference projection disposition drift")
    feature_tokens = root["feature_tokens"]
    if (
        not isinstance(feature_tokens, list)
        or not (1 <= len(feature_tokens) <= 32)
        or feature_tokens != sorted(set(feature_tokens))
        or any(
            not isinstance(item, str) or FEATURE_TOKEN.fullmatch(item) is None
            for item in feature_tokens
        )
    ):
        raise RuntimeError("feature tokens are not a canonical bounded set")

    atoms = root["atoms"]
    if not isinstance(atoms, list) or not (1 <= len(atoms) <= 64):
        raise RuntimeError("implementation atoms exceed the frozen budget")
    orders: list[int] = []
    atom_refs: set[str] = set()
    for raw_atom in atoms:
        if not isinstance(raw_atom, dict):
            raise RuntimeError("implementation atom must be a mapping")
        kind = raw_atom.get("kind")
        required_by_kind = {
            "BRANCH": {
                "atom_ref",
                "kind",
                "operator",
                "operand_ref",
                "source_order",
                "support_refs",
            },
            "CALL_SITE": {
                "atom_ref",
                "kind",
                "target_method_ref",
                "source_order",
                "support_refs",
            },
            "THROW": {
                "atom_ref",
                "kind",
                "exception_type_ref",
                "source_order",
                "support_refs",
            },
            "RETURN": {
                "atom_ref",
                "kind",
                "value_ref",
                "source_order",
                "support_refs",
            },
        }
        expected = required_by_kind.get(kind)
        if expected is None:
            raise RuntimeError("implementation atom kind is outside the allowlist")
        controlled = "controlled_by" in raw_atom or "branch_polarity" in raw_atom
        if controlled:
            expected = expected | {"controlled_by", "branch_polarity"}
        atom = _exact_keys(raw_atom, expected, f"{kind} atom")
        atom_ref = _require_ref(
            atom["atom_ref"],
            ATOM_REF,
            "atom_ref",
            maximum_length=MAXIMUM_ATOM_REF_LENGTH,
        )
        if atom_ref in atom_refs:
            raise RuntimeError("duplicate implementation atom_ref")
        atom_refs.add(atom_ref)
        order = atom["source_order"]
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise RuntimeError("source_order must be a non-negative integer")
        orders.append(order)
        support_refs = atom["support_refs"]
        if (
            not isinstance(support_refs, list)
            or not support_refs
            or support_refs != sorted(set(support_refs))
        ):
            raise RuntimeError("atom Support refs are not a canonical bounded set")
        for support_ref in support_refs:
            _require_ref(
                support_ref,
                SUPPORT_REF,
                "atom support_ref",
                maximum_length=32,
            )
        if controlled:
            _require_ref(
                atom["controlled_by"],
                ATOM_REF,
                "controlled_by",
                maximum_length=MAXIMUM_ATOM_REF_LENGTH,
            )
            if atom["branch_polarity"] not in {"TRUE", "FALSE"}:
                raise RuntimeError("branch polarity is outside the allowlist")
        if kind == "BRANCH":
            if atom["operator"] not in {"NOT", "IS_TRUE", "IS_FALSE", "IS_NULL", "NOT_NULL"}:
                raise RuntimeError("branch operator is outside the allowlist")
            _require_ref(
                atom["operand_ref"],
                SLOT_REF,
                "branch operand_ref",
                maximum_length=MAXIMUM_SLOT_REF_LENGTH,
            )
        elif kind == "CALL_SITE":
            _require_ref(
                atom["target_method_ref"],
                METHOD_REF,
                "call target",
                maximum_length=MAXIMUM_METHOD_REF_LENGTH,
            )
        elif kind == "THROW":
            _require_ref(
                atom["exception_type_ref"],
                TYPE_REF,
                "exception type",
                maximum_length=MAXIMUM_TYPE_REF_LENGTH,
            )
        elif kind == "RETURN":
            _require_ref(
                atom["value_ref"],
                ATOM_REF,
                "return value_ref",
                maximum_length=MAXIMUM_ATOM_REF_LENGTH,
            )
    if orders != sorted(set(orders)):
        raise RuntimeError("implementation atoms are not in unique source order")

    legacy_calls = root["legacy_calls"]
    if not isinstance(legacy_calls, list) or len(legacy_calls) > 64:
        raise RuntimeError("legacy CALLS exceed the frozen budget")
    seen_calls: set[tuple[str, str]] = set()
    for raw_call in legacy_calls:
        call = _exact_keys(
            raw_call,
            {
                "caller_method_ref",
                "callee_method_ref",
                "predicate",
                "modality",
                "call_site_count",
                "source_revision",
                "support_refs",
            },
            "legacy CALLS entry",
        )
        pair = (
            _require_ref(
                call["caller_method_ref"],
                METHOD_REF,
                "CALLS caller",
                maximum_length=MAXIMUM_METHOD_REF_LENGTH,
            ),
            _require_ref(
                call["callee_method_ref"],
                METHOD_REF,
                "CALLS callee",
                maximum_length=MAXIMUM_METHOD_REF_LENGTH,
            ),
        )
        if pair in seen_calls:
            raise RuntimeError("duplicate legacy CALLS entry")
        seen_calls.add(pair)
        if call["predicate"] != "CALLS" or call["modality"] != "JAVA_SOURCE_STATIC_CALL@1":
            raise RuntimeError("legacy CALLS predicate or modality drifted")
        if (
            isinstance(call["call_site_count"], bool)
            or not isinstance(call["call_site_count"], int)
            or call["call_site_count"] < 1
        ):
            raise RuntimeError("legacy CALLS call-site count is invalid")
        if call["source_revision"] != "visible-development":
            raise RuntimeError("legacy CALLS source revision drifted")
        support_refs = call["support_refs"]
        if (
            not isinstance(support_refs, list)
            or support_refs != sorted(set(support_refs))
            or len(support_refs) != call["call_site_count"]
        ):
            raise RuntimeError("legacy CALLS Support count is invalid")
        for support_ref in support_refs:
            _require_ref(
                support_ref,
                SUPPORT_REF,
                "legacy CALLS support_ref",
                maximum_length=32,
            )

    supports = root["supports"]
    if not isinstance(supports, list) or not (1 <= len(supports) <= 64):
        raise RuntimeError("Support records exceed the frozen budget")
    support_refs: set[str] = set()
    source_size = JAVA_SOURCE.stat().st_size
    for raw_support in supports:
        support = _exact_keys(
            raw_support,
            {
                "support_ref",
                "source_revision",
                "locator",
                "byte_start",
                "byte_end",
                "observation_digest",
                "artifact_content_digest",
            },
            "Support record",
        )
        support_ref = _require_ref(
            support["support_ref"],
            SUPPORT_REF,
            "Support ref",
            maximum_length=32,
        )
        if support_ref in support_refs:
            raise RuntimeError("duplicate Support ref")
        support_refs.add(support_ref)
        if support["source_revision"] != "visible-development":
            raise RuntimeError("Support source revision drifted")
        locator = support["locator"]
        if not isinstance(locator, str) or len(locator) > 256:
            raise RuntimeError("Support locator is not canonical")
        match = SUPPORT_LOCATOR.fullmatch(locator)
        if match is None or match.group("path") != REFERENCE_SOURCE_PATH:
            raise RuntimeError("Support locator is not canonical")
        start = support["byte_start"]
        end = support["byte_end"]
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or not 0 <= start < end <= source_size
            or int(match.group("start")) != start
            or int(match.group("end")) != end
        ):
            raise RuntimeError("Support byte range is invalid")
        for field in ("observation_digest", "artifact_content_digest"):
            value = support[field]
            if not isinstance(value, str) or SHA256.fullmatch(value) is None:
                raise RuntimeError(f"Support {field} is invalid")

    referenced_supports = {
        support_ref
        for atom in atoms
        for support_ref in atom["support_refs"]
    } | {
        support_ref
        for call in legacy_calls
        for support_ref in call["support_refs"]
    }
    if referenced_supports != support_refs:
        raise RuntimeError("Support closure is incomplete or has unused records")

    claim_support = root["claim_support"]
    if not isinstance(claim_support, list) or len(claim_support) != len(REQUIRED_CLAIMS):
        raise RuntimeError("claim Support map exceeds the frozen shape")
    observed_claims: list[str] = []
    for raw_entry in claim_support:
        entry = _exact_keys(
            raw_entry,
            {"claim_ref", "support_refs"},
            "claim Support entry",
        )
        claim_ref = entry["claim_ref"]
        claim_refs = entry["support_refs"]
        if (
            not isinstance(claim_ref, str)
            or claim_ref not in REQUIRED_CLAIMS
            or not isinstance(claim_refs, list)
            or not claim_refs
            or claim_refs != sorted(set(claim_refs))
            or not set(claim_refs).issubset(support_refs)
        ):
            raise RuntimeError("claim Support entry is invalid")
        observed_claims.append(claim_ref)
    if tuple(observed_claims) != REQUIRED_CLAIMS:
        raise RuntimeError("claim Support order or coverage drifted")

    expected_projection = _reference_projection()
    if projection != expected_projection:
        raise RuntimeError("reference projection differs from the frozen semantic closure")
    source = JAVA_SOURCE.read_bytes()
    for support in supports:
        start = int(support["byte_start"])
        end = int(support["byte_end"])
        observation = source[start:end].decode("utf-8")
        if (
            support["observation_digest"] != digest_of(observation).value
            or support["artifact_content_digest"] != _content_digest(source).value
        ):
            raise RuntimeError("Support digest does not match the frozen source range")


def _decoded_candidates(value: str) -> tuple[bytes, ...]:
    raw = value.encode("ascii", "ignore")
    candidates: list[bytes] = []
    if len(raw) >= 16:
        for decoder in (
            lambda item: base64.b64decode(item, validate=True),
            lambda item: base64.urlsafe_b64decode(item + b"=" * (-len(item) % 4)),
            lambda item: binascii.unhexlify(item),
        ):
            try:
                decoded = decoder(raw)
            except (ValueError, binascii.Error):
                continue
            if decoded and decoded != raw:
                candidates.append(decoded)
                for decompressor in (gzip.decompress, zlib.decompress):
                    try:
                        expanded = decompressor(decoded)
                    except (OSError, EOFError, zlib.error):
                        continue
                    if expanded:
                        candidates.append(expanded)
    return tuple(candidates)


def _contains_reversible_source(candidate: bytes, source: bytes) -> bool:
    if source in candidate or candidate in source and len(candidate) >= 64:
        return True
    try:
        candidate_text = candidate.decode("utf-8")
        source_text = source.decode("utf-8")
    except UnicodeDecodeError:
        return False
    source_tokens = SOURCE_TOKEN.findall(source_text)
    candidate_tokens = set(SOURCE_TOKEN.findall(candidate_text))
    run = 0
    maximum = 0
    for token in source_tokens:
        if token in candidate_tokens:
            run += 1
            maximum = max(maximum, run)
        else:
            run = 0
    return maximum > 8


def _assert_no_payload(projection: dict[str, object], source: str) -> None:
    policy = json.loads(NO_PAYLOAD_POLICY.read_text(encoding="utf-8"))
    _validate_reference_projection(projection)
    forbidden = set(policy["forbidden_keys"])
    source_bytes = source.encode("utf-8")
    for key, item in _iter_items(projection):
        if key.casefold() in forbidden:
            raise RuntimeError(f"forbidden no-payload key: {key}")
        if isinstance(item, str):
            for decoded in _decoded_candidates(item):
                if _contains_reversible_source(decoded, source_bytes):
                    raise RuntimeError("projection contains reversibly encoded source")
    encoded = json.dumps(projection, ensure_ascii=False, sort_keys=True)
    if source.strip() in encoded:
        raise RuntimeError("projection contains the complete source")
    source_tokens = SOURCE_TOKEN.findall(source)
    projected_tokens = set(SOURCE_TOKEN.findall(encoded))
    run = 0
    maximum = 0
    for token in source_tokens:
        if token in projected_tokens:
            run += 1
            maximum = max(maximum, run)
        else:
            run = 0
    if maximum > int(policy["maximum_contiguous_source_token_run"]):
        raise RuntimeError(f"projection preserves a reversible source-token run: {maximum}")


def _oracle_fileset_digest() -> str:
    entries = []
    for path in (Path(__file__), JAVAC_ORACLE, NO_PAYLOAD_POLICY):
        content = path.read_bytes()
        entries.append(
            {
                "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
                "size": len(content),
                "sha256": _sha256(content),
            }
        )
    return _canonical_digest(
        {"schema": "ITER-007-READINESS-ORACLE-FILESET@1", "entries": entries}
    )


def evaluate() -> dict[str, object]:
    source = JAVA_SOURCE.read_bytes()
    tree_sitter_records = _tree_sitter_records(source)
    javac_records = _javac_records(JAVA_SOURCE)
    if tree_sitter_records != javac_records:
        raise RuntimeError(
            "frontend canonical ranges differ from javac Oracle: "
            f"tree_sitter={tree_sitter_records!r}, javac={javac_records!r}"
        )
    projection = _reference_projection()
    claims = _assert_preservation(projection)
    policy = json.loads(NO_PAYLOAD_POLICY.read_text(encoding="utf-8"))
    if tuple(policy.get("required_claims", ())) != claims:
        raise RuntimeError("no-payload policy required claims drifted")
    expected_legacy_calls = tuple(
        sorted(
            (
                {key: value for key, value in item.items() if key != "support_refs"}
                for item in projection["legacy_calls"]
            ),
            key=lambda item: (
                str(item["caller_method_ref"]),
                str(item["callee_method_ref"]),
            )
        )
    )
    actual_legacy_calls = _legacy_call_targets()
    actual_legacy_semantics = tuple(
        {key: value for key, value in item.items() if key != "support"}
        for item in actual_legacy_calls
    )
    if actual_legacy_semantics != expected_legacy_calls:
        raise RuntimeError(
            "reference projection expands or loses accepted legacy CALLS: "
            f"expected={expected_legacy_calls!r}, actual={actual_legacy_semantics!r}"
        )
    if any(
        not item["support"]
        or len(item["support"]) != item["call_site_count"]
        for item in actual_legacy_calls
    ):
        raise RuntimeError("legacy CALLS Support does not cover every call site")
    _assert_no_payload(projection, source.decode("utf-8"))
    source_text = source.decode("utf-8")
    deliberate_leaks = []
    direct = dict(projection)
    direct["source_text"] = source_text
    deliberate_leaks.append(direct)
    encoded = dict(projection)
    encoded["blob_b64"] = base64.b64encode(source).decode("ascii")
    deliberate_leaks.append(encoded)
    nested = dict(projection)
    nested["ast_dump"] = {
        "encoded_source": base64.b64encode(gzip.compress(source)).decode("ascii")
    }
    deliberate_leaks.append(nested)
    ref_smuggle = dict(projection)
    ref_smuggle["method_ref"] = base64.b64encode(source).decode("ascii")
    deliberate_leaks.append(ref_smuggle)
    canonical_ref_hex_smuggle = dict(projection)
    canonical_ref_hex_smuggle["method_ref"] = "a" + source.hex() + "#m()"
    deliberate_leaks.append(canonical_ref_hex_smuggle)
    distributed_ref_hex_smuggle = json.loads(json.dumps(projection))
    chunks = [source[index : index + 30] for index in range(0, len(source), 30)]
    distributed_ref_hex_smuggle["atoms"].extend(
        {
            "atom_ref": f"atom:call:{ordinal + 6}",
            "kind": "CALL_SITE",
            "target_method_ref": "a" + chunk.hex() + "#m()",
            "source_order": ordinal + 6,
            "support_refs": ["support:4"],
        }
        for ordinal, chunk in enumerate(chunks)
    )
    deliberate_leaks.append(distributed_ref_hex_smuggle)
    for ordinal, leaked in enumerate(deliberate_leaks):
        try:
            _assert_no_payload(leaked, source_text)
        except RuntimeError:
            continue
        raise RuntimeError(f"no-payload Oracle accepted deliberate leak {ordinal}")
    oracle_digest = _oracle_fileset_digest()
    return {
        "schema": "ITER-007-READINESS-ORACLE-RESULT@1",
        "status": "PASS",
        "frontend": _frontend_identity(),
        "visible_development_corpus_digest": _source_manifest_digest(),
        "canonicalization": {
            "status": "PASS",
            "jdk_identity": _jdk_identity(),
            "record_count": len(tree_sitter_records),
            "records_digest": _canonical_digest(tree_sitter_records),
            "oracle_fileset_digest": oracle_digest,
        },
        "information_preservation": {
            "status": "PASS",
            "claims": list(claims),
            "projection_digest": _canonical_digest(projection),
            "oracle_fileset_digest": _canonical_digest(
                {"oracle_fileset_digest": oracle_digest, "role": "preservation"}
            ),
        },
        "legacy_calls_consistency": {
            "status": "PASS",
            "call_count": len(actual_legacy_calls),
            "call_site_count": sum(
                int(item["call_site_count"]) for item in actual_legacy_calls
            ),
            "support_count": sum(len(item["support"]) for item in actual_legacy_calls),
            "calls_digest": _canonical_digest(actual_legacy_calls),
            "oracle_fileset_digest": _canonical_digest(
                {"oracle_fileset_digest": oracle_digest, "role": "legacy-calls"}
            ),
        },
        "information_boundary": {
            "status": "PASS",
            "deliberate_leak_count": len(deliberate_leaks),
            "deliberate_leaks_rejected": len(deliberate_leaks),
            "policy_digest": _sha256(NO_PAYLOAD_POLICY.read_bytes()),
            "oracle_fileset_digest": _canonical_digest(
                {"oracle_fileset_digest": oracle_digest, "role": "boundary"}
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    arguments = parser.parse_args()
    result = evaluate()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        output = Path(arguments.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
