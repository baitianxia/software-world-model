"""Evaluation-only product composition for qualified WORLD_MODEL answers.

The product interpreter is deliberately generic: it recognizes registered
Structure semantics and public entity identifiers from the mounted no-payload
Bundles.  It contains no product case IDs, project-name branches, Source port,
Evidence payload port, oracle, or baseline reader.  A qualified model proposal
must validate one material decision before the deterministic authority chain can
be delivered.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import re
from typing import Mapping, Protocol, Sequence

from software_world_model.ai_infrastructure.model_egress_gateway import (
    JAVA_MODEL_EGRESS_GATEWAY_ROUTE,
    BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_ROUTE,
    MODEL_EGRESS_GATEWAY_ROUTE,
)
from software_world_model.ai_infrastructure.world_model_answer_strategy import (
    COMPLETE_NEGATIVE_ANSWER,
    ENTITY_CANDIDATE_RESOLUTION,
    GENERIC_QUERY_PLANNING,
    ORDERED_DIFF_EXPRESSION,
    VIEW_LIMITATION_AND_KNOWLEDGE_GAP,
    WorldModelCapabilityProposal,
)
from software_world_model.ai_infrastructure.versioned_world_model_answer_strategy import (
    IMPLEMENTATION_ANSWER_DRAFTING,
    IMPLEMENTATION_ANSWER_REVIEW,
    IMPLEMENTATION_INVESTIGATION,
    JAVA_SOURCE_SEMANTICS_REVIEW_FINDING_CODES,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
    MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT,
)
from software_world_model.application_services.structure_read_bundle import (
    StructureSnapshotReadBundle,
)
from software_world_model.application_services.bounded_world_model_investigation import (
    BoundedInvestigationTrace,
    BoundedWorldModelInvestigationSession,
    InvestigationEntityRef,
    InvestigationOperation,
    InvestigationProposal,
    constrained_investigation_operations,
)
from software_world_model.application_services.structure_view import (
    NeighborhoodDirection,
    StructureViewOperation,
)
from software_world_model.application_services.world_model_answering import (
    QUALIFIED_MODEL_STRATEGY_MODE,
    EntitySelectorOrigin,
    InMemoryWorldModelAuthorityStore,
    InMemoryWorldModelEvaluationSink,
    WorldModelAnswerClaimProposal,
    WorldModelAnswerReviewer,
    WorldModelAnsweringService,
    WorldModelAssessment,
    WorldModelAuthorityChain,
    WorldModelClaimKind,
    WorldModelDraftGenerator,
    WorldModelDraftProposal,
    WorldModelEntitySelectorProposal,
    WorldModelGapProposal,
    WorldModelGapReason,
    WorldModelJointConstraint,
    WorldModelJointConstraintKind,
    WorldModelNeed,
    WorldModelNeedOutcome,
    WorldModelQueryPlan,
    WorldModelQueryPlanProposal,
    WorldModelQueryPlanner,
    WorldModelQueryResultSet,
    WorldModelQueryStepProposal,
    WorldModelRequirementFidelityProposal,
    WorldModelRequirementFidelityReviewer,
    WorldModelRequirementPlanner,
    WorldModelRequirementProposal,
    WorldModelRequirementRevision,
    WorldModelResponseControlService,
    WorldModelReviewDecision,
    WorldModelReviewDimension,
    WorldModelReviewDimensionAssessment,
    WorldModelReviewProposal,
    WorldModelStrategyInvocation,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    EntityType,
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    JAVA_STATIC_CALL_PROFILE_REF,
    MAVEN_STRUCTURE_PROFILE_REF,
    RelationPredicate,
)


PRODUCT_STRATEGY_REF = MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_ref
JAVA_PRODUCT_STRATEGY_REF = JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_ref
JAVA_SOURCE_SEMANTICS_PRODUCT_STRATEGY_REF = (
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_ref
)
PRODUCT_GAP_REASON = "CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE"
_EXPLICIT_ARTIFACT_MENTION = re.compile(
    r"`([A-Za-z0-9][A-Za-z0-9._-]{0,127})`"
)


class ProductNeedKind(str, Enum):
    INVENTORY = "INVENTORY"
    METHOD_INVENTORY = "METHOD_INVENTORY"
    PATHS = "PATHS"
    NEW_PATHS = "NEW_PATHS"
    ORDERED_DIFF = "ORDERED_DIFF"
    DIRECT_DEPENDENCY = "DIRECT_DEPENDENCY"
    DIRECT_CALL = "DIRECT_CALL"
    SAME_NAME_IDENTITY = "SAME_NAME_IDENTITY"
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"


@dataclass(frozen=True, slots=True)
class ProductCatalogEntity:
    snapshot_id: StableId
    entity_root_id: StableId
    entity_state_id: StableId
    entity_type: EntityType
    mention: str
    artifact_id: str
    canonical_ga: str | None
    canonical_gav: str | None
    public_aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProductMentionGroup:
    token: str
    first_offset: int
    entity_root_ids: tuple[StableId, ...]


@dataclass(frozen=True, slots=True)
class ProductNeedSpec:
    need_id: str
    kind: ProductNeedKind
    snapshot_ordinals: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ProductQuestionAnalysis:
    needs: tuple[ProductNeedSpec, ...]
    module_mentions: tuple[ProductMentionGroup, ...]
    path_endpoints: tuple[StableId, StableId] | None
    direct_source_root_id: StableId | None
    direct_target_root_ids: tuple[StableId, ...]
    include_state_changes: bool
    uses_ordered_diff: bool


class ProductCapabilityProposalPort(Protocol):
    def propose(
        self,
        *,
        case_id: str,
        capability: str,
        sealed_input: object,
        available_operations: tuple[str, ...] = (),
    ) -> WorldModelCapabilityProposal: ...


class ProductGatewayCounters(Protocol):
    @property
    def provider_call_count(self) -> int: ...

    @property
    def network_operation_count(self) -> int: ...


@dataclass(frozen=True, slots=True)
class ProductWorldModelExecution:
    chain: WorldModelAuthorityChain
    model_proposals: tuple[WorldModelCapabilityProposal, ...]


class ProductBundleCatalog:
    """Public, no-payload entity catalog derived from exact Snapshot Bundles."""

    def __init__(
        self, snapshot_bundles: Sequence[StructureSnapshotReadBundle]
    ) -> None:
        bundles = tuple(snapshot_bundles)
        if not bundles:
            raise _invalid("PRODUCT_BUNDLE_SET_EMPTY", "product Bundle set is empty")
        for bundle in bundles:
            bundle.require_valid()
        if len({item.snapshot_id for item in bundles}) != len(bundles):
            raise _invalid(
                "PRODUCT_BUNDLE_SET_DUPLICATE",
                "product Bundle set repeats a Snapshot",
            )
        self._snapshot_ids = tuple(item.snapshot_id for item in bundles)
        profiles = {
            coverage.root.profile_ref
            for bundle in bundles
            for coverage in bundle.coverages
        }
        if len(profiles) != 1:
            raise _invalid(
                "PRODUCT_PROFILE_SET_INVALID",
                "product Read Set must bind one exact knowledge profile",
            )
        self._profile_ref = next(iter(profiles))
        if self._profile_ref not in {
            MAVEN_STRUCTURE_PROFILE_REF,
            JAVA_STATIC_CALL_PROFILE_REF,
            JAVA_SOURCE_SEMANTICS_PROFILE_REF,
        }:
            raise _invalid(
                "PRODUCT_PROFILE_UNSUPPORTED",
                "product Read Set profile is unsupported",
            )
        entries: list[ProductCatalogEntity] = []
        for bundle in bundles:
            for record in bundle.entities:
                root = record.root.root_fields
                state = record.state.state_payload_fields
                entity_type = record.root.entity_type
                if entity_type is EntityType.SOFTWARE_SYSTEM:
                    artifact = _field_text(state, "artifact_id")
                    label = _field_text(state, "label")
                    system_key = _field_text(root, "canonical_system_key")
                    aliases = _aliases(
                        (artifact, label, system_key, "root", "root pom", "根 pom", "根项目")
                    )
                    ga = None
                    gav = None
                    mention = label
                elif entity_type is EntityType.MAVEN_MODULE:
                    group = _field_text(root, "effective_group_id")
                    artifact = _field_text(root, "artifact_id")
                    version = _field_text(state, "effective_version")
                    label = _field_text(state, "label")
                    module_path = _field_text(state, "module_path")
                    ga = f"{group}:{artifact}"
                    gav = f"{ga}:{version}"
                    aliases = _aliases(
                        (
                            gav,
                            ga,
                            artifact,
                            label,
                            module_path,
                            f"{group.rsplit('.', 1)[-1]} {artifact}",
                            *_identifier_parts(artifact),
                        )
                    )
                    mention = artifact
                elif entity_type is EntityType.JAVA_TYPE:
                    qualified_name = _field_text(root, "qualified_name")
                    simple_name = _field_text(state, "simple_name")
                    source_path = _field_text(state, "source_path")
                    artifact = simple_name
                    ga = None
                    gav = None
                    aliases = _aliases(
                        (qualified_name, simple_name, source_path)
                    )
                    mention = qualified_name
                elif entity_type is EntityType.JAVA_METHOD:
                    declaring_type = _field_text(
                        root, "declaring_type_qualified_name"
                    )
                    method_name = _field_text(root, "method_name")
                    parameters = _field_text_tuple(root, "parameter_types")
                    simple_type = declaring_type.rsplit(".", 1)[-1]
                    parameter_text = ",".join(parameters)
                    signature = (
                        f"{declaring_type}#{method_name}({parameter_text})"
                    )
                    simple_signature = f"{method_name}({parameter_text})"
                    artifact = method_name
                    ga = None
                    gav = None
                    aliases = _aliases(
                        (
                            signature,
                            simple_signature,
                            method_name,
                            f"{simple_type}#{simple_signature}",
                            f"{simple_type}.{simple_signature}",
                        )
                    )
                    mention = signature
                else:
                    continue
                entries.append(
                    ProductCatalogEntity(
                        snapshot_id=bundle.snapshot_id,
                        entity_root_id=record.root_id,
                        entity_state_id=record.state_id,
                        entity_type=entity_type,
                        mention=mention,
                        artifact_id=artifact,
                        canonical_ga=ga,
                        canonical_gav=gav,
                        public_aliases=aliases,
                    )
                )
        self._entries = tuple(entries)
        self._by_snapshot_root = {
            (item.snapshot_id, item.entity_root_id): item for item in self._entries
        }
        for snapshot_id in self._snapshot_ids:
            if self._profile_ref == MAVEN_STRUCTURE_PROFILE_REF and len(
                self.entities(snapshot_id, EntityType.SOFTWARE_SYSTEM)
            ) != 1:
                raise _invalid(
                    "PRODUCT_SYSTEM_ROOT_NOT_UNIQUE",
                    "every product Snapshot must contain one SOFTWARE_SYSTEM",
                )
            if self._profile_ref in {
                JAVA_STATIC_CALL_PROFILE_REF,
                JAVA_SOURCE_SEMANTICS_PROFILE_REF,
            } and not self.entities(snapshot_id, EntityType.JAVA_TYPE):
                raise _invalid(
                    "PRODUCT_JAVA_TYPE_SET_EMPTY",
                    "every Java product Snapshot must contain at least one JAVA_TYPE",
                )

    @property
    def snapshot_ids(self) -> tuple[StableId, ...]:
        return self._snapshot_ids

    @property
    def profile_ref(self) -> str:
        return self._profile_ref

    @property
    def graph_predicate(self) -> RelationPredicate:
        return (
            RelationPredicate.CALLS
            if self._profile_ref
            in {
                JAVA_STATIC_CALL_PROFILE_REF,
                JAVA_SOURCE_SEMANTICS_PROFILE_REF,
            }
            else RelationPredicate.DEPENDS_ON
        )

    def entities(
        self, snapshot_id: StableId, entity_type: EntityType
    ) -> tuple[ProductCatalogEntity, ...]:
        return tuple(
            item
            for item in self._entries
            if item.snapshot_id == snapshot_id and item.entity_type is entity_type
        )

    def system(self, snapshot_id: StableId) -> ProductCatalogEntity:
        return self.entities(snapshot_id, EntityType.SOFTWARE_SYSTEM)[0]

    def entry(
        self, snapshot_id: StableId, root_id: StableId
    ) -> ProductCatalogEntity:
        try:
            return self._by_snapshot_root[(snapshot_id, root_id)]
        except KeyError as exc:
            raise _invalid(
                "PRODUCT_ENTITY_OUTSIDE_READ_SET",
                "product Entity is outside the mounted Read Set",
            ) from exc

    def display_ref(self, root_id: StableId) -> str:
        candidates = tuple(
            item for item in self._entries if item.entity_root_id == root_id
        )
        if not candidates:
            raise _invalid(
                "PRODUCT_ENTITY_OUTSIDE_READ_SET",
                "product Entity is outside the mounted Read Set",
            )
        value = candidates[-1]
        return value.canonical_ga or value.mention

    def entity_type_for_root(self, root_id: StableId) -> EntityType:
        types = {
            item.entity_type
            for item in self._entries
            if item.entity_root_id == root_id
        }
        if len(types) != 1:
            raise _invalid(
                "PRODUCT_ENTITY_TYPE_UNRESOLVED",
                "product Entity Root does not resolve to one public type",
            )
        return next(iter(types))

    def mentioned_modules(
        self, question: str
    ) -> tuple[ProductMentionGroup, ...]:
        normalized = question.casefold()
        candidates: dict[str, set[StableId]] = {}
        offsets: dict[str, int] = {}
        mention_types = (
            {EntityType.JAVA_TYPE, EntityType.JAVA_METHOD}
            if self._profile_ref
            in {
                JAVA_STATIC_CALL_PROFILE_REF,
                JAVA_SOURCE_SEMANTICS_PROFILE_REF,
            }
            else {EntityType.MAVEN_MODULE}
        )
        for item in self._entries:
            if item.entity_type not in mention_types:
                continue
            for alias in item.public_aliases:
                offset = _alias_offset(normalized, alias.casefold())
                if offset is None:
                    continue
                candidates.setdefault(alias, set()).add(item.entity_root_id)
                offsets[alias] = min(offsets.get(alias, offset), offset)
        groups = [
            ProductMentionGroup(
                token=token,
                first_offset=offsets[token],
                entity_root_ids=tuple(sorted(roots, key=lambda item: item.value)),
            )
            for token, roots in candidates.items()
            if len(roots) <= 2
        ]
        groups.sort(key=lambda item: (-len(item.token), item.first_offset, item.token))
        selected: list[ProductMentionGroup] = []
        covered_spans: list[tuple[int, int]] = []
        for group in groups:
            span = (group.first_offset, group.first_offset + len(group.token))
            if any(
                start <= span[0] and span[1] <= end
                for start, end in covered_spans
            ):
                continue
            selected.append(group)
            covered_spans.append(span)
        return tuple(
            sorted(
                selected,
                key=lambda item: (item.first_offset, -len(item.token), item.token),
            )
        )

    def roots_for_artifact(self, artifact_id: str) -> tuple[StableId, ...]:
        return tuple(
            sorted(
                {
                    item.entity_root_id
                    for item in self._entries
                    if item.entity_type is EntityType.MAVEN_MODULE
                    and item.artifact_id == artifact_id
                },
                key=lambda item: item.value,
            )
        )


class ProductQuestionInterpreter:
    """Map natural questions to the closed Structure operation vocabulary."""

    def __init__(self, catalog: ProductBundleCatalog) -> None:
        self._catalog = catalog

    def analyze(self, question: str) -> ProductQuestionAnalysis:
        text = _text(question, "product question")
        if self._catalog.profile_ref == JAVA_SOURCE_SEMANTICS_PROFILE_REF:
            raise _invalid(
                "PRODUCT_SEMANTICS_FIXED_INTERPRETER_FORBIDDEN",
                "Java implementation questions require the generic model Plan chain",
            )
        if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF:
            return self._analyze_java(text)
        folded = text.casefold()
        snapshots = self._catalog.snapshot_ids
        mentions = list(self._catalog.mentioned_modules(text))
        for match in _EXPLICIT_ARTIFACT_MENTION.finditer(text):
            token = match.group(1)
            mentions = [
                item
                for item in mentions
                if item.token.casefold() != token.casefold()
            ]
            roots = tuple(
                sorted(
                    {
                        item.entity_root_id
                        for item in self._catalog.entities(
                            snapshots[-1], EntityType.MAVEN_MODULE
                        )
                        if item.artifact_id == token
                    },
                    key=lambda item: item.value,
                )
            )
            mentions.append(
                ProductMentionGroup(
                    token=token,
                    first_offset=match.start(1),
                    entity_root_ids=roots,
                )
            )
        mentions = sorted(
            mentions,
            key=lambda item: (item.first_offset, -len(item.token), item.token),
        )
        mentions = tuple(mentions)
        unique_mentions = tuple(
            item for item in mentions if len(item.entity_root_ids) == 1
        )
        why = _contains_any(folded, ("为什么", "设计动机", "why ", "reason for"))
        inventory_subject = _contains_any(
            folded,
            (
                "child module",
                "child modules",
                "子模块",
                "子项目",
                "modules 递归",
                "reactor 内的模块",
            ),
        )
        inventory = inventory_subject and _contains_any(
            folded,
            ("列出", "哪些", "有哪些", "各自", "inventory", "return all"),
        )
        path_word = _contains_any(
            folded,
            ("路径", "路线", "path", "走到", "能不能从", "可达", "reachable"),
        )
        direct = _contains_any(
            folded,
            (
                "直接依赖",
                "直接声明",
                "是否直接",
                "directly depend",
                "direct dependency",
                "dependencies 中直接",
                "dependency management",
                "dependencymanagement",
                "形成边",
                "的边是否存在",
            ),
        )
        same_name = _contains_any(
            folded, ("同名", "same artifact", "same-name", "same name")
        )
        change_requested = len(snapshots) >= 2 and _contains_any(
            folded,
            (
                "变化",
                "新增",
                "增删",
                "才有的",
                "new path",
                "new node",
                "added node",
                "state 变化",
            ),
        )
        ordered_diff = len(snapshots) >= 2 and _contains_any(
            folded,
            (
                "图变化",
                "图差异",
                "节点、边",
                "节点和边",
                "节点与边",
                "成员及",
                "边的增删",
                "state 变化",
                "state changes",
                "graph change",
                "graph diff",
                "added node",
                "新增节点",
            ),
        )
        include_state = _contains_any(
            folded,
            ("state", "label", "version", "版本 state", "标签", "版本变化"),
        )
        if why:
            return ProductQuestionAnalysis(
                needs=(
                    ProductNeedSpec(
                        "knowledge-gap",
                        ProductNeedKind.KNOWLEDGE_GAP,
                        (),
                    ),
                ),
                module_mentions=mentions,
                path_endpoints=None,
                direct_source_root_id=None,
                direct_target_root_ids=(),
                include_state_changes=False,
                uses_ordered_diff=False,
            )

        path_endpoints: tuple[StableId, StableId] | None = None
        if path_word and len(unique_mentions) >= 2:
            path_endpoints = (
                unique_mentions[0].entity_root_ids[0],
                unique_mentions[1].entity_root_ids[0],
            )
        elif path_word and not change_requested:
            raise _invalid(
                "PRODUCT_PATH_ENDPOINTS_UNRESOLVED",
                "path question does not identify two unique module Entities",
            )

        root_subject = _contains_any(
            folded, ("根 pom", "root pom", "根项目", "root project")
        )
        direct_source: StableId | None = None
        direct_targets: tuple[StableId, ...] = ()
        if direct:
            if root_subject:
                direct_source = self._catalog.system(snapshots[-1]).entity_root_id
            elif unique_mentions:
                direct_source = unique_mentions[0].entity_root_ids[0]
            else:
                raise _invalid(
                    "PRODUCT_DIRECT_SOURCE_UNRESOLVED",
                    "direct-dependency question has no unique source Entity",
                )
            target_roots = {
                root
                for group in mentions
                for root in group.entity_root_ids
                if root != direct_source
            }
            direct_targets = tuple(sorted(target_roots, key=lambda item: item.value))

        needs: list[ProductNeedSpec] = []
        if inventory:
            for ordinal in range(len(snapshots)):
                needs.append(
                    ProductNeedSpec(
                        f"inventory-{ordinal}",
                        ProductNeedKind.INVENTORY,
                        (ordinal,),
                    )
                )
        if path_endpoints is not None:
            for ordinal in range(len(snapshots)):
                needs.append(
                    ProductNeedSpec(
                        f"paths-{ordinal}",
                        ProductNeedKind.PATHS,
                        (ordinal,),
                    )
                )
            if change_requested:
                needs.append(
                    ProductNeedSpec(
                        "new-paths",
                        ProductNeedKind.NEW_PATHS,
                        tuple(range(len(snapshots))),
                    )
                )
        if ordered_diff:
            needs.append(
                ProductNeedSpec(
                    "ordered-diff",
                    ProductNeedKind.ORDERED_DIFF,
                    (0, 1),
                )
            )
        if direct:
            needs.append(
                ProductNeedSpec(
                    "direct-dependency",
                    ProductNeedKind.DIRECT_DEPENDENCY,
                    (len(snapshots) - 1,),
                )
            )
        elif same_name:
            needs.append(
                ProductNeedSpec(
                    "same-name-identity",
                    ProductNeedKind.SAME_NAME_IDENTITY,
                    (len(snapshots) - 1,),
                )
            )
        if not needs:
            needs.append(
                ProductNeedSpec(
                    "knowledge-gap",
                    ProductNeedKind.KNOWLEDGE_GAP,
                    (),
                )
            )
        return ProductQuestionAnalysis(
            needs=tuple(needs),
            module_mentions=mentions,
            path_endpoints=path_endpoints,
            direct_source_root_id=direct_source,
            direct_target_root_ids=direct_targets,
            include_state_changes=include_state,
            uses_ordered_diff=ordered_diff,
        )

    def _analyze_java(self, text: str) -> ProductQuestionAnalysis:
        folded = text.casefold()
        snapshots = self._catalog.snapshot_ids
        mentions = self._catalog.mentioned_modules(text)
        unique = tuple(
            item for item in mentions if len(item.entity_root_ids) == 1
        )
        type_mentions = tuple(
            item
            for item in unique
            if self._catalog.entity_type_for_root(item.entity_root_ids[0])
            is EntityType.JAVA_TYPE
        )
        method_mentions = tuple(
            item
            for item in unique
            if self._catalog.entity_type_for_root(item.entity_root_ids[0])
            is EntityType.JAVA_METHOD
        )
        unsupported = _contains_any(
            folded,
            (
                "为什么",
                "设计动机",
                "why ",
                "reason for",
                "运行时",
                "实际运行",
                "runtime dispatch",
                "dynamic dispatch",
                "反射",
                "reflection",
                "依赖注入",
                "dependency injection",
            ),
        )
        if unsupported:
            return ProductQuestionAnalysis(
                needs=(
                    ProductNeedSpec(
                        "knowledge-gap", ProductNeedKind.KNOWLEDGE_GAP, ()
                    ),
                ),
                module_mentions=mentions,
                path_endpoints=None,
                direct_source_root_id=None,
                direct_target_root_ids=(),
                include_state_changes=False,
                uses_ordered_diff=False,
            )

        inventory = bool(type_mentions) and _contains_any(
            folded,
            (
                "哪些方法",
                "所有方法",
                "方法清单",
                "methods",
                "method inventory",
                "declared methods",
            ),
        )
        path_word = _contains_any(
            folded,
            ("调用路径", "路径", "call path", "reachable", "可达"),
        )
        direct = _contains_any(
            folded,
            (
                "直接调用",
                "调用哪些",
                "direct call",
                "directly call",
                "calls directly",
            ),
        )
        change_requested = len(snapshots) >= 2 and _contains_any(
            folded,
            ("变化", "新增", "增删", "才有的", "new path", "added"),
        )
        ordered_diff = len(snapshots) >= 2 and _contains_any(
            folded,
            (
                "调用图变化",
                "调用图差异",
                "图变化",
                "图差异",
                "graph change",
                "graph diff",
                "节点和边",
                "节点、边",
            ),
        )
        include_state = _contains_any(
            folded, ("state", "返回类型", "可见性", "return type", "visibility")
        )

        path_endpoints: tuple[StableId, StableId] | None = None
        if path_word:
            if len(method_mentions) < 2 and not change_requested:
                raise _invalid(
                    "PRODUCT_PATH_ENDPOINTS_UNRESOLVED",
                    "call-path question does not identify two unique Java methods",
                )
            if len(method_mentions) >= 2:
                path_endpoints = (
                    method_mentions[0].entity_root_ids[0],
                    method_mentions[1].entity_root_ids[0],
                )

        direct_source: StableId | None = None
        direct_targets: tuple[StableId, ...] = ()
        if inventory:
            direct_source = type_mentions[0].entity_root_ids[0]
        elif direct:
            if not method_mentions:
                raise _invalid(
                    "PRODUCT_DIRECT_SOURCE_UNRESOLVED",
                    "direct-call question has no unique Java method source",
                )
            direct_source = method_mentions[0].entity_root_ids[0]
            direct_targets = tuple(
                sorted(
                    {
                        group.entity_root_ids[0]
                        for group in method_mentions[1:]
                    },
                    key=lambda item: item.value,
                )
            )

        needs: list[ProductNeedSpec] = []
        if inventory:
            for ordinal in range(len(snapshots)):
                needs.append(
                    ProductNeedSpec(
                        f"method-inventory-{ordinal}",
                        ProductNeedKind.METHOD_INVENTORY,
                        (ordinal,),
                    )
                )
        if path_endpoints is not None:
            for ordinal in range(len(snapshots)):
                needs.append(
                    ProductNeedSpec(
                        f"paths-{ordinal}", ProductNeedKind.PATHS, (ordinal,)
                    )
                )
            if change_requested:
                needs.append(
                    ProductNeedSpec(
                        "new-paths",
                        ProductNeedKind.NEW_PATHS,
                        tuple(range(len(snapshots))),
                    )
                )
        if ordered_diff:
            needs.append(
                ProductNeedSpec(
                    "ordered-diff", ProductNeedKind.ORDERED_DIFF, (0, 1)
                )
            )
        if direct:
            needs.append(
                ProductNeedSpec(
                    "direct-call",
                    ProductNeedKind.DIRECT_CALL,
                    (len(snapshots) - 1,),
                )
            )
        if not needs:
            needs.append(
                ProductNeedSpec(
                    "knowledge-gap", ProductNeedKind.KNOWLEDGE_GAP, ()
                )
            )
        return ProductQuestionAnalysis(
            needs=tuple(needs),
            module_mentions=mentions,
            path_endpoints=path_endpoints,
            direct_source_root_id=direct_source,
            direct_target_root_ids=direct_targets,
            include_state_changes=include_state,
            uses_ordered_diff=ordered_diff,
        )


class ProductRequirementPlanner(WorldModelRequirementPlanner):
    strategy_ref = "iter-003-g3b-generic-requirement-planner@1"

    def __init__(self, interpreter: ProductQuestionInterpreter) -> None:
        self._interpreter = interpreter

    def plan(
        self,
        *,
        question,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelRequirementProposal:
        analysis = self._interpreter.analyze(question.original_question)
        needs = tuple(
            WorldModelNeed(
                need_id=item.need_id,
                question=_need_question(item),
            )
            for item in analysis.needs
        )
        constraints: tuple[WorldModelJointConstraint, ...] = ()
        ordered_comparison = any(
            item.kind
            in {ProductNeedKind.NEW_PATHS, ProductNeedKind.ORDERED_DIFF}
            for item in analysis.needs
        )
        if len(needs) > 1 or ordered_comparison:
            if ordered_comparison:
                if len(question.read_authority.snapshot_ids) < 2:
                    raise _invalid(
                        "PRODUCT_ORDERED_READ_SET_MISSING",
                        "ordered comparison requires two Snapshots",
                    )
                constraints = (
                    WorldModelJointConstraint(
                        constraint_id="ordered-read-set",
                        need_ids=tuple(item.need_id for item in needs),
                        kind=WorldModelJointConstraintKind.ORDERED_READ_SET,
                        description="Preserve the caller-declared base-to-target Snapshot order.",
                        base_snapshot_id=question.read_authority.snapshot_ids[0],
                        target_snapshot_id=question.read_authority.snapshot_ids[1],
                    ),
                )
            else:
                constraints = (
                    WorldModelJointConstraint(
                        constraint_id="all-needs",
                        need_ids=tuple(item.need_id for item in needs),
                        kind=WorldModelJointConstraintKind.ALL_NEEDS,
                        description="Every material sub-question must be answered together.",
                    ),
                )
        return WorldModelRequirementProposal(
            original_question=question.original_question,
            response_language=question.response_language,
            needs=needs,
            joint_constraints=constraints,
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class ProductRequirementReviewer(WorldModelRequirementFidelityReviewer):
    strategy_ref = "iter-003-g3b-independent-requirement-reviewer@1"

    def __init__(self, interpreter: ProductQuestionInterpreter) -> None:
        self._interpreter = interpreter

    def review(
        self,
        *,
        question,
        proposal: WorldModelRequirementProposal,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelRequirementFidelityProposal:
        expected = self._interpreter.analyze(question.original_question)
        expected_ids = tuple(item.need_id for item in expected.needs)
        actual_ids = tuple(item.need_id for item in proposal.needs)
        expected_constraints = tuple(
            item.constraint_id for item in proposal.joint_constraints
        )
        approved = (
            proposal.original_question == question.original_question
            and proposal.response_language == question.response_language
            and actual_ids == expected_ids
        )
        return WorldModelRequirementFidelityProposal(
            decision=(
                WorldModelReviewDecision.APPROVE
                if approved
                else WorldModelReviewDecision.REJECT
            ),
            accepted_need_ids=actual_ids if approved else (),
            accepted_constraint_ids=expected_constraints if approved else (),
            original_question_preserved=approved,
            all_material_questions_covered=approved,
            findings=() if approved else ("PRODUCT_REQUIREMENT_MISMATCH",),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class _ProductModelProposalRecorder:
    """Collect isolated provider proposals in exact execution order."""

    def __init__(self) -> None:
        self._items: list[WorldModelCapabilityProposal] = []

    def append(self, proposal: WorldModelCapabilityProposal) -> None:
        self._items.append(proposal)

    @property
    def proposals(self) -> tuple[WorldModelCapabilityProposal, ...]:
        return tuple(self._items)


class JavaSourceSemanticsRequirementPlanner(WorldModelRequirementPlanner):
    """Preserve a free-form implementation question without classifying it."""

    strategy_ref = "iter-007-generic-implementation-requirement@1"

    def plan(
        self,
        *,
        question,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelRequirementProposal:
        return WorldModelRequirementProposal(
            original_question=question.original_question,
            response_language=question.response_language,
            needs=(
                WorldModelNeed(
                    need_id="implementation-answer",
                    question=(
                        "Answer the caller's implementation question from the exact "
                        "typed Java semantics Read Set, or disclose a bounded Gap."
                    ),
                ),
            ),
            joint_constraints=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class JavaSourceSemanticsRequirementReviewer(
    WorldModelRequirementFidelityReviewer
):
    strategy_ref = "iter-007-generic-implementation-requirement-review@1"

    def review(
        self,
        *,
        question,
        proposal: WorldModelRequirementProposal,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelRequirementFidelityProposal:
        expected_need_ids = ("implementation-answer",)
        actual_need_ids = tuple(item.need_id for item in proposal.needs)
        approved = (
            proposal.original_question == question.original_question
            and proposal.response_language == question.response_language
            and actual_need_ids == expected_need_ids
            and proposal.joint_constraints == ()
        )
        return WorldModelRequirementFidelityProposal(
            decision=(
                WorldModelReviewDecision.APPROVE
                if approved
                else WorldModelReviewDecision.REJECT
            ),
            accepted_need_ids=actual_need_ids if approved else (),
            accepted_constraint_ids=(),
            original_question_preserved=approved,
            all_material_questions_covered=approved,
            findings=() if approved else ("IMPLEMENTATION_REQUIREMENT_MISMATCH",),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class JavaSourceSemanticsQueryPlanner(WorldModelQueryPlanner):
    """Run a bounded result-driven investigation, then seal its replay Plan."""

    execution_mode = QUALIFIED_MODEL_STRATEGY_MODE

    def __init__(
        self,
        *,
        model_strategy: ProductCapabilityProposalPort,
        recorder: _ProductModelProposalRecorder,
        strategy_ref: str,
        provider_route: str,
        view,
    ) -> None:
        self._model = model_strategy
        self._recorder = recorder
        self.strategy_ref = strategy_ref
        self.provider_route = provider_route
        self._view = view

    def plan(
        self,
        *,
        question,
        requirement: WorldModelRequirementRevision,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelQueryPlanProposal:
        need_ids = tuple(item.need_id for item in requirement.needs)
        if need_ids != ("implementation-answer",):
            raise _invalid(
                "PRODUCT_IMPLEMENTATION_REQUIREMENT_INVALID",
                "implementation Plan requires the one preserved free-form Need",
            )
        session = BoundedWorldModelInvestigationSession(
            view=self._view,
            question_digest=question.digest,
            need_ids=need_ids,
        )
        previous_result: object = None
        previous_progress: object = None
        while not session.terminal:
            step_index = session.model_call_count + 1
            sealed_input = {
                "original_question": question.original_question,
                "response_language": question.response_language,
                "need_key": need_ids[0],
                "read_authority": question.read_authority.canonical_value(),
                "profile_ref": JAVA_SOURCE_SEMANTICS_PROFILE_REF,
                "step_index": step_index,
                "trace_digest": session.trace_digest.value,
                "previous_result": previous_result,
                "progress_receipt": previous_progress,
                "remaining_budget": {
                    "model_calls": 4 - session.model_call_count,
                    "execution_steps": 4 - len(session.steps),
                },
            }
            available_operations = constrained_investigation_operations(
                sealed_input=sealed_input
            )
            model_proposal = self._model.propose(
                case_id=(
                    f"product:{question.request_ref}:investigation:{step_index}"
                ),
                capability=IMPLEMENTATION_INVESTIGATION,
                sealed_input=sealed_input,
                available_operations=available_operations,
            )
            self._recorder.append(model_proposal)
            normalized = getattr(model_proposal, "normalized_result", None)
            if not isinstance(normalized, Mapping):
                raise _invalid(
                    "PRODUCT_INVESTIGATION_MODEL_OUTPUT_INVALID",
                    "investigation model returned no closed normalized proposal",
                )
            model_digest = getattr(model_proposal, "digest", None)
            if not isinstance(model_digest, Digest):
                model_digest = digest_of(
                    [
                        "PRODUCT_INVESTIGATION_MODEL_PROPOSAL@1",
                        step_index,
                        normalized,
                    ]
                )
            typed_proposal = InvestigationProposal.from_mapping(
                normalized,
                model_proposal_digest=model_digest,
            )
            executed = session.submit(typed_proposal)
            if executed is not None:
                previous_result = {
                    "operation": executed.proposal.operation.value,
                    "results": tuple(
                        _plain_canonical(item.canonical_value())
                        for item in executed.results
                    ),
                    "evidence_requests": [
                        item.canonical_value()
                        for item in executed.proposal.evidence_requests
                    ],
                }
                previous_progress = {
                    "progress_token": executed.progress_token.value,
                    "query_bytes": executed.query_bytes,
                    "result_bytes": executed.result_bytes,
                    "support_item_count": executed.support_item_count,
                    "completeness": (
                        session.current_completeness.canonical_value()
                    ),
                }
        trace = session.seal()
        selectors, steps = _investigation_query_plan(trace, need_ids)
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=(
                requirement.read_authority.ordered_bundle_digest
            ),
            selectors=selectors,
            steps=steps,
            explicit_gaps=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
            investigation_trace=trace,
        )


class JavaSourceSemanticsDraftGenerator(WorldModelDraftGenerator):
    """Generate one answer Claim from the sealed investigation and Results."""

    execution_mode = QUALIFIED_MODEL_STRATEGY_MODE

    def __init__(
        self,
        *,
        model_strategy: ProductCapabilityProposalPort,
        recorder: _ProductModelProposalRecorder,
        strategy_ref: str,
        provider_route: str,
    ) -> None:
        self._model = model_strategy
        self._recorder = recorder
        self.strategy_ref = strategy_ref
        self.provider_route = provider_route

    def draft(
        self,
        *,
        question,
        requirement: WorldModelRequirementRevision,
        plan: WorldModelQueryPlan,
        result_set: WorldModelQueryResultSet,
        assessment: WorldModelAssessment,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelDraftProposal:
        if len(assessment.needs) != 1:
            raise _invalid(
                "PRODUCT_IMPLEMENTATION_ASSESSMENT_INVALID",
                "implementation Draft requires exactly one assessed Need",
            )
        assessed = assessment.needs[0]
        disposition, kind = _implementation_draft_disposition(assessed.outcome)
        expected_result_ids = (
            tuple(item.value for item in assessed.step_result_ids)
            if disposition == "SUPPORTED"
            else ()
        )
        expected_support_digests = (
            tuple(item.value for item in assessed.support_digests)
            if disposition == "SUPPORTED"
            else ()
        )
        expected_gap_code = (
            assessed.gap_code if disposition == "KNOWLEDGE_GAP" else None
        )
        expected_limitations = (
            assessed.limitations if disposition == "LIMITATION" else ()
        )
        proposal = self._model.propose(
            case_id=f"product:{question.request_ref}:draft",
            capability=IMPLEMENTATION_ANSWER_DRAFTING,
            sealed_input={
                "original_question": question.original_question,
                "response_language": question.response_language,
                "requirement": {
                    "needs": tuple(
                        item.canonical_value() for item in requirement.needs
                    ),
                    "digest": requirement.digest.value,
                },
                "query_plan": {
                    "steps": tuple(
                        _plain_canonical(item.canonical_value())
                        for item in plan.steps
                    ),
                    "investigation_trace": (
                        _model_visible_investigation_trace(
                            plan.investigation_trace
                        )
                        if plan.investigation_trace is not None
                        else None
                    ),
                    "digest": plan.digest.value,
                },
                "query_results": _implementation_query_results(result_set),
                "need_assessment": assessed.canonical_value(),
                "assessment_disposition": disposition,
                "authorized_step_result_ids": expected_result_ids,
                "authorized_support_digests": expected_support_digests,
                "assessment_gap_code": expected_gap_code,
                "assessment_limitation_codes": expected_limitations,
            },
        )
        self._recorder.append(proposal)
        normalized = proposal.normalized_result
        answer = normalized.get("answer")
        if (
            normalized.get("disposition") != disposition
            or not isinstance(answer, str)
            or not answer.strip()
            or answer != answer.strip()
            or len(answer) > 65_536
            or tuple(normalized.get("step_result_ids", ()))
            != expected_result_ids
            or tuple(normalized.get("support_digests", ()))
            != expected_support_digests
            or normalized.get("gap_code") != expected_gap_code
            or tuple(normalized.get("limitation_codes", ()))
            != expected_limitations
            or any(
                token in answer.casefold()
                for token in (
                    "source payload",
                    "evidence payload",
                    "evidence excerpt",
                    "源码摘录",
                    "```",
                )
            )
        ):
            raise _invalid(
                "PRODUCT_IMPLEMENTATION_MODEL_DRAFT_INVALID",
                "model Draft is not exactly bound to the sealed formal assessment",
            )
        return WorldModelDraftProposal(
            assessment_id=assessment.assessment_id,
            assessment_digest=assessment.digest,
            claims=(
                WorldModelAnswerClaimProposal(
                    claim_id="claim:implementation-answer",
                    need_id=assessed.need_id,
                    kind=kind,
                    text=answer,
                    step_result_ids=(
                        assessed.step_result_ids
                        if disposition == "SUPPORTED"
                        else ()
                    ),
                ),
            ),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class JavaSourceSemanticsAnswerReviewer(WorldModelAnswerReviewer):
    """Call 3: independently review the exact Question/Result/Draft closure."""

    execution_mode = QUALIFIED_MODEL_STRATEGY_MODE

    def __init__(
        self,
        *,
        model_strategy: ProductCapabilityProposalPort,
        recorder: _ProductModelProposalRecorder,
        strategy_ref: str,
        provider_route: str,
    ) -> None:
        self._model = model_strategy
        self._recorder = recorder
        self.strategy_ref = strategy_ref
        self.provider_route = provider_route

    def review(
        self,
        *,
        question,
        requirement: WorldModelRequirementRevision,
        plan: WorldModelQueryPlan,
        result_set: WorldModelQueryResultSet,
        assessment: WorldModelAssessment,
        draft,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelReviewProposal:
        need_ids = tuple(item.need_id for item in requirement.needs)
        step_result_ids = tuple(
            item.step_result_id.value for item in result_set.step_results
        )
        support_digests = tuple(
            sorted(
                {
                    support.digest.value
                    for result in result_set.step_results
                    for support in result.view_result.support_map
                }
            )
        )
        proposal = self._model.propose(
            case_id=f"product:{question.request_ref}:review",
            capability=IMPLEMENTATION_ANSWER_REVIEW,
            sealed_input={
                "original_question": question.original_question,
                "response_language": question.response_language,
                "requirement": _plain_canonical(requirement.canonical_value()),
                "query_plan": _model_visible_query_plan(plan),
                "query_results": _implementation_query_results(result_set),
                "assessment": _plain_canonical(assessment.canonical_value()),
                "draft": _plain_canonical(draft.canonical_value()),
                "required_checked_need_ids": need_ids,
                "required_checked_step_result_ids": step_result_ids,
                "required_checked_support_digests": support_digests,
            },
        )
        self._recorder.append(proposal)
        normalized = proposal.normalized_result
        finding_codes = _closed_text_list(
            normalized.get("finding_codes"),
            "implementation review finding codes",
            minimum=0,
            maximum=64,
        )
        finding_code_order = {
            code: position
            for position, code in enumerate(
                JAVA_SOURCE_SEMANTICS_REVIEW_FINDING_CODES
            )
        }
        try:
            decision = WorldModelReviewDecision(normalized.get("decision"))
        except (TypeError, ValueError) as exc:
            raise _invalid(
                "PRODUCT_IMPLEMENTATION_MODEL_REVIEW_INVALID",
                "model Review returned an invalid decision",
            ) from exc
        if (
            tuple(normalized.get("checked_need_ids", ())) != need_ids
            or tuple(normalized.get("checked_step_result_ids", ()))
            != step_result_ids
            or tuple(normalized.get("checked_support_digests", ()))
            != support_digests
            or len(set(finding_codes)) != len(finding_codes)
            or any(code not in finding_code_order for code in finding_codes)
            or [finding_code_order[code] for code in finding_codes]
            != sorted(finding_code_order[code] for code in finding_codes)
            or (
                decision is WorldModelReviewDecision.APPROVE
                and finding_codes
            )
            or (
                decision is WorldModelReviewDecision.REJECT
                and not finding_codes
            )
        ):
            raise _invalid(
                "PRODUCT_IMPLEMENTATION_MODEL_REVIEW_INVALID",
                "model Review did not close the exact independent checklist",
            )
        return WorldModelReviewProposal(
            decision=decision,
            dimensions=tuple(
                WorldModelReviewDimensionAssessment(
                    dimension=dimension,
                    decision=decision,
                    finding_codes=finding_codes,
                )
                for dimension in WorldModelReviewDimension
            ),
            checked_need_ids=need_ids,
            checked_constraint_ids=tuple(
                item.constraint_id for item in requirement.joint_constraints
            ),
            checked_step_result_ids=tuple(
                item.step_result_id for item in result_set.step_results
            ),
            original_question_digest=digest_of(question.original_question),
            draft_digest=draft.digest,
            read_set_digest=question.read_authority.read_set_digest,
            finding_codes=finding_codes,
            findings=(
                ()
                if decision is WorldModelReviewDecision.APPROVE
                else tuple(
                    f"independent semantic review: {item}"
                    for item in finding_codes
                )
            ),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class ProductQueryPlanner(WorldModelQueryPlanner):
    strategy_ref = "iter-003-g3b-generic-structure-query-planner@1"

    def __init__(
        self,
        catalog: ProductBundleCatalog,
        interpreter: ProductQuestionInterpreter,
    ) -> None:
        self._catalog = catalog
        self._interpreter = interpreter

    def plan(
        self,
        *,
        question,
        requirement: WorldModelRequirementRevision,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelQueryPlanProposal:
        analysis = self._interpreter.analyze(question.original_question)
        snapshots = question.read_authority.snapshot_ids
        constraint_ids = tuple(
            item.constraint_id for item in requirement.joint_constraints
        )
        selectors: list[WorldModelEntitySelectorProposal] = []
        steps: list[WorldModelQueryStepProposal] = []
        gaps: list[WorldModelGapProposal] = []
        by_kind: dict[ProductNeedKind, list[ProductNeedSpec]] = {}
        for need in analysis.needs:
            by_kind.setdefault(need.kind, []).append(need)

        for need in by_kind.get(ProductNeedKind.INVENTORY, []):
            ordinal = need.snapshot_ordinals[0]
            selector_id = f"system-{ordinal}-{need.need_id}"
            selectors.append(
                self._selector(
                    selector_id=selector_id,
                    need_ids=(need.need_id,),
                    snapshot_id=snapshots[ordinal],
                    entity=self._catalog.system(snapshots[ordinal]),
                    original_question=question.original_question,
                )
            )
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id=need.need_id,
                    need_ids=(need.need_id,),
                    operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
                    arguments={"system": selector_id},
                    constraint_ids=constraint_ids,
                )
            )

        for need in by_kind.get(ProductNeedKind.METHOD_INVENTORY, []):
            ordinal = need.snapshot_ordinals[0]
            snapshot_id = snapshots[ordinal]
            assert analysis.direct_source_root_id is not None
            java_type = self._catalog.entry(
                snapshot_id, analysis.direct_source_root_id
            )
            selector_id = f"java-type-{ordinal}-{need.need_id}"
            selectors.append(
                self._selector(
                    selector_id=selector_id,
                    need_ids=(need.need_id,),
                    snapshot_id=snapshot_id,
                    entity=java_type,
                    original_question=question.original_question,
                )
            )
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id=need.need_id,
                    need_ids=(need.need_id,),
                    operation=StructureViewOperation.DECLARED_METHOD_INVENTORY,
                    arguments={"java_type": selector_id},
                    constraint_ids=constraint_ids,
                )
            )
        path_needs = by_kind.get(ProductNeedKind.PATHS, [])
        new_path_needs = by_kind.get(ProductNeedKind.NEW_PATHS, [])
        if path_needs:
            assert analysis.path_endpoints is not None
            source_root, target_root = analysis.path_endpoints
            new_ids = tuple(item.need_id for item in new_path_needs)
            for need in path_needs:
                ordinal = need.snapshot_ordinals[0]
                snapshot_id = snapshots[ordinal]
                source = self._catalog.entry(snapshot_id, source_root)
                target = self._catalog.entry(snapshot_id, target_root)
                mapped_needs = (need.need_id, *new_ids)
                source_id = f"path-source-{ordinal}"
                target_id = f"path-target-{ordinal}"
                selectors.extend(
                    (
                        self._selector(
                            selector_id=source_id,
                            need_ids=mapped_needs,
                            snapshot_id=snapshot_id,
                            entity=source,
                            original_question=question.original_question,
                        ),
                        self._selector(
                            selector_id=target_id,
                            need_ids=mapped_needs,
                            snapshot_id=snapshot_id,
                            entity=target,
                            original_question=question.original_question,
                        ),
                    )
                )
                steps.append(
                    WorldModelQueryStepProposal.create(
                        step_id=need.need_id,
                        need_ids=mapped_needs,
                        operation=StructureViewOperation.ALL_SIMPLE_PATHS,
                        arguments={"source": source_id, "target": target_id},
                        parameters={"predicate": self._catalog.graph_predicate.value},
                        constraint_ids=constraint_ids,
                    )
                )

        diff_needs = by_kind.get(ProductNeedKind.ORDERED_DIFF, [])
        if new_path_needs or diff_needs:
            mapped_needs = tuple(
                item.need_id for item in (*new_path_needs, *diff_needs)
            )
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id="ordered-diff-query",
                    need_ids=mapped_needs,
                    operation=StructureViewOperation.ORDERED_SNAPSHOT_DIFF,
                    parameters={
                        "base_snapshot_id": snapshots[0].value,
                        "target_snapshot_id": snapshots[1].value,
                    },
                    constraint_ids=constraint_ids,
                )
            )

        direct_needs = by_kind.get(ProductNeedKind.DIRECT_DEPENDENCY, [])
        if direct_needs:
            need = direct_needs[0]
            ordinal = need.snapshot_ordinals[0]
            snapshot_id = snapshots[ordinal]
            assert analysis.direct_source_root_id is not None
            source = self._catalog.entry(
                snapshot_id, analysis.direct_source_root_id
            )
            source_id = "direct-source"
            selectors.append(
                self._selector(
                    selector_id=source_id,
                    need_ids=(need.need_id,),
                    snapshot_id=snapshot_id,
                    entity=source,
                    original_question=question.original_question,
                )
            )
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id="direct-neighborhood",
                    need_ids=(need.need_id,),
                    operation=StructureViewOperation.DIRECT_NEIGHBORHOOD,
                    arguments={"entity": source_id},
                    parameters={
                        "direction": NeighborhoodDirection.OUTGOING.value,
                        "predicate": RelationPredicate.DEPENDS_ON.value,
                    },
                    constraint_ids=constraint_ids,
                )
            )
            inventory_id = "direct-system"
            selectors.append(
                self._selector(
                    selector_id=inventory_id,
                    need_ids=(need.need_id,),
                    snapshot_id=snapshot_id,
                    entity=self._catalog.system(snapshot_id),
                    original_question=question.original_question,
                )
            )
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id="direct-target-catalog",
                    need_ids=(need.need_id,),
                    operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
                    arguments={"system": inventory_id},
                    constraint_ids=constraint_ids,
                )
            )

        direct_call_needs = by_kind.get(ProductNeedKind.DIRECT_CALL, [])
        if direct_call_needs:
            need = direct_call_needs[0]
            ordinal = need.snapshot_ordinals[0]
            snapshot_id = snapshots[ordinal]
            assert analysis.direct_source_root_id is not None
            source = self._catalog.entry(
                snapshot_id, analysis.direct_source_root_id
            )
            selector_id = "direct-call-source"
            selectors.append(
                self._selector(
                    selector_id=selector_id,
                    need_ids=(need.need_id,),
                    snapshot_id=snapshot_id,
                    entity=source,
                    original_question=question.original_question,
                )
            )
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id="direct-call-neighborhood",
                    need_ids=(need.need_id,),
                    operation=StructureViewOperation.DIRECT_NEIGHBORHOOD,
                    arguments={"entity": selector_id},
                    parameters={
                        "direction": NeighborhoodDirection.OUTGOING.value,
                        "predicate": RelationPredicate.CALLS.value,
                    },
                    constraint_ids=constraint_ids,
                )
            )
        same_name_needs = by_kind.get(ProductNeedKind.SAME_NAME_IDENTITY, [])
        if same_name_needs:
            need = same_name_needs[0]
            ordinal = need.snapshot_ordinals[0]
            snapshot_id = snapshots[ordinal]
            unresolved = next(
                (
                    item
                    for item in analysis.module_mentions
                    if len(item.entity_root_ids) != 1
                ),
                None,
            )
            if unresolved is not None:
                selector_id = "same-name-candidate"
                selectors.append(
                    WorldModelEntitySelectorProposal(
                        selector_id=selector_id,
                        need_ids=(need.need_id,),
                        snapshot_id=snapshot_id,
                        origin=EntitySelectorOrigin.MENTION,
                        mention=unresolved.token,
                        entity_type=EntityType.MAVEN_MODULE,
                    )
                )
                steps.append(
                    WorldModelQueryStepProposal.create(
                        step_id="same-name-candidate-check",
                        need_ids=(need.need_id,),
                        operation=StructureViewOperation.DIRECT_NEIGHBORHOOD,
                        arguments={"entity": selector_id},
                        parameters={
                            "direction": NeighborhoodDirection.BOTH.value,
                            "predicate": RelationPredicate.DEPENDS_ON.value,
                        },
                        constraint_ids=constraint_ids,
                    )
                )
            else:
                selector_id = "same-name-system"
                selectors.append(
                    self._selector(
                        selector_id=selector_id,
                        need_ids=(need.need_id,),
                        snapshot_id=snapshot_id,
                        entity=self._catalog.system(snapshot_id),
                        original_question=question.original_question,
                    )
                )
                steps.append(
                    WorldModelQueryStepProposal.create(
                        step_id="same-name-catalog",
                        need_ids=(need.need_id,),
                        operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
                        arguments={"system": selector_id},
                        constraint_ids=constraint_ids,
                    )
                )

        for need in by_kind.get(ProductNeedKind.KNOWLEDGE_GAP, []):
            java_profile = (
                self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF
            )
            gaps.append(
                WorldModelGapProposal(
                    need_id=need.need_id,
                    reason_code=(
                        WorldModelGapReason.KNOWLEDGE_NOT_MODELED
                        if java_profile
                        else WorldModelGapReason.CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE
                    ),
                    detail=(
                        (
                            "The mounted Java static-call View does not model runtime "
                            "dispatch, reflection, dependency injection, or design intent."
                        )
                        if java_profile
                        else (
                            "The mounted Structure View can prove graph change but not "
                            "the design intent that caused it."
                        )
                    ),
                )
            )
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=requirement.read_authority.ordered_bundle_digest,
            selectors=tuple(selectors),
            steps=tuple(steps),
            explicit_gaps=tuple(gaps),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )

    @staticmethod
    def _selector(
        *,
        selector_id: str,
        need_ids: tuple[str, ...],
        snapshot_id: StableId,
        entity: ProductCatalogEntity,
        original_question: str,
    ) -> WorldModelEntitySelectorProposal:
        canonical_gav = (
            entity.canonical_gav
            if entity.canonical_gav is not None
            and entity.canonical_gav in original_question
            else None
        )
        canonical_ga = (
            entity.canonical_ga
            if canonical_gav is None
            and entity.canonical_ga is not None
            and entity.canonical_ga in original_question
            else None
        )
        return WorldModelEntitySelectorProposal(
            selector_id=selector_id,
            need_ids=need_ids,
            snapshot_id=snapshot_id,
            origin=EntitySelectorOrigin.MENTION,
            mention=entity.mention,
            entity_type=entity.entity_type,
            canonical_ga=canonical_ga,
            canonical_gav=canonical_gav,
        )


class ProductModelDraftGenerator(WorldModelDraftGenerator):
    strategy_ref = PRODUCT_STRATEGY_REF
    execution_mode = QUALIFIED_MODEL_STRATEGY_MODE
    provider_route = MODEL_EGRESS_GATEWAY_ROUTE

    def __init__(
        self,
        *,
        catalog: ProductBundleCatalog,
        interpreter: ProductQuestionInterpreter,
        model_strategy: ProductCapabilityProposalPort,
        strategy_ref: str,
        provider_route: str,
    ) -> None:
        self._catalog = catalog
        self._interpreter = interpreter
        self._model = model_strategy
        self.strategy_ref = strategy_ref
        self.provider_route = provider_route
        self._proposals: list[WorldModelCapabilityProposal] = []

    @property
    def proposals(self) -> tuple[WorldModelCapabilityProposal, ...]:
        return tuple(self._proposals)

    def draft(
        self,
        *,
        question,
        requirement: WorldModelRequirementRevision,
        plan: WorldModelQueryPlan,
        result_set: WorldModelQueryResultSet,
        assessment: WorldModelAssessment,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelDraftProposal:
        analysis = self._interpreter.analyze(question.original_question)
        proposal = self._qualified_material_proposal(
            question=question,
            analysis=analysis,
            result_set=result_set,
        )
        self._proposals.append(proposal)
        by_need = {item.need_id: item for item in assessment.needs}
        by_step = {item.step_id: item for item in result_set.step_results}
        claims: list[WorldModelAnswerClaimProposal] = []
        for need in requirement.needs:
            assessed = by_need[need.need_id]
            if assessed.outcome is WorldModelNeedOutcome.KNOWLEDGE_GAP:
                kind = WorldModelClaimKind.KNOWLEDGE_GAP
                if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF:
                    text = (
                        "Knowledge Gap：当前 Java View 只证明源码声明与冻结子集内的"
                        "静态调用，不证明运行时分派、反射、依赖注入或设计动机；"
                        "reason_code=KNOWLEDGE_NOT_MODELED。"
                    )
                else:
                    text = (
                        "Knowledge Gap：当前 Structure View 能证明结构变化，但不能证明变更动机；"
                        f"reason_code={PRODUCT_GAP_REASON}。"
                    )
                result_ids: tuple[StableId, ...] = ()
            elif assessed.outcome is WorldModelNeedOutcome.LIMITATION:
                kind = WorldModelClaimKind.APPLICATION_LIMITATION
                if need.need_id == "same-name-identity":
                    text = self._render_resolution_limitation(analysis)
                else:
                    text = "View Limitation：" + ", ".join(assessed.limitations)
                result_ids = ()
            else:
                kind = WorldModelClaimKind.QUERY_RESULT
                text = self._render_need(
                    need.need_id,
                    analysis=analysis,
                    result_set=result_set,
                    by_step=by_step,
                )
                result_ids = assessed.step_result_ids
            claims.append(
                WorldModelAnswerClaimProposal(
                    claim_id=f"claim:{need.need_id}",
                    need_id=need.need_id,
                    kind=kind,
                    text=text,
                    step_result_ids=result_ids,
                )
            )
        return WorldModelDraftProposal(
            assessment_id=assessment.assessment_id,
            assessment_digest=assessment.digest,
            claims=tuple(claims),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )

    def _qualified_material_proposal(
        self,
        *,
        question,
        analysis: ProductQuestionAnalysis,
        result_set: WorldModelQueryResultSet,
    ) -> WorldModelCapabilityProposal:
        results = tuple(item.view_result for item in result_set.step_results)
        diff = next(
            (
                item
                for item in results
                if item.operation is StructureViewOperation.ORDERED_SNAPSHOT_DIFF
            ),
            None,
        )
        empty_path = next(
            (
                item
                for item in results
                if item.operation is StructureViewOperation.ALL_SIMPLE_PATHS
                and item.payload["path_count"] == 0
            ),
            None,
        )
        case_ref = f"product:{question.request_ref}"
        if any(
            item.kind is ProductNeedKind.KNOWLEDGE_GAP
            for item in analysis.needs
        ):
            proposal = self._model.propose(
                case_id=case_ref,
                capability=VIEW_LIMITATION_AND_KNOWLEDGE_GAP,
                sealed_input={
                    "coverage": "PARTIAL",
                    "need": "change_intent",
                    "query_result": {
                        "all_simple_paths": [],
                        "pagination_complete": True,
                    },
                },
            )
            expected = {
                "view_result": {
                    "status": "LIMITED",
                    "code": "COVERAGE_PARTIAL",
                    "owner": "STRUCTURE_VIEW",
                },
                "need_assessment": {
                    "status": "KNOWLEDGE_GAP",
                    "code": "INSUFFICIENT_COMPLETE_COVERAGE",
                    "owner": "KNOWLEDGE_USE",
                },
            }
        elif diff is not None and any(
            item.kind is ProductNeedKind.ORDERED_DIFF for item in analysis.needs
        ):
            added = [
                item["canonical_ga"] or item["root_id"]
                for item in diff.payload["entities"]["added"]
            ]
            sealed_input = {
                "base": diff.payload["base_snapshot_id"],
                "base_added": [],
                "target": diff.payload["target_snapshot_id"],
                "target_added": added,
            }
            proposal = self._model.propose(
                case_id=case_ref,
                capability=ORDERED_DIFF_EXPRESSION,
                sealed_input=sealed_input,
            )
            expected = {
                "direction": {
                    "base": sealed_input["base"],
                    "target": sealed_input["target"],
                },
                "added_entities": added,
            }
        elif empty_path is not None:
            proposal = self._model.propose(
                case_id=case_ref,
                capability=COMPLETE_NEGATIVE_ANSWER,
                sealed_input={
                    "coverage": empty_path.completeness.value,
                    "modeled_relation": f"{self._catalog.graph_predicate.value}@1",
                    "query_result": {
                        "all_simple_paths": [],
                        "pagination_complete": not empty_path.truncated,
                    },
                },
            )
            expected = {
                "need_status": "SATISFIED_SUPPORTED_NEGATIVE",
                "claim_scope": (
                    "NO_PATH_IN_CALLS_FOR_EXACT_READ_SET"
                    if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF
                    else "NO_PATH_IN_DEPENDS_ON_FOR_EXACT_READ_SET"
                ),
            }
        elif any(
            item.kind
            in {
                ProductNeedKind.DIRECT_DEPENDENCY,
                ProductNeedKind.DIRECT_CALL,
                ProductNeedKind.SAME_NAME_IDENTITY,
            }
            for item in analysis.needs
        ):
            same_name_resolution = any(
                item.kind is ProductNeedKind.SAME_NAME_IDENTITY
                for item in analysis.needs
            )
            unresolved = next(
                (
                    group
                    for group in analysis.module_mentions
                    if len(group.entity_root_ids) != 1
                ),
                None,
            )
            if same_name_resolution and unresolved is not None:
                candidate_refs = tuple(
                    root.value for root in unresolved.entity_root_ids
                )
                mention = unresolved.token
            else:
                candidate_refs = tuple(
                    item.value for item in analysis.direct_target_root_ids
                )
                if not candidate_refs:
                    candidate_refs = tuple(
                        root.value
                        for group in analysis.module_mentions
                        for root in group.entity_root_ids
                    )
                mention = (
                    analysis.module_mentions[-1].token
                    if analysis.module_mentions
                    else "module"
                )
            candidate_refs = tuple(dict.fromkeys(candidate_refs))
            proposal = self._model.propose(
                case_id=case_ref,
                capability=ENTITY_CANDIDATE_RESOLUTION,
                sealed_input={
                    "mention": mention,
                    "candidate_refs": list(candidate_refs),
                },
            )
            status = (
                "NOT_FOUND"
                if not candidate_refs
                else "RESOLVED"
                if len(candidate_refs) == 1
                else "AMBIGUOUS"
            )
            expected = {
                "resolution_status": status,
                "candidate_refs": list(candidate_refs),
                "next_operation_allowed": len(candidate_refs) == 1,
            }
        else:
            sealed_input, expected = self._generic_plan_check(
                analysis, result_set
            )
            proposal = self._model.propose(
                case_id=case_ref,
                capability=GENERIC_QUERY_PLANNING,
                sealed_input=sealed_input,
                available_operations=(
                    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
                    if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF
                    else MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
                ),
            )
        if proposal.normalized_result != expected:
            raise _invalid(
                "PRODUCT_MODEL_PROPOSAL_MISMATCH",
                "qualified model proposal does not match the formal View authority",
            )
        return proposal

    def _generic_plan_check(
        self,
        analysis: ProductQuestionAnalysis,
        result_set: WorldModelQueryResultSet,
    ) -> tuple[dict[str, object], dict[str, object]]:
        inventory_results = tuple(
            item.view_result
            for item in result_set.step_results
            if item.view_result.operation
            is StructureViewOperation.CHILD_MODULE_INVENTORY
        )
        method_inventory_results = tuple(
            item.view_result
            for item in result_set.step_results
            if item.view_result.operation
            is StructureViewOperation.DECLARED_METHOD_INVENTORY
        )
        path_results = tuple(
            item.view_result
            for item in result_set.step_results
            if item.view_result.operation
            is StructureViewOperation.ALL_SIMPLE_PATHS
        )
        needs: list[str] = []
        operations: list[dict[str, object]] = []
        for index, result in enumerate(inventory_results):
            key = "inventory_left" if index == 0 else "inventory_right"
            needs.append(key)
            operations.append(
                {"operation": "inventory", "snapshot": result.snapshot_ids[0].value}
            )
        for index, result in enumerate(method_inventory_results):
            key = "method_inventory_left" if index == 0 else "method_inventory_right"
            needs.append(key)
            operations.append(
                {
                    "operation": "declared_method_inventory",
                    "snapshot": result.snapshot_ids[0].value,
                }
            )
        source_ref: str | None = None
        target_ref: str | None = None
        for index, result in enumerate(path_results):
            key = "paths_left" if index == 0 else "paths_right"
            needs.append(key)
            source_ref = result.payload["source"]["root_id"]
            target_ref = result.payload["target"]["root_id"]
            operations.append(
                {
                    "operation": "all_simple_paths",
                    "snapshot": result.snapshot_ids[0].value,
                    "source_ref": source_ref,
                    "target_ref": target_ref,
                }
            )
        if any(
            item.kind is ProductNeedKind.NEW_PATHS for item in analysis.needs
        ):
            needs.append("new_paths")
            operations.append(
                {
                    "operation": "ordered_snapshot_diff",
                    "base": self._catalog.snapshot_ids[0].value,
                    "target": self._catalog.snapshot_ids[1].value,
                }
            )
        if not needs:
            raise _invalid(
                "PRODUCT_MODEL_PLAN_CHECK_EMPTY",
                "qualified model plan check has no supported formal operation",
            )
        sealed: dict[str, object] = {
            "needs": needs,
            "read_set": [item.value for item in self._catalog.snapshot_ids],
        }
        if source_ref is not None and target_ref is not None:
            sealed["source_entity_ref"] = source_ref
            sealed["target_entity_ref"] = target_ref
        return sealed, {"operations": operations}

    def _render_need(
        self,
        need_id: str,
        *,
        analysis: ProductQuestionAnalysis,
        result_set: WorldModelQueryResultSet,
        by_step: Mapping[str, object],
    ) -> str:
        if need_id.startswith("inventory-"):
            result = by_step[need_id].view_result
            modules = [item["canonical_ga"] for item in result.payload["modules"]]
            return f"{_snapshot_label(result_set, result.snapshot_ids[0])} 的全部递归 reactor child modules（不含根）: {_json(modules)}"
        if need_id.startswith("method-inventory-"):
            result = by_step[need_id].view_result
            methods = [
                self._catalog.display_ref(StableId(item["root_id"]))
                for item in result.payload["methods"]
            ]
            return (
                f"{_snapshot_label(result_set, result.snapshot_ids[0])} 的源码声明方法"
                f"（JAVA_SOURCE_DECLARATION@1）: {_json(methods)}"
            )
        if need_id.startswith("paths-"):
            result = by_step[need_id].view_result
            paths = self._path_refs(result.payload["paths"])
            if not paths and result.payload["negative_conclusion_supported"]:
                source = self._catalog.display_ref(
                    StableId(result.payload["source"]["root_id"])
                )
                target = self._catalog.display_ref(
                    StableId(result.payload["target"]["root_id"])
                )
                if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF:
                    return (
                        f"{_snapshot_label(result_set, result.snapshot_ids[0])} 的当前 "
                        "JAVA_SOURCE_STATIC_CALL@1 图中，不存在从 "
                        f"{source} 到 {target} 的静态调用路径；此结论不扩大为运行时不调用。"
                    )
                return (
                    f"{_snapshot_label(result_set, result.snapshot_ids[0])} 的当前 "
                    "POM 本地声明内部 DEPENDS_ON 图中，不存在从 "
                    f"{source} 到 {target} 的路径；此结论不扩大为其他关系不存在。"
                )
            label = (
                "全部简单静态调用路径"
                if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF
                else "全部简单内部依赖路径"
            )
            return f"{_snapshot_label(result_set, result.snapshot_ids[0])} 的{label}: {_json(paths)}"
        if need_id == "new-paths":
            path_results = tuple(
                item.view_result
                for item in result_set.step_results
                if item.view_result.operation
                is StructureViewOperation.ALL_SIMPLE_PATHS
            )
            if len(path_results) != 2:
                raise _invalid(
                    "PRODUCT_NEW_PATH_READ_SET_INVALID",
                    "new-path answer requires two exact path Results",
                )
            left = {tuple(item) for item in self._path_refs(path_results[0].payload["paths"])}
            right = {tuple(item) for item in self._path_refs(path_results[1].payload["paths"])}
            label = (
                "目标 Snapshot 新增的简单静态调用路径: "
                if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF
                else "目标 Snapshot 新增的简单内部依赖路径: "
            )
            return label + _json(
                [list(item) for item in sorted(right - left)]
            )
        if need_id == "ordered-diff":
            result = by_step["ordered-diff-query"].view_result
            return self._render_diff(result.payload, analysis.include_state_changes)
        if need_id == "direct-dependency":
            neighborhood = by_step["direct-neighborhood"].view_result
            inventory = by_step["direct-target-catalog"].view_result
            return self._render_direct(
                neighborhood.payload,
                inventory.payload,
                analysis,
            )
        if need_id == "direct-call":
            neighborhood = by_step["direct-call-neighborhood"].view_result
            return self._render_direct_call(neighborhood.payload, analysis)
        if need_id == "same-name-identity":
            inventory = by_step["same-name-catalog"].view_result
            return self._render_same_name(inventory.payload, analysis)
        raise _invalid(
            "PRODUCT_DRAFT_NEED_UNREGISTERED",
            "product Draft encountered an unregistered Need",
        )

    def _path_refs(self, paths: object) -> list[list[str]]:
        if not isinstance(paths, tuple):
            raise _invalid("PRODUCT_PATH_RESULT_INVALID", "path Result is invalid")
        return [
            [self._catalog.display_ref(StableId(root_id)) for root_id in item["entity_root_ids"]]
            for item in paths
        ]

    def _render_diff(self, payload: Mapping[str, object], include_state: bool) -> str:
        entities = payload["entities"]
        relations = payload["relations"]
        result: dict[str, object] = {
            "direction": {
                "base": payload["base_snapshot_id"],
                "target": payload["target_snapshot_id"],
            },
            "entities_added": [
                item["canonical_ga"]
                or self._catalog.display_ref(StableId(item["root_id"]))
                for item in entities["added"]
            ],
            "entities_removed": [
                item["canonical_ga"]
                or self._catalog.display_ref(StableId(item["root_id"]))
                for item in entities["removed"]
            ],
            "relations_added": [self._relation_ref(item) for item in relations["added"]],
            "relations_removed": [self._relation_ref(item) for item in relations["removed"]],
        }
        if include_state:
            result["entity_state_changes"] = [
                _public_state_change(item) for item in entities["state_changed"]
            ]
            result["relation_state_changes"] = [
                _relation_state_change(item) for item in relations["state_changed"]
            ]
        return "有序 Snapshot 结构变化: " + _json(result)

    def _relation_ref(self, value: Mapping[str, object]) -> dict[str, str]:
        return {
            "source": self._catalog.display_ref(
                StableId(value["subject_entity_root_id"])
            ),
            "predicate": value["predicate"],
            "target": self._catalog.display_ref(
                StableId(value["object_entity_root_id"])
            ),
            "modality": value["observation_modality"],
        }

    def _render_direct(
        self,
        neighborhood: Mapping[str, object],
        inventory: Mapping[str, object],
        analysis: ProductQuestionAnalysis,
    ) -> str:
        source = _direct_source_ref(neighborhood["entity"])
        targets = [
            self._catalog.display_ref(StableId(item["object_entity_root_id"]))
            for item in neighborhood["relations"]
            if item["subject_entity_root_id"] == neighborhood["entity"]["root_id"]
        ]
        target_status = {
            self._catalog.display_ref(root): self._catalog.display_ref(root) in targets
            for root in analysis.direct_target_root_ids
        }
        same_artifact = _same_artifact_groups(inventory["modules"])
        result = {
            "source": source,
            "direct_internal_dependencies": targets,
            "requested_target_edge_exists": target_status,
            "same_artifact_candidates": same_artifact,
            "relation_modality": "POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY@1",
            "dependency_management_forms_edge": False,
        }
        return "本 Profile 的本地声明直接内部依赖: " + _json(result)

    def _render_direct_call(
        self,
        neighborhood: Mapping[str, object],
        analysis: ProductQuestionAnalysis,
    ) -> str:
        source_root = StableId(neighborhood["entity"]["root_id"])
        targets = [
            self._catalog.display_ref(StableId(item["object_entity_root_id"]))
            for item in neighborhood["relations"]
            if item["subject_entity_root_id"] == source_root.value
            and item["predicate"] == RelationPredicate.CALLS.value
        ]
        target_status = {
            self._catalog.display_ref(root): self._catalog.display_ref(root)
            in targets
            for root in analysis.direct_target_root_ids
        }
        return "冻结源码子集内的直接静态调用: " + _json(
            {
                "source": self._catalog.display_ref(source_root),
                "direct_static_calls": targets,
                "requested_target_edge_exists": target_status,
                "relation_modality": "JAVA_SOURCE_STATIC_CALL@1",
                "runtime_dispatch_claimed": False,
            }
        )

    def _render_same_name(
        self,
        inventory: Mapping[str, object],
        analysis: ProductQuestionAnalysis,
    ) -> str:
        mentioned = {root.value for group in analysis.module_mentions for root in group.entity_root_ids}
        values = [
            {
                "root_id": item["root_id"],
                "ga": item["canonical_ga"],
                "gav": item["canonical_gav"],
            }
            for item in inventory["modules"]
            if not mentioned or item["root_id"] in mentioned
        ]
        return "同名 artifact 必须按稳定 Root 与完整 GA 区分: " + _json(values)

    def _render_resolution_limitation(
        self,
        analysis: ProductQuestionAnalysis,
    ) -> str:
        group = next(
            (
                item
                for item in analysis.module_mentions
                if len(item.entity_root_ids) != 1
            ),
            None,
        )
        if group is None:
            raise _invalid(
                "PRODUCT_RESOLUTION_LIMITATION_MISSING",
                "Entity Resolution Limitation has no bounded candidate group",
            )
        candidates = [
            self._catalog.display_ref(item) for item in group.entity_root_ids
        ]
        status = "ZERO" if not candidates else "AMBIGUOUS"
        return "Entity Resolution Limitation：" + _json(
            {
                "mention": group.token,
                "resolution_status": status,
                "candidate_count": len(candidates),
                "candidates": candidates,
                "next_operation_allowed": False,
            }
        )


class ProductAnswerReviewer(WorldModelAnswerReviewer):
    strategy_ref = "iter-003-g3b-independent-answer-reviewer@1"

    def review(
        self,
        *,
        question,
        requirement: WorldModelRequirementRevision,
        plan: WorldModelQueryPlan,
        result_set: WorldModelQueryResultSet,
        assessment: WorldModelAssessment,
        draft,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelReviewProposal:
        del plan
        expected_needs = tuple(item.need_id for item in requirement.needs)
        expected_results = tuple(
            item.step_result_id for item in result_set.step_results
        )
        actual_needs = tuple(item.need_id for item in draft.claims)
        claims_by_need = {item.need_id: item for item in draft.claims}
        assessments_by_need = {item.need_id: item for item in assessment.needs}
        claim_outcomes_match = all(
            (
                item.kind is WorldModelClaimKind.APPLICATION_LIMITATION
                and item.step_result_ids == ()
                and item.limitation_codes
                == assessments_by_need[item.need_id].limitations
            )
            if assessments_by_need[item.need_id].outcome
            is WorldModelNeedOutcome.LIMITATION
            else (
                item.kind is WorldModelClaimKind.KNOWLEDGE_GAP
                and item.step_result_ids == ()
                and item.gap_code
                == assessments_by_need[item.need_id].gap_code
            )
            if assessments_by_need[item.need_id].outcome
            is WorldModelNeedOutcome.KNOWLEDGE_GAP
            else (
                item.kind is WorldModelClaimKind.QUERY_RESULT
                and item.step_result_ids
                == assessments_by_need[item.need_id].step_result_ids
            )
            for item in draft.claims
        )
        forbidden = ("evidence excerpt", "source payload", "源码摘录")
        approved = (
            actual_needs == expected_needs
            and set(claims_by_need) == set(assessments_by_need)
            and claim_outcomes_match
            and all(item.satisfied for item in assessment.joint_constraints)
            and not any(token in draft.body.casefold() for token in forbidden)
        )
        decision = (
            WorldModelReviewDecision.APPROVE
            if approved
            else WorldModelReviewDecision.REJECT
        )
        finding_codes = () if approved else ("PRODUCT_DRAFT_REVIEW_FAILED",)
        return WorldModelReviewProposal(
            decision=decision,
            dimensions=tuple(
                WorldModelReviewDimensionAssessment(
                    dimension=dimension,
                    decision=decision,
                    finding_codes=finding_codes,
                )
                for dimension in WorldModelReviewDimension
            ),
            checked_need_ids=expected_needs,
            checked_constraint_ids=tuple(
                item.constraint_id for item in requirement.joint_constraints
            ),
            checked_step_result_ids=expected_results,
            original_question_digest=digest_of(question.original_question),
            draft_digest=draft.digest,
            read_set_digest=question.read_authority.read_set_digest,
            finding_codes=finding_codes,
            findings=() if approved else ("independent product Draft review failed",),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class WorldModelProductAnswerService:
    """Execute one qualified, evaluation-only product authority chain."""

    def __init__(
        self,
        *,
        view,
        snapshot_bundles: Sequence[StructureSnapshotReadBundle],
        model_strategy: ProductCapabilityProposalPort,
        gateway_counters: ProductGatewayCounters,
    ) -> None:
        self._view = view
        self._catalog = ProductBundleCatalog(snapshot_bundles)
        if tuple(self._catalog.snapshot_ids) != tuple(view.snapshot_ids):
            raise _invalid(
                "PRODUCT_CATALOG_READ_SET_MISMATCH",
                "product catalog and Structure View bind different Snapshots",
            )
        self._gateway_counters = gateway_counters
        expected_contract = (
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
            if self._catalog.profile_ref == JAVA_SOURCE_SEMANTICS_PROFILE_REF
            else JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
            if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF
            else MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT
        )
        binder = getattr(model_strategy, "for_proposal_contract", None)
        if callable(binder):
            model_strategy = binder(expected_contract)
        self._model_strategy = model_strategy
        expected_strategy_ref = expected_contract.strategy_ref
        actual_strategy_ref = getattr(model_strategy, "strategy_ref", None)
        if actual_strategy_ref != expected_strategy_ref:
            raise _invalid(
                "PRODUCT_MODEL_STRATEGY_PROFILE_MISMATCH",
                "model proposal strategy is not qualified for the mounted profile",
            )
        self._model_strategy_ref = expected_strategy_ref
        self._model_route = (
            BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_ROUTE
            if self._catalog.profile_ref == JAVA_SOURCE_SEMANTICS_PROFILE_REF
            else JAVA_MODEL_EGRESS_GATEWAY_ROUTE
            if self._catalog.profile_ref == JAVA_STATIC_CALL_PROFILE_REF
            else MODEL_EGRESS_GATEWAY_ROUTE
        )

    def execute(
        self,
        *,
        request_ref: str,
        original_question: str,
        response_language: str,
        classification: str,
        permission_digest: Digest,
    ) -> ProductWorldModelExecution:
        initial_provider_calls = self._gateway_counters.provider_call_count
        initial_network_operations = self._gateway_counters.network_operation_count
        store = InMemoryWorldModelAuthorityStore()
        answering = WorldModelAnsweringService(
            store,
            self._view,
            model_route=self._model_route,
        )
        responses = WorldModelResponseControlService(store, answering)
        semantic_profile = (
            self._catalog.profile_ref == JAVA_SOURCE_SEMANTICS_PROFILE_REF
        )
        recorder = _ProductModelProposalRecorder()
        if semantic_profile:
            requirement_planner = JavaSourceSemanticsRequirementPlanner()
            requirement_reviewer = JavaSourceSemanticsRequirementReviewer()
            query_planner = JavaSourceSemanticsQueryPlanner(
                model_strategy=self._model_strategy,
                recorder=recorder,
                strategy_ref=self._model_strategy_ref,
                provider_route=self._model_route,
                view=self._view,
            )
            draft_generator = JavaSourceSemanticsDraftGenerator(
                model_strategy=self._model_strategy,
                recorder=recorder,
                strategy_ref=self._model_strategy_ref,
                provider_route=self._model_route,
            )
            answer_reviewer = JavaSourceSemanticsAnswerReviewer(
                model_strategy=self._model_strategy,
                recorder=recorder,
                strategy_ref=self._model_strategy_ref,
                provider_route=self._model_route,
            )
        else:
            interpreter = ProductQuestionInterpreter(self._catalog)
            requirement_planner = ProductRequirementPlanner(interpreter)
            requirement_reviewer = ProductRequirementReviewer(interpreter)
            query_planner = ProductQueryPlanner(self._catalog, interpreter)
            draft_generator = ProductModelDraftGenerator(
                catalog=self._catalog,
                interpreter=interpreter,
                model_strategy=self._model_strategy,
                strategy_ref=self._model_strategy_ref,
                provider_route=self._model_route,
            )
            answer_reviewer = ProductAnswerReviewer()
        question = answering.open_question(
            request_ref=request_ref,
            original_question=original_question,
            response_language=response_language,
            classification=classification,
            permission_digest=permission_digest,
        )
        requirement = answering.seal_requirement(
            question_id=question.question_id,
            planner=requirement_planner,
            fidelity_reviewer=requirement_reviewer,
        )
        plan = answering.seal_query_plan(
            requirement_id=requirement.requirement_id,
            planner=query_planner,
        )
        result_set = answering.execute_query_plan(plan_id=plan.plan_id)
        assessment = answering.assess(result_set_id=result_set.result_set_id)
        draft = responses.seal_draft(
            assessment_id=assessment.assessment_id,
            generator=draft_generator,
        )
        review = responses.review(
            draft_id=draft.draft_id,
            reviewer=answer_reviewer,
        )
        authorization = responses.authorize(review_id=review.review_id)
        delivery = responses.deliver(
            authorization_id=authorization.authorization_id,
            sink=InMemoryWorldModelEvaluationSink(),
        )
        chain = responses.authority_chain(
            delivery_id=delivery.delivery_id,
            provider_call_count=(
                self._gateway_counters.provider_call_count - initial_provider_calls
            ),
            network_operation_count=(
                self._gateway_counters.network_operation_count
                - initial_network_operations
            ),
        )
        return ProductWorldModelExecution(
            chain=chain,
            model_proposals=(
                recorder.proposals
                if semantic_profile
                else draft_generator.proposals
            ),
        )


def _investigation_query_plan(
    trace: BoundedInvestigationTrace,
    need_ids: tuple[str, ...],
) -> tuple[
    tuple[WorldModelEntitySelectorProposal, ...],
    tuple[WorldModelQueryStepProposal, ...],
]:
    selectors: list[WorldModelEntitySelectorProposal] = []
    steps: list[WorldModelQueryStepProposal] = []

    def selector_for(
        value: InvestigationEntityRef,
        *,
        label: str,
    ) -> str:
        source = trace.result(
            value.source_result_id,
            value.source_result_digest,
        )
        if len(source.snapshot_ids) != 1:
            raise _invalid(
                "PRODUCT_INVESTIGATION_SELECTOR_SNAPSHOT_INVALID",
                "investigation Entity Ref source does not bind one Snapshot",
            )
        selector_id = f"investigation-{label}-{len(selectors) + 1}"
        selectors.append(
            WorldModelEntitySelectorProposal(
                selector_id=selector_id,
                need_ids=need_ids,
                snapshot_id=source.snapshot_ids[0],
                origin=EntitySelectorOrigin.SEALED_INVESTIGATION_RESULT,
                max_candidates=1,
                entity_root_id=value.entity_root_id,
                entity_state_id=value.entity_state_id,
                source_result_id=value.source_result_id,
                source_result_digest=value.source_result_digest,
            )
        )
        return selector_id

    for investigation_index, investigation_step in enumerate(
        trace.steps, start=1
    ):
        proposal = investigation_step.proposal
        prefix = f"investigation-{investigation_index}"
        if proposal.operation is InvestigationOperation.IMPLEMENTATION_CANDIDATES:
            assert proposal.snapshot_id is not None
            assert proposal.limit is not None
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id=f"{prefix}-candidates",
                    need_ids=need_ids,
                    operation=StructureViewOperation.IMPLEMENTATION_CANDIDATES,
                    parameters={
                        "snapshot_id": proposal.snapshot_id.value,
                        "search_terms": proposal.search_terms,
                        "limit": proposal.limit,
                    },
                )
            )
        elif proposal.operation is InvestigationOperation.METHOD_IMPLEMENTATIONS:
            for method_index, method_ref in enumerate(
                proposal.method_refs, start=1
            ):
                selector_id = selector_for(
                    method_ref,
                    label=f"{investigation_index}-method-{method_index}",
                )
                steps.append(
                    WorldModelQueryStepProposal.create(
                        step_id=f"{prefix}-method-{method_index}",
                        need_ids=need_ids,
                        operation=StructureViewOperation.METHOD_IMPLEMENTATION,
                        arguments={"method": selector_id},
                    )
                )
        elif proposal.operation is InvestigationOperation.DECLARED_METHOD_INVENTORY:
            selector_id = selector_for(
                proposal.entity_refs[0],
                label=f"{investigation_index}-java-type",
            )
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id=f"{prefix}-method-inventory",
                    need_ids=need_ids,
                    operation=StructureViewOperation.DECLARED_METHOD_INVENTORY,
                    arguments={"java_type": selector_id},
                )
            )
        elif proposal.operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
            selector_id = selector_for(
                proposal.entity_refs[0],
                label=f"{investigation_index}-entity",
            )
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id=f"{prefix}-neighborhood",
                    need_ids=need_ids,
                    operation=StructureViewOperation.DIRECT_NEIGHBORHOOD,
                    arguments={"entity": selector_id},
                    parameters={
                        "direction": proposal.direction.value,
                        "predicate": (
                            proposal.predicate.value
                            if proposal.predicate is not None
                            else None
                        ),
                    },
                )
            )
        elif proposal.operation in {
            InvestigationOperation.PATH_EXISTS,
            InvestigationOperation.ALL_SIMPLE_PATHS,
        }:
            source_id = selector_for(
                proposal.entity_refs[0],
                label=f"{investigation_index}-source",
            )
            target_id = selector_for(
                proposal.entity_refs[1],
                label=f"{investigation_index}-target",
            )
            parameters = {
                "predicate": proposal.predicate.value,
                "max_depth": proposal.max_depth,
                "max_expansions": proposal.max_expansions,
            }
            if proposal.operation is InvestigationOperation.ALL_SIMPLE_PATHS:
                parameters["max_paths"] = proposal.max_paths
            steps.append(
                WorldModelQueryStepProposal.create(
                    step_id=(
                        f"{prefix}-path-exists"
                        if proposal.operation is InvestigationOperation.PATH_EXISTS
                        else f"{prefix}-all-paths"
                    ),
                    need_ids=need_ids,
                    operation=(
                        StructureViewOperation.PATH_EXISTS
                        if proposal.operation is InvestigationOperation.PATH_EXISTS
                        else StructureViewOperation.ALL_SIMPLE_PATHS
                    ),
                    arguments={"source": source_id, "target": target_id},
                    parameters=parameters,
                )
            )
        else:  # pragma: no cover - FINISH is not an executed trace step
            raise _invalid(
                "PRODUCT_INVESTIGATION_OPERATION_INVALID",
                "terminal or unknown investigation operation entered Query Plan",
            )
    return tuple(selectors), tuple(steps)


def _closed_text_list(
    value: object,
    label: str,
    *,
    minimum: int,
    maximum: int,
) -> tuple[str, ...]:
    if (
        not isinstance(value, (list, tuple))
        or not minimum <= len(value) <= maximum
        or any(
            not isinstance(item, str)
            or not item
            or item != item.strip()
            or len(item) > 256
            or "\x00" in item
            for item in value
        )
    ):
        raise _invalid(
            "PRODUCT_MODEL_TEXT_LIST_INVALID",
            f"{label} is outside its closed bounded schema",
        )
    return tuple(value)


def _plain_canonical(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _plain_canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return tuple(_plain_canonical(item) for item in value)
    return value


def _model_visible_investigation_trace(
    trace: BoundedInvestigationTrace,
) -> dict[str, object]:
    """Project a sealed Trace without exposing its independent Oracle identity."""

    value = _plain_canonical(trace.canonical_value())
    if not isinstance(value, dict):  # pragma: no cover - canonical DTO invariant
        raise _invalid(
            "PRODUCT_INVESTIGATION_TRACE_PROJECTION_INVALID",
            "investigation trace did not project to one closed object",
        )
    value.pop("discovery_oracle", None)
    return value


def _model_visible_query_plan(
    plan: WorldModelQueryPlan,
) -> dict[str, object]:
    value = _plain_canonical(plan.canonical_value())
    if not isinstance(value, dict):  # pragma: no cover - canonical DTO invariant
        raise _invalid(
            "PRODUCT_QUERY_PLAN_PROJECTION_INVALID",
            "Query Plan did not project to one closed object",
        )
    if plan.investigation_trace is not None:
        value["investigation_trace"] = _model_visible_investigation_trace(
            plan.investigation_trace
        )
    return value


def _implementation_query_results(
    result_set: WorldModelQueryResultSet,
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "step_result_id": item.step_result_id.value,
            "step_id": item.step_id,
            "operation": item.view_result.operation.value,
            "result_id": item.view_result.result_id.value,
            "result_digest": item.view_result.digest.value,
            "completeness": item.view_result.completeness.value,
            "truncated": item.view_result.truncated,
            "limitations": item.view_result.limitations,
            "payload": _plain_canonical(item.view_result.payload),
            "support_digests": tuple(
                support.digest.value for support in item.view_result.support_map
            ),
        }
        for item in result_set.step_results
    )


def _implementation_draft_disposition(
    outcome: WorldModelNeedOutcome,
) -> tuple[str, WorldModelClaimKind]:
    if outcome in {
        WorldModelNeedOutcome.SATISFIED,
        WorldModelNeedOutcome.SATISFIED_SUPPORTED_NEGATIVE,
    }:
        return "SUPPORTED", WorldModelClaimKind.QUERY_RESULT
    if outcome is WorldModelNeedOutcome.KNOWLEDGE_GAP:
        return "KNOWLEDGE_GAP", WorldModelClaimKind.KNOWLEDGE_GAP
    if outcome is WorldModelNeedOutcome.LIMITATION:
        return "LIMITATION", WorldModelClaimKind.APPLICATION_LIMITATION
    raise _invalid(
        "PRODUCT_IMPLEMENTATION_NEED_OUTCOME_INVALID",
        "implementation Need has an unsupported assessment outcome",
    )


def _need_question(value: ProductNeedSpec) -> str:
    labels = {
        ProductNeedKind.INVENTORY: "Return the complete recursive reactor child-module inventory.",
        ProductNeedKind.METHOD_INVENTORY: "Return the complete declared Java method inventory.",
        ProductNeedKind.PATHS: "Return all simple modeled-relation paths for the exact Snapshot.",
        ProductNeedKind.NEW_PATHS: "Return modeled-relation paths present only in the target Snapshot.",
        ProductNeedKind.ORDERED_DIFF: "Return the ordered base-to-target graph change.",
        ProductNeedKind.DIRECT_DEPENDENCY: "Return exact locally declared direct internal dependencies.",
        ProductNeedKind.DIRECT_CALL: "Return exact direct Java static-call relations.",
        ProductNeedKind.SAME_NAME_IDENTITY: "Distinguish same-artifact modules by stable Root and full GA.",
        ProductNeedKind.KNOWLEDGE_GAP: "Disclose which requested semantics are outside the mounted profile coverage.",
    }
    return labels[value.kind]


def _snapshot_label(
    result_set: WorldModelQueryResultSet, snapshot_id: StableId
) -> str:
    index = result_set.read_authority.snapshot_ids.index(snapshot_id)
    if len(result_set.read_authority.snapshot_ids) == 2:
        return "A" if index == 0 else "B"
    return "当前 Snapshot"


def _public_state_change(value: Mapping[str, object]) -> dict[str, object]:
    base = value["base"]
    target = value["target"]
    fields = (
        "label",
        "module_path",
        "effective_version",
        "packaging",
        "return_type",
        "visibility",
        "modifiers",
        "source_path",
    )
    changed = {
        field: {
            "base": base["state_fields"].get(field),
            "target": target["state_fields"].get(field),
        }
        for field in fields
        if base["state_fields"].get(field) != target["state_fields"].get(field)
    }
    return {
        "root_id": value["root_id"],
        "ga": target.get("canonical_ga") or base.get("canonical_ga"),
        "changed_fields": changed,
    }


def _relation_state_change(value: Mapping[str, object]) -> dict[str, object]:
    base = value["base"]
    target = value["target"]
    return {
        "root_id": value["root_id"],
        "predicate": target["predicate"],
        "base": dict(base["predicate_state_fields"]),
        "target": dict(target["predicate_state_fields"]),
    }


def _same_artifact_groups(modules: object) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for item in modules:
        artifact = item["root_fields"]["artifact_id"]
        groups.setdefault(artifact, []).append(item["canonical_ga"])
    return {
        key: sorted(values)
        for key, values in sorted(groups.items())
        if len(values) > 1
    }


def _direct_source_ref(entity: object) -> str:
    if not isinstance(entity, Mapping):
        raise _invalid(
            "PRODUCT_DIRECT_SOURCE_INVALID",
            "direct-dependency source Entity is invalid",
        )
    canonical_ga = entity.get("canonical_ga")
    if canonical_ga is not None:
        return _text(canonical_ga, "direct-dependency source canonical GA")
    state_fields = entity.get("state_fields")
    if not isinstance(state_fields, Mapping):
        raise _invalid(
            "PRODUCT_DIRECT_SOURCE_STATE_INVALID",
            "direct-dependency source Entity State is invalid",
        )
    group = _field_text(state_fields, "effective_group_id")
    artifact = _field_text(state_fields, "artifact_id")
    return f"{group}:{artifact}"


def _field_text(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise _invalid(
            "PRODUCT_CATALOG_FIELD_INVALID",
            f"product catalog field {key!r} is invalid",
        )
    return item


def _field_text_tuple(
    value: Mapping[str, object], key: str
) -> tuple[str, ...]:
    item = value.get(key)
    if isinstance(item, (str, bytes)) or not isinstance(item, Sequence):
        raise _invalid(
            "PRODUCT_CATALOG_FIELD_INVALID",
            f"product catalog field {key!r} is invalid",
        )
    result = tuple(item)
    if not all(isinstance(part, str) and part for part in result):
        raise _invalid(
            "PRODUCT_CATALOG_FIELD_INVALID",
            f"product catalog field {key!r} is invalid",
        )
    return result


def _aliases(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {item.casefold() for item in values if isinstance(item, str) and len(item) >= 3},
            key=lambda item: (-len(item), item),
        )
    )


def _identifier_parts(value: str) -> tuple[str, ...]:
    return tuple(
        item
        for item in re.split(r"[^A-Za-z0-9]+", value)
        if len(item) >= 3
    )


def _alias_offset(text: str, alias: str) -> int | None:
    match = re.search(
        rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])",
        text,
    )
    return match.start() if match else None


def _contains_any(value: str, needles: Sequence[str]) -> bool:
    return any(item in value for item in needles)


def _json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _invalid("PRODUCT_TEXT_INVALID", f"{label} must be non-empty")
    return value


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        message,
        {"reason_code": reason_code},
    )
