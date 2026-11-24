# Repair Bench Tracker

> This document specifies phase 1 of the program in [#42](https://github.com/jortega0033/repair-bench-tracker/issues/42). Hour figures in it are early estimates for that phase; its open tickets add up to 65 to 110 hours (2026-11-24). Work that it defers is planned in the later phases only where the program names it.

An offline repair desk that follows each item from intake through diagnosis, repair, testing and handoff. It gives a small bench one shared view of repair history and parts availability.

## Product requirements

**Audience and problem.** A small repair shop or community repair café often has several jobs waiting for the same spare part. When notes and parts counts live in separate places, two volunteers can promise the last part, a failed test can go unnoticed, and a reopened job can lose its earlier history.

**Outcome.** An operator can create a job, record a diagnosis, reserve and use a part, record a failed or successful test, and hand the item back. If the same item returns, the operator opens a new repair cycle on the existing job and can still see the earlier outcome. The job detail and parts shelf agree about what is still available.

**First durable milestone.** Open the bench in Chrome, create a fictional job, diagnose it, close the browser, and see the diagnosis and its history after restarting the local server. The completed epic adds exact stock accounting, a test and handoff gate, reopening, a restart check, and a shareable report using fictional records.

| User | Needs |
| --- | --- |
| Intake volunteer | Give an item a bench number and one clear next step. Find it later by its label or state. |
| Bench technician | See the exact availability of a spare, reserve it once, and leave an accountable repair and test record. |
| Handoff volunteer | Know which jobs passed inspection, confirm collection, and retain a record if an item comes back. |

**Release scope.** One local bench, one inventory shelf, integer quantities, one or two simultaneous browser tabs, and five job views for intake, diagnosis, work, test/ready and history. Planned views include the intake and queue, job detail with its cycle history, parts shelf with reservations by job, and the closed-job report. Include keyboard access, status text, labeled inputs, visible focus, and error text next to the relevant field. The default is a simple operator interface with a short bench alias and a required fictional item label.

**Future scope.** Shelf transfers, multi-site access, memberships, customer contact, pricing, payment, barcode hardware, attachments and messaging are separate product decisions. The release models the functional bench workflow with made-up items, parts and operator aliases.

## Technical design

### Runtime and boundaries

Use Python 3 with the standard library HTTP, JSON and SQLite modules, one local SQLite database, and HTML, CSS and JavaScript served from loopback. Start with a documented CLI taking an explicit data directory, then open the printed loopback URL in Chrome. Reject a data directory that cannot be opened without a clear indication of where writes would go. Open a new database only through an explicit initialization command that refuses an existing file. Use an explicit fictional-fixture command for demo data. Package static assets with the app. Browser requests use the same local origin, no additional origin allowance, and read-only GET routes. Mutation requests require JSON, an exact expected origin and a bounded body. There are no runtime downloads or third-party services.

| Interface | Behavior |
| --- | --- |
| Job queue and job details | Read jobs by state and stable bench label. Details include current revision, cycle, active holds, test attempts and ordered history. |
| Parts shelf | Read on-hand, reserved and available units plus the bench numbers holding them. A receipt adds positive inventory with a reference and a note. Manual adjustments and negative receipts are outside the first release. |
| Job actions | Create, diagnose, reserve, release, start repair, consume, request test, record test, hand off, reopen, or cancel by explicit allowed command. Responses include resulting revision and updated state. |
| End-of-cycle report | A read-only export of selected job cycles as JSON with stable job, event, part and test identifiers. It includes job state and recorded events in order, with a schema version. The inventory report includes each part balance and active reservations at the same transaction snapshot. |

### Job state and commands

Start a new job in **Intake** with cycle 1 and revision 1. A diagnosis records symptom, intended action and whether a part is needed. A completed diagnosis changes Intake to **Diagnosed**. A shift to **In repair** records work start. Diagnosed and In repair allow part holds and releases. Only In repair allows consumption. A no-parts repair may proceed without inventory activity. Ask the operator for a short repair note when requesting a test. A job enters **Testing** only after all remaining holds in its current cycle have been released or consumed.

A test attempt records a checklist result, a note and pass or fail. Fail returns the job to In repair and keeps the failed attempt. Pass moves the job to **Ready**. Handoff requires Ready, a confirmation and a recorded current-cycle pass. It changes Ready to **Handed off**. Ready and Handed off jobs can be reopened with a reason. Reopen changes the job to Intake, increments the cycle, and leaves all earlier events and test attempts visible. The new cycle needs its own diagnosis, repair and pass. A job in Intake, Diagnosed, In repair, Testing or Ready can be canceled with a reason. Cancellation moves to **Canceled** and releases all outstanding holds atomically. It preserves consumed inventory and completed observations. Handed off and Canceled are terminal except for the explicit Handed off reopen transition.

Every successful action that changes a job increments its revision once and creates one job event. Printing and report export leave revisions unchanged. Event order follows the job's monotonically increasing revision so histories remain stable when wall-clock timestamps are equal. Store UTC timestamps for display and never use them as the event ordering key. Reopening changes the current cycle while keeping its earlier cycle numbers on the history and test rows.

### Storage and stock invariants

| Record | Essential fields and constraints |
| --- | --- |
| Job | Stable ID, unique bench number, fictional label, current state, cycle, revision and created time. |
| Job event | Job ID, resulting revision, cycle, action, UTC timestamp, operator alias and a snapshot of the necessary action data. Unique job ID plus revision. Events have an insertion-only application path. |
| Part | Unique part number, label, nonnegative on-hand count and nonnegative reserved count. A row-level check enforces reserved less than or equal to on-hand. |
| Reservation | Job ID, cycle, part ID and positive quantity under a unique job-cycle-part key. Keep only active quantities here. Revision events preserve completed activity. |
| Stock movement | Monotonic movement ID, part ID, optional job and cycle, movement type, on-hand and reserved deltas, and stored resulting balances. Link job-associated movements to the job revision. |
| Test attempt | Job ID, cycle, attempt sequence, outcome, checklist and note. Each result links to its job event. |
| Applied command | Unique client-generated key, canonical request hash, command outcome and response. Keys cover both job and stock commands and persist across restart. |

Available units are on-hand minus reserved. Reserved units equal the sum of active reservations for that part, including holds across different jobs. Holds increase reserved and leave on-hand fixed. Releases decrease reserved and leave on-hand fixed. Consumption decreases on-hand, reserved and that job's active hold by the same quantity. A zero-quantity reservation is deleted. Receipts increase on-hand and leave reserved fixed. Cancellation releases each active hold and records the corresponding movements in the same commit as the job state change.

Example deltas per one unit:

| Command | On-hand change | Reserved change | Available change |
| --- | ---: | ---: | ---: |
| Receive | +1 | 0 | +1 |
| Reserve | 0 | +1 | −1 |
| Release | 0 | −1 | +1 |
| Consume reserved | −1 | −1 | 0 |

Enforce permitted state, revision, integer bounds, unique identifiers and part constraints before writing. At the end of each write transaction assert reservation totals and movement arithmetic for every affected part. An independent offline consistency check replays the movement deltas from zero, compares stored balances per event, and checks the active-reservation sums against current balances. A failed invariant aborts the command and leaves all rows in their previous state.

### Concurrency, retry and recovery

Use a separate database connection per request with foreign-key enforcement enabled on each connection. Start a short `BEGIN IMMEDIATE` transaction before reading mutable job or part state for a write. Inside it, look for the command key first. For a matching stored request hash return the stored response. A reused key with a different request returns a conflict. For an unseen key, require the submitted job revision, validate the current state and available quantity, apply the guarded increments, add the relevant events, store the response, and commit. Reserve must use an availability predicate on the update, and only succeed if the guarded update changed the intended row. Never split stock updates and history across commits. This also ensures a successful request that lost its network response safely replays after restart. A rejected command creates no state change, event, or stored success key. [SQLite transaction behavior](https://sqlite.org/lang_transaction.html) · [SQLite foreign-key enforcement](https://sqlite.org/foreignkeys.html)

Keep a short busy timeout and return a retryable response when the database remains busy. For an outdated job revision show the latest status and retain the entered text so the operator can review it. For two valid jobs competing for one available part, one holds it and the other sees a stock conflict. A job with a stale revision cannot update stock. Use a single read transaction to construct a report spanning multiple tables. If the app fails while writing, restart against the existing data directory and show the recorded state. A missing response is retried with the same key. An operator can refresh a stale job and intentionally submit a revised command with a new key.

Capabilities to verify before development include `python3`, `sqlite3` through Python, Chrome, and local filesystem access in the target environment. Keep JSON requests at or below 32 KiB, note fields at or below 500 characters, part quantities between 1 and 9,999 per command, and part counts capped at 100,000. Paginate queue and history at 50 rows. Limit the report to one job number or at most 100 jobs per export. Validate limits server-side and explain each failed action in text.

## Original verification fixtures

All labels below are invented. Seed one unit of **P-01 Fuse insert** as a receipt with a stock movement. Create **RB-A Table lamp** and **RB-B Practice radio** in Intake at revision 1 and diagnose both at revision 2. Both diagnoses need P-01. Test cases use fixed command keys and a fake clock. Timestamp duplicates do not affect ordering.

| Step | Expected outcome | On-hand | Reserved | Available |
| --- | --- | ---: | ---: | ---: |
| Seed receipt | P-01 has one unit. | 1 | 0 | 1 |
| A reserves and the same command is replayed | A has one active hold and one reserve event at revision 3. Replay returns the original response. | 1 | 1 | 0 |
| B tries to reserve | Insufficient stock. B stays Diagnosed at revision 2 with no new movement or event. | 1 | 1 | 0 |
| A starts repair and consumes its hold | Start is A revision 4. Consume is A revision 5. The hold is cleared. | 0 | 0 | 0 |
| A requests test, records fail, requests again and records pass | A advances through revisions 6, 7, 8 and 9. The failed attempt remains present. A is now Ready. | 0 | 0 | 0 |
| A is handed off and reopened | Handoff is A revision 10. Reopen is A revision 11, Intake, cycle 2. Both cycle 1 tests and its handoff are still visible. Handoff is denied until the new cycle passes its own test. | 0 | 0 | 0 |
| Receive two units and reserve one for B | B reaches revision 3. The receipt and reserve each have one movement. | 2 | 1 | 1 |
| Cancel B | B reaches revision 4 and its active hold is released. A's earlier consumption is preserved. | 2 | 0 | 2 |

The exact movement types are receipt, reserve, consume, receipt, reserve and release-on-cancel. A has eleven job events and B has four. A rejected command with a changed body under an existing key or a stale revision adds no event and leaves the same totals. A separate test resets to the state after both diagnoses and races independent SQLite connections for one unit. Either may win. After both settle, exactly one succeeds, one receives a conflict, one active reservation exists and the combined job event count is five. If the losing connection first receives a busy response, repeat its same command after the winner commits and require the stock conflict.

For recovery, interrupt a test process before committing a reservation, restart, and verify the shelf, job revision and event list are unchanged. Interrupt response delivery after committing a different fixture command, restart, replay it using the original key, and verify one successful event and one stock movement. Compare job history and movement bytes with independently written expected values, then verify visible counts and statuses in a real local Chrome session. These are planned acceptance checks. Only the fixture expectations are calculated here.

## Epic · Run one repair bench with reliable parts and handoff history

Deliver a single offline bench workflow that handles scarce stock, failed tests, handoff and a returned item. The estimated implementation and verification effort is **14–21 engineering hours**. Start RB-01, then build the state machine and the parts transaction in parallel against its schema contract. Bring them together in RB-04. Fold those contracts into RB-05 and close the release through RB-06. Treat the restartable intake/diagnosis path as the first durable milestone. Inventory disputes, repair outcome history and integrated demo evidence are later gates.

### RB-01 · Open the local bench and persist intake

**Estimate.** 2–3 hours. **Dependencies.** None.

As an intake volunteer, I can enter a fictional item and find the same job after restarting the bench.

- **RB-01-A.** Start the local Chrome UI from an empty application directory using the documented command and give a new item a stable bench number at cycle 1, revision 1.
- **RB-01-B.** Restart the local process. The newly created job, its Intake state and one creation event remain visible. Reject a blank label or too-long note without creating an item.
- **RB-01-C.** Pin command request and response shapes, revision semantics, transaction boundaries and an original deterministic fixture. Show the new job in the queue using keyboard-only navigation.

### RB-02 · Enforce the repair state machine and cycle history

**Estimate.** 2–3 hours. **Dependencies.** RB-01.

As a bench technician, I can see which action is allowed and understand how the item reached its current state.

- **RB-02-A.** Transition Intake through Diagnosed and In repair with a recorded reason. Reject starting repair from Intake, duplicate test completion and handoff from Testing.
- **RB-02-B.** Record a fail and a later pass as separate test attempts. Restore the timeline in revision order after restart. Return to In repair after failing and reach Ready after passing.
- **RB-02-C.** Reopen a handed-off fixture. Cycle increments without erasing test attempts or the previous handoff. Require a new diagnosis and successful test before the next handoff.

### RB-03 · Reserve and account for scarce parts atomically

**Estimate.** 3–5 hours. **Dependencies.** RB-01.

As a technician, I can reserve the last available spare for one job and trust the shelf display when another tab tries to reserve it.

- **RB-03-A.** Test the exact receive, reserve, release and consume deltas, partial hold use and active totals. Reject zero, negative and over-limit quantities and consumption without a sufficient hold.
- **RB-03-B.** Use independent connections to race two jobs for one part. After retrying any busy response, obtain one success and one insufficient-stock conflict with one active hold and one reserve movement.
- **RB-03-C.** Replay a successful command key across restart. Receive the stored response, keep one movement, and reject a changed request under that key without modifying state.

### RB-04 · Integrate cancellation, stale revisions and recovery

**Estimate.** 2–3 hours. **Dependencies.** RB-02 and RB-03.

As the bench operator, I can cancel an active job or recover from an interrupted request without losing track of committed stock or actions.

- **RB-04-A.** Deny entering Testing while any hold remains. Cancel a fixture job with holds and release them all in one transaction while preserving consumed parts.
- **RB-04-B.** Send a stale request from a second tab while a part is in stock. Return a revision conflict without taking it, and let the operator review the latest information without dropping the form text.
- **RB-04-C.** Run the two interrupted-request fixture cases. Independently replay the surviving stock movements, assert active sums and verify exact revision and movement counts.

### RB-05 · Build the complete bench browser workflow and report

**Estimate.** 3–4 hours. **Dependencies.** RB-04.

As an intake or handoff volunteer, I can tell what the next action is and review the complete item history without reading the database.

- **RB-05-A.** Demonstrate intake, diagnosis, shelf availability, reservation, test fail and retest, handoff, reopen and cancellation. Use appropriate visible actions and a text explanation for a stock conflict.
- **RB-05-B.** Show current-cycle testing separately from historical results, keep states labeled for keyboard and screen-reader use, and report an invalid entry next to the responsible field.
- **RB-05-C.** Export a versioned report and confirm previous cycles, test outcomes, quantities and event revisions against an independently constructed fixture. Opening or exporting the report does not change job revisions.

### RB-06 · Verify the release from a clean offline workspace

**Estimate.** 2–3 hours. **Dependencies.** RB-05.

As the bench maintainer, I can initialize the project and reproduce its important results without a remote service.

- **RB-06-A.** Follow the documented startup steps with internet access disabled. Verify that the browser invokes only loopback services and records actual Python, SQLite and Chrome versions.
- **RB-06-B.** Use two tabs to run the last-spare fixture and the cancel path, then restart and confirm the expected report numbers and states with the exact command and observed results recorded.
- **RB-06-C.** Verify the end-to-end job and reopened cycle from keyboard navigation. Record pass/fail, any unsupported setup facts, and one exported fictional demo report.

## Scope decisions and follow-on work

The default scenario is one shared bench on one Linux machine. Confirm whether a later release needs storage locations or expense reporting before adding those concepts to the product. Future design work can add policy for warranty returns, scheduled parts reuse and a separately designed backup workflow. The first epic is complete at state, inventory and history reconciliation in the local browser.
