# Plan

   Project name: `WALDO` (Wall-Aided Lateral Drift Offsetting). Repo and folder: `waldo`.
Method: Agile, scoped sprints. One sprint at a time. A sprint is not done until its Definition of Done (DoD) is met.
Companion files: `Progress.md` (what happened), `RequirementsAndSetup.md` (what must exist), `Rules.md` (how we work), `TechStack.md` (what we use and why).
Deeper detail: `docs/PROJECT_BRIEF.md` (rationale), `docs/EXPERIMENTS.md` (experiment spec, source of truth for metrics).

---

## 1. Goal

- Reduce odometry drift of a wheeled robot executing a straight geometric subgoal in a featureless corridor, by using the depth camera to measure lateral offset and heading error from the two walls.
- Show, in simulation, how much it helps and where it stops helping.
- Source of the gap: arXiv:2609.14297v1 (IIT Kanpur, 13 Sep 2026), which says geometric targets can add drift in a featureless corridor and RGB-D data does not constrain them.

## 2. Scope

- In scope:
  - Straight corridor, one subgoal up to 10 m (the paper's cap).
  - Injected drift: wheel-scale mismatch, lateral skid, random noise.
  - Simulated depth with optional Gaussian noise.
  - Baselines: `B1` odometry only, `B2` odometry + simulated gyro heading.
  - Methods: `C_lat`, `C_head`, `C_both`.
- Out of scope (parking lot, do not start):
  - LLM parsing, YOLO, ESANet, person re-ID, turns/junctions, moving obstacles, lighting/reflection noise, real hardware, ROS/Gazebo.

## 3. Success criteria (project level)

- `python src\run_experiments.py` then `python src\plot_results.py` regenerate all results and figures from scratch.
- Baseline drift matches the analytic formula `y ~ L^2 * d_eps / (2b)` at small drift.
- Results reported for 30 trials per condition with paired statistics.
- Limitations section states: injected drift, cleaner-than-real depth, simulation only.
- Conclusions are stated against the fairer `B2` baseline, even if the result is weaker.

## 4. Sprint roadmap

| Sprint | Name | Indicative effort | Branch | Tag on completion |
|---|---|---|---|---|
| 0 | Foundations: repo, env, novelty check, docs | 2 days | `sprint-0-foundations` | none |
| 1 | World, drift model, metrics, analytic check | 3 days | `sprint-1-world-drift` | `v0.1.0` |
| 2 | Perception: depth to wall fits | 4 days | `sprint-2-perception` | `v0.2.0` |
| 3 | Controller and closed loop, gain tuning | 3 days | `sprint-3-controller` | `v0.3.0` |
| 4 | Experiment sweep, ablation, plots | 4 days | `sprint-4-experiments` | `v0.4.0` |
| 5 | Analysis and stress tests | 2 days | `sprint-5-analysis` | `v0.5.0` |
| 6 | Write-up, docs polish, release | 3 days | `sprint-6-release` | `v1.0.0` |

- Effort adds up to about 3 weeks, matching the proposal. Calendar dates are filled in `Progress.md` as each sprint starts, because the real deadline is not fixed in these files yet.

## 5. Sprint details

### Sprint 0: Foundations (status: done 2026-10-20, started 2026-10-05; novelty check carried forward)
- Tasks:
  - [x] Draft project docs (README, brief, environment, experiments, references)
  - [x] Write the proposal (markdown and Word versions)
  - [x] Create the five working docs (this set)
  - [x] Choose the final project name
  - [x] Create the GitHub repo; add `.gitignore` and `.gitattributes`; first commit on `main`
  - [x] Create the conda env from `environment.yml`; select the interpreter in VS Code
  - [x] Run `src\smoke_test.py` (headless depth render works)
  - [x] Time one depth render to budget total sweep runtime
  - [x] Verify assumed parameters: wheel base `b`, camera FOV, camera height, Husky footprint
  - [ ] Novelty check: run the searches listed in `docs/REFERENCES.md`; write positioning notes
       - Deferred on 2026-10-20 by choice. Must be done before Sprint 6 (the report) and before any prior-work claim is written.
  - [x] Add `ruff` config; confirm `ruff check` and `ruff format` run
  - [x] Open GitHub Issues for Sprint 1 tasks
- DoD: smoke test prints a depth image shape and plausible metric range; repo is on GitHub; `Progress.md` has the Sprint 0 entry. (Novelty notes carried forward, see deferral above.)

### Sprint 1: World, drift model, metrics (status: done 2026-10-25, started 2026-10-20; tag v0.1.0)
- Tasks:
  - [x] `config.py`: every constant in one place.
  - [x] `world.py`: corridor from box walls, robot body, depth render, depth-buffer to metric conversion.
  - [x] `drift.py`: TRUE pose vs ODOM pose, wheel-scale mismatch, lateral skid, noise, simulated gyro (for `B2`).
  - [x] `metrics.py`: lateral error, heading error, collision, the paper's drift metric, success.
  - [x] `run_trial.py` for `B1` only (no correction yet).
  - [x] Tests: depth conversion, analytic drift check, determinism.
  - [x] Watch one trial in `p.GUI`.
  - [x] `debug_gui.py`: GUI view of TRUE vs ODOM path, via the `on_step` hook in `run_trial.py`.
- Why `B2`'s gyro model is built now: adding it later means re-running everything. Building it here lets Sprint 4 run all modes in one sweep. (This differs from `docs/PLAN.md`, which put `B2` late; this file supersedes it.)
- DoD:
  - [x] `B1` lateral error matches `L^2 * d_eps / (2b)` within a few percent at small `d_eps`, no noise.
  - [x] Same seed gives identical results on two runs.
  - [x] Same seed gives the same noise sequence across modes (paired comparison).
  
### Sprint 2: Perception
- Tasks:
  - `perception.py`: depth to 3D points, drop floor/ceiling by height, project to ground plane.
  - Own numpy RANSAC line fit per wall (walls run along the forward axis, so `y = a*x + b` is well-conditioned).
  - Outputs: lateral offset, heading error, confidence.
  - Offline test on rendered frames from a grid of known poses.
  - Degradation curve vs depth noise.
  - Choose the confidence threshold from the tuning seeds and record it in `docs/EXPERIMENTS.md`.

- Targets (our choice, state in report): offset error under 0.05 m and heading error under 2 degrees at zero depth noise.
- Camera is at 0.4 m height with no tilt (our choice); readings under 0.52 m are discarded (D455 minimum depth).
- DoD: targets met on the pose grid; tests pass; `ruff check` clean; degradation curve saved; confidence threshold recorded.
  

### Sprint 3: Controller and closed loop
- Tasks:
  - `control.py`: PD correction on lateral offset and heading, output clipping, low-confidence fallback to odometry.
  - Extend `run_trial.py` to all modes (`B1`, `B2`, `C_lat`, `C_head`, `C_both`).
  - Tune gains on seeds 1000 to 1099 only.
- DoD: `C_both` beats `B1` on final absolute lateral error at `d_eps = 1%` on tuning seeds; no visible oscillation in the trajectory plot; no wall collision at 1%.

### Sprint 4: Experiments
- Tasks:
  - `run_experiments.py` with spawn-safe multiprocessing, writing `results\raw.csv`.
  - Main sweep: modes x `d_eps` x 30 seeds (0 to 29).
  - Depth-noise sweep at a fixed drift level.
  - Ablation is covered by the modes `C_lat`, `C_head`, `C_both`.
  - `plot_results.py`: all figures listed in `docs/EXPERIMENTS.md`.
- DoD: two commands regenerate `raw.csv` and all figures; row counts match the experiment spec; total runtime recorded in `Progress.md`.

### Sprint 5: Analysis and stress tests
- Tasks:
  - Lateral-skid sweep; gyro-bias sweep for `B2`.
  - Optional: side-opening (doorway) test of the confidence gate.
  - Paired statistics, confidence intervals, collision-rate intervals.
  - Draft threats-to-validity list from what actually broke.
- DoD: conclusions are written against `B2`. If depth adds little over `B2`, that finding is stated plainly.

### Sprint 6: Write-up and release
- Tasks:
  - Report: problem and gap, method, setup, results, ablation, limitations, prior-work positioning.
  - README results section filled in; docs synced with code.
  - Clean repo, final tag `v1.0.0`, release notes.
- DoD: every claim in the report maps to a figure or table; a fresh clone plus the README steps reproduces the results.

## 6. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| PyBullet install fails on Windows | Blocks everything | conda-forge, Python 3.10/3.11; fallback MuJoCo or NumPy ray-casting |
| Depth rendering too slow for the sweep | Cannot finish 30 seeds x all conditions | Lower resolution, render at 5-10 Hz, shorten runs, time in Sprint 0 |
| TRUE and ODOM poses mixed up | Silently invalid results | Analytic check gate in Sprint 1; separate variable names; tests |
| Correction oscillates | Poor results | Lower gains, clip output, check frame conventions |
| Depth adds nothing over `B2` | Weaker story | Report honestly; focus on cross-track drift and gyro-bias regimes |
| Novelty check finds close prior work | Positioning changes | Reframe as application and measurement, not method |
| Scope creep | Misses deadline | Parking lot; no new features inside a sprint |

## 7. Parking lot (ideas, not committed)

- Turns and junctions; multi-subgoal missions.
- Lighting and reflective-surface noise (the paper's other stated gap).
- MuJoCo or lidar-slice cross-check of the same experiment.
- Real-data replay if any D455 corridor recordings become available.
