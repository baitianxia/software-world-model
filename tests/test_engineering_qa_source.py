from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.application_services.engineering_question_answering import (
    COMPILED_SOURCE_OPERATION_SCHEMA,
    ENGINEERING_QA_BROKER_POLICY,
    CompiledSourceOperation,
    EngineeringEvidenceClass,
    EngineeringQuestionAnsweringService,
    EngineeringQuestionRequest,
    EngineeringQuestionResultStatus,
    RetrievalStatus,
    SourceBroker,
    SourceReadOperation,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.interface.engineering_qa_source import (
    LocalGitEvidenceClassProfile,
    LocalGitRetrievalWorker,
)
from tests import test_engineering_question_answering as fixtures


def sid(kind: str, digit: str) -> StableId:
    return StableId(f"{kind}_{digit * 32}")


class LocalGitRetrievalWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name) / "repository"
        self.repository.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        (self.repository / "README.md").write_text(
            "Use ./run-service to start the service.\nrequest timeout is configurable.\n",
            encoding="utf-8",
        )
        (self.repository / "large.txt").write_text("x" * 128, encoding="utf-8")
        (self.repository / "binary.dat").write_bytes(b"value\x00binary")
        (self.repository / "link.txt").symlink_to("README.md")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.repository_id = sid("repository", "3")
        self.binding_id = sid("binding", "4")
        self.source_profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-local-git-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: (
                    "large.txt",
                    "binary.dat",
                    "link.txt",
                ),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.source_profile,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def operation(
        self,
        *,
        operation: SourceReadOperation,
        allowlist=(".",),
        query=None,
        path=None,
        search_path_scope=(),
        search_path_prefix_scope=(),
        search_fallback_offset=0,
        maximum_source_bytes=4096,
        maximum_files=16,
        evidence_class=EngineeringEvidenceClass.SOURCE,
    ):
        request_digest = Digest("sha256:" + "1" * 64)
        proposal_digest = Digest("sha256:" + "2" * 64)
        source_allowlist = tuple(allowlist)
        locator_reference = (
            None
            if operation is SourceReadOperation.SEARCH
            else sid("source_locator", "5")
        )
        core = {
            "broker_policy": ENGINEERING_QA_BROKER_POLICY,
            "request_digest": request_digest.value,
            "proposal_digest": proposal_digest.value,
            "repository_id": self.repository_id.value,
            "binding_id": self.binding_id.value,
            "repository_revision": self.revision,
            "source_profile_ref": self.source_profile.profile_ref,
            "source_profile_digest": self.source_profile.profile_digest.value,
            "operation": operation.value,
            "source_allowlist": source_allowlist,
            "evidence_class_allowlist": self.source_profile.paths_for(
                evidence_class
            ),
            "evidence_class": evidence_class.value,
            "result_modality": self.source_profile.modality_for(
                evidence_class=evidence_class,
                operation=operation,
            ),
            "query": query,
            "search_path_scope": tuple(search_path_scope),
            "search_path_prefix_scope": tuple(search_path_prefix_scope),
            "search_fallback_offset": search_fallback_offset,
            "path": path,
            "locator_reference": (
                locator_reference.value if locator_reference else None
            ),
            "maximum_files": maximum_files,
            "maximum_source_bytes": maximum_source_bytes,
            "maximum_result_items": 32,
        }
        return CompiledSourceOperation(
            operation_id=StableId(
                "source_operation_"
                + digest_of(["source_operation", core])
                .value.removeprefix("sha256:")[:32]
            ),
            broker_policy=ENGINEERING_QA_BROKER_POLICY,
            request_digest=request_digest,
            proposal_digest=proposal_digest,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            repository_revision=self.revision,
            source_profile_ref=self.source_profile.profile_ref,
            source_profile_digest=self.source_profile.profile_digest,
            operation=operation,
            source_allowlist=source_allowlist,
            evidence_class_allowlist=self.source_profile.paths_for(
                evidence_class
            ),
            evidence_class=evidence_class,
            result_modality=self.source_profile.modality_for(
                evidence_class=evidence_class,
                operation=operation,
            ),
            query=query,
            search_path_scope=tuple(search_path_scope),
            search_path_prefix_scope=tuple(search_path_prefix_scope),
            search_fallback_offset=search_fallback_offset,
            path=path,
            locator_reference=locator_reference,
            maximum_files=maximum_files,
            maximum_source_bytes=maximum_source_bytes,
            maximum_result_items=32,
            digest=digest_of([COMPILED_SOURCE_OPERATION_SCHEMA, core]),
        )

    def test_search_and_read_use_exact_committed_bytes(self):
        search = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("README.md",),
                query="timeout",
                evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
            )
        )
        self.assertEqual(search.status, RetrievalStatus.COMPLETE)
        self.assertEqual(len(search.items), 1)
        self.assertEqual(search.items[0].path, "README.md")

        (self.repository / "README.md").write_text(
            "uncommitted replacement", encoding="utf-8"
        )
        read = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.READ,
                allowlist=("README.md",),
                path="README.md",
                evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
            )
        )
        self.assertEqual(read.status, RetrievalStatus.COMPLETE)
        self.assertEqual(
            read.items[0].modality,
            "EXACT_REPOSITORY_DOCUMENT_TEXT",
        )
        self.assertIn("run-service", read.items[0].content)
        self.assertNotIn("uncommitted", read.items[0].content)

    def test_symlink_and_binary_are_rejected(self):
        link = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.READ,
                allowlist=("link.txt",),
                path="link.txt",
            )
        )
        self.assertEqual(link.status, RetrievalStatus.FAILED)
        self.assertEqual(link.failure_code, "UNSAFE_SOURCE_ENTRY_KIND")

        binary = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.READ,
                allowlist=("binary.dat",),
                path="binary.dat",
            )
        )
        self.assertEqual(binary.status, RetrievalStatus.FAILED)
        self.assertEqual(binary.failure_code, "BINARY_SOURCE_REJECTED")

    def test_oversize_blob_is_not_read_past_fuse(self):
        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.READ,
                allowlist=("large.txt",),
                path="large.txt",
                maximum_source_bytes=16,
            )
        )
        self.assertEqual(result.status, RetrievalStatus.PARTIAL)
        self.assertTrue(result.truncated)
        self.assertEqual(result.bytes_read, 0)
        self.assertEqual(result.files_read, 0)
        self.assertEqual(
            result.failure_code, "SOURCE_BYTE_FUSE_WOULD_BE_EXCEEDED"
        )

    def test_search_reports_unsupported_entries_as_partial(self):
        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                query="value",
            )
        )
        self.assertEqual(result.status, RetrievalStatus.PARTIAL)
        self.assertEqual(result.failure_code, "UNSUPPORTED_SOURCE_ENTRY")
        self.assertTrue(result.truncated)

    def test_search_prioritizes_literal_path_candidates_before_file_fuse(self):
        search_root = self.repository / "search"
        search_root.mkdir()
        for index in range(20):
            (search_root / f"unrelated-{index:02d}.txt").write_text(
                "no matching token\n", encoding="utf-8"
            )
        target = search_root / "LoginService.java"
        target.write_text(
            "// LoginService.java\npublic interface Authentication {}\n",
            encoding="utf-8",
        )
        self.git("add", "search")
        self.git("commit", "-q", "-m", "search ranking fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.source_profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-path-ranked-search-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("search",),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.source_profile,
        )

        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("search",),
                query="LoginService",
                maximum_files=2,
            )
        )

        self.assertEqual(result.status, RetrievalStatus.PARTIAL)
        self.assertEqual(
            result.failure_code,
            "SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP",
        )
        self.assertEqual(result.files_read, 1)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].path, "search/LoginService.java")
        coverage = dict(result.coverage)
        self.assertEqual(
            coverage["candidate_ordering"],
            "QUERY_IDENTIFIER_PATH_RELEVANCE_THEN_ROTATING_CANONICAL_FALLBACK@3",
        )
        self.assertEqual(coverage["exact_stem_candidate_count"], "1")
        self.assertEqual(coverage["filename_candidate_count"], "1")
        self.assertEqual(coverage["filename_content_match_count"], "1")
        self.assertEqual(coverage["filename_early_stop"], "true")

        filename_only_result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("search",),
                query="LoginService.java",
                maximum_files=2,
            )
        )
        filename_only_coverage = dict(filename_only_result.coverage)
        self.assertEqual(filename_only_result.status, RetrievalStatus.PARTIAL)
        self.assertEqual(
            filename_only_result.failure_code,
            "SOURCE_SEARCH_FILE_LIMIT_REACHED",
        )
        self.assertEqual(filename_only_result.files_read, 2)
        self.assertEqual(
            filename_only_coverage["exact_stem_candidate_count"], "0"
        )
        self.assertEqual(filename_only_coverage["filename_early_stop"], "false")

    def test_search_path_hint_prioritizes_exact_cognition_provenance(self):
        search_root = self.repository / "hinted"
        search_root.mkdir()
        for index in range(20):
            (search_root / f"unrelated-{index:02d}.txt").write_text(
                "no matching token\n", encoding="utf-8"
            )
        target = search_root / "implementation.java"
        target.write_text("int updateSkuStock() { return 1; }\n", encoding="utf-8")
        self.git("add", "hinted")
        self.git("commit", "-q", "-m", "cognition source hint fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.source_profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-cognition-hint-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("hinted",),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.source_profile,
            search_path_hints={"updateSkuStock": ("hinted/implementation.java",)},
        )
        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("hinted",),
                query="updateSkuStock",
                maximum_files=1,
            )
        )
        self.assertEqual(result.files_read, 1)
        self.assertEqual(result.items[0].path, "hinted/implementation.java")

    def test_search_prioritizes_identifier_component_beyond_file_fuse(self):
        search_root = self.repository / "module/src/main/java/example"
        search_root.mkdir(parents=True)
        for index in range(75):
            (search_root / f"AFile{index:02d}.java").write_text(
                "final class Fixture {}\n",
                encoding="utf-8",
            )
        target = search_root / "OmsPortalOrderServiceImpl.java"
        target.write_text(
            "final class OmsPortalOrderServiceImpl { void generateOrder() {} }\n",
            encoding="utf-8",
        )
        for index in range(8):
            (search_root / f"ZFile{index:02d}.java").write_text(
                "final class Fixture {}\n",
                encoding="utf-8",
            )
        self.git("add", "module")
        self.git("commit", "-q", "-m", "identifier component search fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.source_profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-identifier-component-search-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("module/src/main/java",),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.source_profile,
        )

        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("module/src/main/java",),
                query="createOrder",
                search_path_prefix_scope=("module/src/main/java",),
                maximum_files=56,
                maximum_source_bytes=64_000,
            )
        )

        self.assertEqual(result.status, RetrievalStatus.PARTIAL)
        self.assertEqual(result.failure_code, "SOURCE_SEARCH_FILE_LIMIT_REACHED")
        self.assertEqual(result.files_read, 56)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(
            result.navigation_candidate_item_ids,
            (result.items[0].item_id,),
        )
        self.assertEqual(
            result.items[0].modality,
            "IDENTIFIER_PATH_NAVIGATION_CANDIDATE",
        )
        self.assertEqual(
            result.items[0].path,
            "module/src/main/java/example/OmsPortalOrderServiceImpl.java",
        )
        coverage = dict(result.coverage)
        self.assertEqual(coverage["scoped_entry_count"], "84")
        self.assertEqual(coverage["fallback_examined_file_count"], "55")
        self.assertEqual(coverage["match_count"], "0")
        self.assertEqual(coverage["identifier_navigation_term_count"], "2")
        self.assertEqual(
            coverage["identifier_navigation_candidate_count"],
            "1",
        )
        self.assertEqual(
            coverage["identifier_navigation_candidate_total_count"],
            "1",
        )
        self.assertEqual(
            coverage["candidate_ordering"],
            "QUESTION_PREFIX_QUERY_IDENTIFIER_PATH_THEN_ROTATING_CANONICAL_FALLBACK@2",
        )

    def test_search_reads_every_exact_stem_candidate_before_early_stop(self):
        for module in ("first", "second"):
            root = self.repository / module
            root.mkdir()
            (root / "LoginService.java").write_text(
                f"package {module}; public interface LoginService {{}}\n",
                encoding="utf-8",
            )
            (root / "Unrelated.java").write_text(
                "final class Unrelated {}\n",
                encoding="utf-8",
            )
        (self.repository / "first" / "LoginServiceAudit.java").write_text(
            "final class LoginServiceAudit {}\n",
            encoding="utf-8",
        )
        self.git("add", "first", "second")
        self.git("commit", "-q", "-m", "duplicate stem search fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.source_profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-multi-stem-search-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("first", "second"),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.source_profile,
        )

        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("first", "second"),
                query="LoginService",
                maximum_files=4,
            )
        )

        self.assertEqual(result.status, RetrievalStatus.PARTIAL)
        self.assertEqual(
            result.failure_code,
            "SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP",
        )
        self.assertEqual(result.files_read, 3)
        self.assertEqual(
            tuple(item.path for item in result.items),
            (
                "first/LoginService.java",
                "second/LoginService.java",
                "first/LoginServiceAudit.java",
            ),
        )
        coverage = dict(result.coverage)
        self.assertEqual(coverage["exact_stem_candidate_count"], "2")
        self.assertEqual(coverage["filename_candidate_count"], "3")
        self.assertEqual(coverage["filename_content_match_count"], "3")
        self.assertEqual(coverage["filename_early_stop"], "true")

    def test_search_reports_compiled_operation_byte_limit_as_local_partial(self):
        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("large.txt",),
                query="not-present",
                maximum_source_bytes=16,
            )
        )

        self.assertEqual(result.status, RetrievalStatus.PARTIAL)
        self.assertEqual(
            result.failure_code,
            "SOURCE_SEARCH_BYTE_LIMIT_REACHED",
        )
        self.assertEqual(result.files_read, 0)
        self.assertEqual(result.bytes_read, 0)

    def test_trusted_target_path_scope_bounds_literal_search_to_exact_files(self):
        search_root = self.repository / "scoped"
        search_root.mkdir()
        for index in range(20):
            (search_root / f"Unrelated{index:02d}.java").write_text(
                "final class Unrelated {}\n",
                encoding="utf-8",
            )
        target = search_root / "CredentialVerifier.java"
        target.write_text(
            "public final class CredentialVerifier {}\n",
            encoding="utf-8",
        )
        self.git("add", "scoped")
        self.git("commit", "-q", "-m", "trusted search scope fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.source_profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-trusted-search-scope-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("scoped",),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.source_profile,
        )

        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("scoped",),
                query="CredentialVerifier",
                search_path_scope=("scoped/CredentialVerifier.java",),
                maximum_files=1,
            )
        )

        self.assertEqual(result.status, RetrievalStatus.COMPLETE)
        self.assertEqual(result.files_read, 1)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].path, "scoped/CredentialVerifier.java")
        coverage = dict(result.coverage)
        self.assertEqual(coverage["allowed_entry_count"], "21")
        self.assertEqual(coverage["examined_file_count"], "1")
        self.assertEqual(coverage["search_path_scope_count"], "1")
        self.assertEqual(
            coverage["candidate_ordering"],
            "TRUSTED_TARGET_PATH_SCOPE_THEN_CANONICAL@2",
        )

    def test_trusted_target_path_scope_missing_from_exact_tree_fails_closed(self):
        search_root = self.repository / "scoped"
        search_root.mkdir()
        (search_root / "Present.java").write_text(
            "final class Present {}\n",
            encoding="utf-8",
        )
        self.git("add", "scoped")
        self.git("commit", "-q", "-m", "trusted search scope exact tree fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.source_profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-missing-search-scope-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("scoped",),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.source_profile,
        )

        result = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=("scoped",),
                query="Missing",
                search_path_scope=("scoped/Missing.java",),
                maximum_files=1,
            )
        )

        self.assertEqual(result.status, RetrievalStatus.FAILED)
        self.assertEqual(
            result.failure_code,
            "SOURCE_SEARCH_PATH_SCOPE_INCONSISTENT",
        )
        self.assertEqual(result.files_read, 0)
        self.assertEqual(result.bytes_read, 0)
        coverage = dict(result.coverage)
        self.assertEqual(coverage["missing_search_path_scope_count"], "1")
        self.assertEqual(
            coverage["search_scope"],
            "TRUSTED_COGNITION_TARGET_PATHS",
        )

    def test_question_prefix_scope_rotates_only_the_canonical_fallback_cohort(
        self,
    ) -> None:
        module_a = self.repository / "module-a/src/main/java/example"
        module_b = self.repository / "module-b/src/main/java/example"
        module_a.mkdir(parents=True)
        module_b.mkdir(parents=True)
        for index in range(70):
            content = (
                "final class Fixture { void needleSecond() {} }\n"
                if index == 62
                else "final class Fixture {}\n"
            )
            (module_a / f"AFile{index:02d}.java").write_text(
                content,
                encoding="utf-8",
            )
        (module_b / "AFile00.java").write_text(
            "final class WrongModule { void needleSecond() {} }\n",
            encoding="utf-8",
        )
        self.git("add", "module-a", "module-b")
        self.git("commit", "-q", "-m", "rotating scoped search fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.source_profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-rotating-prefix-scope-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: (
                    "module-a/src/main/java",
                    "module-b/src/main/java",
                ),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.source_profile,
        )
        allowlist = (
            "module-a/src/main/java",
            "module-b/src/main/java",
        )
        prefix_scope = ("module-a/src/main/java",)

        first = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=allowlist,
                query="absentFirst",
                search_path_prefix_scope=prefix_scope,
                maximum_files=56,
                maximum_source_bytes=64_000,
            )
        )
        second = self.worker.execute(
            self.operation(
                operation=SourceReadOperation.SEARCH,
                allowlist=allowlist,
                query="needleSecond",
                search_path_prefix_scope=prefix_scope,
                search_fallback_offset=56,
                maximum_files=7,
                maximum_source_bytes=64_000,
            )
        )

        self.assertEqual(first.files_read, 56)
        self.assertEqual(
            dict(first.coverage)["fallback_examined_file_count"],
            "56",
        )
        self.assertEqual(second.files_read, 7)
        self.assertEqual(len(second.items), 1)
        self.assertEqual(
            second.items[0].path,
            "module-a/src/main/java/example/AFile62.java",
        )
        coverage = dict(second.coverage)
        self.assertEqual(coverage["allowed_entry_count"], "71")
        self.assertEqual(coverage["scoped_entry_count"], "70")
        self.assertEqual(coverage["search_fallback_offset_applied"], "56")
        self.assertEqual(coverage["fallback_examined_file_count"], "7")
        self.assertEqual(
            coverage["search_scope"],
            "ORIGINAL_QUESTION_EXPLICIT_SOURCE_PREFIXES",
        )

    def test_worker_rejects_another_repository_identity(self):
        operation = replace(
            self.operation(
                operation=SourceReadOperation.READ,
                allowlist=("README.md",),
                path="README.md",
            ),
            repository_id=sid("repository", "9"),
        )
        with self.assertRaises(DomainError):
            self.worker.execute(operation)

    def test_source_profile_rejects_overlapping_evidence_classes(self):
        with self.assertRaises(DomainError):
            LocalGitEvidenceClassProfile.create(
                profile_ref="overlapping-source-profile:1",
                binding_id=self.binding_id,
                evidence_class_paths={
                    EngineeringEvidenceClass.SOURCE: ("src",),
                    EngineeringEvidenceClass.TEST: ("src/test",),
                },
            )

    def test_worker_rejects_model_relabeling_a_document_as_configuration(self):
        operation = self.operation(
            operation=SourceReadOperation.PARSE,
            allowlist=("README.md",),
            path="README.md",
            evidence_class=EngineeringEvidenceClass.BUILD_CONFIGURATION,
        )
        with self.assertRaises(DomainError) as caught:
            self.worker.execute(operation)
        self.assertEqual(
            caught.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

    def test_broker_and_local_git_worker_complete_the_application_chain(self):
        request = EngineeringQuestionRequest.create(
            request_ref="local-git-chain",
            original_question=fixtures.request().original_question,
            response_language="en",
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            repository_revision=self.revision,
            source_profile_ref=self.source_profile.profile_ref,
            source_profile_digest=self.source_profile.profile_digest,
            world_model_read_authority_digest=Digest("sha256:" + "3" * 64),
            source_allowlist=(".",),
        )
        service = EngineeringQuestionAnsweringService(
            question_understanding_role=fixtures.UnderstandingRole(),
            cognition_projector=fixtures.CognitionProjector(),
            initial_investigation_role=fixtures.InitialInvestigator(),
            verification_investigation_role=fixtures.VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=self.source_profile),
            retrieval_worker=self.worker,
            answer_role=fixtures.AnswerRole(),
            reviewer_role=fixtures.ReviewerRole(request_more_evidence=False),
        )
        result = service.answer(request)
        self.assertEqual(result.status, EngineeringQuestionResultStatus.APPROVED)
        self.assertEqual(result.usage.source_operations, 2)
        self.assertTrue(
            any(
                item.locator == "README.md"
                for item in result.current_package.support_citation
            )
        )


if __name__ == "__main__":
    unittest.main()
