# Test and simulation plan

This is a plan, not a record of work done. Nothing below has been executed.

## Staged programme

**A. Bench rig, one corner, unpowered.** Print one shoulder, arm and pod with dummy motors and blade. Confirm J1 and J2 ranges against `media/renders/joint_range_map.png`, walk the staircase by hand, measure friction and play. Gate: all poses reached with no contact and a repeatable lock.

**B. Four-corner rover, rotors off.** Fit the four wheel gearmotors without blades or rotor motors. Drive on several surfaces; measure lift torque, hold torque and tip-over; re-measure CG. Gate: the 0.15 N m and 0.23 N m estimates are replaced by measured values.

**C. Thrust stand and aero, no flight.** One pod on a load cell with a guard, with and without the ring; measure runout and tip gap under load.

**D. Simulation.** Multibody (joints, contact, rollover) and CFD, each calibrated to the stage B and C measurements. Every number labelled by origin: geometric, simulated or measured.

**E. Laboratory qualification.** Static and fatigue load tests on rings, plates and arms; vibration and thermal tests; harness flex-life.

**F. Supervised flight validation.** Only after A-E, under written authorisation from the relevant aviation authority. Start with a tethered rig in an enclosed test area, then incremental hover, with a safety officer and written go/no-go criteria.

## CFD plan

1. **Inputs:** `CF2_flight.step` and the other pose assemblies, simplified to an aero shell, plus the unsimplified case as a sensitivity run.
2. **Solver:** an open-source RANS code such as OpenFOAM or SU2. Steady, k-omega SST, moving reference frame for the rotor zone.
3. **Verification:** three systematically refined meshes per case with a grid-convergence index; report y+ range; domain at least ten body lengths downstream and five elsewhere; convergence criteria written before running.
4. **Study matrix** (relative comparisons): rotor alone vs rotor in ring at equal RPM; full vehicle in flight pose at several inflow speeds and pitch angles; variants (smooth vs lugged tyre, gear teeth covered vs open, gaps sealed vs open, hub fairing, inlet lip); ground pose in ground effect; speed pose including front-to-rear wake.
5. **Physical validation before trusting any CFD:** thrust-stand test with and without the ring; wind-tunnel or open-jet drag of a 1:1 print in each pose; flow visualisation.

## Open design work

- Compaction: smaller rings relative to the fuselage, a longer or folding fuselage, a third fold axis on each arm, pods that fold flat against the fuselage, cranked arms with pods rolled to different heights (needs a ground-contact solution).
- Arm and bay redesign for the Rev C servos, ESC and companion computer.
- Speed-mode wing and control surfaces in CAD.
