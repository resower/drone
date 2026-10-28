import json, math, numpy as np, kin
from params import P, D
G = kin.groups(2.5)
rows = []
for phiF in (60, 65, 70, 75, 80, 85):
    for rho in (-45, -60, -75, -90):
        cfg = dict(phi_F=float(phiF), phi_R=180.0 - phiF, rho_F=float(rho), rho_R=float(-rho))
        cl = kin.config_clearances(cfg, G)
        k, m = kin.margin(cl)
        # thrust vectors
        th = {}
        for c in kin.CORNERS:
            ph, r, TA, TP = kin.corner_state(c, cfg)
            th[c] = (TP[:3, :3] @ np.array([0, 0, 1.0])).round(3).tolist()
        fwd = np.mean([th[c][0] for c in th]); lat = np.mean([abs(th[c][1]) for c in th]); up = np.mean([th[c][2] for c in th])
        rows.append(dict(phiF=phiF, rho=rho, margin=round(float(m), 2), worst=k, fwd=round(float(fwd), 3), lat=round(float(lat), 3), up=round(float(up), 3)))
        print(rows[-1], flush=True)
json.dump(rows, open('../build/speed_search2.json', 'w'), indent=1)
