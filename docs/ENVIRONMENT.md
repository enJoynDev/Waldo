# Environment: Windows 11 + VS Code + conda + PyBullet

Everything here is native Windows. No WSL, no Docker, no ROS.

---

## 1. Prerequisites

- Windows 11, fully updated.
- **Miniconda** (or Anaconda), 64-bit.
- **VS Code**.
- **Git** (optional but recommended).
- Optional fallback only: *Build Tools for Visual Studio 2022* with the "Desktop development with C++" workload (section 6).

## 2. Project folder

- Put the project at `C:\Users\Joy Mandal\Desktop\WALDO\waldo`.
- Reasons:
  - Short path avoids Windows long-path problems.
  - No spaces avoids quoting bugs in scripts.
  - Not inside OneDrive, because OneDrive sync can lock files while experiments write CSVs.

## 3. Create the conda environment

```powershell
cd C:\Users\Joy Mandal\Desktop\WALDO\waldo
conda env create -f environment.yml
conda activate corrdrift
python --version
python -c "import pybullet, numpy, scipy, pandas, matplotlib; print('ok')"
```

- Why conda-forge for PyBullet:
  - Community install guides for Windows report that `pip install pybullet` often needs Microsoft C++ build tools because a prebuilt wheel may not exist for your Python version.
  - The conda-forge package ships prebuilt binaries, so the build tools are usually not needed.
- Why Python 3.11:
  - Several scientific packages lag on the newest Python versions on Windows.
  - 3.11 is a safe middle ground.

## 4. VS Code setup

- Extensions:
  - Python (`ms-python.python`) and Pylance
  - Jupyter (optional, for quick plots)
  - Markdown preview is built in (`Ctrl+Shift+V`) for the docs
- Select the interpreter:
  - `Ctrl+Shift+P` -> `Python: Select Interpreter` -> choose `corrdrift`.
  - Bottom-right of the window should now show the `corrdrift` environment.
- Open the folder with `File -> Open Folder` on `C:\Users\Joy Mandal\Desktop\WALDO\waldo` (not individual files), so VS Code picks up `.vscode\`.

`.vscode\settings.json`

```json
{
  "python.terminal.activateEnvironment": true,
  "editor.formatOnSave": false,
  "files.eol": "\n",
  "files.exclude": { "**/__pycache__": true }
}
```

`.vscode\launch.json`

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: current file",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

- Run from the **project root** so relative paths like `results\raw.csv` resolve correctly.
- Debug with breakpoints in a single trial first (`run_trial.py`) before ever launching the multiprocessing sweep. Debugging spawned workers is much harder.

   ## 5. Smoke test (`src\smoke_test.py`)

   Goal: prove PyBullet can start headless, build a closed corridor, and render a correct, NaN-free metric depth image. Run it with `python src\smoke_test.py`.

   - What it checks:
     - A wall placed exactly 3.0 m ahead reads 3.000 m at the centre pixel, which catches a wrong depth-buffer conversion.
     - No pixel is NaN and all depths lie between near and far.
     - One render is timed, to size the experiment sweep.
   - Why the corridor has a ceiling: PyBullet's depth buffer returns NaN for rays that hit nothing, so every ray must hit a surface.
   - FOV: PyBullet takes the *vertical* FOV. The script converts from the assumed 87 degree horizontal D455 FOV using the image aspect ratio.
   - Expected output: shape (240, 320), 0 NaN pixels, centre depth about 3.000 m, then `SMOKE TEST PASSED`.

## 6. If the conda install of PyBullet fails

- Try in this order:
  1. `conda install -c conda-forge pybullet` inside the activated env.
  2. Make sure Python is 3.10 or 3.11, not newer.
  3. Install *Build Tools for Visual Studio 2022* (workload: Desktop development with C++), restart the terminal, then `pip install pybullet`.
  4. Update pip and wheel first: `python -m pip install -U pip wheel`.
- If it still fails, switch to the MuJoCo or pure-NumPy fallback described in `PROJECT_BRIEF.md` section 8. The perception and control code is simulator-independent as long as `world.py` returns a metric depth image.

## 7. Headless vs GUI

- Use `p.GUI` only when you want to look at the corridor while debugging. It opens an OpenGL window.
- Use `p.DIRECT` for all experiments. It is faster and works over any terminal.
- `getCameraImage` works in `DIRECT` mode with the built-in CPU renderer.

## 8. Multiprocessing on Windows

- Windows uses the spawn start method, so every worker re-imports your script.
- Always guard entry points:

```python
if __name__ == "__main__":
    main()
```

- Each worker must call `p.connect(p.DIRECT)` itself. A PyBullet client cannot be shared across processes.
- Start with `workers = physical cores - 1` and measure.

## 9. Performance notes

- Do not render the camera at the physics rate. Render at about 10 Hz.
- Start with a small image (for example 160 x 120). Increase only if wall fits are noisy.
- In Phase 0, time one full trial and multiply by the number of trials in `EXPERIMENTS.md` to budget total runtime before committing to the sweep size.

## 10. Troubleshooting

- **`conda` not recognised in PowerShell:** open "Anaconda Prompt" once and run `conda init powershell`, then restart VS Code.
- **`conda activate` fails with an execution-policy error:** run PowerShell once as your user and execute `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **VS Code uses the wrong Python:** re-run `Python: Select Interpreter`, then open a new terminal so it re-activates.
- **`ModuleNotFoundError: pybullet` inside VS Code but works in terminal:** the interpreter is not `corrdrift`.
- **Figures do not appear when running a script:** you are probably using the `Agg` backend (intended for batch). Save to file or use `plt.show()` in a notebook.
- **Sweep seems to hang:** missing `if __name__ == "__main__":` guard.
- **CSV locked / permission denied:** close Excel; do not keep the CSV open while experiments write it.
