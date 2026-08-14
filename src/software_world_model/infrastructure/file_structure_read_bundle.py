"""Strict canonical-file adapter for no-payload Structure Read Bundles."""

from __future__ import annotations

from datetime import datetime
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Callable, Mapping

from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.structure_read_bundle import (
    STRUCTURE_ORDERED_READ_BUNDLE_WITH_DISCOVERY_FORMAT,
    STRUCTURE_ORDERED_READ_BUNDLE_FORMAT,
    STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT,
    StructureBusinessDiscoveryRecallBinding,
    StructureBusinessDiscoveryRecallVerdict,
    StoredStructureReadBundle,
    StructureBundleUpstreamEntityRecord,
    StructureOrderedReadBundle,
    StructureSnapshotBundleReference,
    StructureSnapshotReadBundle,
)
from software_world_model.application_services.structure_read_session import (
    StructureCoverageReadBinding,
    StructureReadOrder,
    StructureReadPurpose,
    StructureReadSelectionMode,
    StructureReadSession,
    StructureSnapshotReadBinding,
)
from software_world_model.cross_cutting import (
    CanonicalizationError,
    Digest,
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    canonical_json_bytes,
)
from software_world_model.knowledge_engine.context_comparison import (
    StructureContextComparisonAssessment,
    StructureContextComparisonOutcome,
    StructureContextComparisonPurpose,
)
from software_world_model.knowledge_engine.scope import (
    AssertionOutcome,
    ScopeLifecycle,
    ScopePurpose,
    ScopeStateAssertion,
    ScopeType,
)
from software_world_model.knowledge_engine.structure import (
    CanonicalFields,
    CompleteMemberManifest,
    CoverageCompleteness,
    CoverageMember,
    CoverageMemberKind,
    CoverageRecord,
    CoverageRoot,
    CoverageState,
    EntityRecord,
    EntityRef,
    EntityRoot,
    EntityState,
    EntityType,
    LiteralFactRecord,
    LiteralFactRoot,
    LiteralFactState,
    LiteralObject,
    LiteralType,
    ObservationModality,
    PublicationMode,
    RelationFactRecord,
    RelationFactRoot,
    RelationFactState,
    RelationPredicate,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureSchemaAdoptionMode,
)
from software_world_model.knowledge_engine.structure_publication import (
    SnapshotCoverage,
    SnapshotUpstreamEntity,
    StructureEvidenceMetadata,
    StructureSnapshot,
)


_MAX_BUNDLE_BYTES = 64 * 1024 * 1024
_PAYLOAD_POLICY = {
    "evidence_observation_fields": 0,
    "evidence_excerpt_fields": 0,
    "artifact_payload_fields": 0,
    "source_payload_fields": 0,
    "provider_input_fields": 0,
}


