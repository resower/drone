# Performance estimates (Rev C)

All figures are first-principles calculations from `sim/performance/perf.py`. They are best-case unless marked "typ". **None are measured.** No thrust-stand, drive or flight data exists for this design.

## Assumptions

- Mass 2.0 kg (parts list in `bom/`, uncertainty about +/-15 %).
- Battery 6S 1400 mAh (22.2 V nominal), 85 % usable: 26.4 Wh.
- Propeller disc: 5.1 in (diameter 127 mm). Figure of merit 0.55, drive efficiency 0.80, 25 W avionics and servo allowance in hover.
- Rover: 18 km/h, rolling-resistance coefficient 0.04, drive efficiency 0.5.
- Speed mode: body/ring drag area 0.02 m2 (best) or 0.03 m2 (typ), propulsive efficiency 0.40-0.50, 80 % of usable energy.
- Available thrust at 150 km/h taken as 30 % of static thrust, a generic ratio not tied to a tested motor and propeller.

## Results

| Mode | Power | Endurance | Range |
|---|---|---|---|
| Hover | 586 W | 2.7 min | n/a |
| Normal flight, 50 km/h | 549 W | 2.9 min | 2.4 km |
| Rover, 18 km/h (best / typical) | 21 / 41 W | 76 min (best) | 22.8 / 11.6 km |
| Speed, 100 km/h (best / typical) | 632 / 992 W | 2.0 / 1.3 min | 3.3 / 2.1 km |
| Speed, 150 km/h (best / typical) | 2200 / 3580 W | 0.6 / 0.4 min | 1.4 / 0.9 km |

At 150 km/h the available thrust (about 22 N) is close to the estimated drag (23.5 N best, 34 N typical), so a top speed of 120-130 km/h is more likely than 150 km/h.

A wing sized for level flight at 100 km/h needs about 830 cm2 (369 cm2 at 150 km/h) at a lift coefficient of 0.5. The 830 cm2 wing does not fit between the rings, so the rotors would share lift at 100 km/h.

## Known gaps

- Front-to-rear wake interference in speed mode (estimated 10-20 % thrust loss) is not included in the table.
- The CAD still shows placeholder component sizes. The J1/J2 servos (about twice the arm fairing) and the 4-in-1 ESC and companion computer (larger than their bays) do not fit the current CAD; the arm and bay need a redesign.
- Rover consumption depends heavily on whether the joint servos are mechanically locked or hold position electrically (typical figure assumes holding).
