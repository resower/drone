import json, numpy as np, kin
from params import P
G = kin.groups(2.5)
f, s = P['cfg_flight'], P['cfg_speed']
# order: sweep arms first (rho=0), then roll pods
states = []
N = 8
for i in range(N + 1):
    t = i / N
    states.append(dict(phi_F=f['phi_F'] + t * (s['phi_F'] - f['phi_F']), phi_R=f['phi_R'] + t * (s['phi_R'] - f['phi_R']), rho_F=0.0, rho_R=0.0))
for i in range(1, N + 1):
    t = i / N
    states.append(dict(phi_F=s['phi_F'], phi_R=s['phi_R'], rho_F=t * s['rho_F'], rho_R=t * s['rho_R']))
out = []; worst = 99
for c in states:
    k, m = kin.margin(kin.config_clearances(c, G)); worst = min(worst, m)
    corners = {}
    for cn in kin.CORNERS:
        ph, rho, TA, TP = kin.corner_state2(cn, c)
        corners[cn] = dict(arm=TA.tolist(), pod=TP.tolist())
    out.append(dict(angles=c, corners=corners, margin=round(float(m), 2), worst=k))
    print({k2: round(v, 1) for k2, v in c.items()}, round(float(m), 2), k, flush=True)
json.dump(out, open('../build/path_flight_speed.json', 'w'))
print('min margin', worst)
