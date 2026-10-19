# Requirements and Setup

What must exist before and during development, and how to set it up on Windows 11 with VS Code.
Longer troubleshooting notes live in `docs/ENVIRONMENT.md`. This file is the checklist.

---

## 1. Functional requirements

- FR1: Simulate a straight corridor (12 m long, 2.0 m wide, plain walls, no landmarks).
- FR2: Simulate a differential or skid-steer robot with a Husky-like footprint (0.99 m x 0.67 m), driven kinematically.
- FR3: Inject drift: wheel-scale mismatch, lateral skid, random wheel noise. Odometry must never see the injected error.
- FR4: Render a simulated forward depth camera at about 10 Hz and convert it to metric depth.
- FR5: Estimate lateral offset, heading error and a confidence value from the two corridor walls.
- FR6: Control modes: `B1` odometry only, `B2` odometry + simulated gyro, `C_lat`, `C_head`, `C_both`. Controller falls back to odometry when confidence is low.
- FR7: Run each trial headless and return one metrics dict.
- FR8: Run sweeps (drift level, depth noise, skid, gyro bias) across seeds in parallel and write `results\raw.csv`.
- FR9: Produce all figures and summary tables from `raw.csv` without manual steps.

## 2. Non-functional requirements

- NFR1: Native Windows 11 only. No WSL, Docker, ROS, Gazebo, CUDA.
- NFR2: Deterministic: the same seed gives the same result; the same seed gives the same noise across modes.
- NFR3: No GPU required.
- NFR4: Total sweep runtime fits the time budget. Measure one trial in Sprint 0, then size the sweep.
- NFR5: Reproducible from a fresh clone with the commands in the README.
- NFR6: Code style: concise, flat, function-based, no classes.

## 3. Hardware and OS

- Windows 11, 64-bit.
- Any recent laptop is enough. Multi-core CPU helps the sweep (workers = physical cores minus 1).
- At least about 5 GB free disk for conda, packages and results.
- No GPU and no robot hardware needed.

## 4. Software to install

| Software | Version | Notes |
|---|---|---|
| Miniconda or Anaconda | latest, 64-bit | Provides the conda env |
| Python | 3.11 | Installed inside the conda env |
| VS Code | latest | Editor, debugger, terminal |
| Git for Windows | latest | Version control |
| GitHub account | | Repo, Issues, PRs |
| Build Tools for Visual Studio 2022 (Desktop development with C++) | optional | Only if `pip install pybullet` is ever needed |

VS Code extensions: Python (`ms-python.python`), Pylance, Jupyter (optional), Ruff (`charliermarsh.ruff`), GitLens (optional), GitHub Pull Requests (optional).

## 5. Python packages (from `environment.yml`)

- numpy, scipy, pandas, matplotlib, tqdm, ipykernel, pybullet.
- Dev tools: ruff, pytest (add to the environment in Sprint 0 and update `environment.yml`).
- Do not add heavy packages (PyTorch, OpenCV) unless a sprint explicitly needs them.

## 6. Setup steps (PowerShell)

1. Install Miniconda, VS Code and Git for Windows.
2. Create the project folder at `C:\Users\Joy Mandal\Desktop\WALDO\waldo`. Short path, no spaces, not inside OneDrive.
3. Clone or copy the repo into it.
4. Create and activate the environment:
   ```powershell
   cd C:\Users\Joy Mandal\Desktop\WALDO\waldo
   conda env create -f environment.yml
   conda activate corrdrift
   ```
5. Open the folder in VS Code (`File -> Open Folder`). Select the interpreter: `Ctrl+Shift+P`, `Python: Select Interpreter`, choose `corrdrift`.
6. Install the extensions listed above.
7. Check the install:
   ```powershell
   python -c "import pybullet, numpy, scipy, pandas, matplotlib; print('ok')"
   python src\smoke_test.py
   ```
8. Check lint tooling: `ruff check .` and `ruff format --check .`
9. Check tests run: `pytest -q` (there will be none yet in Sprint 0).

## 7. Parameters to verify (Sprint 0)

- Husky A200 track width (assumed `b = 0.55 m`).
- RealSense D455 depth horizontal FOV (assumed 87 degrees).
- Camera mounting height (assumed 0.4 m).
- Record the verified values in `src\config.py` and `Progress.md`.

## 8. Ready-to-start checklist

- [ ] conda env `corrdrift` creates without errors
- [ ] VS Code shows `corrdrift` as the interpreter
- [ ] `src\smoke_test.py` prints a depth shape and a plausible metric range
- [ ] One depth render timed; total sweep runtime estimated
- [ ] GitHub repo created; first commit on `main`
- [ ] `.gitignore` excludes `__pycache__`, `.vscode` local settings if desired, large result files if needed
- [ ] `ruff` runs cleanly
- [ ] Assumed parameters verified or flagged as assumptions
- [ ] Novelty check notes written in `docs/REFERENCES.md`

## 9. Folder structure (fixed)

```
waldo/
├── README.md
├── CLAUDE.md
├── Plan.md
├── Progress.md
├── RequirementsAndSetup.md
├── Rules.md
├── TechStack.md
├── environment.yml
├── docs/
├── src/
├── tests/
├── results/
│   ├── raw.csv
│   └── figures/
└── .vscode/
```

- Do not add new top-level folders without recording the decision in `Progress.md`.

## 10. Known Windows pitfalls

- Multiprocessing uses spawn. Every runnable script needs `if __name__ == "__main__":`.
- Each worker process opens its own PyBullet client (`p.DIRECT`).
- `conda` not found in PowerShell: run `conda init powershell` from Anaconda Prompt, restart VS Code.
- Activation blocked by execution policy: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Keep `results\raw.csv` closed in Excel while experiments run.
- Line endings: set `.gitattributes` to `* text=auto` so Windows and Git agree.
