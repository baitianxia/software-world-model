from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from swm_demo.formal_validation import (
    AnswerCandidate,
    AnswerClaim,
    Artifact,
    AtomicFact,
    AuthorizedInputItem,
    AuthorizedInputManifest,
    BuildBudget,
    ClosedChangeSetFact,
    ClosedLiteralSelectionFact,
    ContractViolation,
    CriterionObligation,
    DirectClaimOracleItem,
    EntityState,
    Envelope,
    Evidence,
    FormalInference,
    IsolationReceipt,
    JointConstraint,
    JointConstraintAssessment,
    KnowledgeUseIsolationProof,
    LocalGitReadOnlyProvider,
    NeedAssessment,
    ObligationSupport,
    ProductionReader,
    RequirementNeed,
    RequirementRevision,
    RevisionImpactBuildTarget,
    ValidationAuthorityStore,
    assert_acyclic,
    assess_overall,
    authorize_answer,
    build_no_tools_request,
    canonical_bytes,
    compare_claim_preservation,
    digest,
    evidence_for_literal,
    render_manifest,
    review_atomic_fact,
    review_inference,
    verify_closed_change_set,
    verify_closed_literal_selection,
)


TARGET = "dacce5f28dfc1734f2db09668d928d7fac2a3a7a"
PARENT = "00bd03591cfd91f82ebe48787315eed613754277"
NEED_IDS = tuple(f"JWT-N0{index}" for index in range(1, 7))
JAVA_PATH = "mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java"


OBLIGATION_DIMENSIONS = {
    "JWT-N01": (
        ("DIRECT_SUPPORT", "exact target and unique parent"),
        ("ENUMERATION_COVERAGE", "complete changed-file set"),
    ),
    "JWT-N02": (
        ("DIRECT_SUPPORT", "root JJWT version declaration change"),
        ("DIRECT_SUPPORT", "root dependency-management declaration change"),
        ("DIRECT_SUPPORT", "security-module direct dependency change"),
    ),
    "JWT-N03": (
        ("DIRECT_SUPPORT", "token construction API change"),
        ("DIRECT_SUPPORT", "secret byte conversion"),
        ("DIRECT_SUPPORT", "expiration value representation and unit"),
    ),
    "JWT-N04": (
        ("DIRECT_SUPPORT", "signature verification and parsing order"),
        ("COUNTEREXAMPLE_CHECK", "invalid signature or format result"),
        ("COUNTEREXAMPLE_CHECK", "missing username result"),
        ("COUNTEREXAMPLE_CHECK", "missing expiration result"),
        ("COUNTEREXAMPLE_CHECK", "invalid expiration type result"),
        ("COUNTEREXAMPLE_CHECK", "expiration equality boundary"),
    ),
    "JWT-N05": (
        ("DIRECT_SUPPORT", "created accepted representations"),
        ("COUNTEREXAMPLE_CHECK", "unsupported created representation"),
        ("COUNTEREXAMPLE_CHECK", "refresh interval lower and upper boundaries"),
        ("DIRECT_SUPPORT", "original token versus re-sign output"),
    ),
    "JWT-N06": (
        ("UNKNOWN_OR_LIMITATION_DISCLOSURE", "new library default signing algorithm"),
        ("UNKNOWN_OR_LIMITATION_DISCLOSURE", "old HS512 comment modality"),
    ),
}


def make_requirement() -> RequirementRevision:
    needs = []
    for need_ordinal, need_id in enumerate(NEED_IDS):
        obligations = tuple(
            CriterionObligation(
                obligation_id=f"{need_id}-O{ordinal + 1:02d}",
                need_id=need_id,
                ordinal=ordinal,
                role=role,
                dimension=dimension,
            )
            for ordinal, (role, dimension) in enumerate(OBLIGATION_DIMENSIONS[need_id])
        )
        needs.append(
            RequirementNeed(
                need_id=need_id,
                ordinal=need_ordinal,
                question=f"Frozen JWT impact Need {need_id}",
                sufficiency_criterion="Every registered obligation must have exact formal support.",
                obligations=obligations,
            )
        )
    return RequirementRevision(
        revision_id="jwt-requirement-002",
        needs=tuple(needs),
        joint_constraints=(
            JointConstraint(
                constraint_id="JWT-J01",
                need_ids=NEED_IDS,
                criterion="All conclusions use the same repository, target, parent, and comparison context.",
            ),
        ),
    )


