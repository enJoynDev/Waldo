# Plan

Roughly 3 weeks. Compress or stretch to match your real deadline.
Each phase has a "done when" so you can tell if you are actually finished.

---

## Phase 0: Setup and novelty check (Days 1-2)

- [ ] Create `C:\Users\Joy Mandal\Desktop\WALDO\waldo`, copy these docs in, open folder in VS Code.
- [ ] Create the conda env, select the interpreter, run `src\smoke_test.py`.
- [ ] Time one depth render to estimate total sweep runtime.
- [ ] Read the source paper's corridor/drift passages again and note exact wording for citation.
- [ ] **Novelty check (still pending).** Search for:
  - "depth-based corridor centering wheeled robot odometry drift"
  - "wall following RGB-D heading lateral offset correction mobile robot"
  - "mapless navigation corridor drift correction depth camera 2025 2026"
  - "arXiv 2609.14297" citations / follow-ups
- [ ] Write 3-5 bullets: what prior work exists, and how this project is positioned relative to it.
- Done when: smoke test prints a depth shape, and the novelty notes are written in `docs/REFERENCES.md`.

## Phase 1: World and drift model (Days 3-5)

- [ ] `world.py`: build corridor (box walls), robot body, depth render + metric conversion.
- [ ] `drift.py`: TRUE pose vs ODOM pose, with wheel-scale mismatch, lateral skid, noise.
- [ ] `metrics.py`: lateral error, heading error, collision, paper drift metric.
- [ ] Run `B1` (no correction) with no noise.
- [ ] **Analytic check:** simulated lateral error matches `L^2 * d_eps / (2b)` at small `d_eps` (see `EXPERIMENTS.md` section 6).
- Done when: baseline drift is reproducible and matches the formula.

## Phase 2: Perception (Days 6-9)

- [ ] `perception.py`: depth -> 3D points -> remove floor/ceiling -> ground-plane projection.
- [ ] RANSAC line fit per wall, with confidence.
- [ ] Test offline on saved depth frames with KNOWN poses: estimated offset/heading should match ground truth.
- [ ] Add depth noise and see how estimates degrade.
- Done when: offset error under a few centimetres and heading error under a couple of degrees at zero depth noise.

## Phase 3: Controller and integration (Days 10-12)

- [ ] `control.py`: PD correction, output clipping, low-confidence fallback.
- [ ] `run_trial.py`: full closed loop returning one metrics dict.
- [ ] Tune gains on seeds 1000-1099 only.
- [ ] Watch one trial in `p.GUI` to confirm behaviour looks sensible.
- Done when: `C_both` clearly beats `B1` at `d_eps = 1%` on tuning seeds.

## Phase 4: Experiments (Days 13-16)

- [ ] `run_experiments.py` with multiprocessing (spawn-safe) writing `results\raw.csv`.
- [ ] Run main sweep: modes x `d_eps` x 30 seeds.
- [ ] Run depth-noise sweep and ablation.
- [ ] `plot_results.py`: all figures in `EXPERIMENTS.md` section 10.
- Done when: `raw.csv` and figures regenerate from scratch with two commands.

## Phase 5: Fairness and extension (Days 17-18)

- [ ] Add `B2` (gyro-aided baseline) and re-run the affected conditions.
- [ ] Optional: side-opening stress test or lateral-skid sweep.
- [ ] Honest read of results: where does depth help, where does it not?
- Done when: conclusions hold against the fairer baseline, or the report says they do not.

## Phase 6: Write-up (Days 19-21)

- [ ] Problem and gap, cited to the source paper.
- [ ] Method (perception + control), with equations.
- [ ] Experimental setup, metrics, statistics.
- [ ] Results and ablation.
- [ ] Limitations: injected drift, clean depth, matte walls, sim-only, single corridor.
- [ ] Prior-work positioning from Phase 0 notes.
- Done when: every claim in the report maps to a figure or table.

## Risks and mitigations

- **PyBullet fails to install on Windows:** use conda-forge, Python 3.10/3.11; fallback to MuJoCo or NumPy ray-casting.
- **Depth rendering too slow for 30 trials x many conditions:** lower resolution, render at 5-10 Hz, reduce workers' memory, shorten corridor.
- **Baseline does not drift as the formula predicts:** pose bookkeeping bug (TRUE vs ODOM mixed). Fix before anything else.
- **Correction oscillates:** gains too high or perception latency ignored. Lower `k_lat`, add clipping, check that estimates are in the correct frame.
- **No improvement over `B2`:** a legitimate finding. Report it, and focus the discussion on cross-track drift and gyro-bias regimes.
- **Scope creep (turns, LLM, clutter):** do not. Park it in "future work".
