# Repository guide for coding agents

This repository separates current system truth from project/change history. Do not
read every document before acting.

## Required reading order

1. Read `docs/project/current.md` to determine the active iteration, development
   slice, standing authority, product objective, and current work plan.
2. Read the selected iteration's `proposal.md`, `manifest.yaml`,
   `readiness-review.md`, active file under `development-design/`, and
   `verification-matrix.md`.
3. Follow only the referenced documents under `docs/system/`.
4. Confirm the exact files and external effects stay within the active standing
   authority. The current action mirrors the work plan and trusted path boundary;
   it cannot create, revoke, consume, or pause standing authority.
5. Inspect the relevant code and tests. Code and tests own local implementation
   details; system documents own cross-module semantics and invariants.

`docs/project/roadmap/` is planning input, not coding authorization.
`docs/archive/` is historical evidence, not current authority.
`docs/_generated/` is a derived index, not normative content.
When no active slice is named, do not edit product code or create an iteration from
these documents alone; a user's explicit request is still required.

The current checkout has an explicit architecture freeze. Do not modify, add,
delete, rename, move, replace, reformat, regenerate, or otherwise rewrite any
path under `docs/system/architecture/` without the user's explicit consent.
Normal development authority does not include architecture changes, and a test
result, failed gate, or generated index cannot imply consent. The local
architecture lock checker is an additional mechanical guard; never refresh its
manifest automatically. This freeze is checkout-local and must not be assumed
for another clone, worktree, or branch.

The current development plan is constrained to one user-value vertical
sequence. Before changing product code, run the local plan-shape checker at
`.git/hooks/plan-shape-check.py`; it must pass together with the architecture
lock check. Do not add a second phase numbering scheme, hard-code an expired
commit or run, or put configuration, supervision, full regression, or Codex
comparison in front of the first browser experience.


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

Do not exceed the trusted standing authority, and do not let a candidate Manifest
authorize its own diff. Inside that authority, product development continues across
ordinary commits, failures, targeted tests and work-plan adjustments without new
human authorization. A first operable complete browser chain must be handed to the
user immediately with `requires_result=false`; it does not move a plan cursor.
Ordinary failures remain in the same development loop and never require their own
Result, PDR or authorization.

The trusted-parent check is the first executable CI gate. On pull requests it
must validate the pull-request head SHA, not a synthetic merge SHA. Every
plan-controlled commit must have exactly one parent and that parent must be the
previous trusted node; candidate Python, tests, documentation tooling, or other
repository code must not run before this check succeeds.

Mechanical checks reject only an out-of-authority diff or external side effect,
candidate self-authorization, or a false completion claim. A failed check blocks
that diff, operation or claim; it does not revoke the rest of the development
authority. Do not build per-failure actions, Activation clocks, whole-Manifest
digest schemes, or verifier state machines that duplicate the product workflow.

Each real external dispatch still requires an automatic runtime record tied to the
active standing authority, exact source/product/session/route/disclosure/budget,
and Secret Reference. First-experience development runs only targeted impact,
startup, safety and failure-truthfulness tests. Full regression, hidden inputs,
cross-project validation, hardening and Production wait until the experience and
quality direction are confirmed, but they do not require repeated authorization
when they already fall within the same standing scope. Ordinary answer failures
stay in the same development loop: locate the earliest divergence, make a general
repair, and recheck heterogeneous unseen questions.

Local gates do not establish an unbypassable trust boundary against a malicious
repository administrator. Do not claim that property until the remote host has
an immutable required workflow/ruleset and the required user/provider evidence
has independently authenticated signatures.

Run the smallest relevant targeted, startup, and safety tests during first-experience
development. Run the full suite after the experience and quality decision unlocks
hardening, and before final acceptance; do not use it to delay the first complete
browser experience.
