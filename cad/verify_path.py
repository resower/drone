"""Exact clearances for every state on the planned flight->ground path (lock-step, front/rear mirrored)."""
import json, verify, kin
from params import P
s = json.load(open('../build/sequence_flight_ground.json'))['flight_to_ground']
Gs = kin.groups(2.5); rows = []
for (ph, rh) in s['path']:
    cfg = dict(phi_F=ph, rho_F=rh, phi_R=180 - ph, rho_R=rh)
    r = verify.check(cfg, Gs, screen=12.0)
    k, x = min(r.items(), key=lambda kv: kv[1]['exact_mm'] - kv[1]['required_mm'])
    rows.append(dict(phi=ph, rho=rh, tightest=k, exact_mm=x['exact_mm'], required_mm=x['required_mm'], margin_mm=x['exact_mm'] - x['required_mm'], n_pairs=len(r)))
    print(rows[-1], flush=True)
json.dump(rows, open('../build/verify_path_exact.json', 'w'), indent=1)
