"""Exact (OCC BRepExtrema) minimum distances between solids for the three configurations; pairs screened by the sample engine first.
Output out/verify_exact.json.  Required clearances are the project's own THR values (kin.THR) -- design targets, not standards."""
import json, sys, time, numpy as np, cadquery as cq
import library, kin, parts_body as pb
from params import P

L = library.lib(); I4 = np.eye(4)
def loc(T):
    from OCP.gp import gp_Trsf
    t = gp_Trsf(); M = np.asarray(T, float); t.SetValues(*[float(M[r, c]) for r in range(3) for c in range(4)]); return cq.Location(t)
def placed(names, T):
    return cq.Compound.makeCompound([L[n]['shape'].moved(loc(T)) for n in names])
POD_N = ['rolling_rim', 'tyre', 'stator_hub_spokes', 'support_roller_1', 'support_roller_2', 'support_roller_3', 'drive_pinion', 'wheel_gearmotor_placeholder', 'rotor_motor_placeholder', 'rotor_prop_placeholder']
armbody = L['arm_fairing']['shape'].cut(cq.Workplane("XY").workplane(offset=-30).circle(P['knuckle_r'] + 0.3).extrude(60).val())
FUS = pb.fuselage_outer()
def mir(sh, c):
    if kin.SY[c] < 0: sh = sh.mirror('XZ')
    if kin.SX[c] < 0: sh = sh.mirror('YZ')
    return sh
PLATES = {c: cq.Compound.makeCompound([mir(L['shoulder_plate_upper']['shape'], c), mir(L['shoulder_plate_lower']['shape'], c)]) for c in kin.CORNERS}
def exact(a, b): return a.distance(b)

def check(cfg, Gs, screen=14.0):
    st = {c: kin.corner_state(c, cfg) for c in kin.CORNERS}
    ARM = {c: armbody.moved(loc(st[c][2])) for c in kin.CORNERS}
    POD = {c: placed(POD_N, st[c][3]) for c in kin.CORNERS}
    CON = {c: placed(['pylon_wrist_bridge'], st[c][3]) for c in kin.CORNERS}
    samp = kin.config_clearances(cfg, Gs); out = {}
    objs = {}
    for c in kin.CORNERS: objs['ARM_' + c] = ARM[c]; objs['POD_' + c] = POD[c]; objs['CONN_' + c] = CON[c]; objs['PLATE_' + c] = PLATES[c]
    objs['FUS'] = FUS
    for k, v in samp.items():
        if v > screen: continue
        a, b = k.split('|'); out[k] = dict(sample_mm=float(v), exact_mm=float(exact(objs[a], objs[b])), required_mm=float(kin.thr_of(k)) if hasattr(kin, 'thr_of') else None)
    return out

if __name__ == '__main__':
    Gs = kin.groups(2.5); res = {}
    import sys
    names = sys.argv[1:] or ['cfg_flight', 'cfg_ground', 'cfg_compact']
    for n in names:
        t = time.time(); res[n] = check(P[n], Gs)
        w = min(res[n].items(), key=lambda kv: kv[1]['exact_mm'] - (kv[1]['required_mm'] or 0))
        print(n, len(res[n]), 'pairs; tightest vs requirement:', w[0], w[1], '%.0fs' % (time.time() - t), flush=True)
    json.dump(res, open('../build/verify_exact_%s.json' % '_'.join(names), 'w'), indent=1)
