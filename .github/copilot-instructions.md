# Copilot Instructions for Speckit

This repository contains **Speckit**, a specification-driven development system that uses AI-guided agents to create and manage feature specifications, implementation plans, task lists, and executable implementations.

## Quick Reference

### Key Commands

All Speckit commands are custom agents configured in `.github/agents/` and are invoked through the Copilot CLI using `/speckit.*` prefix. Key workflows:

**Specification Phase:**
- `/speckit.specify` — Convert user requirements into structured spec.md
- `/speckit.clarify` — Ask targeted questions to resolve underspecified areas

**Planning Phase:**
- `/speckit.plan` — Create detailed implementation plan (architecture, technical context, project structure)
- `/speckit.checklist` — Generate custom checklists from feature requirements

**Implementation Phase:**
- `/speckit.tasks` — Generate ordered, dependency-tracked task list from spec and plan
- `/speckit.analyze` — Non-destructive audit of spec.md, plan.md, and tasks.md for consistency
- `/speckit.implement` — Execute implementation tasks

**Constitution & Governance:**
- `/speckit.constitution` — Create or update project constitution (core principles and rules)

**Conversion:**
- `/speckit.taskstoissues` — Convert tasks.md into GitHub Issues with dependencies and ordering

### File Structure

Each feature lives in its own directory:

```
specs/[###-feature-name]/
├── spec.md              # User stories, requirements, acceptance criteria
├── plan.md              # Technical decisions, architecture, project layout
├── research.md          # Phase 0 research output (created by /speckit.plan)
├── data-model.md        # Phase 1 data model (created by /speckit.plan)
├── quickstart.md        # Phase 1 usage guide (created by /speckit.plan)
├── contracts/           # Phase 1 interface definitions (created by /speckit.plan)
└── tasks.md             # Phase 2 implementation task list (created by /speckit.tasks)
```

The project constitution lives at `.specify/memory/constitution.md`.

### Core Workflow

1. **Start**: `/speckit.specify "user request"` → creates `spec.md`
2. **Clarify**: `/speckit.clarify` → refine underspecified areas (optional)
3. **Plan**: `/speckit.plan` → creates `plan.md` + supporting research docs
4. **Analyze**: `/speckit.analyze` → validate consistency before implementation
5. **Tasks**: `/speckit.tasks` → creates `tasks.md` with ordered, parallel-safe tasks
6. **Implement**: `/speckit.implement` → execute tasks to completion

At any point, you can convert to GitHub Issues with `/speckit.taskstoissues`.

## Architecture & Key Concepts

### Specification-Driven Development

Speckit enforces a **contract-first** approach:

- **spec.md** defines WHAT (user stories, requirements, acceptance criteria)
- **plan.md** defines HOW (technical approach, architecture, project layout)
- **tasks.md** defines ORDERED STEPS (with parallelization markers and dependencies)
- **Implementation** follows the contract exactly (red-green-refactor TDD cycles)

This separation means:
- Design decisions happen before code
- Changes to spec/plan trigger regeneration of tasks
- Constitution violations are caught early, not during implementation

### Task Organization & Parallelization

Tasks follow a strict format:

```
[T###] [P?] [Story] Description with exact file paths

- [P]     = Can run in parallel (different files, no cross-dependencies)
- [Story] = User story identifier (e.g., US1, US2, US3)
```

**Phases structure:**
1. **Setup** — Project initialization (can be parallel [P])
2. **Foundational** — Blocking prerequisites for all stories (CRITICAL GATE)
3. **User Stories** — Independent implementation per priority (P1, P2, P3, etc.)
4. **Polish** — Cross-cutting concerns (documentation, optimization, refactoring)

Key rule: User stories must be **independently testable** and deployable. This means you can stop at any user story checkpoint and have a working MVP.

### Constitution Authority

The project constitution (`.specify/memory/constitution.md`) defines:

- **Core Principles** — MUST, SHOULD, and OPTIONAL requirements
- **Additional Constraints** — Security, performance, technology stack rules
- **Development Workflow** — Review, testing, and approval gates

**The constitution is non-negotiable** within the scope of a feature. If a principle needs to change, it requires a separate constitution amendment outside the feature workflow.

