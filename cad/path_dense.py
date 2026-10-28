"""Dense (2.5 deg) interpolation of the planned path; sample-based clearances (+-~0.8 mm vs exact) at every sub-step."""
import json, numpy as np, kin
s = json.load(open('../build/sequence_flight_ground.json'))['flight_to_ground']['path']
G = kin.groups(2.5); rows = []
for a, b in zip(s[:-1], s[1:]):
    for t in (0.25, 0.5, 0.75, 1.0):
        ph = a[0] + (b[0] - a[0])*t; rh = a[1] + (b[1] - a[1])*t
        cfg = dict(phi_F=ph, rho_F=rh, phi_R=180 - ph, rho_R=rh); cl = kin.config_clearances(cfg, G); k, m = kin.margin(cl)
        rows.append(dict(phi=ph, rho=rh, pair=k, dist=float(cl[k]), margin=float(m)))
w = min(rows, key=lambda r: r['margin']); print('sub-steps', len(rows), 'worst', w)
json.dump(rows, open('../build/path_dense.json', 'w'), indent=1)