class FileStructureReadBundleStore:
    """Write immutable canonical JSON and reject every non-canonical read."""

    def __init__(self, *, maximum_bytes: int = _MAX_BUNDLE_BYTES) -> None:
        if type(maximum_bytes) is not int or maximum_bytes < 1024:
            raise ValueError("maximum Bundle size must be at least 1024 bytes")
        self._maximum_bytes = maximum_bytes

    def write_snapshot(
        self, locator: str, bundle: StructureSnapshotReadBundle
    ) -> StoredStructureReadBundle:
        bundle.require_valid()
        return self._write(
            locator,
            bundle.document(),
            format_ref=STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT,
            bundle_digest=bundle.digest,
            parser=self.read_snapshot,
        )

    def read_snapshot(
        self, locator: str
    ) -> tuple[StructureSnapshotReadBundle, Digest]:
        document, file_digest = self._read_document(locator)
        try:
            bundle = _snapshot_bundle(document)
        except DomainError:
            raise
        except (KeyError, TypeError, ValueError, CanonicalizationError) as exc:
            raise _invalid(
                "READ_BUNDLE_DOCUMENT_INVALID",
                "Structure Snapshot Bundle document is invalid",
            ) from exc
        bundle.require_valid()
        _require_canonical_document(document, bundle.document())
        return bundle, file_digest

    def write_ordered(
        self, locator: str, bundle: StructureOrderedReadBundle
    ) -> StoredStructureReadBundle:
        bundle.require_valid()
        return self._write(
            locator,
            bundle.document(),
            format_ref=bundle.format_ref,
            bundle_digest=bundle.digest,
            parser=self.read_ordered,
        )

    def read_ordered(
        self, locator: str
    ) -> tuple[StructureOrderedReadBundle, Digest]:
        document, file_digest = self._read_document(locator)
        try:
            bundle = _ordered_bundle(document)
        except DomainError:
            raise
        except (KeyError, TypeError, ValueError, CanonicalizationError) as exc:
            raise _invalid(
                "READ_BUNDLE_DOCUMENT_INVALID",
                "ordered Structure Bundle document is invalid",
            ) from exc
        bundle.require_valid()
        _require_canonical_document(document, bundle.document())
        return bundle, file_digest

    def read_any(
        self, locator: str
    ) -> tuple[StructureSnapshotReadBundle | StructureOrderedReadBundle, Digest]:
        document, file_digest = self._read_document(locator)
        format_ref = document.get("format_ref")
        try:
            if format_ref == STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT:
                bundle = _snapshot_bundle(document)
            elif format_ref in {
                STRUCTURE_ORDERED_READ_BUNDLE_FORMAT,
                STRUCTURE_ORDERED_READ_BUNDLE_WITH_DISCOVERY_FORMAT,
            }:
                bundle = _ordered_bundle(document)
            else:
                raise _invalid(
                    "READ_BUNDLE_FORMAT_UNSUPPORTED",
                    "Structure Bundle document uses an unsupported format",
                )
        except DomainError:
            raise
        except (KeyError, TypeError, ValueError, CanonicalizationError) as exc:
            raise _invalid(
                "READ_BUNDLE_DOCUMENT_INVALID",
                "Structure Bundle document is invalid",
            ) from exc
        bundle.require_valid()
        _require_canonical_document(document, bundle.document())
        return bundle, file_digest

    def _write(
        self,
        locator: str,
        document: dict[str, object],
        *,
        format_ref: str,
        bundle_digest: Digest,
        parser: Callable[
            [str],
            tuple[StructureSnapshotReadBundle | StructureOrderedReadBundle, Digest],
        ],
    ) -> StoredStructureReadBundle:
        destination = _destination(locator)
        payload = canonical_json_bytes(document)
        if len(payload) > self._maximum_bytes:
            raise _invalid(
                "READ_BUNDLE_SIZE_LIMIT_EXCEEDED",
                "Structure Bundle exceeds the configured file size limit",
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink():
                raise _invalid(
                    "READ_BUNDLE_SYMLINK_FORBIDDEN",
                    "Structure Bundle destination cannot be a symbolic link",
                )
            existing = _read_regular_file(destination, self._maximum_bytes)
            if existing != payload:
                raise _invalid(
                    "READ_BUNDLE_DESTINATION_CONFLICT",
                    "Structure Bundle destination already contains different bytes",
                )
        else:
            temporary_name: str | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=destination.parent,
                    prefix=f".{destination.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as temporary:
                    temporary_name = temporary.name
                    temporary.write(payload)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                try:
                    os.link(temporary_name, destination)
                except FileExistsError:
                    existing = _read_regular_file(destination, self._maximum_bytes)
                    if existing != payload:
                        raise _invalid(
                            "READ_BUNDLE_DESTINATION_CONFLICT",
                            "concurrent Bundle writer published different bytes",
                        )
                _fsync_directory(destination.parent)
            finally:
                if temporary_name is not None:
                    try:
                        os.unlink(temporary_name)
                    except FileNotFoundError:
                        pass
        loaded, file_digest = parser(str(destination))
        if loaded.digest != bundle_digest:
            raise _inconsistent("written Bundle does not re-read with its exact digest")
        return StoredStructureReadBundle(
            locator=str(destination),
            format_ref=format_ref,
            bundle_digest=bundle_digest,
            file_digest=file_digest,
        )

    def _read_document(
        self, locator: str
    ) -> tuple[dict[str, object], Digest]:
        path = _source(locator)
        payload = _read_regular_file(path, self._maximum_bytes)
        try:
            text = payload.decode("utf-8", errors="strict")
            value = json.loads(text, object_pairs_hook=_strict_object)
        except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateKeyError) as exc:
            raise _invalid(
                "READ_BUNDLE_JSON_INVALID",
                "Structure Bundle must be strict duplicate-free UTF-8 JSON",
            ) from exc
        if not isinstance(value, dict):
            raise _invalid(
                "READ_BUNDLE_DOCUMENT_INVALID",
                "Structure Bundle top-level value must be an object",
            )
        try:
            canonical = canonical_json_bytes(value)
        except CanonicalizationError as exc:
            raise _invalid(
                "READ_BUNDLE_JSON_NONCANONICAL",
                "Structure Bundle contains a non-canonical JSON value",
            ) from exc
        if canonical != payload:
            raise _invalid(
                "READ_BUNDLE_JSON_NONCANONICAL",
                "Structure Bundle bytes are not the exact canonical encoding",
            )
        return value, _raw_digest(payload)


class _DuplicateKeyError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKeyError(key)
        value[key] = item
    return value


def _snapshot_bundle(document: Mapping[str, object]) -> StructureSnapshotReadBundle:
    value = _object(
        document,
        {
            "format_ref",
            "snapshot",
            "coverages",
            "entities",
            "relation_facts",
            "literal_facts",
            "upstream_entity_records",
            "evidence_metadata",
            "payload_policy",
            "bundle_digest",
        },
        "Snapshot Bundle",
    )
    if _string(value["format_ref"], "Bundle format") != STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT:
        raise _invalid(
            "READ_BUNDLE_FORMAT_UNSUPPORTED",
            "Structure Snapshot Bundle format is unsupported",
        )
    _payload_policy(value["payload_policy"])
    bundle = StructureSnapshotReadBundle(
        snapshot=_snapshot(value["snapshot"]),
        coverages=tuple(_coverage(item) for item in _array(value["coverages"], "coverages")),
        entities=tuple(_entity(item) for item in _array(value["entities"], "entities")),
        relation_facts=tuple(
            _relation(item) for item in _array(value["relation_facts"], "relation facts")
        ),
        literal_facts=tuple(
            _literal(item) for item in _array(value["literal_facts"], "literal facts")
        ),
        upstream_entity_records=tuple(
            _upstream_record(item)
            for item in _array(value["upstream_entity_records"], "upstream records")
        ),
        evidence_metadata=tuple(
            _evidence_metadata(item)
            for item in _array(value["evidence_metadata"], "Evidence metadata")
        ),
        digest=Digest(_string(value["bundle_digest"], "Bundle digest")),
    )
    return bundle


