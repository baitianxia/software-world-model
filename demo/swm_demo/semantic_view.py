from __future__ import annotations

from swm_demo.knowledge_engine import KnowledgeEngine


class StructureViewEngine:
    """Read-only organization of formal knowledge into a Structure View."""

    def __init__(self, knowledge_engine: KnowledgeEngine):
        self.knowledge_engine = knowledge_engine

    def render(self, scope_id: str) -> dict[str, object]:
        snapshot = self.knowledge_engine.current_snapshot(scope_id)
        entities = self.knowledge_engine.read_entities(scope_id)
        facts = self.knowledge_engine.read_facts(scope_id)
        entities_by_id = {item["entity_id"]: item for item in entities}

        contains = [item for item in facts if item["predicate"] == "CONTAINS_MODULE"]
        dependencies = [item for item in facts if item["predicate"] == "DEPENDS_ON"]

        root_ids = sorted({str(item["subject_id"]) for item in contains})
        roots = [entities_by_id[root_id] for root_id in root_ids]
        modules = [
            {
                "entity_id": item["object_id"],
                "name": entities_by_id[item["object_id"]]["name"],
                "fact_id": item["fact_id"],
                "evidence_count": item["evidence_count"],
            }
            for item in contains
        ]
        edges = [
            {
                "source_entity_id": item["subject_id"],
                "source": entities_by_id[item["subject_id"]]["name"],
                "target_entity_id": item["object_id"],
                "target": entities_by_id[item["object_id"]]["name"],
                "fact_id": item["fact_id"],
                "evidence_count": item["evidence_count"],
            }
            for item in dependencies
        ]

        return {
            "view": "Structure",
            "scope_id": scope_id,
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "roots": sorted(roots, key=lambda item: str(item["name"])),
            "modules": sorted(modules, key=lambda item: str(item["name"])),
            "dependencies": sorted(
                edges, key=lambda item: (str(item["source"]), str(item["target"]))
            ),
            "knowledge_references": {
                "entity_count": len(entities),
                "fact_count": len(facts),
            },
        }

    def endpoint_chain(self, scope_id: str, endpoint_name: str) -> dict[str, object]:
        """Organize existing Structure Facts around one endpoint."""

        snapshot = self.knowledge_engine.current_snapshot(scope_id)
        entities = self.knowledge_engine.read_entities(scope_id)
        facts = self.knowledge_engine.read_facts(scope_id)
        entities_by_id = {str(item["entity_id"]): item for item in entities}
        endpoints = [
            item
            for item in entities
            if item["entity_type"] == "web-endpoint"
            and str(item["name"]) == endpoint_name
        ]
        if len(endpoints) != 1:
            return {
                "view": "Structure",
                "scope_id": scope_id,
                "snapshot_id": snapshot["snapshot_id"],
                "revision": snapshot["revision"],
                "endpoint": endpoint_name,
                "status": "KNOWLEDGE_GAP",
                "reason": f"expected one endpoint Entity, found {len(endpoints)}",
                "knowledge_references": [],
            }

        endpoint = endpoints[0]
        exposure = [
            item
            for item in facts
            if item["predicate"] == "EXPOSES_ENDPOINT"
            and item["object_id"] == endpoint["entity_id"]
        ]
        controller_method_ids = {str(item["subject_id"]) for item in exposure}
        declarations = [
            item
            for item in facts
            if item["predicate"] == "DECLARES_METHOD"
            and str(item["object_id"]) in controller_method_ids
        ]
        controller_type_ids = {str(item["subject_id"]) for item in declarations}
        containment = [
            item
            for item in facts
            if item["predicate"] == "CONTAINS_TYPE"
            and str(item["object_id"]) in controller_type_ids
        ]
        calls = [
            item
            for item in facts
            if item["predicate"] == "CALLS"
            and str(item["subject_id"]) in controller_method_ids
        ]
        implemented_method_ids = {
            str(item["object_id"])
            for item in facts
            if item["predicate"] == "IMPLEMENTS_METHOD"
        }
        calls = [
            item
            for item in calls
            if str(item["object_id"]) in implemented_method_ids
        ]
        interface_method_ids = {str(item["object_id"]) for item in calls}
        implementations = [
            item
            for item in facts
            if item["predicate"] == "IMPLEMENTS_METHOD"
            and str(item["object_id"]) in interface_method_ids
        ]
        implementation_method_ids = {
            str(item["subject_id"]) for item in implementations
        }
        implementation_declarations = [
            item
            for item in facts
            if item["predicate"] == "DECLARES_METHOD"
            and str(item["object_id"]) in implementation_method_ids
        ]
        referenced = [
            *exposure,
            *declarations,
            *containment,
            *calls,
            *implementations,
            *implementation_declarations,
        ]
        return {
            "view": "Structure",
            "scope_id": scope_id,
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "status": "READY",
            "endpoint": endpoint,
            "module": [
                entities_by_id[str(item["subject_id"])] for item in containment
            ],
            "controller_types": [
                entities_by_id[item] for item in sorted(controller_type_ids)
            ],
            "controller_methods": [
                entities_by_id[item] for item in sorted(controller_method_ids)
            ],
            "service_methods": [
                entities_by_id[item] for item in sorted(interface_method_ids)
            ],
            "implementation_methods": [
                entities_by_id[item]
                for item in sorted(implementation_method_ids)
            ],
            "implementation_types": [
                entities_by_id[str(item["subject_id"])]
                for item in implementation_declarations
            ],
            "knowledge_references": sorted(
                {str(item["fact_id"]) for item in referenced}
            ),
        }


