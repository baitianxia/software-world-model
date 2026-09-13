from __future__ import annotations

import os
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path

from software_world_model.application_services.java_capability_cognition import (
    ExactJavaCognitionSource,
    JavaCognitionModuleSource,
    build_java_capability_cognition,
)
from software_world_model.cross_cutting import DomainError
from software_world_model.infrastructure.file_capability_cognition import (
    load_capability_cognition,
    write_new_capability_cognition,
)
from software_world_model.knowledge_engine.capability_cognition import (
    CapabilityCognitionIndex,
    CapabilityCognitionSnapshot,
    CognitionBehaviorKind,
    CognitionDirection,
    CognitionEntityKind,
    CognitionRelationKind,
)


REVISION = "a" * 40
TREE = "b" * 40


def _source() -> ExactJavaCognitionSource:
    app_controller = b"""package com.example.app;

import com.example.api.PaymentService;

public class CheckoutController {
    private PaymentService paymentService;
    private boolean enabled;

    public String checkout(String orderId) {
        if (!enabled) {
            throw new IllegalStateException();
        }
        this.enabled = false;
        String result = paymentService.pay(orderId);
        return result;
    }
}
"""
    api_service = b"""package com.example.api;

import org.springframework.transaction.annotation.Transactional;

public interface PaymentService {
    @Transactional
    String pay(java.lang.String orderId);
}
"""
    abstract_service = b"""package com.example.app;

public abstract class AbstractPaymentService {
    @Deprecated
    public abstract String refund(String paymentId);
}
"""
    audit_entry = b"""package com.example.app;

public class AuditEntry {
    public String inspect() {
        return "Payment Service Impl Pay";
    }
}
"""
    payment_request = b"""package com.example.api;

public class PaymentRequest {}
"""
    app_service = b"""package com.example.app;

import com.example.api.*;
import com.vendor.PaymentGateway;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class PaymentServiceImpl extends AbstractPaymentService implements PaymentService {
    private PaymentGateway gateway;

    @Override
    public String pay(String orderId) {
        return gateway.charge(orderId);
    }

    @Override
    public String refund(String paymentId) {
        return gateway.refund(paymentId);
    }

    @Override
    public void authorize(PaymentRequest request) {}

    @Override
    public void settle(List<String> paymentIds) {}
}
"""
    api_service = api_service.replace(
        b"}\n",
        b"    void authorize(PaymentRequest request);\n"
        b"    void settle(java.util.List<String> paymentIds);\n"
        b"}\n",
    )
    modules = (
        JavaCognitionModuleSource(
            module_root="api",
            module_name="api",
            descriptor_path="api/pom.xml",
            descriptor_bytes=b"<project><artifactId>api</artifactId></project>\n",
        ),
        JavaCognitionModuleSource(
            module_root="app",
            module_name="app",
            descriptor_path="app/pom.xml",
            descriptor_bytes=b"<project><artifactId>app</artifactId></project>\n",
        ),
    )
    return ExactJavaCognitionSource(
        project_name="fixture",
        source_revision=REVISION,
        source_tree=TREE,
        selected_roots=("api/src/main/java", "app/src/main/java"),
        modules=modules,
        source_files={
            "app/src/main/java/com/example/app/AbstractPaymentService.java": abstract_service,
            "app/src/main/java/com/example/app/AuditEntry.java": audit_entry,
            "app/src/main/java/com/example/app/CheckoutController.java": app_controller,
            "app/src/main/java/com/example/app/PaymentServiceImpl.java": app_service,
            "api/src/main/java/com/example/api/PaymentRequest.java": payment_request,
            "api/src/main/java/com/example/api/PaymentService.java": api_service,
        },
    )


class CapabilityCognitionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = build_java_capability_cognition(_source())
        self.index = CapabilityCognitionIndex(self.snapshot)

    def _entity(self, qualified_name: str):
        return next(
            item
            for item in self.snapshot.entities
            if item.qualified_name == qualified_name
        )

    def _entity_by_id(self, entity_id):
        return next(
            item for item in self.snapshot.entities if item.entity_id == entity_id
        )

    def test_builds_hierarchy_relations_behavior_and_exact_provenance(self) -> None:
        self.assertEqual(self.snapshot.parsed_file_count, 6)
        self.assertEqual(self.snapshot.partial_file_count, 0)
        self.assertEqual(
            {item.kind for item in self.snapshot.entities},
            {
                CognitionEntityKind.MODULE,
                CognitionEntityKind.PACKAGE,
                CognitionEntityKind.FILE,
                CognitionEntityKind.TYPE,
                CognitionEntityKind.METHOD,
            },
        )
        self.assertTrue(
            {
                CognitionRelationKind.CONTAINS,
                CognitionRelationKind.IMPORTS,
                CognitionRelationKind.INHERITS,
                CognitionRelationKind.IMPLEMENTS,
                CognitionRelationKind.INVOKES,
            }.issubset({item.kind for item in self.snapshot.relations})
        )
        checkout = self._entity(
            "com.example.app.CheckoutController#checkout(String)"
        )
        behaviors = [
            item for item in self.snapshot.behaviors if item.method_id == checkout.entity_id
        ]
        self.assertEqual(
            [item.ordinal for item in behaviors],
            list(range(len(behaviors))),
        )
        self.assertTrue(
            {
                CognitionBehaviorKind.CONDITION,
                CognitionBehaviorKind.THROWS,
                CognitionBehaviorKind.STATE_WRITE,
                CognitionBehaviorKind.CALL,
                CognitionBehaviorKind.RETURN,
            }.issubset({item.kind for item in behaviors})
        )
        self.assertTrue(
            all(item.provenance.source_revision == REVISION for item in behaviors)
        )
        self.assertTrue(all(item.provenance.locator for item in behaviors))

    def test_search_traverse_and_detail_are_bounded_and_reusable(self) -> None:
        search = self.index.search("PaymentServiceImpl")
        self.assertGreaterEqual(search.total, 1)
        implementation = search.items[0]
        self.assertEqual(implementation["kind"], "TYPE")

        checkout = self._entity(
            "com.example.app.CheckoutController#checkout(String)"
        )
        traversal = self.index.traverse(
            checkout.entity_id,
            kinds=(CognitionRelationKind.INVOKES,),
            direction=CognitionDirection.OUTGOING,
            maximum_depth=1,
        )
        self.assertTrue(
            any(
                "com.example.api.PaymentService#pay(java.lang.String)"
                == item["relation"]["object_symbol"]
                for item in traversal.items
            )
        )

        implementation_entity = self._entity("com.example.app.PaymentServiceImpl")
        inheritance = self.index.traverse(
            implementation_entity.entity_id,
            kinds=(CognitionRelationKind.IMPLEMENTS,),
            maximum_depth=1,
        )
        self.assertTrue(
            any(
                item["relation"]["object_symbol"] == "PaymentService"
                and item["relation"]["resolution"] == "INTERNAL"
                for item in inheritance.items
            )
        )

        detail = self.index.detail(checkout.entity_id, limit=3)
        self.assertEqual(len(detail.items), 3)
        self.assertIsNotNone(detail.next_cursor)
        continuation = self.index.detail(
            checkout.entity_id,
            cursor=detail.next_cursor,
            limit=32,
        )
        self.assertGreater(len(continuation.items), 0)
        self.assertEqual(detail.snapshot_digest, continuation.snapshot_digest)
        self.assertEqual(
            search.snapshot_epistemics.coverage.value,
            "PARTIAL",
        )
        self.assertTrue(search.snapshot_epistemics.unknowns)

    def test_search_ranks_rare_declaration_contracts_above_common_context(self) -> None:
        page = self.index.search(
            "PaymentServiceImpl pay transaction rollback service implementation"
        )
        leading = [item["qualified_name"] for item in page.items[:6]]
        self.assertIn("com.example.app.PaymentServiceImpl#pay(String)", leading)
        self.assertIn(
            "com.example.api.PaymentService#pay(java.lang.String)",
            leading,
        )
        interface_method = next(
            item
            for item in page.items
            if item["qualified_name"]
            == "com.example.api.PaymentService#pay(java.lang.String)"
        )
        self.assertEqual(
            interface_method["provenance"]["path"],
            "api/src/main/java/com/example/api/PaymentService.java",
        )

    def test_search_preserves_source_identifier_anchor_over_split_token_noise(self) -> None:
        page = self.index.search("PaymentServiceImpl pay")

        self.assertEqual(
            {item["qualified_name"] for item in page.items[:2]},
            {
                "com.example.app.PaymentServiceImpl#pay(String)",
                "com.example.api.PaymentService#pay(java.lang.String)",
            },
        )
        self.assertNotEqual(
            page.items[0]["qualified_name"],
            "com.example.app.AuditEntry#inspect()",
        )

    def test_broad_type_page_keeps_matching_method_visible(self) -> None:
        source = _source()
        files = dict(source.source_files)
        for number in range(14):
            files[f"app/src/main/java/com/example/app/UploadRecord{number}.java"] = (
                f"package com.example.app; public class UploadRecord{number} {{}}"
            ).encode()
        files["app/src/main/java/com/example/app/UploadController.java"] = (
            b"package com.example.app; public class UploadController { "
            b"public void upload() {} }"
        )
        snapshot = build_java_capability_cognition(replace(source, source_files=files))
        page = CapabilityCognitionIndex(snapshot).search("upload", limit=12)
        self.assertEqual(page.items[0]["kind"], "TYPE")
        self.assertTrue(any(item["kind"] == "METHOD" for item in page.items))

    def test_method_contracts_are_explicit_bidirectional_and_exact_source_bound(self) -> None:
        implementation = self._entity(
            "com.example.app.PaymentServiceImpl#pay(String)"
        )
        declaration = self._entity(
            "com.example.api.PaymentService#pay(java.lang.String)"
        )
        relation = next(
            item
            for item in self.snapshot.relations
            if item.kind is CognitionRelationKind.IMPLEMENTS
            and item.subject_id == implementation.entity_id
            and item.object_id == declaration.entity_id
        )
        attributes = dict(relation.attributes)
        self.assertEqual(attributes["contract_kind"], "INTERFACE_DECLARATION")
        self.assertEqual(attributes["method_match"], "ERASED_PARAMETER_TYPES")
        self.assertEqual(relation.epistemics.coverage.value, "COMPLETE")
        self.assertEqual(
            relation.provenance.evidence_kind,
            "JAVA_TYPE_IMPLEMENTS_CLAUSE",
        )

        outgoing = self.index.traverse(
            implementation.entity_id,
            kinds=(CognitionRelationKind.IMPLEMENTS,),
            maximum_depth=1,
        )
        self.assertEqual(
            outgoing.items[0]["to"]["qualified_name"],
            declaration.qualified_name,
        )
        incoming = self.index.traverse(
            declaration.entity_id,
            kinds=(CognitionRelationKind.IMPLEMENTS,),
            direction=CognitionDirection.INCOMING,
            maximum_depth=1,
        )
        self.assertEqual(
            incoming.items[0]["to"]["qualified_name"],
            implementation.qualified_name,
        )

        wildcard_pairs = {
            (
                "com.example.app.PaymentServiceImpl#authorize(PaymentRequest)",
                "com.example.api.PaymentService#authorize(PaymentRequest)",
            ),
            (
                "com.example.app.PaymentServiceImpl#settle(List<String>)",
                "com.example.api.PaymentService#settle(java.util.List<String>)",
            ),
        }
        contract_pairs = {
            (
                self._entity_by_id(item.subject_id).qualified_name,
                self._entity_by_id(item.object_id).qualified_name,
            )
            for item in self.snapshot.relations
            if item.kind is CognitionRelationKind.IMPLEMENTS
            and item.object_id is not None
            and dict(item.attributes).get("relation_scope") == "METHOD_CONTRACT"
        }
        self.assertTrue(wildcard_pairs.issubset(contract_pairs))
        wildcard_relations = {
            self._entity_by_id(item.subject_id).name: item
            for item in self.snapshot.relations
            if item.kind is CognitionRelationKind.IMPLEMENTS
            and item.object_id is not None
            and self._entity_by_id(item.subject_id).qualified_name
            in {subject for subject, _ in wildcard_pairs}
        }
        self.assertEqual(
            wildcard_relations["authorize"].epistemics.coverage.value,
            "COMPLETE",
        )
        self.assertEqual(
            wildcard_relations["settle"].epistemics.coverage.value,
            "PARTIAL",
        )
        self.assertTrue(wildcard_relations["settle"].epistemics.unknowns)

    def test_method_contracts_respect_java_inheritance_visibility(self) -> None:
        source = ExactJavaCognitionSource(
            project_name="visibility-fixture",
            source_revision=REVISION,
            source_tree=TREE,
            selected_roots=("app/src/main/java",),
            modules=(
                JavaCognitionModuleSource(
                    module_root="app",
                    module_name="app",
                    descriptor_path="app/pom.xml",
                    descriptor_bytes=(
                        b"<project><artifactId>app</artifactId></project>\n"
                    ),
                ),
            ),
            source_files={
                "app/src/main/java/base/BaseService.java": b"""package base;

public class BaseService {
    void packageOnly(String value) {}
    protected void protectedOperation(String value) {}
    public void publicOperation(String value) {}
}
""",
                "app/src/main/java/base/SamePackageService.java": b"""package base;

public class SamePackageService extends BaseService {
    @Override void packageOnly(String value) {}
}
""",
                "app/src/main/java/api/PublicContract.java": b"""package api;

public interface PublicContract {
    void interfaceOperation(String value);
}
""",
                "app/src/main/java/child/CrossPackageService.java": b"""package child;

import base.BaseService;

public class CrossPackageService extends BaseService {
    public void packageOnly(String value) {}
    @Override protected void protectedOperation(String value) {}
    @Override public void publicOperation(String value) {}
}
""",
                "app/src/main/java/child/PublicContractImpl.java": b"""package child;

import api.PublicContract;

public class PublicContractImpl implements PublicContract {
    @Override public void interfaceOperation(String value) {}
}
""",
            },
        )
        snapshot = build_java_capability_cognition(source)
        entities = {item.entity_id: item for item in snapshot.entities}
        contract_pairs = {
            (
                entities[item.subject_id].qualified_name,
                entities[item.object_id].qualified_name,
            )
            for item in snapshot.relations
            if item.kind is CognitionRelationKind.IMPLEMENTS
            and item.object_id is not None
            and dict(item.attributes).get("relation_scope") == "METHOD_CONTRACT"
        }

        self.assertNotIn(
            (
                "child.CrossPackageService#packageOnly(String)",
                "base.BaseService#packageOnly(String)",
            ),
            contract_pairs,
        )
        self.assertTrue(
            {
                (
                    "base.SamePackageService#packageOnly(String)",
                    "base.BaseService#packageOnly(String)",
                ),
                (
                    "child.CrossPackageService#protectedOperation(String)",
                    "base.BaseService#protectedOperation(String)",
                ),
                (
                    "child.CrossPackageService#publicOperation(String)",
                    "base.BaseService#publicOperation(String)",
                ),
                (
                    "child.PublicContractImpl#interfaceOperation(String)",
                    "api.PublicContract#interfaceOperation(String)",
                ),
            }.issubset(contract_pairs)
        )

    def test_generic_contract_gap_is_a_page_level_unknown(self) -> None:
        source = ExactJavaCognitionSource(
            project_name="generic-contract-fixture",
            source_revision=REVISION,
            source_tree=TREE,
            selected_roots=("app/src/main/java",),
            modules=(
                JavaCognitionModuleSource(
                    module_root="app",
                    module_name="app",
                    descriptor_path="app/pom.xml",
                    descriptor_bytes=(
                        b"<project><artifactId>app</artifactId></project>\n"
                    ),
                ),
            ),
            source_files={
                "app/src/main/java/generic/api/GenericContract.java": b"""package generic.api;

public interface GenericContract<T> {
    void accept(T value);
}
""",
                "app/src/main/java/generic/impl/StringContract.java": b"""package generic.impl;

import generic.api.GenericContract;

public class StringContract implements GenericContract<String> {
    @Override public void accept(String value) {}
}
""",
            },
        )
        snapshot = build_java_capability_cognition(source)
        entities = {item.entity_id: item for item in snapshot.entities}
        contract_pairs = {
            (
                entities[item.subject_id].qualified_name,
                entities[item.object_id].qualified_name,
            )
            for item in snapshot.relations
            if item.kind is CognitionRelationKind.IMPLEMENTS
            and item.object_id is not None
            and dict(item.attributes).get("relation_scope") == "METHOD_CONTRACT"
        }
        self.assertNotIn(
            (
                "generic.impl.StringContract#accept(String)",
                "generic.api.GenericContract#accept(T)",
            ),
            contract_pairs,
        )

        page = CapabilityCognitionIndex(snapshot).search("StringContract accept")
        generic_unknown = (
            "method contract closure is partial when generic type-variable "
            "substitution or unresolved signature namespaces are required"
        )
        self.assertIn(generic_unknown, snapshot.unknowns)
        self.assertEqual(page.snapshot_epistemics.coverage.value, "PARTIAL")
        self.assertIn(generic_unknown, page.snapshot_epistemics.unknowns)

    def test_parent_declaration_and_annotations_are_visible_in_bounded_queries(self) -> None:
        implementation_type = self._entity("com.example.app.PaymentServiceImpl")
        type_item = next(
            item
            for item in self.index.search(
                "PaymentServiceImpl",
                kinds=(CognitionEntityKind.TYPE,),
            ).items
            if item["entity_id"] == implementation_type.entity_id.value
        )
        self.assertIn("@Service", dict(type_item["attributes"])["annotations"])

        interface_method = self._entity(
            "com.example.api.PaymentService#pay(java.lang.String)"
        )
        method_item = next(
            item
            for item in self.index.search(
                "PaymentService pay Transactional",
                kinds=(CognitionEntityKind.METHOD,),
            ).items
            if item["entity_id"] == interface_method.entity_id.value
        )
        self.assertIn(
            "@Transactional",
            dict(method_item["attributes"])["annotations"],
        )

        refund = self._entity(
            "com.example.app.PaymentServiceImpl#refund(String)"
        )
        parent_refund = self._entity(
            "com.example.app.AbstractPaymentService#refund(String)"
        )
        relation = next(
            item
            for item in self.snapshot.relations
            if item.kind is CognitionRelationKind.IMPLEMENTS
            and item.subject_id == refund.entity_id
            and item.object_id == parent_refund.entity_id
        )
        self.assertEqual(
            dict(relation.attributes)["contract_kind"],
            "PARENT_TYPE_DECLARATION",
        )

    def test_inheritance_and_contract_details_expose_semantics_and_both_sources(self) -> None:
        implementation_type = self._entity("com.example.app.PaymentServiceImpl")
        inheritance = self.index.traverse(
            implementation_type.entity_id,
            maximum_depth=1,
        )
        kinds_by_target = {
            item["to"]["qualified_name"]: (
                item["relation"]["kind"],
                dict(item["relation"]["attributes"])["inheritance_kind"],
            )
            for item in inheritance.items
            if "inheritance_kind" in item["relation"]["attributes"]
        }
        self.assertEqual(
            kinds_by_target["com.example.app.AbstractPaymentService"],
            ("INHERITS", "EXTENDS"),
        )
        self.assertEqual(
            kinds_by_target["com.example.api.PaymentService"],
            ("IMPLEMENTS", "IMPLEMENTS"),
        )

        declaration = self._entity(
            "com.example.api.PaymentService#pay(java.lang.String)"
        )
        relation_detail = next(
            item
            for item in self.index.detail(declaration.entity_id, limit=64).items
            if item["detail_kind"] == "RELATION"
            and item["relation"]["kind"] == "IMPLEMENTS"
        )
        self.assertEqual(
            relation_detail["from"]["provenance"]["path"],
            "app/src/main/java/com/example/app/PaymentServiceImpl.java",
        )
        self.assertEqual(
            relation_detail["to"]["provenance"]["path"],
            "api/src/main/java/com/example/api/PaymentService.java",
        )

    def test_external_target_is_unknown_bounded_not_fabricated_entity(self) -> None:
        pay = self._entity("com.example.app.PaymentServiceImpl#pay(String)")
        traversal = self.index.traverse(
            pay.entity_id,
            kinds=(CognitionRelationKind.INVOKES,),
            maximum_depth=1,
        )
        gateway = next(
            item
            for item in traversal.items
            if "PaymentGateway#charge/1" in item["relation"]["object_symbol"]
        )
        self.assertEqual(gateway["relation"]["resolution"], "EXTERNAL")
        self.assertIsNone(gateway["relation"]["object_id"])
        self.assertTrue(gateway["relation"]["unknowns"])

    def test_snapshot_conflicts_are_visible_on_every_bounded_query_page(self) -> None:
        modules = tuple(
            JavaCognitionModuleSource(
                module_root=name,
                module_name=name,
                descriptor_path=f"{name}/pom.xml",
                descriptor_bytes=(
                    f"<project><artifactId>{name}</artifactId></project>\n"
                ).encode(),
            )
            for name in ("left", "right")
        )
        duplicate = b"""package com.example;
public class Duplicate {}
"""
        snapshot = build_java_capability_cognition(
            ExactJavaCognitionSource(
                project_name="conflicting-fixture",
                source_revision=REVISION,
                source_tree=TREE,
                selected_roots=(
                    "left/src/main/java",
                    "right/src/main/java",
                ),
                modules=modules,
                source_files={
                    "left/src/main/java/com/example/Duplicate.java": duplicate,
                    "right/src/main/java/com/example/Duplicate.java": duplicate,
                },
            )
        )

        page = CapabilityCognitionIndex(snapshot).search("Duplicate")

        self.assertEqual(page.snapshot_epistemics.coverage.value, "PARTIAL")
        self.assertEqual(
            page.snapshot_epistemics.conflicts,
            ("duplicate Java type identity: com.example.Duplicate",),
        )
        self.assertEqual(
            page.to_payload()["snapshot_epistemics"]["conflicts"],
            ["duplicate Java type identity: com.example.Duplicate"],
        )

    def test_artifact_round_trip_recomputes_exact_digest(self) -> None:
        restored = CapabilityCognitionSnapshot.from_payload(
            self.snapshot.to_payload()
        )
        self.assertEqual(restored.digest, self.snapshot.digest)
        self.assertEqual(restored.snapshot_id, self.snapshot.snapshot_id)
        self.assertEqual(restored.entities, self.snapshot.entities)

    def test_file_artifact_is_private_immutable_and_exactly_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "cognition.json").resolve()
            digest = write_new_capability_cognition(target, self.snapshot)
            self.assertEqual(digest, self.snapshot.digest)
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)
            restored = load_capability_cognition(
                target,
                expected_revision=REVISION,
                expected_tree=TREE,
                expected_digest=digest,
            )
            self.assertEqual(restored, self.snapshot)
            with self.assertRaises(DomainError):
                write_new_capability_cognition(target, self.snapshot)


if __name__ == "__main__":
    unittest.main()
