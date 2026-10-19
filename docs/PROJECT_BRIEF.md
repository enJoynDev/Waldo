# Project Brief

Problem, gap, hypotheses, scope and novelty framing.
Written as exhaustive bullets with reasoning so it can be reused in the report.

---

## 1. Source paper and context

- Paper: *Multi-Task Visual Perception Network with LLM Conditioning for Autonomous Navigation*
  - Kumar, Guruprasad, Sandhan, IIT Kanpur. arXiv:2609.14297v1, 13 Sep 2026.
- What their system does:
  - An LLM (Gemini Pro) turns a natural-language instruction into an ordered plan.
  - The plan alternates **geometric moves** ("move 4 m forward, turn right") and **visual targets** ("find the chair").
  - No global map. Localisation uses wheel encoders + IMU only, with no loop closure.
  - Odometry is reset after each completed mission, so drift is limited to the start-to-target distance.
  - Maximum subgoal distance is 10 m, which they attribute to depth data quality.
  - Hardware: Husky A200 (skid-steer, about 988 mm x 670 mm footprint) with an Intel RealSense D455.
- What they report:
  - Table V: 50 trials per scenario, drift error about 0.03 to 0.08 m in simulation and 0.05 to 0.1 m in real-world runs.
  - Drift metric (their Eq. 6): mean of max(0, ||goal - final position|| - d_s), where d_s is a safety radius around the goal.
  - Table IV: in a "featureless corridor", geometric-only 92%, visual-only 15%, hybrid 95%.

## 2. The gap we target

- Their text says geometric targets can introduce extra drift in a featureless corridor, and that RGB-D data does not constrain them.
- Why this is a real, mechanistic gap (reasoning):
  - A geometric subgoal is open-loop with respect to the environment: it trusts odometry.
  - A featureless corridor has no landmarks, so the visual branch has nothing to lock onto.
  - So nothing observes or corrects the error while it accumulates.
  - A small heading error integrates into a cross-track (lateral) error that grows roughly with the square of distance travelled. Doubling the distance quadruples the sideways error.
  - Their 10 m subgoal cap limits the damage. It does not remove the cause.
- Why the depth camera is the natural fix:
  - The camera is already mounted and already running for other modules.
  - In a corridor the walls are strong, easy geometric structure in depth.
  - Wall geometry directly gives the two quantities odometry cannot observe: lateral offset and heading relative to the corridor.

## 3. Our contribution (stated precisely)

- Add a depth-based corridor-centering correction to geometric subgoal execution.
- Quantify, in simulation, how much it reduces end-of-subgoal drift and wall collisions versus odometry-only baselines.
- Sweep drift severity and depth noise to find where the correction helps most and where it breaks.
- Ablate the two correction terms (lateral-only, heading-only, both) to show which one matters.

## 4. Hypotheses

- **H1:** The correction reduces final lateral error versus the baseline at every non-zero drift level, and the gap widens as drift grows.
- **H2:** The correction keeps wall collisions at zero up to a drift level where the baseline already collides.
- **H3:** The correction degrades gracefully with depth noise. There is a noise level above which it is no better than baseline, and we report that level.
- **H4 (ablation):** Heading-only correction fixes most of the end-of-subgoal drift for wheel-scale error, while lateral correction matters more for skid-type sideways drift.
- Any of these may fail. A null result is reported as a null result.

## 5. Scope

- In scope:
  - Straight corridor, single geometric subgoal of up to 10 m.
  - Differential / skid-steer kinematics with injected drift.
  - Simulated depth camera with optional Gaussian noise.
  - Fallback to odometry when wall fit confidence is low.
- Out of scope (state this explicitly in the report):
  - LLM instruction parsing, YOLO, ESANet, person re-ID.
  - Turns, junctions, multi-subgoal missions (optional stretch only).
  - Moving obstacles, lighting and reflective-surface noise (that is the other gap, not chosen).
  - Real hardware.

## 6. Novelty framing (be honest)

- Corridor centering and wall following from range data is a classical technique. We do NOT claim it as new.
- What we do claim:
  - It targets a limitation the source paper states and leaves unaddressed.
  - We provide a controlled measurement of the benefit and the failure boundary.
  - We include an ablation, which a typical demo skips.
- The paper is only days old (as of 5 Oct 2026), so it is unlikely anyone has already answered it directly. That does not make the underlying technique new.
- **Novelty check is still pending** (Phase 0 in `PLAN.md`). Search terms are listed there.
- IMU caveat (important for credibility):
  - The paper's localisation uses wheel encoders **and an IMU**.
  - A gyro would remove much of the heading drift that wheel-scale error causes.
  - A gyro cannot observe cross-track position, and gyros have their own bias drift.
  - So an encoder-only baseline overstates how much the fix is needed.
  - Fix: include a second, fairer baseline with a simulated gyro-aided heading (baseline B2 in `EXPERIMENTS.md`).

## 7. What simulation-only lets us claim

- We can claim: the algorithm works in a controlled model of the problem.
- We cannot claim:
  - That real drift looks like our injected drift.
  - That a real D455 depth stream (noise, dropouts, range limits, glare on glossy walls) behaves like our simulated depth.
  - That the controller gains transfer to a real robot.
- This is the sim-to-real boundary discussed earlier in the project research. Stating it explicitly is part of the contribution's credibility.
- Their reported real-world drift is small (about 0.1 m or less). Our mild drift settings should include that regime, and severe settings are labelled as stress tests.

## 8. Why PyBullet and not Gazebo / ROS 2

- Constraint: everything must run natively on Windows 11 with VS Code.
- Gazebo and ROS 2 are Linux-first. Running them natively on Windows is possible but fragile, and this project does not need a ROS graph.
- PyBullet:
  - Installs with conda on Windows, pure Python workflow, debuggable in VS Code.
  - Provides a rendered depth camera and collision queries.
  - Runs headless (`p.DIRECT`) for batch experiments.
- Fallbacks if depth rendering is too slow or install fails:
  - MuJoCo (pip/conda wheels, depth rendering available).
  - Pure NumPy 2D ray-casting against wall segments, using a simulated depth "slice". Less visual, but fast and fully deterministic.
