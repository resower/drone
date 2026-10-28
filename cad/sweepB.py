"""Rev-B exploration: checkerboard shoulder heights (FL,RR at +dz ; FR,RL at -dz) and per-corner pod roll (0 = ring above arm, 180 = below).
usage: python3 sweepB.py DZ"""
import sys, json, time, itertools, numpy as np, kin
DZ = float(sys.argv[1]); G = kin.groups(2.5); Gc = kin.groups(6.0)
dz = dict(FL=DZ, RR=DZ, FR=-DZ, RL=-DZ)
pats = {'chk_A': dict(rho_FL=0, rho_RR=0, rho_FR=180, rho_RL=180), 'chk_B': dict(rho_FL=180, rho_RR=180, rho_FR=0, rho_RL=0),
}
found = []; t0 = time.time(); n = 0
for name, rp in pats.items():
    for pf in range(90, 191, 10):
        for pr in range(-10, 91, 10):
            cfg = dict(phi_F=pf, phi_R=pr, rho_F=0, rho_R=0, **rp); n += 1
            ok, key, m = kin.full_ok(cfg, Gc, dz, slack=2.5)
            if not ok: continue
            ok, key, m = kin.full_ok(cfg, G, dz, 0.0)
            if not ok: continue
            lo, hi = kin.bbox2(cfg, G, dz); d = hi - lo
            found.append(dict(pattern=name, phi_F=pf, phi_R=pr, dims=d.tolist(), vol_L=float(np.prod(d)/1e6), foot_cm2=float(d[0]*d[1]/100)))
    print(name, 'done', len(found), '%.0fs' % (time.time() - t0), flush=True)
found.sort(key=lambda t: t['vol_L'])
json.dump(found, open('../build/revB_dz%d.json' % DZ, 'w'), indent=1)
for f in found[:6]: print(f['pattern'], f['phi_F'], f['phi_R'], np.round(f['dims']), round(f['vol_L'], 2), round(f['foot_cm2']))
