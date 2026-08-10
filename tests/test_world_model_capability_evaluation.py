from __future__ import annotations

import unittest

from software_world_model.ai_infrastructure import (
    WORLD_MODEL_EVALUATION_METRIC_CONTRACT,
    WorldModelEvaluationCase,
    WorldModelEvaluationRole,
    create_world_model_evaluation_definition,
    world_model_answer_output_contract_digest,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
    world_model_capability_registry,
)
from software_world_model.cross_cutting import Digest, DomainError, digest_of


def evaluation_case(role: WorldModelEvaluationRole) -> WorldModelEvaluationCase:
    return WorldModelEvaluationCase(
        role=role,
        case_id=f"case-{role.value.lower()}",
        case_version="1.0.0",
        fixture_ref=f"fixture:{role.value}",
        fixture_digest=digest_of({"fixture": role.value}),
        oracle_ref=f"oracle:{role.value}",
        oracle_digest=digest_of({"oracle": role.value}),
    )


class WorldModelCapabilityEvaluationTests(unittest.TestCase):
    def create(self, cases=None):
        return create_world_model_evaluation_definition(
            evaluation_version="1.0.0",
            conformance_result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "1" * 64,
            provider_configuration_fingerprint=Digest("sha256:" + "2" * 64),
            model_ref="glm-5.2",
            adapter_version="openai-chat-completions-no-tools@8",
            exact_g3a_checkpoint_ref="git:" + "3" * 40,
            environment_ref="isolated-v009@1",
            reference_strategy_ref="standalone-evaluator@1",
            resource_policy_ref="one-call-no-retry@1",
            cases=(
                tuple(evaluation_case(role) for role in WorldModelEvaluationRole)
                if cases is None
                else cases
            ),
            valid_for_seconds=3600,
        )

    def test_definition_binds_all_seven_roles_and_exact_strategy_contracts(self):
        definition = self.create()

        self.assertEqual(len(definition.cases), 7)
        self.assertEqual(
            definition.implementation_digest,
            world_model_answer_strategy_implementation_digest(),
        )
        self.assertEqual(
            definition.prompt_program_digest,
            world_model_answer_prompt_program_digest(),
        )
        self.assertEqual(
            definition.output_schema_digest,
            world_model_answer_output_contract_digest(),
        )
        self.assertEqual(
            definition.metric_contract_digest,
            digest_of(WORLD_MODEL_EVALUATION_METRIC_CONTRACT),
        )
        registry = world_model_capability_registry()
        strategy = registry.resolve_strategy(
            definition.strategy_id, definition.strategy_version
        )
        self.assertEqual(strategy.implementation_digest, definition.implementation_digest)
        self.assertTrue(strategy.requires_model)

    def test_missing_required_role_cannot_form_definition(self):
        incomplete = tuple(
            evaluation_case(role)
            for role in WorldModelEvaluationRole
            if role is not WorldModelEvaluationRole.ENTITY_CANDIDATE_RESOLUTION
        )

        with self.assertRaises(DomainError):
            self.create(incomplete)


if __name__ == "__main__":
    unittest.main()
