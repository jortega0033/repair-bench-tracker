# CLAUDE.md

Working instructions for this repository. Read this file first, then the documents it links to. It does not repeat them.

## What this is

An offline repair desk for a small shop or repair cafe: take an item in, diagnose it, reserve the last spare part once, record failed and passed tests, hand it back, and keep the earlier history when it returns. Python 3.12 standard library and SQLite, `127.0.0.1` only, fictional records.

**Nothing is implemented yet.** The repository holds the plan, the delivery tooling and the backlog in epic #1. Commands marked planned below do not work yet. Do not describe a planned thing as working, and do not claim a passing baseline: there is none.

## Sources of truth

| Topic | Document |
|---|---|
| Product scope, design, fixtures with expected values | [docs/PROJECT-PLAN.md](docs/PROJECT-PLAN.md) |
| Planned module map, freeze points, planned versus implemented | [docs/architecture.md](docs/architecture.md) |
| Backlog | Epic issue #1 and its child tickets on GitHub. The epic's table is authoritative for order, dependencies and estimates; tickets state their own owner-decision defaults. |
| Loop setup and its limits | [LOOP.md](LOOP.md), [loop-constraints.md](loop-constraints.md) |
| Project subagents, origin and local changes | [.claude/agency-agents/README.md](.claude/agency-agents/README.md) |
| Ticket workflow and the step at which each role runs | [.claude/skills/implement-ticket/SKILL.md](.claude/skills/implement-ticket/SKILL.md), section "Agent roles" below |
| How a ticket goes from the queue to a ready pull request, who may do what | "Delivery workflow" below |
| UI and copy rules, design tokens | [docs/ui-quality.md](docs/ui-quality.md), [docs/design-tokens.md](docs/design-tokens.md) |
| Decisions the owner made, with dates | [docs/owner-decisions.md](docs/owner-decisions.md) |

The plan wins for product design; the epic and tickets win for order and scope. A ticket that changes a contract fixes the plan in the same pull request.

## Stack and constraints

- Python 3.12, **standard library only**, in the application and in the tests. No package download in any launch, fixture or test step.
- Serves bundled HTML, CSS and JavaScript and a small JSON API on `127.0.0.1`. No build step.
- One local SQLite database in an explicit data directory; one bench, one shelf, integer quantities.
- Limits: 32 KiB per request, 500 characters per note, 1 to 9,999 parts per command, 100,000 per part, 50 rows per page, 100 jobs per export.
- Offline: same-origin assets and data only. Fictional items, parts and aliases only.
- Several shelves or sites, memberships, customer contact, prices, payment, barcode hardware, attachments and messages are outside the first release.
- A runtime version change, a dependency, an external request or a non-loopback listener needs the owner's approval first, not a pull request.

## Commands

Python 3.12 or 3.13. No install step is needed.

| Purpose | Command | Status |
|---|---|---|
| Tests | `python -m unittest discover -s tests` | planned: real with the scaffold |
| Help and version | `python -m repair_bench --help` | planned: real with the scaffold |
| Create a database | `python -m repair_bench init --data-dir ./data` | planned: #2 |
| Run the app | `python -m repair_bench serve --port 8769 --data-dir ./data` | planned: #2 |
| Check consistency | `python -m repair_bench check --data-dir ./data` | planned: #5 |

## Architecture boundaries

The planned module map is in [docs/architecture.md](docs/architecture.md). Invariants every change must keep (the plan is the source):

