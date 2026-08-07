# Repository guide for coding agents

This repository separates current system truth from project/change history. Do not
read every document before acting.

## Required reading order

1. Read `docs/project/current.md` to determine whether an iteration and development
   slice are authorized.
2. Read the selected iteration's `proposal.md`, `manifest.yaml`,
   `readiness-review.md`, active file under `development-design/`, and
   `verification-matrix.md`.
3. Follow only the referenced documents under `docs/system/`.
4. Inspect the relevant code and tests. Code and tests own local implementation
   details; system documents own cross-module semantics and invariants.

`docs/project/roadmap/` is planning input, not coding authorization.
`docs/archive/` is historical evidence, not current authority.
`docs/_generated/` is a derived index, not normative content.
When no active slice is named, do not edit product code or create an iteration from
these documents alone; a user's explicit request is still required.

## Documentation write-back

Implementation is expected to discover new information. Record a finding under the
active iteration's `findings/` when it may affect a system boundary, contract,
quality rule, iteration decision, or future work. Follow
`docs/project/governance/implementation-feedback-policy.md` to classify it.
If no iteration is active, preserve the evidence and follow that policy's bootstrap
rule instead of appending to a completed iteration.

Before an iteration can be accepted, every finding must be dispositioned to exactly
one of these destinations:

- a current document in `docs/system/` (and an ADR when the architectural choice
  changes);
- the active iteration's development design or project decision;
- a planning-only candidate in `docs/project/roadmap/`;
- code and tests only, with the reason documented in the finding;
- rejected, with evidence and rationale.

Do not use a result document to silently redefine the system. Update the owning
system document in the same change when implementation evidence changes system
truth.

## Validation

Run the documentation check after changing current documents:

```bash
python3 scripts/docs.py check
```

Run the smallest relevant code test set, then the full suite when a cross-module
contract or invariant changes.
