"""Transformation-sequence planner.  Fore/aft-mirrored lock-step moves: phi_R = 180 - phi_F, rho_R = rho_F (symmetric left/right).
BFS over the (phi, rho) lattice using the checked feasible state sets + cross checks; returns shortest single-joint-step path.
usage: python3 seq.py  (reads out/states_F.json, states_R.json) -> out/sequence_*.json"""
import sys, json, collections, itertools, numpy as np
import kin
from params import P
OUT = '../build/'
F = {(s['phi'], s['rho']) for s in json.load(open(OUT + 'states_F.json'))}
R = {(s['phi'], s['rho']) for s in json.load(open(OUT + 'states_R.json'))}
Gc = kin.groups(6.0); G = kin.groups(2.5)
_cache = {}
def ok(phi, rho):
    """lock-step state feasible? (front state, mirrored rear state, front/rear cross)"""
    key = (phi, rho)
    if key in _cache: return _cache[key]
    pr = 180 - phi
    res = (phi, rho) in F and (pr, rho) in R
    if res:
        cfg = dict(phi_F=phi, rho_F=rho, phi_R=pr, rho_R=rho)
        res, _, _ = kin.cross_ok(cfg, Gc, slack=2.5)
        if res: res, _, _ = kin.cross_ok(cfg, G, slack=0.0)
    _cache[key] = res; return res

def bfs(start, goal, phis, rhos, step=10):
    prev = {start: None}; q = collections.deque([start])
    while q:
        c = q.popleft()
        if c == goal: break
        for d in ((step, 0), (-step, 0), (0, step), (0, -step)):
            n = (c[0] + d[0], c[1] + d[1])
            if n in prev or n[0] not in phis or n[1] not in rhos: continue
            if ok(*n): prev[n] = c; q.append(n)
    if goal not in prev: return None
    path = []; c = goal
    while c is not None: path.append(c); c = prev[c]
    return path[::-1]

def compress(path):
    """merge collinear single-joint steps into moves"""
    moves = []; cur = None
    for a, b in zip(path[:-1], path[1:]):
        kind = 'yaw' if a[0] != b[0] else 'roll'
        if cur and cur[0] == kind: cur[2] = b[1] if kind == 'roll' else b[0]
        else:
            cur = [kind, a[1] if kind == 'roll' else a[0], b[1] if kind == 'roll' else b[0]]; moves.append(cur)
    return moves

if __name__ == '__main__':
    phis = set(range(-60, 241, 10)); rhos = set(range(-180, 181, 10))
    out = {}
    for name, (a, b) in dict(flight_to_ground=((50, 0), (0, 90)), ground_to_flight=((0, 90), (50, 0))).items():
        if not (ok(*a) and ok(*b)): print(name, 'endpoint infeasible', ok(*a), ok(*b)); continue
        path = bfs(a, b, phis, rhos)
        if path is None: print(name, 'NO PATH'); out[name] = None; continue
        moves = compress(path); print(name, 'path of', len(path), 'states; moves:', moves)
        # fine margins along the path
        tr = []
        for (ph, rh) in path:
            cfg = dict(phi_F=ph, rho_F=rh, phi_R=180 - ph, rho_R=rh)
            cl = kin.config_clearances(cfg, G); k, m = kin.margin(cl); tr.append(dict(phi=ph, rho=rh, worst_pair=k, worst_dist=float(cl[k]), margin=float(m)))
        out[name] = dict(path=path, moves=moves, trace=tr, min_margin=min(t['margin'] for t in tr))
        print('   min margin along path %.1f mm' % out[name]['min_margin'])
        break
    json.dump(out, open(OUT + 'sequence_flight_ground.json', 'w'), indent=1)
