# Operating modes and transformation mechanism

CF-2 has three operating modes. All poses are set by two joints per corner: **J1** (arm yaw about the vertical shoulder hinge) and **J2** (pod roll about the arm axis). Rear arms mirror the front (J1 rear = 180 - J1 front); right-hand arms mirror the sign of the left.

Pose data for every state is in `cad/CF2_Fusion_Build/cf2_transforms.json`.

| Mode | J1 front / rear | J2 | Ring axis | Rotor |
|---|---|---|---|---|
| Normal flight | 50 / 130 deg | 0 | vertical (ring is a horizontal duct) | thrust up |
| Rover | 0 / 180 deg | 90 | horizontal (ring is a vertical wheel) | stopped, locked |
| Speed | 75 / 105 deg | -90 front, +90 rear | forward | thrust forward |

## Normal flight

Standard quadcopter layout. The four arms are swept to 50 / 130 degrees and every pod is level, so each ring is a duct around its propeller (4 mm tip gap). The rings have no drive in flight; the rim should be braked or held by the pinion so wake swirl does not turn it (open issue, see `validation-register.md`).

## Rover

The arms swing flat to 0 / 180 degrees and each pod rolls 90 degrees about the arm axis. The ring's axis is then horizontal, the TPU tyre is the lowest point, and the vehicle rests on four wheels with the fuselage 54 mm above the tyre plane. Each ring is driven independently by its own pinion and internal ring gear, so the vehicle steers skid-style. The propeller and its motor stay fixed on the stator hub and do not turn. The blade tip is 16.3 mm above the ground (geometry only).

## Speed mode (Rev C)

The arms sweep to 75 / 105 degrees and every pod rolls 90 degrees so thrust points forward. Front and rear pods roll in opposite senses (rho_R = -rho_F); that sign relation makes all four pods push forward (forward thrust fraction 0.97 at J1 front = 75 degrees). The rings then act as ducts aligned with the flight direction. A small wing between the rings is intended to carry weight, but the wing is not modelled in CAD and is the least developed part of this mode.

Front and rear rings sit side by side in one plane, so the rear pair flies in the wake of the front pair (an estimated 10-20 % thrust loss). The speed pose was checked with exact solids (smallest gap 3.86 mm against a 2.0 mm requirement) and the flight-to-speed path with 17 modelled states (smallest gap 1.87 mm).

## Transformation: flight to rover

The feasible (J1, J2) region is not a rectangle, so the pods cannot simply roll first or yaw first. The shortest staircase found by search over checked states (lock-step motion, J2 equal on all four) is:

| Move | J1 front | J2 |
|---|---|---|
| 1 | 50 -> 30 | 0 |
| 2 | 30 | 0 -> 10 |
| 3 | 30 -> 20 | 10 |
| 4 | 20 | 10 -> 30 |
| 5 | 20 -> 10 | 30 |
| 6 | 10 | 30 -> 40 |
| 7 | 10 -> 0 | 40 |
| 8 | 0 | 40 -> 90 |

Rover to flight is the reverse. Exact solid distances at the 15 planned states all met their requirements (smallest margin 1.84 mm, arm to own plate). A denser sampled pass at 2.5 degree steps (56 sub-steps) gave the same worst margin. The 57-state path used by the Fusion script is in `cf2_transforms.json`. Results: `sim/clearance/verify_path_exact.json`, `path_dense.json`, `sequence_flight_ground.json`.

**The body must be lifted during the roll.** In flight pose the vehicle rests on its belly with the pods 60 mm above the ground. Rolling pushes the tyres into the ground and lifts the fuselage from 25.7 mm to 79.8 mm. With the estimated 1.33 kg mass and a quasi-static frictionless model, the peak lift torque is about 0.23 N m per J2. In rover pose the same load (about 3.3 N per wheel at 46 mm offset) is a steady 0.15 N m holding torque on each J2, which argues for a mechanical lock rather than actuator holding. These are estimates, not measurements.

## Transformation: flight to speed

17 modelled states from J1 front 50 to 75 degrees with J2 going to -90 (front) and +90 (rear). Data: `sim/clearance/path_flight_speed.json`, `verify_exact_cfg_speed.json`.