- Job state, stock, commands, storage, reports and rendering stay separate. The browser shows server state and never computes availability or an allowed action.
- The states are Intake, Diagnosed, In repair, Testing, Ready, Handed off and Canceled, with exactly the transitions of the plan. Anything else is rejected with a reason and changes nothing.
- Every successful job action raises the revision by one and adds one event. Events are only ever inserted, and their order is the revision, never the clock.
- A job enters Testing only without holds in its current cycle. Handoff needs Ready, a confirmation and a pass in the current cycle. Reopening starts a new cycle and keeps every earlier event and test.
- Available is on-hand minus reserved. Reserved equals the sum of the active holds of that part. Deltas are exactly those of the plan's table, and cancellation releases all holds in the same commit as the state change.
- A write starts with `BEGIN IMMEDIATE`, looks for the command key first, then checks revision, state and availability with a guarded update that must change the intended row. Stock and history never commit separately.
- The same key with the same request returns the stored response, also after a restart; with another request it is a conflict. A rejected command stores nothing.
- At the end of every write transaction reservation totals and movement arithmetic are asserted; a failed check aborts the command. The offline consistency check replays movements from zero and shares no code with the write path.
- One connection per request with foreign keys on, a short busy timeout and a retryable busy response. Reports read in one transaction and change no revision.
- A stale revision never touches stock; the response carries the latest status and the browser keeps the typed text.
- The server binds `127.0.0.1`; writes need JSON, the exact own origin and at most 32 KiB; reads are GET and have no effect. Bounds on notes, quantities, counts and pages are checked on the server.
- The data directory is explicit. A new database is made only by the init command, which refuses an existing file; demo data comes only from its own command.
- Labels, notes and aliases are rendered as text, never as HTML. Same-origin assets only, no telemetry, no personal data.
- States and conflicts are written as text, errors stand next to their field, focus is visible, and the whole workflow works by keyboard.

## Git workflow

