# References

Each entry says how it was used and whether it was actually read.
Do not cite anything in the report that is only listed here as "not read".

---

## Primary source (read in full)

- P. Kumar, K.R. Guruprasad, T. Sandhan. *Multi-Task Visual Perception Network with LLM Conditioning for Autonomous Navigation.* arXiv:2609.14297v1, 13 Sep 2026. Code: https://github.com/PraveenSingh24/VL-Navigation
  - Used for: the stated gap (geometric-target drift in featureless corridors, RGB-D not constraining it), robot parameters (Husky A200, D455), the 10 m subgoal limit, the drift metric (Eq. 6), reported drift magnitudes (Table V).

## Cited by the primary source (not read)

- P. Kumar, T. Sandhan. *Vision-aided online A\* path planning for efficient and safe navigation of service robots.* arXiv:2511.06801, 2025.
  - Possibly useful for related-work context. Read before citing.
- C. Cao et al. *Autonomous exploration development environment and the planning algorithms.* ICRA 2022.
  - Source of the simulation scenarios used by the primary paper. Not needed for this project.

## Sim-to-real context (from the earlier literature search, titles/abstracts seen)

- *From Abstraction to Reality: DARPA's Vision for Robust Sim-to-Real Autonomy.* arXiv:2503.11007.
- *Autonomous Navigation at the Nano-Scale: Algorithms, Architectures, and Constraints.* arXiv:2601.13252.
  - Used for: example of a concrete simulator mismatch (actuator lag), supporting the limitations section.
- *Closing Sim2Real Gaps: A Versatile Development and Validation Platform for Autonomous Driving Stacks.* doi:10.3390/s26041338.
  - Used for: reality-gap vs performance-gap distinction.

## Practical setup sources

- Community PyBullet-on-Windows install guides state that Microsoft C++ build tools are commonly needed for `pip install pybullet`, and that a conda-forge install on Python 3.11 is a workable alternative.
  - Used for: environment choices in `ENVIRONMENT.md`.

## Still to find (Phase 0 task)

- Prior work on depth/range-based corridor centering or wall following for wheeled robots.
- Any follow-up or citation of arXiv:2609.14297 that already addresses the corridor-drift limitation.
- A source for Husky A200 track width and D455 depth FOV to replace the assumed `b = 0.55 m` and 87 degrees.

## Novelty notes (fill in after Phase 0)

- What exists:
- What is different about this project:
- Positioning sentence for the report:
