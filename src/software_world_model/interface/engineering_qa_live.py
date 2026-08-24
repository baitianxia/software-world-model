"""Trusted composition for an exactly authorized DeepSeek Engineering QA run.

Construction is credential-lazy: the supplied transport owns late credential
resolution and this module never reads or stores a key.  A caller must first
freeze one immutable Request and its user run-disclosure authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Callable

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekChatCompletionsTransport,
    DeepSeekModelConfiguration,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DeepSeekChatConformanceQualification,
)
from software_world_model.ai_infrastructure.engineering_question_model_source import (
    EngineeringQuestionModelConfiguration,
    EngineeringQuestionModelEgressPolicy,
    EngineeringQuestionRunDisclosureAuthorization,
    EngineeringQuestionSessionAuthority,
    EngineeringQuestionSessionRunDisclosureAuthorization,
    EngineeringQuestionSubmissionReceipt,
    ModelBackedEngineeringQuestionStructuredOutputSource,
    PolicyEnforcingEngineeringQuestionModelGateway,
    SealedEngineeringQuestionRoleDisclosureAuthorizer,
)
from software_world_model.ai_infrastructure.engineering_question_strategy import (
    EngineeringQuestionStructuredStrategyBundle,
    engineering_question_output_schemas,
)
from software_world_model.ai_infrastructure.model_gateway import (
    ModelGateway,
    ModelGatewayRepository,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    Uuid4IdGenerator,
    digest_of,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringQuestionAnsweringService,
    EngineeringQuestionRequest,
    RetrievalWorker,
    SourceBroker,
    WorldModelCognitionProjector,
)
from .engineering_qa_browser import (
    EngineeringQuestionBrowserApplication,
    EngineeringQuestionSessionExecution,
    EngineeringQuestionSessionRequestTemplate,
    EngineeringQuestionWebRuntimeStatus,
    ExactAuthorizedEngineeringQuestionRequestFactory,
    InMemoryEngineeringQuestionWebProduct,
    InMemoryEngineeringQuestionSessionWebProduct,
)


@dataclass(frozen=True, slots=True)
class DeepSeekEngineeringQuestionRoleRuntime:
    configuration: EngineeringQuestionModelConfiguration
    adapter: DeepSeekChatCompletionsNoToolsAdapter
    gateway: ModelGateway
    policy: EngineeringQuestionModelEgressPolicy
    authorizer: SealedEngineeringQuestionRoleDisclosureAuthorizer
    output_source: ModelBackedEngineeringQuestionStructuredOutputSource
    strategy: EngineeringQuestionStructuredStrategyBundle


@dataclass(frozen=True, slots=True)
class DeepSeekEngineeringQuestionBrowserAssembly:
    role_runtime: DeepSeekEngineeringQuestionRoleRuntime
    service: EngineeringQuestionAnsweringService
    product: InMemoryEngineeringQuestionWebProduct
    application: EngineeringQuestionBrowserApplication


@dataclass(frozen=True, slots=True)
class DeepSeekEngineeringQuestionSessionBrowserAssembly:
    execution_factory: "DeepSeekEngineeringQuestionSessionExecutionFactory"
    product: InMemoryEngineeringQuestionSessionWebProduct
    application: EngineeringQuestionBrowserApplication


class DeepSeekEngineeringQuestionSessionExecutionFactory:
    """Compile each submitted question into a fresh exact run and role runtime."""

    def __init__(
        self,
        *,
        repository: ModelGatewayRepository,
        transport_factory: Callable[[], DeepSeekChatCompletionsTransport],
        provider_configuration: DeepSeekModelConfiguration,
        qualification: DeepSeekChatConformanceQualification,
        configuration: EngineeringQuestionModelConfiguration,
        session_authority: EngineeringQuestionSessionAuthority,
        request_template: EngineeringQuestionSessionRequestTemplate,
        product_candidate_digest: Digest,
        cognition_projector: WorldModelCognitionProjector,
        source_broker: SourceBroker,
        retrieval_worker: RetrievalWorker,
        clock: Callable[[], datetime] | None = None,
        id_generator: IdGenerator | None = None,
    ) -> None:
        self.session_authority = session_authority
        self.request_template = request_template
        self._repository = repository
        self._transport_factory = transport_factory
        self._provider_configuration = provider_configuration
        self._qualification = qualification
        self._configuration = configuration
        self._product_candidate_digest = product_candidate_digest
        self._cognition_projector = cognition_projector
        self._source_broker = source_broker
        self._retrieval_worker = retrieval_worker
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._ids = id_generator or Uuid4IdGenerator()
        self._lock = Lock()
        self._runtimes: list[DeepSeekEngineeringQuestionRoleRuntime] = []
        self._transports: list[DeepSeekChatCompletionsTransport] = []
        self._submission_receipts: list[EngineeringQuestionSubmissionReceipt] = []
        self.session_authority.require_current(
            configuration=self._configuration,
            request_template_digest=self.request_template.digest,
            product_candidate_digest=self._product_candidate_digest,
            at=self._clock(),
        )
        if (
            self.request_template.provider_disclosure_policy
            != self._configuration.provider_disclosure_policy_ref
            or self.request_template.limits.maximum_total_model_role_calls
            != self.session_authority.maximum_dispatches_per_question
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA session template does not match its model fuse",
            )

    @property
    def runtimes(self) -> tuple[DeepSeekEngineeringQuestionRoleRuntime, ...]:
        with self._lock:
            return tuple(self._runtimes)

    @property
    def transports(self) -> tuple[DeepSeekChatCompletionsTransport, ...]:
        with self._lock:
            return tuple(self._transports)

    @property
    def submission_receipts(
        self,
    ) -> tuple[EngineeringQuestionSubmissionReceipt, ...]:
        with self._lock:
            return tuple(self._submission_receipts)

    def create(
        self,
        *,
        question: str,
        disclosure_acknowledged: bool,
    ) -> EngineeringQuestionSessionExecution:
        with self._lock:
            current = self._clock()
            self.session_authority.require_current(
                configuration=self._configuration,
                request_template_digest=self.request_template.digest,
                product_candidate_digest=self._product_candidate_digest,
                at=current,
            )
            receipt = EngineeringQuestionSubmissionReceipt.create(
                receipt_id=self._ids.new("engq_submission"),
                session_authority=self.session_authority,
                question=question,
                disclosure_acknowledged=disclosure_acknowledged,
                submitted_at=current,
            )
            if any(
                existing.receipt_id == receipt.receipt_id
                or existing.digest == receipt.digest
                for existing in self._submission_receipts
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Engineering QA session ID generator repeated a submission identity",
                )
            request = self.request_template.create_request(
                receipt=receipt,
                question=question,
            )
            evaluation_subject = digest_of(
                [
                    "ENGINEERING_QA_SESSION_QUESTION_SUBJECT@1",
                    self._product_candidate_digest.value,
                    self.session_authority.digest.value,
                    receipt.digest.value,
                    request.digest.value,
                ]
            )
            run_authorization = (
                EngineeringQuestionSessionRunDisclosureAuthorization.create_from_session(
                    run_ref=self._ids.new("engq_run").value,
                    request=request,
                    evaluation_subject_digest=evaluation_subject,
                    configuration=self._configuration,
                    session_authority=self.session_authority,
                    question_submission_receipt=receipt,
                    request_template_digest=self.request_template.digest,
                    product_candidate_digest=self._product_candidate_digest,
                )
            )
            transport = self._transport_factory()
            try:
                runtime = create_deepseek_engineering_question_role_runtime(
                    repository=self._repository,
                    transport=transport,
                    provider_configuration=self._provider_configuration,
                    qualification=self._qualification,
                    run_authorization=run_authorization,
                    configuration=self._configuration,
                    clock=self._clock,
                )
                strategy = runtime.strategy
                service = EngineeringQuestionAnsweringService(
                    question_understanding_role=strategy.question_understanding,
                    cognition_projector=self._cognition_projector,
                    initial_investigation_role=strategy.initial_investigation,
                    verification_investigation_role=(
                        strategy.verification_investigation
                    ),
                    source_broker=self._source_broker,
                    retrieval_worker=self._retrieval_worker,
                    answer_role=strategy.answer,
                    reviewer_role=strategy.reviewer,
                )
            except Exception:
                close_failed_transport = getattr(transport, "close", None)
                if callable(close_failed_transport):
                    close_failed_transport()
                raise
            self._runtimes.append(runtime)
            self._transports.append(transport)
            self._submission_receipts.append(receipt)
            close = getattr(transport, "close", None)
            return EngineeringQuestionSessionExecution(
                request=request,
                submission_receipt=receipt,
                run_authorization=run_authorization,
                service=service,
                dispatch_attempt_count=(
                    lambda: runtime.output_source.dispatch_attempt_count
                ),
                close=close if callable(close) else (lambda: None),
            )


def engineering_question_deepseek_configuration(
    *,
    provider_configuration: DeepSeekModelConfiguration,
    qualification: DeepSeekChatConformanceQualification,
    maximum_output_tokens: int = 4_096,
    timeout_milliseconds: int = 180_000,
    maximum_calls: int = 24,
    at: datetime | None = None,
) -> EngineeringQuestionModelConfiguration:
    current = at or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA DeepSeek composition time must be timezone-aware",
        )
    if (
        qualification.adapter_version != provider_configuration.adapter_version
        or qualification.provider_configuration_fingerprint
        != provider_configuration.fingerprint
        or qualification.qualified_model_fingerprints
        != provider_configuration.qualified_model_identities
        or current.astimezone(timezone.utc)
        >= qualification.valid_until.astimezone(timezone.utc)
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek qualification does not bind the exact Engineering QA Provider configuration",
        )
    return EngineeringQuestionModelConfiguration(
        provider_type=provider_configuration.provider_type,
        adapter_version=provider_configuration.adapter_version,
        endpoint=provider_configuration.endpoint,
        model_ref=provider_configuration.model_ref,
        expected_actual_model_fingerprint=(
            provider_configuration.actual_model_fingerprint
        ),
        provider_configuration_fingerprint=provider_configuration.fingerprint,
        secret_reference=provider_configuration.secret_reference,
        qualification_ref=qualification.result_ref,
        qualification_valid_until=qualification.valid_until,
        maximum_output_tokens=maximum_output_tokens,
        timeout_milliseconds=timeout_milliseconds,
        maximum_calls=maximum_calls,
    )


def create_deepseek_engineering_question_role_runtime(
    *,
    repository: ModelGatewayRepository,
    transport: DeepSeekChatCompletionsTransport,
    provider_configuration: DeepSeekModelConfiguration,
    qualification: DeepSeekChatConformanceQualification,
    run_authorization: EngineeringQuestionRunDisclosureAuthorization,
    configuration: EngineeringQuestionModelConfiguration | None = None,
    clock: Callable[[], datetime] | None = None,
) -> DeepSeekEngineeringQuestionRoleRuntime:
    runtime_clock = clock or (lambda: datetime.now(timezone.utc))
    current = runtime_clock()
    expected_configuration = engineering_question_deepseek_configuration(
        provider_configuration=provider_configuration,
        qualification=qualification,
        maximum_output_tokens=(
            configuration.maximum_output_tokens if configuration else 4_096
        ),
        timeout_milliseconds=(
            configuration.timeout_milliseconds if configuration else 180_000
        ),
        maximum_calls=(configuration.maximum_calls if configuration else 24),
        at=current,
    )
    if configuration is not None and configuration != expected_configuration:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Engineering QA model configuration drifts from the exact DeepSeek binding",
        )
    configuration = expected_configuration
    run_authorization.require_current(
        configuration=configuration,
        at=current,
    )
    adapter = DeepSeekChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=provider_configuration,
        output_schemas=engineering_question_output_schemas(),
        live_qualification=qualification,
    )
    gateway = ModelGateway(repository, (adapter,), clock=runtime_clock)
    policy = EngineeringQuestionModelEgressPolicy(
        run_authorization=run_authorization,
        configuration=configuration,
        clock=runtime_clock,
    )
    protected_gateway = PolicyEnforcingEngineeringQuestionModelGateway(
        gateway=gateway,
        policy=policy,
    )
    authorizer = SealedEngineeringQuestionRoleDisclosureAuthorizer(
        run_authorization=run_authorization,
        configuration=configuration,
        clock=runtime_clock,
    )
    output_source = ModelBackedEngineeringQuestionStructuredOutputSource(
        gateway=protected_gateway,
        configuration=configuration,
        authorizer=authorizer,
        clock=runtime_clock,
    )
    return DeepSeekEngineeringQuestionRoleRuntime(
        configuration=configuration,
        adapter=adapter,
        gateway=gateway,
        policy=policy,
        authorizer=authorizer,
        output_source=output_source,
        strategy=EngineeringQuestionStructuredStrategyBundle.create(output_source),
    )


def create_deepseek_engineering_question_browser_assembly(
    *,
    request: EngineeringQuestionRequest,
    role_runtime: DeepSeekEngineeringQuestionRoleRuntime,
    run_authorization: EngineeringQuestionRunDisclosureAuthorization,
    cognition_projector: WorldModelCognitionProjector,
    source_broker: SourceBroker,
    retrieval_worker: RetrievalWorker,
    at: datetime,
) -> DeepSeekEngineeringQuestionBrowserAssembly:
    run_authorization.require_current(
        configuration=role_runtime.configuration,
        at=at,
    )
    if request.digest != run_authorization.request_digest:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering QA browser Request is not the role runtime's authorized Request",
        )
    strategy = role_runtime.strategy
    service = EngineeringQuestionAnsweringService(
        question_understanding_role=strategy.question_understanding,
        cognition_projector=cognition_projector,
        initial_investigation_role=strategy.initial_investigation,
        verification_investigation_role=strategy.verification_investigation,
        source_broker=source_broker,
        retrieval_worker=retrieval_worker,
        answer_role=strategy.answer,
        reviewer_role=strategy.reviewer,
    )
    request_factory = ExactAuthorizedEngineeringQuestionRequestFactory(
        request=request,
        run_authorization=run_authorization,
    )
    runtime_status = EngineeringQuestionWebRuntimeStatus.authorized(
        request=request,
        configuration=role_runtime.configuration,
        run_authorization=run_authorization,
        at=at,
    )
    product = InMemoryEngineeringQuestionWebProduct(
        service=service,
        request_factory=request_factory,
        runtime_status=runtime_status,
    )
    return DeepSeekEngineeringQuestionBrowserAssembly(
        role_runtime=role_runtime,
        service=service,
        product=product,
        application=EngineeringQuestionBrowserApplication(product),
    )


def create_deepseek_engineering_question_session_browser_assembly(
    *,
    repository: ModelGatewayRepository,
    transport_factory: Callable[[], DeepSeekChatCompletionsTransport],
    provider_configuration: DeepSeekModelConfiguration,
    qualification: DeepSeekChatConformanceQualification,
    configuration: EngineeringQuestionModelConfiguration,
    session_authority: EngineeringQuestionSessionAuthority,
    request_template: EngineeringQuestionSessionRequestTemplate,
    product_candidate_digest: Digest,
    cognition_projector: WorldModelCognitionProjector,
    source_broker: SourceBroker,
    retrieval_worker: RetrievalWorker,
    known_limitations: tuple[str, ...],
    at: datetime,
    clock: Callable[[], datetime] | None = None,
    id_generator: IdGenerator | None = None,
) -> DeepSeekEngineeringQuestionSessionBrowserAssembly:
    runtime_clock = clock or (lambda: datetime.now(timezone.utc))
    session_authority.require_current(
        configuration=configuration,
        request_template_digest=request_template.digest,
        product_candidate_digest=product_candidate_digest,
        at=at,
    )
    execution_factory = DeepSeekEngineeringQuestionSessionExecutionFactory(
        repository=repository,
        transport_factory=transport_factory,
        provider_configuration=provider_configuration,
        qualification=qualification,
        configuration=configuration,
        session_authority=session_authority,
        request_template=request_template,
        product_candidate_digest=product_candidate_digest,
        cognition_projector=cognition_projector,
        source_broker=source_broker,
        retrieval_worker=retrieval_worker,
        clock=runtime_clock,
        id_generator=id_generator,
    )
    runtime_status = EngineeringQuestionWebRuntimeStatus.session_authorized(
        template=request_template,
        configuration=configuration,
        session_authority=session_authority,
        product_candidate_digest=product_candidate_digest,
        at=at,
    )
    product = InMemoryEngineeringQuestionSessionWebProduct(
        execution_factory=execution_factory,
        runtime_status=runtime_status,
        known_limitations=known_limitations,
    )
    return DeepSeekEngineeringQuestionSessionBrowserAssembly(
        execution_factory=execution_factory,
        product=product,
        application=EngineeringQuestionBrowserApplication(product),
    )
