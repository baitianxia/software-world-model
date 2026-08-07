from __future__ import annotations

from datetime import datetime, timezone
import unittest

from software_world_model.cross_cutting import (
    CanonicalizationError,
    Revision,
    StableId,
    canonical_json_bytes,
    digest_of,
)


class FoundationTests(unittest.TestCase):
    def test_canonical_digest_is_independent_of_mapping_order(self) -> None:
        left = {"b": [2, 1], "a": {"x": "值"}}
        right = {"a": {"x": "值"}, "b": [2, 1]}

        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))
        self.assertEqual(digest_of(left), digest_of(right))

    def test_canonical_encoding_rejects_ambiguous_values(self) -> None:
        with self.assertRaises(CanonicalizationError):
            canonical_json_bytes({"value": 0.1})
        with self.assertRaises(CanonicalizationError):
            canonical_json_bytes({"values": {"unordered"}})
        with self.assertRaises(CanonicalizationError):
            canonical_json_bytes(datetime(2026, 8, 6))

    def test_revision_and_stable_id_are_validated(self) -> None:
        self.assertEqual(Revision(1).next(), Revision(2))
        with self.assertRaises(ValueError):
            Revision(0)
        with self.assertRaises(ValueError):
            StableId("scope_not-hex")
        stable_id = StableId("scope_00000000000000000000000000000001")
        self.assertEqual(stable_id.kind, "scope")
        self.assertEqual(
            canonical_json_bytes(datetime(2026, 8, 6, tzinfo=timezone.utc)),
            b'"2026-08-06T00:00:00.000000Z"',
        )


if __name__ == "__main__":
    unittest.main()
