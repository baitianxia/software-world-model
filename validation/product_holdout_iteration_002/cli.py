"""Command line entry point for the sealed product validation workflow."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Mapping, Sequence, TextIO

from software_world_model.ai_infrastructure import (
    AgenticModelStrategyConfiguration,
    ModelGateway,
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    evidence_first_task_output_schemas,
    evidence_first_task_strategy_implementation_digest,
    load_ark_chat_conformance_qualification,
)
from software_world_model.application_services import (
    CurrentEvaluationQualificationVerifier,
    EvaluationQualificationDependencies,
    QualificationProof,
    ProductValidationService,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    IdempotencyKey,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteCapabilityEvaluationRepository,
    SqliteDatabase,
    SqliteModelGatewayRepository,
    SqliteProductValidationRepository,
)
from software_world_model.source_integration import LocalGitConnector

from .direct_answer import (
    DirectSourceAnswerExecutor,
    direct_answer_output_schemas,
)
from .execution import HoldoutTaskAnswerPair
from .manifest import (
    build_task_input,
    load_holdout_suite,
    verify_frozen_checkouts,
)
from .independent_review import (
    INDEPENDENT_REVIEW_DRAFT_SCHEMA,
    load_independent_review,
    seal_independent_review_draft,
)
from .result_store import (
    load_path_result,
    save_answer_pair,
    save_path_result,
    verify_answer_pair_document,
    write_validation_document_once,
)
from .evidence_answer import EvidenceFirstAnswerExecutor


QUALIFICATION_DOCUMENT_SCHEMA = "swm.capability-qualification-proof@1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m validation.product_holdout_iteration_002.cli",
        description="Run and seal the frozen product validation workflow",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    verify = commands.add_parser("verify-inputs")
    verify.add_argument("--workspace-root", default=".")

    export = commands.add_parser("export-qualification")
    export.add_argument("--evaluation-database", required=True)
    export.add_argument("--result-id", required=True)
    export.add_argument("--result-directory", required=True)

    direct = commands.add_parser("run-direct")
    _add_run_arguments(direct, needs_capability_evaluation=False)

    world = commands.add_parser("run-system")
    _add_run_arguments(world, needs_capability_evaluation=True)

    pair = commands.add_parser("seal-pair")
    pair.add_argument("--direct-result", required=True)
    pair.add_argument("--system-result", required=True)
    pair.add_argument("--result-directory", required=True)

    prepare_review = commands.add_parser("prepare-review")
    prepare_review.add_argument("--pair", required=True)
    prepare_review.add_argument("--result-directory", required=True)

    review = commands.add_parser("seal-review")
    review.add_argument("--pair", required=True)
    review.add_argument("--review-draft", required=True)
    review.add_argument("--result-directory", required=True)

    acceptance = commands.add_parser("record-acceptance")
    acceptance.add_argument("--workspace-root", default=".")
    acceptance.add_argument("--evidence-directory", required=True)
    acceptance.add_argument("--conformance-result", required=True)
    acceptance.add_argument("--evaluation-database", required=True)
    acceptance.add_argument("--qualification-proof", required=True)
    acceptance.add_argument("--authority-database", required=True)
    acceptance.add_argument("--valid-for-seconds", type=int, default=604800)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
    transport: object | None = None,
) -> int:
    output = stdout or sys.stdout
    arguments = build_parser().parse_args(argv)
    environment_values = os.environ if environment is None else environment
    try:
        if arguments.command == "verify-inputs":
            suite = load_holdout_suite()
            verify_frozen_checkouts(
                suite, workspace_root=arguments.workspace_root
            )
            payload = {
                "status": "PASS",
                "suite_id": suite["suite_id"],
                "suite_version": suite["suite_version"],
                "suite_digest": suite["suite_digest"],
                "repository_count": len(suite["repositories"]),
                "task_count": len(suite["tasks"]),
                "external_model_called": False,
            }
        elif arguments.command == "export-qualification":
            payload = _export_qualification(arguments)
        elif arguments.command == "seal-pair":
            payload = _seal_pair(arguments)
        elif arguments.command == "prepare-review":
            payload = _prepare_review(arguments)
        elif arguments.command == "seal-review":
            payload = _seal_review(arguments)
        elif arguments.command == "record-acceptance":
            payload = _record_acceptance(arguments)
        elif arguments.command == "run-direct":
            payload = _run_direct(
                arguments,
                environment=environment_values,
                transport=transport,
            )
        else:
            payload = _run_system(
                arguments,
                environment=environment_values,
                transport=transport,
            )
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 0
    except (DomainError, OSError, ValueError) as exc:
        payload = {
            "error": (
                exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT"
            ),
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
        }
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 2


def _add_run_arguments(
    parser: argparse.ArgumentParser, *, needs_capability_evaluation: bool
) -> None:
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--conformance-result", required=True)
    parser.add_argument("--result-directory", required=True)
    if needs_capability_evaluation:
        parser.add_argument("--evaluation-database", required=True)
        parser.add_argument("--qualification-proof", required=True)


def _run_direct(
    arguments: argparse.Namespace,
    *,
    environment: Mapping[str, str],
    transport: object | None,
) -> dict[str, object]:
    suite, task_input, checkout = _verified_task(arguments)
    configuration, conformance, adapter_transport = _provider(
        arguments, environment=environment, transport=transport
    )
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=adapter_transport,
        configuration=configuration,
        output_schemas=direct_answer_output_schemas(),
        live_qualification=conformance,
    )
    runtime_path = _runtime_database_path(
        arguments, task_input=task_input, path="direct"
    )
    with SqliteDatabase(runtime_path) as database:
        gateway = ModelGateway(
            SqliteModelGatewayRepository(database), (adapter,)
        )
        model_configuration = _model_configuration(
            configuration,
            qualification_ref=conformance.result_ref,
            task_input=task_input,
        )
        result = DirectSourceAnswerExecutor(
            gateway=gateway,
            configuration=model_configuration,
            expected_model_fingerprint=configuration.actual_model_fingerprint,
        ).execute(
            task_input=task_input,
            connector=LocalGitConnector(str(checkout)),
            run_id=_path_run_id(arguments.run_id, task_input["task_id"], "direct"),
        )
    result_path = save_path_result(
        result,
        task_input=task_input,
        result_directory=arguments.result_directory,
    )
    return _result_payload(result, result_path, suite)


def _run_system(
    arguments: argparse.Namespace,
    *,
    environment: Mapping[str, str],
    transport: object | None,
) -> dict[str, object]:
    suite, task_input, checkout = _verified_task(arguments)
    configuration, conformance, adapter_transport = _provider(
        arguments, environment=environment, transport=transport
    )
    proof = load_qualification_proof(arguments.qualification_proof)
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=adapter_transport,
        configuration=configuration,
        output_schemas=evidence_first_task_output_schemas(),
        live_qualification=conformance,
    )
    runtime_path = _runtime_database_path(
        arguments, task_input=task_input, path="system"
    )
    with SqliteDatabase(arguments.evaluation_database) as evaluation_database:
        evaluation_repository = SqliteCapabilityEvaluationRepository(
            evaluation_database
        )
        verifier = CurrentEvaluationQualificationVerifier(
            evaluation_repository,
            _qualification_dependencies(configuration, conformance),
        )
        if not verifier.validate(proof):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "capability evaluation proof is not current for this implementation",
            )
        with SqliteDatabase(runtime_path) as database:
            gateway = ModelGateway(
                SqliteModelGatewayRepository(database), (adapter,)
            )
            result = EvidenceFirstAnswerExecutor(
                database=database,
                gateway=gateway,
                configuration=_model_configuration(
                    configuration,
                    qualification_ref=proof.proof_ref,
                    task_input=task_input,
                ),
                qualification=proof,
                qualification_verifier=verifier,
                expected_model_fingerprint=(
                    configuration.actual_model_fingerprint
                ),
            ).execute(
                task_input=task_input,
                checkout_path=checkout,
                run_id=_path_run_id(
                    arguments.run_id, task_input["task_id"], "system"
                ),
            )
    result_path = save_path_result(
        result,
        task_input=task_input,
        result_directory=arguments.result_directory,
    )
    return _result_payload(result, result_path, suite)


def _provider(
    arguments: argparse.Namespace,
    *,
    environment: Mapping[str, str],
    transport: object | None,
):
    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        arguments.conformance_result, configuration
    )
    active_transport = transport or UrllibVolcengineArkChatTransport(
        api_key_resolver=lambda: configuration.resolve_api_key(environment)
    )
    return configuration, conformance, active_transport


def _verified_task(arguments: argparse.Namespace):
    suite = load_holdout_suite()
    verify_frozen_checkouts(suite, workspace_root=arguments.workspace_root)
    task_input = build_task_input(suite, task_id=arguments.task_id)
    repository_id = task_input["repository"]["repository_id"]
    repository = next(
        item
        for item in suite["repositories"]
        if item["repository_id"] == repository_id
    )
    checkout = (
        Path(arguments.workspace_root).resolve() / repository["local_path"]
    ).resolve()
    return suite, task_input, checkout


def _model_configuration(
    configuration: VolcengineArkModelConfiguration,
    *,
    qualification_ref: str,
    task_input: Mapping[str, object],
) -> AgenticModelStrategyConfiguration:
    policy = task_input["resource_policy"]
    return AgenticModelStrategyConfiguration(
        provider_type=configuration.provider_type,
        adapter_version=configuration.adapter_version,
        model_ref=configuration.model_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        qualification_ref=qualification_ref,
        max_output_tokens=policy["maximum_output_tokens_per_call"],
        timeout_milliseconds=policy["timeout_per_call_milliseconds"],
        classification="INTERNAL",
    )


def _runtime_database_path(
    arguments: argparse.Namespace,
    *,
    task_input: Mapping[str, object],
    path: str,
) -> Path:
    directory = (
        Path(arguments.result_directory)
        / "runtime"
        / str(task_input["task_id"])
    )
    directory.mkdir(parents=True, exist_ok=True)
    logical_run_id = _path_run_id(
        arguments.run_id, task_input["task_id"], path
    )
    run_digest = digest_of(logical_run_id).value.removeprefix("sha256:")
    return directory / f"{path}-{run_digest}.sqlite3"


def _seal_pair(arguments: argparse.Namespace) -> dict[str, object]:
    direct, direct_task = load_path_result(arguments.direct_result)
    world, world_task = load_path_result(arguments.system_result)
    if direct_task != world_task:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "answer paths were not run from the same sealed task input",
        )
    pair = HoldoutTaskAnswerPair.create(
        direct=direct, world_assisted=world
    )
    path = save_answer_pair(
        pair,
        direct_result_path=arguments.direct_result,
        world_result_path=arguments.system_result,
        result_directory=arguments.result_directory,
    )
    return {
        "status": "SEALED",
        "task_id": pair.direct.task_id,
        "pair_digest": pair.digest.value,
        "pair_path": str(path),
        "independent_review_ready": True,
    }


def _seal_review(arguments: argparse.Namespace) -> dict[str, object]:
    suite = load_holdout_suite()
    pair = verify_answer_pair_document(arguments.pair)
    path = seal_independent_review_draft(
        arguments.review_draft,
        suite=suite,
        pair=pair,
        result_directory=arguments.result_directory,
    )
    review = load_independent_review(path, suite=suite, pair=pair)
    comparison = review.to_product_comparison()
    return {
        "status": "SEALED",
        "task_id": review.task_id,
        "review_path": str(path),
        "review_digest": review.digest.value,
        "comparison_digest": comparison.digest.value,
        "passed": review.passed,
        "production_activated": False,
    }


def _prepare_review(arguments: argparse.Namespace) -> dict[str, object]:
    suite = load_holdout_suite()
    pair = verify_answer_pair_document(arguments.pair)
    task = next(
        (
            item
            for item in suite["tasks"]
            if item["task_id"] == pair.direct.task_id
        ),
        None,
    )
    if (
        task is None
        or pair.direct.suite_digest.value != suite["suite_digest"]
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "answer pair does not belong to the sealed product suite",
        )
    template = {
        "schema": INDEPENDENT_REVIEW_DRAFT_SCHEMA,
        "suite_digest": suite["suite_digest"],
        "task_id": pair.direct.task_id,
        "pair_digest": pair.digest.value,
        "evaluator_identity": None,
        "evaluator_origin": None,
        "assessments": [
            {
                "dimension": dimension,
                "direct_status": None,
                "world_status": None,
                "finding": None,
            }
            for dimension in task["acceptance_dimensions"]
        ],
        "findings": [],
        "reviewed_at": None,
    }
    target = Path(arguments.result_directory) / (
        f"{pair.direct.task_id}--review-draft.json"
    )
    _write_same_or_new(target, template)
    return {
        "status": "REVIEW_TEMPLATE_PREPARED",
        "task_id": pair.direct.task_id,
        "review_draft_path": str(target),
        "judgement_recorded": False,
        "production_activated": False,
    }


def _qualification_dependencies(
    configuration: VolcengineArkModelConfiguration,
    conformance: object,
) -> EvaluationQualificationDependencies:
    """Bind qualification to the provider-observed model identity.

    The request alias and the identity returned by the service may differ.
    Capability evidence records the latter, so every downstream currentness
    check must use the same identity.
    """
    return EvaluationQualificationDependencies(
        strategy_implementation_digest=(
            evidence_first_task_strategy_implementation_digest()
        ),
        conformance_result_ref=conformance.result_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        model_ref=configuration.actual_model_fingerprint,
        adapter_version=configuration.adapter_version,
    )


def _record_acceptance(arguments: argparse.Namespace) -> dict[str, object]:
    suite = load_holdout_suite()
    verify_frozen_checkouts(suite, workspace_root=arguments.workspace_root)
    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        arguments.conformance_result, configuration
    )
    proof = load_qualification_proof(arguments.qualification_proof)
    dependencies = _qualification_dependencies(configuration, conformance)
    evidence_directory = Path(arguments.evidence_directory)
    comparisons = []
    reviews = []
    with SqliteDatabase(arguments.evaluation_database) as evaluation_database:
        verifier = CurrentEvaluationQualificationVerifier(
            SqliteCapabilityEvaluationRepository(evaluation_database), dependencies
        )
        if not verifier.validate(proof):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "capability evaluation proof is not current for product acceptance",
            )
        for task in suite["tasks"]:
            task_id = task["task_id"]
            pair = verify_answer_pair_document(
                evidence_directory / f"{task_id}--pair.json"
            )
            review = load_independent_review(
                evidence_directory / f"{task_id}--independent-review.json",
                suite=suite,
                pair=pair,
            )
            reviews.append(review)
            comparisons.append(review.to_product_comparison())
    if tuple(review.task_id for review in reviews) != tuple(
        task["task_id"] for task in suite["tasks"]
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "product acceptance evidence does not cover every sealed task",
        )
    with SqliteDatabase(arguments.authority_database) as authority_database:
        attestation = ProductValidationService(
            SqliteProductValidationRepository(authority_database)
        ).record_reviewed_holdout(
            idempotency_key=IdempotencyKey(
                f"product-acceptance:{suite['suite_digest']}:{proof.digest.value}"
            ),
            qualification=proof,
            strategy_implementation_digest=(
                evidence_first_task_strategy_implementation_digest()
            ),
            holdout_suite_ref=(
                f"{suite['suite_id']}@{suite['suite_version']}"
            ),
            holdout_suite_digest=Digest(suite["suite_digest"]),
            comparisons=tuple(comparisons),
            valid_for_seconds=arguments.valid_for_seconds,
        )
    return {
        "status": "PRODUCT_ACCEPTANCE_RECORDED",
        "attestation_id": attestation.attestation_id.value,
        "attestation_digest": attestation.digest.value,
        "case_count": len(attestation.case_ids),
        "valid_until": attestation.valid_until.isoformat(),
        "production_activated": False,
    }


def _export_qualification(arguments: argparse.Namespace) -> dict[str, object]:
    with SqliteDatabase(arguments.evaluation_database) as database:
        proof = SqliteCapabilityEvaluationRepository(
            database
        ).qualification_for_result(StableId(arguments.result_id))
    core = {
        "schema": QUALIFICATION_DOCUMENT_SCHEMA,
        "proof": {**proof.core(), "digest": proof.digest.value},
    }
    document = {**core, "document_digest": digest_of(core).value}
    path = Path(arguments.result_directory) / (
        f"qualification-{proof.result_ref.replace(':', '-')}.json"
    )
    _write_same_or_new(path, document)
    loaded = load_qualification_proof(path)
    if loaded != proof:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "exported capability qualification cannot be recovered",
        )
    return {
        "status": "EXPORTED",
        "proof_ref": proof.proof_ref,
        "qualification_digest": proof.digest.value,
        "qualification_path": str(path),
    }


def load_qualification_proof(path: str | Path) -> QualificationProof:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification proof cannot be read",
        ) from exc
    if (
        not isinstance(document, dict)
        or set(document) != {"schema", "proof", "document_digest"}
        or document.get("schema") != QUALIFICATION_DOCUMENT_SCHEMA
        or not isinstance(document.get("proof"), dict)
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification proof document is invalid",
        )
    core = {"schema": document["schema"], "proof": document["proof"]}
    if document["document_digest"] != digest_of(core).value:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification proof document digest is invalid",
        )
    raw = document["proof"]
    required = {
        "proof_ref",
        "capability_id",
        "capability_contract_version",
        "strategy_id",
        "strategy_version",
        "result_ref",
        "validity_ref",
        "qualification_kind",
        "digest",
    }
    if set(raw) != required:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification fields are incomplete",
        )
    try:
        proof = QualificationProof(
            proof_ref=raw["proof_ref"],
            capability_id=raw["capability_id"],
            capability_contract_version=raw["capability_contract_version"],
            strategy_id=raw["strategy_id"],
            strategy_version=raw["strategy_version"],
            result_ref=raw["result_ref"],
            validity_ref=raw["validity_ref"],
            qualification_kind=raw["qualification_kind"],
            digest=Digest(raw["digest"]),
        )
    except (TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification values are invalid",
        ) from exc
    if not proof.verify_digest():
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification digest is invalid",
        )
    return proof


def _write_same_or_new(path: Path, document: Mapping[str, object]) -> None:
    write_validation_document_once(path, document)


def _path_run_id(run_id: str, task_id: object, path: str) -> str:
    if not isinstance(run_id, str) or not run_id or run_id != run_id.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "run ID must be non-empty")
    return f"{run_id}:{task_id}:{path}"


def _result_payload(result, path: Path, suite: Mapping[str, object]):
    return {
        "status": "SEALED",
        "suite_id": suite["suite_id"],
        "task_id": result.task_id,
        "answer_path": result.path.value,
        "result_digest": result.digest.value,
        "result_path": str(path),
        "actual_model_fingerprint": result.actual_model_fingerprint,
        "model_call_count": result.model_call_count,
        "source_action_count": result.source_action_count,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "usage_complete": result.usage_complete,
        "production_activated": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
