# Rules

How this project is run. These apply to every session, every sprint, and to any AI assistant helping with the work.
Reattach this file (with the other four working docs) at the start of each session.

---

## 1. Process rules

- **Agile SDLC in scoped sprints.** One sprint at a time. No starting the next sprint before the current one is done.
- **Definition of Done for a sprint.** A sprint is done only when ALL of these hold:
  - Code is committed and pushed.
  - Code runs from a clean state.
  - Tests for the sprint pass.
  - Docs are updated (see section 5).
  - `Progress.md` has the sprint entry.
- **GitHub is updated after every sprint.** Commit, push, merge the PR, tag if the sprint has a tag.
- **Feature branch per sprint.** Branch name `sprint-N-short-name`. Merged into `main` through a self-reviewed pull request. Read your own diff before merging.
- **GitHub Issues track sprint tasks.** One issue per task; close it from the PR.
- **No scope creep.** New ideas go in the parking lot in `Plan.md`. They do not enter a running sprint.
- **Every significant decision is briefly reasoned and logged** in `Progress.md` with the alternative rejected and why.

## 2. Coding rules

- **All coding happens in VS Code.** Code lives in files, never only in a terminal session or a chat window.
- **Style: concise, flat, function-based.** No classes. Plain functions, dicts and arrays. Pass state explicitly.
- One responsibility per file. Aim for files under about 150 lines.
- Every tunable number lives in `src\config.py`. No magic numbers elsewhere.
- Use `pathlib.Path` for all paths. Never hard-code `C:\...`.
- Seed every random source from the trial seed using `np.random.default_rng(seed)`. Never use the global RNG.
- Vectorise with NumPy when handling depth images or point sets.
- Comments explain WHY, not WHAT.
- **Lint and format before every commit:** `ruff check .` and `ruff format .`
- Add tests for anything that can silently produce wrong numbers: depth conversion, drift model, pose bookkeeping, metrics.

## 3. Simulation-correctness rules (do not break)

- Keep TRUE pose and ODOM pose as separate variables everywhere. Mixing them silently invalidates every result.
- The robot is kinematic. PyBullet is used only for depth rendering and collision queries.
- Convert the PyBullet depth buffer to metric depth before any use: `z = far*near / (far - (far-near)*buf)`.
- Perception must output a confidence value. The controller falls back to odometry when confidence is low.
- Batch runs use `p.connect(p.DIRECT)`. Use `p.GUI` only in debug scripts.
- Every runnable script that uses multiprocessing has an `if __name__ == "__main__":` guard.

## 4. Experiment-integrity rules

- `docs\EXPERIMENTS.md` is the single source of truth for metrics, conditions, trial counts and seeds. If code and doc disagree, change one deliberately and say so in `Progress.md`.
- Tune controller gains only on seeds 1000 to 1099. Report results only on seeds 0 to 29.
- Never hand-edit `results\raw.csv`. Regenerate it.
- Run the analytic drift check before trusting any sweep.
- Report null and negative results honestly. If depth does not beat `B2`, say so.

## 5. Documentation rules

- Docs are kept in sync as part of finishing a sprint, not afterwards.
- Which doc changes when:
  - Scope or sprint change: `Plan.md`
  - What happened: `Progress.md`
  - New tool, version or setup step: `RequirementsAndSetup.md` and `TechStack.md`
  - Metric or experiment change: `docs\EXPERIMENTS.md`
  - New source read or cited: `docs\REFERENCES.md`
- Notes are exhaustive, bullet-point and undergraduate-level, with the reasoning shown, not just the conclusion.
- In `docs\REFERENCES.md`, never cite anything marked "not read" in the report.

## 6. Git rules

- **Conventional commit messages:** `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`. Short subject line, imperative mood.
- Small commits, one idea each.
- **Semantic versioning tags** at milestones: `v0.1.0` after Sprint 1 up to `v1.0.0` at release.
- Never commit secrets. This project has none, but `.env` files stay gitignored by default.
- Do not commit large generated files. `results\raw.csv` is small enough to commit at milestones; figures are committed at release.
- Do not rewrite history on `main`.

## 7. Honesty rules for the report and README

- Never claim hardware validation.
- Always state: drift is injected, and simulated depth is cleaner than a real RealSense D455 stream.
- Never call corridor centering novel. It is a classical technique applied to a stated gap, with a controlled measurement and an ablation.
- Cite the source paper (arXiv:2609.14297v1) for the gap. Do not stretch the quote.
- State our own thresholds as our choices: success threshold 0.15 m, paper-metric safety radius 0.2 m.

## 8. Rules for AI assistants working in this repo

- Read these five files and `CLAUDE.md` first.
- Do not introduce ROS, ROS 2, Gazebo, Docker, WSL, CUDA, PyTorch or any LLM API.
- Do not use classes unless a library forces it.
- Do not change the folder structure or the experiment spec silently.
- Do not mark a sprint done unless its Definition of Done is met.
- Explain reasoning in short bullets, not long paragraphs.
- When unsure whether something is verified, say it is an assumption.
