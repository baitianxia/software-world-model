from __future__ import annotations

import os
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
    String pay(String orderId);
}
"""
    app_service = b"""package com.example.app;

import com.example.api.PaymentService;
import com.vendor.PaymentGateway;

public class PaymentServiceImpl implements PaymentService {
    private PaymentGateway gateway;

    public String pay(String orderId) {
        return gateway.charge(orderId);
    }
}
"""
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
            "app/src/main/java/com/example/app/CheckoutController.java": app_controller,
            "app/src/main/java/com/example/app/PaymentServiceImpl.java": app_service,
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

    def test_builds_hierarchy_relations_behavior_and_exact_provenance(self) -> None:
        self.assertEqual(self.snapshot.parsed_file_count, 3)
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
                "com.example.api.PaymentService#pay(String)"
                == item["relation"]["object_symbol"]
                for item in traversal.items
            )
        )

        implementation_entity = self._entity("com.example.app.PaymentServiceImpl")
        inheritance = self.index.traverse(
            implementation_entity.entity_id,
            kinds=(CognitionRelationKind.INHERITS,),
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

    def test_search_ranks_rare_declaration_contracts_above_common_context(self) -> None:
        page = self.index.search(
            "PaymentServiceImpl pay transaction rollback service implementation"
        )
        leading = [item["qualified_name"] for item in page.items[:6]]
        self.assertIn("com.example.app.PaymentServiceImpl#pay(String)", leading)
        self.assertIn("com.example.api.PaymentService#pay(String)", leading)
        interface_method = next(
            item
            for item in page.items
            if item["qualified_name"] == "com.example.api.PaymentService#pay(String)"
        )
        self.assertEqual(
            interface_method["provenance"]["path"],
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
