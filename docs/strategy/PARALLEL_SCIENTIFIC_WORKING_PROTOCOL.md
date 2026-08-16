# Parallel Scientific Working Protocol

## Purpose

Parallel scientific work accelerates model development by exploring independent mechanisms simultaneously while preserving scientific and artifact independence, preventing duplicate execution and conflicting definitions, and making later integration auditable.

## Lane eligibility

A lane requires a distinct scientific question, issue, branch, worktree, code/document namespace, external result directory, prospectively declared dependencies, and explicit claim and execution boundaries. Agents must not concurrently work on the same protocol, branch, PR, generated matrix, external result bundle, production phase, or solver source files.

## One-writer rule

Only the declared lane owner may write the lane branch, PR, result bundle, authority and manifest artifacts, or GitHub issue/completion comments. Other agents may inspect only at a stable review boundary.

## Repository isolation

Each active lane uses one dedicated worktree and a branch named for its stable task ID. No agent may reset, clean, stash, switch, or execute in another lane's worktree. Lane declarations assign explicit path ownership; secondary work never uses the primary checkout.

## Artifact isolation

Each lane uses a separate external run root. Mutable bundles and case records are never shared, no process targets another lane's output, and copied results cannot be represented as independently generated. Shared reference data are read-only.

## Process ownership

Every execution records task ID, branch, exact source HEAD and tree, parent and worker PIDs, command, external output policy, start/completion times, and owner. No agent may signal, stop, resume, or contain another lane's process without explicit owner adjudication.

## Shared-file policy

Conflict-prone files include `docs/PROJECT_STATE.md`, `docs/strategy/SCIENTIFIC_MODELING_FORWARD_PLAN.md`, `SOURCE_PACKAGE_MANIFEST.json`, `PACKAGE_QA_STATUS.json`, top-level release/status documents, production solver source, and common reference utilities. Active lanes avoid shared status files. Globally generated manifests are updated only when checks require it and regenerated after integration from accepted main. Scientific files stay task-local; a necessary common change receives separate integration review.

## Resource coexistence

The primary lane has priority. Unless the owner changes the allocation, a secondary reduced-model lane uses at most `min(16, floor(0.25 * logical CPU count))` workers, one nested numerical-library thread, 16 GiB memory, and no GPU. A heavy secondary run does not start while production simulation occupies most of the host.

## Integration serialization

1. Each lane completes and is reviewed independently.
2. The owner chooses merge order; the first accepted lane integrates first.
3. The later lane integrates current main and regenerates shared metadata.
4. The executed scientific source commit remains in ancestry; results are not rebound silently.
5. Only integration-affected checks rerun unless scientific source changed.
6. No agent independently marks a PR ready or merges it.

Do not rebase or rewrite an exact adjudicative execution commit without explicit review.

## Duplicate-assignment containment

On overlap, start no new execution. Inventory all processes, branches, worktrees, PRs, and modified artifacts; distinguish writer from observer; preserve evidence; select one owner; and stand down the other agent. Do not delete or clean artifacts before reconciliation.

## Stable review boundaries

Independent review is most useful after protocol freeze, a stable manifest, or a deterministic endpoint, and before production-physics promotion or merge.

## Close-out

Each lane reports final branch/HEAD/tree, issue and PR state, changed files, authority and result identities, a safe external-evidence reference, scientific disposition, claim ceiling, remaining processes, and whether it awaits review, integration, or closure. General records omit personal blame and machine-specific incident narratives.