def _ordered_bundle(document: Mapping[str, object]) -> StructureOrderedReadBundle:
    format_ref = _string(document.get("format_ref"), "Bundle format")
    if format_ref not in {
        STRUCTURE_ORDERED_READ_BUNDLE_FORMAT,
        STRUCTURE_ORDERED_READ_BUNDLE_WITH_DISCOVERY_FORMAT,
    }:
        raise _invalid(
            "READ_BUNDLE_FORMAT_UNSUPPORTED",
            "ordered Structure Bundle format is unsupported",
        )
    expected_fields = {
        "format_ref",
        "session",
        "snapshots",
        "payload_policy",
        "bundle_digest",
    }
    if format_ref == STRUCTURE_ORDERED_READ_BUNDLE_WITH_DISCOVERY_FORMAT:
        expected_fields.add("business_discovery_recall_bindings")
    value = _object(
        document,
        expected_fields,
        "ordered Bundle",
    )
    _payload_policy(value["payload_policy"])
    references = []
    for item in _array(value["snapshots"], "ordered Snapshot references"):
        reference = _object(
            item,
            {
                "ordinal",
                "snapshot_id",
                "snapshot_binding_digest",
                "snapshot_manifest_digest",
                "bundle_digest",
                "file_digest",
            },
            "ordered Snapshot reference",
        )
        references.append(
            StructureSnapshotBundleReference(
                ordinal=_integer(reference["ordinal"], "reference ordinal"),
                snapshot_id=StableId(_string(reference["snapshot_id"], "Snapshot ID")),
                snapshot_binding_digest=Digest(
                    _string(reference["snapshot_binding_digest"], "binding digest")
                ),
                snapshot_manifest_digest=Digest(
                    _string(reference["snapshot_manifest_digest"], "manifest digest")
                ),
                bundle_digest=Digest(
                    _string(reference["bundle_digest"], "Bundle digest")
                ),
                file_digest=Digest(
                    _string(reference["file_digest"], "file digest")
                ),
            )
        )
    return StructureOrderedReadBundle(
        session=_session(value["session"]),
        snapshots=tuple(references),
        digest=Digest(_string(value["bundle_digest"], "Bundle digest")),
        business_discovery_recall_bindings=(
            tuple(
                _business_discovery_recall_binding(item)
                for item in _array(
                    value["business_discovery_recall_bindings"],
                    "business discovery recall bindings",
                )
            )
            if format_ref
            == STRUCTURE_ORDERED_READ_BUNDLE_WITH_DISCOVERY_FORMAT
            else ()
        ),
        format_ref=format_ref,
    )


def _business_discovery_recall_binding(
    value: object,
) -> StructureBusinessDiscoveryRecallBinding:
    item = _object(
        value,
        {
            "oracle_ref",
            "oracle_result_digest",
            "profile_ref",
            "discovery_contract_ref",
            "snapshot_id",
            "snapshot_bundle_digest",
            "counterexample_classes",
            "verdict",
            "digest",
        },
        "business discovery recall binding",
    )
    return StructureBusinessDiscoveryRecallBinding(
        oracle_ref=_string(item["oracle_ref"], "discovery Oracle ref"),
        oracle_result_digest=Digest(
            _string(item["oracle_result_digest"], "Oracle result digest")
        ),
        profile_ref=_string(item["profile_ref"], "discovery Profile ref"),
        discovery_contract_ref=_string(
            item["discovery_contract_ref"],
            "discovery Contract ref",
        ),
        snapshot_id=StableId(_string(item["snapshot_id"], "Snapshot ID")),
        snapshot_bundle_digest=Digest(
            _string(item["snapshot_bundle_digest"], "Snapshot Bundle digest")
        ),
        counterexample_classes=tuple(
            _string(entry, "counterexample class")
            for entry in _array(
                item["counterexample_classes"],
                "counterexample classes",
            )
        ),
        verdict=StructureBusinessDiscoveryRecallVerdict(
            _string(item["verdict"], "discovery recall verdict")
        ),
        digest=Digest(_string(item["digest"], "discovery binding digest")),
    )


def _snapshot(value: object) -> StructureSnapshot:
    item = _object(
        value,
        {
            "snapshot_id",
            "scope_id",
            "snapshot_revision",
            "previous_snapshot_id",
            "schema_ref",
            "schema_digest",
            "schema_adoption_mode",
            "schema_registration_digest",
            "schema_availability_digest",
            "schema_adoption_digest",
            "publication_mode",
            "members",
            "coverages",
            "upstream_entities",
            "manifest_digest",
            "published_at",
        },
        "Snapshot",
    )
    previous = item["previous_snapshot_id"]
    if previous is not None and not isinstance(previous, str):
        raise _document("Snapshot predecessor must be a string or null")
    coverages = []
    for raw in _array(item["coverages"], "Snapshot coverages"):
        coverage = _object(
            raw,
            {
                "coverage_root_id",
                "coverage_state_id",
                "coverage_state_digest",
            },
            "Snapshot Coverage binding",
        )
        coverages.append(
            SnapshotCoverage(
                coverage_root_id=StableId(
                    _string(coverage["coverage_root_id"], "Coverage Root ID")
                ),
                coverage_state_id=StableId(
                    _string(coverage["coverage_state_id"], "Coverage State ID")
                ),
                coverage_state_digest=Digest(
                    _string(coverage["coverage_state_digest"], "Coverage State digest")
                ),
            )
        )
    upstream = []
    for raw in _array(item["upstream_entities"], "Snapshot upstream entities"):
        binding = _object(
            raw,
            {
                "upstream_snapshot_id",
                "entity_root_id",
                "entity_state_id",
                "entity_state_digest",
            },
            "Snapshot upstream Entity binding",
        )
        upstream.append(
            SnapshotUpstreamEntity(
                upstream_snapshot_id=StableId(
                    _string(binding["upstream_snapshot_id"], "upstream Snapshot ID")
                ),
                entity_root_id=StableId(
                    _string(binding["entity_root_id"], "Entity Root ID")
                ),
                entity_state_id=StableId(
                    _string(binding["entity_state_id"], "Entity State ID")
                ),
                entity_state_digest=Digest(
                    _string(binding["entity_state_digest"], "Entity State digest")
                ),
            )
        )
    return StructureSnapshot(
        snapshot_id=StableId(_string(item["snapshot_id"], "Snapshot ID")),
        scope_id=StableId(_string(item["scope_id"], "Scope ID")),
        snapshot_revision=Revision(
            _integer(item["snapshot_revision"], "Snapshot revision")
        ),
        previous_snapshot_id=StableId(previous) if previous is not None else None,
        schema_ref=_string(item["schema_ref"], "Schema ref"),
        schema_digest=Digest(_string(item["schema_digest"], "Schema digest")),
        schema_adoption_mode=StructureSchemaAdoptionMode(
            _string(item["schema_adoption_mode"], "Schema adoption mode")
        ),
        schema_registration_digest=Digest(
            _string(item["schema_registration_digest"], "Schema Registration digest")
        ),
        schema_availability_digest=Digest(
            _string(item["schema_availability_digest"], "Schema Availability digest")
        ),
        schema_adoption_digest=Digest(
            _string(item["schema_adoption_digest"], "Schema Adoption digest")
        ),
        publication_mode=PublicationMode(
            _string(item["publication_mode"], "Publication mode")
        ),
        members=tuple(
            _member(raw) for raw in _array(item["members"], "Snapshot members")
        ),
        coverages=tuple(coverages),
        upstream_entities=tuple(upstream),
        manifest_digest=Digest(
            _string(item["manifest_digest"], "Snapshot manifest digest")
        ),
        published_at=_datetime(item["published_at"], "Snapshot publication time"),
    )


