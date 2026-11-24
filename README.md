# Repair Bench Tracker

An offline repair desk for intake, parts reservations, verification and handoff.

This repository contains the plan for the first implementation epic and a runnable scaffold. There is no product behaviour yet.

- [Product requirements](docs/PROJECT-PLAN.md#product-requirements)
- [Technical design](docs/PROJECT-PLAN.md#technical-design)
- [Epic and implementation tickets](https://github.com/jortega0033/repair-bench-tracker/issues)

The first plan of phase 1 said 14–21 engineering hours. Its open tickets, with tests and review, add up to 65 to 110 hours; the whole program is larger and is described below. All figures are estimates.

Licensed under the [MIT License](LICENSE).

## Program goal

Turn the bench into a system that reasons about the device on it: own circuit simulator, fault isolation that chooses the cheapest next measurement, several offline benches that never promise the same part twice, and proven spare-part planning, with no numerical, solver, replication or search library.

The program is planned ([#42](https://github.com/jortega0033/repair-bench-tracker/issues/42)). Phase 1 is the current epic [#1](https://github.com/jortega0033/repair-bench-tracker/issues/1) and the only phase with tickets.

**Score.** Share of seeded faults in public benchmark circuits that are isolated to the right component within a stated measurement budget, and zero broken stock rules in a randomised fault campaign judged by an independent checker.

| Phase | Content | Hours (rough) | Issue |
|---|---|---|---|
| 1 | The current epic and its tickets | 65 to 110 | [#1](https://github.com/jortega0033/repair-bench-tracker/issues/1) |
| 2 | Devices and circuit simulation | 150 to 260 | [#43](https://github.com/jortega0033/repair-bench-tracker/issues/43) |
| 3 | Fault isolation | 150 to 260 | [#44](https://github.com/jortega0033/repair-bench-tracker/issues/44) |
| 4 | Several benches offline | 130 to 230 | [#45](https://github.com/jortega0033/repair-bench-tracker/issues/45) |
| 5 | Spare-part planning | 110 to 190 | [#46](https://github.com/jortega0033/repair-bench-tracker/issues/46) |
| 6 | Repair knowledge | 110 to 190 | [#47](https://github.com/jortega0033/repair-bench-tracker/issues/47) |

About 720 to 1240 engineer hours in total: rough estimates, not measurements. The numbers in the score and the finish lines are targets until a run shows them. Only phase 1 has tickets to work; the sub-issues of a later phase are written when it starts. No single session is expected to reach the end.
