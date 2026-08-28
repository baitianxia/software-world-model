"""Standing human authority and exact Session derivation for public Source use.

The standing authority records the closed boundary decided by a human.  It is
not itself a Provider dispatch grant.  A trusted Application narrows it to one
exact product/Source/World-Model/route Session, after independently verifying
the local public Source mirror.  Per-Turn and per-call authorities then bind
this derived Session authority and remain one-use at their existing owners.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
import re
from typing import Sequence
from urllib.parse import urlsplit

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)


PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY_SCHEMA = (
    "PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1"
)
PUBLIC_SOURCE_MODEL_SESSION_AUTHORITY_SCHEMA = (
    "PUBLIC_SOURCE_MODEL_SESSION_AUTHORITY@1"
)
PUBLIC_SOURCE_EVALUATION_SINK = "EVALUATION_ONLY"
PUBLIC_SOURCE_LOOPBACK_ORIGIN = "http://127.0.0.1:8765/"
NO_DISPATCH_ADMISSION_POLICY = "NONE"

_GIT_OID = re.compile(r"^[0-9a-f]{40}$")
_SECRET_REFERENCE = re.compile(r"^env:[A-Z_][A-Z0-9_]*$")
_AUTHORITY_REF_PREFIXES = (
    "codex-user-message:",
    "local-user-message-utf8:",
)


@dataclass(frozen=True, slots=True)
class PublicSourceProviderScope:
    """Human-approved, qualification-independent Provider boundary."""

    ordinal: int
    route_role: str
    provider_type: str
    adapter_version: str
    endpoint: str
    model_ref: str
    expected_actual_model_fingerprint: str
    provider_configuration_fingerprint: Digest
    secret_reference: str
    disclosure_policy_ref: str
    dispatch_admission_policy_ref: str
    maximum_calls: int
    maximum_input_bytes: int
    maximum_output_tokens: int
    timeout_milliseconds: int
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        ordinal: int,
        route_role: str,
        provider_type: str,
        adapter_version: str,
        endpoint: str,
        model_ref: str,
        expected_actual_model_fingerprint: str,
        provider_configuration_fingerprint: Digest,
        secret_reference: str,
        disclosure_policy_ref: str,
        dispatch_admission_policy_ref: str,
        maximum_calls: int,
        maximum_input_bytes: int,
        maximum_output_tokens: int,
        timeout_milliseconds: int,
    ) -> "PublicSourceProviderScope":
        if type(ordinal) is not int or ordinal < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "public Source Provider scope ordinal is invalid",
            )
        route_role = _text(route_role, "Provider route role")
        if route_role not in {"PREFERRED", "PRIMARY", "FALLBACK"}:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "public Source Provider route role is invalid",
            )
        texts = tuple(
            _text(value, label)
            for value, label in (
                (provider_type, "Provider type"),
                (adapter_version, "Provider adapter version"),
                (endpoint, "Provider endpoint"),
                (model_ref, "Provider model reference"),
                (
                    expected_actual_model_fingerprint,
                    "Provider actual model fingerprint",
                ),
                (secret_reference, "Provider secret reference"),
                (disclosure_policy_ref, "Provider disclosure policy"),
                (
                    dispatch_admission_policy_ref,
                    "Provider dispatch admission policy",
                ),
            )
        )
        parsed = urlsplit(texts[2])
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "public Source Provider endpoint must be exact credential-free HTTPS",
            )
        if not _SECRET_REFERENCE.fullmatch(texts[5]):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "public Source Provider scope requires an environment Secret Reference",
            )
        if not isinstance(provider_configuration_fingerprint, Digest):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "public Source Provider scope requires its configuration fingerprint",
            )
        for value, label, maximum in (
            (maximum_calls, "call", 128),
            (maximum_input_bytes, "input-byte", 8_388_608),
            (maximum_output_tokens, "output-token", 16_384),
            (timeout_milliseconds, "timeout", 900_000),
        ):
            if type(value) is not int or not 1 <= value <= maximum:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    f"public Source Provider {label} bound is invalid",
                )
        core = {
            "schema": "PUBLIC_SOURCE_PROVIDER_SCOPE@1",
            "ordinal": ordinal,
            "route_role": route_role,
            "provider_type": texts[0],
            "adapter_version": texts[1],
            "endpoint": texts[2],
            "model_ref": texts[3],
            "expected_actual_model_fingerprint": texts[4],
            "provider_configuration_fingerprint": (
                provider_configuration_fingerprint.value
            ),
            "secret_reference": texts[5],
            "disclosure_policy_ref": texts[6],
            "dispatch_admission_policy_ref": texts[7],
            "maximum_calls": maximum_calls,
            "maximum_input_bytes": maximum_input_bytes,
            "maximum_output_tokens": maximum_output_tokens,
            "timeout_milliseconds": timeout_milliseconds,
            "request_retry_allowed": False,
        }
        return cls(
            ordinal=ordinal,
            route_role=route_role,
            provider_type=texts[0],
            adapter_version=texts[1],
            endpoint=texts[2],
            model_ref=texts[3],
            expected_actual_model_fingerprint=texts[4],
            provider_configuration_fingerprint=(
                provider_configuration_fingerprint
            ),
            secret_reference=texts[5],
            disclosure_policy_ref=texts[6],
            dispatch_admission_policy_ref=texts[7],
            maximum_calls=maximum_calls,
            maximum_input_bytes=maximum_input_bytes,
            maximum_output_tokens=maximum_output_tokens,
            timeout_milliseconds=timeout_milliseconds,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class PublicSourceModelStandingAuthority:
    """One closed human decision reusable across exact machine receipts."""

    schema: str
    status: str
    authority_ref: str
    human_authority_ref: str
    human_authority_digest: Digest
    authority_evidence_refs: tuple[str, ...]
    purpose: str
    source_authority_ref: str
    canonical_source_upstream: str
    source_license: str
    source_license_path: str
    source_revision_policy: str
    source_revision: str
    source_tree: str
    source_profile_ref: str
    source_allowlist: tuple[str, ...]
    excluded_source_paths: tuple[str, ...]
    route_policy_ref: str
    provider_scopes: tuple[PublicSourceProviderScope, ...]
    maximum_turns: int
    maximum_dispatches_per_turn: int
    maximum_total_dispatches_per_provider: int
    maximum_input_tokens: int
    maximum_output_tokens: int
    maximum_duration_seconds: int
    authorized_at: datetime
    expires_at: datetime
    sink: str
    loopback_origin: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        authority_ref: str,
        human_authority_ref: str,
        human_authority_digest: Digest,
        authority_evidence_refs: Sequence[str],
        purpose: str,
        source_authority_ref: str,
        canonical_source_upstream: str,
        source_license: str,
        source_license_path: str,
        source_revision_policy: str,
        source_revision: str,
        source_tree: str,
        source_profile_ref: str,
        source_allowlist: Sequence[str],
        excluded_source_paths: Sequence[str],
        route_policy_ref: str,
        provider_scopes: Sequence[PublicSourceProviderScope],
        maximum_turns: int,
        maximum_dispatches_per_turn: int,
        maximum_total_dispatches_per_provider: int,
        maximum_input_tokens: int,
        maximum_output_tokens: int,
        maximum_duration_seconds: int,
        authorized_at: datetime,
        expires_at: datetime,
        sink: str = PUBLIC_SOURCE_EVALUATION_SINK,
        loopback_origin: str = PUBLIC_SOURCE_LOOPBACK_ORIGIN,
    ) -> "PublicSourceModelStandingAuthority":
        authority_ref = _text(authority_ref, "standing authority reference")
        human_authority_ref = _text(
            human_authority_ref, "standing human authority reference"
        )
        if (
            not isinstance(human_authority_digest, Digest)
            or not human_authority_ref.endswith(human_authority_digest.value)
            or not human_authority_ref.startswith(_AUTHORITY_REF_PREFIXES)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "standing authority does not bind its human authority evidence",
            )
        evidence_refs = _unique_texts(
            authority_evidence_refs, "standing authority evidence reference"
        )
        purpose = _text(purpose, "standing authority purpose")
        source_authority_ref = _text(
            source_authority_ref, "public Source authority reference"
        )
        upstream = _exact_public_upstream(canonical_source_upstream)
        source_license = _text(source_license, "public Source license")
        license_path = _source_path(source_license_path, "Source license path")
        source_revision_policy = _text(
            source_revision_policy, "Source revision policy"
        )
        source_revision = _git_oid(source_revision, "Source revision")
        source_tree = _git_oid(source_tree, "Source tree")
        source_profile_ref = _text(source_profile_ref, "Source Profile reference")
        allowlist = _unique_source_paths(source_allowlist, "Source allowlist path")
        exclusions = _unique_source_paths(
            excluded_source_paths, "excluded Source path"
        )
        if any(
            _paths_overlap(allowed, excluded)
            for allowed in allowlist
            for excluded in exclusions
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "standing Source allowlist overlaps an excluded path",
            )
        route_policy_ref = _text(route_policy_ref, "Provider route policy")
        scopes = tuple(provider_scopes)
        if (
            not scopes
            or any(not isinstance(item, PublicSourceProviderScope) for item in scopes)
            or tuple(item.ordinal for item in scopes)
            != tuple(range(1, len(scopes) + 1))
            or scopes[0].route_role not in {"PREFERRED", "PRIMARY"}
            or any(item.route_role != "FALLBACK" for item in scopes[1:])
            or len({item.digest for item in scopes}) != len(scopes)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "standing authority Provider scopes are not one ordered route",
            )
        for value, label in (
            (maximum_turns, "Turn"),
            (maximum_dispatches_per_turn, "per-Turn dispatch"),
            (
                maximum_total_dispatches_per_provider,
                "per-Provider total dispatch",
            ),
            (maximum_input_tokens, "input-token"),
            (maximum_output_tokens, "output-token"),
            (maximum_duration_seconds, "duration"),
        ):
            if type(value) is not int or value < 1:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    f"standing authority {label} bound is invalid",
                )
        if (
            maximum_turns > 128
            or maximum_dispatches_per_turn
            > min(item.maximum_calls for item in scopes)
            or maximum_total_dispatches_per_provider
            > maximum_turns * maximum_dispatches_per_turn
            or maximum_total_dispatches_per_provider
            > min(item.maximum_calls for item in scopes)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "standing authority dispatch bounds exceed the approved route",
            )
        issued = _aware_utc(authorized_at, "standing authority time")
        expiry = _aware_utc(expires_at, "standing authority expiration")
        if issued >= expiry:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "standing authority time window is invalid",
            )
        if sink != PUBLIC_SOURCE_EVALUATION_SINK or loopback_origin != PUBLIC_SOURCE_LOOPBACK_ORIGIN:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "public Source standing authority is restricted to loopback evaluation",
            )
        core = {
            "schema": PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY_SCHEMA,
            "status": "AUTHORIZED",
            "authority_ref": authority_ref,
            "human_authority_ref": human_authority_ref,
            "human_authority_digest": human_authority_digest.value,
            "authority_evidence_refs": evidence_refs,
            "purpose": purpose,
            "source_authority_ref": source_authority_ref,
            "canonical_source_upstream": upstream,
            "source_license": source_license,
            "source_license_path": license_path,
            "source_revision_policy": source_revision_policy,
            "source_revision": source_revision,
            "source_tree": source_tree,
            "source_profile_ref": source_profile_ref,
            "source_allowlist": allowlist,
            "excluded_source_paths": exclusions,
            "route_policy_ref": route_policy_ref,
            "provider_scope_digests": tuple(item.digest.value for item in scopes),
            "maximum_turns": maximum_turns,
            "maximum_dispatches_per_turn": maximum_dispatches_per_turn,
            "maximum_total_dispatches_per_provider": (
                maximum_total_dispatches_per_provider
            ),
            "maximum_input_tokens": maximum_input_tokens,
            "maximum_output_tokens": maximum_output_tokens,
            "maximum_duration_seconds": maximum_duration_seconds,
            "authorized_at": _time(issued),
            "expires_at": _time(expiry),
            "sink": sink,
            "loopback_origin": loopback_origin,
            "external_write_allowed": False,
            "request_retry_allowed": False,
            "production_activation": "NOT_EXECUTED",
        }
        return cls(
            schema=PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY_SCHEMA,
            status="AUTHORIZED",
            authority_ref=authority_ref,
            human_authority_ref=human_authority_ref,
            human_authority_digest=human_authority_digest,
            authority_evidence_refs=evidence_refs,
            purpose=purpose,
            source_authority_ref=source_authority_ref,
            canonical_source_upstream=upstream,
            source_license=source_license,
            source_license_path=license_path,
            source_revision_policy=source_revision_policy,
            source_revision=source_revision,
            source_tree=source_tree,
            source_profile_ref=source_profile_ref,
            source_allowlist=allowlist,
            excluded_source_paths=exclusions,
            route_policy_ref=route_policy_ref,
            provider_scopes=scopes,
            maximum_turns=maximum_turns,
            maximum_dispatches_per_turn=maximum_dispatches_per_turn,
            maximum_total_dispatches_per_provider=(
                maximum_total_dispatches_per_provider
            ),
            maximum_input_tokens=maximum_input_tokens,
            maximum_output_tokens=maximum_output_tokens,
            maximum_duration_seconds=maximum_duration_seconds,
            authorized_at=issued,
            expires_at=expiry,
            sink=sink,
            loopback_origin=loopback_origin,
            digest=digest_of(core),
        )

    def require_current(self, at: datetime) -> None:
        expected = PublicSourceModelStandingAuthority.create(
            authority_ref=self.authority_ref,
            human_authority_ref=self.human_authority_ref,
            human_authority_digest=self.human_authority_digest,
            authority_evidence_refs=self.authority_evidence_refs,
            purpose=self.purpose,
            source_authority_ref=self.source_authority_ref,
            canonical_source_upstream=self.canonical_source_upstream,
            source_license=self.source_license,
            source_license_path=self.source_license_path,
            source_revision_policy=self.source_revision_policy,
            source_revision=self.source_revision,
            source_tree=self.source_tree,
            source_profile_ref=self.source_profile_ref,
            source_allowlist=self.source_allowlist,
            excluded_source_paths=self.excluded_source_paths,
            route_policy_ref=self.route_policy_ref,
            provider_scopes=self.provider_scopes,
            maximum_turns=self.maximum_turns,
            maximum_dispatches_per_turn=self.maximum_dispatches_per_turn,
            maximum_total_dispatches_per_provider=(
                self.maximum_total_dispatches_per_provider
            ),
            maximum_input_tokens=self.maximum_input_tokens,
            maximum_output_tokens=self.maximum_output_tokens,
            maximum_duration_seconds=self.maximum_duration_seconds,
            authorized_at=self.authorized_at,
            expires_at=self.expires_at,
            sink=self.sink,
            loopback_origin=self.loopback_origin,
        )
        if self != expected:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "public Source standing authority is inconsistent",
            )
        current = _aware_utc(at, "standing authority current time")
        if current < self.authorized_at or current >= self.expires_at:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "public Source standing authority is not current",
            )


@dataclass(frozen=True, slots=True)
class PublicSourceModelSessionAuthority:
    """Exact machine-derived child of one public Source standing authority."""

    schema: str
    status: str
    session_ref: str
    parent_authority_digest: Digest
    product_revision: str
    product_tree: str
    product_candidate_digest: Digest
    source_repository_ref: Digest
    canonical_source_upstream: str
    source_revision: str
    source_tree: str
    source_profile_ref: str
    source_profile_digest: Digest
    repository_id: StableId
    binding_id: StableId
    world_model_read_authority_digest: Digest
    chat_binding_digest: Digest
    provider_route_ref: str
    provider_configuration_digests: tuple[Digest, ...]
    provider_qualification_refs: tuple[str, ...]
    authorized_at: datetime
    expires_at: datetime
    derived_at: datetime
    digest: Digest

    @classmethod
    def derive(
        cls,
        *,
        standing_authority: PublicSourceModelStandingAuthority,
        session_ref: str,
        product_revision: str,
        product_tree: str,
        product_candidate_digest: Digest,
        source_repository_ref: Digest,
        observed_source_upstream: str,
        observed_source_revision: str,
        observed_source_tree: str,
        source_clean: bool,
        license_object_type: str,
        source_profile_ref: str,
        source_profile_digest: Digest,
        source_allowlist: Sequence[str],
        excluded_source_paths: Sequence[str],
        repository_id: StableId,
        binding_id: StableId,
        world_model_read_authority_digest: Digest,
        chat_binding_digest: Digest,
        provider_route_ref: str,
        provider_scopes: Sequence[PublicSourceProviderScope],
        provider_configuration_digests: Sequence[Digest],
        provider_qualification_refs: Sequence[str],
        maximum_turns: int,
        maximum_dispatches_per_turn: int,
        maximum_total_dispatches_per_provider: int,
        maximum_input_tokens: int,
        maximum_output_tokens: int,
        maximum_duration_seconds: int,
        authorized_at: datetime,
        expires_at: datetime,
        derived_at: datetime,
    ) -> "PublicSourceModelSessionAuthority":
        if not isinstance(standing_authority, PublicSourceModelStandingAuthority):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "public Source Session derivation requires its standing authority",
            )
        current = _aware_utc(derived_at, "public Source Session derivation time")
        standing_authority.require_current(current)
        issued = _aware_utc(authorized_at, "public Source Session authority time")
        expiry = _aware_utc(expires_at, "public Source Session authority expiration")
        session_ref = _text(session_ref, "public Source Session reference")
        product_revision = _git_oid(product_revision, "product revision")
        product_tree = _git_oid(product_tree, "product tree")
        upstream = _exact_public_upstream(observed_source_upstream)
        source_revision = _git_oid(observed_source_revision, "Source revision")
        source_tree = _git_oid(observed_source_tree, "Source tree")
        profile_ref = _text(source_profile_ref, "Source Profile reference")
        allowlist = _unique_source_paths(source_allowlist, "Source allowlist path")
        exclusions = _unique_source_paths(
            excluded_source_paths, "excluded Source path"
        )
        provider_route_ref = _text(provider_route_ref, "Provider route reference")
        scopes = tuple(provider_scopes)
        configuration_digests = tuple(provider_configuration_digests)
        qualification_refs = _unique_texts(
            provider_qualification_refs, "Provider qualification reference"
        )
        if (
            source_clean is not True
            or license_object_type != "blob"
            or upstream != standing_authority.canonical_source_upstream
            or source_revision != standing_authority.source_revision
            or source_tree != standing_authority.source_tree
            or profile_ref != standing_authority.source_profile_ref
            or allowlist != standing_authority.source_allowlist
            or exclusions != standing_authority.excluded_source_paths
            or scopes != standing_authority.provider_scopes
            or maximum_turns > standing_authority.maximum_turns
            or maximum_dispatches_per_turn
            > standing_authority.maximum_dispatches_per_turn
            or maximum_total_dispatches_per_provider
            > standing_authority.maximum_total_dispatches_per_provider
            or maximum_input_tokens > standing_authority.maximum_input_tokens
            or maximum_output_tokens > standing_authority.maximum_output_tokens
            or maximum_duration_seconds
            > standing_authority.maximum_duration_seconds
            or issued < standing_authority.authorized_at
            or expiry > standing_authority.expires_at
            or issued >= expiry
            or current < issued
            or current >= expiry
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "public Source Session derivation exceeds or drifts from standing scope",
            )
        if (
            not isinstance(product_candidate_digest, Digest)
            or not isinstance(source_repository_ref, Digest)
            or not isinstance(source_profile_digest, Digest)
            or not isinstance(repository_id, StableId)
            or not isinstance(binding_id, StableId)
            or not isinstance(world_model_read_authority_digest, Digest)
            or not isinstance(chat_binding_digest, Digest)
            or len(configuration_digests) != len(scopes)
            or len(qualification_refs) != len(scopes)
            or any(not isinstance(item, Digest) for item in configuration_digests)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "public Source Session derivation identities are incomplete",
            )
        core = {
            "schema": PUBLIC_SOURCE_MODEL_SESSION_AUTHORITY_SCHEMA,
            "status": "AUTHORIZED",
            "session_ref": session_ref,
            "parent_authority_digest": standing_authority.digest.value,
            "product_revision": product_revision,
            "product_tree": product_tree,
            "product_candidate_digest": product_candidate_digest.value,
            "source_repository_ref": source_repository_ref.value,
            "canonical_source_upstream": upstream,
            "source_revision": source_revision,
            "source_tree": source_tree,
            "source_profile_ref": profile_ref,
            "source_profile_digest": source_profile_digest.value,
            "source_allowlist": allowlist,
            "excluded_source_paths": exclusions,
            "repository_id": repository_id.value,
            "binding_id": binding_id.value,
            "world_model_read_authority_digest": (
                world_model_read_authority_digest.value
            ),
            "chat_binding_digest": chat_binding_digest.value,
            "provider_route_ref": provider_route_ref,
            "provider_scope_digests": tuple(item.digest.value for item in scopes),
            "provider_configuration_digests": tuple(
                item.value for item in configuration_digests
            ),
            "provider_qualification_refs": qualification_refs,
            "maximum_turns": maximum_turns,
            "maximum_dispatches_per_turn": maximum_dispatches_per_turn,
            "maximum_total_dispatches_per_provider": (
                maximum_total_dispatches_per_provider
            ),
            "maximum_input_tokens": maximum_input_tokens,
            "maximum_output_tokens": maximum_output_tokens,
            "maximum_duration_seconds": maximum_duration_seconds,
            "authorized_at": _time(issued),
            "expires_at": _time(expiry),
            "derived_at": _time(current),
            "human_approval_request_count": 0,
            "source_disclosure_count_at_derivation": 0,
            "credential_resolution_count_at_derivation": 0,
            "provider_network_count_at_derivation": 0,
            "external_write_allowed": False,
            "request_retry_allowed": False,
            "production_activation": "NOT_EXECUTED",
        }
        return cls(
            schema=PUBLIC_SOURCE_MODEL_SESSION_AUTHORITY_SCHEMA,
            status="AUTHORIZED",
            session_ref=session_ref,
            parent_authority_digest=standing_authority.digest,
            product_revision=product_revision,
            product_tree=product_tree,
            product_candidate_digest=product_candidate_digest,
            source_repository_ref=source_repository_ref,
            canonical_source_upstream=upstream,
            source_revision=source_revision,
            source_tree=source_tree,
            source_profile_ref=profile_ref,
            source_profile_digest=source_profile_digest,
            repository_id=repository_id,
            binding_id=binding_id,
            world_model_read_authority_digest=world_model_read_authority_digest,
            chat_binding_digest=chat_binding_digest,
            provider_route_ref=provider_route_ref,
            provider_configuration_digests=configuration_digests,
            provider_qualification_refs=qualification_refs,
            authorized_at=issued,
            expires_at=expiry,
            derived_at=current,
            digest=digest_of(core),
        )

    def public_status(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "status": self.status,
            "parent_authority_digest": self.parent_authority_digest.value,
            "session_authority_digest": self.digest.value,
            "source_revision": self.source_revision,
            "source_tree": self.source_tree,
            "provider_configuration_digests": tuple(
                item.value for item in self.provider_configuration_digests
            ),
            "human_approval_request_count": 0,
            "production_activation": "NOT_EXECUTED",
        }


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    return value


def _unique_texts(values: Sequence[str], label: str) -> tuple[str, ...]:
    result = tuple(_text(value, label) for value in values)
    if not result or len(set(result)) != len(result):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label}s are invalid")
    return result


def _git_oid(value: str, label: str) -> str:
    value = _text(value, label).casefold()
    if not _GIT_OID.fullmatch(value):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    return value


def _exact_public_upstream(value: str) -> str:
    value = _text(value, "canonical public Source upstream")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not parsed.path
        or parsed.path == "/"
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "canonical public Source upstream must be exact credential-free HTTPS",
        )
    return value


def _source_path(value: str, label: str) -> str:
    value = _text(value, label)
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value.endswith("/")
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    return path.as_posix()


def _unique_source_paths(values: Sequence[str], label: str) -> tuple[str, ...]:
    result = tuple(sorted(_source_path(value, label) for value in values))
    if not result or len(set(result)) != len(result):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label}s are invalid")
    return result


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = PurePosixPath(left).parts
    right_parts = PurePosixPath(right).parts
    length = min(len(left_parts), len(right_parts))
    return left_parts[:length] == right_parts[:length]


def _aware_utc(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    return value.astimezone(timezone.utc)


def _time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "NO_DISPATCH_ADMISSION_POLICY",
    "PUBLIC_SOURCE_EVALUATION_SINK",
    "PUBLIC_SOURCE_LOOPBACK_ORIGIN",
    "PUBLIC_SOURCE_MODEL_SESSION_AUTHORITY_SCHEMA",
    "PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY_SCHEMA",
    "PublicSourceModelSessionAuthority",
    "PublicSourceModelStandingAuthority",
    "PublicSourceProviderScope",
]
