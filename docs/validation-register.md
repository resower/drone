# Validation and issue register

Severity and proposals are engineering judgement, not measured risk. Status of every item: open.

| # | Area | Issue | Why it matters | Proposed check |
|---|---|---|---|---|
| 1 | Locking | No J1 lock designed; stop-lug positions unvalidated | Thrust must not back-drive the hinge | Pin or detent lock; go/no-go gauges; cycle test |
| 2 | Locking | J2 needs a mechanical lock in ground mode (about 0.15 N m static plus shock) | Wheel is a cantilever off a small joint | Static load rig at 1.5x then 3x estimated load |
| 3 | Transition | Lift torque about 0.23 N m per J2 (estimate) with placeholder actuators | Friction and terrain add demand | Measure on the bench rig |
| 4 | Kinematics | Allowed (J1, J2) region is non-rectangular | Wrong move order collides | Firmware interlock and planner; hard stops |
| 5 | Rotor isolation | Rotor disc is vertical beside the ground in rover mode; blades exposed | Debris, injury, tip contact | Motor brake and lock, guard, rotor-off interlock |
| 6 | Blade gap | 4 mm tip gap with printed tolerances and ring runout | Blade strike | Metrology of printed rings; runout limits |
| 7 | Ring structure | 2 mm printed wall carries ground load through 3 rollers | Ovalisation, roller overload, cracking | FEA, then load-to-failure of a printed ring |
| 8 | Drive | Printed Z = 92 ring gear and pinion, open to dust | Wear, jam, noise | Gear wear test with sand; consider options B or C |
| 9 | Traction | Four independent drives, skid-steer scrub | Wheel slip, motor sizing | Drive test on several surfaces |
| 10 | Ring in flight | Rim free to rotate | Wake swirl may spin it | Rim brake or pinion hold |
| 11 | CG and inertia | CG moves about 21 mm; 54 % of mass at arm ends | Controller tuning, stability | Measured CG and inertia per pose |
| 12 | Structure | Printed 4 mm plates and arm at the thrust load | Bending, creep | FEA and ground vibration test |
| 13 | Vibration | Cantilevered pods on printed arms | Sensor noise, fatigue | Accelerometer survey on a thrust stand |
| 14 | Ground | Static tip-over only (49 deg side) | Rollover when turning | Multibody simulation; tilt-table test |
| 15 | Debris | Open ring on the ground | Ingress into gears, rollers, motor | Seals or covers; dust test |
| 16 | Repairability | About 96 STL files; shell longer than most print beds | Field repair and printing | Split-line design; spares plan |
| 17 | Electrical | 16 actuators (4 rotor, 4 wheel, 4 J1, 4 J2); wires cross two joints | Harness fatigue, current, EMI near compass | Harness routing model; flex-life test |
| 18 | Flight control | Configuration-dependent mixer and state machine, no joint-angle sensors in CAD | Wrong mode in flight | Absolute encoders or limit switches; failsafe on joint fault |
| 19 | Aerodynamics | Four wide discs, lugs, gaps, wake obstructions | Drag and thrust loss unknown | CFD plan in `test-plan.md` |
| 20 | Thermal | Motors in a nearly enclosed ring; TPU on PA12 | Overheating, tyre delamination | Thermal soak on a thrust stand; bond test |
| 21 | Speed mode | Wing not modelled; rear pair in front pair's wake; 100 km/h wing area (830 cm2) does not fit between rings | Speed mode is the least proven mode | Wing CAD; wake study; thrust-stand data for the chosen motor and propeller |
| 22 | Packaging | Real J1/J2 servos, 4-in-1 ESC and companion computer exceed CAD placeholder bays | CAD does not represent a buildable vehicle | Arm and bay redesign around the Rev C parts |

## Assumptions and limitations

- All clearances use project-defined thresholds; none come from a standard.
- Sampled clearance has about 1.5 mm error. The base configurations and 15 path states were verified with exact distances.
- Motors, actuators, battery, electronics, fasteners and the propeller in the CAD are placeholders that fix size and position only. The propeller is not an aerodynamic design.
- Masses and CG use volume x density x assumed fill factors plus placeholder masses.
- No structural, thermal, vibration, fatigue, CFD, electrical, firmware or flight analysis has been done.
- Joint angles were swept at 10 degree resolution.
- No part has been printed, assembled or tested.
- The Fusion build script has not been run inside Fusion.
