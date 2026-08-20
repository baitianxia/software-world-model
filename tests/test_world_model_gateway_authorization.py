from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.interface.world_model_runtime_assets import (
    gateway_authorized_workload,
)


_DIGEST_A = "sha256:" + "a" * 64
_DIGEST_B = "sha256:" + "b" * 64


class GatewayAuthorizationWorkloadTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def _receipt(self, *, status: str = "AUTHORIZED") -> Path:
        schema = "SWM-WORLD-MODEL-GATEWAY-AUTHORIZATION-RECEIPT@1"
        core = {
            "schema": schema,
            "status": status,
            "evaluation_grant_digest": _DIGEST_A,
            "disclosure_authorization_digest": _DIGEST_B,
            "authorized_by": "user",
            "authorized_at": "2026-08-11T20:00:00+08:00",
            "authorization_ref": "user-message:test",
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
            ),
            "production_activation": "NOT_EXECUTED",
        }
        value = {
            **core,
            "document_digest": digest_of([schema, core]).value,
        }
        path = self.root / f"receipt-{status}.json"
        path.write_bytes(canonical_json_bytes(value))
        return path

    def _arguments(self, receipt: Path, output: Path) -> list[str]:
        return [
            "--evaluation-authorization-receipt",
            str(receipt),
            "--expected-evaluation-grant-digest",
            _DIGEST_A,
            "--expected-disclosure-authorization-digest",
            _DIGEST_B,
            "--summary-output",
            str(output),
            "--g3b-freeze",
            str(self.root / "legacy-freeze.json"),
        ]

    def test_invalid_current_receipt_stops_before_qualified_baseline(self) -> None:
        output = self.root / "summary.json"
        with patch.object(
            gateway_authorized_workload,
            "_load_qualified_baseline",
        ) as baseline:
            with self.assertRaisesRegex(RuntimeError, "receipt is invalid"):
                gateway_authorized_workload.main(
                    self._arguments(
                        self._receipt(status="NOT_AUTHORIZED"),
                        output,
                    )
                )

        baseline.assert_not_called()
        self.assertFalse(output.exists())

    def test_current_receipt_reclassifies_legacy_freeze_as_baseline_only(self) -> None:
        output = self.root / "summary.json"

        def baseline_main(arguments):
            index = arguments.index("--summary-output")
            baseline_output = Path(arguments[index + 1])
            baseline_output.write_bytes(
                canonical_json_bytes(
                    {
                        "schema": "swm.iter-003.g3b-gateway-workload@1",
                        "status": "PASS",
                        "provider_call_count": 1,
                        "https_dispatch_count": 1,
                        "g3b_freeze_ref": "legacy",
                        "g3b_freeze_digest": _DIGEST_A,
                        "permission_digest": _DIGEST_B,
                        "production_activation": "NOT_EXECUTED",
                    }
                )
            )
            return 0

        with patch.object(
            gateway_authorized_workload,
            "_load_qualified_baseline",
            return_value=SimpleNamespace(main=baseline_main),
        ):
            with redirect_stdout(StringIO()):
                code = gateway_authorized_workload.main(
                    self._arguments(self._receipt(), output)
                )

        self.assertEqual(code, 0)
        value = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(value["evaluation_grant_digest"], _DIGEST_A)
        self.assertEqual(value["disclosure_authorization_digest"], _DIGEST_B)
        self.assertEqual(
            value["qualified_gateway_baseline"]["role"],
            "QUALIFIED_CAPABILITY_BASELINE_ONLY",
        )
        self.assertNotIn("permission_digest", value)
        self.assertNotIn("g3b_freeze_ref", value)
        core = {key: item for key, item in value.items() if key != "document_digest"}
        self.assertEqual(
            value["document_digest"],
            digest_of(
                ["SWM-WORLD-MODEL-AUTHORIZED-GATEWAY@1", core]
            ).value,
        )

    def test_java_baseline_digest_does_not_shadow_authorized_summary(self) -> None:
        output = self.root / "summary.json"

        def baseline_main(arguments):
            index = arguments.index("--summary-output")
            baseline_output = Path(arguments[index + 1])
            baseline_core = {
                "schema": "swm.iter-006.java-gateway-workload@1",
                "status": "PASS",
                "provider_call_count": 1,
                "https_dispatch_count": 1,
                "java_gateway_freeze_ref": "java",
                "java_gateway_freeze_digest": _DIGEST_A,
                "permission_digest": _DIGEST_B,
                "production_activation": "NOT_EXECUTED",
            }
            baseline_output.write_bytes(
                canonical_json_bytes(
                    {
                        **baseline_core,
                        "document_digest": digest_of(baseline_core).value,
                    }
                )
            )
            return 0

        with patch.object(
            gateway_authorized_workload,
            "_load_qualified_baseline",
            return_value=SimpleNamespace(main=baseline_main),
        ):
            with redirect_stdout(StringIO()):
                code = gateway_authorized_workload.main(
                    self._arguments(self._receipt(), output)
                )

        self.assertEqual(code, 0)
        value = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(
            value["qualified_gateway_baseline"],
            {
                "entrypoint_sha256": gateway_authorized_workload._JAVA_GATEWAY_SHA256,
                "capability_freeze_digest": _DIGEST_A,
                "role": "QUALIFIED_CAPABILITY_BASELINE_ONLY",
            },
        )
        core = {key: item for key, item in value.items() if key != "document_digest"}
        self.assertEqual(
            value["document_digest"],
            digest_of(
                ["SWM-WORLD-MODEL-AUTHORIZED-GATEWAY@1", core]
            ).value,
        )

    def test_source_semantics_baseline_preserves_exact_three_call_receipt(self) -> None:
        output = self.root / "summary.json"

        def baseline_main(arguments):
            index = arguments.index("--summary-output")
            baseline_output = Path(arguments[index + 1])
            baseline_core = {
                "schema": (
                    "swm.iter-007.java-source-semantics-gateway-workload@1"
                ),
                "status": "PASS",
                "provider_call_count": 3,
                "https_dispatch_count": 3,
                "server_statuses": ["RESULT", "RESULT", "RESULT"],
                "java_source_semantics_gateway_freeze_ref": "semantics",
                "java_source_semantics_gateway_freeze_digest": _DIGEST_A,
                "permission_digest": _DIGEST_B,
                "production_activation": "NOT_EXECUTED",
            }
            baseline_output.write_bytes(
                canonical_json_bytes(
                    {
                        **baseline_core,
                        "document_digest": digest_of(baseline_core).value,
                    }
                )
            )
            return 0

        with patch.object(
            gateway_authorized_workload,
            "_load_qualified_baseline",
            return_value=SimpleNamespace(main=baseline_main),
        ):
            with redirect_stdout(StringIO()):
                code = gateway_authorized_workload.main(
                    self._arguments(self._receipt(), output)
                )

        self.assertEqual(code, 0)
        value = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(value["provider_call_count"], 3)
        self.assertEqual(value["https_dispatch_count"], 3)
        self.assertEqual(
            value["qualified_gateway_baseline"],
            {
                "entrypoint_sha256": (
                    gateway_authorized_workload.
                    _JAVA_SOURCE_SEMANTICS_GATEWAY_SHA256
                ),
                "source_semantics_capability_freeze_digest": _DIGEST_A,
                "role": "QUALIFIED_CAPABILITY_BASELINE_ONLY",
            },
        )

    def test_bounded_baseline_preserves_selected_provider_and_unused_closure(self) -> None:
        output = self.root / "summary.json"

        def baseline_main(arguments):
            index = arguments.index("--summary-output")
            baseline_output = Path(arguments[index + 1])
            baseline_core = {
                "schema": (
                    "swm.iter-008.bounded-java-source-semantics-"
                    "gateway-workload@1"
                ),
                "status": "PASS",
                "provider_selection_policy": (
                    "PRE_DISPATCH_FIRST_CURRENTLY_QUALIFIED_NO_REQUEST_RETRY"
                ),
                "provider_preference_order": ["VOLCENGINE_ARK", "DEEPSEEK"],
                "selected_provider_type": "DEEPSEEK",
                "provider_type": "DEEPSEEK",
                "adapter_version": "deepseek-chat-completions-no-tools@2",
                "requested_model_ref": "deepseek-v4-pro",
                "expected_actual_model_fingerprint": "deepseek-v4-pro",
                "credential_reference": "env:DEEPSEEK_API_KEY",
                "fallback_after_dispatch": False,
                "provider_call_count": 5,
                "https_dispatch_count": 5,
                "server_statuses": ["RESULT"] * 5,
                "provider_descriptor_provisioned_count": 6,
                "provider_descriptor_consumed_count": 5,
                "provider_descriptor_unused_closed_count": 1,
                "bounded_java_source_semantics_gateway_freeze_ref": "bounded",
                "bounded_java_source_semantics_gateway_freeze_digest": _DIGEST_A,
                "permission_digest": _DIGEST_B,
                "production_activation": "NOT_EXECUTED",
            }
            baseline_output.write_bytes(
                canonical_json_bytes(
                    {
                        **baseline_core,
                        "document_digest": digest_of(baseline_core).value,
                    }
                )
            )
            return 0

        with patch.object(
            gateway_authorized_workload,
            "_load_qualified_baseline",
            return_value=SimpleNamespace(main=baseline_main),
        ):
            with redirect_stdout(StringIO()):
                code = gateway_authorized_workload.main(
                    self._arguments(self._receipt(), output)
                )

        self.assertEqual(code, 0)
        value = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(value["provider_type"], "DEEPSEEK")
        self.assertEqual(value["provider_call_count"], 5)
        self.assertEqual(value["provider_descriptor_unused_closed_count"], 1)
        self.assertEqual(
            value["qualified_gateway_baseline"],
            {
                "entrypoint_sha256": (
                    gateway_authorized_workload.
                    _BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_SHA256
                ),
                "bounded_source_semantics_capability_freeze_digest": _DIGEST_A,
                "role": "QUALIFIED_CAPABILITY_BASELINE_ONLY",
            },
        )


if __name__ == "__main__":
    unittest.main()
