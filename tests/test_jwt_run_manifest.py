from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.ai_infrastructure import (
    ArkChatConformanceQualification,
    VolcengineArkModelConfiguration,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of
from validation.jwt_iteration_001.manifest import (
    DIRECT_AGENT_PROMPT,
    DIRECT_AGENT_PROMPT_REF,
    DIRECT_AGENT_TOOL_POLICY_REF,
    DIRECT_ORACLE_DRAFT_SCHEMA,
    PARENT_COMMIT,
    QUESTION,
    REPOSITORY_IDENTITY,
    TARGET_COMMIT,
    _direct_requirement_view,
    freeze_jwt_run_configuration,
    seal_direct_oracle,
    verify_direct_oracle,
    verify_jwt_run_configuration,
)


class JwtRunManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = VolcengineArkModelConfiguration()
        self.qualification = ArkChatConformanceQualification(
            result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64,
            result_digest=Digest("sha256:" + "a" * 64),
            qualified_model_fingerprints=self.configuration.qualified_model_identities,
            adapter_version=self.configuration.adapter_version,
            provider_configuration_fingerprint=self.configuration.fingerprint,
            valid_until=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        self.repository = (
            Path(__file__).resolve().parents[1] / "validation-projects" / "mall"
        )

    def draft(self):
        prompt = DIRECT_AGENT_PROMPT
        requirement = _direct_requirement_view()
        action = {
            "action": "COMPARE",
            "revision_role": "NONE",
            "path": "",
            "query": "",
            "start_line": 0,
            "end_line": 0,
        }
        content = "M\tpom.xml"
        content_digest = Digest(
            "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
        ).value
        observation_ref = f"direct-observation:000:{content_digest}"
        return {
            "schema": DIRECT_ORACLE_DRAFT_SCHEMA,
            "question": QUESTION,
            "repository_identity": REPOSITORY_IDENTITY,
            "target_commit": TARGET_COMMIT,
            "parent_commit": PARENT_COMMIT,
            "model_ref": self.configuration.model_ref,
            "adapter_version": self.configuration.adapter_version,
            "conformance_result_ref": self.qualification.result_ref,
            "prompt_ref": DIRECT_AGENT_PROMPT_REF,
            "prompt": prompt,
            "prompt_digest": digest_of(prompt).value,
            "tool_policy_ref": DIRECT_AGENT_TOOL_POLICY_REF,
            "requirement": requirement,
            "requirement_digest": digest_of(requirement).value,
            "budget": {
                "max_tool_steps": 40,
                "max_files_read": 16,
                "max_source_bytes": 1_000_000,
                "max_model_calls": 40,
                "timeout_milliseconds": 60_000,
                "max_output_tokens": 4096,
            },
            "started_at": "2026-08-06T00:00:00.000000Z",
            "completed_at": "2026-08-06T00:01:00.000000Z",
            "actual_model_fingerprints": [
                self.configuration.actual_model_fingerprint
            ],
            "provider_request_ids": ["provider-direct-1", "provider-direct-2"],
            "output_normalizations": ["IDENTITY", "IDENTITY"],
            "usage": {"input_tokens": 100, "output_tokens": 50, "complete": True},
            "trace": [
                {
                    "ordinal": 0,
                    "tool": "COMPARE",
                    "request": action,
                    "request_digest": digest_of(action).value,
                    "observation_ref": observation_ref,
                    "result_digest": content_digest,
                }
            ],
            "observations": [
                {
                    "observation_ref": observation_ref,
                    "tool": "COMPARE",
                    "locator": f"git:compare:{PARENT_COMMIT}..{TARGET_COMMIT}",
                    "content": content,
                    "content_digest": content_digest,
                }
            ],
            "direct_answer": "private direct answer that must not enter SWM runtime",
            "claims": [
                {
                    "semantic_key": "claim:changed-file",
                    "claim": "the comparison reports pom.xml as changed",
                    "target": TARGET_COMMIT,
                    "context": "PARENT_TO_TARGET",
                    "modality": "ESTABLISHED",
                    "condition": None,
                    "limitation": None,
                    "coverage": "DIRECT",
                    "source_locators": [
                        f"git:compare:{PARENT_COMMIT}..{TARGET_COMMIT}"
                    ],
                    "source_digests": [content_digest],
                    "need_ids": ["JWT-N01"],
                    "obligation_ids": ["JWT-N01-O01"],
                    "material": True,
                }
            ],
        }

    def test_oracle_and_run_configuration_are_sealed_and_physically_separated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_path = root / "draft.json"
            draft_path.write_text(json.dumps(self.draft()), encoding="utf-8")
            oracle_path = seal_direct_oracle(
                draft_path=draft_path,
                result_directory=root / "oracle",
                qualification=self.qualification,
                configuration=self.configuration,
                operator="direct-agent-operator",
                reviewer="independent-oracle-reviewer",
                now=datetime(2026, 8, 6, tzinfo=timezone.utc),
            )
            oracle = json.loads(oracle_path.read_text())
            verify_direct_oracle(
                oracle,
                qualification=self.qualification,
                configuration=self.configuration,
            )

            run_path = freeze_jwt_run_configuration(
                oracle_path=oracle_path,
                repository_path=self.repository,
                result_directory=root / "run-config",
                qualification=self.qualification,
                configuration=self.configuration,
                operator="swm-run-operator",
                runtime_directory=root / "swm-runtime",
                now=datetime(2026, 8, 6, 1, tzinfo=timezone.utc),
            )
            run = json.loads(run_path.read_text())
            verify_jwt_run_configuration(
                run,
                self.qualification,
                self.configuration,
                at=datetime(2026, 8, 6, 2, tzinfo=timezone.utc),
            )

            self.assertEqual(len(run["roles"]), 7)
            self.assertFalse(run["oracle"]["oracle_content_available_to_runtime"])
            self.assertNotIn(self.draft()["direct_answer"], run_path.read_text())
            self.assertNotIn(str(root / "oracle"), run_path.read_text())
            self.assertEqual(oracle_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(run_path.stat().st_mode & 0o777, 0o600)

    def test_oracle_requires_distinct_human_authorities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            draft_path = Path(directory) / "draft.json"
            draft_path.write_text(json.dumps(self.draft()), encoding="utf-8")
            with self.assertRaises(DomainError) as raised:
                seal_direct_oracle(
                    draft_path=draft_path,
                    result_directory=Path(directory) / "oracle",
                    qualification=self.qualification,
                    configuration=self.configuration,
                    operator="same-person",
                    reviewer="same-person",
                )
            self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_oracle_rejects_stale_direct_requirement_binding(self) -> None:
        draft = self.draft()
        draft["requirement"][0]["question"] = "stale requirement"
        draft["requirement_digest"] = digest_of(draft["requirement"]).value
        with tempfile.TemporaryDirectory() as directory:
            draft_path = Path(directory) / "draft.json"
            draft_path.write_text(json.dumps(draft), encoding="utf-8")
            with self.assertRaises(DomainError) as raised:
                seal_direct_oracle(
                    draft_path=draft_path,
                    result_directory=Path(directory) / "oracle",
                    qualification=self.qualification,
                    configuration=self.configuration,
                    operator="operator",
                    reviewer="reviewer",
                )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_runtime_cannot_be_nested_in_oracle_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_path = root / "draft.json"
            draft_path.write_text(json.dumps(self.draft()), encoding="utf-8")
            oracle_path = seal_direct_oracle(
                draft_path=draft_path,
                result_directory=root / "oracle",
                qualification=self.qualification,
                configuration=self.configuration,
                operator="operator",
                reviewer="reviewer",
            )
            with self.assertRaises(DomainError) as raised:
                freeze_jwt_run_configuration(
                    oracle_path=oracle_path,
                    repository_path=self.repository,
                    result_directory=root / "run-config",
                    qualification=self.qualification,
                    configuration=self.configuration,
                    operator="operator",
                    runtime_directory=root / "oracle" / "runtime",
                )
            self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_tampered_oracle_digest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_path = root / "draft.json"
            draft_path.write_text(json.dumps(self.draft()), encoding="utf-8")
            oracle_path = seal_direct_oracle(
                draft_path=draft_path,
                result_directory=root / "oracle",
                qualification=self.qualification,
                configuration=self.configuration,
                operator="operator",
                reviewer="reviewer",
            )
            oracle = json.loads(oracle_path.read_text())
            oracle["direct_run"]["direct_answer"] = "tampered"
            with self.assertRaises(DomainError) as raised:
                verify_direct_oracle(oracle)
            self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)


if __name__ == "__main__":
    unittest.main()
