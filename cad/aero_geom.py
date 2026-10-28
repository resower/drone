"""Geometry-only aerodynamic measurements of the CF-2 CAD (NO flow solution, NO drag coefficients).
Silhouette (projected) areas along flow directions, ring through-flow areas, exposed-feature inventory.
All outputs are GEOMETRIC MEASUREMENTS of the concept CAD, not simulation results and not physical measurements."""
import json, math, numpy as np, trimesh
from PIL import Image, ImageDraw
import library, assemble, kin
from params import P, D

RES = 0.6   # mm per pixel

def part_meshes(tol=0.4):
    L = library.lib(); M = {}
    for n, d in L.items():
        v, f = d['shape'].tessellate(tol, 0.3)
        M[n] = trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=False)
    return M

def world_meshes(cfg, M, internals=False):
    """list of (group, trimesh in world frame)"""
    out = []
    for i in assemble.instances(cfg):
        if not internals and ('placeholder' in i['part'] and i['part'].split('_')[0] in ('battery', 'fc', 'companion', 'camera', 'gps', 'j1', 'j2', 'wheel', 'rotor_motor') and 'dome' not in i['part']):
            continue
        m = M[i['part']].copy()
        if 'mirror' in i:
            c = i['mirror']
            if kin.SY[c] < 0: m.vertices[:, 1] *= -1; m.invert()
            if kin.SX[c] < 0: m.vertices[:, 0] *= -1; m.invert()
        else:
            m.apply_transform(i['T'])
        grp = i['group'].split('_')[0].split('/')[0]
        if i['part'] in ('tyre', 'rolling_rim'): grp = 'rings'
        elif grp == 'pod': grp = 'rotor_pod_internals'
        out.append((grp, i['part'], m))
    return out

def silhouette_area(meshes, d, groups=None):
    """projected area (cm2) of the union of meshes onto the plane normal to d; per-group exclusive contribution in draw order"""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    u = np.cross(d, [0, 0, 1.0]);
    if np.linalg.norm(u) < 1e-6: u = np.cross(d, [0, 1.0, 0])
    u /= np.linalg.norm(u); v = np.cross(d, u)
    allv = np.vstack([m.vertices for _, _, m in meshes]); pu = allv @ u; pv = allv @ v
    u0, v0 = pu.min() - 5, pv.min() - 5; W = int((pu.max() - u0 + 5)/RES) + 1; H = int((pv.max() - v0 + 5)/RES) + 1
    total = Image.new('1', (W, H), 0); per = {}
    for g, name, m in meshes:
        im = Image.new('1', (W, H), 0); dr = ImageDraw.Draw(im)
        P2 = np.stack([(m.vertices @ u - u0)/RES, (m.vertices @ v - v0)/RES], 1)
        for tri in m.faces:
            dr.polygon([tuple(P2[k]) for k in tri], fill=1)
        a = np.asarray(im); per.setdefault(g, np.zeros_like(a)); per[g] |= a
    tot = np.zeros_like(next(iter(per.values())))
    for a in per.values(): tot |= a
    px = RES*RES/100.0     # cm2 per pixel
    res = dict(total_cm2=float(tot.sum()*px))
    res['by_group_alone_cm2'] = {g: float(a.sum()*px) for g, a in per.items()}
    # exclusive contribution = area that disappears if the group is removed
    res['by_group_exclusive_cm2'] = {}
    for g in per:
        rest = np.zeros_like(tot)
        for h, a in per.items():
            if h != g: rest |= a
        res['by_group_exclusive_cm2'][g] = float((tot & ~rest).sum()*px)
    return res

def flow_dir(pitch_deg, yaw_deg=0.0):
    """flow velocity direction relative to the body: world flow along -x relative to the vehicle at body pitch (nose-down positive).
    returns the unit vector along which the vehicle is projected (flow direction)"""
    p = math.radians(pitch_deg); y = math.radians(yaw_deg)
    # air moves toward -x relative to a vehicle flying +x; body pitched nose-down by p => body x axis tilted down: flow in body frame = (-cos p, 0, ... )
    return np.array([math.cos(p)*math.cos(y), math.cos(p)*math.sin(y), math.sin(p)*(-1.0)*(-1.0)])

if __name__ == '__main__':
    M = part_meshes(); out = {}
    for name in ('cfg_flight', 'cfg_ground', 'cfg_compact'):
        wm = world_meshes(P[name], M)
        r = {}
        # flow along body +x (forward flight, level), plus nose-down pitch, plus side flow, plus top view (vertical flow = hover/descent)
        cases = {'front_x': (1, 0, 0), 'side_y': (0, 1, 0), 'top_z': (0, 0, 1)}
        for k, d in cases.items(): r[k] = silhouette_area(wm, d)
        if name == 'cfg_flight':
            for th in (10, 20, 30):
                dd = (math.cos(math.radians(th)), 0, math.sin(math.radians(th)))    # projection line for nose-down pitch: air arrives from front-above, i.e. along (-cos, 0, -sin) in body axes
                r['front_pitch_%d' % th] = silhouette_area(wm, dd)
        out[name] = r; print(name, {k: round(v['total_cm2'], 1) for k, v in r.items()}, flush=True)
    out['ring_throat_area_cm2_each'] = math.pi*D['R_in']**2/100.0
    out['ring_outer_dia_mm'] = 2*(P['tire_r_out'] + 1.0)
    json.dump(out, open('../build/aero_geometry.json', 'w'), indent=1)
