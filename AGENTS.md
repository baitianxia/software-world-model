# Repository guide for coding agents

This repository separates current system truth from project/change history. Do not
read every document before acting.

## Required reading order

1. Read `docs/project/current.md` to determine whether an iteration, development
   slice, plan revision, and unique next action are authorized.
2. Read the selected iteration's `proposal.md`, `manifest.yaml`,
   `readiness-review.md`, active file under `development-design/`, and
   `verification-matrix.md`.
3. Follow only the referenced documents under `docs/system/`.
4. Confirm the active Manifest action permits the exact files, coding, external
   execution, and Result you intend to change. Its action-level allowlist overrides
   the broader Slice `code` and `tests` lists.
5. Inspect the relevant code and tests. Code and tests own local implementation
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

Before development, validate the current plan snapshot; before handoff or merge,
validate the candidate diff against the trusted base plan:

```bash
python3 scripts/plan_gate.py snapshot
python3 scripts/plan_gate.py diff --base <trusted-base-ref>
```

The current local repository must also have `.githooks/plan-pre-commit` installed
as `.git/hooks/pre-commit`. It validates the staged tree with the gate from trusted
`HEAD`, not the candidate worktree. The remote required workflow remains mandatory;
a local hook is an automatic guardrail, not an administrator-proof trust root.

Do not change product code, run an external provider, or advance an action when the
base action does not explicitly allow it. A candidate Manifest cannot authorize its
own diff. Only a sealed Result plus its digest-bound machine evidence, validated by
the trusted base gate against a pre-registered transition, can move the cursor.

The trusted-parent check is the first executable CI gate. On pull requests it
must validate the pull-request head SHA, not a synthetic merge SHA. Every
plan-controlled commit must have exactly one parent and that parent must be the
previous trusted node; candidate Python, tests, documentation tooling, or other
repository code must not run before this check succeeds.

An action verifier is executable evidence, not a self-reported Result field.
The action runner identity must include exactly one `*/value_gate/runner.py`.
Commit and freeze that self-contained runner before committing the Result: the
trusted-base gate copies the base runner to an isolated temporary directory and
executes it with `python -I -S <runner> verify-plan-evidence`, passing the exact
evidence JSON bytes on stdin. The runner must emit only the registered JSON
verification fields on stdout; the gate binds those fields to the evidence and
Result. A runner and the Result it verifies cannot be introduced in the same
commit. Evidence digests cover raw blob bytes, so line-ending changes, including
CRLF versus LF, are material and must not be normalized.

For an external action to report `PASS`, `external_model_call_count`,
`provider_dispatch_count`, and `http_dispatch_count` must each be positive and
`full_regression_run_count` must be zero. A prerequisite Case produced by the
registered action graph is satisfied only by its digest-bound Result receipt;
textual `PASS` in the Verification Matrix is not sufficient. A plan revision
must remain in the same Iteration, use a strictly higher PDR number, depend on
the base governance action's sealed Result, and use a decision reference that
has never appeared in any trusted-base document or authorization field.

Local gates do not establish an unbypassable trust boundary against a malicious
repository administrator. Do not claim that property until the remote host has
an immutable required workflow/ruleset and the required user/provider evidence
has independently authenticated signatures.

Run the smallest relevant code test set, then the full suite when a cross-module
contract or invariant changes.
