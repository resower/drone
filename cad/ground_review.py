"""Geometry-only ground-mode review: ground clearance, static tip-over angles, and quasi-static lift torque for the roll transition.
All masses are ESTIMATES (mass_cg_v2.json); results are static geometry, not dynamics, not tests."""
import json, math, numpy as np, kin, library
from params import P, D
G = kin.groups(2.5); I4 = np.eye(4); g = 9.81
mass = json.load(open('../build/mass_cg_v2.json'))
def world_pts(grp, T): return G[grp].pts @ T[:3, :3].T + T[:3, 3]
def lowest(cfg):
    st = {c: kin.corner_state(c, cfg) for c in kin.CORNERS}; low = {}
    low['FUS'] = world_pts('FUS', I4)[:, 2].min()
    for c in kin.CORNERS:
        low['TYRE_' + c] = world_pts('TYRE', st[c][3])[:, 2].min(); low['POD_' + c] = world_pts('POD', st[c][3])[:, 2].min()
        low['CONN_' + c] = world_pts('CONN', st[c][3])[:, 2].min(); low['ARM_' + c] = world_pts('ARM', st[c][2])[:, 2].min()
        low['PLATE_' + c] = world_pts('PLATE_' + c, I4)[:, 2].min()
    return low, st
out = {}
# --- ground configuration
low, st = lowest(P['cfg_ground']); floor = min(low[k] for k in low if k.startswith('TYRE'))
out['ground'] = dict(tyre_lowest_z_mm={k: round(v, 2) for k, v in low.items() if k.startswith('TYRE')},
                     clearance_above_tyre_plane_mm={k: round(v - floor, 1) for k, v in low.items() if not k.startswith('TYRE')})
# contact patch lateral/longitudinal positions: points of each tyre within 1.5 mm of the floor
pts = []
for c in kin.CORNERS:
    w = world_pts('TYRE', st[c][3]); sel = w[w[:, 2] < floor + 1.5]; pts.append(sel[:, :2].mean(0))
pts = np.array(pts); track = pts[:, 1].max() - pts[:, 1].min(); wb = pts[:, 0].max() - pts[:, 0].min()
cg = np.array(mass['cfg_ground']['cg']); h = cg[2] - floor
out['ground']['contact_centres_xy_mm'] = pts.round(1).tolist(); out['ground']['track_mm'] = round(float(track), 1); out['ground']['wheelbase_mm'] = round(float(wb), 1)
out['ground']['cg_height_above_ground_mm_ESTIMATE'] = round(float(h), 1); out['ground']['cg_xy_mm_ESTIMATE'] = [round(float(cg[0]), 1), round(float(cg[1]), 1)]
out['ground']['static_roll_tipover_deg'] = round(math.degrees(math.atan((track/2 - abs(cg[1]))/h)), 1)
out['ground']['static_pitch_tipover_fwd_deg'] = round(math.degrees(math.atan((pts[:, 0].max() - cg[0])/h)), 1)
out['ground']['static_pitch_tipover_aft_deg'] = round(math.degrees(math.atan((cg[0] - pts[:, 0].min())/h)), 1)
# --- flight configuration resting on the ground
low, st = lowest(P['cfg_flight']); rest = min(low.values())
out['flight_resting'] = dict(lowest_feature=min(low, key=low.get), lowest_z_mm=round(rest, 1),
                             pod_parts_above_rest_plane_mm={k: round(v - rest, 1) for k, v in low.items() if k.startswith(('TYRE', 'POD', 'CONN'))})
# --- lift transition: body height vs roll with front/rear lock-step yaw schedule from the planned path
seq = json.load(open('../build/sequence_flight_ground.json'))['flight_to_ground']['path']
def height(phi, rho):
    cfg = dict(phi_F=phi, rho_F=rho, phi_R=180 - phi, rho_R=rho); l, _ = lowest(cfg)
    support = {k: v for k, v in l.items()}; k = min(support, key=support.get); return -support[k], k    # height of fuselage origin above ground if resting on the lowest feature
rows = []
for (ph, rh) in seq:
    h_, k = height(ph, rh); rows.append(dict(phi=ph, rho=rh, origin_height_mm=round(h_, 1), supported_by=k))
out['path_support'] = rows
# fine roll scan at the final yaw (phi=0) 0..90
scan = []
for rho in np.arange(0, 91, 2.5):
    h_, k = height(0.0, float(rho)); scan.append((float(rho), h_, k))
out['roll_scan_phi0'] = [dict(rho=a, origin_height_mm=round(b, 2), supported_by=c) for a, b, c in scan]
m = mass['cfg_ground']['mass_g']/1000.0
tau = []
for (a, b, _), (a2, b2, _) in zip(scan[:-1], scan[1:]):
    dh = (b2 - b)/1000.0; dth = math.radians(a2 - a); tau.append(max(0.0, m*g*dh/dth/4.0))    # per joint, 4 joints share the lift equally, quasi-static, frictionless
out['lift_torque_per_J2_Nm_ESTIMATE_quasi_static'] = dict(peak=round(max(tau), 3), mass_kg_estimate=round(m, 3), note='geometry x estimated mass; excludes friction, wheel-ground slip, servo/gearbox efficiency, dynamics')
json.dump(out, open('../build/ground_review.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ('roll_scan_phi0', 'path_support')}, indent=1))
print([ (r['rho'], r['origin_height_mm'], r['supported_by']) for r in out['roll_scan_phi0'][::4]])