class _InferenceViewEngine:
    view_name = "Inference"
    allowed_types: tuple[str, ...] = ()

    def __init__(self, knowledge_engine: KnowledgeEngine):
        self.knowledge_engine = knowledge_engine

    def render(self, scope_id: str) -> dict[str, object]:
        snapshot = self.knowledge_engine.current_snapshot(scope_id)
        inferences = [
            item
            for item in self.knowledge_engine.read_inferences(scope_id)
            if item["inference_type"] in self.allowed_types
        ]
        return {
            "view": self.view_name,
            "scope_id": scope_id,
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "items": inferences,
            "knowledge_references": [
                str(item["inference_id"]) for item in inferences
            ],
        }


class BehaviorViewEngine(_InferenceViewEngine):
    view_name = "Behavior"
    allowed_types = ("BEHAVIOR_FLOW",)


class BusinessViewEngine(_InferenceViewEngine):
    view_name = "Business"
    allowed_types = ("BUSINESS_CONSTRAINT", "BUSINESS_CAPABILITY")


class HistoryViewEngine(_InferenceViewEngine):
    view_name = "History"
    allowed_types = ("HISTORY_IMPACT",)


class SemanticViewRegistry:
    """Small validation registry proving built-in and future views share one contract."""

    def __init__(self, knowledge_engine: KnowledgeEngine):
        self.views = {
            "structure": StructureViewEngine(knowledge_engine),
            "behavior": BehaviorViewEngine(knowledge_engine),
            "business": BusinessViewEngine(knowledge_engine),
            "history": HistoryViewEngine(knowledge_engine),
        }

    def register(self, view_name: str, view: object) -> None:
        key = view_name.lower()
        if key in self.views:
            raise ValueError(f"Semantic View is already registered: {view_name}")
        if not callable(getattr(view, "render", None)):
            raise ValueError("Semantic View extension must provide render(scope_id)")
        self.views[key] = view

    def render(self, view_name: str, scope_id: str) -> dict[str, object]:
        view = self.views.get(view_name.lower())
        if view is None:
            raise ValueError(f"Semantic View is not registered: {view_name}")
        return view.render(scope_id)
