from __future__ import annotations

from swm_demo.artifact_contract import ArtifactRequest
from swm_demo.knowledge_contract import KnowledgeBuildTarget


def mall_full_artifact_request() -> ArtifactRequest:
    """Fixed source boundary from Architecture_Validation_Baseline.md."""

    return ArtifactRequest(
        build_profile="full-validation",
        include_globs=(
            "README.md",
            "**/*.md",
            "pom.xml",
            "**/pom.xml",
            "**/*.java",
            "**/*.xml",
            "**/*.yml",
            "**/*.yaml",
            "**/*.properties",
        ),
        git_commit_ids=(
            "0504e86b1f1b6f1b8aa6a734d37a90fb67346be7",
            "dd6569c",
        ),
        derive_java_ast=True,
    )


def mall_full_knowledge_target() -> KnowledgeBuildTarget:
    """Fixed questions from the validation baseline; contains no answers."""

    implementation = (
        "com.macro.mall.portal.service.impl."
        "OmsPortalOrderServiceImpl"
    )
    return KnowledgeBuildTarget(
        behavior_methods=(
            (f"{implementation}#generateOrder", "B-01 创建订单"),
            (f"{implementation}#cancelTimeOutOrder", "B-02 超时取消"),
            (f"{implementation}#cancelOrder", "B-02 用户取消"),
        ),
        business_constraint_methods=(
            (f"{implementation}#generateOrder", "下单"),
        ),
        capability_modules=("*",),
        history_commits=("0504e86", "dd6569c"),
        required_inference_types=(
            "BEHAVIOR_FLOW",
            "BUSINESS_CAPABILITY",
            "BUSINESS_CONSTRAINT",
            "HISTORY_IMPACT",
        ),
    )
