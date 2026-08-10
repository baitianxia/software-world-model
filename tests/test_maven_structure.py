from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from software_world_model.application_services.maven_structure import (
    BuildExclusion,
    GitEntryMetadata,
    MavenEvaluationInput,
    MavenStructureError,
    MavenStructureErrorCode,
    PomEvidenceMetadata,
    evaluate_maven_reactor,
)
from software_world_model.cross_cutting import Digest, StableId, digest_of
from software_world_model.knowledge_engine.structure import (
    CoverageMemberKind,
    EntityType,
    PublicationMode,
    RelationPredicate,
    StructureEvidence,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "fixtures"
    / "maven-identity"
)
SCOPE_ID = StableId("scope_11111111111111111111111111111111")
SOURCE_BINDING_ID = StableId("binding_22222222222222222222222222222222")


def _stable(kind: str, value: str) -> StableId:
    return StableId(f"{kind}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[-32:]}")


def _content_digest(payload: bytes) -> Digest:
    return Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")


def _fixture_input(
    name: str,
    *,
    source_revision: str = "revision-a",
    reverse: bool = False,
) -> MavenEvaluationInput:
    root = FIXTURE_ROOT / name
    paths = sorted(root.rglob("pom.xml"))
    pairs: list[tuple[str, bytes]] = [
        (path.relative_to(root).as_posix(), path.read_bytes()) for path in paths
    ]
    if reverse:
        pairs.reverse()
    pom_bytes = dict(pairs)
    source_context_id = _stable("context", source_revision)
    entries = {
        path: GitEntryMetadata(
            mode="100644",
            object_type="blob",
            object_id=hashlib.sha1(payload).hexdigest(),
        )
        for path, payload in pairs
    }
    evidence = {
        path: PomEvidenceMetadata(
            artifact_id=_stable("artifact", f"{source_revision}:{path}"),
            source_context_id=source_context_id,
            artifact_content_digest=_content_digest(payload),
            locator=path,
        )
        for path, payload in pairs
    }
    if name == "invalid-git-symlink":
        spec = json.loads((root / "symlink-spec.json").read_text(encoding="utf-8"))
        entries[spec["link_path"]] = GitEntryMetadata(
            mode=spec["required_git_mode"],
            object_type="blob",
            object_id="f" * 40,
        )
    tree_excerpt = "\n".join(
        json.dumps(
            {
                "is_symlink": metadata.is_symlink,
                "mode": metadata.mode,
                "object_id": metadata.object_id,
                "path": path,
                "type": metadata.object_type,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for path, metadata in sorted(entries.items())
    )
    tree_payload = tree_excerpt.encode("utf-8")
    tree_evidence = StructureEvidence.create(
        artifact_id=_stable("artifact", f"tree:{source_revision}:{name}"),
        source_context_id=source_context_id,
        byte_start=0,
        byte_end=len(tree_payload),
        locator=f"git-tree:{source_revision}:all",
        excerpt=tree_excerpt,
        artifact_content_digest=_content_digest(tree_payload),
    )
    return MavenEvaluationInput(
        owning_scope_id=SCOPE_ID,
        canonical_system_key=f"fixture:{name}",
        source_binding_id=SOURCE_BINDING_ID,
        source_revision=source_revision,
        knowledge_context_digest=digest_of(
            {"source_revision": source_revision, "profile": "maven-structure"}
        ),
        pom_bytes=pom_bytes,
        git_entries=entries,
        pom_evidence=evidence,
        tree_evidence=(tree_evidence,),
    )


def _record_ga(record: object) -> str:
    root = record.root
    if root.entity_type is EntityType.SOFTWARE_SYSTEM:
        fields = record.state.state_payload_fields
    else:
        fields = root.root_fields
    return f"{fields['effective_group_id']}:{fields['artifact_id']}"


def _edge_set(result: object) -> set[tuple[str, str]]:
    by_root = {record.root_id: _record_ga(record) for record in result.entities}
    return {
        (
            by_root[relation.root.subject.entity_root_id],
            by_root[relation.root.object.entity_root_id],
        )
        for relation in result.relations
        if relation.root.predicate is RelationPredicate.DEPENDS_ON
    }


def _with_tree_excerpt(
    value: MavenEvaluationInput, excerpt: str
) -> MavenEvaluationInput:
    original = value.tree_evidence[0]
    encoded = excerpt.encode("utf-8")
    evidence = StructureEvidence.create(
        artifact_id=original.artifact_id,
        source_context_id=original.source_context_id,
        byte_start=0,
        byte_end=len(encoded),
        locator=original.locator,
        excerpt=excerpt,
        artifact_content_digest=_content_digest(encoded),
    )
    return MavenEvaluationInput(
        owning_scope_id=value.owning_scope_id,
        canonical_system_key=value.canonical_system_key,
        source_binding_id=value.source_binding_id,
        source_revision=value.source_revision,
        knowledge_context_digest=value.knowledge_context_digest,
        pom_bytes=value.pom_bytes,
        git_entries=value.git_entries,
        pom_evidence=value.pom_evidence,
        tree_evidence=(evidence,),
        logical_reactor_root=value.logical_reactor_root,
    )


def _inline_input(
    pom_bytes: dict[str, bytes], *, canonical_system_key: str
) -> MavenEvaluationInput:
    source_revision = "revision-a"
    source_context_id = _stable("context", source_revision)
    entries = {
        path: GitEntryMetadata(
            mode="100644",
            object_type="blob",
            object_id=hashlib.sha1(payload).hexdigest(),
        )
        for path, payload in sorted(pom_bytes.items())
    }
    evidence = {
        path: PomEvidenceMetadata(
            artifact_id=_stable("artifact", f"{source_revision}:{path}"),
            source_context_id=source_context_id,
            artifact_content_digest=_content_digest(payload),
            locator=path,
        )
        for path, payload in sorted(pom_bytes.items())
    }
    tree_excerpt = "\n".join(
        json.dumps(
            {
                "is_symlink": metadata.is_symlink,
                "mode": metadata.mode,
                "object_id": metadata.object_id,
                "path": path,
                "type": metadata.object_type,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for path, metadata in sorted(entries.items())
    )
    tree_payload = tree_excerpt.encode("utf-8")
    return MavenEvaluationInput(
        owning_scope_id=SCOPE_ID,
        canonical_system_key=canonical_system_key,
        source_binding_id=SOURCE_BINDING_ID,
        source_revision=source_revision,
        knowledge_context_digest=digest_of(
            {"source_revision": source_revision, "profile": "maven-structure"}
        ),
        pom_bytes=pom_bytes,
        git_entries=entries,
        pom_evidence=evidence,
        tree_evidence=(
            StructureEvidence.create(
                artifact_id=_stable(
                    "artifact", f"tree:{canonical_system_key}"
                ),
                source_context_id=source_context_id,
                byte_start=0,
                byte_end=len(tree_payload),
                locator=f"git-tree:{source_revision}:all",
                excerpt=tree_excerpt,
                artifact_content_digest=_content_digest(tree_payload),
            ),
        ),
    )


def _evidence_locators(
    result: object, references: object
) -> set[str]:
    by_id = {item.evidence_id.value: item.locator for item in result.evidence}
    return {
        by_id[reference.value if hasattr(reference, "value") else str(reference)]
        for reference in references
    }


class MavenStructureEvaluatorTests(TestCase):
    def test_valid_fixture_builds_typed_complete_closure_without_name_stitching(
        self,
    ) -> None:
        result = evaluate_maven_reactor(_fixture_input("valid"))

        self.assertEqual(
            {_record_ga(module) for module in result.modules},
            {
                "org.example.aggregate:libs-aggregator",
                "org.example.shared:common-lib",
                "org.example.legacy:common-lib",
                "org.example.services:services-aggregator",
                "org.example.services:billing",
            },
        )
        contains = [
            relation
            for relation in result.relations
            if relation.root.predicate is RelationPredicate.CONTAINS_MODULE
        ]
        depends = [
            relation
            for relation in result.relations
            if relation.root.predicate is RelationPredicate.DEPENDS_ON
        ]
        self.assertEqual(len(contains), 5)
        self.assertEqual(len(depends), 2)
        self.assertEqual(
            _edge_set(result),
            {
                (
                    "org.example.root:structure-fixture",
                    "org.example.shared:common-lib",
                ),
                (
                    "org.example.services:billing",
                    "org.example.shared:common-lib",
                ),
            },
        )
        self.assertNotIn(
            (
                "org.example.services:billing",
                "org.example.legacy:common-lib",
            ),
            _edge_set(result),
        )

        self.assertEqual(
            {item.reason_code for item in result.exclusions},
            {"GA_NOT_IN_REACTOR_CHILD_SET", "REACTOR_TARGET_VERSION_MISMATCH"},
        )
        self.assertTrue(all(isinstance(item, BuildExclusion) for item in result.exclusions))
        self.assertEqual(len(result.report.dependency_declarations), 4)
        self.assertTrue(result.report.complete)
        state_lines = tuple(
            line
            for line in result.report.lines
            if line.startswith(("ROOT ", "MODULE ", "RELATION ", "COVERAGE "))
        )
        self.assertTrue(state_lines)
        self.assertTrue(
            all("state_digest=sha256:" in line and "evidence=" in line for line in state_lines)
        )
        self.assertIn("git-tree:revision-a:all", next(
            line for line in result.report.lines if line.startswith("COVERAGE ")
        ))
        self.assertEqual(result.coverage.state.complete_member_manifest, result.complete_member_manifest)
        self.assertEqual(
            len(result.complete_member_manifest.members),
            len(result.entities) + len(result.relations),
        )
        self.assertEqual(
            {member.kind for member in result.complete_member_manifest.members},
            {CoverageMemberKind.ENTITY, CoverageMemberKind.RELATION_FACT},
        )
        self.assertEqual(result.batch.publication_mode, PublicationMode.REPLACE_COVERAGE)
        self.assertEqual(result.batch.entities, result.entities)
        self.assertEqual(result.batch.relation_facts, result.relations)
        self.assertEqual(result.batch.evidence, result.evidence)
        result.batch.require_admissible()

        evidence_ids = {item.evidence_id for item in result.evidence}
        self.assertTrue(all(isinstance(item, StructureEvidence) for item in result.evidence))
        for entity in result.entities:
            self.assertTrue(set(entity.state.evidence_references).issubset(evidence_ids))
        for relation in result.relations:
            self.assertTrue(set(relation.state.evidence_references).issubset(evidence_ids))
        self.assertTrue(
            set(result.coverage.state.evidence_references).issubset(evidence_ids)
        )
        tree_ids = {
            item.evidence_id
            for item in result.evidence
            if item.locator.startswith("git-tree:")
        }
        self.assertTrue(tree_ids)
        self.assertTrue(
            tree_ids.issubset(set(result.coverage.state.evidence_references))
        )

        entities_by_ga = {_record_ga(item): item for item in result.entities}
        self.assertEqual(
            _evidence_locators(
                result,
                entities_by_ga[
                    "org.example.services:billing"
                ].state.evidence_references,
            ),
            {
                "services/billing-source/pom.xml",
                "services/pom.xml",
            },
        )
        self.assertEqual(
            _evidence_locators(
                result,
                entities_by_ga[
                    "org.example.shared:common-lib"
                ].state.evidence_references,
            ),
            {
                "libraries/shared-source/pom.xml",
                "libraries/pom.xml",
            },
        )
        entity_ga_by_root = {
            item.root_id: _record_ga(item) for item in result.entities
        }
        billing_to_shared = next(
            item
            for item in result.relations
            if item.root.predicate is RelationPredicate.DEPENDS_ON
            and entity_ga_by_root[item.root.subject.entity_root_id]
            == "org.example.services:billing"
            and entity_ga_by_root[item.root.object.entity_root_id]
            == "org.example.shared:common-lib"
        )
        dependency_provenance = {
            "services/billing-source/pom.xml",
            "services/pom.xml",
            "libraries/shared-source/pom.xml",
            "libraries/pom.xml",
        }
        self.assertEqual(
            _evidence_locators(
                result, billing_to_shared.state.evidence_references
            ),
            dependency_provenance,
        )
        billing_to_shared_report = next(
            item
            for item in result.report.dependency_declarations
            if item.consumer_gav == "org.example.services:billing:1.0.0"
            and item.resolved_dependency_ga == "org.example.shared:common-lib"
        )
        self.assertEqual(
            _evidence_locators(
                result, billing_to_shared_report.evidence_references
            ),
            dependency_provenance,
        )
        legacy_mismatch = next(
            item
            for item in result.exclusions
            if item.resolved_dependency_ga == "org.example.legacy:common-lib"
        )
        self.assertEqual(
            _evidence_locators(result, legacy_mismatch.evidence_references),
            {
                "services/billing-source/pom.xml",
                "services/pom.xml",
                "libraries/legacy-source/pom.xml",
                "libraries/pom.xml",
            },
        )
        external = next(
            item
            for item in result.exclusions
            if item.resolved_dependency_ga
            == "org.junit.jupiter:junit-jupiter-api"
        )
        self.assertEqual(
            _evidence_locators(result, external.evidence_references),
            {
                "services/billing-source/pom.xml",
                "services/pom.xml",
            },
        )

        manifest_text = repr(result.complete_member_manifest.canonical_value())
        self.assertNotIn("EXCLUDED", manifest_text)
        self.assertNotIn("REACTOR_TARGET_VERSION_MISMATCH", manifest_text)

    def test_parent_dependencies_are_not_reattributed_and_child_property_wins(
        self,
    ) -> None:
        result = evaluate_maven_reactor(
            _fixture_input("valid-parent-local-dependency")
        )

        self.assertEqual(
            _edge_set(result),
            {
                (
                    "org.example.inheritance:dependency-parent",
                    "org.example.inheritance:inheritance-lib",
                ),
                (
                    "org.example.inheritance:override-child",
                    "org.example.inheritance:inheritance-lib",
                ),
            },
        )
        self.assertNotIn(
            (
                "org.example.inheritance:plain-child",
                "org.example.inheritance:inheritance-lib",
            ),
            _edge_set(result),
        )
        override = next(
            item
            for item in result.report.dependency_declarations
            if item.consumer_gav
            == "org.example.inheritance:override-child:1.0.0"
        )
        self.assertEqual(
            override.resolved_dependency_version_or_null,
            "1.0.0",
        )

    def test_parent_profile_property_used_by_child_structure_is_rejected(
        self,
    ) -> None:
        root = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId><artifactId>root</artifactId><version>1</version>
  <packaging>pom</packaging>
  <modules><module>lib</module><module>app</module></modules>
  <properties><lib.version>1</lib.version></properties>
  <profiles><profile><id>alternate</id><properties>
    <lib.version>2</lib.version>
  </properties></profile></profiles>
</project>"""
        parent = b"""<parent>
    <groupId>example</groupId><artifactId>root</artifactId><version>1</version>
    <relativePath>../pom.xml</relativePath>
  </parent>"""
        library = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>""" + parent + b"""
  <artifactId>lib</artifactId>
</project>"""
        application = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>""" + parent + b"""
  <artifactId>app</artifactId>
  <properties><selected.version>${lib.version}</selected.version></properties>
  <dependencies><dependency>
    <groupId>example</groupId><artifactId>lib</artifactId>
    <version>${selected.version}</version>
  </dependency></dependencies>
</project>"""

        with self.assertRaises(MavenStructureError) as caught:
            evaluate_maven_reactor(
                _inline_input(
                    {
                        "pom.xml": root,
                        "lib/pom.xml": library,
                        "app/pom.xml": application,
                    },
                    canonical_system_key="parent-profile-property",
                )
            )
        self.assertEqual(
            caught.exception.code,
            MavenStructureErrorCode.RELEVANT_PROFILE_UNSUPPORTED,
        )

    def test_profile_property_in_unrelated_reactor_branch_is_ignored(
        self,
    ) -> None:
        root = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId><artifactId>root</artifactId><version>1</version>
  <packaging>pom</packaging>
  <modules><module>lib</module><module>profile-holder</module><module>app</module></modules>
</project>"""
        library = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId><artifactId>lib</artifactId><version>1</version>
</project>"""
        profile_holder = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId><artifactId>profile-holder</artifactId><version>1</version>
  <profiles><profile><id>alternate</id><properties>
    <lib.version>2</lib.version>
  </properties></profile></profiles>
</project>"""
        application = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId><artifactId>app</artifactId><version>1</version>
  <properties><lib.version>1</lib.version></properties>
  <dependencies><dependency>
    <groupId>example</groupId><artifactId>lib</artifactId>
    <version>${lib.version}</version>
  </dependency></dependencies>
</project>"""

        result = evaluate_maven_reactor(
            _inline_input(
                {
                    "pom.xml": root,
                    "lib/pom.xml": library,
                    "profile-holder/pom.xml": profile_holder,
                    "app/pom.xml": application,
                },
                canonical_system_key="unrelated-profile-branch",
            )
        )
        self.assertEqual(
            _edge_set(result),
            {("example:app", "example:lib")},
        )

    def test_every_frozen_invalid_fixture_is_rejected_with_exact_code(self) -> None:
        cases = {
            "invalid-missing-module": MavenStructureErrorCode.MODULE_TARGET_MISSING,
            "invalid-duplicate-ga": MavenStructureErrorCode.REACTOR_GA_AMBIGUOUS,
            "invalid-same-ga-different-version": MavenStructureErrorCode.REACTOR_GA_AMBIGUOUS,
            "invalid-relevant-profile": MavenStructureErrorCode.RELEVANT_PROFILE_UNSUPPORTED,
            "invalid-unresolved-property": MavenStructureErrorCode.REQUIRED_PROPERTY_UNRESOLVED,
            "invalid-env-property": MavenStructureErrorCode.DISALLOWED_PROPERTY_SOURCE,
            "invalid-version-range": MavenStructureErrorCode.VERSION_RANGE_UNSUPPORTED,
            "invalid-external-parent-required": MavenStructureErrorCode.EXTERNAL_PARENT_REQUIRED,
            "invalid-duplicate-dependency": MavenStructureErrorCode.DUPLICATE_LOCAL_DEPENDENCY_GA,
            "invalid-property-cycle": MavenStructureErrorCode.PROPERTY_CYCLE,
            "invalid-reactor-classifier": MavenStructureErrorCode.REACTOR_DEPENDENCY_SHAPE_UNSUPPORTED,
            "invalid-module-path-escape": MavenStructureErrorCode.MODULE_PATH_ESCAPES_ROOT,
            "invalid-duplicate-canonical-module": MavenStructureErrorCode.MODULE_CANONICAL_TARGET_DUPLICATE,
            "invalid-git-symlink": MavenStructureErrorCode.MODULE_PATH_SYMLINK_UNSUPPORTED,
            "invalid-parent-relative-path-gav-mismatch": MavenStructureErrorCode.LOCAL_PARENT_GAV_MISMATCH,
            "invalid-duplicate-property": MavenStructureErrorCode.DUPLICATE_POM_PROPERTY,
        }

        for name, expected in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(MavenStructureError) as caught:
                    evaluate_maven_reactor(_fixture_input(name))
                self.assertEqual(caught.exception.code, expected)

    def test_roots_stay_stable_while_revision_bound_states_change(self) -> None:
        revision_a = evaluate_maven_reactor(
            _fixture_input("valid", source_revision="revision-a")
        )
        revision_b = evaluate_maven_reactor(
            _fixture_input("valid", source_revision="revision-b")
        )

        a_entities = {_record_ga(item): item for item in revision_a.entities}
        b_entities = {_record_ga(item): item for item in revision_b.entities}
        self.assertEqual(set(a_entities), set(b_entities))
        for ga in a_entities:
            self.assertEqual(a_entities[ga].root_id, b_entities[ga].root_id)
            self.assertNotEqual(a_entities[ga].state_id, b_entities[ga].state_id)

        a_relations = {
            (
                item.root.predicate.value,
                item.root.subject.entity_root_id,
                item.root.object.entity_root_id,
            ): item
            for item in revision_a.relations
        }
        b_relations = {
            (
                item.root.predicate.value,
                item.root.subject.entity_root_id,
                item.root.object.entity_root_id,
            ): item
            for item in revision_b.relations
        }
        self.assertEqual(set(a_relations), set(b_relations))
        for key in a_relations:
            self.assertEqual(a_relations[key].root_id, b_relations[key].root_id)
            self.assertNotEqual(a_relations[key].state_id, b_relations[key].state_id)
        self.assertEqual(revision_a.coverage.root_id, revision_b.coverage.root_id)
        self.assertNotEqual(revision_a.coverage.state_id, revision_b.coverage.state_id)

    def test_result_is_independent_of_input_mapping_order(self) -> None:
        forward = evaluate_maven_reactor(_fixture_input("valid"))
        reverse = evaluate_maven_reactor(_fixture_input("valid", reverse=True))

        self.assertEqual(
            tuple(item.root_id for item in forward.entities),
            tuple(item.root_id for item in reverse.entities),
        )
        self.assertEqual(
            tuple(item.state_id for item in forward.relations),
            tuple(item.state_id for item in reverse.relations),
        )
        self.assertEqual(forward.coverage, reverse.coverage)
        self.assertEqual(forward.report, reverse.report)

    def test_evaluator_performs_no_implicit_io_or_environment_lookup(self) -> None:
        evaluation_input = _fixture_input("valid")

        with (
            patch("builtins.open", side_effect=AssertionError("filesystem read")),
            patch("os.getenv", side_effect=AssertionError("environment read")),
            patch("subprocess.run", side_effect=AssertionError("process invocation")),
            patch("socket.socket", side_effect=AssertionError("network access")),
        ):
            result = evaluate_maven_reactor(evaluation_input)
        self.assertTrue(result.report.complete)

    def test_external_dependency_does_not_require_version_resolution(self) -> None:
        root = b"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId><artifactId>root</artifactId><version>1</version>
  <dependencies><dependency>
    <groupId>outside</groupId><artifactId>library</artifactId>
    <version>${env.MUST_NOT_BE_READ}</version>
  </dependency></dependencies>
</project>"""
        path = "pom.xml"
        tree_excerpt = (
            '{"is_symlink":false,"mode":"100644","object_id":'
            '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","path":"pom.xml",'
            '"type":"blob"}'
        )
        evaluation_input = MavenEvaluationInput(
            owning_scope_id=SCOPE_ID,
            canonical_system_key="external-version-is-not-required",
            source_binding_id=SOURCE_BINDING_ID,
            source_revision="revision-a",
            knowledge_context_digest=digest_of({"revision": "a"}),
            pom_bytes={path: root},
            git_entries={
                path: GitEntryMetadata("100644", object_id="a" * 40)
            },
            pom_evidence={
                path: PomEvidenceMetadata(
                    artifact_id=_stable("artifact", path),
                    source_context_id=_stable("context", "revision-a"),
                    artifact_content_digest=_content_digest(root),
                    locator=path,
                )
            },
            tree_evidence=(
                StructureEvidence.create(
                    artifact_id=_stable("artifact", "tree:external"),
                    source_context_id=_stable("context", "revision-a"),
                    byte_start=0,
                    byte_end=len(tree_excerpt.encode("utf-8")),
                    locator="git-tree:revision-a:all",
                    excerpt=tree_excerpt,
                    artifact_content_digest=_content_digest(tree_excerpt.encode("utf-8")),
                ),
            ),
        )

        result = evaluate_maven_reactor(evaluation_input)
        self.assertEqual(len(result.modules), 0)
        self.assertEqual(len(result.relations), 0)
        self.assertEqual(
            [item.reason_code for item in result.exclusions],
            ["GA_NOT_IN_REACTOR_CHILD_SET"],
        )

    def test_unsupported_type_on_reactor_target_is_rejected(self) -> None:
        evaluation_input = _fixture_input("valid")
        path = "services/billing-source/pom.xml"
        modified = evaluation_input.pom_bytes[path].replace(
            b"<artifactId>common-lib</artifactId>",
            b"<artifactId>common-lib</artifactId><type>war</type>",
            1,
        )
        pom_bytes = dict(evaluation_input.pom_bytes)
        pom_bytes[path] = modified
        evidence = dict(evaluation_input.pom_evidence)
        old = evidence[path]
        evidence[path] = PomEvidenceMetadata(
            artifact_id=old.artifact_id,
            source_context_id=old.source_context_id,
            artifact_content_digest=_content_digest(modified),
            locator=old.locator,
        )
        modified_input = MavenEvaluationInput(
            owning_scope_id=evaluation_input.owning_scope_id,
            canonical_system_key=evaluation_input.canonical_system_key,
            source_binding_id=evaluation_input.source_binding_id,
            source_revision=evaluation_input.source_revision,
            knowledge_context_digest=evaluation_input.knowledge_context_digest,
            pom_bytes=pom_bytes,
            git_entries=evaluation_input.git_entries,
            pom_evidence=evidence,
            tree_evidence=evaluation_input.tree_evidence,
        )

        with self.assertRaises(MavenStructureError) as caught:
            evaluate_maven_reactor(modified_input)
        self.assertEqual(
            caught.exception.code,
            MavenStructureErrorCode.REACTOR_DEPENDENCY_SHAPE_UNSUPPORTED,
        )

    def test_pom_bytes_must_match_source_artifact_digest(self) -> None:
        evaluation_input = _fixture_input("valid")
        evidence = dict(evaluation_input.pom_evidence)
        original = evidence["pom.xml"]
        evidence["pom.xml"] = PomEvidenceMetadata(
            artifact_id=original.artifact_id,
            source_context_id=original.source_context_id,
            artifact_content_digest=Digest("sha256:" + "0" * 64),
            locator=original.locator,
        )
        mismatched = MavenEvaluationInput(
            owning_scope_id=evaluation_input.owning_scope_id,
            canonical_system_key=evaluation_input.canonical_system_key,
            source_binding_id=evaluation_input.source_binding_id,
            source_revision=evaluation_input.source_revision,
            knowledge_context_digest=evaluation_input.knowledge_context_digest,
            pom_bytes=evaluation_input.pom_bytes,
            git_entries=evaluation_input.git_entries,
            pom_evidence=evidence,
            tree_evidence=evaluation_input.tree_evidence,
        )

        with self.assertRaises(MavenStructureError) as caught:
            evaluate_maven_reactor(mismatched)
        self.assertEqual(
            caught.exception.code,
            MavenStructureErrorCode.POM_CONTENT_DIGEST_MISMATCH,
        )

    def test_tree_evidence_must_exactly_match_supplied_git_metadata(self) -> None:
        evaluation_input = _fixture_input("valid")
        lines = evaluation_input.tree_evidence[0].excerpt.splitlines()
        first = json.loads(lines[0])
        variants: dict[str, str] = {}

        changed_mode = dict(first)
        changed_mode["mode"] = "100755"
        lines_with_mode = list(lines)
        lines_with_mode[0] = json.dumps(
            changed_mode, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        variants["mode"] = "\n".join(lines_with_mode)

        changed_object = dict(first)
        changed_object["object_id"] = "0" * 40
        lines_with_object = list(lines)
        lines_with_object[0] = json.dumps(
            changed_object, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        variants["object_id"] = "\n".join(lines_with_object)

        unrelated = {
            "is_symlink": False,
            "mode": "100644",
            "object_id": "e" * 40,
            "path": "unrelated.txt",
            "type": "blob",
        }
        variants["unrelated"] = "\n".join(
            (
                *lines,
                json.dumps(
                    unrelated,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )
        )

        for label, excerpt in variants.items():
            with self.subTest(label=label):
                with self.assertRaises(MavenStructureError) as caught:
                    evaluate_maven_reactor(
                        _with_tree_excerpt(evaluation_input, excerpt)
                    )
                self.assertEqual(
                    caught.exception.code,
                    MavenStructureErrorCode.TREE_ENTRY_METADATA_MISMATCH,
                )

        original = evaluation_input.tree_evidence[0]
        digest_mismatch = StructureEvidence.create(
            artifact_id=original.artifact_id,
            source_context_id=original.source_context_id,
            byte_start=original.byte_start,
            byte_end=original.byte_end,
            locator=original.locator,
            excerpt=original.excerpt,
            artifact_content_digest=Digest("sha256:" + "0" * 64),
        )
        with self.assertRaises(MavenStructureError) as caught:
            evaluate_maven_reactor(
                replace(evaluation_input, tree_evidence=(digest_mismatch,))
            )
        self.assertEqual(
            caught.exception.code,
            MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
        )
