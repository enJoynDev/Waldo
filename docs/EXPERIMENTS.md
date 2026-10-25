# Experiment Design

Single source of truth for variables, metrics, conditions, statistics and plots.
If code disagrees with this file, update this file deliberately.

---

## 1. Setup constants (defaults; live in `src/config.py`)

- Corridor: straight, length 12 m, width 2.0 m, plain walls, no landmarks (the "featureless" condition).
- Subgoal: drive straight for L = 10 m (matches the paper's 10 m subgoal cap).
- Robot footprint: 0.99 m x 0.67 m (Husky-like, from the paper). Clearance to each wall when centred: (2.0 - 0.67) / 2 = 0.665 m.
- Nominal speed: 0.5 m/s. Physics/control step 1/240 s. Depth camera at 10 Hz.
- Wheel base (track) b = 0.55 m. Verified: the Husky A200 manual gives a 550 mm track (about 0.555 m effective for skid steer). Using 0.55 m.
- Start pose: centred, heading aligned with the corridor.
- Camera: forward-facing, 87 degree horizontal FOV (D455 depth, per Intel's spec; the vertical FOV is derived from the image aspect ratio), mounted at about 0.4 m height (our choice; not given in the paper), metric depth after conversion. Depth readings closer than 0.52 m (the D455 minimum depth) are discarded in perception.

## 2. Drift model (what we inject)

- True motion differs from what odometry believes. Odometry is computed from nominal wheel speeds and nominal wheel radius, so it never sees the injected error.
- Three drift sources:
  - **Wheel-scale mismatch** `eps_L`, `eps_R` (fractional error). Wheel speeds become `v*(1+eps)`. Produces heading drift. Sweep variable is `d_eps = eps_R - eps_L`.
  - **Lateral skid** `s_lat`: small sideways velocity proportional to forward speed. Produces cross-track drift that heading alone does not reveal.
  - **Random noise** `sigma_w`: Gaussian noise on wheel speeds each step. Produces random-walk drift.
- Defaults (our choices): `s_lat = 0`, `sigma_w = 1%`. The mismatch is split symmetrically: `eps_L = -d_eps/2`, `eps_R = +d_eps/2`.
- `sigma_w` is the fractional standard deviation of each wheel's speed, drawn independently per wheel every 0.1 s. At L = 10 m this gives roughly 1 degree of heading std and 0.1 m of lateral std (hand estimate, to be checked in Sprint 1).
- Why `sigma_w` is not zero: the simulation is deterministic, so with zero noise all 30 seeds would give identical results. The analytic check in section 6 is the only run with `sigma_w = 0`.
- Seeded per trial. Same seed gives the same noise sequence across modes, so comparisons are paired.

## 3. Conditions (what is compared)

- Modes (controller variants):
  - `B1` baseline: odometry only (encoders). No correction.
  - `B2` baseline: encoders + simulated gyro heading (gyro has a constant bias and noise). **Fairer baseline, because the source paper also uses an IMU.**
  - Gyro defaults (our choices, not from a datasheet): constant bias 0.1 deg/s, white noise 0.05 deg/s std. The bias sweep in section 11 uses {0, 0.1, 0.5, 1} deg/s.
  - `C_lat`: depth correction using lateral offset only.
  - `C_head`: depth correction using heading error only.
  - `C_both`: depth correction using both. This is the main method.
- Independent variables:
  - Drift severity `d_eps` in {0, 0.25%, 0.5%, 1%, 2%} (see section 6 for why these values).
  - Depth noise `sigma_d` in {0, 0.02, 0.05} m (Gaussian on metric depth). Secondary sweep at fixed d_eps = 1%.
  - Optional: lateral skid `s_lat` in {0, 1%, 2%} at fixed `d_eps`.
- Trials: **30 per condition** (RRT-style stochastic noise needs repeats; same logic applies here).
- Seeds: 0 to 29 for reported results. **1000 to 1099 reserved for tuning gains.** Never tune on reported seeds.

## 4. Metrics (all per trial)

- `final_lat_err` (m): signed lateral offset from the corridor centreline at the end of the subgoal. Report absolute value in summaries.
- `final_head_err_deg`: heading error relative to the corridor axis at the end.
- `max_lat_err` (m): worst lateral offset during the run.
- `collided` (bool): robot body touched a wall.
- `dist_travelled` (m): forward distance reached (less than L if collided).
- `drift_paper` (m): the paper's metric, `max(0, ||goal - final_pos|| - d_s)`. Use `d_s = 0.2 m`. Included so our numbers can be placed next to theirs.
- `success` (bool): no collision AND `|final_lat_err| < 0.15 m`. The 0.15 m threshold is our choice; state it in the report.
- `fit_fail_frac`: fraction of camera frames where the wall fit confidence was below threshold and the controller fell back to odometry.
- `runtime_s`: wall-clock time per trial (for budgeting).

## 5. Perception and control (summary, so metrics make sense)

- Depth image -> metric depth -> back-project to 3D points in camera frame.
- Drop floor/ceiling points by height. Project remaining points to the ground plane (x forward, y left).
- Find the two walls by sequential RANSAC: fit the strongest line `y = a*x + b`, remove its inliers, fit the second line to what remains. The line with the larger intercept is the left wall. (A split by the sign of y fails when a turned robot sees a near wall cross y = 0.)
- From the two lines:
  - heading error = `-atan((a_left + a_right) / 2)`, positive when the robot is turned left
  - lateral offset = `-(b_left + b_right) * cos(heading) / 2`, positive when the robot is left of the centre
  - confidence = share of wall points explained by the two lines, scaled to 0 if the estimated corridor width is off by 0.5 m or more; 0 if either wall fails to fit
- Controller: `omega = omega_nominal + k_lat * lat_err + k_head * head_err`, with `omega` clipped.
- If confidence is below threshold, hold the last correction briefly, then fall back to odometry-only. The threshold is **0.5** (`CONF_THRESHOLD`). It is provisional: good frames on the tuning seeds never scored below 0.82, and no bad-frame scenario has been tested yet. Revisit in Sprint 5.

### 5a. Perception parameters and Sprint 2 results

- Keep points between 0.15 and 0.85 m height (floor and ceiling removal). Discard readings closer than 0.52 m or at the far clip (9.9 m and beyond).
- RANSAC: 100 iterations, inlier distance 0.05 m (above the renderer's own ~3 cm wall scatter within 6 m), minimum 20 points.
- Accuracy on a 5 x 5 pose grid (lateral -0.4 to 0.4 m, heading -8 to 8 degrees), 100 tuning seeds, 2500 estimates per noise level, no failed fits:

| sigma_d (m) | offset median / p95 (m) | heading median / p95 (deg) | confidence median |
|---|---|---|---|
| 0 | 0.0000 / 0.0000 | 0.000 / 0.000 | 1.000 |
| 0.02 | 0.0003 / 0.0008 | 0.006 / 0.016 | 0.995 |
| 0.05 | 0.0020 / 0.0060 | 0.029 / 0.095 | 0.844 |

- Caveat: these errors are very small because the noise is independent Gaussian per pixel and the fit averages thousands of points. Real depth errors are correlated and biased, so real accuracy would be worse.
- A half-pixel offset in the back-projection gave a constant 0.34 degree heading bias until the sweep exposed it; fixed in `depth_to_points`.
- Reproduce: `python src\perception_sweep.py` (about 70 s).

## 6. Sanity check and why the sweep values were chosen

- Small-angle analytic drift for the baseline over distance L with wheel-scale mismatch:
  - heading after L: `theta ~= L * d_eps / b`
  - lateral error after L: `y ~= L^2 * d_eps / (2 * b)`
- With L = 10 m and b = 0.55 m:
  - `d_eps = 0.25%` -> y about 0.23 m
  - `d_eps = 0.5%`  -> y about 0.45 m
  - `d_eps = 1%`    -> y about 0.91 m
  - `d_eps = 2%`    -> y about 1.82 m
- Wall clearance is 0.665 m, so the baseline should start colliding between 0.5% and 1%. That is the point of the sweep: it straddles the failure boundary.
- At 2% the heading is about 21 degrees, so the small-angle approximation is rough. Expect the simulation to deviate from the formula there. That is fine.
- **Required check before running the sweep:** with `B1`, no noise, and no skid, simulated final lateral error must match the formula within a few percent at small `d_eps`. If not, there is a bug in the drift model or the pose bookkeeping.
- Their reported real-world drift is about 0.1 m or less, which corresponds to the mildest settings here. Label the 1% and 2% runs as stress tests.

## 7. Procedure per trial

- Build corridor, spawn robot at the start pose.
- Loop: update TRUE pose from drifted wheel speeds; update ODOM pose from nominal wheel speeds; every 0.1 s render depth and run perception; apply control; check collision.
- Stop at `dist_travelled >= L` or on collision.
- Compute metrics, return one dict, append one CSV row.

## 8. Output format (`results/raw.csv`)

- Columns: `run_id, seed, mode, d_eps, s_lat, sigma_w, sigma_d, final_lat_err, final_head_err_deg, max_lat_err, collided, dist_travelled, drift_paper, success, fit_fail_frac, runtime_s`
- One row per trial. Regenerate, never edit by hand.

## 9. Statistics

- Summaries per condition: mean, standard deviation, 95% confidence interval (bootstrap or t-interval).
- Paired comparison baseline vs corrected on the same seeds. A Wilcoxon signed-rank test is enough; do not over-engineer.
- Collision and success rates: report counts out of 30, plus a Wilson interval.
- Do not claim "significant" without stating the test and sample size.

## 10. Figures to produce

- Fig 1: final absolute lateral error vs `d_eps`, one line per mode, error bars.
- Fig 2: collision rate vs `d_eps`, one line per mode.
- Fig 3: example trajectories (top-down) for baseline vs `C_both` at `d_eps = 1%`.
- Fig 4: final lateral error vs `sigma_d` for `C_both`, with baseline as a reference line.
- Fig 5: ablation bars (`C_lat`, `C_head`, `C_both`) at two drift levels.
- Table: all metrics per condition (mean +- std).

## 11. Optional stress tests (only if time remains)

- **Side openings:** cut gaps in one wall (doorways). The wall fit loses one side; tests the confidence gate and fallback.
- **Corridor width:** vary 1.5, 2.0, 3.0 m.
- **Gyro bias sweep** for `B2`, to show where gyro-aided odometry alone is enough and where depth still adds value.

## 12. Threats to validity (put in the report)

- Drift is injected by us, not measured on a real robot.
- Simulated depth is cleaner and denser than a real D455 stream.
- Wall surfaces are matte and uniform; no glass, glare, or textureless-wall depth dropouts.
- Controller gains were tuned in simulation.
- Single straight corridor; results may not extend to turns or cluttered spaces.
- The 0.15 m success threshold and `d_s = 0.2 m` are our choices.
