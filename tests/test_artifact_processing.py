from __future__ import annotations

import hashlib
import unittest

from software_world_model.cross_cutting import Digest, Revision, StableId, digest_of
from software_world_model.infrastructure import SqliteArtifactProcessingRepository, SqliteDatabase
from software_world_model.source_integration import (
    DeterministicArtifactProcessingService,
    SourceArtifact,
)


class ArtifactProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.repository = SqliteArtifactProcessingRepository(self.database)
        self.service = DeterministicArtifactProcessingService(self.repository)

    def tearDown(self) -> None:
        self.database.close()

    def parent(self) -> SourceArtifact:
        payload = "甲乙丙丁\nalpha beta gamma\n".encode("utf-8")
        return SourceArtifact(
            artifact_id=StableId("source_artifact_00000000000000000000000000000001"),
            artifact_kind="LOCAL_GIT_FILE@1",
            payload_schema_version="1",
            source_id=StableId("source_00000000000000000000000000000001"),
            source_revision=Revision(1),
            source_context_id=StableId("source_context_00000000000000000000000000000001"),
            source_native_identity="src/test.txt",
            content_digest=Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}"),
            payload=payload,
            classification="INTERNAL",
            truncated=False,
            truncation_offset=None,
            identity_digest=digest_of({"parent": 1}),
        )

    def test_deterministic_chunks_are_utf8_safe_replayable_and_idempotent(self) -> None:
        parent = self.parent()
        first = self.service.chunk_text(parent=parent, max_chunk_bytes=7)
        replay = self.service.chunk_text(parent=parent, max_chunk_bytes=7)

        self.assertEqual(first, replay)
        self.assertEqual(b"".join(item.payload for item in first), parent.payload)
        self.assertTrue(all(item.payload.decode("utf-8") for item in first))
        self.assertTrue(all(item.parent_artifact_ids == (parent.artifact_id,) for item in first))


if __name__ == "__main__":
    unittest.main()
