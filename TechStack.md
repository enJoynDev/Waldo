# Tech Stack

What is used, what each piece is for, and why it was chosen over the alternatives.
Versions are targets; record the exact installed versions in `Progress.md` after Sprint 0.

---

## 1. Summary table

| Layer | Choice | Role |
|---|---|---|
| OS | Windows 11 | Development machine (native, no WSL) |
| Editor | VS Code | Coding, debugging, terminal, Markdown preview |
| Language | Python 3.11 | All project code |
| Environment | conda (env `corrdrift`) | Reproducible dependencies |
| Simulator | PyBullet | Corridor geometry, depth camera, collision queries |
| Numerics | NumPy, SciPy | Depth to points, RANSAC, geometry, statistics |
| Data | pandas | Results table, summaries |
| Plots | matplotlib | All figures |
| Progress | tqdm | Sweep progress bar |
| Parallelism | `multiprocessing` (spawn) | Run many trials at once |
| Quality | ruff, pytest | Lint, format, tests |
| Version control | Git + GitHub | Repo, Issues, PRs, tags |
| Docs | Markdown (and one Word proposal) | Plans, notes, report source |

## 2. Why each choice

### Python 3.11
- Mature scientific wheels on Windows; newest Python versions sometimes lag.
- The author already works in Python for ML/CV, so no learning cost.

### conda
- conda-forge ships prebuilt PyBullet binaries for Windows, which avoids needing Microsoft C++ build tools.
- `environment.yml` makes the setup reproducible from a fresh clone.

### PyBullet
- Provides what the project needs: a rendered depth camera and collision queries, headless via `p.DIRECT`.
- Installs on native Windows and runs inside a normal Python script, so it is debuggable in VS Code.
- Used in a minimal way: the robot is kinematic, so PyBullet is not solving wheel contact physics.
- Alternatives considered:
  - **Gazebo + ROS 2:** Linux-first, fragile natively on Windows, and the project needs no ROS graph. Rejected.
  - **WSL2 + Gazebo:** works but adds a layer and GUI/GPU friction. Rejected for time.
  - **MuJoCo:** good fallback. Has pip/conda wheels and depth rendering. Kept as plan B.
  - **Pure NumPy ray-casting in 2D:** fastest and fully deterministic, loses realism. Kept as plan C.
  - **CARLA / AirSim:** driving- and drone-focused, heavy, and not suited to a small indoor corridor. Rejected.

### NumPy and SciPy
- Depth image to 3D points is vectorised array math.
- RANSAC line fitting is written directly in NumPy. Simple, transparent, easy to explain in a viva, and fast enough for a 2D line fit. SciPy is for statistics (Wilcoxon, bootstrap) and any optional least-squares refinement.
- Alternatives: Open3D or scikit-image RANSAC. Rejected because they add dependencies for something short to write.

### pandas and matplotlib
- Standard tools for the results CSV, grouping by condition, and publication-style figures.
- Plotting uses the `Agg` backend in scripts so figures save without a display.

### multiprocessing (spawn)
- Windows uses spawn, so entry points need the `__main__` guard.
- Each worker has its own PyBullet client. Parallelism is across trials, never inside one trial.

### ruff and pytest
- ruff replaces flake8, isort and black in one fast tool.
- pytest covers the places where wrong numbers could be silent: depth conversion, drift model, metrics, determinism.

## 3. Core algorithms used

- **Depth to metric:** `z = far*near / (far - (far-near)*buf)` for PyBullet's non-linear depth buffer.
- **Back-projection:** pinhole model with intrinsics from the field of view and image size.
- **Wall extraction:** height filter to remove floor/ceiling, then projection to the ground plane (x forward, y left).
- **Wall fit:** RANSAC line fit on each side. Confidence from inlier ratio and agreement between the two wall angles.
- **State estimates:** heading error from the mean wall angle; lateral offset from half the difference of the two wall distances.
- **Control:** PD-style correction on lateral offset and heading, with output clipping and an odometry fallback.
- **Drift model:** wheel-scale mismatch, lateral skid and Gaussian wheel noise, applied to the TRUE pose only.
- **Analytic check:** small-angle drift, lateral error about `L^2 * d_eps / (2b)`.
- **Statistics:** mean, standard deviation, bootstrap or t confidence intervals, Wilcoxon signed-rank on paired seeds, Wilson intervals for collision and success rates.

## 4. Source modules

| File | Purpose |
|---|---|
| `src\config.py` | All constants |
| `src\world.py` | Corridor, robot body, depth camera |
| `src\drift.py` | TRUE vs ODOM pose, injected drift, gyro model |
| `src\perception.py` | Depth to wall fits to (offset, heading, confidence) |
| `src\control.py` | Correction law and fallback |
| `src\metrics.py` | Per-trial metrics |
| `src\run_trial.py` | One closed-loop trial |
| `src\run_experiments.py` | Sweeps, parallel runs, CSV output |
| `src\plot_results.py` | Figures and tables |
| `src\smoke_test.py` | Install and depth-render check |
| `tests\` | pytest tests |

## 5. What is deliberately not used

- ROS, ROS 2, Gazebo, Docker, WSL, CUDA, PyTorch, OpenCV, any LLM API.
- Reason: none is needed for this problem, several are painful on native Windows, and each would add setup time without adding to the result.
- If a later sprint needs one of them, record the reason in `Progress.md` first.

## 6. Version record (fill in after Sprint 0)

| Package | Installed version |
|---|---|
| Python | |
| numpy | |
| scipy | |
| pandas | |
| matplotlib | |
| pybullet | |
| ruff | |
| pytest | |
| tqdm | |
