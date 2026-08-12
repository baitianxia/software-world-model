#!/usr/bin/env python3
"""Serve free-form questions through the accepted ITER-003 World Model chain.

This is a trusted, local, evaluation-only launcher.  It reuses the exact
accepted product packages, prepared Read Bundles, and Gateway inputs.  Every
question receives a fresh immutable run directory and one no-retry provider
call; the browser adapter never receives a Source or repository path.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
import stat
import threading
from typing import Mapping, Sequence
from urllib.parse import quote
from wsgiref.simple_server import WSGIRequestHandler, make_server

from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.interface.world_model_browser import (
    PublicRunnerError,
    WorldModelBrowserApplication,
)
from software_world_model.interface.world_model_evaluation import (
    read_world_model_evaluation_page,
)
from validation.structure_world_model_iteration_003.g3b import run_g3b


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACCEPTED_PRODUCT_COMMIT = "b9b329a9b341b01fc41486ef9b0c809ac8665332"
ACCEPTED_PRODUCT_TREE = "43accc44508a1cce9066aead258ec11a5b6a4ef0"
ACCEPTED_PREPARED_DIGEST = (
    "sha256:ace18c7c0b6c43a1a17a76be810a9d378d8069b34fa679c263de5d74729f4407"
)
ACCEPTED_BATCH_DIGEST = (
    "sha256:bf8ca1fe4c4e8861b3edb7a9853eb33f1536f5ee2a2bcfb90b38f1ac0bffc632"
)
ACCEPTED_EVALUATION_DIGEST = (
    "sha256:7952bd9b6a68e50beb7a6370942ea163ac1e1359c2922cd77500903f149f2b1c"
)
DEFAULT_ARTIFACT_ROOT = (
    PROJECT_ROOT / "var" / "iteration-003" / "g3b" / ACCEPTED_PRODUCT_COMMIT
)
_DATASET_IDS = ("ORDERED_A_B", "EXACT_B", "EXACT_FIXTURE_VALID")
_DATASET_PRESENTATION = {
    "ORDERED_A_B": {
        "label": "Mall A → B",
        "description": "对比两个已密封的 mall Maven reactor 快照",
        "coverage": "reactor 子模块成员关系、POM-local 直接内部依赖与 exact A/B diff",
    },
    "EXACT_B": {
        "label": "Mall Snapshot B",
        "description": "只读取 accepted B 快照的精确结构",
        "coverage": "B 的 reactor 子模块成员关系与 POM-local 直接内部依赖",
    },
    "EXACT_FIXTURE_VALID": {
        "label": "Valid Maven Fixture",
        "description": "小型有效 Maven fixture 的精确结构",
        "coverage": "fixture 的 reactor 子模块成员关系与 POM-local 直接内部依赖",
    },
}
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class CitationRecord:
    result_id: str
    seal_digest: str
    projection_path: Path
    projection_digest: str


@dataclass(frozen=True, slots=True)
class RequestRecord:
    request_id: str
    dataset_id: str
    run_root: Path
    citations: Mapping[str, CitationRecord]


class _LoopbackRequestHandler(WSGIRequestHandler):
    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(300.0)

    def log_message(self, format: str, *args: object) -> None:
        # Keep a concise timestamped access trail without query/body disclosure.
        super().log_message(format, *args)


class AcceptedG3bInteractiveRunner:
    """Serialize questions through one exact accepted G3b execution boundary."""

    def __init__(
        self,
        *,
        artifact_root: Path,
        session_root: Path,
        socket_root: Path,
        timeout_seconds: float = 240.0,
        run_one=run_g3b._run_one,
        run_preflight=run_g3b._run_preflight,
    ) -> None:
        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")
        self._artifact_root = _canonical_directory(artifact_root, "artifact root")
        self._session_root = _new_private_directory(session_root, "session root")
        self._requests_root = self._session_root / "requests"
        self._requests_root.mkdir(mode=0o700)
        self._socket_root = _new_private_directory(socket_root, "socket root")
        if len(os.fsencode(str(self._socket_root / "r999999" / "01" / "gateway.sock"))) >= 100:
            raise ValueError("socket_root is too long for an exact AF_UNIX endpoint")
        self._timeout_seconds = timeout_seconds
        self._run_one = run_one
        self._lock = threading.Lock()
        self._records: dict[str, RequestRecord | None] = {}
        self._ordinal = 0

        accepted = self._load_accepted_artifacts()
        self._prepared_root = accepted["prepared_root"]
        self._registry = accepted["registry"]
        self._stage_root = accepted["stage_root"]
        self._packages = accepted["packages"]
        self._gateway_input = accepted["gateway_input"]
        self._forbidden = accepted["forbidden"]
        self._runtime = run_g3b._runtime_capabilities()
        self._provider_address = accepted["provider_address"]
        self._stage_manifest_digest = accepted["stage_manifest_digest"]
        self._datasets = self._build_datasets()

        preflight_root = self._session_root / "startup"
        preflight_root.mkdir(mode=0o700)
        preflight = run_preflight(
            evidence_root=preflight_root,
            stage_root=self._stage_root,
            socket_stage_root=self._socket_root,
            packages=self._packages,
            gateway_input=self._gateway_input,
            forbidden=self._forbidden,
            runtime=self._runtime,
            provider_address=self._provider_address,
        )
        if (
            preflight.get("status") != "PASS"
            or preflight.get("protected_stage_unchanged") is not True
            or preflight.get("production_activation") != "NOT_EXECUTED"
            or digest_of(run_g3b._tree_manifest(self._stage_root)).value
            != self._stage_manifest_digest
        ):
            raise RuntimeError("current OS isolation preflight failed closed")
        self._startup_preflight_digest = _digest_text(
            preflight.get("document_digest"), "startup preflight digest"
        )

    def health(self) -> Mapping[str, object]:
        return {
            "status": "ready",
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "accepted_product_commit": ACCEPTED_PRODUCT_COMMIT,
            "accepted_product_tree": ACCEPTED_PRODUCT_TREE,
            "accepted_batch_digest": ACCEPTED_BATCH_DIGEST,
            "startup_preflight_digest": self._startup_preflight_digest,
            "stage_manifest_digest": self._stage_manifest_digest,
            "dispatch_policy": "ONE_CALL_PER_QUESTION_NO_HIDDEN_RETRY",
            "production_activation": "NOT_EXECUTED",
        }

    def datasets(self) -> tuple[Mapping[str, object], ...]:
        return self._datasets

    def ask(
        self, *, request_id: str, dataset_id: str, question: str
    ) -> Mapping[str, object]:
        if dataset_id not in _DATASET_IDS:
            raise PublicRunnerError(
                "DATASET_NOT_ALLOWED",
                "dataset_id is not one of the accepted Read Sets",
                status="400 Bad Request",
            )
        if not question or len(question) > 8_000:
            raise PublicRunnerError(
                "QUESTION_INVALID",
                "question must contain 1 to 8000 characters",
                status="400 Bad Request",
            )
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
            try:
                result, record = self._execute(
                    ordinal=ordinal,
                    request_id=request_id,
                    dataset_id=dataset_id,
                    question=question,
                )
            except PublicRunnerError:
                raise
            except Exception as exc:
                self._write_failure_receipt(ordinal, request_id, dataset_id, exc)
                raise PublicRunnerError(
                    "WORLD_MODEL_EXECUTION_FAILED",
                    "the isolated World Model run did not produce a verified result",
                ) from exc
            self._records[request_id] = record
            return result

    def citation(
        self, *, request_id: str, result_id: str
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
            value = run_g3b._load_json(citation.projection_path)
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

    def _execute(
        self,
        *,
        ordinal: int,
        request_id: str,
        dataset_id: str,
        question: str,
    ) -> tuple[dict[str, object], RequestRecord]:
        selector = self._selector(dataset_id)
        request_token = sha256(request_id.encode("ascii")).hexdigest()[:12]
        evidence_root = self._requests_root / f"{ordinal:06d}-{request_token}"
        evidence_root.mkdir(mode=0o700)
        runs_root = evidence_root / "runs"
        runs_root.mkdir(mode=0o700)
        socket_stage_root = self._socket_root / f"r{ordinal:06d}"
        socket_stage_root.mkdir(mode=0o700)
        run_key = f"interactive-{ordinal:06d}-{request_token}"
        run = {
            "run_key": run_key,
            "case_id": "ITER-004-FREE-QUESTION",
            "run_number": ordinal,
            "selector": dataset_id,
            "question": question,
            "resolved_snapshot_ids": list(selector["resolved_snapshot_ids"]),
        }
        terminal = self._run_one(
            index=1,
            run=run,
            registry=self._registry,
            prepared_root=self._prepared_root,
            runs_root=runs_root,
            socket_stage_root=socket_stage_root,
            packages=self._packages,
            gateway_input=self._gateway_input,
            forbidden=self._forbidden,
            runtime=self._runtime,
            provider_address=self._provider_address,
            implementation_commit=ACCEPTED_PRODUCT_COMMIT,
            timeout_seconds=self._timeout_seconds,
        )
        run_root = runs_root / "01"
        terminal_path = run_root / "terminal.json"
        persisted_terminal = run_g3b._load_json(terminal_path)
        if (
            terminal.get("status") != "SUCCESS"
            or persisted_terminal.get("status") != "SUCCESS"
            or persisted_terminal.get("run_key") != run_key
            or persisted_terminal.get("attempt_count") != 1
            or persisted_terminal.get("selective_retry_count") != 0
            or persisted_terminal.get("provider_connection_handoff_count") != 1
            or persisted_terminal.get("gateway_listener_handoff_count") != 1
            or persisted_terminal.get("production_activation") != "NOT_EXECUTED"
            or _document_digest(persisted_terminal) != persisted_terminal.get("document_digest")
        ):
            raise RuntimeError("interactive terminal failed its exact postcondition")

        summary_path = _verified_file_reference(
            persisted_terminal.get("answer_summary"), run_root
        )
        summary = run_g3b._load_json(summary_path)
        timing = run_g3b._load_json(run_root / "timing.json")
        page_path = run_root / "answer-output" / "evaluation.html"
        page_digest = _digest_text(summary.get("page_digest"), "page digest")
        page = read_world_model_evaluation_page(
            page_path,
            expected_implementation_commit=ACCEPTED_PRODUCT_COMMIT,
            expected_page_digest=page_digest,
        )
        snapshots = page.get("read_binding", {}).get("snapshots", [])
        observed_snapshot_ids = [
            item.get("snapshot_id") for item in snapshots if isinstance(item, dict)
        ]
        stages = page.get("authority_chain", {}).get("stages", [])
        if (
            page.get("mode") != "WORLD_MODEL"
            or page.get("environment") != "EVALUATION_ONLY"
            or page.get("evaluation_only") is not True
            or page.get("implementation_commit") != ACCEPTED_PRODUCT_COMMIT
            or page.get("request", {}).get("original_question") != question
            or observed_snapshot_ids != selector["resolved_snapshot_ids"]
            or len(stages) != 10
            or page.get("execution_boundary", {}).get("provider_call_count") != 1
            or page.get("execution_boundary", {}).get("network_operation_count") != 1
            or page.get("execution_boundary", {}).get("source_access_allowed") is not False
            or page.get("execution_boundary", {}).get("evidence_payload_access_allowed") is not False
            or summary.get("source_access_count") != 0
            or summary.get("evidence_payload_access_count") != 0
            or summary.get("authority_database_access_count") != 0
            or summary.get("product_oracle_read_count") != 0
            or summary.get("baseline_result_read_count") != 0
            or summary.get("provider_call_count") != 1
            or summary.get("network_operation_count") != 1
            or summary.get("production_activation") != "NOT_EXECUTED"
        ):
            raise RuntimeError("verified page violates the interactive boundary")

        citations: dict[str, CitationRecord] = {}
        public_citations: list[dict[str, object]] = []
        terminal_citations = persisted_terminal.get("citation_projections")
        if not isinstance(terminal_citations, list):
            raise RuntimeError("terminal citation index is invalid")
        for item in terminal_citations:
            if not isinstance(item, dict):
                raise RuntimeError("terminal citation entry is invalid")
            result_id = _result_id(item.get("result_id"))
            seal_digest = _digest_text(item.get("seal_digest"), "citation seal")
            projection_path = _verified_file_reference(item.get("projection"), run_root)
            projection_digest = _digest_text(
                item.get("projection", {}).get("digest"), "projection digest"
            )
            if result_id in citations:
                raise RuntimeError("duplicate citation Result ID")
            citation = CitationRecord(
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

        record = RequestRecord(
            request_id=request_id,
            dataset_id=dataset_id,
            run_root=run_root,
            citations=citations,
        )
        result = {
            "request_id": request_id,
            "dataset_id": dataset_id,
            "question": question,
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "accepted_product_commit": ACCEPTED_PRODUCT_COMMIT,
            "page_digest": page_digest,
            "page": page,
            "citations": public_citations,
            "execution": {
                "attempt_count": 1,
                "provider_call_count": 1,
                "network_operation_count": 1,
                "selective_retry_count": 0,
                "source_access_count": 0,
                "evidence_payload_access_count": 0,
                "model_call_id": summary.get("model_call_id"),
                "model_fingerprint": summary.get("model_actual_fingerprint"),
                "elapsed_milliseconds": timing.get("request_elapsed_milliseconds"),
                "terminal_digest": persisted_terminal.get("document_digest"),
            },
            "production_activation": "NOT_EXECUTED",
        }
        _write_new(
            evidence_root / "browser-result.json",
            canonical_json_bytes(result),
        )
        return result, record

    def _selector(self, dataset_id: str) -> Mapping[str, object]:
        selectors = self._registry.get("selectors")
        selector = selectors.get(dataset_id) if isinstance(selectors, dict) else None
        if not isinstance(selector, dict):
            raise RuntimeError("accepted selector is missing")
        return selector

    def _build_datasets(self) -> tuple[Mapping[str, object], ...]:
        values: list[Mapping[str, object]] = []
        for dataset_id in _DATASET_IDS:
            selector = self._selector(dataset_id)
            snapshot_ids = selector.get("resolved_snapshot_ids")
            if not isinstance(snapshot_ids, list) or not snapshot_ids:
                raise RuntimeError("accepted selector Snapshot IDs are invalid")
            values.append(
                {
                    "id": dataset_id,
                    **_DATASET_PRESENTATION[dataset_id],
                    "snapshot_count": len(snapshot_ids),
                    "snapshot_ids": list(snapshot_ids),
                    "read_only": True,
                }
            )
        return tuple(values)

    def _load_accepted_artifacts(self) -> dict[str, object]:
        root = self._artifact_root
        prepared_root = _canonical_directory(root / "prepared", "prepared root")
        dispatch_root = _canonical_directory(root / "dispatch", "dispatch root")
        stage_root = _canonical_directory(dispatch_root / "stage", "accepted stage")
        batch = _canonical_document(dispatch_root / "batch-result.json")
        evaluation = _canonical_document(root / "product-evaluation.json")
        historical_preflight = _canonical_document(dispatch_root / "preflight.json")
        registry = run_g3b._load_registry(
            prepared_root / "prepared-inputs.json",
            prepared_root,
            ACCEPTED_PRODUCT_COMMIT,
        )
        if (
            batch.get("schema") != "swm.iter-003.g3b-batch@1"
            or batch.get("status") != "PASS"
            or batch.get("implementation_commit") != ACCEPTED_PRODUCT_COMMIT
            or batch.get("implementation_tree") != ACCEPTED_PRODUCT_TREE
            or batch.get("document_digest") != ACCEPTED_BATCH_DIGEST
            or batch.get("prepared_registry_digest") != ACCEPTED_PREPARED_DIGEST
            or batch.get("success_count") != 60
            or batch.get("failure_count") != 0
            or batch.get("selective_retry_count") != 0
            or batch.get("stage_unchanged_after_batch") is not True
            or batch.get("production_activation") != "NOT_EXECUTED"
            or _document_digest(batch) != ACCEPTED_BATCH_DIGEST
            or evaluation.get("schema") != "swm.iter-003.g3b-product-evaluation@2"
            or evaluation.get("status") != "PASS"
            or evaluation.get("implementation_commit") != ACCEPTED_PRODUCT_COMMIT
            or evaluation.get("document_digest") != ACCEPTED_EVALUATION_DIGEST
            or evaluation.get("prepared_registry_digest") != ACCEPTED_PREPARED_DIGEST
            or evaluation.get("production_activation") != "NOT_EXECUTED"
            or _document_digest(evaluation) != ACCEPTED_EVALUATION_DIGEST
            or registry.get("document_digest") != ACCEPTED_PREPARED_DIGEST
            or historical_preflight.get("status") != "PASS"
            or historical_preflight.get("protected_stage_unchanged") is not True
            or historical_preflight.get("production_activation") != "NOT_EXECUTED"
            or _document_digest(historical_preflight)
            != historical_preflight.get("document_digest")
            or historical_preflight.get("document_digest")
            != batch.get("preflight_digest")
        ):
            raise RuntimeError("accepted ITER-003 evidence identity is invalid")

        stage_manifest = run_g3b._tree_manifest(stage_root)
        stage_manifest_digest = digest_of(stage_manifest).value
        if (
            stage_manifest_digest != batch.get("stage_manifest_before_digest")
            or stage_manifest_digest != batch.get("stage_manifest_after_digest")
            or stage_manifest != historical_preflight.get("protected_stage_manifest_before")
            or stage_manifest != historical_preflight.get("protected_stage_manifest_after")
        ):
            raise RuntimeError("accepted ITER-003 stage drifted")
        selectors = registry.get("selectors")
        if not isinstance(selectors, dict) or any(
            dataset_id not in selectors for dataset_id in _DATASET_IDS
        ):
            raise RuntimeError("accepted Read Set allowlist is incomplete")

        packages_root = _canonical_directory(stage_root / "packages", "packages")
        packages = {
            role: _canonical_directory(packages_root / role, f"{role} package")
            for role in ("answer", "gateway", "projector", "broker")
        }
        gateway_input = _canonical_directory(
            stage_root / "gateway-input", "gateway input"
        )
        authority_database = next((prepared_root / "authority").glob("*.sqlite3"))
        forbidden = {
            "source": (
                PROJECT_ROOT / "validation-projects" / "mall" / "pom.xml"
            ).resolve(strict=True),
            "original_worktree": (
                PROJECT_ROOT / "src" / "software_world_model" / "__init__.py"
            ).resolve(strict=True),
            "git": (PROJECT_ROOT / ".git" / "HEAD").resolve(strict=True),
            "authority_database": authority_database.resolve(strict=True),
            "product_oracle": run_g3b.PRODUCT_SUITE.resolve(strict=True),
            "baseline_result": next(
                run_g3b.BASELINES.glob("direct/runs/*/terminal.json")
            ).resolve(strict=True),
            "other_role": (
                packages["broker"] / "software_world_model" / "__init__.py"
            ).resolve(strict=True),
            "evidence_payload": (
                stage_root / "forbidden" / "evidence-payload.txt"
            ).resolve(strict=True),
            "evidence_store": (
                stage_root / "forbidden" / "evidence-store.txt"
            ).resolve(strict=True),
        }
        provider_address = str(batch.get("selected_provider_address"))
        if (
            run_g3b._provider_address_scope(provider_address)
            != batch.get("selected_provider_address_scope")
        ):
            raise RuntimeError("accepted exact Provider address is invalid")
        return {
            "prepared_root": prepared_root,
            "registry": registry,
            "stage_root": stage_root,
            "packages": packages,
            "gateway_input": gateway_input,
            "forbidden": forbidden,
            "provider_address": provider_address,
            "stage_manifest_digest": stage_manifest_digest,
        }

    def _write_failure_receipt(
        self,
        ordinal: int,
        request_id: str,
        dataset_id: str,
        exc: Exception,
    ) -> None:
        path = self._requests_root / f"failure-{ordinal:06d}.json"
        if path.exists():
            return
        _write_new(
            path,
            canonical_json_bytes(
                {
                    "schema": "swm.iter-004.interactive-failure@1",
                    "request_id_digest": "sha256:"
                    + sha256(request_id.encode("ascii")).hexdigest(),
                    "dataset_id": dataset_id,
                    "exception_type": type(exc).__name__,
                    "production_activation": "NOT_EXECUTED",
                }
            ),
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", default=str(DEFAULT_ARTIFACT_ROOT))
    parser.add_argument("--session-root")
    parser.add_argument("--socket-root")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55121)
    parser.add_argument("--timeout-seconds", type=float, default=240.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.host != "127.0.0.1":
        raise ValueError("interactive evaluation service must bind 127.0.0.1")
    if not 1 <= arguments.port <= 65_535:
        raise ValueError("port must be in 1..65535")
    token = secrets.token_hex(6)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    session_root = (
        Path(arguments.session_root)
        if arguments.session_root
        else PROJECT_ROOT
        / "var"
        / "iteration-004"
        / "interactive"
        / f"{timestamp}-{token}"
    )
    socket_root = (
        Path(arguments.socket_root)
        if arguments.socket_root
        else Path("/private/tmp") / f"swm4-{os.getpid()}-{token}"
    )
    runner = AcceptedG3bInteractiveRunner(
        artifact_root=Path(arguments.artifact_root),
        session_root=session_root,
        socket_root=socket_root,
        timeout_seconds=arguments.timeout_seconds,
    )
    application = WorldModelBrowserApplication(runner)
    with make_server(
        arguments.host,
        arguments.port,
        application,
        handler_class=_LoopbackRequestHandler,
    ) as server:
        print(
            json.dumps(
                {
                    "status": "ready",
                    "url": f"http://{arguments.host}:{arguments.port}/",
                    "mode": "WORLD_MODEL",
                    "environment": "EVALUATION_ONLY",
                    "accepted_product_commit": ACCEPTED_PRODUCT_COMMIT,
                    "session_root": str(runner._session_root),
                    "startup_preflight_digest": runner._startup_preflight_digest,
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


def _canonical_directory(path: Path, label: str) -> Path:
    resolved = path.resolve(strict=True)
    if not resolved.is_dir() or resolved.is_symlink():
        raise ValueError(f"{label} must be a real directory")
    return resolved


def _new_private_directory(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else (Path.cwd() / path)
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


def _canonical_document(path: Path) -> Mapping[str, object]:
    return run_g3b._load_json(path.resolve(strict=True))


def _document_digest(value: Mapping[str, object]) -> str:
    core = {key: item for key, item in value.items() if key != "document_digest"}
    return digest_of(core).value


def _digest_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ValueError(f"{label} is invalid")
    return value


def _result_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"structure_view_result_[0-9a-f]{32}", value)
    ):
        raise ValueError("citation Result ID is invalid")
    return value


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


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _write_new(path: Path, payload: bytes) -> None:
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


if __name__ == "__main__":
    raise SystemExit(main())