- `main` is the default branch. Work on one branch per ticket: `<issue-number>-<short-slug>`. Never commit to `main`.
- Small commits with imperative subjects and a type prefix (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Order for every ticket: local evidence, Code Reviewer, Reality Checker, then a draft pull request that says `Part of epic #1` and `Closes #<ticket>`, then CI on that draft, then `gh pr ready` only when CI is green.
- Do not push or open a pull request unless the owner asked in the current session; starting `/next-ticket` is that request for one ticket. Only the owner merges and releases. Do not push to `main`, force-push, or merge your own pull request.
- Never commit a data directory (`data/`), `.env*`, or build output.
- Do not change `.claude/agents/`, `LOOP.md`, `loop-constraints.md` or `loop-budget.md` as part of a feature ticket.
- Open owner decisions on a ticket are settled with the ticket's stated default. Where a ticket states none, take the conservative option and say so in the pull request.

## Evidence before a ticket is called done

Paste real output into the pull request; never summarise a run you did not make.

1. For each acceptance criterion of the issue: the name of the test that proves it, or the exact step and what was observed.
2. The full output of `python -m unittest discover -s tests` locally, and the link to the green CI run on the draft pull request (Linux and Windows, Python 3.12 and 3.13).
3. For a stock change: the row of the plan's fixture table, on-hand, reserved and available before and after, and the consistency check output.
4. For a concurrency change: the number of connections, the outcome of each and the event and movement counts.
5. For a UI change: the Chrome version, the steps and what was observed, and that the page made no external request.
6. `git status` shows no stray files, and no dependency, external URL or non-loopback listener was added.
7. Anything not verified, said plainly.

## Agent roles

Project subagents are in `.claude/agents/`: nine Agency Agents roles and `loop-verifier`, which belongs to the Loop setup. Each Agency Agents role file starts with a section "In this repository", written for this project. That section and this file override the generic text below it. Sources, licence, local changes and the name collision with a user-level install are in [.claude/agency-agents/README.md](.claude/agency-agents/README.md).

When asked to implement, continue or finish a GitHub issue, follow the playbook [`.claude/skills/implement-ticket/SKILL.md`](.claude/skills/implement-ticket/SKILL.md). Claude Code loads it on its own for ticket work; `/implement-ticket <issue number>` starts it by hand. Delegate to the roles without waiting to be asked: each role's `description` ends with a "Use proactively ..." sentence, which is what makes Claude Code delegate. The playbook gives the exact trigger of each role.

| When | Roles | Access |
|---|---|---|
| Before coding | Software Architect | `Read, Grep, Glob` |
| While coding | Backend Architect, Database Reliability Engineer, Frontend Developer | can edit |
| After coding, when the trigger matches | Application Security Engineer, Accessibility Auditor | `Read, Grep, Glob` |
| After coding, when the trigger matches | API Tester | can edit |
| Gate on every ticket | Code Reviewer on the full diff, until no material finding is left | `Read, Grep, Glob` |
| Acceptance gate on every ticket, after Code Reviewer | Reality Checker on each acceptance criterion and the recorded evidence, and that CI is configured to run the checks (no CI result is needed yet) | `Read, Grep, Glob` |

- The two gates run on every ticket, whatever its size. A ticket is not called done before both have passed.
- Roles limited to `Read, Grep, Glob` cannot run commands. Give them the diff, the acceptance criteria and whatever command output exists.
- The session or role that wrote a change does not count as its reviewer.
- If a role is missing or cannot be delegated to, the session does the before-coding, while-coding and specialist steps itself and says so. It cannot pass the two gates on its own change: do not push or open the pull request. Stop, report that the gates could not run, and leave the run for the owner. This overrides the playbook's sentence "do that step yourself" for the two gates.
- In the pull request description, list under "Agent roles run" each role that ran, what it was asked and its verdict, and any step done without a role.

## Delivery workflow

How a ticket reaches the owner. Each piece is described in its own file; this part only links them.

- **Start:** the owner runs `/next-ticket` ([`.claude/skills/next-ticket/SKILL.md`](.claude/skills/next-ticket/SKILL.md)); it picks one leaf ticket (never a `tracking` parent or a ticket with open sub-issues; the last sub-issue's pull request also closes the parent), creates the branch and worktree, and runs the playbook [`.claude/skills/implement-ticket/SKILL.md`](.claude/skills/implement-ticket/SKILL.md). Nothing is scheduled.
- **Gate hook:** [`.claude/hooks/role_gate.py`](.claude/hooks/role_gate.py) blocks `gh pr create` and `gh pr ready` until Code Reviewer and Reality Checker ran after the last code edit. `ROLE_GATE=off` in the environment Claude Code is started from switches it off for that session; only the owner does that.
- **Permissions:** [`.claude/settings.json`](.claude/settings.json). Agent configuration edits ask in the main checkout and in ticket worktrees; CI, `CLAUDE.md`, `AGENTS.md` and Loop-file edits ask only in the main checkout; in a ticket worktree they are limited by the playbook's scope rule and reviewed by the owner at merge (shell-made edits are not covered, so a ticket never changes agent configuration); force pushes, pushes to `main`, `gh pr merge`, releases and reads of `.env` are denied.
- **CI:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Every job must be green on the current diff before a pull request is marked ready. The agent does not poll: it ends its turn with "Draft pull request #N is waiting for CI" and reads `gh pr checks` once when woken. Reviewers read the diff and evidence from `.claude/state/review/`. An acceptance step that needs a person is listed under "Owner checks" in the pull request.
- **Pull request:** [`.github/pull_request_template.md`](.github/pull_request_template.md). Tickets use [`.github/ISSUE_TEMPLATE/implementation-ticket.md`](.github/ISSUE_TEMPLATE/implementation-ticket.md).
- **Labels:** `status:ready`, `status:blocked`, `status:in-progress`, `needs-decision`, `tracking` (parent container, never worked; its sub-issues are the work items).
- **Changelog:** every ticket pull request adds one line under Unreleased in [CHANGELOG.md](CHANGELOG.md).
- **UI and copy:** [docs/ui-quality.md](docs/ui-quality.md); the `ui-ux-pro-max` and `unslop` skills are in `.claude/skills/`. Colours come from the shared design tokens in `repair_bench/static/tokens.css` ([docs/design-tokens.md](docs/design-tokens.md)); new UI adds no colour literals.
- **Decisions:** [docs/owner-decisions.md](docs/owner-decisions.md). Security reports: [SECURITY.md](SECURITY.md).
- **Merge and release:** only the owner merges and releases ([docs/RELEASING.md](docs/RELEASING.md)). An agent stops at a ready pull request.

## Loop

Issue triage runs at L1: report-only, started by hand, no scheduler, no GitHub writes. See [LOOP.md](LOOP.md).
