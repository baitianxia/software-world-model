"""Sealed evaluation-only runtime for one dynamic World Model question.

This module owns the trusted orchestration that used to exist only in an
iteration verification harness.  It deliberately executes an already-qualified,
digest-sealed role package; it has no dependency on iteration-only modules and stages no new
Answer, Gateway, Broker, or Projector code at runtime.
"""

from __future__ import annotations

import array
import base64
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
import threading
import time
from typing import Iterable, Mapping, Sequence
from urllib.parse import quote

from software_world_model.ai_infrastructure.pinned_ark_https import (
    ARK_PROVIDER_HOST,
    ARK_PROVIDER_PORT,
)
from software_world_model.ai_infrastructure.pinned_deepseek_https import (
    DEEPSEEK_PROVIDER_HOST,
    DEEPSEEK_PROVIDER_PORT,
)
from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.interface.world_model_browser import PublicRunnerError
from software_world_model.interface.world_model_evaluation import (
    read_world_model_evaluation_page,
)
from software_world_model.interface.world_model_http import ResolvedReadSetInput
from software_world_model.knowledge_engine.structure import (
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    JAVA_STATIC_CALL_PROFILE_REF,
    MAVEN_STRUCTURE_PROFILE_REF,
)


GRANT_SCHEMA = "SWM-WORLD-MODEL-EVALUATION-GRANT@2"
ASSET_ROOT = Path(__file__).resolve(strict=True).with_name(
    "world_model_runtime_assets"
)
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
SANDBOXED_PYTHON_FLAGS = ("-I", "-S", "-B")
ANCESTOR_PARAMETER_COUNT = 64
RUNTIME_DEPENDENCY_PARAMETER_COUNT = 3
_XPKG_RUNTIME_DEPENDENCY_ALIASES = (
    Path("openssl.org/v1"),
    Path("sqlite.org/v3"),
    Path("zlib.net/v1"),
)
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_RAW_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_RESULT_ID = re.compile(r"^structure_view_result_[0-9a-f]{32}$")
_EXPECTED_PROVIDER = {
    "provider_type": "VOLCENGINE_ARK",
    "adapter": "openai-chat-completions-no-tools@8",
    "requested_model": "glm-5-2-260617",
    "observed_model": "glm-5.2",
    "endpoint": (
        "https://ark.cn-beijing.volces.com:443/"
        "api/coding/v3/chat/completions"
    ),
    "credential_reference": "env:ARK_API_KEY",
    "conformance_digest": (
        "sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade"
    ),
    "qualification_digest": (
        "sha256:005b1bf43c76a64d123b0184cdac1a9e844331896e7ede6279875881d9bcc62c"
    ),
}
_BOUNDED_DEEPSEEK_PROVIDER = {
    "provider_type": "DEEPSEEK",
    "adapter": "deepseek-chat-completions-no-tools@4",
    "requested_model": "deepseek-v4-pro",
    "observed_model": "deepseek-v4-pro",
    "endpoint": "https://api.deepseek.com/chat/completions",
    "credential_reference": "env:DEEPSEEK_API_KEY",
}
_PROVIDER_ROUTES = {
    "VOLCENGINE_ARK": {
        "hostname": ARK_PROVIDER_HOST,
        "port": ARK_PROVIDER_PORT,
        "credential_reference": "env:ARK_API_KEY",
        "credential_environment_variable": "ARK_API_KEY",
    },
    "DEEPSEEK": {
        "hostname": DEEPSEEK_PROVIDER_HOST,
        "port": DEEPSEEK_PROVIDER_PORT,
        "credential_reference": "env:DEEPSEEK_API_KEY",
        "credential_environment_variable": "DEEPSEEK_API_KEY",
    },
}
_JAVA_GATEWAY_FREEZE_SCHEMA = "SWM-ITER-006-JAVA-GATEWAY-FREEZE@1"
_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA = (
    "SWM-ITER-007-JAVA-SOURCE-SEMANTICS-GATEWAY-FREEZE@1"
)
_BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA = (
    "SWM-ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-GATEWAY-FREEZE@1"
)
_LEGACY_GATEWAY_FREEZE_SCHEMA = "swm.iter-003.g3b-input-freeze@1"
_ONE_CALL_DISPATCH_POLICY = "ONE_CALL_PER_QUESTION_NO_HIDDEN_RETRY"
_SOURCE_SEMANTICS_DISPATCH_POLICY = (
    "THREE_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY"
)
_BOUNDED_SOURCE_SEMANTICS_DISPATCH_POLICY = (
    "FOUR_TO_SIX_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY"
)
_ROLE_ENTRYPOINTS = {
    "answer": ".g3b/answer_workload.py",
    "gateway": ".g3b/gateway_authorized_workload.py",
    "broker": ".g3b/materialize_citations.py",
    "projector": ".g3b/projection_workload.py",
}
_GATEWAY_INPUT_FILES = {
    "conformance.json",
    "qualification.json",
    "closed-result.json",
    "egress-policy.json",
    "g3b-freeze.json",
}


@dataclass(frozen=True, slots=True)
class RuntimeDependencyCapability:
    alias: Path
    root: Path


@dataclass(frozen=True, slots=True)
class _DocumentReference:
    path: Path
    raw_sha256: str
    document_digest: str | None = None


@dataclass(frozen=True, slots=True)
class _EvaluationGrant:
    document_digest: str
    product_commit: str
    product_tree: str
    stage_root: Path
    stage_manifest_digest: str
    packages: Mapping[str, Path]
    gateway_input: Path
    provider: Mapping[str, object]
    forbidden_inputs: Mapping[str, Path]
    disclosure_digest: str
    deterministic_qualification_digest: str
    held_out_suite_digest: str
    independent_evaluator_digest: str
    launcher_manifest_digest: str
    provider_subject_digest: str
    authorization_at: str
    authorization_ref: str


@dataclass(frozen=True, slots=True)
class _CitationRecord:
    result_id: str
    seal_digest: str
    projection_path: Path
    projection_digest: str


@dataclass(frozen=True, slots=True)
class _ExecutorRequestRecord:
    read_set_id: str
    run_root: Path
    citations: Mapping[str, _CitationRecord]


