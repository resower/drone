# cad

Parametric source and exported geometry for CF-2.

| Path | Contents |
|---|---|
| `params.py` | All dimensions, joint poses (`cfg_flight`, `cfg_ground`, `cfg_compact`, `cfg_speed`) and clearance thresholds. Change a value here and re-run the generators. |
| `parts_body.py`, `parts_pod.py` | CadQuery generators for fuselage, shoulders, arms, rings, pods. |
| `library.py`, `assemble.py`, `kin.py` | Part library, assembly instances, kinematics (J1/J2 transforms per corner). |
| `export_all.py` | Writes per-part STEP/STL, the pose assemblies and the manifest. |
| `verify.py`, `verify_path.py`, `path_dense.py` | Exact (OpenCascade) minimum-distance checks for the poses and the transformation path. |
| `sweep1.py`, `sweep2.py`, `sweepB.py`, `seq.py` | Joint-range sweep and transformation-sequence search. |
| `speed_search.py`, `speed_path.py` | Speed-pose search and the flight-to-speed path. |
| `mass.py`, `bom.py`, `aero_geom.py`, `ground_review.py` | Mass/CG estimate, part list, silhouette areas, ground-pose review. |
| `fc_build.py`, `fc_validate.py`, `fc_validate_seq.py` | Build and check the FreeCAD document. |
| `step/` | Whole-assembly STEP files: `CF2_flight`, `CF2_ground`, `CF2_compact`, `CF2_speed`. |
| `step_parts/` | One STEP file per part (46). |
| `stl_parts/` | One STL file per part (96). |
| `CF2_Chameleon-Ring.FCStd` | FreeCAD document with a parameter sheet and expression-driven joints. Part solids are imported from the generators; editing a dimension in FreeCAD does not regenerate a part. Regenerate from `params.py`. |
| `CF2_transform_sequence.FCMacro` | FreeCAD macro that plays the transformation sequence. |
| `CF2_Fusion_Build/` | Autodesk Fusion script, pose data and notes. Untested in Fusion. |

## Requirements

Python 3.10+, `cadquery`, `numpy` (see `../requirements.txt`). `export_all.py` imports `render_scene.py`, which needs Blender's `bpy` module for the material table. `fc_build.py` and `fc_validate.py` run under FreeCAD (`freecadcmd`).

## Rebuild

Scripts write to `../build/` (not tracked). From this folder:

```
python3 export_all.py        # parts, STEP, STL, manifest
python3 verify.py            # exact clearances for the pose assemblies
python3 verify_path.py       # exact clearances along the flight-to-ground path
```

Some scripts read intermediate files written by earlier ones (for example `seq.py` reads the sweep output), so run the sweeps first if the build folder is empty.

## Units and frames

Millimetres and degrees. Body frame: x forward, y left, z up, origin at the fuselage centre. Pod ring axis is the pod's local z axis.
