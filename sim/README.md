# sim

Results of the geometric and analytical checks done so far. **There is no CFD, multibody, flight simulation or firmware in this repository, and nothing here has been measured.** The planned work is in `../docs/test-plan.md`.

## clearance/

Outputs of the scripts in `../cad` (exact OpenCascade solid distances unless noted).

| File | Contents |
|---|---|
| `verify_exact.json` | Exact minimum distances per pair for flight, ground and compact poses. |
| `verify_exact_cfg_speed.json` | Same for the speed pose. |
| `verify_path_exact.json` | Exact clearances at the 15 planned states of the flight-to-ground path. |
| `path_dense.json` | Sampled clearances at 2.5 degree steps (56 sub-steps). |
| `path_flight_speed.json` | The 17-state flight-to-speed path. |
| `sequence_flight_ground.json` | The staircase found by search. |
| `envelopes.json` | Bounding boxes and volumes per pose. |
| `ground_review.json` | Ground-pose track, wheelbase, clearances, tip-over angles. |
| `mass_cg_v2.json` | Estimated mass and CG per pose. |
| `aero_geometry.json` | Projected silhouette areas (geometry, not drag). |

## performance/

`perf.py` is a first-principles power and range model for hover, 50 km/h flight, rover and speed mode; it writes `perf.json`. The assumptions are listed in `../docs/performance-estimates.md`. These are best-case estimates, not test results.

```
cd sim/performance && python3 perf.py
```