class SealedWorldModelExecutor:
    """Run accepted role packages behind exact file/network capabilities."""

    def __init__(
        self,
        *,
        grant: _EvaluationGrant,
        authority_database: Path,
        session_root: Path,
        socket_root: Path,
        timeout_seconds: float,
    ) -> None:
        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")
        if not SANDBOX_EXEC.is_file():
            raise RuntimeError("/usr/bin/sandbox-exec is unavailable")
        self._grant = grant
        self._authority_database = _canonical_file(
            authority_database, "authority database"
        )
        self.session_root = _new_private_directory(session_root, "session root")
        self._requests_root = self.session_root / "requests"
        self._requests_root.mkdir(mode=0o700)
        self._socket_root = _new_private_directory(socket_root, "socket root")
        if len(os.fsencode(str(self._socket_root / "r999999" / "01" / "gateway.sock"))) >= 100:
            raise ValueError("socket_root is too long for an exact AF_UNIX endpoint")
        self._timeout_seconds = timeout_seconds
        self._runtime = _runtime_capabilities()
        self._lock = threading.Lock()
        self._records: dict[str, _ExecutorRequestRecord | None] = {}
        self._ordinal = 0

        outer, workspace_forbidden = _outer_reachability(
            self._authority_database
        )
        self._forbidden = {
            **workspace_forbidden,
            "authority_database": self._authority_database,
            "evidence_store": self._authority_database,
            **grant.forbidden_inputs,
        }
        startup_root = self.session_root / "startup"
        startup_root.mkdir(mode=0o700)
        (
            self._gateway_input,
            self._authorization_receipt_digest,
        ) = _prepare_gateway_input(grant, startup_root / "gateway-input")
        self._provider_call_count = _gateway_call_count(self._gateway_input)
        self._provider_descriptor_count = _gateway_descriptor_count(
            self._gateway_input
        )
        self._provider_type = _provider_type(grant.provider)
        bootstrap_connection, bootstrap = _provision_provider_socket(
            provider_type=self._provider_type
        )
        bootstrap_connection.close()
        self._provider_address = _text(
            bootstrap.get("selected_address"), "selected Provider address"
        )
        _write_new(
            startup_root / "provider-bootstrap.json",
            canonical_json_bytes(bootstrap),
        )
        preflight = _run_preflight(
            evidence_root=startup_root,
            stage_root=grant.stage_root,
            socket_stage_root=self._socket_root,
            packages=grant.packages,
            gateway_input=self._gateway_input,
            forbidden=self._forbidden,
            runtime=self._runtime,
            provider_address=self._provider_address,
            provider_type=self._provider_type,
        )
        stage_digest = digest_of(_tree_manifest(grant.stage_root)).value
        if (
            preflight.get("status") != "PASS"
            or preflight.get("protected_stage_unchanged") is not True
            or preflight.get("production_activation") != "NOT_EXECUTED"
            or stage_digest != grant.stage_manifest_digest
        ):
            raise RuntimeError("current OS isolation preflight failed closed")
        self._startup_preflight_digest = _digest_text(
            preflight.get("document_digest"), "startup preflight digest"
        )
        startup_core = {
            "schema": "SWM-WORLD-MODEL-STARTUP-RECEIPT@1",
            "environment": "EVALUATION_ONLY",
            "grant_digest": grant.document_digest,
            "evaluation_subject_status": "CANDIDATE",
            "evaluation_subject_commit": grant.product_commit,
            "evaluation_subject_tree": grant.product_tree,
            "stage_manifest_digest": stage_digest,
            "launcher_manifest_digest": grant.launcher_manifest_digest,
            "provider_subject_digest": grant.provider_subject_digest,
            "provider_type": self._provider_type,
            "disclosure_authorization_digest": grant.disclosure_digest,
            "gateway_authorization_receipt_digest": (
                self._authorization_receipt_digest
            ),
            "outer_reachability": outer,
            "provider_bootstrap_digest": bootstrap["document_digest"],
            "startup_preflight_digest": self._startup_preflight_digest,
            "dispatch_policy": _dispatch_policy(self._provider_call_count),
            "production_activation": "NOT_EXECUTED",
        }
        startup = {
            **startup_core,
            "document_digest": digest_of(startup_core).value,
        }
        _write_new(
            self.session_root / "startup-receipt.json",
            canonical_json_bytes(startup),
        )
        self._startup_receipt_digest = startup["document_digest"]

    @classmethod
    def from_grant(
        cls,
        *,
        grant_path: Path,
        authority_database: Path,
        session_root: Path,
        socket_root: Path,
        timeout_seconds: float,
    ) -> "SealedWorldModelExecutor":
        grant = _load_evaluation_grant(grant_path)
        return cls(
            grant=grant,
            authority_database=authority_database,
            session_root=session_root,
            socket_root=socket_root,
            timeout_seconds=timeout_seconds,
        )

    def health(self) -> Mapping[str, object]:
        return {
            "status": "ready",
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_status": "CANDIDATE",
            "evaluation_subject_commit": self._grant.product_commit,
            "evaluation_subject_tree": self._grant.product_tree,
            "evaluation_grant_digest": self._grant.document_digest,
            "deterministic_qualification_digest": (
                self._grant.deterministic_qualification_digest
            ),
            "held_out_suite_digest": self._grant.held_out_suite_digest,
            "independent_evaluator_digest": (
                self._grant.independent_evaluator_digest
            ),
            "startup_preflight_digest": self._startup_preflight_digest,
            "startup_receipt_digest": self._startup_receipt_digest,
            "stage_manifest_digest": self._grant.stage_manifest_digest,
            "launcher_manifest_digest": self._grant.launcher_manifest_digest,
            "provider_subject_digest": self._grant.provider_subject_digest,
            "provider_type": self._provider_type,
            "gateway_authorization_receipt_digest": (
                self._authorization_receipt_digest
            ),
            "dispatch_policy": _dispatch_policy(self._provider_call_count),
            "production_activation": "NOT_EXECUTED",
        }

    def execute(
        self,
        *,
        request_id: str,
        read_set: ResolvedReadSetInput,
        question: str,
    ) -> Mapping[str, object]:
        read_set.require_valid()
        with self._lock:
            if request_id in self._records:
                raise PublicRunnerError(
                    "REQUEST_ID_CONFLICT",
                    "request_id was already used and will not be replayed",
                    status="409 Conflict",
                )
            self._records[request_id] = None
            self._ordinal += 1
            ordinal = self._ordinal
            request_token = sha256(request_id.encode("ascii")).hexdigest()[:12]
            evidence_root = self._requests_root / f"{ordinal:06d}-{request_token}"
            evidence_root.mkdir(mode=0o700)
            runs_root = evidence_root / "runs"
            runs_root.mkdir(mode=0o700)
            socket_stage_root = self._socket_root / f"r{ordinal:06d}"
            socket_stage_root.mkdir(mode=0o700)
            run_key = f"question-{ordinal:06d}-{request_token}"
            terminal = _run_one(
                index=1,
                run_key=run_key,
                run_number=ordinal,
                question=question,
                read_set=read_set,
                runs_root=runs_root,
                socket_stage_root=socket_stage_root,
                packages=self._grant.packages,
                gateway_input=self._gateway_input,
                forbidden=self._forbidden,
                runtime=self._runtime,
                provider_address=self._provider_address,
                provider_type=self._provider_type,
                implementation_commit=self._grant.product_commit,
                evaluation_grant_digest=self._grant.document_digest,
                disclosure_authorization_digest=self._grant.disclosure_digest,
                authorization_receipt_digest=(
                    self._authorization_receipt_digest
                ),
                authority_database=self._authority_database,
                timeout_seconds=self._timeout_seconds,
            )
            result, record = self._public_result(
                request_id=request_id,
                read_set=read_set,
                question=question,
                terminal=terminal,
                run_root=runs_root / "01",
            )
            self._records[request_id] = record
            _write_new(
                evidence_root / "browser-result.json",
                canonical_json_bytes(result),
            )
            return result

    def citation(
        self,
        *,
        request_id: str,
        result_id: str,
    ) -> Mapping[str, object]:
        record = self._records.get(request_id)
        if record is None:
            raise PublicRunnerError(
                "RESULT_NOT_FOUND",
                "request has no completed, verified result",
                status="404 Not Found",
            )
        citation = record.citations.get(result_id)
        if citation is None:
            raise PublicRunnerError(
                "CITATION_BINDING_INVALID",
                "citation is not bound to this request and result",
                status="404 Not Found",
            )
        try:
            if _sha256_file(citation.projection_path) != citation.projection_digest:
                raise ValueError("projection file digest drifted")
            value = _load_json(citation.projection_path)
            if (
                value.get("schema") != "swm.iter-003.g3b-citation-projection@1"
                or value.get("status") != "PASS"
                or value.get("environment") != "EVALUATION_ONLY"
                or value.get("production_activation") != "NOT_EXECUTED"
                or value.get("network_operation_count") != 0
                or value.get("answer_return_port") is not False
                or value.get("result_id") != citation.result_id
                or value.get("seal_digest") != citation.seal_digest
                or not isinstance(value.get("citation_projection"), dict)
            ):
                raise ValueError("projection binding is invalid")
        except (OSError, ValueError) as exc:
            raise PublicRunnerError(
                "CITATION_VERIFICATION_FAILED",
                "the independently projected citation failed verification",
                status="409 Conflict",
            ) from exc
        return {
            "request_id": request_id,
            "result_id": result_id,
            "seal_digest": citation.seal_digest,
            "projection_digest": citation.projection_digest,
            "environment": "EVALUATION_ONLY",
            "network_operation_count": 0,
            "answer_return_port": False,
            "citation_projection": value["citation_projection"],
            "production_activation": "NOT_EXECUTED",
        }

    def _public_result(
        self,
        *,
        request_id: str,
        read_set: ResolvedReadSetInput,
        question: str,
        terminal: Mapping[str, object],
        run_root: Path,
    ) -> tuple[dict[str, object], _ExecutorRequestRecord]:
        terminal_path = run_root / "terminal.json"
        persisted_terminal = _load_json(terminal_path)
        provisioned_calls = self._provider_call_count
        handed_off_connections = self._provider_descriptor_count
        if (
            terminal.get("status") != "SUCCESS"
            or persisted_terminal.get("status") != "SUCCESS"
            or persisted_terminal.get("attempt_count") != 1
            or persisted_terminal.get("selective_retry_count") != 0
            or persisted_terminal.get("provider_connection_handoff_count")
            != handed_off_connections
            or persisted_terminal.get("gateway_listener_handoff_count") != 1
            or persisted_terminal.get("production_activation") != "NOT_EXECUTED"
            or _document_digest(persisted_terminal)
            != persisted_terminal.get("document_digest")
        ):
            raise PublicRunnerError(
                "WORLD_MODEL_EXECUTION_FAILED",
                "the isolated World Model run did not produce a verified terminal",
            )
        summary_path = _verified_file_reference(
            persisted_terminal.get("answer_summary"), run_root
        )
        summary = _load_json(summary_path)
        expected_calls = summary.get("provider_call_count")
        if (
            type(expected_calls) is not int
            or (
                provisioned_calls == 6
                and not 4 <= expected_calls <= 6
            )
            or (
                provisioned_calls != 6
                and expected_calls != provisioned_calls
            )
        ):
            raise RuntimeError("answer Provider call count is outside its protocol")
        timing = _load_json(run_root / "timing.json")
        if (
            _document_digest(timing) != timing.get("document_digest")
            or timing.get("run_key") != persisted_terminal.get("run_key")
            or timing.get("terminal_document_digest")
            != persisted_terminal.get("document_digest")
            or timing.get("terminal_file_digest") != _sha256_file(terminal_path)
            or timing.get("production_activation") != "NOT_EXECUTED"
        ):
            raise RuntimeError("question timing receipt is not bound to its terminal")
        page_path = run_root / "answer-output" / "evaluation.html"
        page_digest = _digest_text(summary.get("page_digest"), "page digest")
        page = read_world_model_evaluation_page(
            page_path,
            expected_implementation_commit=self._grant.product_commit,
            expected_page_digest=page_digest,
        )
        expected_snapshot_ids = [
            item.snapshot_id.value
            for item in read_set.registration.snapshot_bindings
        ]
        observed_snapshot_ids = [
            item.get("snapshot_id")
            for item in page.get("read_binding", {}).get("snapshots", [])
            if isinstance(item, dict)
        ]
        stages = page.get("authority_chain", {}).get("stages", [])
        if (
            page.get("mode") != "WORLD_MODEL"
            or page.get("environment") != "EVALUATION_ONLY"
            or page.get("evaluation_only") is not True
            or page.get("implementation_commit") != self._grant.product_commit
            or page.get("request", {}).get("original_question") != question
            or page.get("read_binding", {}).get("read_set_digest")
            != read_set.registration.read_set_digest.value
            or observed_snapshot_ids != expected_snapshot_ids
            or not isinstance(stages, list)
            or len(stages) != 10
            or page.get("execution_boundary", {}).get("provider_call_count")
            != expected_calls
            or page.get("execution_boundary", {}).get("network_operation_count")
            != expected_calls
            or page.get("execution_boundary", {}).get("source_access_allowed") is not False
            or page.get("execution_boundary", {}).get("evidence_payload_access_allowed") is not False
            or summary.get("source_access_count") != 0
            or summary.get("evidence_payload_access_count") != 0
            or summary.get("authority_database_access_count") != 0
            or summary.get("product_oracle_read_count") != 0
            or summary.get("baseline_result_read_count") != 0
            or summary.get("provider_call_count") != expected_calls
            or summary.get("network_operation_count") != expected_calls
            or summary.get("production_activation") != "NOT_EXECUTED"
        ):
            raise RuntimeError("verified page violates the dynamic browser boundary")

        citations: dict[str, _CitationRecord] = {}
        public_citations: list[dict[str, object]] = []
        terminal_citations = persisted_terminal.get("citation_projections")
        if not isinstance(terminal_citations, list):
            raise RuntimeError("terminal citation index is invalid")
        for item in terminal_citations:
            if not isinstance(item, dict):
                raise RuntimeError("terminal citation entry is invalid")
            result_id = _result_id(item.get("result_id"))
            seal_digest = _digest_text(item.get("seal_digest"), "citation seal")
            projection_path = _verified_file_reference(
                item.get("projection"), run_root
            )
            projection_digest = _digest_text(
                item.get("projection", {}).get("digest"), "projection digest"
            )
            if result_id in citations:
                raise RuntimeError("duplicate citation Result ID")
            citation = _CitationRecord(
                result_id=result_id,
                seal_digest=seal_digest,
                projection_path=projection_path,
                projection_digest=projection_digest,
            )
            citations[result_id] = citation
            public_citations.append(
                {
                    "result_id": result_id,
                    "seal_digest": seal_digest,
                    "projection_digest": projection_digest,
                    "url": (
                        f"/v1/world-model/requests/{quote(request_id, safe='')}/"
                        f"citations/{quote(result_id, safe='')}"
                    ),
                }
            )
        record = _ExecutorRequestRecord(
            read_set_id=read_set.registration.read_set_id.value,
            run_root=run_root,
            citations=citations,
        )
        result = {
            "request_id": request_id,
            "read_set_id": read_set.registration.read_set_id.value,
            "question": question,
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_status": "CANDIDATE",
            "evaluation_subject_commit": self._grant.product_commit,
            "evaluation_subject_tree": self._grant.product_tree,
            "page_digest": page_digest,
            "page": page,
            "citations": public_citations,
            "execution": {
                "attempt_count": 1,
                "provider_call_count": expected_calls,
                "network_operation_count": expected_calls,
                "selective_retry_count": 0,
                "provider_type": self._provider_type,
                "source_access_count": 0,
                "evidence_payload_access_count": 0,
                "model_call_id": summary.get("model_call_id"),
                "model_fingerprint": summary.get("model_actual_fingerprint"),
                "model_call_ids": summary.get(
                    "model_call_ids",
                    [summary["model_call_id"]]
                    if isinstance(summary.get("model_call_id"), str)
                    else [],
                ),
                "model_fingerprints": summary.get(
                    "model_actual_fingerprints",
                    [summary["model_actual_fingerprint"]]
                    if isinstance(summary.get("model_actual_fingerprint"), str)
                    else [],
                ),
                "elapsed_milliseconds": timing.get("request_elapsed_milliseconds"),
                "terminal_digest": persisted_terminal.get("document_digest"),
            },
            "production_activation": "NOT_EXECUTED",
        }
        return result, record


def _load_evaluation_grant(path: Path) -> _EvaluationGrant:
    grant_path = _canonical_file(path, "evaluation grant")
    document = _load_json(grant_path)
    expected_top = {
        "schema",
        "environment",
        "live_dispatch_authorized",
        "disclosure_authorization",
        "evaluation_subject",
        "provider",
        "launcher_files",
        "forbidden_inputs",
        "production_activation",
        "document_digest",
    }
    _exact_keys(document, expected_top, "evaluation grant")
    if document.get("schema") != GRANT_SCHEMA:
        raise ValueError("evaluation grant schema is unsupported")
    core = {key: value for key, value in document.items() if key != "document_digest"}
    expected_digest = digest_of([GRANT_SCHEMA, core]).value
    if document.get("document_digest") != expected_digest:
        raise ValueError("evaluation grant digest is invalid")
    if (
        document.get("environment") != "EVALUATION_ONLY"
        or document.get("production_activation") != "NOT_EXECUTED"
    ):
        raise ValueError("evaluation grant cannot activate production")

    disclosure = _object(
        document.get("disclosure_authorization"),
        {
            "status",
            "authorized_by",
            "authorized_at",
            "authorization_ref",
            "payload_boundary",
            "document_digest",
        },
        "disclosure authorization",
    )
    disclosure_core = {
        key: value for key, value in disclosure.items() if key != "document_digest"
    }
    disclosure_digest = digest_of(
        ["SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1", disclosure_core]
    ).value
    if disclosure.get("document_digest") != disclosure_digest:
        raise ValueError("disclosure authorization digest is invalid")
    if (
        document.get("live_dispatch_authorized") is not True
        or disclosure.get("status") != "AUTHORIZED"
        or disclosure.get("authorized_by") != "user"
        or disclosure.get("payload_boundary")
        != "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
    ):
        raise PublicRunnerError(
            "LIVE_DISPATCH_NOT_AUTHORIZED",
            "evaluation grant does not contain explicit user disclosure authorization",
            status="503 Service Unavailable",
        )
    authorization_at = _text(
        disclosure.get("authorized_at"), "authorization time"
    )
    _aware_time(authorization_at)
    authorization_ref = _text(
        disclosure.get("authorization_ref"), "authorization ref"
    )

    subject = _object(
        document.get("evaluation_subject"),
        {
            "status",
            "commit",
            "tree",
            "stage_root",
            "stage_manifest_digest",
            "deterministic_qualification",
            "held_out_suite",
            "independent_evaluator",
            "gateway_input_sha256",
            "role_entrypoint_sha256",
        },
        "evaluation subject",
    )
    if subject.get("status") != "CANDIDATE":
        raise ValueError("evaluation subject must be an unaccepted candidate")
    commit = _commit(subject.get("commit"))
    tree = _commit(subject.get("tree"))
    stage_root = _canonical_directory(
        Path(_text(subject.get("stage_root"), "stage root")), "stage root"
    )
    stage_manifest_digest = _digest_text(
        subject.get("stage_manifest_digest"), "stage manifest digest"
    )
    observed_stage_digest = digest_of(_tree_manifest(stage_root)).value
    if observed_stage_digest != stage_manifest_digest:
        raise ValueError("candidate role package stage manifest drifted")

    qualification_ref = _document_reference(
        subject.get("deterministic_qualification"),
        "deterministic qualification",
    )
    suite_ref = _document_reference(
        subject.get("held_out_suite"), "held-out suite"
    )
    evaluator_ref = _document_reference(
        subject.get("independent_evaluator"),
        "independent evaluator",
        allow_no_document_digest=True,
    )
    qualification = _verified_document(
        qualification_ref, "deterministic qualification"
    )
    suite = _verified_document(suite_ref, "held-out suite")
    _verify_raw_sha256(
        evaluator_ref.path,
        evaluator_ref.raw_sha256,
        "independent evaluator",
    )

    packages_root = _canonical_directory(
        stage_root / "packages", "accepted packages root"
    )
    packages = {
        role: _canonical_directory(packages_root / role, f"{role} package")
        for role in ("answer", "gateway", "broker", "projector")
    }
    entrypoint_hashes = _string_map(
        subject.get("role_entrypoint_sha256"), "role entrypoint digests"
    )
    if set(entrypoint_hashes) != set(_ROLE_ENTRYPOINTS):
        raise ValueError("role entrypoint digest set is not closed")
    for role, relative in _ROLE_ENTRYPOINTS.items():
        _verify_raw_sha256(
            packages[role] / relative,
            entrypoint_hashes[role],
            f"{role} entrypoint",
        )

    gateway_input = _canonical_directory(
        stage_root / "gateway-input", "gateway input"
    )
    gateway_hashes = _string_map(
        subject.get("gateway_input_sha256"), "gateway input digests"
    )
    if set(gateway_hashes) != _GATEWAY_INPUT_FILES:
        raise ValueError("gateway input digest set is not closed")
    if {item.name for item in gateway_input.iterdir()} != _GATEWAY_INPUT_FILES:
        raise ValueError("gateway input directory contains missing or extra files")
    for name, expected in gateway_hashes.items():
        _verify_raw_sha256(gateway_input / name, expected, f"gateway input {name}")

    expected_provider, java_qualification = _provider_binding_for_gateway_input(
        gateway_input
    )
    qualification_binding_field = _gateway_qualification_binding_field(
        gateway_input
    )
    provider = _object(
        document.get("provider"), set(_EXPECTED_PROVIDER), "Provider subject"
    )
    if dict(provider) != expected_provider:
        raise ValueError("Provider subject differs from the qualified exact endpoint")

    launcher_hashes = _string_map(
        document.get("launcher_files"), "launcher file digests"
    )
    launcher_files = _launcher_files(
        include_bounded=(
            _gateway_call_count(gateway_input) == 6
        )
    )
    if set(launcher_hashes) != set(launcher_files):
        raise ValueError("launcher file digest set is not closed")
    for label, file_path in launcher_files.items():
        _verify_raw_sha256(
            file_path, launcher_hashes[label], f"launcher file {label}"
        )
    launcher_manifest_digest = digest_of(
        ["SWM-WORLD-MODEL-LAUNCHER-MANIFEST@1", launcher_hashes]
    ).value

    evaluator_digest = _sha256_file(evaluator_ref.path)
    if (
        qualification.get("schema")
        != "SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@1"
        or qualification.get("status") != "PASS"
        or qualification.get("evaluation_subject_status") != "CANDIDATE"
        or qualification.get("implementation_commit") != commit
        or qualification.get("implementation_tree") != tree
        or qualification.get("stage_manifest_digest")
        != stage_manifest_digest
        or qualification.get("launcher_manifest_digest")
        != launcher_manifest_digest
        or qualification.get("held_out_suite_digest")
        != suite.get("document_digest")
        or qualification.get("independent_evaluator_digest")
        != evaluator_digest
        or qualification.get("focused_tests_pass") is not True
        or qualification.get("candidate_answer_package_tests_pass") is not True
        or qualification.get("deterministic_product_probe_pass") is not True
        or not isinstance(
            qualification.get("deterministic_product_probe_digest"), str
        )
        or not _DIGEST.fullmatch(
            str(qualification.get("deterministic_product_probe_digest"))
        )
        or qualification.get("full_regression_pass") is not True
        or qualification.get("docs_check_pass") is not True
        or qualification.get("external_model_called") is not False
        or qualification.get("production_activation") != "NOT_EXECUTED"
        or any(
            field in qualification
            for field in {
                "java_capability_qualification",
                "java_source_semantics_capability_qualification",
                "bounded_java_source_semantics_capability_qualification",
            }
            if field != qualification_binding_field
        )
        or (
            qualification_binding_field is not None
            and qualification.get(qualification_binding_field)
            != java_qualification
        )
        or suite.get("schema") != "SWM-WORLD-MODEL-HELD-OUT-SUITE@2"
        or suite.get("environment") != "EVALUATION_ONLY"
        or suite.get("evaluation_subject_commit") != commit
        or suite.get("evaluation_subject_tree") != tree
        or suite.get("sealed_before_world_model_results") is not True
        or suite.get("world_model_result_count_at_seal") != 0
        or suite.get("controlled_direct_result_count_at_seal") != 0
        or suite.get("mature_source_agent_result_count_at_seal") != 0
        or suite.get("comparison_surfaces")
        != ["WORLD_MODEL", "CONTROLLED_DIRECT", "MATURE_SOURCE_AGENT"]
        or not isinstance(suite.get("comparison_protocols"), dict)
        or not isinstance(suite.get("source_closures"), dict)
        or suite.get("production_activation") != "NOT_EXECUTED"
    ):
        raise ValueError(
            "candidate deterministic qualification is not an exact PASS subject"
        )

    forbidden_values = _object(
        document.get("forbidden_inputs"),
        {"product_oracle", "baseline_result", "independent_evaluator"},
        "forbidden inputs",
    )
    forbidden: dict[str, Path] = {}
    for label, value in forbidden_values.items():
        reference = _document_reference(
            value, f"forbidden {label}", allow_no_document_digest=True
        )
        _verify_raw_sha256(reference.path, reference.raw_sha256, label)
        forbidden[label] = reference.path
    if forbidden["independent_evaluator"] != evaluator_ref.path:
        raise ValueError("independent evaluator forbidden target is inconsistent")

    return _EvaluationGrant(
        document_digest=expected_digest,
        product_commit=commit,
        product_tree=tree,
        stage_root=stage_root,
        stage_manifest_digest=stage_manifest_digest,
        packages=packages,
        gateway_input=gateway_input,
        provider=provider,
        forbidden_inputs=forbidden,
        disclosure_digest=disclosure_digest,
        deterministic_qualification_digest=_digest_text(
            qualification.get("document_digest"),
            "deterministic qualification digest",
        ),
        held_out_suite_digest=_digest_text(
            suite.get("document_digest"), "held-out suite digest"
        ),
        independent_evaluator_digest=evaluator_digest,
        launcher_manifest_digest=launcher_manifest_digest,
        provider_subject_digest=digest_of(
            ["SWM-WORLD-MODEL-PROVIDER-SUBJECT@1", provider]
        ).value,
        authorization_at=authorization_at,
        authorization_ref=authorization_ref,
    )