def _entity(value: object) -> EntityRecord:
    item = _object(value, {"root", "state"}, "Entity record")
    root_value = _object(
        item["root"],
        {
            "entity_root_id",
            "entity_type",
            "identity_scheme",
            "root_fields",
            "allocation_key_digest",
        },
        "Entity Root",
    )
    state_value = _object(
        item["state"],
        {
            "entity_state_id",
            "entity_state_digest",
            "entity_root_id",
            "entity_type",
            "state_payload_fields",
            "allocation_key_digest",
        },
        "Entity State",
    )
    root = EntityRoot(
        entity_root_id=StableId(
            _string(root_value["entity_root_id"], "Entity Root ID")
        ),
        entity_type=EntityType(_string(root_value["entity_type"], "Entity type")),
        identity_scheme=_string(root_value["identity_scheme"], "identity scheme"),
        root_fields=CanonicalFields(
            _mapping(root_value["root_fields"], "Entity Root fields")
        ),
        allocation_key_digest=Digest(
            _string(root_value["allocation_key_digest"], "Entity Root digest")
        ),
    )
    state = EntityState(
        entity_state_id=StableId(
            _string(state_value["entity_state_id"], "Entity State ID")
        ),
        entity_state_digest=Digest(
            _string(state_value["entity_state_digest"], "Entity State digest")
        ),
        entity_root_id=StableId(
            _string(state_value["entity_root_id"], "Entity Root ID")
        ),
        entity_type=EntityType(
            _string(state_value["entity_type"], "Entity State type")
        ),
        state_payload_fields=CanonicalFields(
            _mapping(state_value["state_payload_fields"], "Entity State fields")
        ),
        allocation_key_digest=Digest(
            _string(state_value["allocation_key_digest"], "Entity State allocation digest")
        ),
    )
    return EntityRecord(root=root, state=state)


def _relation(value: object) -> RelationFactRecord:
    item = _object(value, {"root", "state"}, "Relation Fact record")
    root_value = _object(
        item["root"],
        {
            "relation_root_id",
            "owning_scope_id",
            "schema_ref",
            "subject",
            "predicate",
            "object",
            "observation_modality",
            "allocation_key_digest",
        },
        "Relation Fact Root",
    )
    state_value = _object(
        item["state"],
        {
            "relation_state_id",
            "relation_state_digest",
            "relation_root_id",
            "subject_entity_state_id",
            "object_entity_state_id",
            "source_revision",
            "knowledge_context_digest",
            "evidence_references",
            "predicate_state_payload_fields",
            "allocation_key_digest",
        },
        "Relation Fact State",
    )
    root = RelationFactRoot(
        relation_root_id=StableId(
            _string(root_value["relation_root_id"], "Relation Root ID")
        ),
        owning_scope_id=StableId(
            _string(root_value["owning_scope_id"], "owning Scope ID")
        ),
        schema_ref=_string(root_value["schema_ref"], "Schema ref"),
        subject=_entity_ref(root_value["subject"]),
        predicate=RelationPredicate(
            _string(root_value["predicate"], "Relation predicate")
        ),
        object=_entity_ref(root_value["object"]),
        observation_modality=ObservationModality(
            _string(root_value["observation_modality"], "observation modality")
        ),
        allocation_key_digest=Digest(
            _string(root_value["allocation_key_digest"], "Relation Root digest")
        ),
    )
    state = RelationFactState(
        relation_state_id=StableId(
            _string(state_value["relation_state_id"], "Relation State ID")
        ),
        relation_state_digest=Digest(
            _string(state_value["relation_state_digest"], "Relation State digest")
        ),
        relation_root_id=StableId(
            _string(state_value["relation_root_id"], "Relation Root ID")
        ),
        subject_entity_state_id=StableId(
            _string(state_value["subject_entity_state_id"], "subject State ID")
        ),
        object_entity_state_id=StableId(
            _string(state_value["object_entity_state_id"], "object State ID")
        ),
        source_revision=_string(state_value["source_revision"], "source revision"),
        knowledge_context_digest=Digest(
            _string(state_value["knowledge_context_digest"], "Context digest")
        ),
        evidence_references=_stable_ids(
            state_value["evidence_references"], "Relation Evidence references"
        ),
        predicate_state_payload_fields=CanonicalFields(
            _mapping(
                state_value["predicate_state_payload_fields"],
                "predicate State fields",
            )
        ),
        allocation_key_digest=Digest(
            _string(state_value["allocation_key_digest"], "Relation State allocation digest")
        ),
    )
    return RelationFactRecord(root=root, state=state)