def make_target(provider: LocalGitReadOnlyProvider) -> RevisionImpactBuildTarget:
    return RevisionImpactBuildTarget(
        repository_identity=provider.repository_identity,
        target_commit=TARGET,
        base_commit=PARENT,
        requirement=make_requirement(),
        budget=BuildBudget(40, 16, 1_000_000, 80),
    )


class FormalValidationConformanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[2]
        cls.provider = LocalGitReadOnlyProvider(
            root / "validation-projects" / "mall",
            "repo:macrozheng/mall",
        )

    def test_01_build_target_requires_full_commit_unique_parent_and_complete_needs(self) -> None:
        target = make_target(self.provider)
        target.validate(parent_resolver=self.provider.parents, expected_need_ids=NEED_IDS)
        with self.assertRaises(ContractViolation):
            replace(target, target_commit=TARGET[:8]).validate(
                parent_resolver=self.provider.parents,
                expected_need_ids=NEED_IDS,
            )
        with self.assertRaises(ContractViolation):
            replace(target, base_commit="0" * 40).validate(
                parent_resolver=self.provider.parents,
                expected_need_ids=NEED_IDS,
            )
        incomplete = replace(target.requirement, needs=target.requirement.needs[:-1])
        with self.assertRaises(ContractViolation):
            replace(target, requirement=incomplete).validate(
                parent_resolver=self.provider.parents,
                expected_need_ids=NEED_IDS,
            )

    def _manifest(self, role: str = "ANSWER_GENERATOR") -> AuthorizedInputManifest:
        return AuthorizedInputManifest(
            role=role,
            capability_ref="capability@1",
            strategy_ref="strategy@1",
            prompt_contract_ref="prompt@1",
            output_contract_ref="output@1",
            items=(
                AuthorizedInputItem("PROMPT_INSTRUCTION", "prompt@1#0", {"instruction": "Use only supplied formal knowledge."}),
                AuthorizedInputItem("REQUIREMENT", "requirement@2", {"needs": NEED_IDS}),
                AuthorizedInputItem("FORMAL_KNOWLEDGE", "snapshot@3", {"members": ["fact:1"]}),
            ),
        )

    def _request(self) -> tuple[AuthorizedInputManifest, dict]:
        manifest = self._manifest()
        rendered = render_manifest(
            manifest,
            rendering_step_ref="renderer@1",
            allowed_kinds={"PROMPT_INSTRUCTION", "REQUIREMENT", "FORMAL_KNOWLEDGE"},
        )
        request = build_no_tools_request(
            manifest,
            rendered,
            model="pinned-model-snapshot",
            max_output_tokens=2000,
            reasoning={"effort": "medium"},
            metadata={
                "call_id": "call-1",
                "capability_id": "capability@1",
                "manifest_digest": digest(manifest),
                "baseline_id": "SWM-DBM-ITER-001-REV-002",
            },
            output_schema={"type": "json_schema", "name": "answer", "strict": True, "schema": {"type": "object"}},
        )
        return manifest, request

    def test_02_manifest_rendering_is_bidirectional_and_answer_rejects_source(self) -> None:
        manifest = self._manifest()
        rendered = render_manifest(
            manifest,
            rendering_step_ref="renderer@1",
            allowed_kinds={"PROMPT_INSTRUCTION", "REQUIREMENT", "FORMAL_KNOWLEDGE"},
        )
        with self.assertRaises(ContractViolation):
            build_no_tools_request(
                manifest,
                rendered[:-1],
                model="pinned-model-snapshot",
                max_output_tokens=10,
                reasoning={"effort": "low"},
                metadata={},
                output_schema={"type": "text"},
            )
        with self.assertRaises(ContractViolation):
            build_no_tools_request(
                manifest,
                rendered,
                model="pinned-model-snapshot",
                max_output_tokens=10,
                reasoning={"effort": "low"},
                metadata={
                    "call_id": "call-1",
                    "capability_id": "another-capability@1",
                    "manifest_digest": digest(manifest),
                    "baseline_id": "SWM-DBM-ITER-001-REV-002",
                },
                output_schema={"type": "text"},
            )
        tampered = (
            replace(rendered[0], content='{"instruction":"different"}'),
        ) + rendered[1:]
        with self.assertRaises(ContractViolation):
            build_no_tools_request(
                manifest,
                tampered,
                model="pinned-model-snapshot",
                max_output_tokens=10,
                reasoning={"effort": "low"},
                metadata={
                    "call_id": "call-1",
                    "capability_id": "capability@1",
                    "manifest_digest": digest(manifest),
                    "baseline_id": "SWM-DBM-ITER-001-REV-002",
                },
                output_schema={"type": "text"},
            )
        source_manifest = replace(
            manifest,
            items=manifest.items + (AuthorizedInputItem("SOURCE_OBSERVATION", "artifact:1", {"payload": "forbidden"}),),
        )
        with self.assertRaises(ContractViolation):
            render_manifest(
                source_manifest,
                rendering_step_ref="renderer@1",
                allowed_kinds={"PROMPT_INSTRUCTION", "REQUIREMENT", "FORMAL_KNOWLEDGE"},
            )

    def test_03_pre_dispatch_isolation_receipt_requires_live_cc_and_exact_body(self) -> None:
        _, request = self._request()
        receipt = IsolationReceipt.issue(
            request,
            adapter_profile_ref="SWM-ADAPTER-OAI-RESPONSES-001@0.1.0",
            live_conformance_result_ref="CC-MODEL-NO-TOOLS-001:PASS:fixture",
        )
        receipt.verify_dispatched_body(request)
        with self.assertRaises(ContractViolation):
            IsolationReceipt.issue(
                {**request, "tools": [{"type": "web_search"}]},
                adapter_profile_ref="adapter",
                live_conformance_result_ref="cc",
            )
        with self.assertRaises(ContractViolation):
            IsolationReceipt.issue(
                request,
                adapter_profile_ref="adapter",
                live_conformance_result_ref="",
            )
        with self.assertRaises(ContractViolation):
            receipt.verify_dispatched_body({**request, "store": True})

    def test_04_atomic_fact_is_directly_entailed_and_rejects_cross_evidence_semantics(self) -> None:
        artifact = Artifact("a", "READ", "repo", TARGET, JAVA_PATH, b"return JWTUtil.createToken(claims, getSigningKey());", True, True)
        evidence = Evidence.materialize("e", artifact, 0, len(artifact.payload))
        entity = EntityState("entity:method", "code-symbol", "JwtTokenUtil#generateToken", "anchor")
        valid = AtomicFact(
            "fact:valid",
            entity.entity_id,
            "DECLARES_INVOCATION",
            (("TARGET", "JWTUtil.createToken"),),
            "CODE_DECLARES",
            evidence.evidence_id,
            TARGET,
            ("JWT-N03-O01",),
        )
        review_atomic_fact(valid, evidence, {entity.entity_id: entity})
        invalid = replace(valid, fact_id="fact:invalid", role_terms=(("ALGORITHM", "library default"),))
        with self.assertRaises(ContractViolation):
            review_atomic_fact(invalid, evidence, {entity.entity_id: entity})

    def test_05_closed_change_and_literal_coverage_fail_on_partial_or_wrong_members(self) -> None:
        comparison = self.provider.compare(PARENT, TARGET)
        expected = (
            ("M", "mall-security/pom.xml"),
            ("M", JAVA_PATH),
            ("M", "pom.xml"),
        )
        verify_closed_change_set(comparison, expected, declared_cardinality=3)
        with self.assertRaises(ContractViolation):
            verify_closed_change_set(comparison, expected[:-1], declared_cardinality=2)
        after_root = self.provider.read(TARGET, "pom.xml")
        verify_closed_literal_selection(
            after_root,
            b"<jjwt.version>",
            (),
            scanned_bytes=len(after_root.payload),
            source_blob_bytes=len(after_root.payload),
        )
        with self.assertRaises(ContractViolation):
            verify_closed_literal_selection(
                replace(after_root, terminal=False),
                b"<jjwt.version>",
                (),
                scanned_bytes=len(after_root.payload),
                source_blob_bytes=len(after_root.payload),
            )

    def test_06_entity_then_fact_then_inference_publication_is_enforced(self) -> None:
        store = ValidationAuthorityStore("validation:jwt")
        entity = EntityState("entity:file", "source-unit", JAVA_PATH, "e:anchor")
        entity_snapshot = store.publish(entities=(entity,))
        fact = AtomicFact("fact:1", entity.entity_id, "DECLARES_RETURN", (("OUTPUT", "return null"),), "CODE_DECLARES", "e:1", TARGET, ("JWT-N04-O02",))
        with self.assertRaises(ContractViolation):
            ValidationAuthorityStore("validation:other").publish(facts=(fact,))
        fact_snapshot = store.publish(facts=(fact,))
        inference = FormalInference("inf:1", entity.entity_id, "EXCEPTION_FLOW", "RETURNS_WHEN", (fact.fact_id,), TARGET, ("JWT-N04-O02",))
        inference_snapshot = store.publish(inferences=(inference,))
        self.assertEqual((entity_snapshot.sequence, fact_snapshot.sequence, inference_snapshot.sequence), (1, 2, 3))
        with self.assertRaises(ContractViolation):
            same_batch = ValidationAuthorityStore("validation:same-batch")
            same_batch.publish(entities=(entity,))
            same_batch.publish(facts=(fact,), inferences=(inference,))

    def test_07_semantic_change_is_atomic(self) -> None:
        entity = EntityState("entity:file", "source-unit", JAVA_PATH, "e")
        valid = FormalInference("inf", entity.entity_id, "API_CALL", "REPLACES", ("fact:1",), TARGET, ("JWT-N03-O01",))
        review_inference(valid, premise_snapshot_id="s1", snapshot_id_by_knowledge_id={"fact:1": "s1"}, entities={entity.entity_id: entity})
        with self.assertRaises(ContractViolation):
            review_inference(
                replace(valid, aspect="HISTORY_SUMMARY", relation="MANY_CHANGES"),
                premise_snapshot_id="s1",
                snapshot_id_by_knowledge_id={"fact:1": "s1"},
                entities={entity.entity_id: entity},
            )

    def test_08_unknown_requires_boundary_and_missing_premise(self) -> None:
        entity = EntityState("entity:file", "source-unit", JAVA_PATH, "e")
        unknown = FormalInference(
            "inf:unknown",
            entity.entity_id,
            "VALUE_SEMANTICS",
            "NOT_ESTABLISHED_WITHIN_BOUNDARY",
            ("fact:create-token",),
            TARGET,
            ("JWT-N06-O01",),
            unknown_boundary="LIBRARY_DEFAULT",
            missing_premises=("formal Hutool createToken default algorithm contract",),
        )
        review_inference(unknown, premise_snapshot_id="s1", snapshot_id_by_knowledge_id={"fact:create-token": "s1"}, entities={entity.entity_id: entity})
        with self.assertRaises(ContractViolation):
            review_inference(
                replace(unknown, missing_premises=()),
                premise_snapshot_id="s1",
                snapshot_id_by_knowledge_id={"fact:create-token": "s1"},
                entities={entity.entity_id: entity},
            )

    def test_09_assessment_requires_every_obligation_same_snapshot_and_joint_constraint(self) -> None:
        requirement = make_requirement()
        entity = EntityState("entity:file", "source-unit", JAVA_PATH, "e")
        all_obligations = [ob for need in requirement.needs for ob in need.obligations]
        facts = tuple(
            AtomicFact(f"fact:{ob.obligation_id}", entity.entity_id, "DECLARES_CONDITION", (("CONDITION", ob.dimension),), "CODE_DECLARES", "e", TARGET, (ob.obligation_id,))
            for ob in all_obligations
        )
        store = ValidationAuthorityStore("validation:assessment")
        store.publish(entities=(entity,))
        snapshot = store.publish(facts=facts)
        assessments = tuple(
            NeedAssessment(
                need.need_id,
                "SATISFIED",
                tuple(ObligationSupport(ob.obligation_id, snapshot.snapshot_id, (f"fact:{ob.obligation_id}",)) for ob in need.obligations),
            )
            for need in requirement.needs
        )
        joint = (JointConstraintAssessment("JWT-J01", "SATISFIED", NEED_IDS),)
        self.assertEqual(assess_overall(requirement, snapshot, assessments, joint), "SATISFIED")
        self.assertEqual(assess_overall(requirement, snapshot, assessments[:-1], joint), "NOT_SATISFIED")
        first = assessments[0]
        missing_obligation = (replace(first, supports=first.supports[:-1]),) + assessments[1:]
        self.assertEqual(assess_overall(requirement, snapshot, missing_obligation, joint), "NOT_SATISFIED")
        wrong_snapshot = replace(first.supports[0], snapshot_id="another")
        wrong = (replace(first, supports=(wrong_snapshot,) + first.supports[1:]),) + assessments[1:]
        self.assertEqual(assess_overall(requirement, snapshot, wrong, joint), "NOT_SATISFIED")

    def test_10_answer_authorization_rejects_every_source_side_attempt(self) -> None:
        requirement = make_requirement()
        entity = EntityState("entity:file", "source-unit", JAVA_PATH, "e")
        store = ValidationAuthorityStore("validation:answer")
        store.publish(entities=(entity,))
        facts = tuple(
            AtomicFact(f"fact:{ob.obligation_id}", entity.entity_id, "DECLARES_CONDITION", (("CONDITION", ob.dimension),), "CODE_DECLARES", "e", TARGET, (ob.obligation_id,))
            for need in requirement.needs for ob in need.obligations
        )
        snapshot = store.publish(facts=facts)
        claims = tuple(
            AnswerClaim(
                f"claim:{ob.obligation_id}",
                need.need_id,
                ob.dimension,
                ObligationSupport(ob.obligation_id, snapshot.snapshot_id, (f"fact:{ob.obligation_id}",)),
            )
            for need in requirement.needs for ob in need.obligations
        )
        candidate = AnswerCandidate(snapshot.snapshot_id, claims, "\n".join(claim.text for claim in claims))
        authorize_answer(requirement, snapshot, "SATISFIED", candidate, KnowledgeUseIsolationProof())
        with self.assertRaises(ContractViolation):
            authorize_answer(
                requirement,
                snapshot,
                "SATISFIED",
                candidate,
                KnowledgeUseIsolationProof(source_operation_attempts=1),
            )

    def test_11_production_reader_rejects_validation_snapshot(self) -> None:
        snapshot = ValidationAuthorityStore("validation:jwt").publish()
        with self.assertRaises(ContractViolation):
            ProductionReader().read(snapshot)

    def test_12_envelope_tamper_and_reference_cycles_fail(self) -> None:
        envelope = Envelope.seal("CORE", {"a": 1})
        envelope.verify()
        with self.assertRaises(ContractViolation):
            replace(envelope, core={"a": 2}).verify()
        assert_acyclic({"answer": ("snapshot",), "snapshot": ("facts",), "facts": ()})
        with self.assertRaises(ContractViolation):
            assert_acyclic({"answer": ("snapshot",), "snapshot": ("answer",)})

    def test_13_real_mall_feasibility_witness_runs_build_review_publish_and_source_closed_answer(self) -> None:
        target = make_target(self.provider)
        target.validate(parent_resolver=self.provider.parents, expected_need_ids=NEED_IDS)
        requirement = target.requirement

        comparison = self.provider.compare(PARENT, TARGET)
        expected_changes = (
            ("M", "mall-security/pom.xml"),
            ("M", JAVA_PATH),
            ("M", "pom.xml"),
        )
        verify_closed_change_set(comparison, expected_changes, declared_cardinality=3)

        before_root = self.provider.read(PARENT, "pom.xml")
        after_root = self.provider.read(TARGET, "pom.xml")
        before_security = self.provider.read(PARENT, "mall-security/pom.xml")
        after_security = self.provider.read(TARGET, "mall-security/pom.xml")
        before_java = self.provider.read(PARENT, JAVA_PATH)
        after_java = self.provider.read(TARGET, JAVA_PATH)
        verify_closed_literal_selection(after_root, b"<jjwt.version>", (), scanned_bytes=len(after_root.payload), source_blob_bytes=len(after_root.payload))
        verify_closed_literal_selection(after_security, b"<artifactId>jjwt</artifactId>", (), scanned_bytes=len(after_security.payload), source_blob_bytes=len(after_security.payload))

        evidence_by_id: dict[str, Evidence] = {}

        def literal_evidence(evidence_id: str, artifact: Artifact, text: str) -> Evidence:
            evidence = evidence_for_literal(evidence_id, artifact, text.encode("utf-8"))
            evidence_by_id[evidence_id] = evidence
            return evidence

        source_literals = (
            ("e:jjwt-version", before_root, "<jjwt.version>0.9.1</jjwt.version>"),
            ("e:jjwt-root", before_root, "<artifactId>jjwt</artifactId>"),
            ("e:jjwt-security", before_security, "<artifactId>jjwt</artifactId>"),
            ("e:old-create", before_java, ".signWith(SignatureAlgorithm.HS512, secret)"),
            ("e:utf8", after_java, "return secret.getBytes(StandardCharsets.UTF_8);"),
            ("e:exp", after_java, "long expireTime = System.currentTimeMillis() + expiration * 1000;"),
            ("e:new-create", after_java, "return JWTUtil.createToken(claims, getSigningKey());"),
            ("e:verify", after_java, "if (!JWTUtil.verify(token, getSigningKey()))"),
            ("e:parse", after_java, "return JWTUtil.parseToken(token).getPayloads();"),
            ("e:null-guard", after_java, "return username != null && username.equals(userDetails.getUsername()) && !isTokenExpired(token);"),
            ("e:exp-missing", after_java, "if (exp == null) {\n                return false;\n            }"),
            ("e:exp-cast", after_java, "long expTime = exp instanceof Long ? (Long) exp : ((Number) exp).longValue();"),
            ("e:exp-boundary", after_java, "return expTime < System.currentTimeMillis();"),
            ("e:created-long", after_java, "if (created instanceof Long)"),
            ("e:created-date", after_java, "} else if (created instanceof Date)"),
            ("e:created-null", after_java, "if (createdDate == null)"),
            ("e:refresh-boundary", after_java, "return refreshDate.after(createdDate) && refreshDate.before(DateUtil.offsetSecond(createdDate, time));"),
            ("e:return-old", after_java, "if (tokenRefreshJustBefore(token, 30 * 60)) {\n            return token;"),
            ("e:resign", after_java, "return generateToken(payload);"),
            ("e:comment", after_java, ' * {"alg": "HS512","typ": "JWT"}'),
        )
        for args in source_literals:
            literal_evidence(*args)

        entities = (
            EntityState("entity:base", "git-revision", PARENT, "e:comparison"),
            EntityState("entity:target", "git-revision", TARGET, "e:comparison"),
            EntityState("entity:root-pom", "source-unit", "pom.xml", "e:jjwt-version"),
            EntityState("entity:security-pom", "source-unit", "mall-security/pom.xml", "e:jjwt-security"),
            EntityState("entity:jwt-util", "source-unit", JAVA_PATH, "e:new-create"),
        )
        entity_map = {item.entity_id: item for item in entities}
        store = ValidationAuthorityStore("validation:jwt-run-002")
        entity_snapshot = store.publish(entities=entities)

        atomic_specs = (
            ("fact:version", "entity:root-pom", "DECLARES_VALUE_BINDING", "VALUE", "<jjwt.version>0.9.1</jjwt.version>", "e:jjwt-version", "JWT-N02-O01", PARENT),
            ("fact:root-jjwt", "entity:root-pom", "DECLARES_DEPENDENCY", "TARGET", "<artifactId>jjwt</artifactId>", "e:jjwt-root", "JWT-N02-O02", PARENT),
            ("fact:security-jjwt", "entity:security-pom", "DECLARES_DEPENDENCY", "TARGET", "<artifactId>jjwt</artifactId>", "e:jjwt-security", "JWT-N02-O03", PARENT),
            ("fact:old-create", "entity:jwt-util", "DECLARES_INVOCATION", "TARGET", "SignatureAlgorithm.HS512", "e:old-create", "JWT-N03-O01", PARENT),
            ("fact:utf8", "entity:jwt-util", "DECLARES_RETURN", "OUTPUT", "StandardCharsets.UTF_8", "e:utf8", "JWT-N03-O02", TARGET),
            ("fact:exp", "entity:jwt-util", "DECLARES_VALUE_BINDING", "VALUE", "expiration * 1000", "e:exp", "JWT-N03-O03", TARGET),
            ("fact:new-create", "entity:jwt-util", "DECLARES_INVOCATION", "TARGET", "JWTUtil.createToken", "e:new-create", "JWT-N03-O01", TARGET),
            ("fact:verify", "entity:jwt-util", "DECLARES_CONDITION", "CONDITION", "JWTUtil.verify", "e:verify", "JWT-N04-O01", TARGET),
            ("fact:parse", "entity:jwt-util", "DECLARES_RETURN", "OUTPUT", "JWTUtil.parseToken", "e:parse", "JWT-N04-O01", TARGET),
            ("fact:null-guard", "entity:jwt-util", "DECLARES_RETURN", "CONDITION", "username != null", "e:null-guard", "JWT-N04-O03", TARGET),
            ("fact:exp-missing", "entity:jwt-util", "DECLARES_CONDITION", "OUTPUT", "return false", "e:exp-missing", "JWT-N04-O04", TARGET),
            ("fact:exp-cast", "entity:jwt-util", "DECLARES_VALUE_BINDING", "TYPE", "((Number) exp).longValue()", "e:exp-cast", "JWT-N04-O05", TARGET),
            ("fact:exp-boundary", "entity:jwt-util", "DECLARES_RETURN", "CONDITION", "expTime < System.currentTimeMillis()", "e:exp-boundary", "JWT-N04-O06", TARGET),
            ("fact:created-long", "entity:jwt-util", "DECLARES_TYPE_BRANCH", "TYPE", "created instanceof Long", "e:created-long", "JWT-N05-O01", TARGET),
            ("fact:created-date", "entity:jwt-util", "DECLARES_TYPE_BRANCH", "TYPE", "created instanceof Date", "e:created-date", "JWT-N05-O01", TARGET),
            ("fact:created-null", "entity:jwt-util", "DECLARES_CONDITION", "CONDITION", "createdDate == null", "e:created-null", "JWT-N05-O02", TARGET),
            ("fact:refresh-boundary", "entity:jwt-util", "DECLARES_RETURN", "CONDITION", "refreshDate.after(createdDate)", "e:refresh-boundary", "JWT-N05-O03", TARGET),
            ("fact:return-old", "entity:jwt-util", "DECLARES_RETURN", "OUTPUT", "return token", "e:return-old", "JWT-N05-O04", TARGET),
            ("fact:resign", "entity:jwt-util", "DECLARES_RETURN", "OUTPUT", "generateToken(payload)", "e:resign", "JWT-N05-O04", TARGET),
            ("fact:comment", "entity:jwt-util", "DECLARES_COMMENT", "ALGORITHM", "HS512", "e:comment", "JWT-N06-O02", TARGET),
        )
        atomic_facts = []
        for fact_id, entity_id, predicate, role, term, evidence_id, obligation_id, revision in atomic_specs:
            fact = AtomicFact(fact_id, entity_id, predicate, ((role, term),), "CODE_COMMENT_DECLARES" if predicate == "DECLARES_COMMENT" else "CODE_DECLARES", evidence_id, revision, (obligation_id,))
            review_atomic_fact(fact, evidence_by_id[evidence_id], entity_map)
            atomic_facts.append(fact)

        closed_facts = (
            ClosedChangeSetFact("fact:changes", "entity:target", expected_changes, 3, TARGET, ("JWT-N01-O01", "JWT-N01-O02")),
            ClosedLiteralSelectionFact("fact:no-root-version", "entity:root-pom", "<jjwt.version>", (), TARGET, ("JWT-N02-O01",)),
            ClosedLiteralSelectionFact("fact:no-security-jjwt", "entity:security-pom", "<artifactId>jjwt</artifactId>", (), TARGET, ("JWT-N02-O03",)),
        )
        fact_snapshot = store.publish(facts=tuple(atomic_facts) + closed_facts)

        all_obligations = [ob for need in requirement.needs for ob in need.obligations]
        premise_by_obligation: dict[str, tuple[str, ...]] = {}
        for fact in tuple(atomic_facts) + closed_facts:
            for obligation_id in fact.related_obligation_ids:
                premise_by_obligation.setdefault(obligation_id, tuple())
                premise_by_obligation[obligation_id] += (fact.fact_id,)
        premise_by_obligation["JWT-N04-O02"] = ("fact:verify",)
        premise_by_obligation["JWT-N06-O01"] = ("fact:new-create",)

        aspect_by_need = {
            "JWT-N01": "REVISION_SCOPE",
            "JWT-N02": "DEPENDENCY",
            "JWT-N03": "API_CALL",
            "JWT-N04": "CONTROL_FLOW",
            "JWT-N05": "REFRESH_BEHAVIOR",
            "JWT-N06": "VALUE_SEMANTICS",
        }
        inferences = []
        for obligation in all_obligations:
            premises = premise_by_obligation[obligation.obligation_id]
            is_unknown = obligation.obligation_id == "JWT-N06-O01"
            inference = FormalInference(
                inference_id=f"inference:{obligation.obligation_id}",
                affected_entity_id="entity:target" if obligation.need_id == "JWT-N01" else "entity:jwt-util",
                aspect=aspect_by_need[obligation.need_id],
                relation="NOT_ESTABLISHED_WITHIN_BOUNDARY" if is_unknown else ("ENUMERATES_COMPLETE_SET" if obligation.need_id == "JWT-N01" else "TRANSFORMS_TO"),
                premise_ids=premises,
                context_revision=TARGET,
                related_obligation_ids=(obligation.obligation_id,),
                unknown_boundary="LIBRARY_DEFAULT" if is_unknown else None,
                missing_premises=("Hutool JWTUtil.createToken default algorithm contract",) if is_unknown else (),
            )
            review_inference(
                inference,
                premise_snapshot_id=fact_snapshot.snapshot_id,
                snapshot_id_by_knowledge_id={fact_id: fact_snapshot.snapshot_id for fact_id in fact_snapshot.facts},
                entities=entity_map,
            )
            inferences.append(inference)
        final_snapshot = store.publish(inferences=inferences)
        self.assertEqual((entity_snapshot.sequence, fact_snapshot.sequence, final_snapshot.sequence), (1, 2, 3))

        assessments = tuple(
            NeedAssessment(
                need.need_id,
                "SATISFIED",
                tuple(
                    ObligationSupport(ob.obligation_id, final_snapshot.snapshot_id, (f"inference:{ob.obligation_id}",))
                    for ob in need.obligations
                ),
            )
            for need in requirement.needs
        )
        joint = (JointConstraintAssessment("JWT-J01", "SATISFIED", NEED_IDS),)
        overall = assess_overall(requirement, final_snapshot, assessments, joint)
        self.assertEqual(overall, "SATISFIED")

        answer_text = {
            "JWT-N01-O01": f"目标提交 {TARGET} 的唯一父提交是 {PARENT}。",
            "JWT-N01-O02": f"完整变更集为 pom.xml、mall-security/pom.xml 与 {JAVA_PATH}，均为修改。",
            "JWT-N02-O01": "根 POM 删除 jjwt.version=0.9.1。",
            "JWT-N02-O02": "根 POM 删除 dependencyManagement 中的 io.jsonwebtoken:jjwt 管理声明。",
            "JWT-N02-O03": "mall-security 删除对 io.jsonwebtoken:jjwt 的直接依赖。",
            "JWT-N03-O01": "生成从 Jwts.builder/signWith(HS512) 改为 JWTUtil.createToken。",
            "JWT-N03-O02": "签名 Secret 显式转换为 UTF-8 字节。",
            "JWT-N03-O03": "exp 从旧 Date 设置改为 System.currentTimeMillis()+expiration*1000 的毫秒 long。",
            "JWT-N04-O01": "新实现先 JWTUtil.verify 验签，再 parseToken 读取 payload。",
            "JWT-N04-O02": "验签失败或解析异常时 getPayloadFromToken 返回 null。",
            "JWT-N04-O03": "validateToken 新增 username != null，缺失或无效用户名返回 false。",
            "JWT-N04-O04": "已验签 payload 缺少 exp 时 isTokenExpired 返回 false。",
            "JWT-N04-O05": "exp 非 Long 时按 Number 转 long；非 Number 等转换异常被视为过期。",
            "JWT-N04-O06": "过期条件是 expTime < 当前毫秒；恰好相等时该表达式仍判未过期。",
            "JWT-N05-O01": "created 仅显式接受 Long 或 Date。",
            "JWT-N05-O02": "created 为其他类型或缺失时 createdDate 为 null，因而不属于刚刷新。",
            "JWT-N05-O03": "30 分钟窗口严格要求 now>created 且 now<created+1800秒；两个等值边界都不在窗口内。",
            "JWT-N05-O04": "窗口内返回去掉 tokenHead 后的原 token；否则更新 created 并重新签发。",
            "JWT-N06-O01": "当前授权仓库没有 Hutool 默认签名算法的正式前提，不能断言新 token 的具体默认算法。",
            "JWT-N06-O02": "文件头 HS512 仍是注释声明，不能作为新 JWTUtil.createToken 行为的代码证据。",
        }
        claims = tuple(
            AnswerClaim(
                claim_id=f"claim:{ob.obligation_id}",
                need_id=ob.need_id,
                text=answer_text[ob.obligation_id],
                support=ObligationSupport(ob.obligation_id, final_snapshot.snapshot_id, (f"inference:{ob.obligation_id}",)),
            )
            for ob in all_obligations
        )
        candidate = AnswerCandidate(final_snapshot.snapshot_id, claims, "\n".join(item.text for item in claims))

        # From this point onward no Provider method is called: only the exact Snapshot is available.
        delivery_digest = authorize_answer(
            requirement,
            final_snapshot,
            overall,
            candidate,
            KnowledgeUseIsolationProof(),
        )
        self.assertEqual(len(delivery_digest), 64)

        oracle = tuple(
            DirectClaimOracleItem(
                claim_id=f"oracle:{ob.obligation_id}",
                semantic_key=ob.obligation_id,
                evidence_digest=digest(premise_by_obligation[ob.obligation_id]),
            )
            for ob in all_obligations
        )
        compare_claim_preservation(oracle, tuple(claim.support.obligation_id for claim in claims))
        self.assertEqual(len(claims), 20)
        self.assertIn("恰好相等", candidate.answer_body)
        self.assertIn("不能断言", candidate.answer_body)


if __name__ == "__main__":
    unittest.main()
