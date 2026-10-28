"""Stage-1 sweep B: (A) per-side feasible states on a fine grid, (B) compact-pose search over feasible front x rear combinations.
usage: python3 sweep2.py A F|R   |   python3 sweep2.py B"""
import sys, json, time, itertools, numpy as np, kin
from params import P
OUT = '../build/'
phis = list(range(-60, 241, 10)); rhos = list(range(-180, 181, 10))

def ext_of(side, ph, rh, G):
    cs = ('FL', 'FR') if side == 'F' else ('RL', 'RR')
    cfg = dict(phi_F=ph, rho_F=rh, phi_R=ph, rho_R=rh)
    lo = np.full(3, 1e9); hi = np.full(3, -1e9)
    for c in cs:
        _, _, TA, TP = kin.corner_state(c, cfg)
        for g, T in (('POD', TP), ('CONN', TP), ('ARM', TA)):
            p = G[g].pts @ T[:3, :3].T + T[:3, 3]; lo = np.minimum(lo, p.min(0)); hi = np.maximum(hi, p.max(0))
    return lo, hi

if sys.argv[1] == 'A':
    side = sys.argv[2]; G = kin.groups(2.5); Gc = kin.groups(6.0); act = ('FL', 'FR') if side == 'F' else ('RL', 'RR')
    res = []; t0 = time.time()
    for ph in phis:
        for rh in rhos:
            cfg = dict(phi_F=ph, rho_F=rh, phi_R=ph, rho_R=rh)
            ok, key, m = kin.side_ok(cfg, Gc, act, slack=2.5)
            if ok:
                cl = kin.config_clearances(cfg, G, active=act); k, m = kin.margin(cl); ok = m >= 0
            if ok:
                lo, hi = ext_of(side, ph, rh, G); res.append(dict(phi=ph, rho=rh, margin=float(m), lo=lo.tolist(), hi=hi.tolist()))
        print(side, ph, len(res), '%.0fs' % (time.time() - t0), flush=True)
    json.dump(res, open(OUT + 'states_%s.json' % side, 'w'))
else:
    G = kin.groups(2.5); Gc = kin.groups(6.0)
    F = json.load(open(OUT + 'states_F.json')); R = json.load(open(OUT + 'states_R.json'))
    # static extents: fuselage + plates
    slo = G['FUS'].pts.min(0).copy(); shi = G['FUS'].pts.max(0).copy()
    for c in kin.CORNERS: slo = np.minimum(slo, G['PLATE_' + c].pts.min(0)); shi = np.maximum(shi, G['PLATE_' + c].pts.max(0))
    combos = []
    for f in F:
        for r in R:
            lo = np.minimum(np.minimum(slo, f['lo']), r['lo']); hi = np.maximum(np.maximum(shi, f['hi']), r['hi']); d = hi - lo
            combos.append((float(np.prod(d)), float(d[0]*d[1]), f, r, d.tolist()))
    KEY = sys.argv[2] if len(sys.argv) > 2 else 'vol'
    keyf = dict(vol=lambda t: t[0], foot=lambda t: t[1], maxdim=lambda t: max(t[4][0], t[4][1]))[KEY]
    combos.sort(key=keyf); print('states F', len(F), 'R', len(R), 'combos', len(combos), flush=True)
    found = []; t0 = time.time(); n = 0
    for vol, foot, f, r, d in combos:
        cfg = dict(phi_F=f['phi'], rho_F=f['rho'], phi_R=r['phi'], rho_R=r['rho'])
        n += 1
        ok, key, m = kin.cross_ok(cfg, Gc, slack=2.5)
        if ok:
            cl = kin.cross_clearances(cfg, G); key = min(cl, key=lambda q: cl[q] - kin.thr_of(q)); m = cl[key] - kin.thr_of(key); ok = m >= 0
        if ok:
            found.append(dict(cfg=cfg, vol_L=vol/1e6, dims=d, margin=float(m), pair=key)); print('FEASIBLE', cfg, 'dims', np.round(d), 'vol %.2f L' % (vol/1e6), 'foot %.0f cm2' % (foot/100), flush=True)
            if len(found) >= 12: break
        if n % 200 == 0: print('evaluated', n, '%.0fs' % (time.time() - t0), 'current vol %.2f' % (vol/1e6), flush=True)
    json.dump(found, open(OUT + 'compact_found_%s.json' % KEY, 'w'), indent=1)
