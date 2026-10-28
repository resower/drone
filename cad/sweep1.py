"""Stage-1 sweep A: single-pair (left/right symmetric) joint-range maps.  usage: python3 sweep1.py F|R"""
import sys, json, time, numpy as np, kin
from params import P
which = sys.argv[1]
G = kin.groups(2.5)
phis = list(range(-20, 201, 10)); rhos = list(range(-100, 101, 10))
act = ('FL', 'FR') if which == 'F' else ('RL', 'RR')
res = {}
t0 = time.time()
for ph in phis:
    for rh in rhos:
        cfg = dict(phi_F=ph, rho_F=rh, phi_R=ph, rho_R=rh)
        cl = kin.config_clearances(cfg, G, active=act)
        k, m = kin.margin(cl)
        res['%d,%d' % (ph, rh)] = dict(margin=float(m), pair=k, d=float(cl[k]))
    print(which, ph, '%.0fs' % (time.time() - t0), flush=True)
json.dump(dict(phis=phis, rhos=rhos, res=res), open('../build/sweep1_%s.json' % which, 'w'))
