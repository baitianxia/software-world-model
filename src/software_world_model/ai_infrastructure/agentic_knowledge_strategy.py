"""No-tools model strategy for bounded task-driven source investigation."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import re
from typing import Mapping, Protocol

from software_world_model.application_services import (
    AnswerDraftPlan,
    AnswerDraftSelection,
    AnswerNeedEvidence,
    AnswerCandidate,
    ConversationalTask,
    JointConstraint,
    KnowledgeNeed,
    KnowledgeReadSet,
    KnowledgeRequirement,
    KnowledgeRequirementPlan,
    KnowledgeUpdateRequest,
    NeedStatus,
    NeedSufficiencyDecision,
    ReviewDimension,
    SEMANTIC_CANDIDATE_EXPANSION_POLICY,
    SemanticAnswerReviewDecision,
    SourceActionProposal,
    SufficiencyAssessment,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine import (
    EntityProposal,
    EvidenceProposal,
    FactProposal,
    FormalKnowledgeRecord,
    KnowledgeCandidateBundle,
    KnowledgeContext,
    KnowledgeObjectKind,
    KNOWLEDGE_TERM_MATCH_POLICY,
    ReviewedFactGrounding,
)
from software_world_model.source_integration import (
    SourceArtifact,
    SourceOperationResult,
    SourceTool,
)

from .model_gateway import (
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    ModelExecutionContext,
    ModelCallState,
    ModelGatewayResult,
    PlatformProposalMode,
    RuntimeAccessMode,
    RecoveredModelCall,
)
from .openai_responses_adapter import OutputSchemaDefinition


AGENTIC_SOURCE_PLANNER_SCHEMA_REF = "agentic-source-planner@1"
AGENTIC_SOURCE_PLANNER_PROMPT_REF = "agentic-source-planner-prompt@6"
AGENTIC_SOURCE_PLANNER_STRATEGY_REF = "model-source-investigation-planner@6"
AGENTIC_FACT_PROPOSER_SCHEMA_REF = "agentic-fact-proposer@1"
AGENTIC_FACT_REVIEWER_SCHEMA_REF = "agentic-fact-reviewer@3"
AGENTIC_FACT_PROPOSER_PROMPT_REF = "agentic-fact-proposer-prompt@14"
AGENTIC_FACT_REVIEWER_PROMPT_REF = "agentic-fact-reviewer-prompt@14"
AGENTIC_FACT_PROPOSER_STRATEGY_REF = "model-fact-proposer@14"
AGENTIC_FACT_REVIEWER_STRATEGY_REF = "model-fact-reviewer@14"
AGENTIC_SUFFICIENCY_REVIEWER_SCHEMA_REF = "agentic-sufficiency-reviewer@1"
AGENTIC_SUFFICIENCY_REVIEWER_PROMPT_REF = "agentic-sufficiency-reviewer-prompt@8"
AGENTIC_SUFFICIENCY_REVIEWER_STRATEGY_REF = "model-need-sufficiency-reviewer@8"
AGENTIC_REQUIREMENT_PLANNER_SCHEMA_REF = "agentic-requirement-planner@1"
AGENTIC_REQUIREMENT_REVIEWER_SCHEMA_REF = "agentic-requirement-reviewer@1"
AGENTIC_REQUIREMENT_PLANNER_PROMPT_REF = "agentic-requirement-planner-prompt@6"
AGENTIC_REQUIREMENT_REVIEWER_PROMPT_REF = "agentic-requirement-reviewer-prompt@6"
AGENTIC_REQUIREMENT_PLANNER_STRATEGY_REF = "model-requirement-planner@6"
AGENTIC_REQUIREMENT_REVIEWER_STRATEGY_REF = "model-requirement-reviewer@6"
AGENTIC_ANSWER_DRAFTER_SCHEMA_REF = "agentic-answer-drafter@1"
AGENTIC_ANSWER_DRAFTER_PROMPT_REF = "agentic-answer-drafter-prompt@4"
AGENTIC_ANSWER_DRAFTER_STRATEGY_REF = "model-source-closed-answer-drafter@4"
AGENTIC_ANSWER_REVIEWER_SCHEMA_REF = "agentic-answer-reviewer@1"
AGENTIC_ANSWER_REVIEWER_PROMPT_REF = "agentic-answer-reviewer-prompt@5"
AGENTIC_ANSWER_REVIEWER_STRATEGY_REF = "model-semantic-answer-reviewer@5"
AGENTIC_KNOWLEDGE_STRATEGY_ID = "reviewed-model-software-knowledge-task"
AGENTIC_KNOWLEDGE_STRATEGY_VERSION = "1.38.0"
_MAX_STRUCTURED_OUTPUT_ATTEMPTS = 3
_MAX_ANSWER_DRAFT_ATTEMPTS = 3
_MAX_SOURCE_PROPOSAL_ATTEMPTS = 3
_MAX_REQUIREMENT_FIDELITY_ATTEMPTS = 3
_MAX_REQUIREMENT_CONTRACT_ATTEMPTS = 3
_MAX_FACT_CONTRACT_ATTEMPTS = 5
_MAX_FACT_COVERAGE_ATTEMPTS = 3
_MAX_SUFFICIENCY_CONTRACT_ATTEMPTS = 3
MAX_REQUIREMENT_NEEDS = 8
MAX_FACT_CANDIDATES = 10


AGENTIC_SOURCE_PLANNER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "agentic_source_planner",
    {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["EXECUTE", "STOP"]},
            "tool": {
                "type": "string",
                "enum": ["LIST", "SEARCH", "READ", "COMPARE", "NONE"],
            },
            "revision": {"type": "string"},
            "base": {"type": "string"},
            "path": {"type": "string"},
            "query": {"type": "string"},
            "cursor": {"type": "string"},
            "offset": {"type": "string"},
            "max_bytes": {"type": "string"},
            "page_size": {"type": "string"},
            "rationale": {"type": "string"},
        },
        "required": [
            "decision",
            "tool",
            "revision",
            "base",
            "path",
            "query",
            "cursor",
            "offset",
            "max_bytes",
            "page_size",
            "rationale",
        ],
        "additionalProperties": False,
    },
)


_CANDIDATE_PROPERTIES = {
    "candidate_key": {"type": "string"},
    "artifact_id": {"type": "string"},
    "line_start": {"type": "integer", "minimum": 1},
    "line_end": {"type": "integer", "minimum": 1},
    "entity_type": {
        "type": "string",
        "enum": [
            "SOFTWARE_SYSTEM",
            "MODULE",
            "SOURCE_FILE",
            "CODE_SYMBOL",
            "ENDPOINT",
            "CONFIGURATION",
        ],
    },
    "predicate": {
        "type": "string",
        "enum": [
            "DECLARES",
            "CALLS",
            "DEPENDS_ON",
            "EXPOSES",
            "HAS_VALUE",
            "CHANGED_IN",
            "DESCRIBED_AS",
        ],
    },
    "statement": {"type": "string"},
    "condition": {"type": ["string", "null"]},
    "limitation": {"type": ["string", "null"]},
}


AGENTIC_FACT_PROPOSER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "agentic_fact_proposer",
    {
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "maxItems": MAX_FACT_CANDIDATES,
                "items": {
                    "type": "object",
                    "properties": _CANDIDATE_PROPERTIES,
                    "required": list(_CANDIDATE_PROPERTIES),
                    "additionalProperties": False,
                },
            },
            "limitations": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["candidates", "limitations"],
        "additionalProperties": False,
    },
)


AGENTIC_FACT_REVIEWER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "agentic_fact_reviewer",
    {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["ACCEPT", "REJECT"]},
            "accepted_candidate_keys": {
                "type": "array",
                "items": {"type": "string"},
            },
            "all_supported_objective_aspects_covered": {"type": "boolean"},
            "findings": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "decision",
            "accepted_candidate_keys",
            "all_supported_objective_aspects_covered",
            "findings",
        ],
        "additionalProperties": False,
    },
)


AGENTIC_SUFFICIENCY_REVIEWER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "agentic_sufficiency_reviewer",
    {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["SATISFIED", "GAP", "CONFLICT", "UNKNOWN"],
            },
            "supporting_reference_ids": {
                "type": "array",
                "items": {"type": "string"},
            },
            "gap": {"type": ["string", "null"]},
            "counterexample_reference_ids": {
                "type": "array",
                "items": {"type": "string"},
            },
            "conflict_reference_ids": {
                "type": "array",
                "items": {"type": "string"},
            },
            "unknowns": {"type": "array", "items": {"type": "string"}},
            "limitations": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
        },
        "required": [
            "status",
            "supporting_reference_ids",
            "gap",
            "counterexample_reference_ids",
            "conflict_reference_ids",
            "unknowns",
            "limitations",
            "rationale",
        ],
        "additionalProperties": False,
    },
)


_PLANNED_NEED_PROPERTIES = {
    "need_id": {"type": "string"},
    "question": {"type": "string"},
    "required_kinds": {
        "type": "array",
        "items": {"type": "string", "enum": ["ENTITY", "FACT", "INFERENCE"]},
    },
    "required_type_names": {
        "type": "array",
        "items": {"type": "string"},
        "maxItems": 0,
    },
    "retrieval_terms": {"type": "array", "items": {"type": "string"}},
    "minimum_support_count": {"type": "integer", "minimum": 1},
}


AGENTIC_REQUIREMENT_PLANNER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "agentic_requirement_planner",
    {
        "type": "object",
        "properties": {
            "needs": {
                "type": "array",
                "minItems": 1,
                "maxItems": MAX_REQUIREMENT_NEEDS,
                "items": {
                    "type": "object",
                    "properties": _PLANNED_NEED_PROPERTIES,
                    "required": list(_PLANNED_NEED_PROPERTIES),
                    "additionalProperties": False,
                },
            },
            "joint_constraints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "constraint_id": {"type": "string"},
                        "need_ids": {"type": "array", "items": {"type": "string"}},
                        "description": {"type": "string"},
                    },
                    "required": ["constraint_id", "need_ids", "description"],
                    "additionalProperties": False,
                },
            },
            "rationale": {"type": "string"},
        },
        "required": ["needs", "joint_constraints", "rationale"],
        "additionalProperties": False,
    },
)


AGENTIC_REQUIREMENT_REVIEWER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "agentic_requirement_reviewer",
    {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["ACCEPT", "REJECT"]},
            "accepted_need_ids": {"type": "array", "items": {"type": "string"}},
            "original_request_preserved": {"type": "boolean"},
            "all_material_questions_covered": {"type": "boolean"},
            "findings": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "decision",
            "accepted_need_ids",
            "original_request_preserved",
            "all_material_questions_covered",
            "findings",
        ],
        "additionalProperties": False,
    },
)


AGENTIC_ANSWER_DRAFTER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "agentic_answer_drafter",
    {
        "type": "object",
        "properties": {
            "selections": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "need_id": {"type": "string"},
                        "formal_reference_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["need_id", "formal_reference_ids"],
                    "additionalProperties": False,
                },
            },
            "rationale": {"type": "string"},
        },
        "required": ["selections", "rationale"],
        "additionalProperties": False,
    },
)


AGENTIC_ANSWER_REVIEWER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "agentic_answer_reviewer",
    {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["APPROVE", "REJECT"]},
            "failed_dimensions": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [item.value for item in ReviewDimension],
                },
            },
            "findings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["decision", "failed_dimensions", "findings"],
        "additionalProperties": False,
    },
)


_PROMPT = """You are the source-investigation planner for a Software World Model.
You have no tools, files, web, workspace, or hidden source access. Use only the supplied exact target and prior authorized observations.
Choose exactly one next platform proposal: LIST, SEARCH, READ, COMPARE, or STOP.
Do not answer the software question and do not invent a revision, path, source result, or completion claim.
Use empty strings for fields not used by the selected tool. LIST uses revision and optional cursor/page_size. SEARCH uses revision/query and optional cursor/page_size. READ uses revision/path and optional offset/max_bytes. COMPARE uses exact base/revision. STOP uses tool NONE and all parameter fields empty.
When allowed_paths is non-empty, every READ path must be copied exactly from that list. Never add a directory prefix, normalize, or guess an alternative path. SEARCH and LIST are already restricted by the platform to the same paths.
When required_source_paths is non-empty, every listed path is a material part of the task and must be READ completely before STOP. For a single-revision target, read each path at that exact revision. For a base-to-target comparison, read each path at both the exact base and exact target revisions. A partial READ must be continued from its exact next byte offset and revision. COMPARE, SEARCH, LIST, or reading a different path does not satisfy this full-read obligation.
LIST, SEARCH, READ, and COMPARE inspect repository paths or file content only; they cannot retrieve commit messages or other revision metadata. Never propose SEARCH to obtain a commit message. If a requested epistemic limitation cannot be proved from the available source tools, investigate the answerable source questions and preserve that limitation instead of inventing an invalid action.
The decision and tool MUST agree: EXECUTE requires one executable tool; STOP requires tool NONE. If the rationale says the observations are sufficient or recommends stopping, return decision STOP, tool NONE, and empty action parameters.
When a reviewed requirement plan is supplied, use each Need to judge whether the observations are sufficient. For a base-to-target comparison, a diff proves changed lines but not omitted unchanged implementation. If any Need asks about the parent baseline, unchanged surrounding flow, behavior outside a diff hunk, or why both versions differ, READ the relevant allowed path at the exact base and target revisions before STOP. Both revisions are inside the authorized comparison boundary; never invent another revision or path.
Prefer bounded, information-gaining actions. STOP only after the supplied observations are sufficient for the objective and the exact target boundary has been observed."""


_FACT_PROPOSER_PROMPT = f"""You are a formal Fact Candidate proposer for a Software World Model.
You have no tools, files, web, workspace, or hidden source access. Use only the supplied objective, reviewed requirement plan when present, exact target, and authorized source artifacts.
Propose no more than {MAX_FACT_CANDIDATES} material facts that are directly entailed by an exact contiguous line range in one supplied artifact and help answer the objective. Prefer one concise fact that consolidates closely related branches from the same minimal range instead of many overlapping candidates. However, when the objective explicitly asks for separate outcomes under alternative conditions, repeated calls, before/after states, or comparison sides, create a candidate whose statement explicitly says the outcome for each requested branch; do not rely on a generic operation plus its condition field to leave a requested outcome implicit. The consolidation preference never permits merging away a separately requested result. The cited range must be the smallest contiguous range needed to establish the complete proposition; do not include surrounding braces, imports, comments, declarations, or other lines that are not required as evidence. Do not copy an entire file as a fact. Do not infer library runtime defaults, absence outside observed coverage, causality, uniqueness, or behavior not visible in the cited lines.
The output token budget is a hard boundary. Use one short sentence per candidate, keep condition and limitation short, and return an empty top-level limitations array when no extra disclosure is essential. When one excerpt directly supports multiple closely related Needs, use one concise candidate instead of repeating the same code in separate candidates. Never add prose outside the JSON object.
For a repeated-call or before/after proposition, trace the visible state chronologically: state at first-call entry, each first-call mutation, state at first-call exit, and state read at second-call entry. Respect boolean short-circuit order. The statement must not give a second-call local variable a value that contradicts a state mutation completed by the first call.
Each artifact includes its authorized source observation when available: exact repository revision, source tool, subject, and coverage. In a base-to-target task, a READ at the exact base revision is inside the authorized comparison boundary and directly supports parent-side behavior; a READ at the target supports target-side behavior. For a changed-from-X-to-Y proposition, either cite a minimal diff range containing both the removed and added lines, or propose separate parent-side and target-side facts whose statements explicitly identify their sides. Never cite only an added target line while claiming what the parent line was. On coverage repair, correct this evidence range instead of repeating the same incomplete comparison.
Each candidate_key must be unique. artifact_id must exactly match a supplied artifact. line_start and line_end are one-based inclusive and line_start must not exceed line_end. statement must be a self-contained proposition and must not contain the reserved labels "Condition:" or "Limitation:". Put those values only in their separate fields; use JSON null only when none applies, never the text "null".
When a reviewed requirement plan is supplied, treat each Need question as an explicit objective aspect. For every Need that the artifacts support, at least one candidate statement must explicitly state that Need's answer; a generic statement whose consequence is only explained later by a reviewer is insufficient.
Also preserve every source-supported relationship named by the objective or a joint constraint, including caller-to-helper, wrapper-to-delegate, and helper-to-observable-outcome chains. If one excerpt shows a caller or wrapper delegation and another shows what the delegated helper returns, throws, catches, closes, or invokes, propose separate minimal facts as needed; naming the helper alone does not state its observable result.
When a requested mechanism crosses artifacts, keep every edge explicit: propose one exact fact for the caller or wrapper passing its relevant argument or flag into the helper, and a separate exact fact for the helper's conditional result. Never overclaim the downstream result in the caller fact. If a prior review rejects that overclaim, repair it into the exact caller-to-helper edge instead of deleting the only bridge between the endpoints. For a requested end-to-end call sequence, reserve candidates for every named stage and its top-level return or exception behavior before spending candidates on incidental detail.
For an entry-to-end call sequence, the entry fact must preserve each material construction, initialization, assignment, and call that creates a component or data value consumed by the next named stage. Do not compress away creation of the input document, resolver, default delegate or renderer, or resolved result collection when those objects establish the requested flow.
When a Need names conceptual categories and the excerpt explicitly binds them through an argument or selector, state both the user's category and the exact source expression. For example, a lookup by a tag-name argument is the named-tag choice, a lookup by a syntax-sign argument is the syntax-character choice, and a lookup by the element's class is the element-type choice. This direct argument binding is source text, not outside inference. Do not replace the user's categories with source method names alone.
When the objective asks how a caller configures or uses a feature, preserve the public entry-point chain. Propose the builder, factory, client, or facade method that the caller invokes and its delegation, plus the downstream storage or behavior when another excerpt establishes it. An internal or lower-level configuration method alone is not a complete how-to answer when a supplied public entry point delegates to it.
When the objective asks why a path is skipped, deferred, or returned unchanged, an explicit guard, class check, early return, or later handling branch is a source-supported mechanism answer. State that mechanism directly. Do not add a limitation merely because a separate design motivation is unavailable unless the objective explicitly asks for design intent or motivation.
On a bounded coverage-repair attempt, the authorized state also contains the previous proposed candidates and the prior review findings. Correct every identified grounding or coverage problem and return a complete replacement candidate set. Do not merely repeat a rejected candidate set.
On a contract-repair attempt, fix the exact candidate, field, artifact, or line range named in last_error_details before returning the complete replacement set. Keep JSON null as null and keep every cited line within that artifact's supplied line_count.
The platform, not you, creates Evidence, Entity, Fact identities and decides admission."""


_FACT_REVIEWER_PROMPT = """You are the independent Knowledge Reviewer for proposed formal facts.
You have no tools, files, web, workspace, or hidden source access. You did not generate the candidates. Use only the supplied objective, reviewed requirement plan when present, exact target, candidate fields, and exact cited excerpts.
Accept a candidate only when its full statement, condition, limitation, entity type, and predicate are directly supported by its excerpt and do not overclaim scope, absence, runtime behavior, causality, or uniqueness. The statement must not duplicate the separate condition or limitation fields, contain the reserved labels "Condition:" or "Limitation:", or spell a missing value as the text "null". The cited line range must also be minimal: reject a candidate when its excerpt contains surrounding lines that are not needed to establish the complete proposition. Relevance alone is insufficient. Reject unsupported or ambiguous candidates.
Direct support includes deterministic consequences of explicit control flow and state mutation within the cited excerpt. When the objective asks about a repeated call, do not require a literal second invocation in the source if the shown method body fully determines that repeated-call behavior. Apply the same evidence standard to symmetric conditions and branches.
For every candidate about repeated calls or before/after state, independently simulate the cited control flow in chronological order, including short-circuit evaluation and mutations. In the findings, state the value read at each call entry and the mutation that connects the calls. Reject a candidate whose stated second-call value, branch, or outcome contradicts that trace, even when its final conclusion happens to be correct.
Use each candidate's authorized source observation to distinguish base, target, and diff evidence. The exact base revision named by a comparison target is authorized evidence, not an outside observation. A parent file excerpt directly supports parent behavior; a target file excerpt directly supports target behavior; and a diff excerpt supports a before/after change only when the cited range includes the material removed and added lines. Do not reject a parent-side fact merely because it comes from the sealed base-revision READ.
Judge the accepted set against the whole objective and every supplied reviewed Need as well as each candidate. all_supported_objective_aspects_covered is true only when every material question, condition, comparison, requested branch, and source-supported Need is explicitly answered in the statement field of at least one accepted candidate. The condition field only scopes a statement and cannot substitute for stating a requested outcome. In particular, a generic operation statement conditioned on one branch does not explicitly answer what a repeated call, alternative branch, before/after state, or comparison side does. Coverage cannot come from your findings or rationale. Do not mark coverage complete merely because you can construct an unstated conclusion by combining narrower candidates. A material objective branch or reviewed Need cannot be rejected and then silently omitted. Reject individually grounded candidates that do not help answer the objective.
When the objective names a caller, wrapper, helper, configured handler, or delegated layer, require the accepted statements to make that relationship and its requested observable result explicit. A statement that merely says a helper is called is incomplete when another supplied excerpt establishes the return, exception, fallback, close, or handler behavior the objective asks about.
For a requested cross-artifact mechanism, complete coverage requires both the exact caller-to-helper edge, including any behavior-controlling argument or flag, and the helper's exact conditional outcome. If a candidate overclaims the downstream outcome, reject that candidate but also set coverage false and require a replacement candidate containing the supported caller edge; endpoint facts cannot silently substitute for a missing edge. For an end-to-end call sequence, verify that no requested stage or top-level exception outcome was displaced by incidental detail.
For an entry-to-end sequence, reject complete coverage when the accepted entry fact omits a visible construction or initialization that creates the document, resolver, default delegate or renderer, or resolved data consumed by the next stage. When source arguments directly identify user-named conceptual categories, require the accepted statement to retain both the conceptual names and the exact selectors so later review does not depend on unstated terminology mapping.
For a how-to configuration or usage request, complete coverage requires the supplied public builder, factory, client, or facade entry point and its downstream effect. Reject coverage when the accepted set starts only at a lower-level configuration or storage method even if that method is public.
When the objective asks why a path is skipped, deferred, or returned unchanged, accept an exact source-supported guard, class check, early return, or later handling branch as the mechanism answer. Do not demand design intent or add a motivation gap unless the objective explicitly asks for design intent or motivation.
ACCEPT requires at least one accepted key and complete supported-objective coverage. REJECT requires false coverage and precise findings that a repair attempt can address; on REJECT, accepted_candidate_keys may retain the individually supported candidates for diagnostics, but the platform will publish none of them until a complete replacement set passes.
accepted_candidate_keys must be unique and drawn exactly from supplied candidates. Findings must explain material rejections or omissions without rewriting candidates."""


_SUFFICIENCY_REVIEWER_PROMPT = """You are the semantic Need Sufficiency Reviewer for a Software World Model.
You have no tools, files, web, workspace, or hidden source access. You did not create the requirement or formal knowledge. Use only the supplied original request, one Need, and the exact bounded read set.
Treat retrieval terms and type filters as candidate selection hints, not as proof. SATISFIED requires that the immutable text of the selected formal records explicitly states the answer to the whole Need question, meets minimum_support_count, and leaves no material contradiction or unknown. Your rationale cannot add a new conclusion that is merely implied by narrower formal texts. A condition attached to a generic operation does not by itself state the outcome of a requested repeated call, alternative branch, before/after state, or comparison side. Select only exact supplied record IDs. GAP means required explicit support is absent and requires a precise gap. CONFLICT requires supplied conflicting record IDs. UNKNOWN requires a precise unknown, including an incomplete read set. SATISFIED is the only status that may return supporting_reference_ids. GAP, CONFLICT, and UNKNOWN must return an empty supporting_reference_ids array. Only GAP may return a non-null gap; CONFLICT must return at least one supplied conflict reference; UNKNOWN must return at least one precise unknown. Do not infer source facts from general knowledge, identifiers, or your own rationale.
Do not add a completion criterion that the Need and original request do not ask for. A request for a call sequence is answered by the explicit caller-to-callee, dispatch, branch, and observable-outcome steps in scope; it does not require the internals of every called method or an unrequested policy-mapping algorithm. A request for when and in what order an operation runs is answered by an explicit relative position and list or branch order; do not demand a broader lifecycle phase. Judge the requested granularity, not a more detailed question you could have asked.
When a request asks what a method guarantees, explicit return behavior for every requested input branch is the guarantee. Do not demand a separately labelled invariant, type-safety statement, non-null promise, or the literal word guarantee unless the request specifically asks for one of those properties.
Treat source expressions and their explicit arguments as literal semantic bindings. A record that says the first lookup uses a tag name, the second a syntax sign, and the third the element class explicitly states named-tag, syntax-character, and element-type priority even if it also calls them custom, default, and template policies. Do not create a terminology GAP for that direct mapping.
Before returning SATISFIED, enumerate every explicit clause, condition, alternative, comparison side, or requested result in the Need. Select formal records whose immutable text covers each one. For an enumerative question such as which restrictions apply, a record about a related special case cannot replace a supplied record that states another requested guard or branch. Do not mark the Need complete while omitting a directly relevant supplied rule.
For a Need covering exception paths across separately named processing stages, select every supplied formal record needed to state each distinct failure branch. A later validate-or-render catch cannot replace a supplied record for an earlier type-conversion failure, and vice versa.
Interpret why according to the requested evidence boundary. When the request asks why one code path is skipped, deferred, or handled later, explicit control flow that states the guard or early return and the later detection, prerequisite, or handling path is a source-supported mechanism answer. Do not require a design comment, product motivation, or deeper causal rationale unless the original request explicitly asks for that motivation. Keep any genuinely unproved motivation as a limitation instead of converting a proved mechanism into a GAP.
Explicit formal records may be combined to prove one cross-component mechanism when they state every edge: for example, a wrapper calls a helper with an idempotency flag and the helper returns an already-wrapped value unchanged under that flag. Do not reject that complete chain merely because no single record spans multiple source artifacts.
When SATISFIED selects a formal record that states a material evidence boundary, condition, or limitation, preserve that boundary in the returned limitations array. Never return an empty limitations array when a selected record explicitly warns that it proves only a source declaration, only a bounded path, or not every runtime path. Do not broaden the selected proposition by dropping its own qualification.
SATISFIED cannot use a limitation to admit that an explicit part of the Need remains unanswered. If a returned limitation says a requested phase, branch, caller, result, or exception behavior is missing, the decision must be GAP or UNKNOWN rather than SATISFIED.
ENTITY records are internal identity/linkage metadata, not answer propositions: never select an ENTITY as supporting evidence. When one FACT only names a helper step and another supplied FACT explains the requested observable effect of that helper, the helper name alone is not complete support; select all facts needed to state the whole path.
The platform validates every reference and issues any support proof; your output is only an untrusted semantic decision."""


_REQUIREMENT_PLANNER_PROMPT = f"""You are the Requirement Planner for a Software World Model task.
You have no tools, files, web, workspace, knowledge snapshot, or hidden source access. Decompose only the supplied original request into atomic, answerable Needs without answering it or inventing source facts.
Return no more than {MAX_REQUIREMENT_NEEDS} Needs. Use separate Needs when the request asks what happens under mutually exclusive conditions, on separate comparison sides, or before versus after a change, so each requested result can be independently proven and rendered. Combine closely related acceptance conditions only when necessary to stay within this hard execution bound without dropping or hiding a material question.
Each Need question must preserve a material part of the request. required_kinds and retrieval_terms are candidate-selection hints, not answers or proof; required_kinds may contain FACT and INFERENCE but never ENTITY because entity records are internal linkage metadata rather than answer propositions. Leave a filter array empty when narrowing it would risk excluding relevant formal knowledge. A record matching any one retrieval term may enter the candidate set, so use concise independent terms that broaden recall rather than phrases that assume an answer. You have no authorized formal type catalog, so required_type_names MUST always be an empty array and must never contain a class, symbol, module, or guessed predicate. Use stable unique need IDs. Add a joint constraint when the request requires named Needs to be satisfied together or when one task-wide condition, limitation, uncertainty, or scope boundary applies to multiple Needs. Every such boundary must remain explicit in each affected Need question or in one joint constraint binding all affected Needs; do not leave it only in the rationale or imply it indirectly. Do not weaken conditions, comparisons, requested limitations, uncertainty, or scope.
Every required_kinds array MUST include FACT because this source-investigation path publishes reviewed source facts; add INFERENCE only as an optional additional kind. A negative capability or bounded absence that can be stated by a reviewed source fact or its explicit limitation still requires FACT and must never be restricted to INFERENCE alone.
Preserve grammatical scope. If the request asks how to configure one named mechanism and separately asks for the priority among that mechanism and other alternatives, create a configuration Need only for the mechanism actually governed by “how to configure.” The alternatives are participants in the priority Need, not new configuration questions. Never turn a named comparison participant into an independent how-to, rationale, or behavior question unless the original request asks it.
Interpret ordinary why questions about source-visible branches as mechanism questions. When a request asks why code skips, defers, preserves, or returns a value unchanged, formulate the Need around the exact guard, class check, early return, or later handling path unless the request explicitly asks for design intent, rationale, or motivation. Never upgrade why into an unavailable design-motivation requirement, especially when the request forbids unproved motivation.
Preserve each named processing path and its observable failure outcome. When a request separately lists paths such as type conversion, validation failure, normal rendering, and exceptions, a Need for type conversion must include how conversion failure is handled, or an exception Need must explicitly retain that distinct conversion-failure branch. A generic later-stage exception question cannot silently absorb or omit a failure path belonging to another named stage.
Preserve named subjects and relationship clauses such as “combine with callers”, “through a wrapper”, or “delegates to the same utility” in a Need question or applicable joint constraint. Do not spend separate Needs on details that one source proposition naturally covers when doing so would force a named caller, delegation, fallback, or observable outcome out of the bounded plan.
Treat a negative epistemic instruction such as "do not infer beyond the supplied source" or "do not claim motives beyond the commit message" as a joint constraint, not as a separate question asking whether or how unavailable metadata discusses the topic. Create a separate Need only when the user independently asks for that metadata or asks what it says.
On a bounded fidelity-repair attempt, the authorized state also contains the previous proposed plan and the prior review findings. Correct the identified fidelity problems without answering the task or adding unsupported source facts, then return the complete replacement plan."""


_REQUIREMENT_REVIEWER_PROMPT = """You are the isolated Requirement Fidelity Reviewer.
You have no tools, files, web, workspace, knowledge snapshot, or hidden source access. You did not create the proposed plan. Compare it only with the supplied original request.
Reject any Need whose required_kinds omits FACT; INFERENCE may only widen the FACT candidate set in this source-investigation workflow. Reject grammatical scope expansion: an item named only as a participant in a priority, comparison, or fallback list must not become a separate configuration, rationale, or behavior question.
Reject a plan that turns an ordinary source-code why question into a design-intent or motivation requirement when the original request asks only for the source-visible mechanism. Reject a plan that loses a distinct failure outcome of a separately named processing stage by relying on a generic exception Need; type-conversion failure, validation failure, and later rendering exceptions must remain distinguishable when the original request asks their paths separately.
ACCEPT only if every material question, named subject or caller, relationship clause, condition, comparison, limitation, and requested scope is explicit in each affected Need or an applicable joint constraint, no answer or unsupported source fact was inserted, required_type_names is empty, required_kinds never contains ENTITY, retrieval filters do not unjustifiably exclude possible evidence, every accepted_need_id exactly names a proposed Need, and all proposed Needs are accepted. When the request explicitly asks for separate results under mutually exclusive conditions, comparison sides, or before/after states, each result must have its own Need unless the hard Need limit makes that impossible; a combined Need that can be marked satisfied while one requested result remains implicit requires REJECT. Reject a plan that allocates separate Needs to naturally co-located details but consequently omits an explicit caller, wrapper, delegation, fallback, or observable-outcome relationship from the request. A negative epistemic instruction is normally a joint constraint rather than a new Need to retrieve unavailable metadata; reject a plan that turns such a boundary into an unasked factual question. required_kinds lists allowed candidate kinds; listing both FACT and INFERENCE widens retrieval and does not require an inferred answer. Retrieval terms use any-match candidate selection; one weak or misspelled term does not exclude evidence when other terms remain broad, and it is not a fidelity failure by itself. Judge the questions and constraints, not stylistic wording in retrieval hints. A boundary that appears only in rationale, is merely implied, or is absent from the returned plan is not preserved and requires REJECT. Otherwise REJECT and state precise findings. Do not repair or replace the plan in your review."""


_ANSWER_DRAFTER_PROMPT = """You are the source-closed Answer Drafter for a Software World Model.
You have no tools, files, web, workspace, hidden source access, or permission to write answer prose. Use only the supplied original request, per-Need assessment, and exact formal records already authorized by each Need support proof.
Return every Need exactly once. For a SATISFIED Need, select one or more exact formal_reference_ids that together answer its question while avoiding irrelevant repetition. For GAP, CONFLICT, or UNKNOWN, select no formal references; the platform will emit the authoritative assessment disclosure. Never select a record from another Need, invent an ID, paraphrase a proposition, or add general knowledge. The platform reconstructs immutable claim text from selected formal records and performs final review.
For a compound or enumerative SATISFIED Need, map every explicit clause, condition, alternative, comparison side, and requested result to the literal text of at least one selected record. Select every authorized record needed for that coverage. Relevance or topical overlap is not enough: a special-case record cannot replace a record that states a separate guard, phase, or outcome requested by the Need.
ENTITY records are internal identity/linkage metadata and must never be selected as answer claims. If a selected FACT names a helper step but another authorized FACT states a requested return, exception, fallback, close, or configured-handler effect, select both so the literal claim text covers the whole Need."""


_ANSWER_REVIEWER_PROMPT = """You are the isolated semantic Answer Reviewer for a Software World Model.
You have no tools, files, web, workspace, hidden source access, or permission to revise the candidate. You did not draft the candidate. Use only the supplied original request, frozen Requirement, exact Sufficiency Assessment, and source-closed Answer Candidate.
APPROVE only if the candidate preserves the original task, explicitly answers every requested condition, branch, comparison side, repeated-call result, and Need consistently with its assessment, makes no claim beyond its formal text, keeps material conditions and limitations visible, and discloses every GAP, CONFLICT, or UNKNOWN without implying completion. A conclusion that appears only in a Need assessment rationale or can merely be inferred by combining narrower candidate sentences is absent from the source-closed Answer Candidate and requires REJECT. Otherwise REJECT with one or more exact failed ReviewDimension values and concise findings. APPROVE requires empty failed_dimensions and findings; REJECT requires both to be non-empty.
For an enumerative or compound Need, verify every explicit guard, condition, alternative, phase, and requested outcome against the candidate's literal claim text. Reject when the assessment authorized the needed fact but the drafter selected only related facts and omitted that material clause. Do not approve based on the assessment rationale alone.
Reject internal identity metadata rendered as an answer claim. Also reject a path that stops at a helper or callback name when the original request asks for its observable return, error, close, fallback, or configured-handler behavior and the candidate does not state that behavior literally.
For an unsatisfied Need, a truthful authoritative disclosure that identifies the original question, says a verified answer is unavailable, and states the precise evidence gap is the complete source-closed answer for that Need. Do not demand a positive answer, a particular synonymous phrase, or an unsupported cause to replace such a disclosure. A disclosure that says the evidence proves observed behavior but does not establish its reason also satisfies a constraint against presenting unverified motivation as fact.
Judge the literal meaning of the complete candidate, including disclosures and limitations, rather than requiring a specific wording."""


def agentic_knowledge_strategy_implementation_digest() -> Digest:
    """Fingerprint every prompt, schema, and role boundary in the strategy bundle."""

    return digest_of(
        {
            "strategy_id": AGENTIC_KNOWLEDGE_STRATEGY_ID,
            "strategy_version": AGENTIC_KNOWLEDGE_STRATEGY_VERSION,
            "structured_output_retry_policy": {
                "maximum_attempts": _MAX_STRUCTURED_OUTPUT_ATTEMPTS,
                "retryable_failure": "COMPLETE_AUDITED_STRUCTURED_OUTPUT_REJECTION_ONLY",
            },
            "knowledge_candidate_query_policy": {
                "term_match": KNOWLEDGE_TERM_MATCH_POLICY,
                "semantic_candidate_expansion": (
                    SEMANTIC_CANDIDATE_EXPANSION_POLICY
                ),
            },
            "required_source_coverage_policy": (
                "COMPLETE_EXACT_REVISION_READ_FOR_EVERY_REQUIRED_PATH@2"
            ),
            "comparison_action_policy": "EXACT_AUTHORIZED_BASE_TO_TARGET@1",
            "fact_missing_value_normalization_policy": (
                "CASE_INSENSITIVE_TEXT_NULL_TO_JSON_NULL@1"
            ),
            "answerable_formal_kind_policy": "FACT_OR_INFERENCE_ONLY@1",
            "answer_draft_contract_retry_policy": {
                "maximum_total_attempts": _MAX_ANSWER_DRAFT_ATTEMPTS,
                "structured_attempts_per_contract_attempt": 1,
                "retryable_failure": "STRUCTURED_OUTPUT_INVALID_ONLY",
            },
            "source_proposal_contract_retry_policy": {
                "maximum_total_attempts": _MAX_SOURCE_PROPOSAL_ATTEMPTS,
                "structured_attempts_per_contract_attempt": 1,
                "retryable_failure": "STRUCTURED_OUTPUT_INVALID_ONLY",
            },
            "fact_contract_retry_policy": {
                "maximum_total_attempts": _MAX_FACT_CONTRACT_ATTEMPTS,
                "structured_attempts_per_contract_attempt": 1,
                "retryable_failure": "STRUCTURED_OUTPUT_INVALID_ONLY",
                "repair_input": "LAST_ERROR_MESSAGE_AND_EXACT_LOCAL_DETAILS",
            },
            "sufficiency_contract_retry_policy": {
                "maximum_total_attempts": _MAX_SUFFICIENCY_CONTRACT_ATTEMPTS,
                "structured_attempts_per_contract_attempt": 1,
                "retryable_failure": "STRUCTURED_OUTPUT_INVALID_ONLY",
            },
            "answer_rendering_policy": "ORDERED_UNIQUE_CLAIM_TEXT@1",
            "requirement_fidelity_repair_policy": {
                "maximum_cycles": _MAX_REQUIREMENT_FIDELITY_ATTEMPTS,
                "calls_per_cycle": "ONE_PROPOSAL_AND_ONE_ISOLATED_REVIEW",
                "repair_input": "PREVIOUS_PLAN_AND_PRIOR_REVIEW_FINDINGS",
            },
            "roles": (
                {
                    "role": "requirement-planning",
                    "strategy_refs": (
                        AGENTIC_REQUIREMENT_PLANNER_STRATEGY_REF,
                        AGENTIC_REQUIREMENT_REVIEWER_STRATEGY_REF,
                    ),
                    "prompts": (
                        (AGENTIC_REQUIREMENT_PLANNER_PROMPT_REF, _REQUIREMENT_PLANNER_PROMPT),
                        (AGENTIC_REQUIREMENT_REVIEWER_PROMPT_REF, _REQUIREMENT_REVIEWER_PROMPT),
                    ),
                    "schemas": (
                        (AGENTIC_REQUIREMENT_PLANNER_SCHEMA_REF, AGENTIC_REQUIREMENT_PLANNER_OUTPUT_SCHEMA.schema),
                        (AGENTIC_REQUIREMENT_REVIEWER_SCHEMA_REF, AGENTIC_REQUIREMENT_REVIEWER_OUTPUT_SCHEMA.schema),
                    ),
                },
                {
                    "role": "source-investigation",
                    "strategy_ref": AGENTIC_SOURCE_PLANNER_STRATEGY_REF,
                    "prompts": ((AGENTIC_SOURCE_PLANNER_PROMPT_REF, _PROMPT),),
                    "schemas": ((AGENTIC_SOURCE_PLANNER_SCHEMA_REF, AGENTIC_SOURCE_PLANNER_OUTPUT_SCHEMA.schema),),
                },
                {
                    "role": "formal-fact-building",
                    "strategy_refs": (
                        AGENTIC_FACT_PROPOSER_STRATEGY_REF,
                        AGENTIC_FACT_REVIEWER_STRATEGY_REF,
                    ),
                    "prompts": (
                        (AGENTIC_FACT_PROPOSER_PROMPT_REF, _FACT_PROPOSER_PROMPT),
                        (AGENTIC_FACT_REVIEWER_PROMPT_REF, _FACT_REVIEWER_PROMPT),
                    ),
                    "schemas": (
                        (AGENTIC_FACT_PROPOSER_SCHEMA_REF, AGENTIC_FACT_PROPOSER_OUTPUT_SCHEMA.schema),
                        (AGENTIC_FACT_REVIEWER_SCHEMA_REF, AGENTIC_FACT_REVIEWER_OUTPUT_SCHEMA.schema),
                    ),
                },
                {
                    "role": "need-sufficiency",
                    "strategy_ref": AGENTIC_SUFFICIENCY_REVIEWER_STRATEGY_REF,
                    "prompts": ((AGENTIC_SUFFICIENCY_REVIEWER_PROMPT_REF, _SUFFICIENCY_REVIEWER_PROMPT),),
                    "schemas": ((AGENTIC_SUFFICIENCY_REVIEWER_SCHEMA_REF, AGENTIC_SUFFICIENCY_REVIEWER_OUTPUT_SCHEMA.schema),),
                },
                {
                    "role": "answer-drafting",
                    "strategy_ref": AGENTIC_ANSWER_DRAFTER_STRATEGY_REF,
                    "prompts": ((AGENTIC_ANSWER_DRAFTER_PROMPT_REF, _ANSWER_DRAFTER_PROMPT),),
                    "schemas": ((AGENTIC_ANSWER_DRAFTER_SCHEMA_REF, AGENTIC_ANSWER_DRAFTER_OUTPUT_SCHEMA.schema),),
                },
                {
                    "role": "answer-review",
                    "strategy_ref": AGENTIC_ANSWER_REVIEWER_STRATEGY_REF,
                    "prompts": ((AGENTIC_ANSWER_REVIEWER_PROMPT_REF, _ANSWER_REVIEWER_PROMPT),),
                    "schemas": ((AGENTIC_ANSWER_REVIEWER_SCHEMA_REF, AGENTIC_ANSWER_REVIEWER_OUTPUT_SCHEMA.schema),),
                },
            ),
            "model_access": "NO_EXTERNAL_ACCESS",
            "answer_claim_policy": "PLATFORM_RECONSTRUCTS_FORMAL_TEXT@1",
            "reference_policy": "EXACT_AUTHORIZED_INPUT_ONLY@1",
        }
    )


def agentic_knowledge_output_schemas() -> dict[str, OutputSchemaDefinition]:
    """Return the exact closed schemas required by the complete strategy bundle."""

    return {
        AGENTIC_SOURCE_PLANNER_SCHEMA_REF: AGENTIC_SOURCE_PLANNER_OUTPUT_SCHEMA,
        AGENTIC_FACT_PROPOSER_SCHEMA_REF: AGENTIC_FACT_PROPOSER_OUTPUT_SCHEMA,
        AGENTIC_FACT_REVIEWER_SCHEMA_REF: AGENTIC_FACT_REVIEWER_OUTPUT_SCHEMA,
        AGENTIC_SUFFICIENCY_REVIEWER_SCHEMA_REF: AGENTIC_SUFFICIENCY_REVIEWER_OUTPUT_SCHEMA,
        AGENTIC_REQUIREMENT_PLANNER_SCHEMA_REF: AGENTIC_REQUIREMENT_PLANNER_OUTPUT_SCHEMA,
        AGENTIC_REQUIREMENT_REVIEWER_SCHEMA_REF: AGENTIC_REQUIREMENT_REVIEWER_OUTPUT_SCHEMA,
        AGENTIC_ANSWER_DRAFTER_SCHEMA_REF: AGENTIC_ANSWER_DRAFTER_OUTPUT_SCHEMA,
        AGENTIC_ANSWER_REVIEWER_SCHEMA_REF: AGENTIC_ANSWER_REVIEWER_OUTPUT_SCHEMA,
    }


def agentic_knowledge_prompt_program_digest() -> Digest:
    """Fingerprint the exact prompts used by all model calls in this strategy."""

    return digest_of(
        (
            (AGENTIC_REQUIREMENT_PLANNER_PROMPT_REF, _REQUIREMENT_PLANNER_PROMPT),
            (AGENTIC_REQUIREMENT_REVIEWER_PROMPT_REF, _REQUIREMENT_REVIEWER_PROMPT),
            (AGENTIC_SOURCE_PLANNER_PROMPT_REF, _PROMPT),
            (AGENTIC_FACT_PROPOSER_PROMPT_REF, _FACT_PROPOSER_PROMPT),
            (AGENTIC_FACT_REVIEWER_PROMPT_REF, _FACT_REVIEWER_PROMPT),
            (AGENTIC_SUFFICIENCY_REVIEWER_PROMPT_REF, _SUFFICIENCY_REVIEWER_PROMPT),
            (AGENTIC_ANSWER_DRAFTER_PROMPT_REF, _ANSWER_DRAFTER_PROMPT),
            (AGENTIC_ANSWER_REVIEWER_PROMPT_REF, _ANSWER_REVIEWER_PROMPT),
        )
    )


def agentic_knowledge_output_contract_digest() -> Digest:
    """Fingerprint every closed structured-output contract used by the strategy."""

    schemas = agentic_knowledge_output_schemas()
    return digest_of(
        tuple(
            (schema_ref, schemas[schema_ref].schema)
            for schema_ref in sorted(schemas)
        )
    )


@dataclass(frozen=True, slots=True)
class AgenticModelStrategyConfiguration:
    provider_type: str
    adapter_version: str
    model_ref: str
    provider_configuration_fingerprint: Digest
    qualification_ref: str
    max_output_tokens: int = 1200
    timeout_milliseconds: int = 180_000
    classification: str = "INTERNAL"
    max_input_records: int = 100

    def __post_init__(self) -> None:
        for value, label in (
            (self.provider_type, "provider type"),
            (self.adapter_version, "adapter version"),
            (self.model_ref, "model reference"),
            (self.qualification_ref, "qualification reference"),
            (self.classification, "classification"),
        ):
            if not isinstance(value, str) or not value or value != value.strip():
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty"
                )
        if (
            not isinstance(self.max_output_tokens, int)
            or isinstance(self.max_output_tokens, bool)
            or self.max_output_tokens < 1
            or not isinstance(self.timeout_milliseconds, int)
            or isinstance(self.timeout_milliseconds, bool)
            or self.timeout_milliseconds < 1
            or not isinstance(self.max_input_records, int)
            or isinstance(self.max_input_records, bool)
            or self.max_input_records < 1
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "agentic model strategy resource bounds must be positive integers",
            )


class ModelGatewayPort(Protocol):
    def invoke(self, context: ModelExecutionContext) -> ModelGatewayResult: ...


class AuditableModelGatewayPort(ModelGatewayPort, Protocol):
    def recover_call(self, model_call_id: StableId) -> RecoveredModelCall: ...

    def authorized_manifest(
        self, model_call_id: StableId
    ) -> AuthorizedInputManifest: ...


class ModelReviewedFactGroundingVerifier:
    """Verify that a semantic fact was proposed and independently reviewed."""

    def __init__(self, gateway: AuditableModelGatewayPort) -> None:
        self._gateway = gateway

    def verify(
        self,
        *,
        proposal: FactProposal,
        subject_proposal: EntityProposal | None,
        evidence_proposals: tuple[EvidenceProposal, ...],
    ) -> bool:
        try:
            return self._verify(
                proposal=proposal,
                subject_proposal=subject_proposal,
                evidence_proposals=evidence_proposals,
            )
        except (DomainError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False

    def _verify(
        self,
        *,
        proposal: FactProposal,
        subject_proposal: EntityProposal | None,
        evidence_proposals: tuple[EvidenceProposal, ...],
    ) -> bool:
        grounding = proposal.reviewed_grounding
        if (
            grounding is None
            or not grounding.verify_digest()
            or proposal.candidate_key != f"fact:{grounding.candidate_key}"
            or subject_proposal is None
            or len(evidence_proposals) != 1
        ):
            return False
        evidence = evidence_proposals[0]
        proposer = self._gateway.recover_call(grounding.proposer_model_call_id)
        reviewer = self._gateway.recover_call(grounding.reviewer_model_call_id)
        if not self._calls_match_grounding(proposer, reviewer, grounding):
            return False
        proposer_manifest = self._gateway.authorized_manifest(
            grounding.proposer_model_call_id
        )
        reviewer_manifest = self._gateway.authorized_manifest(
            grounding.reviewer_model_call_id
        )
        if not self._manifests_are_exact(proposer_manifest, reviewer_manifest):
            return False
        proposer_output = json.loads(proposer.response.output_text)
        reviewer_output = json.loads(reviewer.response.output_text)
        if (
            not isinstance(proposer_output, dict)
            or set(proposer_output) != {"candidates", "limitations"}
            or not isinstance(proposer_output.get("candidates"), list)
            or not _string_list(proposer_output.get("limitations"), allow_empty=True)
        ):
            return False
        raw_matches = [
            item
            for item in proposer_output["candidates"]
            if isinstance(item, dict)
            and item.get("candidate_key") == grounding.candidate_key
        ]
        if len(raw_matches) != 1:
            return False
        raw = _normalize_candidate_missing_values(raw_matches[0])
        if (
            set(raw) != _CANDIDATE_FIELDS
            or raw.get("artifact_id") != evidence.artifact.artifact_id.value
            or raw.get("entity_type") != subject_proposal.entity_type
            or raw.get("predicate") != proposal.predicate
            or _fact_text(raw) != proposal.object_value
            or not isinstance(raw.get("line_start"), int)
            or isinstance(raw.get("line_start"), bool)
            or not isinstance(raw.get("line_end"), int)
            or isinstance(raw.get("line_end"), bool)
        ):
            return False
        byte_start, byte_end = _line_byte_range(
            evidence.artifact, raw["line_start"], raw["line_end"]
        )
        if (
            byte_start != evidence.byte_start
            or byte_end != evidence.byte_end
            or proposal.evidence_keys != (evidence.evidence_key,)
            or subject_proposal.evidence_keys != (evidence.evidence_key,)
        ):
            return False
        proposer_state = _manifest_json_item(proposer_manifest, "authorized-state")
        reviewer_state = _manifest_json_item(reviewer_manifest, "authorized-state")
        artifact_view = _artifact_view(evidence.artifact)
        proposer_artifacts = proposer_state.get("artifacts")
        matching_artifacts = (
            [
                item
                for item in proposer_artifacts
                if isinstance(item, dict)
                and all(
                    item.get(key) == value
                    for key, value in artifact_view.items()
                    if key != "source_observation"
                )
            ]
            if isinstance(proposer_artifacts, list)
            else []
        )
        if (
            len(matching_artifacts) != 1
            or proposer_state.get("objective") != reviewer_state.get("objective")
            or proposer_state.get("target") != reviewer_state.get("target")
        ):
            return False
        authorized_artifact_view = matching_artifacts[0]
        expected_review_candidate = {
            **raw,
            "excerpt": _line_excerpt(
                evidence.artifact, raw["line_start"], raw["line_end"]
            ),
            "artifact_identity": evidence.artifact.source_native_identity,
            "artifact_content_digest": evidence.artifact.content_digest.value,
            "artifact_source_observation": authorized_artifact_view.get(
                "source_observation"
            ),
        }
        review_candidates = reviewer_state.get("candidates")
        if (
            not isinstance(review_candidates, list)
            or expected_review_candidate not in review_candidates
        ):
            return False
        accepted = _accepted_candidate_keys(reviewer_output, review_candidates)
        return grounding.candidate_key in accepted

    @staticmethod
    def _calls_match_grounding(
        proposer: RecoveredModelCall,
        reviewer: RecoveredModelCall,
        grounding: ReviewedFactGrounding,
    ) -> bool:
        calls = (proposer.call, reviewer.call)
        responses = (proposer.response, reviewer.response)
        return (
            all(item.state is ModelCallState.COMPLETED for item in calls)
            and all(item.usage_complete for item in calls)
            and all(item.provider_request_id for item in calls)
            and calls[0].provider_request_id != calls[1].provider_request_id
            and calls[0].requested_model_ref == calls[1].requested_model_ref
            and calls[0].actual_model_fingerprint
            == calls[1].actual_model_fingerprint
            == grounding.actual_model_fingerprint
            and responses[0] is not None
            and responses[1] is not None
            and responses[0].output_digest == grounding.proposer_output_digest
            and responses[1].output_digest == grounding.reviewer_output_digest
        )

    @staticmethod
    def _manifests_are_exact(
        proposer: AuthorizedInputManifest,
        reviewer: AuthorizedInputManifest,
    ) -> bool:
        expected = (
            (
                proposer,
                "knowledge.fact-proposal",
                AGENTIC_FACT_PROPOSER_STRATEGY_REF,
                "FACT_CANDIDATE_PROPOSAL",
                AGENTIC_FACT_PROPOSER_PROMPT_REF,
                _FACT_PROPOSER_PROMPT,
            ),
            (
                reviewer,
                "knowledge.fact-review",
                AGENTIC_FACT_REVIEWER_STRATEGY_REF,
                "FACT_CANDIDATE_REVIEW",
                AGENTIC_FACT_REVIEWER_PROMPT_REF,
                _FACT_REVIEWER_PROMPT,
            ),
        )
        for manifest, capability, strategy, stage, prompt_ref, prompt in expected:
            items = {item.item_id: item for item in manifest.items}
            if (
                manifest.capability_id != capability
                or manifest.strategy_ref != strategy
                or manifest.execution_stage != stage
                or manifest.calling_module != "application-services/knowledge-update"
                or set(items) != {"instruction", "authorized-state", "qualification"}
                or items["instruction"].authority_reference != prompt_ref
                or items["instruction"].content != prompt
            ):
                return False
        proposer_items = {item.item_id: item for item in proposer.items}
        reviewer_items = {item.item_id: item for item in reviewer.items}
        return (
            proposer.manifest_id != reviewer.manifest_id
            and proposer_items["qualification"].content
            == reviewer_items["qualification"].content
        )


class ModelReviewedKnowledgeRequirementPlanner:
    """Create a natural-language Requirement only after an isolated fidelity review."""

    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration
        self.strategy_implementation_digest = (
            agentic_knowledge_strategy_implementation_digest()
        )
        self.qualification_ref = configuration.qualification_ref
        self.classification = configuration.classification

    def plan(self, *, original_request: str) -> KnowledgeRequirementPlan:
        if not _nonempty(original_request):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "original request must be non-empty"
            )
        request_digest = digest_of(original_request).value
        previous_plan: KnowledgeRequirementPlan | None = None
        prior_findings: tuple[str, ...] = ()
        last_error: DomainError | None = None
        for fidelity_attempt in range(
            1, _MAX_REQUIREMENT_FIDELITY_ATTEMPTS + 1
        ):
            fidelity_suffix = (
                ""
                if fidelity_attempt == 1
                else f":fidelity-repair:{fidelity_attempt}"
            )
            proposal_state: dict[str, object] = {
                "original_request": original_request
            }
            if previous_plan is not None:
                proposal_state.update(
                    {
                        "previous_proposed_plan": _requirement_plan_view(
                            previous_plan
                        ),
                        "prior_review_findings": prior_findings,
                    }
                )
            plan: KnowledgeRequirementPlan | None = None
            proposal_error: DomainError | None = None
            for contract_attempt in range(
                1, _MAX_REQUIREMENT_CONTRACT_ATTEMPTS + 1
            ):
                contract_suffix = (
                    ""
                    if contract_attempt == 1
                    else f":contract-retry:{contract_attempt}"
                )
                try:
                    proposal = _invoke_configuration_json_role(
                        gateway=self._gateway,
                        configuration=self._configuration,
                        execution_ref=(
                            f"requirement-plan:{request_digest}"
                            f"{fidelity_suffix}{contract_suffix}"
                        ),
                        stage="REQUIREMENT_PROPOSAL",
                        capability_id="task.requirement-planning",
                        strategy_ref=AGENTIC_REQUIREMENT_PLANNER_STRATEGY_REF,
                        prompt_ref=AGENTIC_REQUIREMENT_PLANNER_PROMPT_REF,
                        prompt=_REQUIREMENT_PLANNER_PROMPT,
                        schema_ref=AGENTIC_REQUIREMENT_PLANNER_SCHEMA_REF,
                        state=proposal_state,
                        max_structured_output_attempts=1,
                    )
                    plan = _requirement_plan(proposal)
                    break
                except DomainError as exc:
                    if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                        raise
                    proposal_error = exc
            if plan is None:
                assert proposal_error is not None
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "requirement proposer exhausted bounded contract retries",
                    {
                        "attempt_count": _MAX_REQUIREMENT_CONTRACT_ATTEMPTS,
                        "last_error": proposal_error.message,
                    },
                ) from proposal_error

            review: dict[str, object] | None = None
            review_error: DomainError | None = None
            for contract_attempt in range(
                1, _MAX_REQUIREMENT_CONTRACT_ATTEMPTS + 1
            ):
                contract_suffix = (
                    ""
                    if contract_attempt == 1
                    else f":contract-retry:{contract_attempt}"
                )
                try:
                    review = _invoke_configuration_json_role(
                        gateway=self._gateway,
                        configuration=self._configuration,
                        execution_ref=(
                            f"requirement-review:{request_digest}"
                            f"{fidelity_suffix}{contract_suffix}"
                        ),
                        stage="REQUIREMENT_FIDELITY_REVIEW",
                        capability_id="task.requirement-review",
                        strategy_ref=AGENTIC_REQUIREMENT_REVIEWER_STRATEGY_REF,
                        prompt_ref=AGENTIC_REQUIREMENT_REVIEWER_PROMPT_REF,
                        prompt=_REQUIREMENT_REVIEWER_PROMPT,
                        schema_ref=AGENTIC_REQUIREMENT_REVIEWER_SCHEMA_REF,
                        state={
                            "original_request": original_request,
                            "proposed_plan": _requirement_plan_view(plan),
                        },
                        max_structured_output_attempts=1,
                    )
                    _verify_requirement_review(review, plan)
                    return plan
                except DomainError as exc:
                    if exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID:
                        review_error = exc
                        continue
                    if exc.code is not ErrorCode.CONTROL_STATE_DENIED:
                        raise
                    last_error = exc
                    break
            else:
                assert review_error is not None
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "requirement reviewer exhausted bounded contract retries",
                    {
                        "attempt_count": _MAX_REQUIREMENT_CONTRACT_ATTEMPTS,
                        "last_error": review_error.message,
                    },
                ) from review_error

            assert review is not None
            assert last_error is not None
            previous_plan = plan
            findings = review.get("findings")
            prior_findings = (
                tuple(findings)
                if isinstance(findings, list)
                and all(_nonempty(item) for item in findings)
                else (last_error.message,)
            )
        assert last_error is not None
        raise DomainError(
            (
                ErrorCode.CONTROL_STATE_DENIED
                if previous_plan is not None
                else last_error.code
            ),
            "requirement proposal exhausted bounded fidelity repair",
            {
                "attempt_count": _MAX_REQUIREMENT_FIDELITY_ATTEMPTS,
                "last_error": last_error.message,
            },
        ) from last_error


class ModelSourceClosedAnswerDraftPlanner:
    """Select assessment-bound formal claims without generating answer prose."""

    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration
        self.strategy_implementation_digest = (
            agentic_knowledge_strategy_implementation_digest()
        )
        self.qualification_ref = configuration.qualification_ref
        self.classification = configuration.classification

    def plan(
        self,
        *,
        original_request: str,
        needs: tuple[AnswerNeedEvidence, ...],
    ) -> AnswerDraftPlan:
        if not _nonempty(original_request) or not needs:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "answer draft input requires an original request and Needs",
            )
        state = {
            "original_request": original_request,
            "needs": tuple(
                {
                    "need_id": item.need_id,
                    "question": item.question,
                    "status": item.status.value,
                    "formal_records": tuple(
                        _formal_record_view(record)
                        for record in item.formal_records
                        if record.kind is not KnowledgeObjectKind.ENTITY
                    ),
                    "assessment_disclosure": item.disclosure,
                    "limitations": item.limitations,
                }
                for item in needs
            ),
        }
        execution_ref = f"answer-draft:{digest_of(state).value}"
        last_error: DomainError | None = None
        for attempt in range(1, _MAX_ANSWER_DRAFT_ATTEMPTS + 1):
            attempt_ref = (
                execution_ref
                if attempt == 1
                else f"{execution_ref}:contract-retry:{attempt}"
            )
            try:
                attempt_state = state
                if attempt > 1:
                    assert last_error is not None
                    attempt_state = {
                        **state,
                        "contract_repair": {
                            "last_error": last_error.message,
                            "allowed_reference_ids_by_need": {
                                item.need_id: tuple(
                                    record.object_id.value
                                    for record in item.formal_records
                                    if record.kind is not KnowledgeObjectKind.ENTITY
                                )
                                for item in needs
                            },
                            "required_action": (
                                "Return a complete replacement selection. For each "
                                "Need copy references only from that Need's own allowed "
                                "list; never reuse a reference merely because it is "
                                "available to another Need."
                            ),
                        },
                    }
                value = _invoke_configuration_json_role(
                    gateway=self._gateway,
                    configuration=self._configuration,
                    execution_ref=attempt_ref,
                    stage="ANSWER_DRAFT_SELECTION",
                    capability_id="response.answer-drafting",
                    strategy_ref=AGENTIC_ANSWER_DRAFTER_STRATEGY_REF,
                    prompt_ref=AGENTIC_ANSWER_DRAFTER_PROMPT_REF,
                    prompt=_ANSWER_DRAFTER_PROMPT,
                    schema_ref=AGENTIC_ANSWER_DRAFTER_SCHEMA_REF,
                    state=attempt_state,
                    max_structured_output_attempts=1,
                )
                return _answer_draft_plan(value, needs)
            except DomainError as exc:
                if exc.code not in {
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    ErrorCode.CONTROL_STATE_DENIED,
                }:
                    raise
                last_error = exc
        assert last_error is not None
        raise DomainError(
            last_error.code,
            "answer draft exhausted bounded contract retries",
            {
                "attempt_count": _MAX_ANSWER_DRAFT_ATTEMPTS,
                "last_error": last_error.message,
            },
        ) from last_error


class ModelSemanticAnswerReviewer:
    """Review task fidelity and completeness in an isolated model call."""

    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration
        self.strategy_implementation_digest = (
            agentic_knowledge_strategy_implementation_digest()
        )
        self.qualification_ref = configuration.qualification_ref
        self.classification = configuration.classification

    def review(
        self,
        *,
        task: ConversationalTask,
        requirement: KnowledgeRequirement,
        candidate: AnswerCandidate,
        assessment: SufficiencyAssessment,
    ) -> SemanticAnswerReviewDecision:
        state = {
            "original_request": task.original_request,
            "requirement": {
                "id": requirement.requirement_id.value,
                "revision": requirement.revision.value,
                "digest": requirement.digest.value,
                "needs": tuple(
                    {
                        "need_id": item.need_id,
                        "question": item.question,
                    }
                    for item in requirement.needs
                ),
                "joint_constraints": tuple(
                    {
                        "constraint_id": item.constraint_id,
                        "need_ids": item.need_ids,
                        "description": item.description,
                    }
                    for item in requirement.joint_constraints
                ),
            },
            "assessment": {
                "id": assessment.assessment_id.value,
                "digest": assessment.digest.value,
                "sufficient": assessment.sufficient,
                "joint_constraint_failures": assessment.joint_constraint_failures,
                "items": tuple(
                    {
                        "need_id": item.need_id,
                        "status": item.status.value,
                        "supporting_references": (
                            tuple(
                                reference.value
                                for reference in item.proof.supporting_references
                            )
                            if item.proof
                            else ()
                        ),
                        "gap": item.gap,
                        "unknowns": item.unknowns,
                        "limitations": item.limitations,
                        "conflicts": tuple(
                            reference.value for reference in item.conflicts
                        ),
                    }
                    for item in assessment.items
                ),
            },
            "candidate": {
                "id": candidate.candidate_id.value,
                "digest": candidate.digest.value,
                "response_kind": candidate.response_kind.value,
                "body": candidate.body,
                "claims": tuple(
                    {
                        "claim_id": item.claim_id,
                        "need_id": item.need_id,
                        "kind": item.kind.value,
                        "text": item.text,
                        "formal_reference": (
                            item.formal_reference.value
                            if item.formal_reference
                            else None
                        ),
                        "gap": item.gap,
                    }
                    for item in candidate.claims
                ),
            },
        }
        value = _invoke_configuration_json_role(
            gateway=self._gateway,
            configuration=self._configuration,
            execution_ref=f"answer-review:{candidate.candidate_id.value}:{candidate.digest.value}",
            stage="ANSWER_SEMANTIC_REVIEW",
            capability_id="response.answer-review",
            strategy_ref=AGENTIC_ANSWER_REVIEWER_STRATEGY_REF,
            prompt_ref=AGENTIC_ANSWER_REVIEWER_PROMPT_REF,
            prompt=_ANSWER_REVIEWER_PROMPT,
            schema_ref=AGENTIC_ANSWER_REVIEWER_SCHEMA_REF,
            state=state,
        )
        return _semantic_answer_review(value)


class ModelSourceInvestigationPlanner:
    """Translate eligible no-tools model output into an untrusted source proposal."""

    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration
        self.strategy_implementation_digest = (
            agentic_knowledge_strategy_implementation_digest()
        )
        self.qualification_ref = configuration.qualification_ref
        self.classification = configuration.classification

    def propose(
        self,
        *,
        request: KnowledgeUpdateRequest,
        completed_operations: tuple[SourceOperationResult, ...],
        ordinal: int,
    ) -> SourceActionProposal:
        manifest = AuthorizedInputManifest.create(
            capability_id="knowledge.source-investigation",
            strategy_ref=AGENTIC_SOURCE_PLANNER_STRATEGY_REF,
            execution_stage="SOURCE_TOOL_PROPOSAL",
            calling_module="application-services/knowledge-update",
            proposal_vocabulary_ref=AGENTIC_SOURCE_PLANNER_SCHEMA_REF,
            items=(
                AuthorizedInputItem.create(
                    item_id="instruction",
                    schema_ref="text@1",
                    classification=self._configuration.classification,
                    purpose="source planning policy",
                    authority_reference=AGENTIC_SOURCE_PLANNER_PROMPT_REF,
                    disposition=InputDisposition.PROVIDED,
                    content=_PROMPT,
                ),
                AuthorizedInputItem.create(
                    item_id="task-state",
                    schema_ref="agentic-source-task-state@1",
                    classification=request.classification,
                    purpose="choose the next bounded source action",
                    authority_reference=(
                        f"knowledge-update:{request.idempotency_key.value}:proposal:{ordinal}"
                    ),
                    disposition=InputDisposition.PROVIDED,
                    content=json.dumps(
                        {
                            "objective": {
                                "id": request.objective.objective_id,
                                "description": request.objective.description,
                                "unacceptable_outcomes": request.objective.unacceptable_outcomes,
                                "digest": request.objective.digest.value,
                            },
                            "reviewed_requirement_plan": (
                                _requirement_plan_view(
                                    getattr(request, "requirement_plan")
                                )
                                if getattr(request, "requirement_plan", None)
                                is not None
                                else None
                            ),
                            "target": {
                                "kind": request.target.target_kind.value,
                                "identity": dict(request.target.canonical_identity),
                                "boundary": request.target.boundary,
                                "digest": request.target.digest.value,
                                "allowed_paths": getattr(
                                    request, "allowed_source_paths", ()
                                ),
                                "required_source_paths": getattr(
                                    request, "required_source_paths", ()
                                ),
                            },
                            "budget": {
                                "max_steps": request.max_steps,
                                "current_ordinal": ordinal,
                                "remaining_steps_including_current": (
                                    request.max_steps - ordinal + 1
                                ),
                                "max_items_per_step": request.max_items_per_step,
                                "max_bytes_per_step": request.max_bytes_per_step,
                            },
                            "completed_operations": [
                                _operation_view(item) for item in completed_operations
                            ],
                            "recovery_guidance": _source_recovery_guidance(
                                completed_operations
                            ),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
                AuthorizedInputItem.create(
                    item_id="qualification",
                    schema_ref="qualification-ref@1",
                    classification=self._configuration.classification,
                    purpose="bind the selected evaluated strategy",
                    authority_reference=self._configuration.qualification_ref,
                    disposition=InputDisposition.PROVIDED,
                    content=self._configuration.qualification_ref,
                ),
            ),
        )
        base_context = ModelExecutionContext(
            execution_envelope_ref=(
                f"knowledge-update:{request.idempotency_key.value}:planner:{ordinal}"
            ),
            manifest=manifest,
            prompt_program_ref=AGENTIC_SOURCE_PLANNER_PROMPT_REF,
            rendering_contract_version="manifest-messages@1",
            output_schema_ref=AGENTIC_SOURCE_PLANNER_SCHEMA_REF,
            runtime_access_mode=RuntimeAccessMode.NO_EXTERNAL_ACCESS,
            platform_proposal_mode=(
                PlatformProposalMode.DECLARED_PLATFORM_PROPOSAL_ONLY
            ),
            requested_model_ref=self._configuration.model_ref,
            provider_type=self._configuration.provider_type,
            adapter_version=self._configuration.adapter_version,
            provider_configuration_fingerprint=(
                self._configuration.provider_configuration_fingerprint
            ),
            max_output_tokens=self._configuration.max_output_tokens,
            timeout_milliseconds=self._configuration.timeout_milliseconds,
            classification=request.classification,
            required_exact_fingerprint=True,
        )
        last_error: DomainError | None = None
        for attempt in range(1, _MAX_SOURCE_PROPOSAL_ATTEMPTS + 1):
            if attempt == 1:
                attempt_context = base_context
            else:
                assert last_error is not None
                repair_item = AuthorizedInputItem.create(
                    item_id=f"contract-repair-{attempt}",
                    schema_ref="source-proposal-contract-repair@1",
                    classification=self._configuration.classification,
                    purpose="repair an invalid source proposal contract",
                    authority_reference=AGENTIC_SOURCE_PLANNER_PROMPT_REF,
                    disposition=InputDisposition.PROVIDED,
                    content=json.dumps(
                        {
                            "last_error": last_error.message,
                            "last_error_details": dict(last_error.details),
                            "required_action": (
                                "Return a complete replacement proposal that obeys "
                                "the closed tool contract. If missing_required_paths "
                                "is present, READ the first exact path at the exact "
                                "target revision and continue any partial range from "
                                "its next required offset. If consecutive_empty_searches "
                                "is present, do not SEARCH again; READ an exact path "
                                "copied from a prior LIST result or STOP. If expected_base and "
                                "expected_revision are present, copy them exactly into "
                                "the COMPARE base and revision fields. Otherwise supply "
                                "every required non-empty parameter for the selected tool."
                            ),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
                retry_manifest = AuthorizedInputManifest.create(
                    capability_id=manifest.capability_id,
                    strategy_ref=manifest.strategy_ref,
                    execution_stage=manifest.execution_stage,
                    calling_module=manifest.calling_module,
                    proposal_vocabulary_ref=manifest.proposal_vocabulary_ref,
                    items=manifest.items + (repair_item,),
                )
                attempt_context = replace(
                    base_context,
                    execution_envelope_ref=(
                        f"{base_context.execution_envelope_ref}:contract-retry:{attempt}"
                    ),
                    manifest=retry_manifest,
                )
            try:
                result = _invoke_eligible_model_result(
                    self._gateway,
                    attempt_context,
                    stage="source planner",
                    max_attempts=1,
                )
                assert result.response is not None
                try:
                    value = json.loads(result.response.output_text)
                except json.JSONDecodeError as exc:
                    raise DomainError(
                        ErrorCode.STRUCTURED_OUTPUT_INVALID,
                        "source planner output is not JSON",
                    ) from exc
                return _proposal(
                    value,
                    request=request,
                    completed_operations=completed_operations,
                )
            except DomainError as exc:
                if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                    raise
                last_error = exc
        assert last_error is not None
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "source planner exhausted bounded contract retries",
            {
                "attempt_count": _MAX_SOURCE_PROPOSAL_ATTEMPTS,
                "last_error": last_error.message,
            },
        ) from last_error


class ModelReviewedKnowledgeBuilder:
    """Create formal candidates only after an isolated source-grounded review."""

    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration
        self.strategy_implementation_digest = (
            agentic_knowledge_strategy_implementation_digest()
        )
        self.qualification_ref = configuration.qualification_ref
        self.classification = configuration.classification

    def build(
        self,
        *,
        request: KnowledgeUpdateRequest,
        target: object,
        artifacts: tuple[SourceArtifact, ...],
        source_operations: tuple[SourceOperationResult, ...] = (),
    ) -> KnowledgeCandidateBundle:
        usable = tuple(item for item in artifacts if item.payload and not item.truncated)
        if not usable:
            return KnowledgeCandidateBundle("INITIAL@1", (), (), (), ())
        common = {
            "objective": {
                "id": request.objective.objective_id,
                "description": request.objective.description,
                "unacceptable_outcomes": request.objective.unacceptable_outcomes,
                "digest": request.objective.digest.value,
            },
            "target": {
                "kind": request.target.target_kind.value,
                "identity": dict(request.target.canonical_identity),
                "boundary": request.target.boundary,
                "digest": request.target.digest.value,
            },
            "response_language": _requested_response_language(
                request.objective.description
            ),
        }
        requirement_plan = getattr(request, "requirement_plan", None)
        if requirement_plan is not None:
            common["reviewed_requirement_plan"] = _requirement_plan_view(
                requirement_plan
            )
        artifact_origins = _artifact_origins(source_operations)
        proposal_result: ModelGatewayResult | None = None
        review_result: ModelGatewayResult | None = None
        candidates: list[dict[str, object]] | None = None
        accepted: frozenset[str] | None = None
        prior_candidates: list[dict[str, object]] | None = None
        prior_findings: list[str] = []
        for coverage_attempt in range(1, _MAX_FACT_COVERAGE_ATTEMPTS + 1):
            coverage_suffix = (
                ""
                if coverage_attempt == 1
                else f":coverage-repair:{coverage_attempt}"
            )
            proposal_state: dict[str, object] = {
                **common,
                "artifacts": [
                    _artifact_view(
                        item, artifact_origins.get(item.artifact_id.value)
                    )
                    for item in usable
                ],
            }
            if prior_candidates is not None:
                proposal_state.update(
                    {
                        "previous_proposed_candidates": prior_candidates,
                        "prior_review_findings": prior_findings,
                    }
                )
            proposal_result = None
            candidates = None
            last_error: DomainError | None = None
            for attempt in range(1, _MAX_FACT_CONTRACT_ATTEMPTS + 1):
                contract_suffix = (
                    "" if attempt == 1 else f":contract-retry:{attempt}"
                )
                try:
                    attempt_state = proposal_state
                    if attempt > 1:
                        assert last_error is not None
                        attempt_state = {
                            **proposal_state,
                            "contract_repair": {
                                "last_error": last_error.message,
                                "last_error_details": dict(last_error.details),
                                "required_action": (
                                    "Return a complete replacement JSON object within "
                                    "the hard output budget. Shorten every candidate, "
                                    "consolidate facts supported by the same excerpt, "
                                    "and emit no prose outside JSON."
                                ),
                            },
                        }
                    proposal, proposal_result = _invoke_json_role_with_result(
                        gateway=self._gateway,
                        configuration=self._configuration,
                        request=request,
                        stage="FACT_CANDIDATE_PROPOSAL",
                        capability_id="knowledge.fact-proposal",
                        strategy_ref=AGENTIC_FACT_PROPOSER_STRATEGY_REF,
                        prompt_ref=AGENTIC_FACT_PROPOSER_PROMPT_REF,
                        prompt=_FACT_PROPOSER_PROMPT,
                        schema_ref=AGENTIC_FACT_PROPOSER_SCHEMA_REF,
                        state=attempt_state,
                        execution_suffix=coverage_suffix + contract_suffix,
                        max_structured_output_attempts=1,
                    )
                    candidates = _candidate_views(
                        proposal, usable, artifact_origins
                    )
                    _validate_candidate_response_language(
                        candidates, common["response_language"]
                    )
                    break
                except DomainError as exc:
                    if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                        raise
                    last_error = exc
            if candidates is None or proposal_result is None:
                assert last_error is not None
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "fact proposer exhausted bounded contract retries",
                    {
                        "attempt_count": _MAX_FACT_CONTRACT_ATTEMPTS,
                        "last_error": last_error.message,
                    },
                ) from last_error
            if not candidates:
                return KnowledgeCandidateBundle("INITIAL@1", (), (), (), ())

            review_result = None
            accepted = None
            review: Mapping[str, object] | None = None
            last_error = None
            for attempt in range(1, _MAX_FACT_CONTRACT_ATTEMPTS + 1):
                contract_suffix = (
                    "" if attempt == 1 else f":contract-retry:{attempt}"
                )
                try:
                    review_state: dict[str, object] = {
                        **common,
                        "candidates": candidates,
                    }
                    if attempt > 1:
                        assert last_error is not None
                        review_state["contract_repair"] = {
                            "last_error": last_error.message,
                            "required_action": (
                                "Return a complete concise replacement review JSON "
                                "within the hard output budget; keep findings short."
                            ),
                        }
                    review, review_result = _invoke_json_role_with_result(
                        gateway=self._gateway,
                        configuration=self._configuration,
                        request=request,
                        stage="FACT_CANDIDATE_REVIEW",
                        capability_id="knowledge.fact-review",
                        strategy_ref=AGENTIC_FACT_REVIEWER_STRATEGY_REF,
                        prompt_ref=AGENTIC_FACT_REVIEWER_PROMPT_REF,
                        prompt=_FACT_REVIEWER_PROMPT,
                        schema_ref=AGENTIC_FACT_REVIEWER_SCHEMA_REF,
                        state=review_state,
                        execution_suffix=coverage_suffix + contract_suffix,
                        max_structured_output_attempts=1,
                    )
                    accepted = _accepted_candidate_keys(review, candidates)
                    break
                except DomainError as exc:
                    if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                        raise
                    last_error = exc
            if accepted is None or review_result is None or review is None:
                assert last_error is not None
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "fact reviewer exhausted bounded contract retries",
                    {
                        "attempt_count": _MAX_FACT_CONTRACT_ATTEMPTS,
                        "last_error": last_error.message,
                    },
                ) from last_error
            if accepted:
                break
            prior_candidates = candidates
            prior_findings = list(review["findings"])
        else:
            return KnowledgeCandidateBundle("INITIAL@1", (), (), (), ())

        assert proposal_result is not None
        assert review_result is not None
        assert candidates is not None
        assert accepted is not None
        artifacts_by_id = {item.artifact_id.value: item for item in usable}
        context = KnowledgeContext.create(dict(request.target.canonical_identity))
        evidence = []
        entities = []
        facts = []
        if (
            proposal_result.response is None
            or review_result.response is None
            or proposal_result.call.actual_model_fingerprint is None
            or proposal_result.call.actual_model_fingerprint
            != review_result.call.actual_model_fingerprint
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "fact proposal and review do not have the same recorded actual model",
            )
        for item in candidates:
            if item["candidate_key"] not in accepted:
                continue
            artifact = artifacts_by_id[item["artifact_id"]]
            byte_start, byte_end = _line_byte_range(
                artifact,
                int(item["line_start"]),
                int(item["line_end"]),
            )
            key = item["candidate_key"]
            evidence_key = f"evidence:{key}"
            entity_key = f"entity:{key}"
            evidence.append(
                EvidenceProposal(
                    evidence_key=evidence_key,
                    artifact=artifact,
                    byte_start=byte_start,
                    byte_end=byte_end,
                    locator=(
                        f"{artifact.source_native_identity}:"
                        f"{item['line_start']}-{item['line_end']}"
                    ),
                )
            )
            entities.append(
                EntityProposal(
                    candidate_key=entity_key,
                    entity_type=item["entity_type"],
                    natural_key=(
                        f"{request.target.digest.value}:"
                        f"{artifact.source_native_identity}:{key}"
                    ),
                    label=artifact.source_native_identity,
                    context=context,
                    evidence_keys=(evidence_key,),
                )
            )
            facts.append(
                FactProposal(
                    candidate_key=f"fact:{key}",
                    subject_candidate_key=entity_key,
                    subject_entity_id=None,
                    predicate=item["predicate"],
                    object_value=_fact_text(item),
                    context=context,
                    evidence_keys=(evidence_key,),
                    reviewed_grounding=ReviewedFactGrounding.create(
                        candidate_key=key,
                        proposer_model_call_id=proposal_result.call.model_call_id,
                        proposer_output_digest=proposal_result.response.output_digest,
                        reviewer_model_call_id=review_result.call.model_call_id,
                        reviewer_output_digest=review_result.response.output_digest,
                        actual_model_fingerprint=(
                            proposal_result.call.actual_model_fingerprint
                        ),
                    ),
                )
            )
        return KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=tuple(evidence),
            entities=tuple(entities),
            facts=tuple(facts),
            inferences=(),
        )


class ModelNeedSufficiencyEvaluator:
    """Semantically review one Need using only its exact formal read set."""

    semantic_zero_match_fallback_enabled = True
    semantic_candidate_expansion_enabled = True

    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration
        self.strategy_implementation_digest = (
            agentic_knowledge_strategy_implementation_digest()
        )
        self.qualification_ref = configuration.qualification_ref
        self.classification = configuration.classification
        self.semantic_candidate_expansion_limit = configuration.max_input_records

    def evaluate(
        self,
        *,
        requirement: KnowledgeRequirement,
        need: KnowledgeNeed,
        read_set: KnowledgeReadSet,
    ) -> NeedSufficiencyDecision:
        if not read_set.complete:
            return NeedSufficiencyDecision(
                status=NeedStatus.UNKNOWN,
                unknowns=("the exact formal read set is incomplete",),
                limitations=("semantic model review was not invoked",),
            )
        if len(read_set.records) > self._configuration.max_input_records:
            return NeedSufficiencyDecision(
                status=NeedStatus.UNKNOWN,
                unknowns=("the formal read set exceeds the configured model input budget",),
                limitations=("semantic model review was not invoked",),
            )
        manifest = AuthorizedInputManifest.create(
            capability_id="knowledge.need-sufficiency",
            strategy_ref=AGENTIC_SUFFICIENCY_REVIEWER_STRATEGY_REF,
            execution_stage="NEED_SUFFICIENCY_REVIEW",
            calling_module="application-services/knowledge-use",
            proposal_vocabulary_ref=None,
            items=(
                AuthorizedInputItem.create(
                    item_id="instruction",
                    schema_ref="text@1",
                    classification=self._configuration.classification,
                    purpose="semantic Need sufficiency policy",
                    authority_reference=AGENTIC_SUFFICIENCY_REVIEWER_PROMPT_REF,
                    disposition=InputDisposition.PROVIDED,
                    content=_SUFFICIENCY_REVIEWER_PROMPT,
                ),
                AuthorizedInputItem.create(
                    item_id="authorized-state",
                    schema_ref="need-sufficiency-state@1",
                    classification=self._configuration.classification,
                    purpose="review one Need against one exact formal read set",
                    authority_reference=(
                        f"requirement:{requirement.requirement_id.value}:"
                        f"{requirement.revision.value}:need:{need.need_id}"
                    ),
                    disposition=InputDisposition.PROVIDED,
                    content=json.dumps(
                        {
                            "original_request": requirement.original_request,
                            "requirement_digest": requirement.digest.value,
                            "need": {
                                "need_id": need.need_id,
                                "question": need.question,
                                "required_kinds": tuple(
                                    item.value for item in need.required_kinds
                                ),
                                "required_type_names": need.required_type_names,
                                "retrieval_terms": need.required_terms,
                                "minimum_support_count": need.minimum_support_count,
                            },
                            "read_set": {
                                "digest": read_set.digest.value,
                                "complete": read_set.complete,
                                "records": tuple(
                                    _formal_record_view(item)
                                    for item in read_set.records
                                ),
                            },
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
                AuthorizedInputItem.create(
                    item_id="qualification",
                    schema_ref="qualification-ref@1",
                    classification=self._configuration.classification,
                    purpose="bind the selected evaluated strategy",
                    authority_reference=self._configuration.qualification_ref,
                    disposition=InputDisposition.PROVIDED,
                    content=self._configuration.qualification_ref,
                ),
            ),
        )
        execution_ref = (
            f"requirement:{requirement.requirement_id.value}:"
            f"{requirement.revision.value}:need:{need.need_id}:"
            f"read-set:{read_set.digest.value}:sufficiency"
        )
        base_context = ModelExecutionContext(
                execution_envelope_ref=execution_ref,
                manifest=manifest,
                prompt_program_ref=AGENTIC_SUFFICIENCY_REVIEWER_PROMPT_REF,
                rendering_contract_version="manifest-messages@1",
                output_schema_ref=AGENTIC_SUFFICIENCY_REVIEWER_SCHEMA_REF,
                runtime_access_mode=RuntimeAccessMode.NO_EXTERNAL_ACCESS,
                platform_proposal_mode=PlatformProposalMode.NONE,
                requested_model_ref=self._configuration.model_ref,
                provider_type=self._configuration.provider_type,
                adapter_version=self._configuration.adapter_version,
                provider_configuration_fingerprint=(
                    self._configuration.provider_configuration_fingerprint
                ),
                max_output_tokens=self._configuration.max_output_tokens,
                timeout_milliseconds=self._configuration.timeout_milliseconds,
                classification=self._configuration.classification,
                required_exact_fingerprint=True,
        )
        last_error: DomainError | None = None
        for attempt in range(1, _MAX_SUFFICIENCY_CONTRACT_ATTEMPTS + 1):
            if attempt == 1:
                attempt_context = base_context
            else:
                assert last_error is not None
                repair_item = AuthorizedInputItem.create(
                    item_id=f"contract-repair-{attempt}",
                    schema_ref="need-sufficiency-contract-repair@1",
                    classification=self._configuration.classification,
                    purpose="repair an invalid Need sufficiency decision",
                    authority_reference=AGENTIC_SUFFICIENCY_REVIEWER_PROMPT_REF,
                    disposition=InputDisposition.PROVIDED,
                    content=json.dumps(
                        {
                            "last_error": last_error.message,
                            "allowed_reference_ids": tuple(
                                item.object_id.value
                                for item in read_set.records
                                if item.kind is not KnowledgeObjectKind.ENTITY
                            ),
                            "required_action": (
                                "Return a complete replacement decision. Copy any "
                                "formal reference exactly from allowed_reference_ids; "
                                "do not select ENTITY metadata and do not repair, "
                                "extend, or invent an identifier."
                            ),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
                retry_manifest = AuthorizedInputManifest.create(
                    capability_id=manifest.capability_id,
                    strategy_ref=manifest.strategy_ref,
                    execution_stage=manifest.execution_stage,
                    calling_module=manifest.calling_module,
                    proposal_vocabulary_ref=manifest.proposal_vocabulary_ref,
                    items=manifest.items + (repair_item,),
                )
                attempt_context = replace(
                    base_context,
                    execution_envelope_ref=(
                        f"{execution_ref}:contract-retry:{attempt}"
                    ),
                    manifest=retry_manifest,
                )
            try:
                result = _invoke_eligible_model_result(
                    self._gateway,
                    attempt_context,
                    stage="Need sufficiency",
                    max_attempts=1,
                )
                assert result.response is not None
                try:
                    value = json.loads(result.response.output_text)
                except json.JSONDecodeError as exc:
                    raise DomainError(
                        ErrorCode.STRUCTURED_OUTPUT_INVALID,
                        "Need sufficiency output is not JSON",
                    ) from exc
                return _sufficiency_decision(value, read_set, need)
            except DomainError as exc:
                if exc.code not in {
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    ErrorCode.CONTROL_STATE_DENIED,
                }:
                    raise
                last_error = exc
        assert last_error is not None
        raise DomainError(
            last_error.code,
            "Need sufficiency exhausted bounded contract retries",
            {
                "attempt_count": _MAX_SUFFICIENCY_CONTRACT_ATTEMPTS,
                "last_error": last_error.message,
            },
        ) from last_error


@dataclass(frozen=True, slots=True)
class AgenticKnowledgeStrategyBundle:
    """One exact, fingerprinted assembly of all six model-backed task roles."""

    implementation_digest: Digest
    requirement_planner: ModelReviewedKnowledgeRequirementPlanner
    source_planner: ModelSourceInvestigationPlanner
    knowledge_builder: ModelReviewedKnowledgeBuilder
    sufficiency_evaluator: ModelNeedSufficiencyEvaluator
    answer_planner: ModelSourceClosedAnswerDraftPlanner
    answer_reviewer: ModelSemanticAnswerReviewer

    @classmethod
    def create(
        cls,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> "AgenticKnowledgeStrategyBundle":
        implementation_digest = agentic_knowledge_strategy_implementation_digest()
        return cls(
            implementation_digest=implementation_digest,
            requirement_planner=ModelReviewedKnowledgeRequirementPlanner(
                gateway, configuration
            ),
            source_planner=ModelSourceInvestigationPlanner(gateway, configuration),
            knowledge_builder=ModelReviewedKnowledgeBuilder(gateway, configuration),
            sufficiency_evaluator=ModelNeedSufficiencyEvaluator(
                gateway, configuration
            ),
            answer_planner=ModelSourceClosedAnswerDraftPlanner(
                gateway, configuration
            ),
            answer_reviewer=ModelSemanticAnswerReviewer(gateway, configuration),
        )


def _invoke_configuration_json_role(
    *,
    gateway: ModelGatewayPort,
    configuration: AgenticModelStrategyConfiguration,
    execution_ref: str,
    stage: str,
    capability_id: str,
    strategy_ref: str,
    prompt_ref: str,
    prompt: str,
    schema_ref: str,
    state: Mapping[str, object],
    max_structured_output_attempts: int = _MAX_STRUCTURED_OUTPUT_ATTEMPTS,
) -> dict[str, object]:
    manifest = AuthorizedInputManifest.create(
        capability_id=capability_id,
        strategy_ref=strategy_ref,
        execution_stage=stage,
        calling_module="application-services/task-query",
        proposal_vocabulary_ref=None,
        items=(
            AuthorizedInputItem.create(
                item_id="instruction",
                schema_ref="text@1",
                classification=configuration.classification,
                purpose=stage.lower().replace("_", " "),
                authority_reference=prompt_ref,
                disposition=InputDisposition.PROVIDED,
                content=prompt,
            ),
            AuthorizedInputItem.create(
                item_id="authorized-state",
                schema_ref=f"{stage.lower().replace('_', '-')}@1",
                classification=configuration.classification,
                purpose="authorized task role input",
                authority_reference=execution_ref,
                disposition=InputDisposition.PROVIDED,
                content=json.dumps(
                    state,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
            AuthorizedInputItem.create(
                item_id="qualification",
                schema_ref="qualification-ref@1",
                classification=configuration.classification,
                purpose="bind the selected evaluated strategy",
                authority_reference=configuration.qualification_ref,
                disposition=InputDisposition.PROVIDED,
                content=configuration.qualification_ref,
            ),
        ),
    )
    result = _invoke_eligible_model_result(
        gateway,
        ModelExecutionContext(
            execution_envelope_ref=execution_ref,
            manifest=manifest,
            prompt_program_ref=prompt_ref,
            rendering_contract_version="manifest-messages@1",
            output_schema_ref=schema_ref,
            runtime_access_mode=RuntimeAccessMode.NO_EXTERNAL_ACCESS,
            platform_proposal_mode=PlatformProposalMode.NONE,
            requested_model_ref=configuration.model_ref,
            provider_type=configuration.provider_type,
            adapter_version=configuration.adapter_version,
            provider_configuration_fingerprint=(
                configuration.provider_configuration_fingerprint
            ),
            max_output_tokens=configuration.max_output_tokens,
            timeout_milliseconds=configuration.timeout_milliseconds,
            classification=configuration.classification,
            required_exact_fingerprint=True,
        ),
        stage=stage.lower(),
        max_attempts=max_structured_output_attempts,
    )
    assert result.response is not None
    try:
        value = json.loads(result.response.output_text)
    except json.JSONDecodeError as exc:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            f"{stage.lower()} output is not JSON",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            f"{stage.lower()} output must be an object",
        )
    return value


def _invoke_json_role_with_result(
    *,
    gateway: ModelGatewayPort,
    configuration: AgenticModelStrategyConfiguration,
    request: KnowledgeUpdateRequest,
    stage: str,
    capability_id: str,
    strategy_ref: str,
    prompt_ref: str,
    prompt: str,
    schema_ref: str,
    state: Mapping[str, object],
    execution_suffix: str = "",
    max_structured_output_attempts: int = _MAX_STRUCTURED_OUTPUT_ATTEMPTS,
) -> tuple[dict[str, object], ModelGatewayResult]:
    execution_ref = (
        f"knowledge-update:{request.idempotency_key.value}:{stage}"
        f"{execution_suffix}"
    )
    manifest = AuthorizedInputManifest.create(
        capability_id=capability_id,
        strategy_ref=strategy_ref,
        execution_stage=stage,
        calling_module="application-services/knowledge-update",
        proposal_vocabulary_ref=None,
        items=(
            AuthorizedInputItem.create(
                item_id="instruction",
                schema_ref="text@1",
                classification=configuration.classification,
                purpose=stage.lower().replace("_", " "),
                authority_reference=prompt_ref,
                disposition=InputDisposition.PROVIDED,
                content=prompt,
            ),
            AuthorizedInputItem.create(
                item_id="authorized-state",
                schema_ref=f"{stage.lower().replace('_', '-')}@1",
                classification=request.classification,
                purpose="authorized role input",
                authority_reference=execution_ref,
                disposition=InputDisposition.PROVIDED,
                content=json.dumps(
                    state,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
            AuthorizedInputItem.create(
                item_id="qualification",
                schema_ref="qualification-ref@1",
                classification=configuration.classification,
                purpose="bind the selected evaluated strategy",
                authority_reference=configuration.qualification_ref,
                disposition=InputDisposition.PROVIDED,
                content=configuration.qualification_ref,
            ),
        ),
    )
    result = _invoke_eligible_model_result(
        gateway,
        ModelExecutionContext(
            execution_envelope_ref=execution_ref,
            manifest=manifest,
            prompt_program_ref=prompt_ref,
            rendering_contract_version="manifest-messages@1",
            output_schema_ref=schema_ref,
            runtime_access_mode=RuntimeAccessMode.NO_EXTERNAL_ACCESS,
            platform_proposal_mode=PlatformProposalMode.NONE,
            requested_model_ref=configuration.model_ref,
            provider_type=configuration.provider_type,
            adapter_version=configuration.adapter_version,
            provider_configuration_fingerprint=(
                configuration.provider_configuration_fingerprint
            ),
            max_output_tokens=configuration.max_output_tokens,
            timeout_milliseconds=configuration.timeout_milliseconds,
            classification=request.classification,
            required_exact_fingerprint=True,
        ),
        stage=stage.lower(),
        max_attempts=max_structured_output_attempts,
    )
    assert result.response is not None
    try:
        value = json.loads(result.response.output_text)
    except json.JSONDecodeError as exc:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            f"{stage.lower()} output is not JSON",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            f"{stage.lower()} output must be an object",
        )
    return value, result


def _invoke_eligible_model_result(
    gateway: ModelGatewayPort,
    context: ModelExecutionContext,
    *,
    stage: str,
    max_attempts: int = _MAX_STRUCTURED_OUTPUT_ATTEMPTS,
) -> ModelGatewayResult:
    """Retry only complete, auditable structured-output rejections."""

    if max_attempts < 1 or max_attempts > _MAX_STRUCTURED_OUTPUT_ATTEMPTS:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "structured-output attempt bound is invalid",
        )
    last_result: ModelGatewayResult | None = None
    for attempt in range(1, max_attempts + 1):
        if attempt == 1:
            attempt_context = context
        else:
            original = context.manifest
            retry_manifest = AuthorizedInputManifest.create(
                capability_id=original.capability_id,
                strategy_ref=original.strategy_ref,
                execution_stage=original.execution_stage,
                calling_module=original.calling_module,
                proposal_vocabulary_ref=original.proposal_vocabulary_ref,
                items=original.items,
            )
            attempt_context = replace(
                context,
                execution_envelope_ref=(
                    f"{context.execution_envelope_ref}:structured-retry:{attempt}"
                ),
                manifest=retry_manifest,
            )
        result = gateway.invoke(attempt_context)
        last_result = result
        if (
            result.eligibility.eligible_for_production_domain_output
            and result.response is not None
        ):
            return result
        response = result.response
        call_failure_code = getattr(result.call, "failure_code", None)
        retryable = (
            call_failure_code == ErrorCode.STRUCTURED_OUTPUT_INVALID.value
            and result.eligibility.reason
            == "MODEL_OUTPUT_REJECTED_STRUCTURED_OUTPUT_INVALID"
            and response is not None
            and bool(response.provider_request_id)
            and bool(response.actual_model_fingerprint)
            and response.usage_complete
            and response.input_tokens is not None
            and response.output_tokens is not None
        )
        if not retryable:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                f"{stage} model result is not eligible for domain output",
                {
                    "eligibility_reason": result.eligibility.reason,
                    "model_failure_code": call_failure_code or "NONE",
                },
            )
    assert last_result is not None
    raise DomainError(
        ErrorCode.STRUCTURED_OUTPUT_INVALID,
        f"{stage} exhausted bounded structured-output retries",
        {
            "attempt_count": max_attempts,
            "last_eligibility_reason": last_result.eligibility.reason,
        },
    )


def _invoke_json_role(
    *,
    gateway: ModelGatewayPort,
    configuration: AgenticModelStrategyConfiguration,
    request: KnowledgeUpdateRequest,
    stage: str,
    capability_id: str,
    strategy_ref: str,
    prompt_ref: str,
    prompt: str,
    schema_ref: str,
    state: Mapping[str, object],
) -> dict[str, object]:
    value, _ = _invoke_json_role_with_result(
        gateway=gateway,
        configuration=configuration,
        request=request,
        stage=stage,
        capability_id=capability_id,
        strategy_ref=strategy_ref,
        prompt_ref=prompt_ref,
        prompt=prompt,
        schema_ref=schema_ref,
        state=state,
    )
    return value


_TOOL = {
    "LIST": SourceTool.LIST,
    "SEARCH": SourceTool.SEARCH,
    "READ": SourceTool.READ,
    "COMPARE": SourceTool.COMPARE,
}
_PARAMETERS = {
    "LIST": ("revision", "cursor", "page_size"),
    "SEARCH": ("revision", "query", "cursor", "page_size"),
    "READ": ("revision", "path", "offset", "max_bytes"),
    "COMPARE": ("base", "revision"),
}


_PLANNED_NEED_FIELDS = frozenset(_PLANNED_NEED_PROPERTIES)
_PLANNED_CONSTRAINT_FIELDS = {"constraint_id", "need_ids", "description"}
_REQUIREMENT_REVIEW_FIELDS = {
    "decision",
    "accepted_need_ids",
    "original_request_preserved",
    "all_material_questions_covered",
    "findings",
}


def _requirement_plan(value: Mapping[str, object]) -> KnowledgeRequirementPlan:
    if set(value) != {"needs", "joint_constraints", "rationale"}:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "requirement proposal does not match the closed contract",
        )
    raw_needs = value.get("needs")
    raw_constraints = value.get("joint_constraints")
    if (
        not isinstance(raw_needs, list)
        or not raw_needs
        or len(raw_needs) > MAX_REQUIREMENT_NEEDS
        or not isinstance(raw_constraints, list)
        or not _nonempty(value.get("rationale"))
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "requirement proposal is incomplete",
        )
    needs = []
    for item in raw_needs:
        if not isinstance(item, dict) or set(item) != _PLANNED_NEED_FIELDS:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "planned Need does not match the closed contract",
            )
        kinds = item.get("required_kinds")
        type_names = item.get("required_type_names")
        terms = item.get("retrieval_terms")
        minimum = item.get("minimum_support_count")
        if (
            not _nonempty(item.get("need_id"))
            or not _nonempty(item.get("question"))
            or not _string_list(kinds, allow_empty=True)
            or not _string_list(type_names, allow_empty=True)
            or bool(type_names)
            or not _string_list(terms, allow_empty=True)
            or len(kinds) != len(set(kinds))
            or any(
                kind not in {enum_kind.value for enum_kind in KnowledgeObjectKind}
                for kind in kinds
            )
            or KnowledgeObjectKind.ENTITY.value in kinds
            or KnowledgeObjectKind.FACT.value not in kinds
            or not isinstance(minimum, int)
            or isinstance(minimum, bool)
            or minimum < 1
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "planned Need contains invalid fields",
            )
        needs.append(
            KnowledgeNeed(
                need_id=item["need_id"],
                question=item["question"],
                required_kinds=tuple(KnowledgeObjectKind(kind) for kind in kinds),
                required_type_names=tuple(type_names),
                required_terms=tuple(terms),
                minimum_support_count=minimum,
            )
        )
    constraints = []
    for item in raw_constraints:
        if (
            not isinstance(item, dict)
            or set(item) != _PLANNED_CONSTRAINT_FIELDS
            or not _nonempty(item.get("constraint_id"))
            or not _string_list(item.get("need_ids"), allow_empty=False)
            or not _nonempty(item.get("description"))
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "planned joint constraint is invalid",
            )
        constraints.append(
            JointConstraint(
                constraint_id=item["constraint_id"],
                need_ids=tuple(item["need_ids"]),
                description=item["description"],
            )
        )
    if len({item.constraint_id for item in constraints}) != len(constraints):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "planned joint constraint IDs must be unique",
        )
    return KnowledgeRequirementPlan(tuple(needs), tuple(constraints))


def _requirement_plan_view(plan: KnowledgeRequirementPlan) -> dict[str, object]:
    return {
        "needs": tuple(
            {
                "need_id": item.need_id,
                "question": item.question,
                "required_kinds": tuple(kind.value for kind in item.required_kinds),
                "required_type_names": item.required_type_names,
                "retrieval_terms": item.required_terms,
                "minimum_support_count": item.minimum_support_count,
            }
            for item in plan.needs
        ),
        "joint_constraints": tuple(
            {
                "constraint_id": item.constraint_id,
                "need_ids": item.need_ids,
                "description": item.description,
            }
            for item in plan.joint_constraints
        ),
    }


def _verify_requirement_review(
    review: Mapping[str, object], plan: KnowledgeRequirementPlan
) -> None:
    accepted = review.get("accepted_need_ids")
    findings = review.get("findings")
    if (
        set(review) != _REQUIREMENT_REVIEW_FIELDS
        or review.get("decision") not in {"ACCEPT", "REJECT"}
        or not _string_list(accepted, allow_empty=True)
        or not _string_list(findings, allow_empty=True)
        or not isinstance(review.get("original_request_preserved"), bool)
        or not isinstance(review.get("all_material_questions_covered"), bool)
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "requirement fidelity review does not match the closed contract",
        )
    expected = {item.need_id for item in plan.needs}
    if (
        review["decision"] != "ACCEPT"
        or review["original_request_preserved"] is not True
        or review["all_material_questions_covered"] is not True
        or set(accepted) != expected
        or len(accepted) != len(expected)
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "requirement proposal failed independent fidelity review",
            {"finding_count": len(findings)},
        )


def _string_list(value: object, *, allow_empty: bool) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_nonempty(item) for item in value)
        and len(value) == len(set(value))
    )


def _answer_draft_plan(
    value: Mapping[str, object], needs: tuple[AnswerNeedEvidence, ...]
) -> AnswerDraftPlan:
    raw = value.get("selections")
    if (
        set(value) != {"selections", "rationale"}
        or not isinstance(raw, list)
        or not _nonempty(value.get("rationale"))
        or len({item.need_id for item in needs}) != len(needs)
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "answer draft output does not match the closed contract",
        )
    needs_by_id = {item.need_id: item for item in needs}
    selections = []
    seen = set()
    for item in raw:
        if (
            not isinstance(item, dict)
            or set(item) != {"need_id", "formal_reference_ids"}
            or item.get("need_id") not in needs_by_id
            or item["need_id"] in seen
            or not _string_list(
                item.get("formal_reference_ids"), allow_empty=True
            )
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "answer draft selection is invalid",
            )
        need = needs_by_id[item["need_id"]]
        known = {
            record.object_id.value: record.object_id
            for record in need.formal_records
            if record.kind is not KnowledgeObjectKind.ENTITY
        }
        references = item["formal_reference_ids"]
        if (
            any(reference not in known for reference in references)
            or (need.status is NeedStatus.SATISFIED and not references)
            or (need.status is not NeedStatus.SATISFIED and references)
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "answer draft selection exceeds its Need support boundary",
            )
        seen.add(item["need_id"])
        selections.append(
            AnswerDraftSelection(
                need_id=item["need_id"],
                formal_references=tuple(known[reference] for reference in references),
            )
        )
    if seen != set(needs_by_id):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "answer draft output does not cover every Need",
        )
    return AnswerDraftPlan(tuple(selections))


def _semantic_answer_review(
    value: Mapping[str, object],
) -> SemanticAnswerReviewDecision:
    if set(value) != {"decision", "failed_dimensions", "findings"}:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "semantic answer review does not match the closed contract",
        )
    decision = value.get("decision")
    dimensions = value.get("failed_dimensions")
    findings = value.get("findings")
    known = {item.value: item for item in ReviewDimension}
    if (
        decision not in {"APPROVE", "REJECT"}
        or not _string_list(dimensions, allow_empty=True)
        or any(item not in known for item in dimensions)
        or not _string_list(findings, allow_empty=True)
        or (decision == "APPROVE" and (dimensions or findings))
        or (decision == "REJECT" and (not dimensions or not findings))
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "semantic answer review decision is invalid",
        )
    return SemanticAnswerReviewDecision(
        approved=decision == "APPROVE",
        failed_dimensions=tuple(known[item] for item in dimensions),
        findings=tuple(findings),
    )


def _proposal(
    value: object,
    *,
    request: KnowledgeUpdateRequest,
    completed_operations: tuple[SourceOperationResult, ...] = (),
) -> SourceActionProposal:
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "source planner output must be an object",
        )
    decision = value.get("decision")
    tool_name = value.get("tool")
    rationale = value.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "source planner rationale is missing",
        )
    rationale = rationale.strip()
    if decision == "STOP":
        identity = dict(request.target.canonical_identity)
        harmless_echoes = {
            "revision": frozenset(
                item
                for item in (identity.get("revision"), identity.get("target"))
                if isinstance(item, str) and item
            ),
            "base": frozenset(
                item
                for item in (identity.get("base"),)
                if isinstance(item, str) and item
            ),
        }
        carries_action = False
        for key in (
            "revision",
            "base",
            "path",
            "query",
            "cursor",
            "offset",
            "max_bytes",
            "page_size",
        ):
            item = value.get(key)
            if not item:
                continue
            if not isinstance(item, str) or item not in harmless_echoes.get(
                key, frozenset()
            ):
                carries_action = True
                break
        if tool_name != "NONE" or carries_action:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "source stop output carries an executable action",
            )
        missing_required_paths = _missing_required_reads(
            request, completed_operations
        )
        if missing_required_paths:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "source planner cannot stop before required revision paths are fully read",
                {"missing_required_paths": missing_required_paths},
            )
        return SourceActionProposal.finish(rationale=rationale)
    if decision != "EXECUTE" or tool_name not in _TOOL:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "source planner decision or tool is invalid",
        )
    parameters = {}
    for key in _PARAMETERS[tool_name]:
        item = value.get(key)
        if item:
            if not isinstance(item, str):
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "source planner parameter is not text",
                )
            parameters[key] = item
    required_parameters = {
        "LIST": ("revision",),
        "SEARCH": ("revision", "query"),
        "READ": ("revision", "path"),
        "COMPARE": ("base", "revision"),
    }
    missing = tuple(
        key for key in required_parameters[tool_name] if key not in parameters
    )
    if missing:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "source planner proposal is missing required parameters: "
            + ", ".join(missing),
        )
    identity = dict(request.target.canonical_identity)
    if tool_name == "COMPARE" and (
        parameters["base"] != identity.get("base")
        or parameters["revision"] != identity.get("target")
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "source planner COMPARE must use the exact authorized base-to-target direction",
            {
                "expected_base": identity.get("base"),
                "expected_revision": identity.get("target"),
                "received_base": parameters["base"],
                "received_revision": parameters["revision"],
            },
        )
    allowed_paths = tuple(getattr(request, "allowed_source_paths", ()))
    empty_search_streak = _consecutive_empty_search_count(
        completed_operations
    )
    if tool_name == "SEARCH" and empty_search_streak >= 2:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "source planner cannot repeat SEARCH after two consecutive empty results; "
            "READ an exact path copied from a prior LIST result or STOP",
            {
                "consecutive_empty_searches": empty_search_streak,
                "required_next_tools": ("READ", "STOP"),
            },
        )
    if (
        tool_name == "READ"
        and allowed_paths
        and parameters["path"] not in allowed_paths
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "source planner READ path must exactly match an allowed path",
        )
    return SourceActionProposal.execute(
        _TOOL[tool_name], parameters, rationale=rationale
    )


def _source_recovery_guidance(
    completed_operations: tuple[SourceOperationResult, ...],
) -> dict[str, object]:
    empty_search_streak = _consecutive_empty_search_count(
        completed_operations
    )
    return {
        "consecutive_empty_searches": empty_search_streak,
        "search_allowed": empty_search_streak < 2,
        "instruction": (
            "After two consecutive empty SEARCH results, choose READ using an exact "
            "path copied from a prior LIST result, or STOP if no authorized evidence "
            "can answer the reviewed Needs. Do not try another query synonym."
        ),
    }


def _consecutive_empty_search_count(
    completed_operations: tuple[SourceOperationResult, ...],
) -> int:
    count = 0
    for operation in reversed(completed_operations):
        observation = operation.observation
        if (
            observation is None
            or observation.tool is not SourceTool.SEARCH
            or observation.item_count != 0
        ):
            break
        count += 1
    return count


def _missing_required_reads(
    request: KnowledgeUpdateRequest,
    completed_operations: tuple[SourceOperationResult, ...],
) -> tuple[dict[str, object], ...]:
    required_paths = tuple(getattr(request, "required_source_paths", ()))
    if not required_paths:
        return ()
    identity = dict(request.target.canonical_identity)
    target_revision = identity.get("target") or identity.get("revision")
    base_revision = identity.get("base")
    revisions = tuple(
        revision
        for revision in (base_revision, target_revision)
        if isinstance(revision, str) and revision
    )
    if not revisions:
        return tuple(
            {"revision": None, "path": path, "next_offset": 0}
            for path in required_paths
        )

    spans_by_revision_path: dict[
        tuple[str, str], list[tuple[int, int, bool]]
    ] = {
        (revision, path): []
        for revision in revisions
        for path in required_paths
    }
    for operation in completed_operations:
        observation = operation.observation
        if (
            observation is None
            or observation.tool is not SourceTool.READ
        ):
            continue
        revision = observation.source_context.repository_revision
        coverage = dict(observation.coverage)
        path = coverage.get("path")
        byte_range = coverage.get("range")
        key = (revision, path)
        if key not in spans_by_revision_path or not isinstance(byte_range, str):
            continue
        prefix = "bytes:"
        if not byte_range.startswith(prefix) or "-" not in byte_range:
            continue
        start_text, end_text = byte_range[len(prefix) :].split("-", 1)
        try:
            start, end = int(start_text), int(end_text)
        except ValueError:
            continue
        if start < 0 or end < start:
            continue
        spans_by_revision_path[key].append((start, end, observation.has_more))

    missing = []
    for revision in revisions:
        for path in required_paths:
            covered_until = 0
            terminal_end: int | None = None
            for start, end, has_more in sorted(
                spans_by_revision_path[(revision, path)]
            ):
                if start > covered_until:
                    break
                covered_until = max(covered_until, end)
                if not has_more:
                    terminal_end = max(terminal_end or 0, end)
            if terminal_end is None or covered_until < terminal_end:
                missing.append(
                    {
                        "revision": revision,
                        "path": path,
                        "next_offset": covered_until,
                    }
                )
    return tuple(missing)


_CANDIDATE_FIELDS = frozenset(_CANDIDATE_PROPERTIES)
_ENTITY_TYPES = frozenset(
    _CANDIDATE_PROPERTIES["entity_type"]["enum"]
)
_FACT_PREDICATES = frozenset(
    _CANDIDATE_PROPERTIES["predicate"]["enum"]
)


def _candidate_views(
    proposal: Mapping[str, object],
    artifacts: tuple[SourceArtifact, ...],
    artifact_origins: Mapping[str, Mapping[str, object]] | None = None,
) -> list[dict[str, object]]:
    raw = proposal.get("candidates")
    limitations = proposal.get("limitations")
    if (
        set(proposal) != {"candidates", "limitations"}
        or not isinstance(raw, list)
        or len(raw) > MAX_FACT_CANDIDATES
        or not isinstance(limitations, list)
        or not all(isinstance(item, str) for item in limitations)
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "fact proposal output does not match the closed contract",
        )
    artifacts_by_id = {item.artifact_id.value: item for item in artifacts}
    candidates = []
    keys = set()
    for index, item in enumerate(raw):
        if isinstance(item, dict):
            item = _normalize_candidate_missing_values(item)
        if (
            not isinstance(item, dict)
            or set(item) != _CANDIDATE_FIELDS
            or not _nonempty(item.get("candidate_key"))
            or item["candidate_key"] in keys
            or item.get("artifact_id") not in artifacts_by_id
            or item.get("entity_type") not in _ENTITY_TYPES
            or item.get("predicate") not in _FACT_PREDICATES
            or not _nonempty(item.get("statement"))
            or _contains_reserved_fact_metadata(item.get("statement"))
            or not isinstance(item.get("line_start"), int)
            or isinstance(item.get("line_start"), bool)
            or not isinstance(item.get("line_end"), int)
            or isinstance(item.get("line_end"), bool)
            or item["line_start"] < 1
            or item["line_end"] < item["line_start"]
            or item.get("condition") is not None
            and not _nonempty(item.get("condition"))
            or _textual_null(item.get("condition"))
            or item.get("limitation") is not None
            and not _nonempty(item.get("limitation"))
            or _textual_null(item.get("limitation"))
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "fact candidate is invalid or references unauthorized source",
                {
                    "candidate_index": index,
                    "candidate_key": (
                        item.get("candidate_key")
                        if isinstance(item, dict)
                        else None
                    ),
                },
            )
        artifact = artifacts_by_id[item["artifact_id"]]
        try:
            _line_byte_range(artifact, item["line_start"], item["line_end"])
        except DomainError as exc:
            if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                raise
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "fact candidate line range is outside its cited artifact",
                {
                    "candidate_index": index,
                    "candidate_key": item["candidate_key"],
                    "artifact_id": artifact.artifact_id.value,
                    "artifact_identity": artifact.source_native_identity,
                    "line_start": item["line_start"],
                    "line_end": item["line_end"],
                    "artifact_line_count": len(
                        artifact.payload.decode("utf-8").splitlines()
                    ),
                },
            ) from exc
        excerpt = _line_excerpt(
            artifact, item["line_start"], item["line_end"]
        )
        missing_constructors = _missing_constructor_mentions(
            excerpt=excerpt,
            statement=item["statement"],
        )
        if missing_constructors:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "fact candidate omits a constructor present in its cited minimal excerpt",
                {
                    "candidate_index": index,
                    "candidate_key": item["candidate_key"],
                    "missing_constructor_types": missing_constructors,
                    "required_action": (
                        "Mention every constructor type in the statement or narrow "
                        "the cited line range so it remains a minimal complete excerpt."
                    ),
                },
            )
        keys.add(item["candidate_key"])
        candidates.append(
            {
                **item,
                "excerpt": excerpt,
                "artifact_identity": artifact.source_native_identity,
                "artifact_content_digest": artifact.content_digest.value,
                "artifact_source_observation": (
                    dict((artifact_origins or {}).get(artifact.artifact_id.value, {}))
                    or None
                ),
            }
        )
    return candidates


def _requested_response_language(objective_description: str) -> str:
    if "回答语言：简体中文。" in objective_description:
        return "zh-CN"
    if "Response language: English." in objective_description:
        return "en"
    return "source-default"


def _validate_candidate_response_language(
    candidates: list[dict[str, object]], response_language: object
) -> None:
    if response_language != "zh-CN":
        return
    mismatched = tuple(
        candidate.get("candidate_key")
        for candidate in candidates
        if isinstance(candidate.get("statement"), str)
        and not any(
            "\u4e00" <= character <= "\u9fff"
            for character in candidate["statement"]
        )
    )
    if mismatched:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Chinese browser request requires Chinese formal fact statements",
            {
                "response_language": "zh-CN",
                "mismatched_candidate_keys": mismatched,
            },
        )


def _missing_constructor_mentions(*, excerpt: str, statement: str) -> tuple[str, ...]:
    """Keep constructor-bearing minimal excerpts semantically complete."""

    constructors = {
        qualified_name.rsplit(".", 1)[-1]
        for qualified_name in re.findall(
            r"\bnew\s+([A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)",
            excerpt,
        )
    }
    if len(constructors) < 2:
        return ()
    return tuple(sorted(name for name in constructors if name not in statement))


def _accepted_candidate_keys(
    review: Mapping[str, object], candidates: list[dict[str, object]]
) -> frozenset[str]:
    if set(review) != {
        "decision",
        "accepted_candidate_keys",
        "all_supported_objective_aspects_covered",
        "findings",
    }:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "fact review output does not match the closed contract",
        )
    decision = review.get("decision")
    accepted = review.get("accepted_candidate_keys")
    coverage_complete = review.get("all_supported_objective_aspects_covered")
    findings = review.get("findings")
    known = {item["candidate_key"] for item in candidates}
    if (
        decision not in {"ACCEPT", "REJECT"}
        or not isinstance(accepted, list)
        or not all(isinstance(item, str) for item in accepted)
        or len(accepted) != len(set(accepted))
        or not set(accepted).issubset(known)
        or not isinstance(findings, list)
        or not all(isinstance(item, str) and item.strip() for item in findings)
        or not isinstance(coverage_complete, bool)
        or (decision == "ACCEPT" and (not accepted or not coverage_complete))
        or (decision == "REJECT" and coverage_complete)
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "fact review decision is invalid",
        )
    return frozenset(accepted) if decision == "ACCEPT" else frozenset()


_SUFFICIENCY_FIELDS = {
    "status",
    "supporting_reference_ids",
    "gap",
    "counterexample_reference_ids",
    "conflict_reference_ids",
    "unknowns",
    "limitations",
    "rationale",
}


def _sufficiency_decision(
    value: object, read_set: KnowledgeReadSet, need: KnowledgeNeed
) -> NeedSufficiencyDecision:
    if not isinstance(value, dict) or set(value) != _SUFFICIENCY_FIELDS:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Need sufficiency output does not match the closed contract",
        )
    records_by_id = {
        item.object_id.value: item for item in read_set.records
    }
    known = {
        reference: record.object_id
        for reference, record in records_by_id.items()
    }
    reference_fields = (
        "supporting_reference_ids",
        "counterexample_reference_ids",
        "conflict_reference_ids",
    )
    text_fields = ("unknowns", "limitations")
    for field in reference_fields:
        items = value.get(field)
        if (
            not isinstance(items, list)
            or not all(isinstance(item, str) for item in items)
            or len(items) != len(set(items))
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "Need sufficiency output contains invalid formal references",
            )
        if any(item not in known for item in items):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Need sufficiency output references knowledge outside its exact read set",
            )
    for field in text_fields:
        items = value.get(field)
        if not isinstance(items, list) or not all(_nonempty(item) for item in items):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "Need sufficiency output contains an invalid disclosure",
            )
    gap = value.get("gap")
    if gap is not None and not _nonempty(gap):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Need sufficiency gap is invalid",
        )
    if not _nonempty(value.get("rationale")):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Need sufficiency rationale is missing",
        )
    try:
        status = NeedStatus(value.get("status"))
    except (TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Need sufficiency status is invalid",
        ) from exc
    supporting = value["supporting_reference_ids"]
    conflicts = value["conflict_reference_ids"]
    unknowns = value["unknowns"]
    if status is NeedStatus.SATISFIED:
        valid_status_fields = (
            len(supporting) >= need.minimum_support_count
            and all(
                records_by_id[item].kind is not KnowledgeObjectKind.ENTITY
                for item in supporting
            )
            and gap is None
            and not value["counterexample_reference_ids"]
            and not conflicts
            and not unknowns
        )
    elif status is NeedStatus.GAP:
        valid_status_fields = not supporting and _nonempty(gap)
    elif status is NeedStatus.CONFLICT:
        valid_status_fields = not supporting and gap is None and bool(conflicts)
    else:
        valid_status_fields = not supporting and gap is None and bool(unknowns)
    if not valid_status_fields:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Need sufficiency status and evidence fields are contradictory",
        )
    return NeedSufficiencyDecision(
        status=status,
        supporting_references=tuple(
            known[item] for item in value["supporting_reference_ids"]
        ),
        gap=gap,
        counterexamples=tuple(
            known[item] for item in value["counterexample_reference_ids"]
        ),
        conflicts=tuple(known[item] for item in value["conflict_reference_ids"]),
        unknowns=tuple(value["unknowns"]),
        limitations=tuple(value["limitations"]),
    )


def _formal_record_view(record: FormalKnowledgeRecord) -> dict[str, object]:
    return {
        "object_id": record.object_id.value,
        "object_digest": record.object_digest.value,
        "kind": record.kind.value,
        "type_name": record.type_name,
        "text": record.text,
        "context_digest": record.context_digest.value,
        "support_references": tuple(
            item.value for item in record.support_references
        ),
    }


def _artifact_view(
    artifact: SourceArtifact,
    source_observation: Mapping[str, object] | None = None,
) -> dict[str, object]:
    try:
        content = artifact.payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "fact proposer input artifact is not UTF-8",
        ) from exc
    return {
        "artifact_id": artifact.artifact_id.value,
        "kind": artifact.artifact_kind,
        "identity": artifact.source_native_identity,
        "source_context_id": artifact.source_context_id.value,
        "content_digest": artifact.content_digest.value,
        "source_observation": dict(source_observation or {}) or None,
        "line_count": len(content.splitlines()),
        "numbered_content": "\n".join(
            f"{ordinal}: {line}"
            for ordinal, line in enumerate(content.splitlines(), 1)
        ),
    }


def _artifact_origins(
    operations: tuple[SourceOperationResult, ...],
) -> dict[str, dict[str, object]]:
    origins: dict[str, dict[str, object]] = {}
    for operation in operations:
        observation = operation.observation
        if observation is None:
            continue
        origin = {
            "tool": observation.tool.value,
            "repository_revision": observation.source_context.repository_revision,
            "subject": observation.source_context.subject,
            "coverage": dict(observation.coverage),
        }
        for artifact in observation.artifacts:
            origins[artifact.artifact_id.value] = origin
    return origins


def _line_byte_range(
    artifact: SourceArtifact, line_start: int, line_end: int
) -> tuple[int, int]:
    try:
        text = artifact.payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "candidate evidence artifact is not UTF-8",
        ) from exc
    lines = text.splitlines(keepends=True)
    if not lines or line_start < 1 or line_end < line_start or line_end > len(lines):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "candidate evidence line range is outside the artifact",
        )
    byte_start = len("".join(lines[: line_start - 1]).encode("utf-8"))
    byte_end = len("".join(lines[:line_end]).encode("utf-8"))
    if byte_end <= byte_start:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "candidate evidence line range is empty",
        )
    return byte_start, byte_end


def _line_excerpt(artifact: SourceArtifact, line_start: int, line_end: int) -> str:
    byte_start, byte_end = _line_byte_range(artifact, line_start, line_end)
    return artifact.payload[byte_start:byte_end].decode("utf-8")


def _manifest_json_item(
    manifest: AuthorizedInputManifest, item_id: str
) -> dict[str, object]:
    matches = [item for item in manifest.items if item.item_id == item_id]
    if len(matches) != 1:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "authorized model input item is missing or duplicated",
        )
    value = json.loads(matches[0].content)
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "authorized model input item is not an object",
        )
    return value


def _fact_text(candidate: Mapping[str, object]) -> str:
    parts = [str(candidate["statement"])]
    if candidate.get("condition"):
        parts.append(f"Condition: {candidate['condition']}")
    if candidate.get("limitation"):
        parts.append(f"Limitation: {candidate['limitation']}")
    return " ".join(parts)


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _contains_reserved_fact_metadata(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.casefold()
    return "condition:" in normalized or "limitation:" in normalized


def _textual_null(value: object) -> bool:
    return isinstance(value, str) and value.casefold() == "null"


def _normalize_candidate_missing_values(
    candidate: Mapping[str, object],
) -> dict[str, object]:
    normalized = dict(candidate)
    for field in ("condition", "limitation"):
        if _textual_null(normalized.get(field)):
            normalized[field] = None
    return normalized


def _operation_view(operation: SourceOperationResult) -> dict[str, object]:
    observation = operation.observation
    return {
        "operation_id": operation.operation_id.value,
        "status": operation.status.value,
        "failure_code": operation.failure_code,
        "observation": (
            {
                "tool": observation.tool.value,
                "repository_revision": (
                    observation.source_context.repository_revision
                ),
                "subject": observation.source_context.subject,
                "coverage": dict(observation.coverage),
                "item_count": observation.item_count,
                "byte_count": observation.byte_count,
                "has_more": observation.has_more,
                "next_cursor": observation.next_cursor,
                "artifacts": [
                    {
                        "artifact_id": artifact.artifact_id.value,
                        "kind": artifact.artifact_kind,
                        "identity": artifact.source_native_identity,
                        "content_digest": artifact.content_digest.value,
                        "truncated": artifact.truncated,
                        "content": artifact.payload.decode(
                            "utf-8", errors="replace"
                        ),
                    }
                    for artifact in observation.artifacts
                ],
            }
            if observation is not None
            else None
        ),
    }
