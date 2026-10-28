# CF-2 "Chameleon-Ring": design notes

CF-2 is a non-weaponised university research quadcopter whose four rotor-guard rings double as drive wheels. This document records the architecture, the three base configurations and how they were checked. It describes a concept: geometry and kinematics only. No part has been built, printed or tested.

## 1. Summary

1. Each corner is a two-joint module. **J1** yaws the arm about a vertical hinge at the fuselage. **J2** rolls the whole rotor-wheel pod about the arm axis. A 90 degree roll turns the pod's outer ring from a horizontal duct into a vertical wheel.
2. The two joints are independent actuators but not independent in range. The allowed (J1, J2) region is not a rectangle, so joint stops and a motion planner are required (see `modes.md`).
3. The compact pose is a weak result: folding the arms reduces the envelope volume by only 7.6 % (13.8 L against 14.9 L). The narrowest pose is the ground pose (223 mm wide, 45 % narrower than flight).
4. A staggered "checkerboard" shoulder height cuts the footprint by about 41 % but breaks four-wheel ground contact. A cranked-arm variant that would keep contact cannot interleave the pods. Neither was adopted.
5. The main open risks are mechanical (wheel-load path through a thin printed ring, blade-to-ring gap under load, joint locking) and aerodynamic (four wide discs). See `validation-register.md`.

## 2. Architecture

### 2.1 Rotor-wheel pod

The propeller assembly is the wheel module.

- **Ring.** One annular part is both duct wall and wheel rim. Inner radius 67.5 mm around a 127 mm propeller (4 mm tip gap); outer tyre diameter 157 mm. A TPU tyre with 36 chevron lugs is the only part intended to touch the ground.
- **Support and drive.** The ring runs on three V-groove rollers on the stator and is driven by a pinion on a gearmotor through an internal ring gear (Z = 92, module 1.5, pinion about 12 teeth). The ring rotates around the stator, so no slip ring is needed and the rotor never turns with the wheel.
- **Rotor.** Motor and propeller sit on the stator hub (four spokes) and stay still in ground mode. With the tyre as the lowest point, the blade tip is 16.3 mm above the ground plane in ground mode (geometry only; tyre deflection would reduce this).
- **J2.** A pylon runs from the stator hub to the arm's wrist, giving a single-sided axle in ground mode. The ring mid-plane is 46 mm from the arm axis, so after a 90 degree roll the wheel sits outboard of the arm.
- **J1.** A vertical yaw hinge between two shoulder plates fixed to the fuselage, with the arm knuckle between them.

### 2.2 Base configurations

| | J1 front / rear | J2 roll | Envelope (mm) | Volume | Footprint | Exact min. clearance |
|---|---|---|---|---|---|---|
| Flight | 50 / 130 deg | 0 | 404 x 405 x 91 | 14.9 L | 1636 cm2 | 3.9 mm (arm to own shoulder plate) |
| Ground | 0 / 180 deg | 90 | 476 x 223 x 160 | 16.9 L | 1060 cm2 | 3.8 mm (same pair) |
| Compact | 70 / 110 deg | 0 | 344 x 440 x 91 | 13.8 L | 1512 cm2 | 3.9 mm (same pair) |
| Speed (Rev C) | 75 / 105 deg | -90 front, +90 rear | see `sim/clearance/verify_exact_cfg_speed.json` | | | 3.86 mm (requirement 2.0 mm) |

Envelopes are bounding boxes from surface samples (about 1.5 mm uncertainty). The compact pose was chosen from a sweep for a sampled margin of about 20 mm over the pod requirements. A slightly smaller pose (70/100 deg, 13.4 L) existed with only about 3 mm of margin and was rejected.

Clearance requirements are design targets, not standards: pod to pod 5 mm, pod to fuselage 5 mm, pod to shoulder plate 4 mm, pod to own arm 4 mm, connector to anything 3 mm, arm to arm 3 mm, arm to fuselage 3 mm, arm to own plate 2 mm, arm to other plate 3 mm. All pairs closer than 14 mm in each configuration were re-measured with exact solids (OpenCascade); sampled and exact values differed by at most 0.8 mm. The arm-to-own-plate pair is the tightest against its requirement because it is a deliberately small designed gap.

### 2.3 Joint ranges

The sweep covered J1 from -60 to 240 degrees and J2 from -180 to 180 degrees in 10 degree steps, with every state tested against all clearances (`media/renders/joint_range_map.png`).

- Front arms: feasible J1 from 0 to 170 degrees. Rear arms: 10 to 180 degrees (mirror image).
- At J1 between about 50 and 115 degrees the pod may roll through all 360 degrees.
- Toward the ground pose the feasible roll band narrows. At the ground pose itself, roll values from about 35 degrees up are feasible and 0 is not.
- Negative J1 (arms swung past the fuselage axis) is infeasible.

These are geometric limits at 10 degree resolution. They say nothing about actuator range, wiring or loads.

## 3. Drive and traction options

The requirement: traction independent of the rotor, blades never touching the ground, rotor mechanically isolated from the wheel, no extra add-on wheels.

