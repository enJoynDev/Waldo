"""Every tunable number for WALDO lives here (Rules: no magic numbers elsewhere).

Frame: x forward along the corridor, y left, heading 0 along +x.
SI units; angles in radians unless the name ends in _DEG.
Drift values are fractions (0.01 = 1%).
"""

import math
from pathlib import Path

# --- paths (pathlib only, never a hard-coded C:\ path) ---
ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
RAW_CSV = RESULTS_DIR / "raw.csv"

# --- corridor ---
CORRIDOR_WIDTH = 2.0
# starts a little behind the robot so no camera ray escapes backwards or sideways
CORRIDOR_X_MIN = -1.0
CORRIDOR_X_MAX = 12.0
WALL_HEIGHT = 1.0
WALL_THICKNESS = 0.1

# --- robot (Husky A200 footprint from the source paper) ---
ROBOT_LENGTH = 0.99
ROBOT_WIDTH = 0.67
ROBOT_HEIGHT = 0.4  # only matters for the collision shape; the robot is never rendered
WHEEL_BASE = 0.55  # track width b; Husky manual says 550 mm
SPEED = 0.5  # nominal forward speed
CLEARANCE = (CORRIDOR_WIDTH - ROBOT_WIDTH) / 2  # wall gap when centred, 0.665 m

# --- start pose and subgoal ---
START_X = 0.0
START_Y = 0.0
START_HEADING = 0.0
SUBGOAL_DIST = 10.0  # the source paper's 10 m subgoal cap

# --- timing ---
DT = 1 / 240  # kinematic integration step
CAMERA_PERIOD = 0.1  # depth camera at 10 Hz
NOISE_PERIOD = 0.1  # wheel noise is redrawn this often so it random-walks, not averages out
MAX_TRIAL_TIME = 40.0  # safety stop: twice the nominal drive time
NOISE_N = int(MAX_TRIAL_TIME / NOISE_PERIOD) + 1  # noise samples drawn per trial

# --- depth camera (D455-like) ---
IMG_W = 160
IMG_H = 120
FOV_H_DEG = 87.0  # horizontal; PyBullet needs vertical, converted in world.py
# PyBullet wants the vertical FOV; derive it from the aspect ratio
FOV_V_DEG = math.degrees(2 * math.atan(math.tan(math.radians(FOV_H_DEG) / 2) * IMG_H / IMG_W))
NEAR = 0.1  # render clipping plane
FAR = 10.0
CAMERA_HEIGHT = 0.4  # our choice, not given in the paper
CAMERA_MIN_DEPTH = 0.52  # D455 minimum depth; perception discards closer readings

# --- injected drift (defaults; applied to the TRUE pose only) ---
D_EPS_DEFAULT = 0.0  # wheel-scale mismatch eps_R - eps_L, split symmetrically
S_LAT_DEFAULT = 0.0  # lateral skid: sideways velocity = s_lat * forward speed
SIGMA_W_DEFAULT = 0.01  # nonzero, or all 30 seeds would be identical
SIGMA_D_DEFAULT = 0.0  # depth noise std in metres

# --- gyro for B2 (our choices, not from a datasheet) ---
GYRO_BIAS_DEG_S = 0.1
GYRO_NOISE_DEG_S = 0.05

# --- sweeps ---
D_EPS_LEVELS = (0.0, 0.0025, 0.005, 0.01, 0.02)
SIGMA_D_LEVELS = (0.0, 0.02, 0.05)
S_LAT_LEVELS = (0.0, 0.01, 0.02)
GYRO_BIAS_LEVELS_DEG_S = (0.0, 0.1, 0.5, 1.0)
DEPTH_SWEEP_D_EPS = 0.01  # fixed drift level for the depth-noise sweep

# --- seeds: tune on one set, report on the other, never mix ---
SEEDS_REPORT = tuple(range(0, 30))
SEEDS_TUNE = tuple(range(1000, 1100))

# --- modes ---
MODES = ("B1", "B2", "C_lat", "C_head", "C_both")

# --- metrics (thresholds are our choices; state them in the report) ---
SUCCESS_LAT_M = 0.15
DRIFT_SAFETY_RADIUS = 0.2  # d_s in the paper's drift metric
