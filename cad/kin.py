"""CF-2 kinematics + fast clearance engine (surface-sample KD-trees; exact OCC check for final candidates is in verify.py)."""
import math, functools, itertools, numpy as np, trimesh
from scipy.spatial import cKDTree
from params import P, D
import library

CORNERS = ['FL', 'FR', 'RL', 'RR']
SX = dict(FL=1, FR=1, RL=-1, RR=-1); SY = dict(FL=1, FR=-1, RL=1, RR=-1)

def Rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); M = np.eye(4); M[0, 0] = c; M[0, 1] = -s; M[1, 0] = s; M[1, 1] = c; return M
def Rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); M = np.eye(4); M[1, 1] = c; M[1, 2] = -s; M[2, 1] = s; M[2, 2] = c; return M
def Tr(x, y, z):
    M = np.eye(4); M[:3, 3] = (x, y, z); return M

def j1_pos(c, dz=None):
    return (SX[c]*P['j1_x'], SY[c]*P['j1_y'], P['j1_z'] + (dz or {}).get(c, 0.0))

def phi_of(c, cfg):
    base = cfg['phi_F'] if c in ('FL', 'FR') else cfg['phi_R']
    return base if SY[c] > 0 else -base

def side_sign(c, phi):
    """local-y sign that points outboard for corner c at arm yaw phi"""
    cp = math.cos(math.radians(phi))
    if abs(cp) < 1e-9: return 1.0
    return (1.0 if cp > 0 else -1.0) * (1.0 if SY[c] > 0 else -1.0)

def arm_T(c, phi, dz=None):
    return Tr(*j1_pos(c, dz)) @ Rz(phi)

def pod_T(c, phi, rho, dz=None):
    """rho >= 0 : ring displaced OUTBOARD of the arm axis by rho degrees of roll; rho < 0 : inboard"""
    s = side_sign(c, phi)
    return arm_T(c, phi, dz) @ Tr(P['arm_L'], 0, 0) @ Rx(-s*rho) @ Tr(0, 0, -D['pod_A_z'])

def corner_state(c, cfg, dz=None):
    ph = phi_of(c, cfg); rho = cfg['rho_F'] if c in ('FL', 'FR') else cfg['rho_R']
    return ph, rho, arm_T(c, ph, dz), pod_T(c, ph, rho, dz)

# ------------------------------------------------------------------ meshes + sample groups
def _mesh(shape, tol=0.3):
    v, f = shape.tessellate(tol, 0.25)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=False)

class Grp:
    def __init__(self, pts):
        self.pts = np.asarray(pts, float); self.tree = cKDTree(self.pts)
        self.c = self.pts.mean(0); self.r = np.linalg.norm(self.pts - self.c, axis=1).max()