def _literal(value: object) -> LiteralFactRecord:
    item = _object(value, {"root", "state"}, "Literal Fact record")
    root_value = _object(
        item["root"],
        {
            "literal_root_id",
            "owning_scope_id",
            "schema_ref",
            "subject",
            "predicate",
            "object",
            "observation_modality",
            "allocation_key_digest",
        },
        "Literal Fact Root",
    )
    literal_value = _object(
        root_value["object"], {"literal_type", "value"}, "Literal object"
    )
    state_value = _object(
        item["state"],
        {
            "literal_state_id",
            "literal_state_digest",
            "literal_root_id",
            "subject_entity_state_id",
            "source_revision",
            "knowledge_context_digest",
            "evidence_references",
            "allocation_key_digest",
        },
        "Literal Fact State",
    )
    root = LiteralFactRoot(
        literal_root_id=StableId(
            _string(root_value["literal_root_id"], "Literal Root ID")
        ),
        owning_scope_id=StableId(
            _string(root_value["owning_scope_id"], "owning Scope ID")
        ),
        schema_ref=_string(root_value["schema_ref"], "Schema ref"),
        subject=_entity_ref(root_value["subject"]),
        predicate=_string(root_value["predicate"], "Literal predicate"),
        object=LiteralObject(
            literal_type=LiteralType(
                _string(literal_value["literal_type"], "literal type")
            ),
            value=_literal_scalar(literal_value["value"]),
        ),
        observation_modality=_string(
            root_value["observation_modality"], "observation modality"
        ),
        allocation_key_digest=Digest(
            _string(root_value["allocation_key_digest"], "Literal Root digest")
        ),
    )
    state = LiteralFactState(
        literal_state_id=StableId(
            _string(state_value["literal_state_id"], "Literal State ID")
        ),
        literal_state_digest=Digest(
            _string(state_value["literal_state_digest"], "Literal State digest")
        ),
        literal_root_id=StableId(
            _string(state_value["literal_root_id"], "Literal Root ID")
        ),
        subject_entity_state_id=StableId(
            _string(state_value["subject_entity_state_id"], "subject State ID")
        ),
        source_revision=_string(state_value["source_revision"], "source revision"),
        knowledge_context_digest=Digest(
            _string(state_value["knowledge_context_digest"], "Context digest")
        ),
        evidence_references=_stable_ids(
            state_value["evidence_references"], "Literal Evidence references"
        ),
        allocation_key_digest=Digest(
            _string(state_value["allocation_key_digest"], "Literal State allocation digest")
        ),
    )
    return LiteralFactRecord(root=root, state=state)


def _coverage(value: object) -> CoverageRecord:
    item = _object(value, {"root", "state"}, "Coverage record")
    root_value = _object(
        item["root"],
        {
            "coverage_root_id",
            "coverage_root_ref",
            "owning_scope_id",
            "profile_ref",
            "schema_ref",
            "schema_digest",
            "source_binding_id",
            "logical_reactor_root",
            "maven_evaluation_context_ref",
            "maven_evaluation_context_digest",
            "covered_entity_types",
            "covered_relation_predicates",
            "canonicalization_ref",
            "canonicalization_digest",
            "allocation_key_digest",
        },
        "Coverage Root",
    )
    state_value = _object(
        item["state"],
        {
            "coverage_state_id",
            "coverage_state_digest",
            "coverage_root_id",
            "source_revision",
            "knowledge_context_digest",
            "schema_ref",
            "schema_digest",
            "maven_evaluation_context_ref",
            "maven_evaluation_context_digest",
            "canonicalization_ref",
            "canonicalization_digest",
            "complete_member_manifest",
            "evidence_references",
            "allocation_key_digest",
        },
        "Coverage State",
    )
    manifest_value = _object(
        state_value["complete_member_manifest"],
        {"completeness", "members", "digest"},
        "complete member Manifest",
    )
    manifest = CompleteMemberManifest(
        members=tuple(
            _member(raw)
            for raw in _array(manifest_value["members"], "Coverage members")
        ),
        digest=Digest(_string(manifest_value["digest"], "member Manifest digest")),
        completeness=CoverageCompleteness(
            _string(manifest_value["completeness"], "Coverage completeness")
        ),
    )
    root = CoverageRoot(
        coverage_root_id=StableId(
            _string(root_value["coverage_root_id"], "Coverage Root ID")
        ),
        coverage_root_ref=_string(root_value["coverage_root_ref"], "Coverage Root ref"),
        owning_scope_id=StableId(
            _string(root_value["owning_scope_id"], "owning Scope ID")
        ),
        profile_ref=_string(root_value["profile_ref"], "Profile ref"),
        schema_ref=_string(root_value["schema_ref"], "Schema ref"),
        schema_digest=Digest(_string(root_value["schema_digest"], "Schema digest")),
        source_binding_id=StableId(
            _string(root_value["source_binding_id"], "Source Binding ID")
        ),
        logical_reactor_root=_string(
            root_value["logical_reactor_root"], "logical reactor root"
        ),
        maven_evaluation_context_ref=_string(
            root_value["maven_evaluation_context_ref"], "Evaluation Context ref"
        ),
        maven_evaluation_context_digest=Digest(
            _string(
                root_value["maven_evaluation_context_digest"],
                "Evaluation Context digest",
            )
        ),
        covered_entity_types=tuple(
            EntityType(_string(raw, "covered Entity type"))
            for raw in _array(root_value["covered_entity_types"], "covered Entity types")
        ),
        covered_relation_predicates=tuple(
            RelationPredicate(_string(raw, "covered Relation predicate"))
            for raw in _array(
                root_value["covered_relation_predicates"],
                "covered Relation predicates",
            )
        ),
        canonicalization_ref=_string(
            root_value["canonicalization_ref"], "Canonicalization ref"
        ),
        canonicalization_digest=Digest(
            _string(root_value["canonicalization_digest"], "Canonicalization digest")
        ),
        allocation_key_digest=Digest(
            _string(root_value["allocation_key_digest"], "Coverage Root digest")
        ),
    )
    state = CoverageState(
        coverage_state_id=StableId(
            _string(state_value["coverage_state_id"], "Coverage State ID")
        ),
        coverage_state_digest=Digest(
            _string(state_value["coverage_state_digest"], "Coverage State digest")
        ),
        coverage_root_id=StableId(
            _string(state_value["coverage_root_id"], "Coverage Root ID")
        ),
        source_revision=_string(state_value["source_revision"], "source revision"),
        knowledge_context_digest=Digest(
            _string(state_value["knowledge_context_digest"], "Context digest")
        ),
        schema_ref=_string(state_value["schema_ref"], "Schema ref"),
        schema_digest=Digest(_string(state_value["schema_digest"], "Schema digest")),
        maven_evaluation_context_ref=_string(
            state_value["maven_evaluation_context_ref"], "Evaluation Context ref"
        ),
        maven_evaluation_context_digest=Digest(
            _string(
                state_value["maven_evaluation_context_digest"],
                "Evaluation Context digest",
            )
        ),
        canonicalization_ref=_string(
            state_value["canonicalization_ref"], "Canonicalization ref"
        ),
        canonicalization_digest=Digest(
            _string(state_value["canonicalization_digest"], "Canonicalization digest")
        ),
        complete_member_manifest=manifest,
        evidence_references=_stable_ids(
            state_value["evidence_references"], "Coverage Evidence references"
        ),
        allocation_key_digest=Digest(
            _string(state_value["allocation_key_digest"], "Coverage State allocation digest")
        ),
    )
    return CoverageRecord(root=root, state=state)


