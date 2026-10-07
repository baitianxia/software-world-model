"""Trusted loopback launcher for one exact ITER-010 Engineering QA preview.

The launcher is intentionally generic: it accepts a frozen product candidate,
one exact local Git revision, published Structure Read Bundle files, and one
already user-authorized question.  It does not infer a project, question type,
Source Profile, or disclosure scope from the question text.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Sequence, TextIO
from wsgiref.simple_server import WSGIRequestHandler, make_server

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekModelConfiguration,
    PersistentDeepSeekChatTransport,
    deepseek_transport_session_audit,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    load_deepseek_chat_conformance_qualification,
)
from software_world_model.ai_infrastructure.engineering_question_model_source import (
    ENGINEERING_QUESTION_DISCLOSURE_POLICY_REF,
    EngineeringQuestionRunDisclosureAuthorization,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringEvidenceClass,
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    SourceBroker,
)
from software_world_model.application_services.engineering_question_cognition import (
    StructureBundleWorldModelCognitionProjector,
)
from software_world_model.application_services.structure_view import (
    StructureViewService,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)

from .engineering_qa_live import (
    DeepSeekEngineeringQuestionBrowserAssembly,
    create_deepseek_engineering_question_browser_assembly,
    create_deepseek_engineering_question_role_runtime,
    engineering_question_deepseek_configuration,
)
from .engineering_qa_source import (
    LocalGitEvidenceClassProfile,
    LocalGitRetrievalWorker,
)


ENGINEERING_QA_PREVIEW_SUBJECT_SCHEMA = (
    "SWM-ITER-010-SLICE-001-ENGINEERING-QA-PREVIEW-SUBJECT@1"
)
_FULL_GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class _QuietLoopbackHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        # Request paths can contain result identifiers.  The product response
        # and audit chain are the authoritative record; stdout stays sanitized.
        return None


@dataclass(frozen=True, slots=True)
class PreparedEngineeringQuestionPreview:
    assembly: DeepSeekEngineeringQuestionBrowserAssembly
    request: EngineeringQuestionRequest
    run_authorization: EngineeringQuestionRunDisclosureAuthorization
    evaluation_subject_digest: Digest
    product_candidate_commit: str
    product_candidate_tree: str
    ordered_bundle_digest: Digest
    ordered_file_digest: Digest
    snapshot_bundle_digests: tuple[Digest, ...]
    snapshot_file_digests: tuple[Digest, ...]
    conformance_result_digest: Digest

    def public_status(self, *, port: int) -> dict[str, object]:
        return {
            **self.assembly.product.health(),
            "schema": "SWM-ENGINEERING-QA-PREVIEW-LAUNCH@1",
            "url": f"http://127.0.0.1:{port}/",
            "product_candidate_commit": self.product_candidate_commit,
            "product_candidate_tree": self.product_candidate_tree,
            "request_digest": self.request.digest.value,
            "evaluation_subject_digest": self.evaluation_subject_digest.value,
            "run_authorized_at": _time(self.run_authorization.authorized_at),
            "run_expires_at": _time(self.run_authorization.expires_at),
        }

    def launch_receipt(self, *, port: int) -> dict[str, object]:
        core = {
            "schema": "SWM-ENGINEERING-QA-PREVIEW-LAUNCH-RECEIPT@1",
            "status": "AUTHORIZED_NOT_DISPATCHED",
            "public_status": self.public_status(port=port),
            "request": self.request.investigation_control_view(),
            "world_model": {
                "read_authority_digest": (
                    self.request.world_model_read_authority_digest.value
                ),
                "ordered_bundle_digest": self.ordered_bundle_digest.value,
                "ordered_file_digest": self.ordered_file_digest.value,
                "snapshot_bundle_digests": tuple(
                    item.value for item in self.snapshot_bundle_digests
                ),
                "snapshot_file_digests": tuple(
                    item.value for item in self.snapshot_file_digests
                ),
            },
            "run_authorization": self.run_authorization.model_view(),
            "conformance_result_digest": self.conformance_result_digest.value,
            "provider_dispatch_count_at_seal": 0,
            "production_activation": "NOT_EXECUTED",
        }
        return _sealed_document(core)

    def terminal_receipt(
        self, *, transport: PersistentDeepSeekChatTransport
    ) -> dict[str, object]:
        audits = self.assembly.role_runtime.output_source.audits
        core = {
            "schema": "SWM-ENGINEERING-QA-PREVIEW-TERMINAL-RECEIPT@1",
            "status": (
                "STOPPED_AFTER_DISPATCH"
                if audits
                else "STOPPED_WITHOUT_DISPATCH"
            ),
            "request_digest": self.request.digest.value,
            "evaluation_subject_digest": self.evaluation_subject_digest.value,
            "run_authorization_digest": self.run_authorization.digest.value,
            "dispatch_attempt_count": len(audits),
            "dispatch_audits": tuple(item.model_view() for item in audits),
            "transport_audit": deepseek_transport_session_audit(transport),
            "request_retry_count": 0,
            "provider_switch_count": 0,
            "production_activation": "NOT_EXECUTED",
        }
        return _sealed_document(core)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swm-engineering-qa-preview-evaluation",
        description="Launch one exact, user-authorized Engineering QA direction preview",
    )
    parser.add_argument("--product-repository", required=True)
    parser.add_argument("--product-commit", required=True)
    parser.add_argument("--product-tree", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--repository-id", required=True)
    parser.add_argument("--binding-id", required=True)
    parser.add_argument("--repository-revision", required=True)
    parser.add_argument("--source-profile-ref", required=True)
    parser.add_argument("--source-path", action="append", required=True)
    parser.add_argument("--document-path", action="append", required=True)
    parser.add_argument("--build-path", action="append", required=True)
    parser.add_argument("--test-path", action="append", required=True)
    parser.add_argument("--ordered-envelope", required=True)
    parser.add_argument("--snapshot-bundle", action="append", required=True)
    parser.add_argument(
        "--cognition-snapshot-id",
        help="required when the ordered Read Bundle contains more than one Snapshot",
    )
    parser.add_argument("--question", required=True)
    parser.add_argument("--response-language", default="zh-CN")
    parser.add_argument("--request-ref", required=True)
    parser.add_argument("--run-ref", required=True)
    parser.add_argument("--authorization-message-digest", required=True)
    parser.add_argument("--conformance-result", required=True)
    parser.add_argument("--gateway-database", required=True)
    parser.add_argument("--launch-receipt", required=True)
    parser.add_argument("--terminal-receipt", required=True)
    parser.add_argument("--maximum-dispatches", type=int, default=20)
    parser.add_argument("--authorization-ttl-seconds", type=int, default=3600)
    parser.add_argument("--port", type=int, required=True)
    return parser


def prepare_engineering_question_preview(
    arguments: argparse.Namespace,
    *,
    database: SqliteDatabase,
    transport: PersistentDeepSeekChatTransport,
    at: datetime,
) -> PreparedEngineeringQuestionPreview:
    current = _aware_utc(at)
    product_repository = _canonical_directory(
        arguments.product_repository, "product repository"
    )
    product_commit, product_tree = _verify_product_candidate(
        repository=product_repository,
        expected_commit=arguments.product_commit,
        expected_tree=arguments.product_tree,
    )
    source_repository = _canonical_directory(
        arguments.repository, "source repository"
    )
    repository_revision = _exact_source_revision(
        source_repository, arguments.repository_revision
    )
    repository_id = _stable_id(arguments.repository_id, "repository ID")
    binding_id = _stable_id(arguments.binding_id, "binding ID")

    profile = LocalGitEvidenceClassProfile.create(
        profile_ref=arguments.source_profile_ref,
        binding_id=binding_id,
        evidence_class_paths={
            EngineeringEvidenceClass.SOURCE: tuple(arguments.source_path),
            EngineeringEvidenceClass.REPOSITORY_DOCUMENT: tuple(
                arguments.document_path
            ),
            EngineeringEvidenceClass.BUILD_CONFIGURATION: tuple(
                arguments.build_path
            ),
            EngineeringEvidenceClass.TEST: tuple(arguments.test_path),
        },
    )
    store = FileStructureReadBundleStore()
    ordered, ordered_file_digest = store.read_ordered(arguments.ordered_envelope)
    loaded = tuple(
        store.read_snapshot(path) for path in arguments.snapshot_bundle
    )
    view = StructureViewService(ordered, loaded)
    snapshot_bundle = _select_cognition_snapshot(
        loaded=loaded,
        requested_snapshot_id=arguments.cognition_snapshot_id,
    )
    cognition = StructureBundleWorldModelCognitionProjector(
        view=view,
        snapshot_bundle=snapshot_bundle,
    )
    if (
        cognition.binding_id != binding_id
        or cognition.source_revision != repository_revision
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "published World Model cognition does not bind the exact Source revision",
        )

    provider_configuration = DeepSeekModelConfiguration()
    qualification = load_deepseek_chat_conformance_qualification(
        arguments.conformance_result,
        provider_configuration,
        now=current,
    )
    model_configuration = engineering_question_deepseek_configuration(
        provider_configuration=provider_configuration,
        qualification=qualification,
        maximum_calls=arguments.maximum_dispatches,
        at=current,
    )
    request = EngineeringQuestionRequest.create(
        request_ref=arguments.request_ref,
        original_question=arguments.question,
        response_language=arguments.response_language,
        repository_id=repository_id,
        binding_id=binding_id,
        repository_revision=repository_revision,
        source_profile_ref=profile.profile_ref,
        source_profile_digest=profile.profile_digest,
        world_model_read_authority_digest=cognition.read_authority_digest,
        source_allowlist=tuple(
            path
            for paths in (
                arguments.source_path,
                arguments.document_path,
                arguments.build_path,
                arguments.test_path,
            )
            for path in paths
        ),
        provider_disclosure_policy=ENGINEERING_QUESTION_DISCLOSURE_POLICY_REF,
        limits=EngineeringQuestionResourceLimits(
            maximum_total_model_role_calls=arguments.maximum_dispatches,
        ),
    )
    evaluation_subject = engineering_question_preview_subject_digest(
        product_commit=product_commit,
        product_tree=product_tree,
        request=request,
        ordered_bundle_digest=view.ordered_bundle_digest,
        ordered_file_digest=ordered_file_digest,
        snapshot_bundle_digests=view.snapshot_bundle_digests,
        snapshot_file_digests=tuple(item[1] for item in loaded),
        provider_binding_digest=model_configuration.digest,
        conformance_result_digest=qualification.result_digest,
    )
    authorization_message_digest = Digest(arguments.authorization_message_digest)
    ttl = arguments.authorization_ttl_seconds
    if type(ttl) is not int or not 1 <= ttl <= 86_400:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA preview authorization TTL must be from 1 through 86400 seconds",
        )
    expires_at = min(
        current + timedelta(seconds=ttl),
        qualification.valid_until,
    )
    run_authorization = EngineeringQuestionRunDisclosureAuthorization.create(
        run_ref=arguments.run_ref,
        request=request,
        evaluation_subject_digest=evaluation_subject,
        configuration=model_configuration,
        maximum_dispatches=arguments.maximum_dispatches,
        authorized_at=current,
        expires_at=expires_at,
        authorization_ref=(
            f"codex-user-message:{authorization_message_digest.value}"
        ),
        authorization_message_digest=authorization_message_digest,
    )
    role_runtime = create_deepseek_engineering_question_role_runtime(
        repository=SqliteModelGatewayRepository(database),
        transport=transport,
        provider_configuration=provider_configuration,
        qualification=qualification,
        run_authorization=run_authorization,
        configuration=model_configuration,
    )
    worker = LocalGitRetrievalWorker(
        source_repository,
        repository_id=repository_id,
        binding_id=binding_id,
        source_profile=profile,
    )
    assembly = create_deepseek_engineering_question_browser_assembly(
        request=request,
        role_runtime=role_runtime,
        run_authorization=run_authorization,
        cognition_projector=cognition,
        source_broker=SourceBroker(source_profile=profile),
        retrieval_worker=worker,
        at=current,
    )
    return PreparedEngineeringQuestionPreview(
        assembly=assembly,
        request=request,
        run_authorization=run_authorization,
        evaluation_subject_digest=evaluation_subject,
        product_candidate_commit=product_commit,
        product_candidate_tree=product_tree,
        ordered_bundle_digest=view.ordered_bundle_digest,
        ordered_file_digest=ordered_file_digest,
        snapshot_bundle_digests=view.snapshot_bundle_digests,
        snapshot_file_digests=tuple(item[1] for item in loaded),
        conformance_result_digest=qualification.result_digest,
    )


def engineering_question_preview_subject_digest(
    *,
    product_commit: str,
    product_tree: str,
    request: EngineeringQuestionRequest,
    ordered_bundle_digest: Digest,
    ordered_file_digest: Digest,
    snapshot_bundle_digests: Sequence[Digest],
    snapshot_file_digests: Sequence[Digest],
    provider_binding_digest: Digest,
    conformance_result_digest: Digest,
) -> Digest:
    commit = _git_oid(product_commit, "product candidate commit")
    tree = _git_oid(product_tree, "product candidate tree")
    if (
        not snapshot_bundle_digests
        or len(snapshot_bundle_digests) != len(snapshot_file_digests)
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA preview requires exact semantic and file digests for every Snapshot",
        )
    return digest_of(
        [
            ENGINEERING_QA_PREVIEW_SUBJECT_SCHEMA,
            {
                "product_commit": commit,
                "product_tree": tree,
                "request_digest": request.digest.value,
                "ordered_bundle_digest": ordered_bundle_digest.value,
                "ordered_file_digest": ordered_file_digest.value,
                "snapshot_bundle_digests": tuple(
                    item.value for item in snapshot_bundle_digests
                ),
                "snapshot_file_digests": tuple(
                    item.value for item in snapshot_file_digests
                ),
                "provider_binding_digest": provider_binding_digest.value,
                "conformance_result_digest": conformance_result_digest.value,
                "production_activation": "NOT_EXECUTED",
            },
        ]
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    output = stdout or sys.stdout
    error_output = stderr or sys.stderr
    arguments = build_parser().parse_args(argv)
    transport: PersistentDeepSeekChatTransport | None = None
    try:
        if type(arguments.port) is not int or not 1 <= arguments.port <= 65_535:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering QA preview port must be from 1 through 65535",
            )
        gateway_database = _new_database_path(arguments.gateway_database)
        launch_receipt = _new_private_output_path(arguments.launch_receipt)
        terminal_receipt = _new_private_output_path(arguments.terminal_receipt)
        if len({gateway_database, launch_receipt, terminal_receipt}) != 3:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Gateway database and preview receipts require distinct paths",
            )
        provider_configuration = DeepSeekModelConfiguration()
        transport = PersistentDeepSeekChatTransport(
            api_key_resolver=provider_configuration.resolve_api_key
        )
        _create_new_private_database(gateway_database)
        with _private_file_creation_mask():
            with SqliteDatabase(gateway_database) as database:
                preview = prepare_engineering_question_preview(
                    arguments,
                    database=database,
                    transport=transport,
                    at=datetime.now(timezone.utc),
                )
                _write_new_private_json(
                    launch_receipt,
                    preview.launch_receipt(port=arguments.port),
                )
                with make_server(
                    "127.0.0.1",
                    arguments.port,
                    preview.assembly.application,
                    handler_class=_QuietLoopbackHandler,
                ) as server:
                    output.write(
                        canonical_json_bytes(
                            preview.public_status(port=server.server_port)
                        ).decode("utf-8")
                        + "\n"
                    )
                    output.flush()
                    try:
                        server.serve_forever()
                    except KeyboardInterrupt:
                        pass
                    _write_new_private_json(
                        terminal_receipt,
                        preview.terminal_receipt(transport=transport),
                    )
        return 0
    except (DomainError, OSError, ValueError, subprocess.SubprocessError) as exc:
        payload = {
            "error": exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT",
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
            "production_activation": "NOT_EXECUTED",
        }
        error_output.write(canonical_json_bytes(payload).decode("utf-8") + "\n")
        error_output.flush()
        return 2
    finally:
        if transport is not None:
            transport.close()


def _select_cognition_snapshot(*, loaded, requested_snapshot_id: str | None):
    if requested_snapshot_id is None:
        if len(loaded) != 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "an exact cognition Snapshot ID is required for a multi-Snapshot Read Bundle",
            )
        return loaded[0][0]
    requested = _stable_id(requested_snapshot_id, "cognition Snapshot ID")
    matches = tuple(bundle for bundle, _ in loaded if bundle.snapshot_id == requested)
    if len(matches) != 1:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "cognition Snapshot is absent or duplicated in the mounted Read Bundle",
        )
    return matches[0]


def _verify_product_candidate(
    *,
    repository: Path,
    expected_commit: str,
    expected_tree: str,
    implementation_path: Path | None = None,
) -> tuple[str, str]:
    expected_commit = _git_oid(expected_commit, "product candidate commit")
    expected_tree = _git_oid(expected_tree, "product candidate tree")
    actual_commit = _git(repository, "rev-parse", "HEAD").casefold()
    actual_tree = _git(repository, "rev-parse", "HEAD^{tree}").casefold()
    status = _git(repository, "status", "--porcelain", "--untracked-files=normal")
    try:
        implementation = (implementation_path or Path(__file__)).resolve(strict=True)
        implementation_relative = implementation.relative_to(repository).as_posix()
    except (OSError, ValueError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering QA launcher is not loaded from the frozen product candidate",
        ) from exc
    tracked_implementation = _git(
        repository,
        "ls-files",
        "--error-unmatch",
        implementation_relative,
    )
    if status:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Engineering QA live preview requires a clean product candidate",
        )
    if (
        actual_commit != expected_commit
        or actual_tree != expected_tree
        or tracked_implementation != implementation_relative
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering QA product candidate commit or tree drifted",
        )
    return actual_commit, actual_tree


def _exact_source_revision(repository: Path, expected_revision: str) -> str:
    expected = _git_oid(expected_revision, "source repository revision")
    actual = _git(
        repository,
        "rev-parse",
        "--verify",
        f"{expected}^{{commit}}",
    ).casefold()
    if actual != expected:
        raise DomainError(
            ErrorCode.SOURCE_REVISION_INCONSISTENT,
            "source repository revision does not resolve to the exact commit",
        )
    return actual


def _git(repository: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DomainError(
            ErrorCode.SOURCE_TARGET_NOT_FOUND,
            "exact Git candidate or revision cannot be resolved",
        ) from exc
    return result.stdout.strip()


def _canonical_directory(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise DomainError(
            ErrorCode.SOURCE_TARGET_NOT_FOUND, f"{label} does not exist"
        ) from exc
    if resolved != path or not resolved.is_dir():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be a canonical non-symlink directory",
        )
    return resolved


def _new_database_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.exists() or path.is_symlink():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Gateway database must be a new absolute non-symlink path",
        )
    try:
        parent = path.parent.resolve(strict=True)
    except OSError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Gateway database parent must already exist",
        ) from exc
    if parent != path.parent or not parent.is_dir():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Gateway database parent must be canonical",
        )
    return path


def _create_new_private_database(path: Path) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_RDWR | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        os.fchmod(descriptor, 0o600)
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Gateway database path was concurrently occupied",
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


@contextmanager
def _private_file_creation_mask():
    previous_mask = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous_mask)


def _new_private_output_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.exists() or path.is_symlink():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "preview receipt must be a new absolute non-symlink path",
        )
    try:
        parent = path.parent.resolve(strict=True)
    except OSError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "preview receipt parent must already exist",
        ) from exc
    if parent != path.parent or not parent.is_dir():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "preview receipt parent must be canonical",
        )
    return path


def _write_new_private_json(path: Path, value: dict[str, object]) -> None:
    payload = canonical_json_bytes(value) + b"\n"
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "wb") as output:
            descriptor = None
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "preview receipt path was concurrently occupied",
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _sealed_document(core: dict[str, object]) -> dict[str, object]:
    return {
        **core,
        "document_digest": digest_of([core["schema"], core]).value,
    }


def _stable_id(value: str, label: str) -> StableId:
    try:
        return StableId(value)
    except (TypeError, ValueError) as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid") from exc


def _git_oid(value: str, label: str) -> str:
    if not isinstance(value, str) or not _FULL_GIT_OID.fullmatch(value.casefold()):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    return value.casefold()


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA preview time must be timezone-aware",
        )
    return value.astimezone(timezone.utc)


def _time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ENGINEERING_QA_PREVIEW_SUBJECT_SCHEMA",
    "PreparedEngineeringQuestionPreview",
    "build_parser",
    "engineering_question_preview_subject_digest",
    "main",
    "prepare_engineering_question_preview",
]
