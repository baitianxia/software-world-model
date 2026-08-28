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
own diff. Product development may span multiple ordinary commits inside one active
long-running action as long as each diff stays within the base action's paths,
permissions, and locks. A first operable complete browser chain must be handed to
the user immediately with `requires_result=false`; that delivery neither seals a
Result nor moves the plan cursor. A sealed Result plus base-validated machine
evidence is required only for the final direction handoff (or after one
evidence-backed general repair still fails) when moving the plan cursor, not for
every commit, failed attempt, test, provider dispatch, or first browser delivery.

The trusted-parent check is the first executable CI gate. On pull requests it
must validate the pull-request head SHA, not a synthetic merge SHA. Every
plan-controlled commit must have exactly one parent and that parent must be the
previous trusted node; candidate Python, tests, documentation tooling, or other
repository code must not run before this check succeeds.

An action verifier is executable evidence, not a self-reported Result field. Freeze
the smallest self-contained runner needed for the final direction handoff before the
Result it verifies; the trusted-base gate must replay that runner against the exact
evidence bytes. A candidate runner cannot verify itself. Do not build per-failure
actions, Activation clocks, whole-Manifest digest schemes, or verifier state
machines that duplicate the product workflow.

Each real external dispatch still requires a one-use runtime receipt tied to active
standing authority, exact source/product/session/route/disclosure/budget, and the
Secret Reference. First experience development may run only targeted impact,
startup, safety, and failure-truthfulness tests; full regression, hidden inputs,
cross-project validation, hardening, and Production remain locked until the user
continues after the quality comparison. A direction receipt records the user's
decision only: `CONTINUE` makes later work eligible but does not itself unlock it.
Unlocking requires a subsequent PDR, explicit user authorization, and trusted-parent
cutover; a local message digest is an evidence reference, not platform-authenticated
authority. Ordinary answer failures stay in the same
action: attribute the earliest divergence before one general repair and targeted
recheck.

Local gates do not establish an unbypassable trust boundary against a malicious
repository administrator. Do not claim that property until the remote host has
an immutable required workflow/ruleset and the required user/provider evidence
has independently authenticated signatures.

Run the smallest relevant targeted, startup, and safety tests during first-experience
development. Run the full suite after the experience and quality decision unlocks
hardening, and before final acceptance; do not use it to delay the first complete
browser experience.
