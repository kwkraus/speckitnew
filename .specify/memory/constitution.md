<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles:
	- Template principle 1 -> I. Code Quality Is Enforced
	- Template principle 2 -> II. Tests Define Completion
	- Template principle 3 -> III. User Experience Stays Consistent
	- Template principle 4 -> IV. Performance Is Budgeted
- Added sections:
	- Delivery Standards
	- Development Workflow
- Removed sections:
	- Placeholder fifth principle slot from the template
- Templates requiring updates:
	- ✅ .specify/templates/plan-template.md
	- ✅ .specify/templates/spec-template.md
	- ✅ .specify/templates/tasks-template.md
	- ✅ .specify/templates/commands/*.md (no files present; no update required)
- Follow-up TODOs:
	- TODO(RATIFICATION_DATE): original adoption date is not recoverable from repository context
-->

# Speckit Constitution

## Core Principles

### I. Code Quality Is Enforced
Every change MUST leave the repository in a clearer and more maintainable state.
Production code MUST be explicit, minimal in scope, and aligned with existing project
structure. Linting, formatting, and static analysis requirements MUST be defined in the
plan before implementation begins. Reviewers MUST reject speculative abstractions,
unbounded complexity, and undocumented deviations from established project patterns.
Rationale: Speckit is a workflow system; unclear or brittle implementation guidance
propagates defects into every downstream artifact.

### II. Tests Define Completion
Each user story MUST specify how it is validated independently, and implementation is
not complete until automated tests prove the required behavior. Plans MUST describe the
test strategy for unit, integration, and contract coverage where applicable. Tasks MUST
place test creation before implementation work, and any decision to omit a test layer
MUST be justified explicitly in the plan. Rationale: Speckit depends on reliable,
repeatable execution steps; unverifiable work is incomplete work.

### III. User Experience Stays Consistent
User-facing behavior MUST preserve a coherent experience across flows, copy,
interaction states, and visual patterns. Specifications for features with a UI or CLI
surface MUST describe the relevant experience conventions, including empty states,
errors, and accessibility expectations. Plans and tasks MUST call out any intentional
new pattern so reviewers can evaluate whether it extends or fragments the product.
Rationale: inconsistent experiences increase support cost and reduce trust even when
features are technically correct.

### IV. Performance Is Budgeted
Performance requirements MUST be stated as measurable budgets whenever a feature can
affect latency, throughput, resource usage, or perceived responsiveness. The plan MUST
record the expected budget and the validation method, and tasks MUST include any needed
profiling, benchmarking, or regression checks. A change that meets functional goals but
violates an agreed budget is incomplete until the variance is resolved or formally
accepted. Rationale: performance regressions are product regressions and must be managed
with the same rigor as correctness.

## Delivery Standards

- Plans MUST document quality gates, test strategy, UX consistency expectations, and
	performance budgets before implementation tasks are generated.
- Specifications MUST describe independently testable user stories and measurable
	success criteria.
- Tasks MUST use exact file paths and sequence validation work ahead of implementation.
- Documentation that guides operators or contributors MUST be updated when behavior,
	workflow, or expectations change.

## Development Workflow

- `/speckit.specify` outputs MUST capture user stories, independent tests, edge cases,
	requirements, and measurable success criteria.
- `/speckit.plan` outputs MUST pass the Constitution Check before implementation starts
	and MUST restate any justified exceptions in Complexity Tracking.
- `/speckit.tasks` outputs MUST preserve story independence, include validation work,
	and surface cross-cutting tasks for quality, UX, and performance when relevant.
- `/speckit.implement` work MUST follow the ordered tasks unless the governing spec,
	plan, and tasks artifacts are regenerated.


## Governance

This constitution supersedes conflicting repository guidance for Speckit workflows.
Amendments MUST be made in this file, MUST include a Sync Impact Report, and MUST update
affected templates or guidance in the same change.

Versioning policy:
- MAJOR: remove a principle, redefine a principle in a backward-incompatible way, or
	materially weaken a compliance requirement.
- MINOR: add a new principle or materially expand required workflow guidance.
- PATCH: clarify wording, fix inconsistencies, or make non-semantic edits.

Compliance review expectations:
- Every plan MUST document how it satisfies the four core principles.
- Every task list MUST show where testing, UX validation, and performance checks occur
	when relevant to the feature.
- Reviewers MUST block approval when required gates, measurements, or justifications are
	missing.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date unknown | **Last Amended**: 2026-03-30
