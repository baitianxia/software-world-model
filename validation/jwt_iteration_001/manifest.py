"""Freeze the independent Direct Oracle and sanitized JWT run configuration.

This module is validation-only.  The SWM runtime receives the run
configuration, which contains only an opaque oracle reference and digest.  It
never receives the Direct Answer or claim contents stored in the oracle file.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Mapping
import uuid

from software_world_model.ai_infrastructure import (
    ArkChatConformanceQualification,
    VolcengineArkModelConfiguration,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


DIRECT_ORACLE_DRAFT_SCHEMA = "swm.jwt-direct-oracle-draft@2"
DIRECT_ORACLE_SCHEMA = "swm.jwt-direct-oracle@2"
JWT_RUN_CONFIGURATION_SCHEMA = "swm.jwt-capability-run-configuration@1"
QUESTION = "Commit dacce5f28dfc1734f2db09668d928d7fac2a3a7a 的 JWT 迁移影响了哪些技术区域？"
REPOSITORY_IDENTITY = "https://github.com/macrozheng/mall.git"
TARGET_COMMIT = "dacce5f28dfc1734f2db09668d928d7fac2a3a7a"
PARENT_COMMIT = "00bd03591cfd91f82ebe48787315eed613754277"
DIRECT_AGENT_PROMPT_REF = "direct-agent:jwt-impact@2"
DIRECT_AGENT_TOOL_POLICY_REF = "direct-local-git-read-only@1"
STRICT_JSON_OUTPUT_INSTRUCTION = (
    "Return exactly one JSON object matching the supplied strict schema. "
    "Populate every required field. Do not emit Markdown fences, explanatory prose, "
    "or reasoning outside the JSON object."
)
DIRECT_AGENT_PROMPT = f"""You are the independent Direct Agent for a frozen software-change evaluation.
{STRICT_JSON_OUTPUT_INSTRUCTION}
Investigate only the supplied repository boundary through observations explicitly included in this request.
Choose exactly one next action: RESOLVE, COMPARE, READ, SEARCH, or FINISH.
Every response must contain exactly these top-level fields: action, revision_role, path, query, start_line, end_line, rationale, answer, and claims.
Do not invent source content, library behavior, or runtime behavior. Preserve unknowns and modality. For verification/parsing failures, state only the source-proven branch conditions: verify=false returns null and an exception returns null; do not claim every invalid signature or format necessarily maps to a specific Hutool return or exception path.
When no observations exist, choose COMPARE first. COMPARE returns the bounded unified diff for the complete frozen change set. Use READ or SEARCH only when the diff leaves a specific required source question unresolved. READ is limited to a changed file, one revision role, and a bounded line range. SEARCH is literal and revision-bound.
After a complete COMPARE observation, FINISH next unless one specific source question truly requires READ or SEARCH. When FINISH, keep the answer concise and return at most one material claim per frozen Need (at most six claims total). Each claim may map all Obligation IDs for that Need, but its claim text must explicitly answer every mapped Obligation rather than relying on implication. State exact outcomes for counterexamples and both sides of equality or interval boundaries. Track returned expressions exactly: never call a derived, stripped, converted, or copied value the original value. Treat source comments only as comment-modality evidence, never as verified runtime behavior or as an old/new implementation attribution unless the diff proves that attribution. Do not expand a local diff into a repository-wide absence claim; qualify the observed scope or SEARCH first. Each claim must cite one or more supplied observation_ref values and must state source-only unknowns in limitation rather than expanding the investigation. For non-FINISH actions, answer must be empty and claims must be an empty array.
This Direct result is an external evaluation oracle. It must never be used as SWM runtime input."""
_FULL_OID = re.compile(r"^[0-9a-f]{40}$")


_NEEDS = (
    (
        "JWT-N01",
        "比较对象和完整变更范围是什么？",
        (
            ("DIRECT_SUPPORT", "exact target and unique parent"),
            ("ENUMERATION_COVERAGE", "complete changed-file set"),
        ),
    ),
    (
        "JWT-N02",
        "JWT依赖声明发生了什么变化？",
        (
            ("DIRECT_SUPPORT", "root JJWT version declaration change"),
            ("DIRECT_SUPPORT", "root dependency-management declaration change"),
            ("DIRECT_SUPPORT", "security-module direct dependency change"),
        ),
    ),
    (
        "JWT-N03",
        "令牌生成与exp表达发生了什么变化？",
        (
            ("DIRECT_SUPPORT", "token construction API change"),
            ("DIRECT_SUPPORT", "secret byte conversion"),
            (
                "DIRECT_SUPPORT",
                "exp is stored as a long epoch-millisecond value computed from currentTimeMillis plus expiration seconds times 1000",
            ),
        ),
    ),
    (
        "JWT-N04",
        "解析、验签、过期判断、校验和异常行为如何变化？",
        (
            ("DIRECT_SUPPORT", "signature verification and parsing order"),
            (
                "COUNTEREXAMPLE_CHECK",
                "verify=false returns null and verification/parsing exceptions return null; the mapping from every invalid signature or format to a Hutool return or exception path is not source-proven",
            ),
            (
                "COUNTEREXAMPLE_CHECK",
                "missing username makes getUserNameFromToken return null and validateToken return false because of the username != null guard",
            ),
            ("COUNTEREXAMPLE_CHECK", "missing expiration result"),
            (
                "COUNTEREXAMPLE_CHECK",
                "a non-Number exp conversion exception is caught by isTokenExpired and returns true",
            ),
            (
                "COUNTEREXAMPLE_CHECK",
                "exp equal to the sampled currentTimeMillis is not expired because the comparison is strict less-than",
            ),
        ),
    ),
    (
        "JWT-N05",
        "刷新行为如何变化？",
        (
            ("DIRECT_SUPPORT", "created accepted representations"),
            ("COUNTEREXAMPLE_CHECK", "unsupported created representation"),
            ("COUNTEREXAMPLE_CHECK", "refresh interval lower and upper boundaries"),
            (
                "DIRECT_SUPPORT",
                "within-window returns the tokenHead-stripped local token; outside-window returns a newly signed token",
            ),
        ),
    ),
    (
        "JWT-N06",
        "哪些结论不能仅由当前来源证明？",
        (
            ("UNKNOWN_OR_LIMITATION_DISCLOSURE", "new library default signing algorithm"),
            ("UNKNOWN_OR_LIMITATION_DISCLOSURE", "old library String-key semantics and comment modality"),
            ("UNKNOWN_OR_LIMITATION_DISCLOSURE", "payload serialization and parsed Java type"),
        ),
    ),
)


def _direct_requirement_view() -> list[dict[str, object]]:
    """Return the exact requirement payload supplied to every Direct call."""

    return [
        {
            "need_id": need_id,
            "question": question,
            "obligations": [
                {
                    "obligation_id": f"{need_id}-O{ordinal:02d}",
                    "role": role,
                    "dimension": dimension,
                }
                for ordinal, (role, dimension) in enumerate(dimensions, start=1)
            ],
        }
        for need_id, question, dimensions in _NEEDS
    ]


_ROLE_INPUTS = {
    "INVESTIGATION_PLANNER": (
        "BOUNDARY",
        "REQUIREMENT",
        "BUILD_TARGET",
        "SOURCE_OBSERVATION",
        "CONTRACT_REF",
    ),
    "FACT_PROPOSER": (
        "BOUNDARY",
        "REQUIREMENT",
        "BUILD_TARGET",
        "SOURCE_OBSERVATION",
        "FORMAL_KNOWLEDGE",
        "CONTRACT_REF",
    ),
    "KNOWLEDGE_REVIEWER": (
        "BOUNDARY",
        "REQUIREMENT",
        "BUILD_TARGET",
        "KNOWLEDGE_PROPOSAL",
        "SOURCE_OBSERVATION",
        "FORMAL_KNOWLEDGE",
        "CONTRACT_REF",
    ),
    "INFERENCE_PROPOSER": (
        "BOUNDARY",
        "REQUIREMENT",
        "FORMAL_KNOWLEDGE",
        "CONTRACT_REF",
    ),
    "SUFFICIENCY_REVIEWER": (
        "BOUNDARY",
        "REQUIREMENT",
        "FORMAL_KNOWLEDGE",
        "CONTRACT_REF",
    ),
    "ANSWER_GENERATOR": (
        "BOUNDARY",
        "REQUIREMENT",
        "ASSESSMENT",
        "FORMAL_KNOWLEDGE",
        "CONTRACT_REF",
    ),
    "ANSWER_REVIEWER": (
        "BOUNDARY",
        "REQUIREMENT",
        "ASSESSMENT",
        "ANSWER_CANDIDATE",
        "FORMAL_KNOWLEDGE",
        "CONTRACT_REF",
    ),
}


_PROMPTS = {
    "INVESTIGATION_PLANNER": f"{STRICT_JSON_OUTPUT_INSTRUCTION} Propose exactly one bounded Local Git source action or STOP. Use only supplied boundary, requirement, target, and prior observations. Do not answer the task. Treat DENIED observations only as correction feedback and never as successful source coverage. Follow this mandatory successful-action sequence: if RESOLVE is absent, choose RESOLVE; otherwise if COMPARE is absent, choose COMPARE; otherwise if the TARGET READ of mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java lines 150 through 203 is absent, choose exactly that READ; otherwise choose STOP unless one other specific frozen obligation requires a bounded READ or SEARCH. For RESOLVE and COMPARE set revision_role=NONE, path=\"\", query=\"\", start_line=0, end_line=0, and stop_reason=\"\". For the mandatory READ set revision_role=TARGET, the exact path above, query=\"\", start_line=150, end_line=203, and stop_reason=\"\". For STOP use empty source parameters and a non-empty stop_reason. Any other READ uses PARENT or TARGET, one changed path, query=\"\", and a 1-based inclusive range of at most 300 lines. SEARCH is literal and revision-bound. Never repeat an action that already has a successful observation.",
    "FACT_PROPOSER": f"{STRICT_JSON_OUTPUT_INSTRUCTION} Propose at most 10 concise atomic facts directly supported by the one supplied SOURCE_OBSERVATION and only for the supplied bounded REQUIREMENT scope. Treat each obligation.dimension as a literal acceptance criterion: a proposal may bind an obligation_id only when its statement explicitly answers that exact dimension, never merely a related migration fact. COUNTEREXAMPLE_CHECK facts must state the named input or boundary and exact resulting branch. UNKNOWN_OR_LIMITATION_DISCLOSURE facts must explicitly preserve what the source cannot prove and any comment-only modality; do not substitute the observed replacement implementation. Frozen clarification: JWT-N05 concerns tokenRefreshJustBefore and refreshHeadToken. When the scoped REQUIREMENT is JWT-N05 and the focused READ contains the branches, return exactly four proposals, one for each JWT-N05-O01 through O04. Machine-checkable wording is mandatory: N05-O01 statement contains created, Long, Date; N05-O02 contains created, other, null, false; N05-O03 contains refreshDate, after, createdDate, before, DateUtil.offsetSecond, lower, upper, exclusive; N05-O04 contains tokenHead, stripped, tokenRefreshJustBefore, generateToken. For JWT-N06 unknown disclosures, N06-O01 contains algorithm and unknown; N06-O02 contains String, comment, unknown; N06-O03 contains payload, type, unknown. N05-O01/O02 concern the CLAIM_KEY_CREATED payload value representation, not token construction APIs, libraries, or serialized token representations. A fact may otherwise bind multiple obligations only when its statement explicitly covers every one of them. Keep each statement, condition, and limitation compact. Copy target exactly from BUILD_TARGET.target_commit and set context exactly to PARENT_TO_TARGET. Each proposal must use a globally distinctive semantic_key derived from the supplied observation_ref and applicable need_id values; use only exact entity formal_ref values from the ENTITY snapshot; set source_observation_refs to an array containing exactly the current observation_ref; and use only the exact need_id and obligation_id values from the scoped REQUIREMENT. Every obligation_id must belong to one of the listed need_ids. State source modality, conditions, and limitations without importing library or runtime assumptions. If this observation supports no scoped obligation, return an empty proposals array and explain that in limitations.",
    "KNOWLEDGE_REVIEWER": f"{STRICT_JSON_OUTPUT_INSTRUCTION} Independently review only the supplied KNOWLEDGE_PROPOSAL against its supplied evidence or formal premises and REQUIREMENT. For every proposed obligation_id, compare the proposal statement with that obligation's role and dimension; a related fact is not coverage. COUNTEREXAMPLE_CHECK must include the exact named case and outcome or both strict boundaries. UNKNOWN_OR_LIMITATION_DISCLOSURE must state the unresolved behavior and preserve comment-only modality instead of replacing it with a known code change. Frozen clarification: JWT-N05-O01/O02 refer only to CLAIM_KEY_CREATED value types in tokenRefreshJustBefore (Long and Date accepted; every other representation leaves createdDate null and returns false), O03 is the refreshDate.after(createdDate) and refreshDate.before(DateUtil.offsetSecond(createdDate,time)) lower/upper exclusive interval, and O04 is the tokenHead-stripped token returned inside tokenRefreshJustBefore with generateToken used outside. Accept all four when the focused READ supports their exact machine-checkable statements. accepted_semantic_keys must be unique and copied exactly from proposed semantic_key values. ACCEPT requires at least one accepted key; REJECT requires an empty accepted_semantic_keys array. Accept only proposals whose statement, modality, target, PARENT_TO_TARGET context, references, need IDs, obligation IDs, conditions, and limitations are fully supported; reject expanded, ambiguous, hidden-premise, or incorrectly bound semantics. When reviewing source facts, use only the supplied SOURCE_OBSERVATION; when reviewing inferences, use only the supplied FORMAL_KNOWLEDGE premises.",
    "INFERENCE_PROPOSER": f"{STRICT_JSON_OUTPUT_INSTRUCTION} Propose only bounded inferences entailed by supplied same-snapshot FORMAL_KNOWLEDGE. Never use source text, artifacts, hidden memory, library behavior, or model knowledge as a premise. Set target exactly to the BOUNDARY target_commit and context exactly to PARENT_TO_TARGET. Use a new semantic_key distinct from every supplied member key; premise_refs must be a non-empty array containing only exact supplied formal_ref values. Use only exact REQUIREMENT need_id and obligation_id values, and every obligation_id must belong to one of the listed need_ids. Return an empty proposals array when no sound new inference exists.",
    "SUFFICIENCY_REVIEWER": f"{STRICT_JSON_OUTPUT_INSTRUCTION} Return exactly one assessment entry for every REQUIREMENT obligation_id and exactly one for every joint constraint_id, with no duplicates or extras. An obligation_id carried by a formal member is only a proposed binding: mark SATISFIED only when the cited statement actually entails that obligation's role and dimension. Related code changes do not satisfy a different criterion. COUNTEREXAMPLE_CHECK requires the named case and exact result or both boundaries; UNKNOWN_OR_LIMITATION_DISCLOSURE requires an explicit unknown and preserved source/comment modality. Use only exact formal_ref values from the supplied same-snapshot FORMAL_KNOWLEDGE. SATISFIED requires a non-empty unique supporting_refs array, and each cited formal member must carry that obligation_id; every other status requires an empty supporting_refs array. A joint constraint is SATISFIED only with non-empty formal support. Findings must be non-empty and must preserve unknowns and limitations. Set overall to SATISFIED only when every obligation and joint constraint is SATISFIED; otherwise set it to INSUFFICIENT.",
    "ANSWER_GENERATOR": f"{STRICT_JSON_OUTPUT_INSTRUCTION} Produce non-empty claims that cover every frozen obligation_id exactly once, with no extras. Each claim text must explicitly answer every mapped obligation.role and obligation.dimension; do not substitute a related implementation change. COUNTEREXAMPLE_CHECK text must state the named input/boundary and exact result, and UNKNOWN_OR_LIMITATION_DISCLOSURE text must state what remains source-unproven, including comment modality where required. Frozen clarification: JWT-N05-O01/O02 mean CLAIM_KEY_CREATED payload value representations in tokenRefreshJustBefore—Long/Date accepted; any other type leaves createdDate null and returns false—not token construction or JWT-library representation. Machine-checkable wording is mandatory: N05-O01 claim text contains created, Long, Date; N05-O02 contains created, other, null, false; N05-O03 contains refreshDate, after, createdDate, before, DateUtil.offsetSecond, lower, upper, exclusive; N05-O04 contains tokenHead, stripped, tokenRefreshJustBefore, generateToken. N06-O01 contains algorithm and unknown; N06-O02 contains String, comment, unknown; N06-O03 contains payload, type, unknown. Copy target exactly from BOUNDARY.target_commit and set context exactly to PARENT_TO_TARGET; use only exact REQUIREMENT need_ids and matching obligation_ids. A FORMAL_KNOWLEDGE claim may cover only SATISFIED obligations and its unique supporting_refs must equal the exact union of those obligations' assessment supporting_refs. A KNOWLEDGE_GAP claim may cover only non-SATISFIED obligations and must have an empty supporting_refs array. Do not combine satisfied and non-satisfied obligations in one claim. Preserve modality, conditions, limitations, and unknowns. Set answer to exactly the claim text values joined in claim order with a single newline and no other text. List the disclosed non-satisfied areas in gaps.",
    "ANSWER_REVIEWER": f"{STRICT_JSON_OUTPUT_INSTRUCTION} Independently review every supplied candidate claim exactly once. Compare each claim text with every mapped obligation.role and obligation.dimension; related behavior is not coverage. Require exact named counterexample outcomes and both interval boundaries, and require unknown-disclosure claims to retain every unresolved behavior and comment-only modality. claim_findings must contain one unique entry for every candidate semantic_key and no extras. Verify exact obligation coverage, target, PARENT_TO_TARGET context, modality, support equality with ASSESSMENT, gaps, and absence of hidden source or stronger claims. A PASS finding must not describe missing, subset, contradictory, or non-exact support. Accurate KNOWLEDGE_GAP claims that match a non-SATISFIED assessment are valid coverage and may be APPROVED; do not require revision merely because the assessment contains a gap. missing_obligation_ids must contain only exact frozen obligations omitted by the candidate. APPROVED requires an empty missing_obligation_ids array and PASS for every claim; otherwise use REVISION_REQUIRED or REJECTED and mark each faulty claim FAIL with a concrete finding.",
}


_CRITICAL_WORLD_SEMANTICS = (
    "Frozen exact semantics: JWT-N01-O01 covers only the exact target and unique parent; "
    "JWT-N01-O02 must itself enumerate the complete paths pom.xml, mall-security/pom.xml, and "
    "mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java rather than only naming technical areas. "
    "JWT-N04-O01 must say verify is evaluated first; "
    "verify=false returns null before parsing; verify=true proceeds to a parse attempt; "
    "and an exception during verification or parsing is caught and returns null. "
    "Never say that a parsing exception causes parsing to be skipped, because parsing was attempted. "
    "JWT-N04-O02 must express two disjoint source-proven branches: verify returns false and returns null; "
    "or an exception is thrown during verify or parse and is caught and returns null. Never condition an exception during verification on verify=true. "
    "JWT-N06-O01 must distinguish the old code's explicit SignatureAlgorithm.HS512 call and the HMACSHA512 comment "
    "from the unknown new Hutool JWTUtil.createToken default algorithm; neither proves the new algorithm. "
    "JWT-N06-O02 must preserve that the source contains an HMACSHA512 comment, treat it only as "
    "comment-modality evidence, and state that the old JJWT String-key semantics remain unproven; "
    "never attribute the comment to Hutool runtime behavior. "
    "JWT-N06-O03 must distinguish the visible getPayloads return declaration Map<String,Object> from the unknown "
    "concrete runtime payload value types and serialization; do not reduce this unknown to equivalence with old Claims."
)
_CRITICAL_WORLD_ROLES = {
    "FACT_PROPOSER",
    "KNOWLEDGE_REVIEWER",
    "SUFFICIENCY_REVIEWER",
    "ANSWER_GENERATOR",
    "ANSWER_REVIEWER",
}


def _prompt_for_role(role: str) -> str:
    prompt = _PROMPTS[role]
    return (
        f"{prompt} {_CRITICAL_WORLD_SEMANTICS}"
        if role in _CRITICAL_WORLD_ROLES
        else prompt
    )


_OUTPUT_SCHEMA_SHAPES = {
    "INVESTIGATION_PLANNER": ("action", "parameters", "rationale", "stop_reason"),
    "FACT_PROPOSER": ("proposals", "limitations"),
    "KNOWLEDGE_REVIEWER": ("decision", "accepted_semantic_keys", "findings"),
    "INFERENCE_PROPOSER": ("proposals", "limitations"),
    "SUFFICIENCY_REVIEWER": ("obligations", "joint_constraints", "overall"),
    "ANSWER_GENERATOR": ("claims", "answer", "gaps"),
    "ANSWER_REVIEWER": ("decision", "claim_findings", "missing_obligation_ids"),
}


_ROLE_MAX_OUTPUT_TOKENS = {
    role: (
        8192
        if role
        in {
            "FACT_PROPOSER",
            "INFERENCE_PROPOSER",
            "SUFFICIENCY_REVIEWER",
            "ANSWER_GENERATOR",
            "ANSWER_REVIEWER",
        }
        else 4096
    )
    for role in _ROLE_INPUTS
}


def seal_direct_oracle(
    *,
    draft_path: str | Path,
    result_directory: str | Path,
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
    operator: str,
    reviewer: str,
    now: datetime | None = None,
) -> Path:
    """Validate a separately produced/reviewed Direct Oracle and seal it."""

    _identity(operator, "oracle operator")
    _identity(reviewer, "independent oracle reviewer")
    if operator == reviewer:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Direct Oracle operator and independent reviewer must differ",
        )
    try:
        draft = json.loads(Path(draft_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Oracle draft cannot be read") from exc
    if not isinstance(draft, dict):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Oracle draft must be an object")
    _validate_oracle_draft(draft, qualification, configuration)
    sealed_at = _utc(now or datetime.now(timezone.utc))
    if (
        sealed_at >= qualification.valid_until
        or qualification.adapter_version != configuration.adapter_version
        or qualification.provider_configuration_fingerprint != configuration.fingerprint
        or qualification.qualified_model_fingerprints
        != configuration.qualified_model_identities
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Direct Oracle cannot use stale or mismatched adapter conformance",
        )
    oracle_id = f"oracle_{uuid.uuid4().hex}"
    core = {
        "schema": DIRECT_ORACLE_SCHEMA,
        "oracle_id": oracle_id,
        "question": QUESTION,
        "repository_identity": REPOSITORY_IDENTITY,
        "target_commit": TARGET_COMMIT,
        "parent_commit": PARENT_COMMIT,
        "operator": operator,
        "independent_reviewer": reviewer,
        "sealed_at": _time(sealed_at),
        "conformance_result_ref": qualification.result_ref,
        "model_ref": configuration.model_ref,
        "adapter_version": configuration.adapter_version,
        "provider_configuration_fingerprint": configuration.fingerprint.value,
        "direct_run": draft,
        "separation_policy": {
            "available_to_swm_runtime": False,
            "comparison_allowed_after_delivery": True,
            "oracle_directory_must_differ_from_runtime_directory": True,
        },
    }
    document = {**core, "oracle_digest": digest_of(core).value}
    return _seal(document, result_directory, f"JWT-DIRECT-ORACLE-{oracle_id}.json")


def verify_direct_oracle(
    document: Mapping[str, object],
    *,
    qualification: ArkChatConformanceQualification | None = None,
    configuration: VolcengineArkModelConfiguration | None = None,
) -> None:
    expected = {
        "schema",
        "oracle_id",
        "question",
        "repository_identity",
        "target_commit",
        "parent_commit",
        "operator",
        "independent_reviewer",
        "sealed_at",
        "conformance_result_ref",
        "model_ref",
        "adapter_version",
        "provider_configuration_fingerprint",
        "direct_run",
        "separation_policy",
        "oracle_digest",
    }
    if set(document) != expected or document.get("schema") != DIRECT_ORACLE_SCHEMA:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Direct Oracle shape is invalid")
    if (
        document.get("question") != QUESTION
        or document.get("repository_identity") != REPOSITORY_IDENTITY
        or document.get("target_commit") != TARGET_COMMIT
        or document.get("parent_commit") != PARENT_COMMIT
        or document.get("operator") == document.get("independent_reviewer")
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Direct Oracle boundary is invalid")
    supplied = _digest_value(document.get("oracle_digest"), "Direct Oracle digest")
    core = {key: value for key, value in document.items() if key != "oracle_digest"}
    if digest_of(core) != supplied:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Direct Oracle digest does not verify")
    direct_run = document.get("direct_run")
    if not isinstance(direct_run, dict):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Direct Oracle run is missing")
    if qualification is not None and configuration is not None:
        _validate_oracle_draft(direct_run, qualification, configuration)
        if (
            document.get("conformance_result_ref") != qualification.result_ref
            or document.get("model_ref") != configuration.model_ref
            or document.get("adapter_version") != configuration.adapter_version
            or document.get("provider_configuration_fingerprint")
            != configuration.fingerprint.value
        ):
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Direct Oracle provider evidence is stale")


def freeze_jwt_run_configuration(
    *,
    oracle_path: str | Path,
    repository_path: str | Path,
    result_directory: str | Path,
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
    operator: str,
    runtime_directory: str | Path,
    now: datetime | None = None,
) -> Path:
    """Freeze the sanitized configuration consumed by the future SWM run."""

    _identity(operator, "run configuration operator")
    oracle_file = Path(oracle_path).resolve()
    runtime = Path(runtime_directory).resolve()
    if _overlaps(oracle_file.parent, runtime):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "oracle and SWM runtime directories must be physically separate",
        )
    try:
        oracle = json.loads(oracle_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "sealed Direct Oracle cannot be read") from exc
    if not isinstance(oracle, dict):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "sealed Direct Oracle must be an object")
    verify_direct_oracle(
        oracle, qualification=qualification, configuration=configuration
    )
    source = _verify_repository(repository_path)
    created_at = _utc(now or datetime.now(timezone.utc))
    requirement = _requirement_manifest()
    roles = _role_manifest()
    harness = _harness_manifest()
    run_configuration_id = f"jwtrun_{uuid.uuid4().hex}"
    core = {
        "schema": JWT_RUN_CONFIGURATION_SCHEMA,
        "run_configuration_id": run_configuration_id,
        "version": "1.0.0",
        "created_at": _time(created_at),
        "operator": operator,
        "question": QUESTION,
        "source": source,
        "requirement": requirement,
        "adapter": {
            "provider_type": configuration.provider_type,
            "adapter_version": configuration.adapter_version,
            "configuration_fingerprint": configuration.fingerprint.value,
            "conformance_result_ref": qualification.result_ref,
            "conformance_valid_until": _time(qualification.valid_until),
            "requested_model_ref": configuration.model_ref,
            "qualified_model_fingerprints": qualification.qualified_model_fingerprints,
            "runtime_access_mode": "NO_EXTERNAL_ACCESS",
        },
        "roles": roles,
        "budget": {
            "max_tool_steps": 40,
            "max_files_read": 16,
            "max_source_bytes": 1_000_000,
            "max_model_calls": 80,
            "max_duration_milliseconds": 1_800_000,
            "max_result_bytes": 10_000_000,
            "cost_policy_ref": "actual-usage-recorded-price-not-configured@1",
        },
        "oracle": {
            "oracle_ref": oracle.get("oracle_id"),
            "oracle_digest": oracle.get("oracle_digest"),
            "oracle_content_available_to_runtime": False,
            "comparison_stage": "AFTER_AUTHORIZED_DELIVERY",
        },
        "isolation": {
            "runtime_directory_digest": _raw_digest(str(runtime).encode()).value,
            "runtime_directory_persisted": False,
            "oracle_directory_digest": _raw_digest(str(oracle_file.parent).encode()).value,
            "source_allowed_roles": ["INVESTIGATION_PLANNER", "FACT_PROPOSER", "KNOWLEDGE_REVIEWER"],
            "source_closed_roles": [
                "INFERENCE_PROPOSER",
                "SUFFICIENCY_REVIEWER",
                "ANSWER_GENERATOR",
                "ANSWER_REVIEWER",
            ],
            "production_namespace_writable": False,
            "evaluation_sink_only": True,
        },
        "harness": harness,
    }
    document = {**core, "configuration_digest": digest_of(core).value}
    verify_jwt_run_configuration(document, qualification, configuration)
    return _seal(
        document,
        result_directory,
        f"JWT-RUN-CONFIG-{run_configuration_id}.json",
    )


def verify_jwt_run_configuration(
    document: Mapping[str, object],
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
    *,
    at: datetime | None = None,
    require_current_harness: bool = True,
) -> None:
    expected = {
        "schema",
        "run_configuration_id",
        "version",
        "created_at",
        "operator",
        "question",
        "source",
        "requirement",
        "adapter",
        "roles",
        "budget",
        "oracle",
        "isolation",
        "harness",
        "configuration_digest",
    }
    if set(document) != expected or document.get("schema") != JWT_RUN_CONFIGURATION_SCHEMA:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT run configuration shape is invalid")
    supplied = _digest_value(document.get("configuration_digest"), "run configuration digest")
    core = {key: value for key, value in document.items() if key != "configuration_digest"}
    if digest_of(core) != supplied:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT run configuration digest does not verify")
    source = document.get("source")
    adapter = document.get("adapter")
    oracle = document.get("oracle")
    isolation = document.get("isolation")
    if not all(isinstance(item, dict) for item in (source, adapter, oracle, isolation)):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT run dependencies are missing")
    if (
        source.get("repository_identity") != REPOSITORY_IDENTITY
        or source.get("target_commit") != TARGET_COMMIT
        or source.get("parent_commit") != PARENT_COMMIT
        or adapter.get("conformance_result_ref") != qualification.result_ref
        or adapter.get("configuration_fingerprint") != configuration.fingerprint.value
        or adapter.get("requested_model_ref") != configuration.model_ref
        or adapter.get("adapter_version") != configuration.adapter_version
        or oracle.get("oracle_content_available_to_runtime") is not False
        or isolation.get("production_namespace_writable") is not False
        or isolation.get("evaluation_sink_only") is not True
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT run dependency is stale or unsafe")
    current = _utc(at or datetime.now(timezone.utc))
    if current >= qualification.valid_until:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT run uses expired adapter conformance")
    roles = document.get("roles")
    if not isinstance(roles, list) or digest_of(roles) != digest_of(_role_manifest()):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT seven-role matrix is incomplete")
    if document.get("requirement") != _requirement_manifest():
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT requirement manifest is stale")
    harness = document.get("harness")
    if not isinstance(harness, dict) or not _frozen_harness_verifies(harness):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT frozen harness is invalid")
    if require_current_harness and harness != _harness_manifest():
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT harness implementation is stale")
    budget = document.get("budget")
    expected_budget_fields = {
        "max_tool_steps",
        "max_files_read",
        "max_source_bytes",
        "max_model_calls",
        "max_duration_milliseconds",
        "max_result_bytes",
        "cost_policy_ref",
    }
    if (
        not isinstance(budget, dict)
        or set(budget) != expected_budget_fields
        or any(
            isinstance(budget.get(field), bool)
            or not isinstance(budget.get(field), int)
            or budget.get(field) < 1
            for field in expected_budget_fields - {"cost_policy_ref"}
        )
        or budget.get("cost_policy_ref")
        != "actual-usage-recorded-price-not-configured@1"
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT run budget is invalid")


def _frozen_harness_verifies(harness: Mapping[str, object]) -> bool:
    if set(harness) != {"files", "aggregate_digest"}:
        return False
    files = harness.get("files")
    if not isinstance(files, list) or not files:
        return False
    paths = set()
    for item in files:
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "digest"}
            or not isinstance(item.get("path"), str)
            or not item["path"]
            or item["path"] in paths
        ):
            return False
        try:
            Digest(str(item.get("digest")))
        except ValueError:
            return False
        paths.add(item["path"])
    return harness.get("aggregate_digest") == digest_of(files).value
    if (
        adapter.get("qualified_model_fingerprints")
        != list(qualification.qualified_model_fingerprints)
        and adapter.get("qualified_model_fingerprints")
        != qualification.qualified_model_fingerprints
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT qualified model set is stale")
    if adapter.get("runtime_access_mode") != "NO_EXTERNAL_ACCESS":
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT runtime access mode is unsafe")
    if (
        isolation.get("source_allowed_roles")
        != ["INVESTIGATION_PLANNER", "FACT_PROPOSER", "KNOWLEDGE_REVIEWER"]
        or isolation.get("source_closed_roles")
        != [
            "INFERENCE_PROPOSER",
            "SUFFICIENCY_REVIEWER",
            "ANSWER_GENERATOR",
            "ANSWER_REVIEWER",
        ]
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT role isolation matrix is stale")
    oracle_ref = oracle.get("oracle_ref")
    try:
        _digest_value(oracle.get("oracle_digest"), "JWT oracle digest")
    except DomainError as exc:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, exc.message) from exc
    if not isinstance(oracle_ref, str) or not re.fullmatch(r"oracle_[0-9a-f]{32}", oracle_ref):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "JWT oracle reference is invalid")


def _validate_oracle_draft(
    draft: Mapping[str, object],
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
) -> None:
    expected = {
        "schema",
        "question",
        "repository_identity",
        "target_commit",
        "parent_commit",
        "model_ref",
        "adapter_version",
        "conformance_result_ref",
        "prompt_ref",
        "prompt",
        "prompt_digest",
        "tool_policy_ref",
        "requirement",
        "requirement_digest",
        "budget",
        "started_at",
        "completed_at",
        "actual_model_fingerprints",
        "provider_request_ids",
        "output_normalizations",
        "usage",
        "trace",
        "observations",
        "direct_answer",
        "claims",
    }
    if set(draft) != expected or draft.get("schema") != DIRECT_ORACLE_DRAFT_SCHEMA:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Oracle draft shape is invalid")
    if (
        draft.get("question") != QUESTION
        or draft.get("repository_identity") != REPOSITORY_IDENTITY
        or draft.get("target_commit") != TARGET_COMMIT
        or draft.get("parent_commit") != PARENT_COMMIT
        or draft.get("model_ref") != configuration.model_ref
        or draft.get("adapter_version") != configuration.adapter_version
        or draft.get("conformance_result_ref") != qualification.result_ref
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Direct Oracle draft boundary is stale")
    prompt = draft.get("prompt")
    if (
        prompt != DIRECT_AGENT_PROMPT
        or draft.get("prompt_ref") != DIRECT_AGENT_PROMPT_REF
        or draft.get("tool_policy_ref") != DIRECT_AGENT_TOOL_POLICY_REF
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Direct Agent prompt or tool policy is stale")
    if digest_of(prompt) != _digest_value(
        draft.get("prompt_digest"), "Direct Agent prompt digest"
    ):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent prompt digest does not verify")
    requirement = draft.get("requirement")
    expected_requirement = _direct_requirement_view()
    if (
        requirement != expected_requirement
        or digest_of(requirement)
        != _digest_value(
            draft.get("requirement_digest"),
            "Direct Agent requirement digest",
        )
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Direct Agent requirement binding is stale",
        )
    answer = draft.get("direct_answer")
    if not isinstance(answer, str) or not answer.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Answer is empty")
    request_ids = draft.get("provider_request_ids")
    if (
        not isinstance(request_ids, list)
        or not request_ids
        or len(set(request_ids)) != len(request_ids)
        or any(not isinstance(item, str) or not item for item in request_ids)
    ):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent request IDs are incomplete")
    output_normalizations = draft.get("output_normalizations")
    if (
        not isinstance(output_normalizations, list)
        or len(output_normalizations) != len(request_ids)
        or any(
            item
            not in {
                "IDENTITY",
                "MARKDOWN_JSON_FENCE_V1",
                "MARKDOWN_JSON_FENCE_WITH_PREFIX_V1",
            }
            for item in output_normalizations
        )
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Direct Agent output-normalization evidence is invalid",
        )
    if draft.get("actual_model_fingerprints") != [
        configuration.actual_model_fingerprint
    ]:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Direct Agent actual model identity is invalid")
    try:
        started = datetime.fromisoformat(str(draft.get("started_at")).replace("Z", "+00:00"))
        completed = datetime.fromisoformat(str(draft.get("completed_at")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent run time is invalid") from exc
    if (
        started.tzinfo is None
        or completed.tzinfo is None
        or completed < started
        or completed >= qualification.valid_until
    ):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent run time is invalid")
    _verify_qualification(qualification, configuration, at=started)
    usage = draft.get("usage")
    if (
        not isinstance(usage, dict)
        or set(usage) != {"input_tokens", "output_tokens", "complete"}
        or usage.get("complete") is not True
        or any(
            isinstance(usage.get(key), bool)
            or not isinstance(usage.get(key), int)
            or usage.get(key) < 0
            for key in ("input_tokens", "output_tokens")
        )
    ):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent usage must be complete")
    budget = draft.get("budget")
    allowed_budget_fields = {
        "max_tool_steps",
        "max_files_read",
        "max_source_bytes",
        "max_model_calls",
        "timeout_milliseconds",
        "max_output_tokens",
    }
    if (
        not isinstance(budget, dict)
        or set(budget) != allowed_budget_fields
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 1
            for value in budget.values()
        )
        or len(request_ids) > budget["max_model_calls"]
    ):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent budget is invalid")
    trace = draft.get("trace")
    if not isinstance(trace, list) or not trace:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent trace is empty")
    allowed_tools = {"RESOLVE", "COMPARE", "SEARCH", "READ", "DENIED"}
    allowed_request_actions = {
        "RESOLVE",
        "COMPARE",
        "SEARCH",
        "READ",
        "FINISH",
        "INVALID_OUTPUT",
    }
    observations = draft.get("observations")
    if not isinstance(observations, list) or len(observations) != len(trace):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent observations are incomplete")
    observation_by_ref = {}
    for observation in observations:
        if not isinstance(observation, dict) or set(observation) != {
            "observation_ref",
            "tool",
            "locator",
            "content",
            "content_digest",
        }:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent observation is invalid")
        reference = observation.get("observation_ref")
        content = observation.get("content")
        if (
            not isinstance(reference, str)
            or not reference
            or reference in observation_by_ref
            or not isinstance(content, str)
            or _raw_digest(content.encode("utf-8"))
            != _digest_value(observation.get("content_digest"), "observation digest")
        ):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent observation digest is invalid")
        observation_by_ref[reference] = observation
    trace_observation_refs = set()
    for ordinal, item in enumerate(trace):
        if not isinstance(item, dict) or set(item) != {
            "ordinal",
            "tool",
            "request",
            "request_digest",
            "observation_ref",
            "result_digest",
        }:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent trace item is invalid")
        if item.get("ordinal") != ordinal or item.get("tool") not in allowed_tools:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent trace order or tool is invalid")
        if not isinstance(item.get("request"), dict) or digest_of(item["request"]) != _digest_value(
            item.get("request_digest"), "trace request digest"
        ):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent trace request digest is invalid")
        observation = observation_by_ref.get(item.get("observation_ref"))
        expected_observation_ref = (
            f"direct-observation:{ordinal:03d}:{item.get('result_digest')}"
        )
        if (
            observation is None
            or item.get("observation_ref") != expected_observation_ref
            or item.get("observation_ref") in trace_observation_refs
            or observation.get("tool") != item.get("tool")
            or observation.get("content_digest") != item.get("result_digest")
        ):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent trace observation is invalid")
        request_action = item["request"].get("action")
        if (
            (item.get("tool") == "DENIED" and request_action not in allowed_request_actions)
            or (item.get("tool") != "DENIED" and item.get("tool") != request_action)
            or (
                item.get("tool") == "DENIED"
                and not str(observation.get("locator", "")).startswith(
                    "direct-tool-denial:sha256:"
                )
            )
        ):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent tool outcome is invalid")
        trace_observation_refs.add(item.get("observation_ref"))
        _digest_value(item.get("result_digest"), "trace result digest")
    if trace_observation_refs != set(observation_by_ref):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent contains unreferenced observations")
    if len(trace) > budget["max_tool_steps"]:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent trace exceeds its budget")
    if len(request_ids) != len(trace) + 1:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent call and trace counts disagree")
    observed_source_bytes = sum(
        len(str(observation["content"]).encode("utf-8")) for observation in observations
    )
    files_read = {
        (str(item["request"].get("revision_role")), str(item["request"].get("path")))
        for item in trace
        if item.get("tool") == "READ"
    }
    if (
        observed_source_bytes > budget["max_source_bytes"]
        or len(files_read) > budget["max_files_read"]
    ):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent source usage exceeds its budget")
    claims = draft.get("claims")
    if not isinstance(claims, list) or not claims:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Claim Oracle is empty")
    semantic_keys = set()
    known_obligations = {
        f"{need_id}-O{ordinal:02d}"
        for need_id, _, dimensions in _NEEDS
        for ordinal in range(1, len(dimensions) + 1)
    }
    known_needs = {item[0] for item in _NEEDS}
    for claim in claims:
        expected_claim = {
            "semantic_key",
            "claim",
            "target",
            "context",
            "modality",
            "condition",
            "limitation",
            "coverage",
            "source_locators",
            "source_digests",
            "need_ids",
            "obligation_ids",
            "material",
        }
        if not isinstance(claim, dict) or set(claim) != expected_claim:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Claim shape is invalid")
        key = claim.get("semantic_key")
        textual_fields = ("semantic_key", "claim", "target", "context", "modality", "coverage")
        if (
            any(not isinstance(claim.get(field), str) or not claim[field].strip() for field in textual_fields)
            or not isinstance(key, str)
            or key in semantic_keys
        ):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Claim semantic key is invalid")
        semantic_keys.add(key)
        if claim.get("material") is not True:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "non-material claims must not enter the gate oracle")
        obligations = claim.get("obligation_ids")
        if not isinstance(obligations, list) or not obligations or not set(obligations).issubset(known_obligations):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Claim obligation mapping is invalid")
        needs = claim.get("need_ids")
        if not isinstance(needs, list) or not needs or not set(needs).issubset(known_needs):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Claim Need mapping is invalid")
        if any(not obligation.startswith(tuple(f"{need_id}-" for need_id in needs)) for obligation in obligations):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Claim Need and obligation mappings disagree")
        locators = claim.get("source_locators")
        digests = claim.get("source_digests")
        if not isinstance(locators, list) or not locators or not isinstance(digests, list) or len(locators) != len(digests):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Claim source support is incomplete")
        available_support = {
            (observation["locator"], observation["content_digest"])
            for observation in observations
        }
        if any(pair not in available_support for pair in zip(locators, digests)):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Claim cites unavailable support")
        for value in digests:
            _digest_value(value, "Direct Claim source digest")


def _requirement_manifest() -> dict[str, object]:
    needs = []
    for need_ordinal, (need_id, question, dimensions) in enumerate(_NEEDS):
        obligations = [
            {
                "obligation_id": f"{need_id}-O{ordinal:02d}",
                "ordinal": ordinal - 1,
                "role": role,
                "dimension": dimension,
            }
            for ordinal, (role, dimension) in enumerate(dimensions, start=1)
        ]
        needs.append(
            {
                "need_id": need_id,
                "ordinal": need_ordinal,
                "question": question,
                "sufficiency_criterion": "Every registered obligation must have exact same-snapshot formal support or an explicit gap/unknown outcome.",
                "required": True,
                "obligations": obligations,
            }
        )
    core = {
        "requirement_id": "jwt-requirement-002-runtime-001",
        "revision": 1,
        "needs": needs,
        "joint_constraints": [
            {
                "constraint_id": "JWT-J01",
                "need_ids": [item[0] for item in _NEEDS],
                "criterion": "All support uses the same repository, target, parent, and comparison context.",
            }
        ],
    }
    return {**core, "requirement_digest": digest_of(core).value}


def _verify_qualification(
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
    *,
    at: datetime,
) -> None:
    current = _utc(at)
    if (
        current >= qualification.valid_until
        or qualification.adapter_version != configuration.adapter_version
        or qualification.provider_configuration_fingerprint != configuration.fingerprint
        or qualification.qualified_model_fingerprints
        != configuration.qualified_model_identities
        or not qualification.result_ref.startswith("CC-ARK-CHAT-NO-TOOLS-001:sha256:")
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "validation run uses stale or mismatched adapter conformance",
        )


def _role_manifest() -> list[dict[str, object]]:
    roles = []
    for role, inputs in _ROLE_INPUTS.items():
        prompt = _prompt_for_role(role)
        schema_core = {
            "schema_ref": f"jwt-{role.lower().replace('_', '-')}@1",
            "closed_fields": _OUTPUT_SCHEMA_SHAPES[role],
            "additional_properties": False,
        }
        roles.append(
            {
                "role": role,
                "allowed_input_kinds": inputs,
                "prompt_ref": f"prompt:jwt-{role.lower().replace('_', '-')}@1",
                "prompt_digest": digest_of(prompt).value,
                "output_contract": {**schema_core, "schema_digest": digest_of(schema_core).value},
                "provider_tools": [],
                "store": False,
                "stream": False,
                "max_output_tokens": _ROLE_MAX_OUTPUT_TOKENS[role],
                "independent_call_required": role in {"KNOWLEDGE_REVIEWER", "ANSWER_REVIEWER"},
            }
        )
    return roles


def _verify_repository(repository_path: str | Path) -> dict[str, object]:
    path = Path(repository_path).resolve()
    origin = _git(path, "config", "--get", "remote.origin.url")
    identity = origin.removesuffix("/")
    if identity.endswith(".git"):
        identity += ""
    if identity != REPOSITORY_IDENTITY:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "validation repository identity is wrong")
    if not _FULL_OID.fullmatch(TARGET_COMMIT) or not _FULL_OID.fullmatch(PARENT_COMMIT):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "validation object IDs are invalid")
    parents = _git(path, "rev-list", "--parents", "-n", "1", TARGET_COMMIT).split()
    if parents != [TARGET_COMMIT, PARENT_COMMIT]:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "validation target does not have the frozen unique parent")
    object_type = _git(path, "cat-file", "-t", TARGET_COMMIT)
    if object_type != "commit":
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "validation target is not a commit")
    return {
        "provider": "LOCAL_GIT",
        "repository_identity": identity,
        "target_commit": TARGET_COMMIT,
        "parent_commit": PARENT_COMMIT,
        "comparison_context": "PARENT_TO_TARGET",
        "local_repository_path_persisted": False,
    }


def _harness_manifest() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    relative_files = (
        "validation/jwt_iteration_001/manifest.py",
        "validation/jwt_iteration_001/direct_agent.py",
        "validation/jwt_iteration_001/world_model.py",
        "validation/jwt_iteration_001/comparison.py",
        "validation/jwt_iteration_001/evaluation_bridge.py",
        "validation/jwt_iteration_001/cli.py",
        "src/software_world_model/application_services/evaluation.py",
        "src/software_world_model/infrastructure/sqlite_evaluation_repository.py",
        "src/software_world_model/ai_infrastructure/ark_chat_conformance.py",
        "src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py",
    )
    files = []
    for relative in relative_files:
        payload = (root / relative).read_bytes()
        files.append({"path": relative, "digest": _raw_digest(payload).value})
    return {"files": files, "aggregate_digest": digest_of(files).value}


def _seal(document: Mapping[str, object], directory: str | Path, name: str) -> Path:
    target_directory = Path(directory)
    target_directory.mkdir(parents=True, exist_ok=True)
    path = target_directory / name
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "validation evidence path already exists and cannot be overwritten",
        ) from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def _git(path: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(path), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "validation Git metadata cannot be verified") from exc
    return result.stdout.strip()


def _identity(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 128:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    return value


def _digest_value(value: object, label: str) -> Digest:
    if not isinstance(value, str):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is missing")
    try:
        return Digest(value)
    except ValueError as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid") from exc


def _raw_digest(payload: bytes) -> Digest:
    return Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "validation time must be timezone-aware")
    return value.astimezone(timezone.utc)


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _overlaps(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents
