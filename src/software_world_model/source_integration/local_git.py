"""Local Git data-source configuration normalization (no repository reads)."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
from typing import Mapping

from software_world_model.cross_cutting import DomainError, ErrorCode

from .configuration import (
    NormalizedDataSource,
    NormalizedSelection,
    canonical_fields,
)


_FULL_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class LocalGitConfigurationProvider:
    provider_type = "LOCAL_GIT"
    contract_version = "0.1.0"
    connector_tools = (
        "local-git.list@1",
        "local-git.tree@1",
        "local-git.search@1",
        "local-git.read@1",
        "local-git.compare@1",
    )

    def normalize_data_source(
        self,
        *,
        identity_domain: str,
        source_target: str,
        provider_configuration: Mapping[str, str],
        secret_reference: str | None,
    ) -> NormalizedDataSource:
        if not identity_domain or identity_domain != identity_domain.strip():
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "identity domain must be non-empty")
        if not source_target or source_target != source_target.strip():
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "source target must be non-empty")
        target = Path(source_target).expanduser()
        if not target.is_absolute():
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "Local Git source target must be an absolute path"
            )
        canonical_target = str(target.resolve(strict=False))
        return NormalizedDataSource(
            identity_strategy_version="local-git-realpath@1",
            identity_domain=identity_domain.casefold(),
            canonical_source_target=canonical_target,
            provider_configuration=canonical_fields(
                provider_configuration,
                label="Local Git provider configuration",
                reject_credentials=True,
            ),
            secret_reference=secret_reference,
        )

    def normalize_selection(
        self,
        *,
        selector: Mapping[str, str],
        context_constraint: Mapping[str, str],
    ) -> NormalizedSelection:
        allowed = {"paths", "commit", "comparison_base", "comparison_head"}
        unknown = set(selector) - allowed
        if unknown:
            raise DomainError(
                ErrorCode.SELECTOR_INVALID,
                "Local Git selector contains unsupported fields",
                {"field": sorted(unknown)[0]},
            )
        normalized = dict(selector)
        if "paths" in normalized:
            paths = tuple(
                sorted({_normalize_relative_path(item) for item in normalized["paths"].split(",")})
            )
            if not paths:
                raise DomainError(ErrorCode.SELECTOR_INVALID, "paths selector cannot be empty")
            normalized["paths"] = ",".join(paths)
        pinned_commit = normalized.get("commit")
        comparison_base = normalized.get("comparison_base")
        comparison_head = normalized.get("comparison_head")
        if pinned_commit is not None:
            normalized["commit"] = _normalize_oid(pinned_commit, "commit")
        if (comparison_base is None) != (comparison_head is None):
            raise DomainError(
                ErrorCode.SELECTOR_INVALID,
                "comparison_base and comparison_head must be supplied together",
            )
        if comparison_base is not None and comparison_head is not None:
            normalized["comparison_base"] = _normalize_oid(
                comparison_base, "comparison_base"
            )
            normalized["comparison_head"] = _normalize_oid(
                comparison_head, "comparison_head"
            )
        if pinned_commit is not None and comparison_base is not None:
            raise DomainError(
                ErrorCode.SELECTOR_INVALID,
                "commit and comparison selectors are mutually exclusive",
            )
        if not normalized:
            raise DomainError(ErrorCode.SELECTOR_INVALID, "Local Git selector cannot be empty")
        return NormalizedSelection(
            selector=canonical_fields(normalized, label="Local Git selector"),
            context_constraint=canonical_fields(
                context_constraint, label="Local Git context constraint"
            ),
        )


def _normalize_oid(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise DomainError(
            ErrorCode.SELECTOR_INVALID,
            f"Local Git {field} selector must be a full object ID",
        )
    normalized = value.casefold()
    if not _FULL_OID.fullmatch(normalized):
        raise DomainError(
            ErrorCode.SELECTOR_INVALID,
            f"Local Git {field} selector must be a full object ID",
        )
    return normalized


def _normalize_relative_path(value: str) -> str:
    clean = value.strip().replace("\\", "/")
    path = PurePosixPath(clean)
    if not clean or path.is_absolute() or ".." in path.parts:
        raise DomainError(
            ErrorCode.SELECTOR_INVALID,
            "Local Git selected paths must be repository-relative and cannot traverse parents",
        )
    normalized = path.as_posix().rstrip("/")
    return normalized or "."