def _sample(mesh, spacing):
    n = max(int(mesh.area/(spacing**2*0.8)), 50)
    p, _ = trimesh.sample.sample_surface_even(mesh, n)
    return np.vstack([p, mesh.vertices[::max(1, len(mesh.vertices)//2000)]])

@functools.lru_cache(maxsize=4)
def groups(spacing=2.5):
    L = library.lib(); G = {}
    import cadquery as cq, parts_body as pb
    # fuselage outer skin (static)
    G['FUS'] = Grp(_sample(_mesh(pb.fuselage_outer(), 0.4), spacing*1.4))
    up, lo = L['shoulder_plate_upper']['shape'], L['shoulder_plate_lower']['shape']
    # four plate groups (mirror for corners)
    for c in CORNERS:
        pts = []
        for s in (up, lo):
            sh = s
            if SY[c] < 0: sh = sh.mirror('XZ')
            if SX[c] < 0: sh = sh.mirror('YZ')
            pts.append(_sample(_mesh(sh, 0.4), spacing))
        G['PLATE_' + c] = Grp(np.vstack(pts))
    # arm (knuckle removed -> it is pocketed by design)
    arm = L['arm_fairing']['shape']
    cut = cq.Workplane("XY").workplane(offset=-30).circle(P['knuckle_r'] + 0.3).extrude(60).val()
    body = arm.cut(cut)
    G['ARM'] = Grp(_sample(_mesh(body, 0.3), spacing))
    ringlike = ['rolling_rim', 'tyre', 'stator_hub_spokes', 'support_roller_1', 'support_roller_2', 'support_roller_3', 'drive_pinion',
                'wheel_gearmotor_placeholder', 'rotor_motor_placeholder', 'rotor_prop_placeholder']
    G['POD'] = Grp(np.vstack([_sample(_mesh(L[n]['shape'], 0.3), spacing) for n in ringlike]))
    G['CONN'] = Grp(_sample(_mesh(L['pylon_wrist_bridge']['shape'], 0.3), spacing))
    # individual pod pieces used for ground / envelope metrics
    G['TYRE'] = Grp(_sample(_mesh(L['tyre']['shape'], 0.3), spacing))
    return G

def _dist(A, TA, B, TB):
    """min surface-sample distance between group A (world transform TA) and B (TB)"""
    cA = TA[:3, :3] @ A.c + TA[:3, 3]; cB = TB[:3, :3] @ B.c + TB[:3, 3]
    gap = np.linalg.norm(cA - cB) - A.r - B.r
    if gap > 40: return gap
    M = np.linalg.inv(TB) @ TA
    pa = A.pts @ M[:3, :3].T + M[:3, 3]
    d1 = B.tree.query(pa, k=1)[0].min()
    M2 = np.linalg.inv(TA) @ TB
    pb_ = B.pts @ M2[:3, :3].T + M2[:3, 3]
    d2 = A.tree.query(pb_, k=1)[0].min()
    return min(d1, d2)

I4 = np.eye(4)
def mirrorT(c):
    return I4

def config_clearances(cfg, G=None, dz=None, active=None):
    """return dict of named min distances (mm) for one full configuration (all 4 corners)"""
    G = G or groups()
    st = {c: corner_state(c, cfg, dz) for c in CORNERS}
    out = {}
    act = list(active or CORNERS)
    for c in act:
        ph, rho, TA, TP = st[c]
        out['ARM_%s|FUS' % c] = _dist(G['ARM'], TA, G['FUS'], I4)
        out['POD_%s|FUS' % c] = _dist(G['POD'], TP, G['FUS'], I4)
        out['CONN_%s|FUS' % c] = _dist(G['CONN'], TP, G['FUS'], I4)
        for k in CORNERS:
            out['ARM_%s|PLATE_%s' % (c, k)] = _dist(G['ARM'], TA, G['PLATE_' + k], I4)
            out['POD_%s|PLATE_%s' % (c, k)] = _dist(G['POD'], TP, G['PLATE_' + k], I4)
        out['POD_%s|ARM_%s' % (c, c)] = _dist(G['POD'], TP, G['ARM'], TA)
        for k in act:
            if k == c: continue
            TAk, TPk = st[k][2], st[k][3]
            if c < k:
                out['POD_%s|POD_%s' % (c, k)] = _dist(G['POD'], TP, G['POD'], TPk)
                out['ARM_%s|ARM_%s' % (c, k)] = _dist(G['ARM'], TA, G['ARM'], TAk)
            out['POD_%s|ARM_%s' % (c, k)] = _dist(G['POD'], TP, G['ARM'], TAk)
            out['CONN_%s|POD_%s' % (c, k)] = _dist(G['CONN'], TP, G['POD'], TPk)
    return out

def worst(cl):
    k = min(cl, key=cl.get); return k, cl[k]

THR = dict(POD_POD=5.0, POD_FUS=5.0, POD_PLATE=4.0, POD_ARM=4.0, CONN_ANY=3.0, ARM_ARM=3.0, ARM_FUS=3.0, ARM_PLATE_OWN=2.0, ARM_PLATE=3.0)
def thr_of(key):
    a, b = key.split('|'); ta, tb = a.split('_')[0], b.split('_')[0]
    if ta == 'CONN' or tb == 'CONN': return THR['CONN_ANY']
    if ta == 'POD' and tb == 'POD': return THR['POD_POD']
    if ta == 'POD' and tb == 'FUS': return THR['POD_FUS']
    if ta == 'POD' and tb == 'PLATE': return THR['POD_PLATE']
    if ta == 'POD' and tb == 'ARM': return THR['POD_ARM']
    if ta == 'ARM' and tb == 'ARM': return THR['ARM_ARM']
    if ta == 'ARM' and tb == 'FUS': return THR['ARM_FUS']
    if ta == 'ARM' and tb == 'PLATE': return THR['ARM_PLATE_OWN'] if a.split('_')[1] == b.split('_')[1] else THR['ARM_PLATE']
    return 3.0
def margin(cl):
    """worst (distance - required clearance) and the offending pair"""
    k = min(cl, key=lambda q: cl[q] - thr_of(q)); return k, cl[k] - thr_of(k)

def cross_clearances(cfg, G, dz=None):
    """front<->rear pair distances only (front/rear states are already individually feasible)"""
    st = {c: corner_state(c, cfg, dz) for c in CORNERS}; out = {}
    for c in ('FL', 'FR'):
        for k in ('RL', 'RR'):
            TAc, TPc = st[c][2], st[c][3]; TAk, TPk = st[k][2], st[k][3]
            out['POD_%s|POD_%s' % (c, k)] = _dist(G['POD'], TPc, G['POD'], TPk)
            out['ARM_%s|ARM_%s' % (c, k)] = _dist(G['ARM'], TAc, G['ARM'], TAk)
            out['POD_%s|ARM_%s' % (c, k)] = _dist(G['POD'], TPc, G['ARM'], TAk)
            out['POD_%s|ARM_%s' % (k, c)] = _dist(G['POD'], TPk, G['ARM'], TAc)
            out['CONN_%s|POD_%s' % (c, k)] = _dist(G['CONN'], TPc, G['POD'], TPk)
            out['CONN_%s|POD_%s' % (k, c)] = _dist(G['CONN'], TPk, G['POD'], TPc)
    return out

def bbox_of(cfg, G, dz=None):
    """axis-aligned bounding box of the whole vehicle in a configuration (surface samples)"""
    lo = G['FUS'].pts.min(0).copy(); hi = G['FUS'].pts.max(0).copy()
    for c in CORNERS:
        ph, rho, TA, TP = corner_state(c, cfg, dz)
        for g, T in (('POD', TP), ('CONN', TP), ('ARM', TA), ('PLATE_' + c, I4)):
            p = G[g].pts @ T[:3, :3].T + T[:3, 3]; lo = np.minimum(lo, p.min(0)); hi = np.maximum(hi, p.max(0))
    return lo, hi

def cross_ok(cfg, G, slack=0.0, dz=None):
    """early-exit cross check; returns (ok, worst_pair, worst_margin_seen)"""
    st = {c: corner_state(c, cfg, dz) for c in CORNERS}
    order = [('FL', 'RL'), ('FR', 'RR'), ('FL', 'RR'), ('FR', 'RL')]
    for (c, k) in order:
        TAc, TPc = st[c][2], st[c][3]; TAk, TPk = st[k][2], st[k][3]
        for (ga, Ta, gb, Tb, key) in ((G['POD'], TPc, G['POD'], TPk, 'POD_%s|POD_%s' % (c, k)),
                                      (G['POD'], TPc, G['ARM'], TAk, 'POD_%s|ARM_%s' % (c, k)),
                                      (G['POD'], TPk, G['ARM'], TAc, 'POD_%s|ARM_%s' % (k, c)),
                                      (G['ARM'], TAc, G['ARM'], TAk, 'ARM_%s|ARM_%s' % (c, k)),
                                      (G['CONN'], TPc, G['POD'], TPk, 'CONN_%s|POD_%s' % (c, k)),
                                      (G['CONN'], TPk, G['POD'], TPc, 'CONN_%s|POD_%s' % (k, c))):
            d = _dist(ga, Ta, gb, Tb); m = d - thr_of(key)
            if m < -slack: return False, key, m
    return True, None, 0.0


def side_ok(cfg, G, act, slack=0.0, dz=None):
    """early-exit feasibility of one side (pair of corners): fuselage, all plates, own arm, partner pod/arm"""
    st = {c: corner_state(c, cfg, dz) for c in act}
    chk = []
    for c in act:
        ph, rho, TA, TP = st[c]
        chk += [(G['POD'], TP, G['FUS'], I4, 'POD_%s|FUS' % c), (G['ARM'], TA, G['FUS'], I4, 'ARM_%s|FUS' % c), (G['CONN'], TP, G['FUS'], I4, 'CONN_%s|FUS' % c)]
        for kk in CORNERS:
            chk += [(G['POD'], TP, G['PLATE_' + kk], I4, 'POD_%s|PLATE_%s' % (c, kk)), (G['ARM'], TA, G['PLATE_' + kk], I4, 'ARM_%s|PLATE_%s' % (c, kk))]
        chk += [(G['POD'], TP, G['ARM'], TA, 'POD_%s|ARM_%s' % (c, c))]
    a, b = act
    chk += [(G['POD'], st[a][3], G['POD'], st[b][3], 'POD_%s|POD_%s' % (a, b)), (G['ARM'], st[a][2], G['ARM'], st[b][2], 'ARM_%s|ARM_%s' % (a, b)),
            (G['POD'], st[a][3], G['ARM'], st[b][2], 'POD_%s|ARM_%s' % (a, b)), (G['POD'], st[b][3], G['ARM'], st[a][2], 'POD_%s|ARM_%s' % (b, a)),
            (G['CONN'], st[a][3], G['POD'], st[b][3], 'CONN_%s|POD_%s' % (a, b)), (G['CONN'], st[b][3], G['POD'], st[a][3], 'CONN_%s|POD_%s' % (b, a))]
    for (ga, Ta, gb, Tb, key) in chk:
        m = _dist(ga, Ta, gb, Tb) - thr_of(key)
        if m < -slack: return False, key, m
    return True, None, 0.0

# ======================= generalised (per-corner roll / per-corner shoulder height) interface =======================
def corner_vals(c, cfg):
    ph = cfg.get('phi_' + c, None)
    if ph is None: ph = phi_of(c, cfg)
    rho = cfg.get('rho_' + c, None)
    if rho is None: rho = cfg['rho_F'] if c in ('FL', 'FR') else cfg['rho_R']
    return ph, rho

def corner_state2(c, cfg, dz=None):
    ph, rho = corner_vals(c, cfg)
    return ph, rho, arm_T(c, ph, dz), pod_T(c, ph, rho, dz)

def pair_list(cfg, G, dz=None):
    """all non-adjacent pair checks for the whole vehicle as (groupA, TA, groupB, TB, key), most-likely-to-fail first"""
    dz = dz or {}
    st = {c: corner_state2(c, cfg, dz) for c in CORNERS}
    PT = {k: Tr(0, 0, dz.get(k, 0.0)) for k in CORNERS}
    L = []
    for a, b in itertools.combinations(CORNERS, 2):
        L += [(G['POD'], st[a][3], G['POD'], st[b][3], 'POD_%s|POD_%s' % (a, b)), (G['ARM'], st[a][2], G['ARM'], st[b][2], 'ARM_%s|ARM_%s' % (a, b)),
              (G['POD'], st[a][3], G['ARM'], st[b][2], 'POD_%s|ARM_%s' % (a, b)), (G['POD'], st[b][3], G['ARM'], st[a][2], 'POD_%s|ARM_%s' % (b, a)),
              (G['CONN'], st[a][3], G['POD'], st[b][3], 'CONN_%s|POD_%s' % (a, b)), (G['CONN'], st[b][3], G['POD'], st[a][3], 'CONN_%s|POD_%s' % (b, a))]
    for c in CORNERS:
        ph, rho, TA, TP = st[c]
        L += [(G['POD'], TP, G['FUS'], I4, 'POD_%s|FUS' % c), (G['ARM'], TA, G['FUS'], I4, 'ARM_%s|FUS' % c), (G['CONN'], TP, G['FUS'], I4, 'CONN_%s|FUS' % c)]
        L += [(G['POD'], TP, G['ARM'], TA, 'POD_%s|ARM_%s' % (c, c))]
        for k in CORNERS:
            L += [(G['POD'], TP, G['PLATE_' + k], PT[k], 'POD_%s|PLATE_%s' % (c, k)), (G['ARM'], TA, G['PLATE_' + k], PT[k], 'ARM_%s|PLATE_%s' % (c, k))]
    return L

def full_ok(cfg, G, dz=None, slack=0.0):
    for (ga, Ta, gb, Tb, key) in pair_list(cfg, G, dz):
        m = _dist(ga, Ta, gb, Tb) - thr_of(key)
        if m < -slack: return False, key, m
    return True, None, 0.0

def full_clear(cfg, G, dz=None):
    return {key: _dist(ga, Ta, gb, Tb) for (ga, Ta, gb, Tb, key) in pair_list(cfg, G, dz)}

def bbox2(cfg, G, dz=None):
    dz = dz or {}
    lo = G['FUS'].pts.min(0).copy(); hi = G['FUS'].pts.max(0).copy()
    for c in CORNERS:
        ph, rho, TA, TP = corner_state2(c, cfg, dz); PT = Tr(0, 0, dz.get(c, 0.0))
        for g, T in (('POD', TP), ('CONN', TP), ('ARM', TA), ('PLATE_' + c, PT)):
            p = G[g].pts @ T[:3, :3].T + T[:3, 3]; lo = np.minimum(lo, p.min(0)); hi = np.maximum(hi, p.max(0))
    return lo, hi
