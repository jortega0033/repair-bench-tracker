# Implementer map

Status: **scaffold only: the modules exist as empty stubs, no product behaviour is implemented.** This page maps the boundaries that [PROJECT-PLAN.md](PROJECT-PLAN.md) requires onto a module layout so that parallel tickets do not collide. It adds no requirement; the plan wins where they differ. The names are the orchestrator's proposal, fixed by the scaffold; a ticket that changes one corrects this page in the same pull request.

## Planned module map

| Boundary | Module | Owns | Parent ticket |
|---|---|---|---|
| Command line | `repair_bench/__main__.py` | Arguments and the subcommands init, demo, serve, check and report | #2, #5, #6 |
| Contracts | `repair_bench/contracts.py` | Command request and response shapes, limits, error codes | #2 (freeze), #3, #4 |
| Storage | `repair_bench/store.py` | SQLite schema, transactions, command keys, init | #2, #4 |
| Jobs | `repair_bench/jobs.py` | State machine, cycles, events, test attempts | #2 (intake), #3, #5 |
| Parts | `repair_bench/parts.py` | Receipts, holds, releases, consumption, movements | #4, #5 |
| Commands | `repair_bench/commands.py` | One entry for every write: key, revision, state, stock, response | #2 to #5 |
| Reports | `repair_bench/reports.py` | Versioned job and inventory export from one snapshot | #6 |
| Consistency check | `repair_bench/check.py` | Independent replay of movements and active holds | #5 |
| HTTP | `repair_bench/server.py` | Loopback bind, request guards, routes, static assets | #2 to #6 |
| Browser assets | `repair_bench/static/` | Queue, job detail, parts shelf, report | #2 (intake), #5 (minimal job page), #6 |
| Test oracle | `tests/expected.py` | Fixture table of the plan as independent values | #2 to #7 |
| Test support | `tests/fixtures.py` (added by #4) | Job rows seeded by SQL, so #4 stays parallel to #3 | #4 |

Dependency direction: `__main__` depends on `server`, `commands`, `store`, `check` and `reports`; `server` on `commands` and `reports`, and for reads on `jobs`, `parts` and `store`; `reports` on `store`; `commands` on `jobs`, `parts` and `store`; `jobs` and `parts` on `contracts`. `contracts` imports nothing from the package. `check` reads the database file only and imports nothing from the write path. `tests/expected.py` and `tests/fixtures.py` import nothing from the package.

## Freeze points

Parallel tickets rely on these shapes. A ticket that changes a frozen shape updates this page and every dependent ticket in the same pull request.

- **Command request and response shapes, revision rule, transaction boundary and SQLite schema version 1**: ticket #2 writes them down here before #3 and #4 start in parallel.
- **Movement types and deltas**: #4 documents them before #5 replays them.
- **Report schema version 1**: #6, before #7 exports the demo report.

## What is verified where

Python tests run locally and in CI on Linux and Windows. Races use separate SQLite connections in separate processes or threads. Browser checks are manual in Chrome unless a ticket states a headless run.
