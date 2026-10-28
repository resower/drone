import json, csv, mass, library
L = library.lib(); rows = mass.part_table()
PROC = {'PA12-CF (SLS/FDM)': 'SLS PA12 / CF-nylon FDM (print orientation drives strength; unproven)', 'TPU 95A': 'FDM TPU (or cast urethane tread bonded to rim)', 'CFRP tube': 'Off-the-shelf pultruded/rolled carbon tube, cut to length',
        'Acetal (POM)': 'Machined or injection-moulded roller, bearing pressed in', 'Steel': 'Standard hardware / hobby-grade pinion', 'Electronics': 'Off-the-shelf catalogue-class part (size placeholder only)', 'Placeholder block': 'Placeholder geometry only - to be designed'}
QTY = {'fus': 1, 'pod': 4, 'arm': 4}
out = []
for n, r in rows.items():
    fr = L[n]['frame']; q = QTY[fr] if n not in ('shoulder_plate_upper', 'shoulder_plate_lower', 'j1_hinge_pin') else 4
    out.append(dict(part=n, subsystem=r['group'], qty=q, material=r['material'], process=PROC.get(r['material'], ''), mass_each_g_ESTIMATE=round(r['mass_g'], 1), mass_total_g_ESTIMATE=round(r['mass_g']*q, 1),
                    mass_basis=r['basis'], placeholder='YES' if r['placeholder'] else 'no', role=L[n]['role'], note=L[n]['note']))
out.sort(key=lambda d: (d['subsystem'], d['part']))
with open('../build/CF2_BOM.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
tot = sum(d['mass_total_g_ESTIMATE'] for d in out); ph = sum(d['mass_total_g_ESTIMATE'] for d in out if d['placeholder'] == 'YES')
print(len(out), 'lines total est. mass %.0f g, of which placeholder-class %.0f g' % (tot, ph))
bysub = {}
for d in out: bysub[d['subsystem']] = bysub.get(d['subsystem'], 0) + d['mass_total_g_ESTIMATE']
print({k: round(v) for k, v in bysub.items()})