def _upstream_record(value: object) -> StructureBundleUpstreamEntityRecord:
    item = _object(value, {"snapshot_id", "entity"}, "upstream Entity record")
    return StructureBundleUpstreamEntityRecord(
        snapshot_id=StableId(_string(item["snapshot_id"], "upstream Snapshot ID")),
        entity=_entity(item["entity"]),
    )


def _evidence_metadata(value: object) -> StructureEvidenceMetadata:
    item = _object(
        value,
        {
            "evidence_id",
            "artifact_id",
            "source_context_id",
            "byte_start",
            "byte_end",
            "locator",
            "excerpt_digest",
            "artifact_content_digest",
            "digest",
        },
        "Evidence metadata",
    )
    return StructureEvidenceMetadata(
        evidence_id=StableId(_string(item["evidence_id"], "Evidence ID")),
        artifact_id=StableId(_string(item["artifact_id"], "Artifact ID")),
        source_context_id=StableId(
            _string(item["source_context_id"], "Source Context ID")
        ),
        byte_start=_integer(item["byte_start"], "Evidence byte start"),
        byte_end=_integer(item["byte_end"], "Evidence byte end"),
        locator=_string(item["locator"], "Evidence locator"),
        excerpt_digest=Digest(
            _string(item["excerpt_digest"], "Evidence excerpt digest")
        ),
        artifact_content_digest=Digest(
            _string(item["artifact_content_digest"], "Artifact content digest")
        ),
        digest=Digest(_string(item["digest"], "Evidence digest")),
    )


def _session(value: object) -> StructureReadSession:
    item = _object(
        value,
        {
            "session_id",
            "request_digest",
            "scope_id",
            "scope_revision",
            "task_boundary",
            "scope_assertion",
            "caller_ref",
            "purpose",
            "selection_mode",
            "order",
            "snapshots",
            "context_comparisons",
            "read_set_digest",
            "opened_at",
            "digest",
        },
        "Structure read Session",
    )
    boundary_value = _object(
        item["task_boundary"],
        {
            "task_id",
            "task_revision",
            "scope_id",
            "purpose",
            "classification",
            "digest",
        },
        "Task Boundary",
    )
    boundary = TaskBoundary(
        task_id=StableId(_string(boundary_value["task_id"], "Task ID")),
        task_revision=Revision(
            _integer(boundary_value["task_revision"], "Task revision")
        ),
        scope_id=StableId(_string(boundary_value["scope_id"], "Task Scope ID")),
        purpose=_string(boundary_value["purpose"], "Task purpose"),
        classification=_string(
            boundary_value["classification"], "Task classification"
        ),
        digest=Digest(_string(boundary_value["digest"], "Task Boundary digest")),
    )
    assertion_value = _object(
        item["scope_assertion"],
        {
            "assertion_id",
            "scope_id",
            "scope_type",
            "definition_revision",
            "lifecycle",
            "purpose",
            "outcome",
            "caller_ref",
            "request_ref",
            "classification",
            "read_at",
            "digest",
        },
        "Scope assertion",
    )
    assertion = ScopeStateAssertion(
        assertion_id=StableId(
            _string(assertion_value["assertion_id"], "Scope assertion ID")
        ),
        scope_id=StableId(_string(assertion_value["scope_id"], "Scope ID")),
        scope_type=ScopeType(_string(assertion_value["scope_type"], "Scope type")),
        definition_revision=Revision(
            _integer(assertion_value["definition_revision"], "Scope revision")
        ),
        lifecycle=ScopeLifecycle(
            _string(assertion_value["lifecycle"], "Scope lifecycle")
        ),
        purpose=ScopePurpose(_string(assertion_value["purpose"], "Scope purpose")),
        outcome=AssertionOutcome(
            _string(assertion_value["outcome"], "Scope assertion outcome")
        ),
        caller_ref=_string(assertion_value["caller_ref"], "caller ref"),
        request_ref=_string(assertion_value["request_ref"], "request ref"),
        classification=_string(
            assertion_value["classification"], "classification"
        ),
        read_at=_datetime(assertion_value["read_at"], "Scope assertion time"),
        digest=Digest(_string(assertion_value["digest"], "Scope assertion digest")),
    )
    snapshots = tuple(
        _snapshot_binding(raw)
        for raw in _array(item["snapshots"], "Session Snapshot bindings")
    )
    comparisons = []
    for raw in _array(item["context_comparisons"], "Context comparisons"):
        comparison = _object(
            raw,
            {
                "assessment_id",
                "ordinal",
                "purpose",
                "base_snapshot_id",
                "base_snapshot_binding_digest",
                "target_snapshot_id",
                "target_snapshot_binding_digest",
                "base_knowledge_context_digests",
                "target_knowledge_context_digests",
                "comparison_basis_digests",
                "outcome",
                "digest",
            },
            "Context comparison",
        )
        comparisons.append(
            StructureContextComparisonAssessment(
                assessment_id=StableId(
                    _string(comparison["assessment_id"], "assessment ID")
                ),
                ordinal=_integer(comparison["ordinal"], "comparison ordinal"),
                purpose=StructureContextComparisonPurpose(
                    _string(comparison["purpose"], "comparison purpose")
                ),
                base_snapshot_id=StableId(
                    _string(comparison["base_snapshot_id"], "base Snapshot ID")
                ),
                base_snapshot_binding_digest=Digest(
                    _string(
                        comparison["base_snapshot_binding_digest"],
                        "base binding digest",
                    )
                ),
                target_snapshot_id=StableId(
                    _string(comparison["target_snapshot_id"], "target Snapshot ID")
                ),
                target_snapshot_binding_digest=Digest(
                    _string(
                        comparison["target_snapshot_binding_digest"],
                        "target binding digest",
                    )
                ),
                base_knowledge_context_digests=_digests(
                    comparison["base_knowledge_context_digests"],
                    "base Context digests",
                ),
                target_knowledge_context_digests=_digests(
                    comparison["target_knowledge_context_digests"],
                    "target Context digests",
                ),
                comparison_basis_digests=_digests(
                    comparison["comparison_basis_digests"],
                    "comparison basis digests",
                ),
                outcome=StructureContextComparisonOutcome(
                    _string(comparison["outcome"], "comparison outcome")
                ),
                digest=Digest(
                    _string(comparison["digest"], "comparison digest")
                ),
            )
        )
    return StructureReadSession(
        session_id=StableId(_string(item["session_id"], "Session ID")),
        request_digest=Digest(_string(item["request_digest"], "request digest")),
        scope_id=StableId(_string(item["scope_id"], "Scope ID")),
        scope_revision=Revision(_integer(item["scope_revision"], "Scope revision")),
        task_boundary=boundary,
        scope_assertion=assertion,
        caller_ref=_string(item["caller_ref"], "caller ref"),
        purpose=StructureReadPurpose(_string(item["purpose"], "read purpose")),
        selection_mode=StructureReadSelectionMode(
            _string(item["selection_mode"], "selection mode")
        ),
        order=StructureReadOrder(_string(item["order"], "read order")),
        snapshots=snapshots,
        context_comparisons=tuple(comparisons),
        read_set_digest=Digest(_string(item["read_set_digest"], "read set digest")),
        opened_at=_datetime(item["opened_at"], "Session opening time"),
        digest=Digest(_string(item["digest"], "Session digest")),
    )