def _provider_binding_for_gateway_input(
    gateway_input: Path,
) -> tuple[dict[str, object], dict[str, object] | None]:
    """Derive the provider qualification from the sealed Gateway authority.

    The legacy package remains pinned to its inherited ITER-003 qualification.
    A Java package must carry a newly closed qualification, and the grant cannot
    substitute its digest because this function derives it from the protected
    Gateway input files.
    """

    freeze = _load_json(gateway_input / "g3b-freeze.json")
    schema = freeze.get("schema")
    if schema == _LEGACY_GATEWAY_FREEZE_SCHEMA:
        return dict(_EXPECTED_PROVIDER), None
    if schema == _BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA:
        return _bounded_java_source_semantics_provider_binding(
            gateway_input,
            freeze,
        )
    if schema == _JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA:
        return _java_source_semantics_provider_binding(gateway_input, freeze)
    if schema != _JAVA_GATEWAY_FREEZE_SCHEMA:
        raise ValueError("qualified Gateway freeze schema is unsupported")

    from software_world_model.ai_infrastructure.java_model_egress_qualification import (
        JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST,
        load_java_gateway_qualification_binding,
    )

    binding = load_java_gateway_qualification_binding(
        qualification_path=gateway_input / "qualification.json",
        closed_result_path=gateway_input / "closed-result.json",
        policy_path=gateway_input / "egress-policy.json",
    )
    expected_freeze_keys = {
        "schema",
        "freeze_ref",
        "environment",
        "strategy_ref",
        "prompt_ref",
        "proposal_vocabulary_ref",
        "capability_qualification_document_digest",
        "closed_capability_result_digest",
        "egress_policy_digest",
        "conformance_result_ref",
        "conformance_result_digest",
        "permission_digest",
        "production_activation",
        "document_digest",
    }
    _exact_keys(freeze, expected_freeze_keys, "Java Gateway freeze")
    freeze_core = {
        key: value for key, value in freeze.items() if key != "document_digest"
    }
    if (
        freeze.get("freeze_ref")
        != "ITER-006-JAVA-PRODUCT-GATEWAY-CANDIDATE@1"
        or freeze.get("environment") != "EVALUATION_ONLY"
        or freeze.get("strategy_ref")
        != "model-snapshot-first-world-model-answer@1.1.0"
        or freeze.get("prompt_ref")
        != "snapshot-first-world-model-proposal-prompt@4"
        or freeze.get("proposal_vocabulary_ref")
        != "world-model-authority-proposal-vocabulary@2"
        or freeze.get("capability_qualification_document_digest")
        != binding.qualification_document_digest.value
        or freeze.get("closed_capability_result_digest")
        != binding.closed_capability_result_digest.value
        or freeze.get("egress_policy_digest")
        != JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST
        or freeze.get("conformance_result_digest")
        != _EXPECTED_PROVIDER["conformance_digest"]
        or freeze.get("production_activation") != "NOT_EXECUTED"
        or freeze.get("document_digest")
        != digest_of([_JAVA_GATEWAY_FREEZE_SCHEMA, freeze_core]).value
    ):
        raise ValueError("Java Gateway freeze is not an exact qualified authority")
    permission_digest = _digest_text(
        freeze.get("permission_digest"), "Java Gateway permission digest"
    )
    expected_provider = dict(_EXPECTED_PROVIDER)
    expected_provider["qualification_digest"] = (
        binding.capability_qualification_digest.value
    )
    qualification = {
        "capability_qualification_ref": binding.capability_qualification_ref,
        "capability_qualification_digest": (
            binding.capability_qualification_digest.value
        ),
        "capability_qualification_document_digest": (
            binding.qualification_document_digest.value
        ),
        "closed_capability_result_digest": (
            binding.closed_capability_result_digest.value
        ),
        "conformance_result_ref": _text(
            freeze.get("conformance_result_ref"),
            "Java Gateway conformance result reference",
        ),
        "conformance_result_digest": _digest_text(
            freeze.get("conformance_result_digest"),
            "Java Gateway conformance result digest",
        ),
        "java_gateway_freeze_digest": _digest_text(
            freeze.get("document_digest"), "Java Gateway freeze digest"
        ),
        "permission_digest": permission_digest,
    }
    return expected_provider, qualification


def _java_source_semantics_provider_binding(
    gateway_input: Path,
    freeze: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    from software_world_model.ai_infrastructure.java_source_semantics_model_egress_qualification import (
        JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST,
        load_java_source_semantics_gateway_qualification_binding,
    )

    binding = load_java_source_semantics_gateway_qualification_binding(
        qualification_path=gateway_input / "qualification.json",
        closed_result_path=gateway_input / "closed-result.json",
        policy_path=gateway_input / "egress-policy.json",
    )
    expected_freeze_keys = {
        "schema",
        "freeze_ref",
        "environment",
        "strategy_ref",
        "prompt_ref",
        "proposal_vocabulary_ref",
        "capability_qualification_document_digest",
        "closed_capability_result_digest",
        "egress_policy_digest",
        "conformance_result_ref",
        "conformance_result_digest",
        "permission_digest",
        "production_activation",
        "document_digest",
    }
    _exact_keys(freeze, expected_freeze_keys, "source-semantics Gateway freeze")
    freeze_core = {
        key: value for key, value in freeze.items() if key != "document_digest"
    }
    if (
        freeze.get("freeze_ref")
        != "ITER-007-JAVA-SOURCE-SEMANTICS-PRODUCT-GATEWAY-CANDIDATE@1"
        or freeze.get("environment") != "EVALUATION_ONLY"
        or freeze.get("strategy_ref")
        != "model-snapshot-first-world-model-answer@1.2.2"
        or freeze.get("prompt_ref")
        != "java-source-semantics-world-model-prompt@3"
        or freeze.get("proposal_vocabulary_ref")
        != "java-source-semantics-world-model-vocabulary@3"
        or freeze.get("capability_qualification_document_digest")
        != binding.qualification_document_digest.value
        or freeze.get("closed_capability_result_digest")
        != binding.closed_capability_result_digest.value
        or freeze.get("egress_policy_digest")
        != JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
        or freeze.get("conformance_result_digest")
        != _EXPECTED_PROVIDER["conformance_digest"]
        or freeze.get("production_activation") != "NOT_EXECUTED"
        or freeze.get("document_digest")
        != digest_of(
            [_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA, freeze_core]
        ).value
    ):
        raise ValueError(
            "source-semantics Gateway freeze is not an exact qualified authority"
        )
    permission_digest = _digest_text(
        freeze.get("permission_digest"),
        "source-semantics Gateway permission digest",
    )
    expected_provider = dict(_EXPECTED_PROVIDER)
    expected_provider["qualification_digest"] = (
        binding.capability_qualification_digest.value
    )
    qualification = {
        "capability_qualification_ref": binding.capability_qualification_ref,
        "capability_qualification_digest": (
            binding.capability_qualification_digest.value
        ),
        "capability_qualification_document_digest": (
            binding.qualification_document_digest.value
        ),
        "closed_capability_result_digest": (
            binding.closed_capability_result_digest.value
        ),
        "conformance_result_ref": _text(
            freeze.get("conformance_result_ref"),
            "source-semantics Gateway conformance result reference",
        ),
        "conformance_result_digest": _digest_text(
            freeze.get("conformance_result_digest"),
            "source-semantics Gateway conformance result digest",
        ),
        "java_source_semantics_gateway_freeze_digest": _digest_text(
            freeze.get("document_digest"),
            "source-semantics Gateway freeze digest",
        ),
        "permission_digest": permission_digest,
    }
    return expected_provider, qualification


def _bounded_java_source_semantics_provider_binding(
    gateway_input: Path,
    freeze: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    from software_world_model.ai_infrastructure.bounded_java_source_semantics_model_egress_qualification import (
        BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST,
        load_bounded_java_source_semantics_gateway_qualification_binding,
    )
    from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
        DeepSeekModelConfiguration,
    )
    from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
        load_deepseek_chat_conformance_qualification,
    )

    binding = load_bounded_java_source_semantics_gateway_qualification_binding(
        qualification_path=gateway_input / "qualification.json",
        closed_result_path=gateway_input / "closed-result.json",
        policy_path=gateway_input / "egress-policy.json",
    )
    configuration = DeepSeekModelConfiguration()
    conformance = load_deepseek_chat_conformance_qualification(
        gateway_input / "conformance.json",
        configuration,
    )
    expected_freeze_keys = {
        "schema",
        "freeze_ref",
        "environment",
        "strategy_ref",
        "prompt_ref",
        "proposal_vocabulary_ref",
        "capability_qualification_document_digest",
        "closed_capability_result_digest",
        "egress_policy_digest",
        "conformance_result_ref",
        "conformance_result_digest",
        "permission_digest",
        "production_activation",
        "document_digest",
    }
    _exact_keys(
        freeze,
        expected_freeze_keys,
        "bounded source-semantics Gateway freeze",
    )
    freeze_core = {
        key: value for key, value in freeze.items() if key != "document_digest"
    }
    if (
        freeze.get("freeze_ref")
        != "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-PRODUCT-GATEWAY-CANDIDATE@1"
        or freeze.get("environment") != "EVALUATION_ONLY"
        or freeze.get("strategy_ref")
        != "model-snapshot-first-world-model-answer@1.5.3"
        or freeze.get("prompt_ref")
        != "java-source-semantics-world-model-prompt@12"
        or freeze.get("proposal_vocabulary_ref")
        != "java-source-semantics-world-model-vocabulary@12"
        or freeze.get("capability_qualification_document_digest")
        != binding.qualification_document_digest.value
        or freeze.get("closed_capability_result_digest")
        != binding.closed_capability_result_digest.value
        or freeze.get("egress_policy_digest")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
        or freeze.get("conformance_result_digest")
        != conformance.result_digest.value
        or freeze.get("conformance_result_ref") != conformance.result_ref
        or binding.conformance_result_ref != conformance.result_ref
        or freeze.get("production_activation") != "NOT_EXECUTED"
        or freeze.get("document_digest")
        != digest_of(
            [_BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA, freeze_core]
        ).value
    ):
        raise ValueError(
            "bounded source-semantics Gateway freeze is not an exact qualified authority"
        )
    permission_digest = _digest_text(
        freeze.get("permission_digest"),
        "bounded source-semantics Gateway permission digest",
    )
    expected_provider = {
        **_BOUNDED_DEEPSEEK_PROVIDER,
        "conformance_digest": conformance.result_digest.value,
        "qualification_digest": binding.capability_qualification_digest.value,
    }
    qualification = {
        "capability_qualification_ref": binding.capability_qualification_ref,
        "capability_qualification_digest": (
            binding.capability_qualification_digest.value
        ),
        "capability_qualification_document_digest": (
            binding.qualification_document_digest.value
        ),
        "closed_capability_result_digest": (
            binding.closed_capability_result_digest.value
        ),
        "conformance_result_ref": _text(
            freeze.get("conformance_result_ref"),
            "bounded source-semantics Gateway conformance result reference",
        ),
        "conformance_result_digest": _digest_text(
            freeze.get("conformance_result_digest"),
            "bounded source-semantics Gateway conformance result digest",
        ),
        "bounded_java_source_semantics_gateway_freeze_digest": _digest_text(
            freeze.get("document_digest"),
            "bounded source-semantics Gateway freeze digest",
        ),
        "permission_digest": permission_digest,
    }
    return expected_provider, qualification