| Option | Traction path | Advantage | Main problem / unproven |
|---|---|---|---|
| **A. Internal ring gear + pinion, ring on 3 V-rollers (baseline)** | Gearmotor on stator, four independent drives | Positive drive, no slip ring, compact | Printed 92-tooth gear wear and debris tolerance; ring runout vs 4 mm tip gap; roller wear |
| B. Friction roller on ring inner wall | Same layout, no teeth | Simpler ring, quieter | Slip under load and when wet; preload loads the thin ring |
| C. Belt around a ring groove | Belt to gearmotor | Tolerant of misalignment | Belt must clear airflow and rollers; tensioner adds parts |
| D. Ring as motor rotor | Direct drive | No gears | Magnets and coils in the wheel; heat; mass; hard to print |
| E. Separate hub wheel, rotor behind spokes | Hub motor | Conventional wheel | Spokes vs blades; loses the duct-wall-is-rim idea |
| F. Rotor thrust only | None | No wheel hardware | Not independent of the rotor; uncontrollable on slopes |
| G. Four add-on wheels | Beside pods | Easy | Excluded by the brief; adds mass and drag in every pose |

Option A is the baseline because it keeps the rotor isolated and gives positive drive with printable parts. Option B is the cheapest fallback to try first on a bench rig.

## 4. Appearance and manufacturing

- **Fuselage:** a tapered, superelliptic-section loft, 300 mm long and 66 x 56 mm at the widest, with a 2 mm shell.
- **Integrated hinges:** one hull-shaped plate pair per shoulder blends into the fuselage skin; the arm knuckle sits between the plates on a pin. Right-hand arms reuse left-hand parts with mirrored plates.
- **Access panels:** nose cone, dorsal hatch, belly hatch, two service panels with cooling slots, and tail cap, with 0.35 mm seam gaps and M2 fastener positions (placeholder).
- **Finish:** pearl-white shell, graphite panels and arms, anodised-orange hinge hardware, black tyres. Colour is presentation only.
- **Materials (assumed, untested):** PA12-CF for rims, plates, arms and shell; TPU 95A tyres; POM rollers; CFRP tube spars; steel pins.
- **Printing limits:** the fuselage is 300 mm long, longer than common 220-256 mm print beds, so it needs a split-line design (not done) or a large printer. The ring (about 150 mm) fits, but its inner gear teeth and V-rail need support or careful orientation.

## 5. Mass, centre of gravity, ground clearance

Mass is an estimate: about 1.33 kg with the CAD placeholders (pods 725 g, fuselage and internals 410 g, arms 197 g), about 604 g of it placeholder-class. With the Rev C parts list the estimate rises to about 1.9 kg (`bom/bom_totals.json`).

| Pose | CG x | CG z (fuselage frame) |
|---|---|---|
| Flight | +5.0 mm | +20.5 mm (about 35 mm below the rotor plane) |
| Ground | +5.0 mm | -0.2 mm |
| Compact | +5.0 mm | +20.5 mm |

The CG moves about 21 mm vertically between flight and ground poses, so a flight controller would need configuration-aware inertia. About 54 % of the mass sits at the arm ends, which also raises the moment of inertia.

Ground pose: track 183 mm, wheelbase 316 mm, fuselage underside 54 mm above the tyre plane, arms, plates and pylon 63-66 mm above it, CG about 80 mm above ground. Static tip-over angles are about 49 degrees sideways and 62-64 degrees fore and aft. Cornering, braking, slopes and obstacles were not analysed.

## 6. Aerodynamic geometry (not simulation)

Projected silhouette areas of the externally visible parts, rasterised at 0.6 mm per pixel. Source: `cad/aero_geom.py`; output `sim/clearance/aero_geometry.json`.

| Pose / view | Total (cm2) | Rings alone | Fuselage alone | Arms alone | Pod internals alone |
|---|---|---|---|---|---|
| Flight, front | 226 | 90 | 36 | 26 | 31 |
| Flight, side | 268 | 89 | 83 | 1 | 9 |
| Flight, top | 671 | 222 | 177 | 32 | 188 |
| Flight, 10 deg nose-down | 419 | 182 | 50 | 19 | 15 |
| Flight, 20 deg nose-down | 564 | 258 | 77 | 6 | 25 |
| Flight, 30 deg nose-down | 641 | 289 | 103 | 14 | 62 |
| Ground, front | 185 | 88 | 35 | 1 | 11 |
| Ground, side | 334 | 102 | 84 | 1 | 89 |

"Alone" columns do not sum to the total. Ring throat area is 143 cm2 each. These are areas, not drag; no drag coefficient is derived from them.

Geometric penalty inventory: four wide discs (40 % of the flight frontal silhouette); 36 tyre lugs per ring on the duct exterior; ring gear, rollers and pinion inside the throat; hub, spokes, motor and pylon in the slipstream; hinge and seam gaps; an unfaired arm-to-pod junction; no designed inlet lip radius; exposed transformation hardware at each shoulder.