def _snapshot_binding(value: object) -> StructureSnapshotReadBinding:
    item = _object(
        value,
        {
            "scope_id",
            "snapshot_id",
            "snapshot_revision",
            "snapshot_manifest_digest",
            "schema_ref",
            "schema_digest",
            "schema_registration_digest",
            "schema_availability_digest",
            "schema_adoption_digest",
            "coverages",
            "coverage_set_digest",
            "digest",
        },
        "Snapshot read binding",
    )
    coverages = []
    for raw in _array(item["coverages"], "Coverage read bindings"):
        coverage = _object(
            raw,
            {
                "coverage_root_id",
                "coverage_root_digest",
                "coverage_root_ref",
                "coverage_state_id",
                "coverage_state_digest",
                "profile_ref",
                "schema_ref",
                "schema_digest",
                "source_binding_id",
                "logical_reactor_root",
                "evaluation_context_ref",
                "evaluation_context_digest",
                "canonicalization_ref",
                "canonicalization_digest",
                "knowledge_context_digest",
                "source_revision",
                "member_manifest_digest",
                "comparison_basis_digest",
                "digest",
            },
            "Coverage read binding",
        )
        coverages.append(
            StructureCoverageReadBinding(
                coverage_root_id=StableId(
                    _string(coverage["coverage_root_id"], "Coverage Root ID")
                ),
                coverage_root_digest=Digest(
                    _string(coverage["coverage_root_digest"], "Coverage Root digest")
                ),
                coverage_root_ref=_string(
                    coverage["coverage_root_ref"], "Coverage Root ref"
                ),
                coverage_state_id=StableId(
                    _string(coverage["coverage_state_id"], "Coverage State ID")
                ),
                coverage_state_digest=Digest(
                    _string(coverage["coverage_state_digest"], "Coverage State digest")
                ),
                profile_ref=_string(coverage["profile_ref"], "Profile ref"),
                schema_ref=_string(coverage["schema_ref"], "Schema ref"),
                schema_digest=Digest(
                    _string(coverage["schema_digest"], "Schema digest")
                ),
                source_binding_id=StableId(
                    _string(coverage["source_binding_id"], "Source Binding ID")
                ),
                logical_reactor_root=_string(
                    coverage["logical_reactor_root"], "logical reactor root"
                ),
                evaluation_context_ref=_string(
                    coverage["evaluation_context_ref"], "Evaluation Context ref"
                ),
                evaluation_context_digest=Digest(
                    _string(
                        coverage["evaluation_context_digest"],
                        "Evaluation Context digest",
                    )
                ),
                canonicalization_ref=_string(
                    coverage["canonicalization_ref"], "Canonicalization ref"
                ),
                canonicalization_digest=Digest(
                    _string(
                        coverage["canonicalization_digest"],
                        "Canonicalization digest",
                    )
                ),
                knowledge_context_digest=Digest(
                    _string(
                        coverage["knowledge_context_digest"],
                        "Knowledge Context digest",
                    )
                ),
                source_revision=_string(
                    coverage["source_revision"], "source revision"
                ),
                member_manifest_digest=Digest(
                    _string(
                        coverage["member_manifest_digest"],
                        "member Manifest digest",
                    )
                ),
                comparison_basis_digest=Digest(
                    _string(
                        coverage["comparison_basis_digest"],
                        "comparison basis digest",
                    )
                ),
                digest=Digest(_string(coverage["digest"], "Coverage binding digest")),
            )
        )
    return StructureSnapshotReadBinding(
        scope_id=StableId(_string(item["scope_id"], "Scope ID")),
        snapshot_id=StableId(_string(item["snapshot_id"], "Snapshot ID")),
        snapshot_revision=Revision(
            _integer(item["snapshot_revision"], "Snapshot revision")
        ),
        snapshot_manifest_digest=Digest(
            _string(item["snapshot_manifest_digest"], "Snapshot manifest digest")
        ),
        schema_ref=_string(item["schema_ref"], "Schema ref"),
        schema_digest=Digest(_string(item["schema_digest"], "Schema digest")),
        schema_registration_digest=Digest(
            _string(item["schema_registration_digest"], "Schema Registration digest")
        ),
        schema_availability_digest=Digest(
            _string(item["schema_availability_digest"], "Schema Availability digest")
        ),
        schema_adoption_digest=Digest(
            _string(item["schema_adoption_digest"], "Schema Adoption digest")
        ),
        coverages=tuple(coverages),
        coverage_set_digest=Digest(
            _string(item["coverage_set_digest"], "Coverage set digest")
        ),
        digest=Digest(_string(item["digest"], "Snapshot binding digest")),
    )