def _gateway_call_count(gateway_input: Path) -> int:
    freeze = _load_json(gateway_input / "g3b-freeze.json")
    if freeze.get("schema") == _BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA:
        return 6
    if freeze.get("schema") == _JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA:
        return 3
    if freeze.get("schema") in {
        _LEGACY_GATEWAY_FREEZE_SCHEMA,
        _JAVA_GATEWAY_FREEZE_SCHEMA,
    }:
        return 1
    raise ValueError("qualified Gateway freeze schema is unsupported")


def _gateway_descriptor_count(gateway_input: Path) -> int:
    freeze = _load_json(gateway_input / "g3b-freeze.json")
    if freeze.get("schema") == _BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA:
        return 3
    return _gateway_call_count(gateway_input)


def _gateway_qualification_binding_field(gateway_input: Path) -> str | None:
    freeze = _load_json(gateway_input / "g3b-freeze.json")
    schema = freeze.get("schema")
    if schema == _LEGACY_GATEWAY_FREEZE_SCHEMA:
        return None
    if schema == _JAVA_GATEWAY_FREEZE_SCHEMA:
        return "java_capability_qualification"
    if schema == _JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA:
        return "java_source_semantics_capability_qualification"
    if schema == _BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA:
        return "bounded_java_source_semantics_capability_qualification"
    raise ValueError("qualified Gateway freeze schema is unsupported")


def _dispatch_policy(provider_call_count: int) -> str:
    if provider_call_count == 1:
        return _ONE_CALL_DISPATCH_POLICY
    if provider_call_count == 3:
        return _SOURCE_SEMANTICS_DISPATCH_POLICY
    if provider_call_count == 6:
        return _BOUNDED_SOURCE_SEMANTICS_DISPATCH_POLICY
    raise ValueError("qualified Gateway provider call count is unsupported")


def _launcher_files(
    *,
    include_bounded: bool = False,
) -> Mapping[str, Path]:
    interface = Path(__file__).resolve(strict=True).parent
    files = {
        "world_model_runtime.py": interface / "world_model_runtime.py",
        "world_model_http.py": interface / "world_model_http.py",
        "world_model_browser.py": interface / "world_model_browser.py",
        "world_model_browser_ui.py": interface / "world_model_browser_ui.py",
        "runtime_assets/answer.sb": ASSET_ROOT / "answer.sb",
        "runtime_assets/gateway.sb": ASSET_ROOT / "gateway.sb",
        "runtime_assets/gateway_authorized_workload.py": (
            ASSET_ROOT / "gateway_authorized_workload.py"
        ),
        "runtime_assets/java_gateway_workload.py": (
            ASSET_ROOT / "java_gateway_workload.py"
        ),
        "runtime_assets/java_source_semantics_gateway_workload.py": (
            ASSET_ROOT / "java_source_semantics_gateway_workload.py"
        ),
        "runtime_assets/java_source_semantics_answer_workload.py": (
            ASSET_ROOT / "java_source_semantics_answer_workload.py"
        ),
        "runtime_assets/projector.sb": ASSET_ROOT / "projector.sb",
        "runtime_assets/role_worker.py": ASSET_ROOT / "role_worker.py",
        "runtime_assets/os_probe_worker.py": ASSET_ROOT / "os_probe_worker.py",
        "runtime_assets/provider_socket_worker.py": (
            ASSET_ROOT / "provider_socket_worker.py"
        ),
    }
    if include_bounded:
        files[
            "runtime_assets/bounded_java_source_semantics_answer_workload.py"
        ] = ASSET_ROOT / "bounded_java_source_semantics_answer_workload.py"
        files[
            "runtime_assets/bounded_java_source_semantics_gateway_workload.py"
        ] = ASSET_ROOT / "bounded_java_source_semantics_gateway_workload.py"
    return files


def _prepare_gateway_input(
    grant: _EvaluationGrant,
    destination: Path,
) -> tuple[Path, str]:
    destination.mkdir(mode=0o700)
    resolved = destination.resolve(strict=True)
    if resolved != destination or stat.S_IMODE(resolved.stat().st_mode) != 0o700:
        raise RuntimeError("Gateway session input directory is not exact and private")
    for name in sorted(_GATEWAY_INPUT_FILES):
        source = _canonical_descendant_file(
            grant.gateway_input / name,
            grant.gateway_input,
            f"qualified Gateway input {name}",
        )
        target = resolved / name
        shutil.copy2(source, target)
        if _sha256_file(target) != _sha256_file(source):
            raise RuntimeError("qualified Gateway input copy drifted")
    receipt_schema = "SWM-WORLD-MODEL-GATEWAY-AUTHORIZATION-RECEIPT@1"
    receipt_core = {
        "schema": receipt_schema,
        "status": "AUTHORIZED",
        "evaluation_grant_digest": grant.document_digest,
        "disclosure_authorization_digest": grant.disclosure_digest,
        "authorized_by": "user",
        "authorized_at": grant.authorization_at,
        "authorization_ref": grant.authorization_ref,
        "payload_boundary": (
            "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
        ),
        "production_activation": "NOT_EXECUTED",
    }
    receipt = {
        **receipt_core,
        "document_digest": digest_of([receipt_schema, receipt_core]).value,
    }
    _write_new(
        resolved / "authorization-receipt.json",
        canonical_json_bytes(receipt),
    )
    return resolved, str(receipt["document_digest"])


