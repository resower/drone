"""CF-2 rotor-wheel pod parts (pod frame: z = rotor axis, z=0 = blade plane, origin on ring axis)."""
import math, cadquery as cq
from cadquery import Vector as V
from params import P, D

def revolve_rz(pts):
    """revolve a closed (r,z) polygon about the z axis"""
    return cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()

def arc_pts(cx, cz, r, a0, a1, n=6):
    return [(cx + r*math.cos(math.radians(a0 + (a1 - a0)*i/n)), cz + r*math.sin(math.radians(a0 + (a1 - a0)*i/n))) for i in range(n + 1)]

def gear_poly(m, Z, rp_shift=0.0, internal=False):
    """simple trapezoid-tooth polygon. external: tips outside; internal: tips point inwards"""
    rp = m*Z/2.0; pitch = 2*math.pi/Z
    ra = rp - m if internal else rp + m
    rf = rp + 1.25*m if internal else rp - 1.25*m
    pts = []
    for i in range(Z):
        b = i*pitch
        # tooth centred at b ; gap centred at b+pitch/2
        for (a, r) in [(-.27, rf), (-.17, ra), (.17, ra), (.27, rf)] if internal else [(-.27, rf), (-.15, ra), (.15, ra), (.27, rf)]:
            pts.append(((r)*math.cos(b + a*pitch), (r)*math.sin(b + a*pitch)))
    return pts

def ring_rim():
    """Rolling rim = annular duct wall + roller V-rail + internal ring-gear band. Local frame = pod frame."""
    R = D['R_in']; zt = P['z_top']; zb = P['z_bot']; lr = P['lip_r']; wo = P['wall_out']
    gb = P['gear_band']; rz = P['rail_z']
    Rroot = R + 1.25*P['gear_m'] + 0.0
    # inner side bottom->top, then outer side top->bottom
    inner = [(R + 3.0, zb), (R + 3.0, zb + gb)]          # gear band pocket (inner radius widened; teeth added separately)
    inner += [(R, zb + gb + 1.0), (R, rz - 3), (R - 1.4, rz), (R, rz + 3)]   # V-rail ridge
    inner += [(R, 3.0)] + arc_pts(R + lr, 3.0, lr, 180, 90, 6)[1:]           # throat + bellmouth lip
    outer = [(wo - 1.5, zt), (wo, zt - 1.5), (wo, P['tire_z1'] + 1.0), (wo - 2.0, P['tire_z1'] + 1.0),
             (wo - 2.0, P['tire_z0'] - 1.0), (wo, P['tire_z0'] - 1.0), (wo, zb + 1.5), (wo - 1.5, zb)]
    rim = revolve_rz(inner + outer)
    # internal gear (tips toward axis) in the pocket
    Z = int(round(2*(R + P['gear_m'])/P['gear_m']))       # pitch radius = R + m
    pts = gear_poly(P['gear_m'], Z, internal=True)
    outer_c = cq.Workplane("XY").workplane(offset=zb).circle(R + 3.2).extrude(gb)
    inner_g = cq.Workplane("XY").workplane(offset=zb).polyline(pts).close().extrude(gb)
    gear = outer_c.cut(inner_g).val()
    return rim.fuse(gear).clean(), Z

def tire():
    ri = P['wall_out'] - 2.0; ro = P['tire_r_out']; z0 = P['tire_z0']; z1 = P['tire_z1']
    base = revolve_rz([(ri, z0), (ro - 1.0, z0), (ro, z0 + 1.0), (ro, z1 - 1.0), (ro - 1.0, z1), (ri, z1)])
    # tread blocks (chevron lugs)
    lugs = None
    n = P['n_lugs']
    for i in range(n):
        a = 360.0*i/n
        for side in (-1, 1):
            zc = 0.5*(z0 + z1) + side*5.0
            b = cq.Workplane("XY").box(2.0, 6.5, 3.0).translate((ro, 0, 0))
            b = b.rotate((ro, 0, 0), (ro, 0, 1), -side*25).translate((0, 0, zc)).rotate((0, 0, 0), (0, 0, 1), a)
            lugs = b if lugs is None else lugs.union(b)
    # lugs stick out of the tread cylinder by ~1.5 mm -> this is the ground-contact radius
    return base.fuse(lugs.val()).clean() if False else cq.Workplane(obj=base).union(lugs).val()

def stator():
    """hub plate + 4 spokes + roller axles; returns dict of named solids"""
    R = D['R_in']; sz = P['spoke_z']; t = P['spoke_t']; w = P['spoke_w']; rr = R - P['roller_r']
    hub = cq.Workplane("XY").workplane(offset=sz - t/2).circle(P['hub_r']).extrude(t)
    # motor mounting boss
    spokes = None
    angs = [45, 135, 225, 315]
    for a in angs:
        s = cq.Workplane("XY").box(rr - P['hub_r'] + 6, w, t).translate(((rr + P['hub_r'] - 6)/2 + 0.0, 0, sz)).rotate((0, 0, 0), (0, 0, 1), a)
        spokes = s if spokes is None else spokes.union(s)
    body = hub.union(spokes)
    # axle bosses (roller / pinion axles)
    for a in angs:
        x = rr*math.cos(math.radians(a)); y = rr*math.sin(math.radians(a))
        ax = cq.Workplane("XY").workplane(offset=sz).center(x, y).circle(2.0).extrude(P['z_top'] - sz - 14)   # 3 mm axle up to ~ -4? trimmed below
        body = body.union(cq.Workplane("XY").workplane(offset=sz).center(x, y).circle(3.2).extrude(4.0))
    return body.val()

