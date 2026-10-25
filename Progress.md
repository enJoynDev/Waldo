# Progress

Running log. One entry per sprint, newest at the bottom of the log section.
Rule: a sprint entry is written, and GitHub is updated (commit + push + PR merge), before the next sprint starts. See `Rules.md`.

---

## 1. Status board

| Sprint | Name | Status | Start | End | Tag |
|---|---|---|---|---|---|
| 0 | Foundations | Done | 2026-10-05 | 2026-10-20 | none |
| 1 | World, drift model, metrics | Done | 2026-10-20 | 2026-10-25 | `v0.1.0` |
| 2 | Perception | Not started | | | `v0.2.0` |
| 3 | Controller and closed loop | Not started | | | `v0.3.0` |
| 4 | Experiments | Not started | | | `v0.4.0` |
| 5 | Analysis and stress tests | Not started | | | `v0.5.0` |
| 6 | Write-up and release | Not started | | | `v1.0.0` |

Status values: Not started, In progress, Blocked, Done.

## 2. Current focus

- Sprint 1: world, drift model, metrics, analytic check.
- Next concrete action: create branch `sprint-1-world-drift` and start with issue #1 (`config.py`).

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
- **2026-10-19: The corridor in `world.py` is fully enclosed, with a ceiling.**
  - Why: PyBullet's depth buffer returns NaN for rays that hit nothing (seen in an earlier test with open-top walls), and perception must never see NaN.
  - Rejected: replacing NaN after rendering (hides real no-return pixels).
- **2026-10-19: PyBullet gets the vertical FOV, converted from the 87 degree horizontal one.**
  - Why: `computeProjectionMatrixFOV` takes the vertical FOV; passing 87 would silently widen the horizontal view.
  - Rejected: passing 87 directly.
- **2026-10-19: Default wheel noise `sigma_w` is 1%, never zero in the main sweep.**
  - Why: the simulation is deterministic, so with zero noise all 30 seeds would give identical results.
  - Rejected: `sigma_w = 0` (fake confidence intervals).
- **2026-10-19: Gyro defaults for `B2`: bias 0.1 deg/s, noise 0.05 deg/s.**
  - Why: our own choice for a plausible MEMS gyro; swept in Sprint 5.
  - Rejected: no gyro bias (would make `B2` unrealistically good).
- **2026-10-19: Retired `docs/PLAN.md` in favour of `Plan.md`.**
  - Why: two plan files disagreed (`B2` timing); one source of truth.
  - Rejected: keeping both in sync by hand.
- **2026-10-20: Novelty check deferred; Sprint 0 closed without it.**
  - Why: it is reading and writing only, and nothing in Sprints 1 to 5 depends on it.
  - Rejected: holding Sprint 0 open (it would block all code work).
  - Condition: the notes in `docs/REFERENCES.md` are written before Sprint 6, and nothing is cited as read until it is.

## 4. Assumptions still to verify

| Assumption | Value used | Verify against | Status |
|---|---|---|---|
| Wheel base `b` | 0.55 m | Husky A200 datasheet | Verified |
| Camera horizontal FOV | 87 degrees | RealSense D455 datasheet | Verified |
| Camera height | 0.4 m | Husky + D455 mounting in the paper's figures | Our choice (not given in the paper) |
| Robot footprint | 0.99 m x 0.67 m | The paper's text (988 mm x 670 mm) | Taken from paper |
| Corridor width | 2.0 m | Our choice | Fixed |
| Success threshold | 0.15 m lateral | Our choice | Fixed |
| Paper drift safety radius `d_s` | 0.2 m | Our choice | Fixed |
| Camera minimum depth | 0.52 m | D455 spec; perception discards closer readings | Verified |
| Default wheel noise sigma_w | 1% per 0.1 s | Our choice | Fixed |
| Gyro bias / noise (B2) | 0.1 / 0.05 deg/s | Our choice, not from a datasheet | Fixed |

## 5. Open questions

- Real course deadline, which decides how Sprint 4 to 6 are compressed.
- Does the course want a written report, a demo, a viva, or all three?
- Does the course expect a ROS/Gazebo demo? If yes, plan an optional port after Sprint 4.

## 6. Sprint log

### Sprint 0: Foundations (done)

- Started: 2026-10-05
- Ended: 2026-10-20
- Done so far:
  - Conda env `corrdrift` built from `environment.yml`; versions recorded in `TechStack.md`.
  - Repo `enJoynDev/Waldo` created; `.gitignore`, `.gitattributes`, `pyproject.toml` (ruff and pytest) added.
  - Smoke test passes: shape (240, 320), 0 NaN pixels, centre pixel 3.000 m, 36.7 ms per frame at 320x240.
  - Docs synced and renamed to WALDO; `docs/EXPERIMENTS.md` parameters filled in.
  - Sprint 1 issues #1 to #7 opened.
- Remaining (carried forward): novelty notes in `docs/REFERENCES.md`. See the decision of 2026-10-20.
- Branch: `sprint-0-foundations`.

### Sprint 1: World + drift model (2026-10-20 to 2026-10-25) — Done

**Delivered:** `config.py`, `world.py`, `drift.py`, `metrics.py`, `run_trial.py`, `debug_gui.py`, 39 tests (issues #1–#7).

**Results**
- Analytic drift check (y ≈ L²·d_eps/2b): simulated 0.907 m vs analytic 0.909 m.
- Same seed gives the same result. Noise is paired across modes (pre-drawn per seed).
- B1, seed 0, no noise:

| d_eps | final y (m) | distance (m) | outcome |
|---|---|---|---|
| 0 | 0.000 | 10.00 | success |
| 0.0025 | +0.227 | 10.00 | fail (>0.15 m) |
| 0.005 | +0.454 | 9.99 | fail |
| 0.01 | collides | 8.08 | collision |
| 0.02 | collides | 5.58 | collision |

- Noise-only spread (d_eps = 0): 0.100 m lateral, 1.02° heading.
- Timing: depth render 9.2 ms per frame (160×120); B1 trial 68 ms.

**Decisions**
- Collisions use `getClosestPoints` (gap ≤ 0), because `getContactPoints` skips static-static pairs.
- The corridor is closed (floor + ceiling), because PyBullet returns NaN depth for rays that hit nothing.
- Noise is pre-drawn per seed from `SeedSequence(seed).spawn(3)`. Wheel noise is redrawn every 0.1 s.
- The robot body is invisible. The GUI uses a stand-in marker.
- `on_step` hook added to `run_trial` for the debug GUI.
- `fit_fail_frac` is NaN for B1.
- `success` is cast to `bool` in `metrics.py`.

**Honesty notes:** drift is injected, not measured from hardware. Simulated depth is cleaner than real depth.
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