def _outer_reachability(
    database: Path,
) -> tuple[dict[str, object], dict[str, Path]]:
    uri = f"file:{quote(str(database), safe='/')}?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=5.0)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only = ON")
            columns = {
                str(row["name"])
                for row in connection.execute(
                    "PRAGMA table_info(app_maven_workspaces)"
                ).fetchall()
            }
            if "knowledge_profile_ref" in columns:
                rows = connection.execute(
                    """SELECT workspace_id, repository_locator, root_pom,
                              knowledge_profile_ref
                       FROM app_maven_workspaces
                       ORDER BY workspace_id"""
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT workspace_id, repository_locator, root_pom
                       FROM app_maven_workspaces
                       ORDER BY workspace_id"""
                ).fetchall()
            connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' LIMIT 1"
            ).fetchone()
    except sqlite3.Error as exc:
        raise RuntimeError("outer authority database preflight failed") from exc
    if not rows:
        raise RuntimeError("outer preflight found no Maven Workspace")
    forbidden: dict[str, Path] = {}
    workspaces: list[dict[str, object]] = []
    for ordinal, row in enumerate(rows):
        workspace_id = _text(row["workspace_id"], "Workspace ID")
        repository = _canonical_directory(
            Path(_text(row["repository_locator"], "repository locator")),
            "Workspace repository",
        )
        profile_ref = (
            _text(row["knowledge_profile_ref"], "knowledge profile")
            if "knowledge_profile_ref" in row.keys()
            else MAVEN_STRUCTURE_PROFILE_REF
        )
        logical_root = _text(row["root_pom"], "logical source root")
        if profile_ref == MAVEN_STRUCTURE_PROFILE_REF:
            source_probe = _canonical_descendant_file(
                repository / logical_root,
                repository,
                "Workspace root POM",
            )
            source_document = {
                "root_pom": str(source_probe),
                "root_pom_digest": _sha256_file(source_probe),
            }
            profile_document: dict[str, object] = {}
        elif profile_ref in {
            JAVA_STATIC_CALL_PROFILE_REF,
            JAVA_SOURCE_SEMANTICS_PROFILE_REF,
        }:
            source_root = _canonical_directory(
                repository / logical_root,
                "Workspace Java source root",
            )
            java_candidates = sorted(
                path for path in source_root.rglob("*.java") if path.is_file()
            )
            if not java_candidates:
                raise RuntimeError(
                    "outer preflight found no Java source probe file"
                )
            source_probe = _canonical_descendant_file(
                java_candidates[0],
                source_root,
                "Workspace Java source probe",
            )
            source_document = {
                "source_root": str(source_root),
                "source_probe": str(source_probe),
                "source_probe_digest": _sha256_file(source_probe),
            }
            profile_document = {"knowledge_profile_ref": profile_ref}
        else:
            raise RuntimeError("outer preflight found unsupported Workspace profile")
        git_marker = _canonical_descendant_file(
            repository / ".git" / "HEAD",
            repository,
            "Workspace Git marker",
        )
        source_byte = source_probe.read_bytes()[:1]
        git_byte = git_marker.read_bytes()[:1]
        if not source_byte or not git_byte:
            raise RuntimeError("outer Workspace reachability probe read no bytes")
        forbidden[f"source_{ordinal:04d}"] = source_probe
        forbidden[f"git_{ordinal:04d}"] = git_marker
        workspaces.append(
            {
                "workspace_id": workspace_id,
                **profile_document,
                **source_document,
                "git_marker": str(git_marker),
                "git_marker_digest": _sha256_file(git_marker),
                "outside_sandbox_reachable": True,
            }
        )
    core = {
        "schema": "SWM-WORLD-MODEL-OUTER-REACHABILITY@1",
        "authority_database": {
            "path": str(database),
            "raw_sha256": _raw_sha256_file(database),
            "read_only_query": "PASS",
        },
        "evidence_store": {
            "physical_binding": "AUTHORITY_DATABASE",
            "outside_sandbox_reachable": True,
        },
        "workspaces": workspaces,
        "production_activation": "NOT_EXECUTED",
    }
    return {**core, "document_digest": digest_of(core).value}, forbidden


def _document_reference(
    value: object,
    label: str,
    *,
    allow_no_document_digest: bool = False,
) -> _DocumentReference:
    expected = {"path", "raw_sha256"}
    if not allow_no_document_digest:
        expected.add("document_digest")
    item = _object(value, expected, label)
    path = _canonical_file(Path(_text(item.get("path"), f"{label} path")), label)
    raw_sha = _raw_digest_text(item.get("raw_sha256"), f"{label} raw SHA-256")
    document_digest = (
        None
        if allow_no_document_digest
        else _digest_text(item.get("document_digest"), f"{label} document digest")
    )
    return _DocumentReference(path, raw_sha, document_digest)


def _verified_document(
    reference: _DocumentReference, label: str
) -> Mapping[str, object]:
    _verify_raw_sha256(reference.path, reference.raw_sha256, label)
    value = _load_json(reference.path)
    schema = value.get("schema")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if (
        not isinstance(schema, str)
        or not schema
        or reference.document_digest is None
        or value.get("document_digest") != reference.document_digest
        or digest_of([schema, core]).value != reference.document_digest
    ):
        raise ValueError(f"{label} document digest is invalid")
    return value


def _run_one(
    *,
    index: int,
    run_key: str,
    run_number: int,
    question: str,
    read_set: ResolvedReadSetInput,
    runs_root: Path,
    socket_stage_root: Path,
    packages: Mapping[str, Path],
    gateway_input: Path,
    forbidden: Mapping[str, Path],
    runtime: Mapping[str, object],
    provider_address: str,
    provider_type: str,
    implementation_commit: str,
    evaluation_grant_digest: str,
    disclosure_authorization_digest: str,
    authorization_receipt_digest: str,
    authority_database: Path,
    timeout_seconds: float,
) -> dict[str, object]:
    run_root = runs_root / f"{index:02d}"
    run_root.mkdir(mode=0o700)
    evaluator_root = run_root / "evaluator"
    answer_input = run_root / "answer-input"
    answer_output = run_root / "answer-output"
    gateway_output = run_root / "gateway-output"
    for directory in (evaluator_root, answer_input, answer_output, gateway_output):
        directory.mkdir(mode=0o700)
    citation_seals = answer_output / "citation-seals"
    citation_seals.mkdir(mode=0o700)

    ordered = answer_input / "ordered.json"
    shutil.copy2(read_set.ordered_bundle, ordered)
    snapshots: list[Path] = []
    for number, source in enumerate(read_set.snapshot_bundles, start=1):
        target = answer_input / f"snapshot-{number}.json"
        shutil.copy2(source, target)
        snapshots.append(target)
    expected_files = {
        item.role.value + ":" + str(item.ordinal): item.file_digest.value
        for item in read_set.registration.file_manifest
    }
    observed_files = {
        "ORDERED_ENVELOPE:0": _sha256_file(ordered),
        **{
            f"SNAPSHOT:{ordinal}": _sha256_file(path)
            for ordinal, path in enumerate(snapshots)
        },
    }
    if observed_files != expected_files:
        raise RuntimeError("copied Read Set Bundle files drifted from the Catalog")

    socket_root = socket_stage_root / f"{index:02d}"
    socket_root.mkdir(mode=0o700)
    gateway_socket = socket_root / "gateway.sock"
    gateway_call_count = _gateway_call_count(gateway_input)
    gateway_descriptor_count = _gateway_descriptor_count(gateway_input)
    connected_with_receipts = tuple(
        _provision_provider_socket(
            provider_address,
            provider_type=provider_type,
        )
        for _ in range(gateway_descriptor_count)
    )
    connections = tuple(item[0] for item in connected_with_receipts)
    provisionings = tuple(item[1] for item in connected_with_receipts)
    try:
        gateway_listener, listener_provisioning = _provision_gateway_listener(
            gateway_socket
        )
    except BaseException:
        for connection in connections:
            connection.close()
        raise
    connection_fds = tuple(connection.fileno() for connection in connections)
    listener_fd = gateway_listener.fileno()
    try:
        provisioning_document = (
            provisionings[0]
            if gateway_descriptor_count == 1
            else {
                "schema": "SWM-PROVIDER-CONNECTION-SET@1",
                "connection_count": gateway_descriptor_count,
                "connections": provisionings,
                "production_activation": "NOT_EXECUTED",
            }
        )
        _write_new(
            evaluator_root / "connection-provisioning.json",
            canonical_json_bytes(provisioning_document),
        )
        _write_new(
            evaluator_root / "gateway-listener-provisioning.json",
            canonical_json_bytes(listener_provisioning),
        )
        gateway_environment = _role_environment(
            gateway_output,
            credential=_required_credential(provider_type),
            provider_type=provider_type,
        )
    except BaseException:
        for connection in connections:
            connection.close()
        gateway_listener.close()
        gateway_socket.unlink(missing_ok=True)
        raise

    payload = {
        "case_id": "DYNAMIC-WORLD-MODEL-QUESTION",
        "question_variant": question,
        "resolved_snapshot_ids": [
            item.snapshot_id.value
            for item in read_set.registration.snapshot_bindings
        ],
    }
    answer_summary = answer_output / "summary.json"
    answer_page = answer_output / "evaluation.html"
    gateway_summary = gateway_output / "summary.json"
    gateway_report = gateway_output / "role-report.json"
    answer_report = answer_output / "role-report.json"
    request_started_ns: int | None = None

    gateway_argv = [
        "--socket-path", str(gateway_socket),
        "--gateway-listener-socket-fd", str(listener_fd),
        "--numeric-provider-address", provider_address,
    ]
    for connection_fd in connection_fds:
        gateway_argv.extend(
            ("--connected-provider-socket-fd", str(connection_fd))
        )
    gateway_argv.extend([
        "--database", str(gateway_output / "model-gateway.sqlite3"),
        "--conformance-result", str(gateway_input / "conformance.json"),
        "--capability-qualification", str(gateway_input / "qualification.json"),
        "--closed-capability-result", str(gateway_input / "closed-result.json"),
        "--egress-policy", str(gateway_input / "egress-policy.json"),
        "--g3b-freeze", str(gateway_input / "g3b-freeze.json"),
        "--evaluation-authorization-receipt",
        str(gateway_input / "authorization-receipt.json"),
        "--expected-evaluation-grant-digest", evaluation_grant_digest,
        "--expected-disclosure-authorization-digest",
        disclosure_authorization_digest,
        "--implementation-commit", implementation_commit,
        "--server-audit-output", str(gateway_output / "server-audit.jsonl"),
        "--transport-audit-output", str(gateway_output / "transport-audit.jsonl"),
        "--summary-output", str(gateway_summary),
        "--startup-timeout-seconds", "30",
        "--idle-timeout-seconds",
        "5.0" if gateway_call_count in {3, 6} else "0.25",
    ])
    gateway_policy = _audit_policy(
        role="gateway",
        package_root=packages["gateway"],
        input_root=gateway_input,
        output_root=gateway_output,
        socket_root=socket_root,
        runtime=runtime,
        forbidden=forbidden,
        other_role_roots=(packages["answer"], packages["projector"]),
    )
    gateway_command = _role_command(
        role="gateway",
        package_root=packages["gateway"],
        output_root=gateway_output,
        entrypoint=_ROLE_ENTRYPOINTS["gateway"],
        argv=gateway_argv,
        report=gateway_report,
        policy=gateway_policy,
        parameters=_profile_parameters(
            role="gateway",
            package_root=packages["gateway"],
            input_root=gateway_input,
            output_root=gateway_output,
            socket_root=socket_root,
            gateway_socket=gateway_socket,
            runtime=runtime,
        ),
        nonce=secrets.token_hex(16),
    )
    cold_process_started_ns = time.monotonic_ns()
    try:
        gateway_process = subprocess.Popen(
            gateway_command,
            cwd=str(packages["gateway"]),
            env=gateway_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(*connection_fds, listener_fd),
        )
    except BaseException:
        for connection in connections:
            connection.close()
        gateway_listener.close()
        gateway_socket.unlink(missing_ok=True)
        raise
    else:
        for connection in connections:
            connection.close()
        gateway_listener.close()

    failure_stage: str | None = None
    answer_process_elapsed_milliseconds: int | None = None
    answer_value: Mapping[str, object] | None = None
    try:
        _wait_for_socket(gateway_socket, gateway_process, timeout_seconds=30.0)
        answer_argv = [
            "--product-payload-base64", _encode(payload),
            "--ordered-bundle", str(ordered),
        ]
        if gateway_call_count == 6:
            answer_argv.extend(
                (
                    "--conformance-result-ref",
                    _text(
                        _load_json(gateway_input / "g3b-freeze.json").get(
                            "conformance_result_ref"
                        ),
                        "bounded Answer Conformance result reference",
                    ),
                )
            )
        for snapshot in snapshots:
            answer_argv.extend(("--snapshot-bundle", str(snapshot)))
        answer_argv.extend(
            (
                "--gateway-socket", str(gateway_socket),
                "--run-ref", run_key,
                "--implementation-commit", implementation_commit,
                "--authority-page-output", str(answer_page),
                "--citation-seal-output-directory", str(citation_seals),
                "--summary-output", str(answer_summary),
            )
        )
        answer_policy = _audit_policy(
            role="answer",
            package_root=packages["answer"],
            input_root=answer_input,
            output_root=answer_output,
            socket_root=socket_root,
            runtime=runtime,
            forbidden=forbidden,
            other_role_roots=(packages["gateway"], packages["projector"]),
            gateway_socket=gateway_socket,
        )
        answer_command = _role_command(
            role="answer",
            package_root=packages["answer"],
            output_root=answer_output,
            entrypoint=_ROLE_ENTRYPOINTS["answer"],
            argv=answer_argv,
            report=answer_report,
            policy=answer_policy,
            parameters=_profile_parameters(
                role="answer",
                package_root=packages["answer"],
                input_root=answer_input,
                output_root=answer_output,
                socket_root=socket_root,
                gateway_socket=gateway_socket,
                runtime=runtime,
            ),
            nonce=secrets.token_hex(16),
        )
        answer_process_started_ns = time.monotonic_ns()
        request_started_ns = answer_process_started_ns
        answer_completed = subprocess.run(
            answer_command,
            cwd=str(packages["answer"]),
            env=_role_environment(answer_output),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        answer_process_elapsed_milliseconds = (
            time.monotonic_ns() - answer_process_started_ns
        ) // 1_000_000
        _preserve_process_streams(evaluator_root, "answer", answer_completed)
        if answer_completed.returncode != 0:
            failure_stage = (
                "ANSWER_OPERATION_AUDIT"
                if _is_operation_audit_failure(answer_report)
                else "ANSWER"
            )
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        failure_stage = "ANSWER_STARTUP"
        _write_new(
            evaluator_root / "answer-launch-failure.json",
            canonical_json_bytes(
                {"type": type(exc).__name__, "errno": getattr(exc, "errno", None)}
            ),
        )
    gateway_stdout, gateway_stderr = _finish_gateway(
        gateway_process, timeout_seconds
    )
    _preserve_stream_bytes(
        evaluator_root, "gateway", gateway_stdout, gateway_stderr
    )
    if gateway_process.returncode != 0 and failure_stage is None:
        failure_stage = (
            "GATEWAY_OPERATION_AUDIT"
            if _is_operation_audit_failure(gateway_report)
            else "GATEWAY"
        )

    projections: list[dict[str, object]] = []
    if failure_stage is None and answer_summary.is_file() and gateway_summary.is_file():
        answer_value = _load_json(answer_summary)
        gateway_value = _load_json(gateway_summary)
        postcondition_phase = "ROLE_POSTCONDITION"
        try:
            actual_gateway_calls = answer_value.get("provider_call_count")
            if (
                type(actual_gateway_calls) is not int
                or (
                    gateway_call_count == 6
                    and not 4 <= actual_gateway_calls <= 6
                )
                or (
                    gateway_call_count != 6
                    and actual_gateway_calls != gateway_call_count
                )
            ):
                raise RuntimeError(
                    "Answer did not report an allowed exact Provider call count"
                )
            _verify_role_success(
                answer_report,
                "answer",
                expected_unix_connect_count=actual_gateway_calls,
            )
            _verify_role_success(
                gateway_report,
                "gateway",
                expected_unix_connect_count=0,
            )
            _verify_answer_gateway(
                answer_value,
                gateway_value,
                payload,
                run_key,
                evaluation_grant_digest=evaluation_grant_digest,
                disclosure_authorization_digest=(
                    disclosure_authorization_digest
                ),
                authorization_receipt_digest=authorization_receipt_digest,
                provider_type=provider_type,
            )
            postcondition_phase = "CITATION_PROJECTION"
            projections = _project_all_citations(
                run_root=run_root,
                answer_summary=answer_value,
                citation_seals=citation_seals,
                authority_database=authority_database,
                packages=packages,
                forbidden=forbidden,
                runtime=runtime,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            failure_stage = postcondition_phase
            _write_new(
                evaluator_root / "postcondition-failure.json",
                canonical_json_bytes(
                    {
                        "phase": postcondition_phase,
                        "type": type(exc).__name__,
                        "errno": getattr(exc, "errno", None),
                    }
                ),
            )
    status = "SUCCESS" if failure_stage is None else "FAILURE"
    terminal_core = {
        "schema": "SWM-WORLD-MODEL-QUESTION-TERMINAL@1",
        "run_key": run_key,
        "case_id": "DYNAMIC-WORLD-MODEL-QUESTION",
        "run_number": run_number,
        "read_set_id": read_set.registration.read_set_id.value,
        "catalog_digest": read_set.catalog_pointer.catalog_digest.value,
        "status": status,
        "failure_stage": failure_stage,
        "attempt_count": 1,
        "selective_retry_count": 0,
        "provider_connection_handoff_count": gateway_descriptor_count,
        "provider_type": provider_type,
        "gateway_listener_handoff_count": 1,
        "gateway_listener_provisioning": _file_reference(
            evaluator_root / "gateway-listener-provisioning.json"
        ),
        "performance_timing_receipt": "timing.json",
        "answer_summary": _file_reference(answer_summary),
        "gateway_summary": _file_reference(gateway_summary),
        "answer_role_report": _file_reference(answer_report),
        "gateway_role_report": _file_reference(gateway_report),
        "citation_projection_count": len(projections),
        "citation_projections": projections,
        "completed_at": _utc_now(),
        "production_activation": "NOT_EXECUTED",
    }
    terminal = {
        **terminal_core,
        "document_digest": digest_of(terminal_core).value,
    }
    terminal_path = run_root / "terminal.json"
    _write_new(terminal_path, canonical_json_bytes(terminal))
    terminal_persisted_ns = time.monotonic_ns()
    timing_core = {
        "schema": "SWM-WORLD-MODEL-QUESTION-TIMING@1",
        "run_key": run_key,
        "terminal_document_digest": terminal["document_digest"],
        "terminal_file_digest": _sha256_file(terminal_path),
        "request_elapsed_milliseconds": (
            (terminal_persisted_ns - request_started_ns) // 1_000_000
            if request_started_ns is not None
            else None
        ),
        "cold_process_elapsed_milliseconds": (
            terminal_persisted_ns - cold_process_started_ns
        ) // 1_000_000,
        "answer_process_elapsed_milliseconds": answer_process_elapsed_milliseconds,
        "answer_worker_request_elapsed_milliseconds": (
            answer_value.get("request_elapsed_milliseconds")
            if answer_value is not None
            else None
        ),
        "answer_worker_cold_process_elapsed_milliseconds": (
            answer_value.get("cold_process_elapsed_milliseconds")
            if answer_value is not None
            else None
        ),
        "request_timing_scope": (
            "ANSWER_REQUEST_DISPATCH_TO_TERMINAL_PERSISTED_INCLUDING_"
            "GATEWAY_AND_CITATION_PROJECTION"
        ),
        "cold_timing_scope": "GATEWAY_PROCESS_START_TO_TERMINAL_PERSISTED",
        "persisted_at": _utc_now(),
        "production_activation": "NOT_EXECUTED",
    }
    timing = {**timing_core, "document_digest": digest_of(timing_core).value}
    _write_new(run_root / "timing.json", canonical_json_bytes(timing))
    return terminal


def _project_all_citations(
    *,
    run_root: Path,
    answer_summary: Mapping[str, object],
    citation_seals: Path,
    authority_database: Path,
    packages: Mapping[str, Path],
    forbidden: Mapping[str, Path],
    runtime: Mapping[str, object],
    timeout_seconds: float,
) -> list[dict[str, object]]:
    values = answer_summary.get("citation_seals")
    if not isinstance(values, list):
        raise RuntimeError("Answer citation seal index is invalid")
    citations_root = run_root / "citations"
    citations_root.mkdir(mode=0o700)
    projected: list[dict[str, object]] = []
    for index, value in enumerate(values, start=1):
        if not isinstance(value, dict):
            raise RuntimeError("Answer citation seal entry is invalid")
        root = citations_root / f"{index:02d}"
        input_root = root / "input"
        evaluator_root = root / "evaluator"
        output_root = root / "output"
        for directory in (root, input_root, evaluator_root, output_root):
            directory.mkdir(mode=0o700)
        seal_name = _text(value.get("file_name"), "seal file")
        if Path(seal_name).name != seal_name:
            raise RuntimeError("Answer citation seal name is not a basename")
        source_seal = _canonical_descendant_file(
            citation_seals / seal_name,
            citation_seals,
            "Answer citation seal",
        )
        if _sha256_file(source_seal) != value.get("file_digest"):
            raise RuntimeError("Answer citation seal file digest drifted")
        sealed = input_root / "sealed-result.json"
        shutil.copy2(source_seal, sealed)
        store_root = root / "store"
        materialization = evaluator_root / "materialization.json"
        broker = _run_evaluator_entrypoint(
            package_root=packages["broker"],
            entrypoint=packages["broker"] / _ROLE_ENTRYPOINTS["broker"],
            argv=(
                "--authority-database", str(authority_database),
                "--sealed-result", str(sealed),
                "--store-root", str(store_root),
                "--summary-output", str(materialization),
            ),
            output_root=evaluator_root,
            label="broker",
            timeout_seconds=timeout_seconds,
        )
        if broker.returncode != 0:
            raise RuntimeError("trusted Citation broker failed")
        projection = output_root / "projection.json"
        report = output_root / "role-report.json"
        policy = _audit_policy(
            role="projector",
            package_root=packages["projector"],
            input_root=input_root,
            output_root=output_root,
            socket_root=root,
            runtime=runtime,
            forbidden=forbidden,
            other_role_roots=(packages["answer"], packages["gateway"]),
            store_root=store_root,
        )
        command = _role_command(
            role="projector",
            package_root=packages["projector"],
            output_root=output_root,
            entrypoint=_ROLE_ENTRYPOINTS["projector"],
            argv=(
                "--sealed-result", str(sealed),
                "--store", str(store_root),
                "--expected-result-id", _text(value.get("result_id"), "result ID"),
                "--expected-seal-digest", _text(
                    value.get("seal_digest"), "seal digest"
                ),
                "--projection-output", str(projection),
            ),
            report=report,
            policy=policy,
            parameters=_profile_parameters(
                role="projector",
                package_root=packages["projector"],
                input_root=input_root,
                output_root=output_root,
                socket_root=root,
                gateway_socket=root / "forbidden.sock",
                runtime=runtime,
                store_root=store_root,
            ),
            nonce=secrets.token_hex(16),
        )
        completed = subprocess.run(
            command,
            cwd=str(packages["projector"]),
            env=_role_environment(output_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        _preserve_process_streams(evaluator_root, "projector", completed)
        if completed.returncode != 0:
            raise RuntimeError("sandboxed Citation Projector failed")
        _verify_role_success(
            report,
            "projector",
            expected_unix_connect_count=0,
        )
        projection_value = _load_json(projection)
        materialization_value = _load_json(materialization)
        if (
            projection_value.get("status") != "PASS"
            or projection_value.get("network_operation_count") != 0
            or projection_value.get("answer_return_port") is not False
            or materialization_value.get("status") != "PASS"
            or materialization_value.get("result_id") != value.get("result_id")
            or materialization_value.get("seal_digest") != value.get("seal_digest")
        ):
            raise RuntimeError("Citation materialization/projection binding failed")
        projected.append(
            {
                "result_id": value["result_id"],
                "seal_digest": value["seal_digest"],
                "materialization": _file_reference(materialization),
                "projection": _file_reference(projection),
                "role_report": _file_reference(report),
                "store_manifest_digest": materialization_value[
                    "store_manifest_digest"
                ],
            }
        )
    return projected


def _run_preflight(
    *,
    evidence_root: Path,
    stage_root: Path,
    socket_stage_root: Path,
    packages: Mapping[str, Path],
    gateway_input: Path,
    forbidden: Mapping[str, Path],
    runtime: Mapping[str, object],
    provider_address: str,
    provider_type: str,
) -> dict[str, object]:
    preflight_root = evidence_root / "preflight"
    preflight_root.mkdir(mode=0o700)
    protected_stage_manifest_before = _tree_manifest(stage_root)
    records: dict[str, object] = {}
    for ordinal, role in enumerate(("answer", "gateway", "projector"), start=1):
        role_root = preflight_root / role
        output_root = role_root / "output"
        input_root = role_root / "input"
        store_root = role_root / "store"
        socket_root = socket_stage_root / f"probe-{ordinal}"
        for directory in (
            role_root,
            output_root,
            input_root,
            store_root,
            socket_root,
        ):
            directory.mkdir(mode=0o700)
        allowed_read = input_root / "allowed.txt"
        _write_new(allowed_read, b"allowed\n")
        if role == "gateway":
            allowed_read = gateway_input / "conformance.json"
        gateway_socket = socket_root / "gateway.sock"
        other_socket = socket_root / "other.sock"
        local_listener = _TCPListener()
        exact_listener = None
        other_listener = _UnixListener(other_socket)
        if role in {"answer", "projector"}:
            exact_listener = _UnixListener(gateway_socket)
        inherited_connection: socket.socket | None = None
        gateway_listener: socket.socket | None = None
        gateway_probe_client: socket.socket | None = None
        gateway_listener_provisioning: Mapping[str, object] | None = None
        try:
            if role == "gateway":
                inherited_connection, provisioning = _provision_provider_socket(
                    provider_address,
                    provider_type=provider_type,
                )
                _write_new(
                    role_root / "connection-provisioning.json",
                    canonical_json_bytes(provisioning),
                )
                gateway_listener, gateway_listener_provisioning = (
                    _provision_gateway_listener(gateway_socket)
                )
                _write_new(
                    role_root / "gateway-listener-provisioning.json",
                    canonical_json_bytes(gateway_listener_provisioning),
                )
                gateway_probe_client = socket.socket(
                    socket.AF_UNIX, socket.SOCK_STREAM
                )
                gateway_probe_client.settimeout(10.0)
                gateway_probe_client.connect(str(gateway_socket))
                gateway_probe_client.sendall(b"P")
            inherited_fd = (
                inherited_connection.fileno()
                if inherited_connection is not None
                else -1
            )
            gateway_listener_fd = (
                gateway_listener.fileno() if gateway_listener is not None else -1
            )
            argv = [
                "--role", role,
                "--nonce", secrets.token_hex(16),
                "--allowed-read-file", str(allowed_read),
                "--allowed-write-file", str(output_root / "allowed-write.txt"),
                "--gateway-socket", str(gateway_socket),
                "--other-unix-socket", str(other_socket),
                "--provider-address", provider_address,
                "--provider-type", provider_type,
                "--connected-provider-socket-fd", str(inherited_fd),
                "--gateway-listener-socket-fd", str(gateway_listener_fd),
                "--local-tcp-port", str(local_listener.port),
                "--output", str(output_root / "probe.json"),
            ]
            for label, path in sorted(forbidden.items()):
                argv.extend(("--forbidden-file", f"{label}={path}"))
            parameters = _profile_parameters(
                role=role,
                package_root=packages[role],
                input_root=gateway_input if role == "gateway" else input_root,
                output_root=output_root,
                socket_root=socket_root,
                gateway_socket=gateway_socket,
                runtime=runtime,
                store_root=store_root,
            )
            command = _sandbox_prefix(role, parameters) + [
                str(runtime["python_executable"]),
                *SANDBOXED_PYTHON_FLAGS,
                str(packages[role] / ".g3b" / "os_probe_worker.py"),
                *argv,
            ]
            inherited_fds = tuple(
                descriptor
                for descriptor in (inherited_fd, gateway_listener_fd)
                if descriptor >= 0
            )
            completed = subprocess.run(
                command,
                cwd=str(packages[role]),
                env=_role_environment(
                    output_root,
                    credential=(
                        "world-model-probe-sentinel"
                        if role == "gateway"
                        else None
                    ),
                    provider_type=provider_type,
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
                check=False,
                pass_fds=inherited_fds,
            )
            if inherited_connection is not None:
                inherited_connection.close()
                inherited_connection = None
            _preserve_process_streams(role_root, "probe", completed)
            probe_path = output_root / "probe.json"
            value = _load_json(probe_path) if probe_path.is_file() else None
            gateway_listener_round_trip = None
            if gateway_probe_client is not None:
                try:
                    gateway_listener_round_trip = (
                        gateway_probe_client.recv(1) == b"Q"
                    )
                except OSError:
                    gateway_listener_round_trip = False
            records[role] = {
                "returncode": completed.returncode,
                "profile": str(ASSET_ROOT / f"{role}.sb"),
                "profile_digest": _sha256_file(ASSET_ROOT / f"{role}.sb"),
                "parameters": parameters,
                "probe": value,
                "gateway_listener_provisioning": gateway_listener_provisioning,
                "gateway_listener_round_trip": gateway_listener_round_trip,
                "status": (
                    "PASS"
                    if completed.returncode == 0
                    and isinstance(value, dict)
                    and value.get("status") == "PASS"
                    and (role != "gateway" or gateway_listener_round_trip is True)
                    else "FAIL"
                ),
            }
        finally:
            if inherited_connection is not None:
                inherited_connection.close()
            if gateway_probe_client is not None:
                gateway_probe_client.close()
            if gateway_listener is not None:
                gateway_listener.close()
                gateway_socket.unlink(missing_ok=True)
            if exact_listener is not None:
                exact_listener.close()
            other_listener.close()
            local_listener.close()
    protected_stage_manifest_after = _tree_manifest(stage_root)
    protected_stage_unchanged = (
        protected_stage_manifest_after == protected_stage_manifest_before
    )
    status_value = (
        "PASS"
        if all(value["status"] == "PASS" for value in records.values())
        and protected_stage_unchanged
        else "FAIL"
    )
    core = {
        "schema": "SWM-WORLD-MODEL-STARTUP-PREFLIGHT@1",
        "status": status_value,
        "provider_address": provider_address,
        "provider_address_scope": _provider_address_scope(provider_address),
        "provider_type": provider_type,
        "roles": records,
        "protected_stage_manifest_before": protected_stage_manifest_before,
        "protected_stage_manifest_after": protected_stage_manifest_after,
        "protected_stage_unchanged": protected_stage_unchanged,
        "os_enforcement": "MACOS_SEATBELT_DENY_DEFAULT",
        "gateway_external_capability": (
            "INHERITED_EXACT_PROVIDER_AND_AF_UNIX_LISTENER_FDS; "
            "NEW_SOCKET_SYSCALL_DENIED"
        ),
        "ancestor_limitation": (
            "literal ancestor reads may expose direct entry names, not child contents"
        ),
        "production_activation": "NOT_EXECUTED",
    }
    result = {**core, "document_digest": digest_of(core).value}
    _write_new(evidence_root / "preflight.json", canonical_json_bytes(result))
    return result


def _runtime_capabilities() -> dict[str, object]:
    executable = Path(sys.executable).resolve(strict=True)
    runtime = Path(sys.base_prefix).resolve(strict=True)
    dependencies = _python_runtime_dependency_capabilities(runtime)
    return {
        "python_executable": executable,
        "python_runtime": runtime,
        "dependencies": dependencies,
    }


def _python_runtime_dependency_capabilities(
    python_runtime: Path,
) -> tuple[RuntimeDependencyCapability, ...]:
    package_manager_root = python_runtime.parent.parent
    executable = Path(sys.executable).resolve(strict=True)
    if (
        package_manager_root.name != "pkgs"
        or python_runtime.parent.name != "python.org"
        or not _is_within(executable, python_runtime)
    ):
        return ()
    capabilities: list[RuntimeDependencyCapability] = []
    for relative_alias in _XPKG_RUNTIME_DEPENDENCY_ALIASES:
        alias = package_manager_root / relative_alias
        try:
            root = alias.resolve(strict=True)
        except OSError as exc:
            raise RuntimeError(
                f"required Python runtime dependency is missing: {alias}"
            ) from exc
        family_root = alias.parent.resolve(strict=True)
        if (
            not alias.is_symlink()
            or not root.is_dir()
            or root.is_symlink()
            or not _is_within(root, family_root)
            or root == family_root
        ):
            raise RuntimeError(f"Python runtime dependency alias is unsafe: {alias}")
        capabilities.append(RuntimeDependencyCapability(alias=alias, root=root))
    return tuple(capabilities)


def _profile_parameters(
    *,
    role: str,
    package_root: Path,
    input_root: Path,
    output_root: Path,
    socket_root: Path,
    gateway_socket: Path,
    runtime: Mapping[str, object],
    store_root: Path | None = None,
) -> dict[str, str]:
    dependencies = runtime["dependencies"]
    recursive_roots = {
        runtime["python_runtime"],
        *(item.root for item in dependencies),
        Path("/System/Library"),
        Path("/usr/lib"),
        Path("/private/var/db/dyld"),
        package_root,
        input_root,
        output_root,
    }
    if store_root is not None:
        recursive_roots.add(store_root)
    directory_roots = set(recursive_roots)
    directory_roots.add(runtime["python_executable"].parent)
    directory_roots.add(socket_root)
    directory_roots.add(Path("/private/etc"))
    directory_roots.add(Path("/private/etc/ssl"))
    directory_roots.update(item.alias for item in dependencies)
    ancestors = sorted(
        {
            ancestor
            for root in directory_roots
            for ancestor in (root, *root.parents)
        },
        key=lambda item: (len(item.parts), str(item)),
    )
    if len(ancestors) > ANCESTOR_PARAMETER_COUNT:
        raise RuntimeError("World Model profile ancestor set exceeds fixed capacity")
    common = {
        "PYTHON_EXECUTABLE": str(runtime["python_executable"]),
        "PYTHON_RUNTIME": str(runtime["python_runtime"]),
        **{
            f"PYTHON_RUNTIME_DEPENDENCY_{index:02d}": str(
                dependencies[index].root
                if index < len(dependencies)
                else runtime["python_runtime"]
            )
            for index in range(RUNTIME_DEPENDENCY_PARAMETER_COUNT)
        },
        **{
            f"ANCESTOR_{index:02d}": str(
                ancestors[index] if index < len(ancestors) else Path("/")
            )
            for index in range(ANCESTOR_PARAMETER_COUNT)
        },
        "PACKAGE_ROOT": str(package_root),
        "OUTPUT_ROOT": str(output_root),
    }
    if role == "answer":
        return {
            **common,
            "BUNDLE_ROOT": str(input_root),
            "GATEWAY_SOCKET": str(gateway_socket),
        }
    if role == "gateway":
        return {
            **common,
            "INPUT_ROOT": str(input_root),
            "SOCKET_ROOT": str(socket_root),
            "GATEWAY_SOCKET": str(gateway_socket),
        }
    if role == "projector" and store_root is not None:
        return {
            **common,
            "INPUT_ROOT": str(input_root),
            "STORE_ROOT": str(store_root),
        }
    raise ValueError("unsupported World Model profile role")


def _audit_policy(
    *,
    role: str,
    package_root: Path,
    input_root: Path,
    output_root: Path,
    socket_root: Path,
    runtime: Mapping[str, object],
    forbidden: Mapping[str, Path],
    other_role_roots: tuple[Path, ...],
    gateway_socket: Path | None = None,
    store_root: Path | None = None,
) -> dict[str, object]:
    allowed_read = [
        runtime["python_runtime"],
        *(item.root for item in runtime["dependencies"]),
        Path("/System/Library"),
        Path("/usr/lib"),
        Path("/private/var/db/dyld"),
        package_root,
        input_root,
        output_root,
    ]
    if store_root is not None:
        allowed_read.append(store_root)
    categories = {
        "source_operations": [
            str(path) for name, path in forbidden.items() if name.startswith("source_")
        ],
        "git_operations": [
            str(path) for name, path in forbidden.items() if name.startswith("git_")
        ],
        "evidence_payload_reads": [],
        "authority_database_operations": [str(forbidden["authority_database"])],
        "evidence_store_operations": [str(forbidden["evidence_store"])],
        "other_role_operations": [str(item) for item in other_role_roots],
        "product_oracle_operations": [
            str(forbidden["product_oracle"]),
            str(forbidden["independent_evaluator"]),
        ],
        "baseline_result_operations": [str(forbidden["baseline_result"])],
    }
    return {
        "allowed_read_roots": [str(item) for item in allowed_read],
        "allowed_read_files": [
            "/dev/null",
            "/dev/random",
            "/dev/urandom",
            "/private/etc/localtime",
            "/private/etc/ssl/cert.pem",
            "/etc/ssl/cert.pem",
        ],
        "allowed_write_roots": [
            str(output_root),
            *([str(socket_root)] if role == "gateway" else []),
        ],
        "allowed_write_files": ["/dev/null"],
        "allowed_network": {
            "unix_connect": (
                [str(gateway_socket)]
                if role == "answer" and gateway_socket is not None
                else []
            ),
            "unix_bind": [],
            "provider_connect": [],
        },
        "forbidden_categories": categories,
    }


def _role_command(
    *,
    role: str,
    package_root: Path,
    output_root: Path,
    entrypoint: str,
    argv: Sequence[str],
    report: Path,
    policy: Mapping[str, object],
    parameters: Mapping[str, str],
    nonce: str,
) -> list[str]:
    return _sandbox_prefix(role, parameters) + [
        str(Path(sys.executable).resolve(strict=True)),
        *SANDBOXED_PYTHON_FLAGS,
        str(package_root / ".g3b" / "role_worker.py"),
        "--role", role,
        "--nonce", nonce,
        "--package-root", str(package_root),
        "--output-root", str(output_root),
        "--entrypoint", entrypoint,
        "--argv-base64", _encode(list(argv)),
        "--audit-policy-base64", _encode(policy),
        "--report-output", str(report),
    ]


def _sandbox_prefix(role: str, parameters: Mapping[str, str]) -> list[str]:
    command = [str(SANDBOX_EXEC)]
    for key, value in sorted(parameters.items()):
        command.extend(("-D", f"{key}={value}"))
    command.extend(("-f", str(ASSET_ROOT / f"{role}.sb")))
    return command


def _run_evaluator_entrypoint(
    *,
    package_root: Path,
    entrypoint: Path,
    argv: Sequence[str],
    output_root: Path,
    label: str,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[bytes]:
    loader = (
        "import runpy,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "sys.argv=sys.argv[2:];"
        "runpy.run_path(sys.argv[0],run_name='__main__')"
    )
    completed = subprocess.run(
        [
            str(Path(sys.executable).resolve(strict=True)),
            *SANDBOXED_PYTHON_FLAGS,
            "-c", loader,
            str(package_root),
            str(entrypoint),
            *argv,
        ],
        cwd=str(package_root),
        env=_role_environment(output_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )
    _preserve_process_streams(output_root, label, completed)
    return completed


def _role_environment(
    output_root: Path,
    *,
    credential: str | None = None,
    provider_type: str = "VOLCENGINE_ARK",
) -> dict[str, str]:
    value = {
        "TMPDIR": str(output_root),
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }
    if credential is not None:
        route = _provider_route(provider_type)
        value[str(route["credential_environment_variable"])] = credential
    return value


def _verify_role_success(
    path: Path,
    role: str,
    *,
    expected_unix_connect_count: int,
) -> Mapping[str, object]:
    value = _load_json(path)
    audit = value.get("operation_audit")
    if (
        role not in {"answer", "gateway", "projector"}
        or type(expected_unix_connect_count) is not int
        or expected_unix_connect_count < 0
        or (role != "answer" and expected_unix_connect_count != 0)
    ):
        raise ValueError("role network expectation is invalid")
    expected_network = {
        "unix_connect": expected_unix_connect_count,
        "unix_bind": 0,
        "provider_connect": 0,
    }
    if (
        value.get("status") != "PASS"
        or value.get("role") != role
        or not isinstance(audit, dict)
        or audit.get("status") != "PASS"
        or audit.get("allowed_network_operations") != expected_network
        or any(audit.get("prohibited_counts", {}).values())
    ):
        raise RuntimeError(f"{role} normal workload audit failed")
    return value


def _is_operation_audit_failure(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        value = _load_json(path)
    except (OSError, ValueError):
        return False
    audit = value.get("operation_audit")
    return (
        value.get("exit_code") == 0
        and isinstance(audit, dict)
        and audit.get("status") == "FAIL"
    )


def _verify_answer_gateway(
    answer: Mapping[str, object],
    gateway: Mapping[str, object],
    payload: Mapping[str, object],
    run_key: str,
    *,
    evaluation_grant_digest: str,
    disclosure_authorization_digest: str,
    authorization_receipt_digest: str,
    provider_type: str = "VOLCENGINE_ARK",
) -> None:
    gateway_core = {
        key: value for key, value in gateway.items() if key != "document_digest"
    }
    baseline = gateway.get("qualified_gateway_baseline")
    if not isinstance(baseline, Mapping):
        raise RuntimeError("qualified Gateway baseline is invalid")
    bounded = (
        "bounded_source_semantics_capability_freeze_digest" in baseline
    )
    semantic = "source_semantics_capability_freeze_digest" in baseline
    expected_calls = answer.get("provider_call_count") if bounded else (
        3 if semantic else 1
    )
    if type(expected_calls) is not int or (
        bounded and not 4 <= expected_calls <= 6
    ):
        raise RuntimeError("Answer/Gateway Provider call count is invalid")
    expected_statuses = ["RESULT"] * expected_calls
    if (
        answer.get("status") != "PASS"
        or answer.get("run_ref") != run_key
        or answer.get("provider_call_count") != expected_calls
        or answer.get("network_operation_count") != expected_calls
        or answer.get("source_access_count") != 0
        or answer.get("evidence_payload_access_count") != 0
        or answer.get("authority_database_access_count") != 0
        or answer.get("product_oracle_read_count") != 0
        or answer.get("baseline_result_read_count") != 0
        or answer.get("credential_visible") is not False
        or (
            bounded
            and (
                answer.get("provider_type") != provider_type
                or answer.get("adapter_version")
                != _BOUNDED_DEEPSEEK_PROVIDER["adapter"]
                or answer.get("requested_model_ref")
                != _BOUNDED_DEEPSEEK_PROVIDER["requested_model"]
                or not str(answer.get("conformance_result_ref", "")).startswith(
                    "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:"
                )
            )
        )
        or answer.get("resolved_snapshot_ids") != payload["resolved_snapshot_ids"]
        or gateway.get("schema")
        != "SWM-WORLD-MODEL-AUTHORIZED-GATEWAY@1"
        or gateway.get("document_digest")
        != digest_of(
            ["SWM-WORLD-MODEL-AUTHORIZED-GATEWAY@1", gateway_core]
        ).value
        or gateway.get("evaluation_grant_digest")
        != evaluation_grant_digest
        or gateway.get("disclosure_authorization_digest")
        != disclosure_authorization_digest
        or gateway.get("authorization_receipt_digest")
        != authorization_receipt_digest
        or baseline.get("role") != "QUALIFIED_CAPABILITY_BASELINE_ONLY"
        or gateway.get("status") != "PASS"
        or gateway.get("provider_call_count") != expected_calls
        or gateway.get("https_dispatch_count") != expected_calls
        or gateway.get("server_statuses") != expected_statuses
        or (
            bounded
            and (
                gateway.get("provider_selection_policy")
                != "PRE_DISPATCH_FIRST_CURRENTLY_QUALIFIED_NO_REQUEST_RETRY"
                or gateway.get("provider_preference_order")
                != ["VOLCENGINE_ARK", "DEEPSEEK"]
                or gateway.get("selected_provider_type") != provider_type
                or gateway.get("provider_type") != provider_type
                or gateway.get("adapter_version")
                != _BOUNDED_DEEPSEEK_PROVIDER["adapter"]
                or gateway.get("requested_model_ref")
                != _BOUNDED_DEEPSEEK_PROVIDER["requested_model"]
                or gateway.get("expected_actual_model_fingerprint")
                != _BOUNDED_DEEPSEEK_PROVIDER["observed_model"]
                or gateway.get("credential_reference")
                != _provider_route(provider_type)["credential_reference"]
                or gateway.get("fallback_after_dispatch") is not False
            )
        )
        or (
            bounded
            and (
                gateway.get("provider_connection_policy")
                != "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1"
                or gateway.get("maximum_pre_dispatch_tls_handshake_attempts")
                != 3
                or gateway.get("provider_descriptor_provisioned_count") != 3
                or type(gateway.get("provider_descriptor_consumed_count"))
                is not int
                or not 1
                <= gateway["provider_descriptor_consumed_count"]
                <= 3
                or gateway.get("provider_descriptor_unused_closed_count")
                != 3 - gateway["provider_descriptor_consumed_count"]
                or gateway.get("tls_handshake_attempt_count")
                != gateway["provider_descriptor_consumed_count"]
                or type(gateway.get("tls_handshake_success_count")) is not int
                or not 1
                <= gateway["tls_handshake_success_count"]
                <= gateway["tls_handshake_attempt_count"]
                or gateway.get("pre_dispatch_tls_handshake_failure_count")
                != gateway["tls_handshake_attempt_count"]
                - gateway["tls_handshake_success_count"]
                or gateway.get("connection_reuse_count")
                != expected_calls - gateway["tls_handshake_success_count"]
                or gateway.get("request_retry_count") != 0
                or gateway.get("credential_resolution_count")
                != expected_calls
                or gateway.get("credential_resolution_success_count")
                != expected_calls
                or not isinstance(
                    gateway.get("pre_dispatch_tls_failure_codes"), list
                )
                or len(gateway["pre_dispatch_tls_failure_codes"])
                != gateway["pre_dispatch_tls_handshake_failure_count"]
                or not isinstance(
                    gateway.get("verified_peer_certificate_sha256s"), list
                )
                or len(gateway["verified_peer_certificate_sha256s"])
                != gateway["tls_handshake_success_count"]
            )
        )
        or gateway.get("dns_operation_count_in_dispatch_process") != 0
        or gateway.get("credential_value_recorded") is not False
        or gateway.get("provider_connection_capability")
        != (
            "INHERITED_EXACT_CONNECTED_SOCKET_SET"
            if bounded
            else "INHERITED_EXACT_CONNECTED_SOCKET"
        )
        or gateway.get("gateway_listener_capability")
        != "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER"
        or gateway.get("new_socket_syscall_capability") != "DENIED_BY_SEATBELT"
        or gateway.get("numeric_provider_address_scope")
        != _provider_address_scope(gateway.get("numeric_provider_address"))
    ):
        raise RuntimeError("Answer/Gateway exact postcondition failed")


def _provision_provider_socket(
    numeric_address: str | None = None,
    *,
    provider_type: str = "VOLCENGINE_ARK",
) -> tuple[socket.socket, dict[str, object]]:
    route = _provider_route(provider_type)
    provider_hostname = str(route["hostname"])
    provider_port = int(route["port"])
    if numeric_address is not None:
        parsed = ipaddress.ip_address(numeric_address)
        _provider_address_scope(str(parsed))
        if str(parsed) != numeric_address:
            raise ValueError("Provider peer pin must be canonical")
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    environment = _provisioner_environment()
    worker = ASSET_ROOT / "provider_socket_worker.py"
    command = [
        str(Path(sys.executable).resolve(strict=True)),
        *SANDBOXED_PYTHON_FLAGS,
        str(worker),
        "--control-fd", str(child.fileno()),
        "--provider-type", provider_type,
        "--timeout-seconds", "20",
    ]
    if numeric_address is not None:
        command.extend(("--numeric-address", numeric_address))
    process: subprocess.Popen[bytes] | None = None
    received_descriptors: list[int] = []
    try:
        process = subprocess.Popen(
            command,
            cwd=str(ASSET_ROOT),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(child.fileno(),),
        )
        child.close()
        parent.settimeout(90.0)
        descriptor_array = array.array("i")
        payload, ancillary, message_flags, _ = parent.recvmsg(
            64 * 1024,
            socket.CMSG_SPACE(descriptor_array.itemsize),
        )
        stdout, stderr = process.communicate(timeout=10.0)
        if message_flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
            raise RuntimeError("Provider descriptor handoff message was truncated")
        for level, kind, data in ancillary:
            if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                usable = len(data) - (len(data) % descriptor_array.itemsize)
                descriptor_array.frombytes(data[:usable])
        received_descriptors.extend(descriptor_array.tolist())
        if (
            process.returncode != 0
            or stdout
            or stderr
            or len(received_descriptors) != 1
            or not payload
        ):
            raise RuntimeError(
                "credential-free Provider socket supervisor failed "
                f"(returncode={process.returncode}, stdout_bytes={len(stdout)}, "
                f"stderr_sha256={sha256(stderr).hexdigest()}, "
                f"descriptor_count={len(received_descriptors)}, "
                f"payload_bytes={len(payload)})"
            )
        value = json.loads(payload, object_pairs_hook=_unique_object)
        if (
            not isinstance(value, dict)
            or canonical_json_bytes(value) != payload
            or value.get("schema")
            != "swm.world-model-provider-socket-provisioning@2"
        ):
            raise RuntimeError("Provider socket supervisor receipt is invalid")
        worker_core = {
            key: item for key, item in value.items() if key != "document_digest"
        }
        selected = value.get("selected_address")
        resolved = value.get("resolved_addresses")
        resolved_scopes = value.get("resolved_address_scopes")
        if (
            value.get("document_digest") != digest_of(worker_core).value
            or value.get("provider_type") != provider_type
            or value.get("provider_hostname") != provider_hostname
            or value.get("provider_port") != provider_port
            or not isinstance(resolved, list)
            or not resolved
            or any(
                not isinstance(item, str)
                or _provider_address_scope(item)
                not in {"PUBLIC_UNICAST", "EXECUTOR_SYNTHETIC_EXTERNAL"}
                for item in resolved
            )
            or resolved_scopes
            != [
                {"address": item, "scope": _provider_address_scope(item)}
                for item in resolved
            ]
            or selected not in resolved
            or value.get("selected_address_scope")
            != _provider_address_scope(selected)
            or value.get("connected_peer_address") != selected
            or value.get("connected_peer_port") != provider_port
            or value.get("tcp_connect_count") != 1
            or value.get("descriptor_transfer_count") != 1
            or value.get("credential_visible") is not False
            or value.get("product_request_payload_visible") is not False
            or value.get("provider_response_payload_visible") is not False
            or value.get("tls_operation_count") != 0
            or value.get("http_operation_count") != 0
            or value.get("production_activation") != "NOT_EXECUTED"
            or (numeric_address is None and value.get("dns_operation_count") != 1)
            or (
                numeric_address is not None
                and (
                    value.get("dns_operation_count") != 0
                    or resolved != [numeric_address]
                    or selected != numeric_address
                )
            )
        ):
            raise RuntimeError("Provider socket supervisor boundary is invalid")
        connection = socket.socket(fileno=received_descriptors.pop())
        connection.settimeout(20.0)
        peer = connection.getpeername()
        if (
            str(ipaddress.ip_address(peer[0])) != selected
            or peer[1] != provider_port
        ):
            connection.close()
            raise RuntimeError("received Provider descriptor peer is not exact")
        receipt_core = {
            **worker_core,
            "schema": "SWM-WORLD-MODEL-PROVIDER-SOCKET-HANDOFF@1",
            "worker_receipt_digest": value["document_digest"],
            "worker_script_digest": _sha256_file(worker),
            "worker_environment_keys": sorted(environment),
            "parent_received_descriptor_count": 1,
        }
        return connection, {
            **receipt_core,
            "document_digest": digest_of(receipt_core).value,
        }
    except BaseException:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.communicate(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=5.0)
        raise
    finally:
        parent.close()
        child.close()
        for descriptor in received_descriptors:
            os.close(descriptor)


def _provisioner_environment() -> dict[str, str]:
    return {
        "TMPDIR": "/private/tmp",
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }


def _provider_address_scope(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Provider address must be text")
    address = ipaddress.ip_address(value)
    if str(address) != value:
        raise ValueError("Provider address must be canonical")
    if address.is_global:
        return "PUBLIC_UNICAST"
    if address in ipaddress.ip_network("198.18.0.0/15"):
        return "EXECUTOR_SYNTHETIC_EXTERNAL"
    raise ValueError("Provider address is not an accepted external egress peer")


def _provider_route(provider_type: object) -> Mapping[str, object]:
    if not isinstance(provider_type, str) or provider_type not in _PROVIDER_ROUTES:
        raise ValueError("Provider type is not in the exact runtime route registry")
    return _PROVIDER_ROUTES[provider_type]


def _provider_type(provider: Mapping[str, object]) -> str:
    provider_type = _text(provider.get("provider_type"), "Provider type")
    route = _provider_route(provider_type)
    if provider.get("credential_reference") != route["credential_reference"]:
        raise ValueError("Provider credential reference differs from its route")
    return provider_type


def _required_credential(provider_type: str = "VOLCENGINE_ARK") -> str:
    route = _provider_route(provider_type)
    environment_variable = str(route["credential_environment_variable"])
    credential = os.environ.get(environment_variable)
    if (
        not isinstance(credential, str)
        or not credential
        or "\r" in credential
        or "\n" in credential
    ):
        raise RuntimeError(
            f"{environment_variable} is required for authorized evaluation"
        )
    return credential


def _provision_gateway_listener(
    path: Path,
) -> tuple[socket.socket, dict[str, object]]:
    if path.exists() or path.is_symlink():
        raise RuntimeError("Gateway listener path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(path))
        path.chmod(0o600)
        listener.listen(1)
        listener.settimeout(30.0)
        metadata = path.lstat()
        bound = listener.getsockname()
        if isinstance(bound, bytes):
            bound = bound.decode("utf-8")
        if (
            path.is_symlink()
            or not stat.S_ISSOCK(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or bound != str(path)
        ):
            raise RuntimeError("Gateway listener is not exact and private")
        core = {
            "schema": "SWM-WORLD-MODEL-GATEWAY-LISTENER-HANDOFF@1",
            "socket_path": str(path),
            "socket_mode": "0600",
            "address_family": "AF_UNIX",
            "socket_type": "SOCK_STREAM",
            "bound_by": "TRUSTED_EVALUATOR",
            "listener_state": "BOUND_AND_LISTENING",
            "credential_visible": False,
            "product_request_payload_visible": False,
            "provider_response_payload_visible": False,
            "descriptor_transfer_count": 1,
            "production_activation": "NOT_EXECUTED",
        }
        return listener, {**core, "document_digest": digest_of(core).value}
    except BaseException:
        listener.close()
        path.unlink(missing_ok=True)
        raise


class _UnixListener:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(str(path))
        self.socket.listen(4)
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        self.socket.settimeout(0.1)
        while not self.stop.is_set():
            try:
                connection, _ = self.socket.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with connection:
                try:
                    connection.recv(1)
                except OSError:
                    pass

    def close(self) -> None:
        self.stop.set()
        self.socket.close()
        self.thread.join(timeout=1)
        self.path.unlink(missing_ok=True)


class _TCPListener:
    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.listen(4)
        self.port = int(self.socket.getsockname()[1])

    def close(self) -> None:
        self.socket.close()


def _wait_for_socket(
    path: Path,
    process: subprocess.Popen[bytes],
    *,
    timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.is_socket() and not path.is_symlink():
            return
        if process.poll() is not None:
            raise RuntimeError("Gateway exited before publishing its exact socket")
        time.sleep(0.05)
    raise RuntimeError("Gateway socket startup timed out")


def _finish_gateway(
    process: subprocess.Popen[bytes], timeout_seconds: float
) -> tuple[bytes, bytes]:
    try:
        return process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            return process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.communicate(timeout=5)


def _preserve_process_streams(
    root: Path,
    label: str,
    completed: subprocess.CompletedProcess[bytes],
) -> None:
    _preserve_stream_bytes(root, label, completed.stdout, completed.stderr)


def _preserve_stream_bytes(
    root: Path, label: str, stdout: bytes, stderr: bytes
) -> None:
    _write_new(root / f"{label}-stdout.log", stdout)
    _write_new(root / f"{label}-stderr.log", stderr)


def _file_reference(path: Path) -> dict[str, object] | None:
    if not path.is_file() or path.is_symlink():
        return None
    return {
        "path": str(path),
        "digest": _sha256_file(path),
        "size": path.stat().st_size,
    }


def _verified_file_reference(value: object, root: Path) -> Path:
    if not isinstance(value, dict) or set(value) != {"path", "digest", "size"}:
        raise ValueError("file reference is invalid")
    path_value = value.get("path")
    if not isinstance(path_value, str):
        raise ValueError("file reference path is invalid")
    path = Path(path_value)
    try:
        resolved = path.resolve(strict=True)
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise ValueError("file reference failed verification") from exc
    if (
        path != resolved
        or not resolved.is_file()
        or resolved.is_symlink()
        or not resolved.is_relative_to(resolved_root)
        or resolved.stat().st_size != value.get("size")
        or _sha256_file(resolved) != _digest_text(value.get("digest"), "file digest")
    ):
        raise ValueError("file reference failed verification")
    return resolved


def _tree_manifest(root: Path) -> dict[str, object]:
    files: list[dict[str, object]] = []
    directories: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"symlink in protected role package tree: {path}")
        if stat.S_ISDIR(metadata.st_mode):
            directories.append(relative)
        elif stat.S_ISREG(metadata.st_mode):
            files.append(
                {
                    "path": relative,
                    "digest": _sha256_file(path),
                    "size": metadata.st_size,
                }
            )
        else:
            raise RuntimeError(
                f"unsupported entry in protected role package tree: {path}"
            )
    return {"directories": directories, "files": files}


def _canonical_directory(path: Path, label: str) -> Path:
    lexical = path if path.is_absolute() else Path.cwd() / path
    resolved = lexical.resolve(strict=True)
    if resolved != lexical or not resolved.is_dir() or lexical.is_symlink():
        raise ValueError(f"{label} must be a canonical non-symlink directory")
    return resolved


def _canonical_file(path: Path, label: str) -> Path:
    lexical = path if path.is_absolute() else Path.cwd() / path
    resolved = lexical.resolve(strict=True)
    if resolved != lexical or not resolved.is_file() or lexical.is_symlink():
        raise ValueError(f"{label} must be a canonical non-symlink file")
    return resolved


def _canonical_descendant_file(path: Path, root: Path, label: str) -> Path:
    if path.is_absolute():
        lexical = path
    else:
        lexical = root / path
    resolved = lexical.resolve(strict=True)
    if (
        resolved != lexical
        or not resolved.is_file()
        or resolved.is_symlink()
        or not resolved.is_relative_to(root)
    ):
        raise ValueError(f"{label} is not an exact descendant file")
    return resolved


def _new_private_directory(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    absolute.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    parent = absolute.parent.resolve(strict=True)
    candidate = parent / absolute.name
    if candidate.exists() or candidate.is_symlink():
        raise ValueError(f"{label} must not already exist")
    candidate.mkdir(mode=0o700)
    resolved = candidate.resolve(strict=True)
    if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
        raise ValueError(f"{label} permissions must be 0700")
    return resolved


def _write_new(path: Path, payload: bytes) -> None:
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("output path must be canonical and absolute")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def _load_json(path: Path) -> Mapping[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise ValueError(f"JSON document is not a canonical object: {path}")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    observed = set(value)
    if observed != expected:
        raise ValueError(
            f"{label} keys are not closed "
            f"(missing={sorted(expected - observed)}, extra={sorted(observed - expected)})"
        )


def _object(
    value: object, expected: set[str], label: str
) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    _exact_keys(value, expected, label)
    return value


def _string_map(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) or not isinstance(item, str)
        for key, item in value.items()
    ):
        raise ValueError(f"{label} must be a string map")
    return dict(value)


def _document_digest(value: Mapping[str, object]) -> str:
    core = {key: item for key, item in value.items() if key != "document_digest"}
    return digest_of(core).value


def _digest_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ValueError(f"{label} is invalid")
    return value


def _raw_digest_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not _RAW_SHA256.fullmatch(value):
        raise ValueError(f"{label} is invalid")
    return value


def _verify_raw_sha256(path: Path, expected: str, label: str) -> None:
    expected_value = _raw_digest_text(expected, f"{label} SHA-256")
    if _raw_sha256_file(_canonical_file(path, label)) != expected_value:
        raise ValueError(f"{label} file digest drifted")


def _raw_sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + _raw_sha256_file(path)


def _encode(value: object) -> str:
    return base64.b64encode(canonical_json_bytes(value)).decode("ascii")


def _commit(value: object) -> str:
    if not isinstance(value, str) or not _COMMIT.fullmatch(value):
        raise ValueError("commit/tree identity is invalid")
    return value


def _result_id(value: object) -> str:
    if not isinstance(value, str) or not _RESULT_ID.fullmatch(value):
        raise ValueError("Citation Result ID is invalid")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise ValueError(f"{label} must be non-empty normalized text")
    return value


def _aware_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
