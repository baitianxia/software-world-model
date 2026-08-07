"""Local Git data-source configuration normalization (no repository reads)."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Mapping

from software_world_model.cross_cutting import DomainError, ErrorCode

from .configuration import (
    NormalizedDataSource,
    NormalizedSelection,
    canonical_fields,
)


class LocalGitConfigurationProvider:
    provider_type = "LOCAL_GIT"
    contract_version = "0.1.0"
    connector_tools = (
        "local-git.list@1",
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
        if not normalized:
            raise DomainError(ErrorCode.SELECTOR_INVALID, "Local Git selector cannot be empty")
        return NormalizedSelection(
            selector=canonical_fields(normalized, label="Local Git selector"),
            context_constraint=canonical_fields(
                context_constraint, label="Local Git context constraint"
            ),
        )


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
