# CF-2 Chameleon-Ring in Autodesk Fusion

**Status, read first.** This script has not been run in Fusion, and no native `.f3d` file exists.
What *has* been tested: the pose maths (60 poses, identical to the checked CAD kinematics) and the script's logic against a mock of the Fusion API.
What has *not*: the real Fusion API calls (STEP import, component creation, transforms). Expect that a line or two may need fixing; the error box names the line.
This is a **concept model**. Motors, battery, electronics and propeller are size stand-ins. Nothing here is flight-worthy.

## Route A: one-click build (recommended)
1. Keep `CF2_Fusion_Build.py` and `cf2_transforms.json` together. The script reads the part files from `step_parts/` in this folder, or from `../step_parts/` (the layout in this repository).
2. Fusion: **File > New Design** (must be empty).
3. **Utilities > Add-Ins > Scripts and Add-Ins**, open the *Scripts* tab, click **+** (My Scripts), choose this folder, select **CF2_Fusion_Build**, **Run**.
4. Wait a few minutes. 43 STEP files are imported, the 4 arms and 4 pods are placed in the flight pose.
5. Run it again for a pose prompt: `1` flight, `2` ground, `3` compact, `4` plays the 57-step transformation path, or type `J1,J2` in degrees (for example `30,10`).

Structure it creates: `CF2_Fuselage` (shell, hatches, placeholders), four `CF2_Shoulder_FL/FR/RL/RR`, and one `CF2_ArmModule` and one `CF2_RotorWheelPod` each used four times as instances. Arms and pods are siblings at the top level (not nested), because the right-hand pods roll in the opposite sense and instances cannot carry that on their own.
Five user parameters are added (arm length, ring diameter, prop diameter, and the two joint angles). The two angle parameters are labels only; the script reads your typed answer, not the parameters.

## Route B: no script (works even if Route A fails)
Use **Insert > Insert into Current Design** (or File > Open) with the whole-assembly STEP files in `../step/`: `CF2_flight.step`, `CF2_ground.step`, `CF2_compact.step`. Each is the full model in one fixed pose, with the part hierarchy kept. Static only, no motion.

## Route C: add real joints by hand
Fusion joints are not created by the script. To get a drag-to-move model, import the parts with Route A, then (Assemble > Joint) add, per corner, with limits in degrees:

| Joint | Type | Axis (body frame) | Pivot | Checked range |
|---|---|---|---|---|
| J1 shoulder yaw | Revolute | vertical, Z | at (±58, ±46, 0) mm, sign by corner | front arms 0 to 170, rear arms 10 to 180 |
| J2 pod roll | Revolute | along the arm, local X | at 100 mm out along the arm | 0 to 90 used in the transformation; larger rolls only inside the feasible band |

The feasible (J1, J2) region is not a rectangle: see `../../media/renders/joint_range_map.png`. At about 50 to 115 degrees J1 the pod can roll freely; toward the ground pose the roll band narrows and 0 degrees roll at J1 = 0 is infeasible. Joint limits in Fusion are boxes, so they cannot represent this; the staircase path in the script (state 4) is the safe route. These limits are geometric only (10 degree resolution) and say nothing about actuators, wiring or loads.

Pose conventions: front arms at J1 = phi, rear arms at 180 - phi, right-hand arms mirror the sign. Flight phi = 50 / J2 = 0. Ground phi = 0 (front), 180 (rear) / J2 = 90. Compact phi = 70 / J2 = 0.

## Units
Fusion works in cm internally. The script converts from mm. The STEP files are in mm.

## Files
`CF2_Fusion_Build.py`, `.manifest`, `cf2_transforms.json` (all poses and the 57-step path), `../step_parts/` (46 STEP files), `../step/CF2_flight/ground/compact.step`, `../../media/renders/joint_range_map.png`.


## Rev-C additions: speedster pose

- New pose **5 speedster**: arms swept to 75 deg / 105 deg, every pod rolled 90 deg so thrust points forward (`../step/CF2_speed.step`, "speed" in cf2_transforms.json).
- New option **6**: animate flight to speedster (17 modelled steps, smallest gap 1.87 mm). Exact check of the speedster pose: smallest gap 3.86 mm (requirement 2.0 mm).
- Front and rear rings sit side by side in the same plane in this pose: the rear pair flies in the wake of the front pair (an estimated 10-20 % thrust loss).
- `../../bom/CF2_RevC_BOM.csv` lists the real parts and prices. The CAD still shows placeholder sizes: the real J1/J2 servos do not fit the current arm fairing.
- `../../sim/performance/perf.json` holds the performance estimates (first-principles, not measured).
- As before, this script has not been run inside Fusion. If it fails, the error box names the line; please open an issue with the text.
