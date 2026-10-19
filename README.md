# WALDO: Wall-Aided Lateral Drift Offsetting

Depth-based corridor drift correction for mapless robot navigation (simulation-only).
Mini project for the Autonomous Systems course.
Platform: **Windows 11 + VS Code + PyBullet (Python 3.11, conda)**. No hardware.

   Status: Sprint 0 (foundations). See `Plan.md` and `Progress.md`.

---

## One-line summary

- A wheeled robot driving a straight "geometric" subgoal through a **featureless corridor** has nothing to correct its odometry drift.
- The robot already carries an RGB-D camera, but the paper we build on says that data does not constrain this drift.
- We use the depth stream to fit the two corridor walls, estimate lateral offset + heading error, and feed a small correction back into the controller.
- We measure how much that reduces drift and wall collisions versus an odometry-only baseline, across drift severity and depth-noise levels.

## Where this comes from

- Paper: *Multi-Task Visual Perception Network with LLM Conditioning for Autonomous Navigation*
  - Authors: Praveen Kumar, K.R. Guruprasad, Tushar Sandhan (IIT Kanpur)
  - arXiv:2609.14297v1, 13 Sep 2026
- Their system is mapless: LLM-parsed instructions become alternating geometric moves and visual targets, localisation uses wheel encoders + IMU, no loop closure.
- Their own limitation (paraphrased): geometric targets can add extra drift in a featureless corridor, and RGB-D data does not constrain them.
- This project isolates **only that one limitation**. We do not rebuild their LLM / YOLO / ESANet pipeline.

## What is and is not claimed

- Claimed (if results support it): a depth-based correction reduces end-of-subgoal lateral error and wall collisions in simulation, and we know where it stops working (depth noise, side openings).
- Not claimed:
  - Not a new technique. Wall-centering from range data is classical. The contribution is a targeted fix + controlled measurement + ablation.
  - Not validated on hardware. Drift is injected by us, and simulated depth is cleaner than a real D455.
  - Not a replication of the full paper.

## Quick start (PowerShell)

```powershell
cd C:\Users\Joy Mandal\Desktop\WALDO\waldo
conda env create -f environment.yml
conda activate corrdrift
python src\smoke_test.py          # confirms PyBullet + depth camera work
python src\run_experiments.py     # runs the full sweep -> results\raw.csv
python src\plot_results.py        # figures -> results\figures\
```

Full setup, VS Code configuration and troubleshooting: `docs/ENVIRONMENT.md`.

## Repo layout

```
waldo/
├── README.md
├── CLAUDE.md
├── Plan.md                   # sprint roadmap (current plan)
├── Progress.md               # running log and decisions
├── RequirementsAndSetup.md
├── Rules.md
├── TechStack.md
├── pyproject.toml            # ruff and pytest settings                 # rules for AI assistants working in this repo
├── environment.yml
├── docs/
│   ├── PROJECT_BRIEF.md      # problem, gap, hypotheses, scope, novelty framing
│   ├── ENVIRONMENT.md        # Windows 11 + VS Code + conda + PyBullet setup
│   ├── PLAN.md               # superseded by Plan.md
│   ├── EXPERIMENTS.md        # variables, metrics, conditions, stats, plots
│   └── REFERENCES.md         # sources and what was / was not read
├── src/
│   ├── config.py             # every constant lives here
│   ├── world.py              # corridor, robot body, depth camera
│   ├── drift.py              # true motion vs odometry model
│   ├── perception.py         # depth -> points -> wall fits -> (lat, head, conf)
│   ├── control.py            # PD correction
│   ├── metrics.py            # drift, collision, success
│   ├── run_trial.py          # one trial -> dict of metrics
│   ├── run_experiments.py    # sweeps + multiprocessing -> CSV
│   ├── plot_results.py
│   └── smoke_test.py
├── tests/
├── results/
│   ├── raw.csv
│   └── figures/
└── .vscode/
    ├── settings.json
    └── launch.json
```

## Results (fill in after Phase 4)

- Table: final lateral error (mean ± std, 95% CI) per drift level, baseline vs corrected.
- Figure: lateral error vs drift level.
- Figure: collision rate vs drift level.
- Figure: sensitivity to depth noise.
- Figure: ablation (lateral-only / heading-only / both).
