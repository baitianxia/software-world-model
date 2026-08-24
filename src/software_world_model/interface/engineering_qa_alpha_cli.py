"""Trusted launcher for the sustained ITER-010 Engineering QA Web Alpha.

One closed session configuration freezes the product, source revision, World
Model projection, Source Profile, Provider qualification, disclosure boundary,
and bounded user authorization before the loopback listener starts.  Browser
users submit only an exact question plus an explicit disclosure acknowledgement;
the trusted application creates fresh request and run identities for every
question.  Provider credentials and sockets stay lazy until that submission.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Callable, Mapping, Sequence, TextIO
from wsgiref.simple_server import make_server

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekChatCompletionsTransport,
    DeepSeekModelConfiguration,
    PersistentDeepSeekChatTransport,
    deepseek_transport_session_audit,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    load_deepseek_chat_conformance_qualification,
)
from software_world_model.ai_infrastructure.engineering_question_model_source import (
    ENGINEERING_QUESTION_DISCLOSURE_POLICY_REF,
    EngineeringQuestionSessionAuthority,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringEvidenceClass,
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

from .engineering_qa_browser import EngineeringQuestionSessionRequestTemplate
from .engineering_qa_live import (
    DeepSeekEngineeringQuestionSessionBrowserAssembly,
    create_deepseek_engineering_question_session_browser_assembly,
    engineering_question_deepseek_configuration,
)
from .engineering_qa_preview_cli import (
    _QuietLoopbackHandler,
    _aware_utc,
    _canonical_directory,
    _exact_source_revision,
    _git_oid,
    _new_database_path,
    _new_private_output_path,
    _sealed_document,
    _select_cognition_snapshot,
    _stable_id,
    _time,
    _verify_product_candidate,
    _write_new_private_json,
)
from .engineering_qa_source import (
    LocalGitEvidenceClassProfile,
    LocalGitRetrievalWorker,
)


ENGINEERING_QA_ALPHA_SESSION_CONFIG_SCHEMA = (
    "SWM-ENGINEERING-QA-ALPHA-SESSION-CONFIG@1"
)
ENGINEERING_QA_ALPHA_SUBJECT_SCHEMA = (
    "SWM-ITER-010-SLICE-001-ENGINEERING-QA-ALPHA-SUBJECT@1"
)
ENGINEERING_QA_ALPHA_PORT = 8765
_MAXIMUM_SESSION_CONFIG_BYTES = 1_048_576
_SESSION_CONFIG_FIELDS = frozenset(
    {
        "schema",
        "product_repository",
        "product_commit",
        "product_tree",
        "repository",
        "repository_id",
        "binding_id",
        "repository_revision",
        "source_profile_ref",
        "source_paths",
        "document_paths",
        "build_paths",
        "test_paths",
        "excluded_source_paths",
        "ordered_envelope",
        "snapshot_bundles",
        "cognition_snapshot_id",
        "response_language",
        "session_ref",
        "authorization_message_digest",
        "authorized_at",
        "expires_at",
        "conformance_result",
        "gateway_database",
        "launch_receipt",
        "terminal_receipt",
        "maximum_questions",
        "maximum_dispatches_per_question",
        "maximum_total_dispatches",
        "known_limitations",
    }
)


@dataclass(frozen=True, slots=True)
class EngineeringQuestionAlphaSessionConfig:
    path: Path
    file_digest: Digest
    product_repository: str
    product_commit: str
    product_tree: str
    repository: str
    repository_id: str
    binding_id: str
    repository_revision: str
    source_profile_ref: str
    source_paths: tuple[str, ...]
    document_paths: tuple[str, ...]
    build_paths: tuple[str, ...]
    test_paths: tuple[str, ...]
    excluded_source_paths: tuple[str, ...]
    ordered_envelope: str
    snapshot_bundles: tuple[str, ...]
    cognition_snapshot_id: str | None
    response_language: str
    session_ref: str
    authorization_message_digest: Digest
    authorized_at: datetime
    expires_at: datetime
    conformance_result: str
    gateway_database: str
    launch_receipt: str
    terminal_receipt: str
    maximum_questions: int
    maximum_dispatches_per_question: int
    maximum_total_dispatches: int
    known_limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreparedEngineeringQuestionAlpha:
    assembly: DeepSeekEngineeringQuestionSessionBrowserAssembly
    session_config: EngineeringQuestionAlphaSessionConfig
    session_authority: EngineeringQuestionSessionAuthority
    request_template: EngineeringQuestionSessionRequestTemplate
    evaluation_subject_digest: Digest
    product_candidate_commit: str
    product_candidate_tree: str
    ordered_bundle_digest: Digest
    ordered_file_digest: Digest
    snapshot_bundle_digests: tuple[Digest, ...]
    snapshot_file_digests: tuple[Digest, ...]
    conformance_result_digest: Digest

    def public_status(self) -> dict[str, object]:
        return {
            **self.assembly.product.health(),
            "schema": "SWM-ENGINEERING-QA-ALPHA-LAUNCH@1",
            "url": f"http://127.0.0.1:{ENGINEERING_QA_ALPHA_PORT}/",
            "product_candidate_commit": self.product_candidate_commit,
            "product_candidate_tree": self.product_candidate_tree,
            "session_config_file_digest": self.session_config.file_digest.value,
            "evaluation_subject_digest": self.evaluation_subject_digest.value,
            "session_authorized_at": _time(self.session_authority.authorized_at),
            "session_expires_at": _time(self.session_authority.expires_at),
        }

    def launch_receipt(self) -> dict[str, object]:
        if (
            self.assembly.execution_factory.runtimes
            or self.assembly.execution_factory.transports
            or self.assembly.execution_factory.submission_receipts
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA Alpha launch receipt requires zero accepted questions",
            )
        core = {
            "schema": "SWM-ENGINEERING-QA-ALPHA-LAUNCH-RECEIPT@1",
            "status": "SESSION_AUTHORIZED_NOT_DISPATCHED",
            "public_status": self.public_status(),
            "request_template": self.request_template.public_view(),
            "world_model": {
                "read_authority_digest": (
                    self.request_template.world_model_read_authority_digest.value
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
            "session_authority": self.session_authority.model_view(),
            "conformance_result_digest": self.conformance_result_digest.value,
            "accepted_question_count_at_seal": 0,
            "provider_dispatch_count_at_seal": 0,
            "request_retry_count": 0,
            "provider_switch_count": 0,
            "production_activation": "NOT_EXECUTED",
        }
        return _sealed_document(core)

    def terminal_receipt(self) -> dict[str, object]:
        factory = self.assembly.execution_factory
        runtimes = factory.runtimes
        transports = factory.transports
        submissions = factory.submission_receipts
        if not (len(runtimes) == len(transports) == len(submissions)):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA Alpha terminal audit identities are incomplete",
            )
        question_audits: list[dict[str, object]] = []
        dispatch_attempt_count = 0
        for ordinal, (runtime, transport, submission) in enumerate(
            zip(runtimes, transports, submissions),
            start=1,
        ):
            dispatch_audits = runtime.output_source.audits
            dispatch_attempt_count += len(dispatch_audits)
            run_authorization = runtime.authorizer.run_authorization
            question_audits.append(
                {
                    "ordinal": ordinal,
                    "submission_receipt_id": submission.receipt_id.value,
                    "submission_receipt_digest": submission.digest.value,
                    "question_digest": submission.question_digest.value,
                    "question_utf8_bytes": submission.question_utf8_bytes,
                    "submitted_at": _time(submission.submitted_at),
                    "run_authorization_digest": run_authorization.digest.value,
                    "request_digest": run_authorization.request_digest.value,
                    "dispatch_attempt_count": len(dispatch_audits),
                    "dispatch_audits": tuple(
                        item.model_view() for item in dispatch_audits
                    ),
                    "transport_audit": deepseek_transport_session_audit(transport),
                }
            )
        core = {
            "schema": "SWM-ENGINEERING-QA-ALPHA-TERMINAL-RECEIPT@1",
            "status": (
                "STOPPED_AFTER_DISPATCH"
                if dispatch_attempt_count
                else "STOPPED_WITHOUT_DISPATCH"
            ),
            "session_authority_digest": self.session_authority.digest.value,
            "evaluation_subject_digest": self.evaluation_subject_digest.value,
            "accepted_question_count": len(submissions),
            "dispatch_attempt_count": dispatch_attempt_count,
            "question_audits": tuple(question_audits),
            "request_retry_count": 0,
            "provider_switch_count": 0,
            "production_activation": "NOT_EXECUTED",
        }
        return _sealed_document(core)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swm-engineering-qa",
        description="Launch one exact sustained Engineering QA Web Alpha session",
    )
    parser.add_argument("--session-config", required=True)
    return parser


def load_engineering_question_alpha_session_config(
    value: str | Path,
) -> EngineeringQuestionAlphaSessionConfig:
    path = _canonical_private_file(value, "Engineering QA Alpha session config")
    raw = path.read_bytes()
    if not raw or len(raw) > _MAXIMUM_SESSION_CONFIG_BYTES:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA Alpha session config has an invalid size",
        )
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA Alpha session config is not unique-key UTF-8 JSON",
        ) from exc
    if not isinstance(decoded, Mapping) or set(decoded) != _SESSION_CONFIG_FIELDS:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA Alpha session config contains missing or unknown fields",
        )
    if decoded["schema"] != ENGINEERING_QA_ALPHA_SESSION_CONFIG_SCHEMA:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA Alpha session config schema is not current",
        )
    try:
        authorization_message_digest = Digest(
            _required_text(decoded, "authorization_message_digest")
        )
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA Alpha authorization message digest is invalid",
        ) from exc
    cognition_snapshot_id = decoded["cognition_snapshot_id"]
    if cognition_snapshot_id is not None:
        cognition_snapshot_id = _required_text(decoded, "cognition_snapshot_id")
    return EngineeringQuestionAlphaSessionConfig(
        path=path,
        file_digest=Digest("sha256:" + sha256(raw).hexdigest()),
        product_repository=_required_text(decoded, "product_repository"),
        product_commit=_required_text(decoded, "product_commit"),
        product_tree=_required_text(decoded, "product_tree"),
        repository=_required_text(decoded, "repository"),
        repository_id=_required_text(decoded, "repository_id"),
        binding_id=_required_text(decoded, "binding_id"),
        repository_revision=_required_text(decoded, "repository_revision"),
        source_profile_ref=_required_text(decoded, "source_profile_ref"),
        source_paths=_required_text_list(decoded, "source_paths"),
        document_paths=_required_text_list(decoded, "document_paths"),
        build_paths=_required_text_list(decoded, "build_paths"),
        test_paths=_required_text_list(decoded, "test_paths"),
        excluded_source_paths=_required_text_list(
            decoded, "excluded_source_paths"
        ),
        ordered_envelope=_required_text(decoded, "ordered_envelope"),
        snapshot_bundles=_required_text_list(decoded, "snapshot_bundles"),
        cognition_snapshot_id=cognition_snapshot_id,
        response_language=_required_text(decoded, "response_language"),
        session_ref=_required_text(decoded, "session_ref"),
        authorization_message_digest=authorization_message_digest,
        authorized_at=_required_time(decoded, "authorized_at"),
        expires_at=_required_time(decoded, "expires_at"),
        conformance_result=_required_text(decoded, "conformance_result"),
        gateway_database=_required_text(decoded, "gateway_database"),
        launch_receipt=_required_text(decoded, "launch_receipt"),
        terminal_receipt=_required_text(decoded, "terminal_receipt"),
        maximum_questions=_required_positive_int(decoded, "maximum_questions"),
        maximum_dispatches_per_question=_required_positive_int(
            decoded, "maximum_dispatches_per_question"
        ),
        maximum_total_dispatches=_required_positive_int(
            decoded, "maximum_total_dispatches"
        ),
        known_limitations=_required_text_list(decoded, "known_limitations"),
    )


def prepare_engineering_question_alpha(
    session_config: EngineeringQuestionAlphaSessionConfig,
    *,
    database: SqliteDatabase,
    transport_factory: Callable[[], DeepSeekChatCompletionsTransport],
    at: datetime,
) -> PreparedEngineeringQuestionAlpha:
    current = _aware_utc(at)
    product_repository = _canonical_directory(
        session_config.product_repository,
        "product repository",
    )
    product_commit, product_tree = _verify_product_candidate(
        repository=product_repository,
        expected_commit=session_config.product_commit,
        expected_tree=session_config.product_tree,
        implementation_path=Path(__file__),
    )
    source_repository = _canonical_directory(
        session_config.repository,
        "source repository",
    )
    repository_revision = _exact_source_revision(
        source_repository,
        session_config.repository_revision,
    )
    repository_id = _stable_id(session_config.repository_id, "repository ID")
    binding_id = _stable_id(session_config.binding_id, "binding ID")
    profile = LocalGitEvidenceClassProfile.create(
        profile_ref=session_config.source_profile_ref,
        binding_id=binding_id,
        evidence_class_paths={
            EngineeringEvidenceClass.SOURCE: session_config.source_paths,
            EngineeringEvidenceClass.REPOSITORY_DOCUMENT: (
                session_config.document_paths
            ),
            EngineeringEvidenceClass.BUILD_CONFIGURATION: (
                session_config.build_paths
            ),
            EngineeringEvidenceClass.TEST: session_config.test_paths,
        },
    )
    source_allowlist = tuple(
        path
        for _, paths in profile.evidence_class_paths
        for path in paths
    )
    if any(
        _source_paths_overlap(allowed, excluded)
        for allowed in source_allowlist
        for excluded in session_config.excluded_source_paths
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Engineering QA excluded source path overlaps an authorized Source Profile path",
        )

    store = FileStructureReadBundleStore()
    ordered_path = _canonical_regular_file(
        session_config.ordered_envelope,
        "ordered Structure Read Bundle",
    )
    snapshot_paths = tuple(
        _canonical_regular_file(path, "Snapshot Structure Read Bundle")
        for path in session_config.snapshot_bundles
    )
    ordered, ordered_file_digest = store.read_ordered(str(ordered_path))
    loaded = tuple(store.read_snapshot(str(path)) for path in snapshot_paths)
    view = StructureViewService(ordered, loaded)
    snapshot_bundle = _select_cognition_snapshot(
        loaded=loaded,
        requested_snapshot_id=session_config.cognition_snapshot_id,
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
    conformance_path = _canonical_regular_file(
        session_config.conformance_result,
        "DeepSeek conformance result",
    )
    qualification = load_deepseek_chat_conformance_qualification(
        str(conformance_path),
        provider_configuration,
        now=current,
    )
    model_configuration = engineering_question_deepseek_configuration(
        provider_configuration=provider_configuration,
        qualification=qualification,
        maximum_calls=session_config.maximum_dispatches_per_question,
        at=current,
    )
    request_template = EngineeringQuestionSessionRequestTemplate.create(
        response_language=session_config.response_language,
        repository_id=repository_id,
        binding_id=binding_id,
        repository_revision=repository_revision,
        source_profile_ref=profile.profile_ref,
        source_profile_digest=profile.profile_digest,
        world_model_read_authority_digest=cognition.read_authority_digest,
        source_allowlist=source_allowlist,
        provider_disclosure_policy=ENGINEERING_QUESTION_DISCLOSURE_POLICY_REF,
        limits=EngineeringQuestionResourceLimits(
            maximum_total_model_role_calls=(
                session_config.maximum_dispatches_per_question
            ),
        ),
        source_class_allowlist=tuple(
            (evidence_class.value, paths)
            for evidence_class, paths in profile.evidence_class_paths
        ),
        excluded_source_paths=session_config.excluded_source_paths,
    )
    evaluation_subject = engineering_question_alpha_subject_digest(
        product_commit=product_commit,
        product_tree=product_tree,
        request_template_digest=request_template.digest,
        ordered_bundle_digest=view.ordered_bundle_digest,
        ordered_file_digest=ordered_file_digest,
        snapshot_bundle_digests=view.snapshot_bundle_digests,
        snapshot_file_digests=tuple(item[1] for item in loaded),
        provider_binding_digest=model_configuration.digest,
        conformance_result_digest=qualification.result_digest,
        session_config_file_digest=session_config.file_digest,
    )
    session_authority = EngineeringQuestionSessionAuthority.create(
        session_ref=session_config.session_ref,
        product_candidate_digest=evaluation_subject,
        request_template_digest=request_template.digest,
        configuration=model_configuration,
        maximum_questions=session_config.maximum_questions,
        maximum_dispatches_per_question=(
            session_config.maximum_dispatches_per_question
        ),
        maximum_total_dispatches=session_config.maximum_total_dispatches,
        authorized_at=session_config.authorized_at,
        expires_at=session_config.expires_at,
        authorization_ref=(
            "codex-user-message:"
            + session_config.authorization_message_digest.value
        ),
        authorization_message_digest=(
            session_config.authorization_message_digest
        ),
    )
    worker = LocalGitRetrievalWorker(
        source_repository,
        repository_id=repository_id,
        binding_id=binding_id,
        source_profile=profile,
    )
    assembly = create_deepseek_engineering_question_session_browser_assembly(
        repository=SqliteModelGatewayRepository(database),
        transport_factory=transport_factory,
        provider_configuration=provider_configuration,
        qualification=qualification,
        configuration=model_configuration,
        session_authority=session_authority,
        request_template=request_template,
        product_candidate_digest=evaluation_subject,
        cognition_projector=cognition,
        source_broker=SourceBroker(source_profile=profile),
        retrieval_worker=worker,
        known_limitations=session_config.known_limitations,
        at=current,
    )
    return PreparedEngineeringQuestionAlpha(
        assembly=assembly,
        session_config=session_config,
        session_authority=session_authority,
        request_template=request_template,
        evaluation_subject_digest=evaluation_subject,
        product_candidate_commit=product_commit,
        product_candidate_tree=product_tree,
        ordered_bundle_digest=view.ordered_bundle_digest,
        ordered_file_digest=ordered_file_digest,
        snapshot_bundle_digests=view.snapshot_bundle_digests,
        snapshot_file_digests=tuple(item[1] for item in loaded),
        conformance_result_digest=qualification.result_digest,
    )


def engineering_question_alpha_subject_digest(
    *,
    product_commit: str,
    product_tree: str,
    request_template_digest: Digest,
    ordered_bundle_digest: Digest,
    ordered_file_digest: Digest,
    snapshot_bundle_digests: Sequence[Digest],
    snapshot_file_digests: Sequence[Digest],
    provider_binding_digest: Digest,
    conformance_result_digest: Digest,
    session_config_file_digest: Digest,
) -> Digest:
    commit = _git_oid(product_commit, "product candidate commit")
    tree = _git_oid(product_tree, "product candidate tree")
    if (
        not snapshot_bundle_digests
        or len(snapshot_bundle_digests) != len(snapshot_file_digests)
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA Alpha requires exact semantic and file digests for every Snapshot",
        )
    return digest_of(
        [
            ENGINEERING_QA_ALPHA_SUBJECT_SCHEMA,
            {
                "product_commit": commit,
                "product_tree": tree,
                "request_template_digest": request_template_digest.value,
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
                "session_config_file_digest": session_config_file_digest.value,
                "loopback_origin": (
                    f"http://127.0.0.1:{ENGINEERING_QA_ALPHA_PORT}/"
                ),
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
    prepared: PreparedEngineeringQuestionAlpha | None = None
    try:
        session_config = load_engineering_question_alpha_session_config(
            arguments.session_config
        )
        gateway_database = _new_database_path(session_config.gateway_database)
        launch_receipt = _new_private_output_path(session_config.launch_receipt)
        terminal_receipt = _new_private_output_path(session_config.terminal_receipt)
        if len(
            {
                session_config.path,
                gateway_database,
                launch_receipt,
                terminal_receipt,
            }
        ) != 4:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Session config, Gateway database, and Alpha receipts require distinct paths",
            )
        provider_configuration = DeepSeekModelConfiguration()

        def transport_factory() -> PersistentDeepSeekChatTransport:
            return PersistentDeepSeekChatTransport(
                api_key_resolver=provider_configuration.resolve_api_key
            )

        with SqliteDatabase(gateway_database) as database:
            prepared = prepare_engineering_question_alpha(
                session_config,
                database=database,
                transport_factory=transport_factory,
                at=datetime.now(timezone.utc),
            )
            with make_server(
                "127.0.0.1",
                ENGINEERING_QA_ALPHA_PORT,
                prepared.assembly.application,
                handler_class=_QuietLoopbackHandler,
            ) as server:
                if server.server_port != ENGINEERING_QA_ALPHA_PORT:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "Engineering QA Alpha listener port drifted",
                    )
                _write_new_private_json(
                    launch_receipt,
                    prepared.launch_receipt(),
                )
                output.write(
                    canonical_json_bytes(prepared.public_status()).decode("utf-8")
                    + "\n"
                )
                output.flush()
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    pass
                _write_new_private_json(
                    terminal_receipt,
                    prepared.terminal_receipt(),
                )
        return 0
    except (
        DomainError,
        OSError,
        ValueError,
        subprocess.SubprocessError,
    ) as exc:
        payload = {
            "error": (
                exc.code.value
                if isinstance(exc, DomainError)
                else "INVALID_ARGUMENT"
            ),
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
            "production_activation": "NOT_EXECUTED",
        }
        error_output.write(canonical_json_bytes(payload).decode("utf-8") + "\n")
        error_output.flush()
        return 2
    finally:
        if prepared is not None:
            for transport in prepared.assembly.execution_factory.transports:
                close = getattr(transport, "close", None)
                if callable(close):
                    close()


def _canonical_private_file(value: str | Path, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be absolute")
    try:
        resolved = path.resolve(strict=True)
        metadata = path.stat()
    except OSError as exc:
        raise DomainError(
            ErrorCode.SOURCE_TARGET_NOT_FOUND,
            f"{label} does not exist",
        ) from exc
    if (
        resolved != path
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) & 0o077
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            f"{label} must be a canonical owner-private regular file",
        )
    return path


def _canonical_regular_file(value: str | Path, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise DomainError(
            ErrorCode.SOURCE_TARGET_NOT_FOUND,
            f"{label} does not exist",
        ) from exc
    if resolved != path or not resolved.is_file():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be a canonical non-symlink regular file",
        )
    return path


def _unique_json_object(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _required_text(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > 65_536
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering QA Alpha session config field {field} is invalid",
        )
    return value


def _required_text_list(
    document: Mapping[str, object],
    field: str,
) -> tuple[str, ...]:
    value = document.get(field)
    if not isinstance(value, list) or not value:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering QA Alpha session config field {field} must be a non-empty list",
        )
    values = tuple(value)
    for item in values:
        if (
            not isinstance(item, str)
            or not item
            or item != item.strip()
            or len(item.encode("utf-8")) > 65_536
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                f"Engineering QA Alpha session config field {field} contains invalid text",
            )
    if len(values) != len(set(values)):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering QA Alpha session config field {field} contains duplicates",
        )
    return values


def _required_positive_int(document: Mapping[str, object], field: str) -> int:
    value = document.get(field)
    if type(value) is not int or value < 1:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering QA Alpha session config field {field} must be positive",
        )
    return value


def _required_time(document: Mapping[str, object], field: str) -> datetime:
    value = _required_text(document, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering QA Alpha session config field {field} is not a time",
        ) from exc
    current = _aware_utc(parsed)
    if _time(current) != value:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering QA Alpha session config field {field} is not canonical UTC",
        )
    return current


def _source_paths_overlap(left: str, right: str) -> bool:
    return (
        left == "."
        or right == "."
        or left == right
        or left.startswith(right + "/")
        or right.startswith(left + "/")
    )


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ENGINEERING_QA_ALPHA_PORT",
    "ENGINEERING_QA_ALPHA_SESSION_CONFIG_SCHEMA",
    "ENGINEERING_QA_ALPHA_SUBJECT_SCHEMA",
    "EngineeringQuestionAlphaSessionConfig",
    "PreparedEngineeringQuestionAlpha",
    "build_parser",
    "engineering_question_alpha_subject_digest",
    "load_engineering_question_alpha_session_config",
    "main",
    "prepare_engineering_question_alpha",
]
