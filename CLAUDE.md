# CLAUDE.md: rules for AI assistants in this repo

Read this first, then `docs/PROJECT_BRIEF.md` and `docs/EXPERIMENTS.md`.
- Project name: **WALDO** (Wall-Aided Lateral Drift Offsetting). Repo and folder: `waldo`.
---

## 1. What this project is (30-second version)

- Simulation-only mini project (Autonomous Systems course).
- Problem: odometry-only straight-line motion in a featureless corridor drifts sideways.
- Fix being tested: use the depth camera to fit both corridor walls, estimate lateral offset + heading error, and correct the controller.
- Compared against odometry-only baselines in PyBullet, across drift severity and depth noise.
- Source of the gap: arXiv:2609.14297v1 (IIT Kanpur). We isolate one limitation only.

## 2. Environment (fixed, do not change)

- OS: **Windows 11**. Shell: **PowerShell**. Editor: **VS Code**.
- Python 3.11 in conda env `corrdrift` (see `environment.yml`).
- Simulator: **PyBullet**. Libraries: numpy, scipy, pandas, matplotlib, tqdm.
- Do NOT introduce: ROS, ROS 2, Gazebo, Docker, WSL, CUDA, PyTorch, any LLM API. None are needed and several are painful on native Windows.

## 3. Coding style (strict)

- **Concise, flat, function-based code. No classes.**
  - Use plain functions and dicts. Pass state explicitly.
  - Reason: easier to read, easier to debug in VS Code, matches how the author writes.
- One responsibility per file (see layout in README). Keep each file short, ideally under ~150 lines.
- All tunable numbers live in `src/config.py` as module-level constants. No magic numbers elsewhere.
- Use `pathlib.Path` for every path. Never hard-code `C:\...` or use forward/back slash string concatenation.
- Seed every random source from the trial seed (`np.random.default_rng(seed)`). Never use the global RNG.
- NumPy vectorisation over Python loops when processing depth images or point sets.
- Add a short comment above each non-obvious line saying WHY, not WHAT.
- No type-hint overload, but add simple hints on function signatures where it helps readability.
- Print minimal progress (tqdm bar only). No noisy logging.

## 4. Windows-specific rules

- `multiprocessing` on Windows uses spawn. Every script that uses it MUST have `if __name__ == "__main__":` around the entry point.
- PyBullet in batch runs: `p.connect(p.DIRECT)` (headless). Use `p.GUI` only in debug scripts.
- Each worker process creates its own PyBullet client. Never share a client across processes.
- matplotlib in scripts: call `matplotlib.use("Agg")` before importing pyplot when only saving figures.
- Do not write outside the repo folder. Do not rely on OneDrive-synced paths.

## 5. Simulation design rules (do not break)

- The robot is **kinematic**: set its pose each step with `resetBasePositionAndOrientation`. PyBullet is used only for (a) rendering the depth camera, (b) collision queries. Reason: avoids tuning physics, keeps runs deterministic.
- Keep two poses separate at all times:
  - TRUE pose: what the simulator uses (affected by injected drift).
  - ODOM pose: what the controller believes (wheel-based, never sees the injected error).
  - Mixing them up silently invalidates every result.
- Depth buffer from PyBullet is non-linear. Always convert to metric depth with `z = far*near / (far - (far-near)*buf)` before use.
- Camera renders at ~10 Hz, not at the physics rate.
- Perception code must return a **confidence** value. Controller must fall back to odometry-only when confidence is low.

## 6. Experiment rules

- Metrics, conditions, trial counts and seeds are defined in `docs/EXPERIMENTS.md`. If code and doc disagree, fix the doc deliberately, never silently.
- Every trial writes one CSV row with the columns listed in `EXPERIMENTS.md`.
- Never hand-edit `results/raw.csv`. Regenerate it.
- Do not tune controller gains on the same seeds used for the final results. Tune on seeds 1000-1099, report on seeds 0-29 per condition.
- Report negative or null results honestly.

## 7. Honesty rules for write-ups and comments

- Never claim hardware validation.
- Always state that drift is injected and simulated depth is cleaner than real depth.
- Never call corridor centering novel. Call it a targeted application of a classical idea to a stated gap.
- Cite the source paper for the gap; do not paraphrase beyond what it says.

## 8. Notes and docs style

- Notes are written as **exhaustive, bullet-point explanations at undergraduate level**, with the reasoning shown, not just the conclusion.
- Prefer many short bullets over polished prose paragraphs.
- When adding a design decision, add a bullet explaining the alternative considered and why it was rejected.

## 9. Definition of done (project level)

- `python src\run_experiments.py` reproduces `results\raw.csv` from scratch.
- `python src\plot_results.py` reproduces every figure in the report.
- Analytical drift check from `EXPERIMENTS.md` section 6 passes for the baseline.
- Limitations section written and consistent with section 7 above.