def _member(value: object) -> CoverageMember:
    item = _object(
        value,
        {"kind", "root_id", "state_id", "state_digest"},
        "Coverage member",
    )
    return CoverageMember(
        kind=CoverageMemberKind(_string(item["kind"], "member kind")),
        root_id=StableId(_string(item["root_id"], "member Root ID")),
        state_id=StableId(_string(item["state_id"], "member State ID")),
        state_digest=Digest(_string(item["state_digest"], "member State digest")),
    )


def _entity_ref(value: object) -> EntityRef:
    item = _object(
        value,
        {"entity_root_id", "entity_type", "owning_scope_id"},
        "Entity ref",
    )
    return EntityRef(
        entity_root_id=StableId(_string(item["entity_root_id"], "Entity Root ID")),
        entity_type=EntityType(_string(item["entity_type"], "Entity type")),
        owning_scope_id=StableId(_string(item["owning_scope_id"], "owning Scope ID")),
    )


def _payload_policy(value: object) -> None:
    item = _object(value, set(_PAYLOAD_POLICY), "payload policy")
    if item != _PAYLOAD_POLICY:
        raise _invalid(
            "READ_BUNDLE_PAYLOAD_POLICY_INVALID",
            "Structure Bundle must declare zero forbidden payload fields",
        )


def _destination(locator: object) -> Path:
    value = _path_text(locator, "Bundle destination")
    raw = Path(value)
    parent = raw.parent.resolve(strict=False)
    return parent / raw.name


def _source(locator: object) -> Path:
    value = _path_text(locator, "Bundle locator")
    raw = Path(value)
    if raw.is_symlink():
        raise _invalid(
            "READ_BUNDLE_SYMLINK_FORBIDDEN",
            "Structure Bundle locator cannot be a symbolic link",
        )
    # Resolve only the parent.  Resolving the leaf would follow a symbolic link
    # after the check above and create a check/use race.  The descriptor open
    # below independently refuses a symbolic-link leaf.
    return raw.parent.resolve(strict=True) / raw.name


def _read_regular_file(path: Path, maximum_bytes: int) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise _invalid(
                "READ_BUNDLE_SYMLINK_FORBIDDEN",
                "Structure Bundle locator cannot be a symbolic link",
            ) from exc
        raise
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise _invalid(
                "READ_BUNDLE_FILE_TYPE_INVALID",
                "Structure Bundle must be a regular file",
            )
        if metadata.st_size > maximum_bytes:
            raise _invalid(
                "READ_BUNDLE_SIZE_LIMIT_EXCEEDED",
                "Structure Bundle exceeds the configured file size limit",
            )
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
    finally:
        os.close(descriptor)
    if len(payload) > maximum_bytes:
        raise _invalid(
            "READ_BUNDLE_SIZE_LIMIT_EXCEEDED",
            "Structure Bundle exceeds the configured file size limit",
        )
    return payload


def _require_canonical_document(
    actual: Mapping[str, object], expected: Mapping[str, object]
) -> None:
    if canonical_json_bytes(actual) != canonical_json_bytes(expected):
        raise _invalid(
            "READ_BUNDLE_DOCUMENT_NONCANONICAL",
            "Structure Bundle document is not the exact typed canonical encoding",
        )


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _raw_digest(value: bytes) -> Digest:
    return Digest(f"sha256:{hashlib.sha256(value).hexdigest()}")


def _object(
    value: object, keys: set[str], label: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise _invalid(
            "READ_BUNDLE_FIELD_SET_INVALID",
            f"{label} has missing or unknown fields",
        )
    return value


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise _document(f"{label} must be an object")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise _document(f"{label} must be an array")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise _document(f"{label} must be a string")
    return value


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise _document(f"{label} must be an integer")
    return value


def _literal_scalar(value: object) -> bool | int | str:
    if type(value) not in (bool, int, str):
        raise _document("Literal value has an unsupported JSON type")
    return value


def _stable_ids(value: object, label: str) -> tuple[StableId, ...]:
    return tuple(StableId(_string(item, label)) for item in _array(value, label))


def _digests(value: object, label: str) -> tuple[Digest, ...]:
    return tuple(Digest(_string(item, label)) for item in _array(value, label))


def _datetime(value: object, label: str) -> datetime:
    text = _string(value, label)
    if not text.endswith("Z"):
        raise _document(f"{label} must use canonical UTC Z form")
    parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _document(f"{label} must include a timezone")
    return parsed


def _path_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise _invalid(
            "READ_BUNDLE_LOCATOR_INVALID",
            f"{label} must be a non-empty filesystem path",
        )
    return value


def _document(message: str) -> DomainError:
    return _invalid("READ_BUNDLE_DOCUMENT_INVALID", message)


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


__all__ = ["FileStructureReadBundleStore"]