def rollers():
    """3 flanged V-groove rollers at 135, 225, 315 deg"""
    R = D['R_in']; rr = R - P['roller_r']; zc = P['rail_z']; h = P['roller_h']; r = P['roller_r']
    out = []
    for a in (135, 225, 315):
        x = rr*math.cos(math.radians(a)); y = rr*math.sin(math.radians(a))
        prof = [(0, zc - h/2), (r - 1.0, zc - h/2), (r, zc - h/2 + 1.0), (r - 1.4, zc), (r, zc + h/2 - 1.0), (r - 1.0, zc + h/2), (0, zc + h/2)]
        s = revolve_rz(prof).translate(V(x, y, 0))
        axle = cq.Workplane("XY").workplane(offset=P['spoke_z']).center(x, y).circle(1.5).extrude(zc + h/2 - P['spoke_z'] + 1.0).val()
        out.append(s.fuse(axle).clean())
    return out

def drive_pinion():
    R = D['R_in']; m = P['gear_m']; Zp = P['pinion_Z']; Rp = m*Zp/2
    cd = (R + m) - Rp           # centre distance to ring pitch circle
    a = math.radians(45)
    x, y = cd*math.cos(a), cd*math.sin(a)
    pts = gear_poly(m, Zp, internal=False)
    zb = P['z_bot'] + 1.0
    g = cq.Workplane("XY").workplane(offset=zb).center(x, y).polyline(pts).close().extrude(P['gear_band'] - 1.5).val()
    # gearmotor below spoke plane (N20-class placeholder, dia 12 x 24)
    gm = cq.Workplane("XY").workplane(offset=P['spoke_z'] - P['spoke_t']/2 - 24).center(x, y).circle(6.0).extrude(24).val()
    shaft = cq.Workplane("XY").workplane(offset=P['spoke_z']).center(x, y).circle(1.5).extrude(zb - P['spoke_z']).val()
    return g.fuse(shaft).clean(), gm, (x, y)

def motor():
    d = P['motor_d']; z0 = P['motor_base_z']
    base = cq.Workplane("XY").workplane(offset=z0).circle(10.5).extrude(6.0)
    bell = cq.Workplane("XY").workplane(offset=z0 + 6.0).circle(d/2).extrude(P['motor_h'] - 6.0 - 7.0).faces(">Z").edges().fillet(1.5)
    shaft = cq.Workplane("XY").workplane(offset=z0 + P['motor_h'] - 7.0).circle(2.5).extrude(7.0)
    return base.union(bell).union(shaft).val()

def prop():
    """PLACEHOLDER 3-blade prop (not an aerodynamic design): flat twisted planform, 127 mm."""
    Rt = P['prop_d']/2; zc = P['motor_base_z'] + P['motor_h'] - 3.5    # blade plane ~ z=-3.5.. -> shift so that z=0 is mid chord
    zc = -1.0
    hub = cq.Workplane("XY").workplane(offset=zc - 3.0).circle(8.0).extrude(8.0)
    blades = None
    for i in range(3):
        pts = [(7, -3.0), (22, -6.5), (45, -8.5), (60, -6.0), (Rt - 0.8, -1.8), (Rt - 0.8, 1.8), (58, 5.5), (40, 8.0), (20, 6.0), (7, 3.0)]
        b = cq.Workplane("XY").workplane(offset=zc - 0.9).polyline(pts).close().extrude(1.8).val()
        b = b.rotate(V(0, 0, 0), V(1, 0, 0), 14)
        b = b.rotate(V(0, 0, 0), V(0, 0, 1), 120*i)
        blades = b if blades is None else blades.fuse(b)
    return hub.val().fuse(blades).clean()

def pylon_bridge():
    """pylon (hub -> arm axis) + pod-side wrist flange.  Pod frame; arm axis A is at z = pod_A_z along pod x."""
    Az = D['pod_A_z']; sz = P['spoke_z']
    py = cq.Workplane("XY").workplane(offset=Az).circle(P['pylon_r']).extrude(sz - P['spoke_t']/2 - Az)
    # bridge block from flange (x=-24..-18) to pylon
    bridge = cq.Workplane("XY").box(33.0, 24.0, 22.0).translate((-24 + 33/2.0 - 0.0, 0, Az))
    flange = cq.Workplane("YZ").workplane(offset=-24.0).center(0, Az).circle(15.0).extrude(6.0)
    return py.union(bridge).union(flange).val()
