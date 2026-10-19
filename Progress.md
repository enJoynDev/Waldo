# Progress

Running log. One entry per sprint, newest at the bottom of the log section.
Rule: a sprint entry is written, and GitHub is updated (commit + push + PR merge), before the next sprint starts. See `Rules.md`.

---

## 1. Status board

| Sprint | Name | Status | Start | End | Tag |
|---|---|---|---|---|---|
| 0 | Foundations | In progress | 2026-10-05 | | none |
| 1 | World, drift model, metrics | Not started | | | `v0.1.0` |
| 2 | Perception | Not started | | | `v0.2.0` |
| 3 | Controller and closed loop | Not started | | | `v0.3.0` |
| 4 | Experiments | Not started | | | `v0.4.0` |
| 5 | Analysis and stress tests | Not started | | | `v0.5.0` |
| 6 | Write-up and release | Not started | | | `v1.0.0` |

Status values: Not started, In progress, Blocked, Done.

## 2. Current focus

- Sprint 0: finish environment setup and the novelty check.
- Next concrete action: choose the final project name, create the GitHub repo, run the smoke test.

## 3. Decisions log

Each decision: what, why, alternative rejected.

- **2026-10-05: Isolate one gap only (corridor drift).**
  - Why: the source paper also names lighting/reflection noise as a limitation, but that needs a segmentation network and may not reproduce in simulation.
  - Rejected: lighting/reflection gap (more infrastructure, baseline failure may not appear in the simulator).
- **2026-10-05: Simulation-only, PyBullet, native Windows 11.**
  - Why: no hardware available; Gazebo and ROS 2 are Linux-first and this project does not need a ROS graph.
  - Rejected: Gazebo + ROS 2 (fragile on native Windows), WSL (extra layer, more setup).
  - Fallbacks if PyBullet fails: MuJoCo, or pure NumPy ray-casting.
- **2026-10-05: Add a gyro-aided baseline `B2`.**
  - Why: the source paper's robot also has an IMU, so an encoder-only baseline would exaggerate the benefit of the fix.
- **2026-10-05: Kinematic robot, PyBullet used only for depth rendering and collision queries.**
  - Why: avoids tuning contact physics, keeps runs deterministic.
  - Rejected: full wheel-ground physics (slow, hard to control drift magnitude).
- **2026-10-08: Build `B2` gyro model in Sprint 1, not later.**
  - Why: lets Sprint 4 run every mode in one sweep. Supersedes the ordering in `docs/PLAN.md`.
- **2026-10-08: Adopt the five-file working-docs set (Plan, Progress, RequirementsAndSetup, Rules, TechStack), same as Cadenza.**
  - Why: same workflow, reattached at the start of each session.
- **2026-10-19: Project name is WALDO (Wall-Aided Lateral Drift Offsetting); repo and folder `waldo`.**
  - Why: short, memorable, describes what it does (wall-aided, lateral drift).
  - Rejected: CORD, DriftLock, Centerline.
  
## 4. Assumptions still to verify

| Assumption | Value used | Verify against | Status |
|---|---|---|---|
| Wheel base `b` | 0.55 m | Husky A200 datasheet | Open |
| Camera horizontal FOV | 87 degrees | RealSense D455 datasheet | Open |
| Camera height | 0.4 m | Husky + D455 mounting in the paper's figures | Open |
| Robot footprint | 0.99 m x 0.67 m | The paper's text (988 mm x 670 mm) | Taken from paper |
| Corridor width | 2.0 m | Our choice | Fixed |
| Success threshold | 0.15 m lateral | Our choice | Fixed |
| Paper drift safety radius `d_s` | 0.2 m | Our choice | Fixed |

## 5. Open questions

- Real course deadline, which decides how Sprint 4 to 6 are compressed.
- Does the course want a written report, a demo, a viva, or all three?
- Does the course expect a ROS/Gazebo demo? If yes, plan an optional port after Sprint 4.

## 6. Sprint log

### Sprint 0: Foundations (in progress)

- Started: 2026-10-05
- Done so far:
  - Chose the project: depth-based corridor drift correction (gap 1 of arXiv:2609.14297).
  - Wrote README, CLAUDE.md, environment.yml, and docs: PROJECT_BRIEF, ENVIRONMENT, PLAN, EXPERIMENTS, REFERENCES.
  - Wrote the proposal in markdown and Word.
  - Wrote the five working docs (this set).
- Remaining: see Sprint 0 task list in `Plan.md`.
- Blockers: none.
- Commit / PR: not yet created.

<!-- Template for each new sprint entry:

### Sprint N: Name (status)

- Started: YYYY-MM-DD
- Ended: YYYY-MM-DD
- Branch: sprint-N-name
- What was built:
  -
- Decisions made (with reasons):
  -
- Tests run and results:
  -
- Numbers worth remembering (runtime, error values, etc.):
  -
- Problems hit and how they were fixed:
  -
- Docs updated:
  -
- Commit / PR / tag:
- Next sprint starts with:
-->