During specification and planning phases, `/speckit.analyze` will flag any constitution violations as CRITICAL issues.

### Data Model & Contracts

**Phase 1 outputs** (created by `/speckit.plan`) include:

- **data-model.md** — Entity definitions, relationships, constraints
- **contracts/** — API/interface definitions (HTTP contracts, function signatures, schema definitions)
- **quickstart.md** — Integration guide for developers using this feature

These are used by `/speckit.tasks` to generate implementation tasks that map 1:1 to acceptance criteria.

## Helper Scripts

PowerShell scripts in `.specify/scripts/powershell/`:

- `check-prerequisites.ps1` — Validate required files exist (spec.md, plan.md, tasks.md)
- `create-new-feature.ps1` — Initialize new feature directory structure
- `setup-plan.ps1` — Scaffold a new feature spec with guided questions
- `common.ps1` — Shared utilities (path resolution, JSON formatting)
- `update-agent-context.ps1` — Sync agent files with current prompts

**To use**: Run directly from repo root with PowerShell 7+
```powershell
./.specify/scripts/powershell/check-prerequisites.ps1 -Json
```

## Conventions

### Branch Naming

Feature branches follow the pattern: `[###]-feature-name`

- `###` = Sequential feature number (e.g., `001-user-auth`)
- Use kebab-case for feature names

### Task IDs

Use descriptive kebab-case identifiers, not sequential numbers:

```
# GOOD:
[user-auth-model] — Create User model with bcrypt hashing
[api-routes] — Setup Express routes

# BAD:
[T001] or [T1] — Create model
```

When task IDs must be sequential (in generated tasks.md), format as `[T###]` with 3 digits.

### Documentation Requirements

- spec.md MUST include acceptance scenarios (Given/When/Then format)
- plan.md MUST include project structure diagram and technical context
- Each task MUST include exact file paths (e.g., `src/models/user.ts`, not `src/models/`)
- Commit messages MUST reference task IDs and user story

### Story Prioritization

User stories MUST be assigned priorities:

- **P1** — MVP-critical, deliver value standalone
- **P2** — Important enhancement, non-blocking
- **P3** — Nice-to-have, lowest priority

Each story must be independently testable (can be developed/deployed without others).

## Testing Strategy

### Test Organization

Tests follow the phase structure:

```
tests/
├── contract/          # API contracts (Phase 2 prerequisites)
├── integration/       # End-to-end user journeys (one per story)
└── unit/              # Logic-layer tests (per story)
```

### Test-Driven Development (TDD)

In `/speckit.implement`, tests are written FIRST:

1. Write failing contract test that validates acceptance criteria
2. Write failing integration test for user story journey
3. Implement code to make tests pass
4. Refactor while keeping tests green

Tests MUST reference the task ID and story (e.g., `[T010][US1] Contract test for login endpoint`).

### Running Tests

Check generated tasks.md for exact test commands, which will be specific to:
- Language/framework (pytest, Jest, Mocha, xUnit, etc.)
- Test runners (cargo test, npm test, dotnet test, etc.)
- File organization (single project vs. monorepo)

Example commands (actual commands in tasks.md will be specific):
```bash
npm test                          # Run all tests
npm test -- --testNamePattern=US1 # Run tests for User Story 1
npm test:unit                     # Unit tests only
npm test:integration              # Integration tests only
```

## Common Patterns

### Starting a New Feature

```bash
# Step 1: Create feature specification
/speckit.specify "user description of feature"

# Step 2: Clarify any ambiguous requirements
/speckit.clarify

# Step 3: Plan the implementation
/speckit.plan

# Step 4: Validate consistency
/speckit.analyze

# Step 5: Generate task list
/speckit.tasks

# Step 6: Create GitHub issues (optional)
/speckit.taskstoissues

# Step 7: Implement
/speckit.implement
```

### Working with Multiple Features

Each feature directory is independent:

- Specs are in `specs/[###-feature-name]/`
- Agents work on one feature at a time
- Constitution applies to all features
- Tasks from different features can be executed in parallel by different team members

### Making Changes Mid-Development

If spec or plan changes after tasks.md is generated:

1. Edit the spec.md or plan.md file
2. Re-run `/speckit.analyze` to identify impact
3. Re-run `/speckit.tasks` to regenerate task list
4. Review changes (tasks are deterministic given same inputs)

Changed tasks might affect:
- Task ordering (dependencies)
- Parallelization markers [P]
- Story assignments
- File paths

**Important**: Don't manually edit tasks.md if you plan to regenerate — regeneration will replace manual edits.

## AI Agent Configuration

Custom agents are defined in `.github/agents/`:

- Each agent has a `.agent.md` file (metadata + execution instructions)
- Paired with a `.prompt.md` file in `.github/prompts/` (the actual prompt)
- Agents are invoked via `/speckit.*` commands
- Agents can only read files; to make changes, they call sub-agents or manual steps

To modify an agent's behavior:
1. Edit `.github/prompts/speckit.[command].prompt.md`
2. Optionally update `.github/agents/speckit.[command].agent.md` (metadata only)
3. Run `./.specify/scripts/powershell/update-agent-context.ps1` to sync

## Debugging & Troubleshooting

### Common Issues

**Problem**: `/speckit.tasks` says tasks.md already exists but you need to regenerate

**Solution**: Delete the old `specs/[###-feature-name]/tasks.md` and run `/speckit.tasks` again

**Problem**: Analyzing reports CRITICAL constitution violations

**Solution**: Constitution violations must be fixed before proceeding. Either:
- Amend the constitution (separate workflow outside feature), OR
- Revise spec/plan to comply with existing constitution

**Problem**: Agent output seems incomplete or out-of-sync

**Solution**: Run `/speckit.analyze` to check consistency; if CRITICAL issues exist, address them before proceeding to `/speckit.implement`

### Checking Prerequisites

Before running any command, validate prerequisite files exist:

```powershell
./.specify/scripts/powershell/check-prerequisites.ps1 -Json
```

This will output paths and available documents (spec.md, plan.md, tasks.md).

## Configuration Files

### `.specify/init-options.json`

Global Speckit configuration:

```json
{
  "ai": "copilot",              // AI backend (copilot, claude, etc.)
  "ai_commands_dir": null,      // Custom commands directory
  "ai_skills": false,           // Whether to use AI skills
  "branch_numbering": "sequential",
  "here": true,                 // Execute in current directory
  "offline": false,             // Offline mode flag
  "preset": null,               // Preset configuration
  "script": "ps"                // Script language (ps = PowerShell)
}
```

### `.vscode/settings.json`

VS Code Copilot integration (chat prompts):

```json
{
  "chat.promptFilesRecommendations": {
    "speckit.constitution": true,
    "speckit.specify": true,
    "speckit.plan": true,
    "speckit.tasks": true,
    "speckit.implement": true
  }
}
```

## Best Practices

### Before Starting Implementation

1. Run `/speckit.analyze` on a complete spec + plan
2. Fix all CRITICAL issues before generating tasks
3. Review the data model and contracts in plan output
4. Ensure user stories are independently testable (stop-gate rule)

### During Implementation

1. Follow task order strictly (dependencies matter)
2. Run tests BEFORE implementation (red-green-refactor)
3. Commit after each task or logical group
4. Reference task IDs in commit messages

### After Completing a Story

1. All tests for that story pass
2. Run the "Independent Test" from spec.md for that story
3. Verify no regressions in other stories
4. Only then move to next priority

### For Code Reviews

- Verify spec.md acceptance criteria are met
- Check that contract tests pass
- Ensure task-to-code mapping is 1:1
- Validate no constitution violations

## Resources

- **Speckit Documentation**: Prompts in `.github/prompts/`
- **Templates**: `.specify/templates/` (spec, plan, tasks, checklist, constitution, agent config)
- **Agent Definitions**: `.github/agents/` (metadata for each `/speckit.*` command)
- **Constitution**: `.specify/memory/constitution.md` (project governance rules)

---

**Version**: 0.4.3 | **Last Updated**: 2026-03-30

For more details, see the `.specify/templates/` directory and `.github/agents/` configuration files.
