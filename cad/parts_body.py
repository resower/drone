"""CF-2 fuselage, shoulder fairings, arm.  Fuselage frame: x fwd, y left, z up, origin at mid-body.
Arm-local frame (left-hand arm): origin on the J1 axis at arm mid-height, +x toward the pod."""
import math, numpy as np, cadquery as cq
from cadquery import Vector as V
from params import P, D

# ---------------- fuselage section schedule: (x, half-width, half-height top, half-height bottom, z-centre, superellipse exponent)
K = P['f_len'] / 300.0
SECT = [(150, 7, 9, 9, -6.0, 2.0), (138, 13, 15, 14, -5.0, 2.1), (112, 22, 23, 21, -3.0, 2.3), (72, 30, 27, 23, -1.0, 2.5),
        (22, 33, 29, 25, 0.0, 2.6), (-38, 32, 28.5, 24.5, 0.0, 2.6), (-92, 26, 24, 20, 1.0, 2.4), (-128, 18, 18, 15, 2.0, 2.2), (-150, 12, 12, 10, 3.0, 2.0)]
SECT = [(x*K,) + s[1:] for s in SECT for x in [s[0]]]

def _interp(x):
    xs = [s[0] for s in SECT][::-1]
    return [float(np.interp(x, xs, [s[i] for s in SECT][::-1])) for i in range(1, 6)]

def _section_wire(x, w, ht, hb, zc, n, inset=0.0, N=28):
    pts = []
    w = max(w - inset, 1.5); ht = max(ht - inset, 1.5); hb = max(hb - inset, 1.5)
    for i in range(N):
        t = 2*math.pi*i/N; c = math.cos(t); s = math.sin(t)
        y = w*math.copysign(abs(c)**(2.0/n), c); z = zc + (ht if s >= 0 else hb)*math.copysign(abs(s)**(2.0/n), s)
        pts.append(V(x, y, z))
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(pts, periodic=True)])

def _loft(inset):
    return cq.Solid.makeLoft([_section_wire(x, w, ht, hb, zc, n, inset) for (x, w, ht, hb, zc, n) in SECT], False)

def fuselage_outer():
    return _loft(0.0)

def fuselage_shell():
    return cq.Workplane(obj=_loft(0.0)).cut(cq.Workplane(obj=_loft(P['wall']))).val()

def sec_dims(x):
    w, ht, hb, zc, n = _interp(x); return w, 0.5*(ht + hb), zc

def skin_z(x, y, top=True):
    w, ht, hb, zc, n = _interp(x)
    t = max(0.0, 1 - (abs(y)/w)**n)**(1.0/n)
    return zc + (ht*t if top else -hb*t)

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1)/2, (y0 + y1)/2, (z0 + z1)/2))

# panel windows (x0,x1,y0,y1,z0,z1) in the fuselage frame
PANELS = {
    'nose_cone':    (110*K, 170*K, -60, 60, -60, 60),
    'dorsal_hatch': (-62*K, 70*K, -20, 20, 7, 60),
    'belly_hatch':  (-40*K, 56*K, -21, 21, -60, -12),
    'service_L':    (-92*K, -10*K, 20, 60, -14, 12),
    'service_R':    (-92*K, -10*K, -60, -20, -14, 12),
    'tail_cap':     (-170*K, -128*K, -60, 60, -60, 60),
}
GAP = 0.35

def fuselage_split():
    """dict name -> solid: main shell and each removable panel (seam gap GAP); service panels get cooling slots"""
    shell = cq.Workplane(obj=fuselage_shell()); out = {}; main = shell
    for name, (x0, x1, y0, y1, z0, z1) in PANELS.items():
        pan = shell.intersect(box(x0, x1, y0, y1, z0, z1))
        if name.startswith('service'):
            for i in range(5):
                xs = (-80 + 11*i)*K
                pan = pan.cut(box(xs - 1.2, xs + 1.2, -60, 60, -9, 5))
        out[name] = pan.val()
        main = main.cut(box(x0 - GAP, x1 + GAP, y0 - GAP, y1 + GAP, z0 - GAP, z1 + GAP))
    out['fuselage_main'] = main.val()
    return out

def fasteners():
    pts = []
    for xs in (-52, -26, 0, 26, 56): pts += [(xs*K, 17.0, True), (xs*K, -17.0, True)]
    for xs in (-30, -4, 22, 48): pts += [(xs*K, 18.0, False), (xs*K, -18.0, False)]
    sol = None
    for (x, y, top) in pts:
        z = skin_z(x, y, top)
        c = cq.Workplane("XY").workplane(offset=z - (0.5 if top else 0.8)).center(x, y).circle(1.9).extrude(1.3)
        sol = c if sol is None else sol.union(c)
    for xs in (-86, -60, -34, -14):
        for sgn in (1, -1):
            x = xs*K; w = _interp(x)[0]; y = sgn*w*0.99
            c = cq.Workplane("XZ").workplane(offset=-y).center(x, 6.0).circle(1.9).extrude(1.3 if sgn > 0 else -1.3)
            sol = sol.union(c)
    return sol.val()

def antenna_fin():
    x0 = -125*K; pts = [(x0, skin_z(x0, 0) - 2), (x0 + 36, skin_z(x0 + 36, 0) - 2), (x0 + 30, skin_z(x0 + 30, 0) + 14), (x0 + 10, skin_z(x0 + 10, 0) + 15)]
    return cq.Workplane("XZ").polyline(pts).close().extrude(1.0, both=True).edges("|Y").fillet(1.5).val()

def nose_dome():
    """sensor dome (placeholder glazing) at the nose"""
    x = 128*K
    return cq.Workplane("YZ").workplane(offset=x).center(0, -4.0).circle(8.5).extrude(18*K).faces(">X").edges().fillet(4.0).val()

# ---------------- internals (placeholders packaged to check fit)
def internals():
    c = {}
    c['battery_placeholder'] = box(-34*K, 46*K, -19, 19, -22, 17).val()
    c['fc_stack_placeholder'] = box(-88*K, -52*K, -17, 17, -14, 10).val()
    c['companion_computer_placeholder'] = box(64*K, 104*K, -17, 17, -12, 4).val()
    c['camera_module_placeholder'] = box(110*K, 130*K, -9, 9, -14, 4).val()
    c['gps_puck_placeholder'] = cq.Workplane("XY").workplane(offset=26.0).center(-30*K, 0).circle(14).extrude(7).val()
    return c

# ---------------- shoulder fairing (fixed to fuselage; upper/lower plates sandwich the arm root)
def _tangent_pt(P_, C, R, side):
    """tangent point on circle (C,R) from external point P_; side=+1/-1 picks the outboard one"""
    px, py = P_[0] - C[0], P_[1] - C[1]; d = math.hypot(px, py); a = math.atan2(py, px); b = math.acos(R/d)
    t = a + side*b
    return (C[0] + R*math.cos(t), C[1] + R*math.sin(t))

def _plate(z0, t, x0, y0, R, yb, wb):
    P1 = (x0 - wb, yb); P2 = (x0 + wb, yb)
    T1 = _tangent_pt(P1, (x0, y0), R, -1); T2 = _tangent_pt(P2, (x0, y0), R, +1)
    wp = (cq.Workplane("XY").workplane(offset=z0).moveTo(*P1).lineTo(*T1).threePointArc((x0, y0 + R), T2).lineTo(*P2).close().extrude(t))
    try: wp = wp.faces(">Z or <Z").edges().fillet(1.3)
    except Exception: pass
    return wp

def shoulder_plates():
    """left-front plate pair in the fuselage frame (J1 at (+j1_x, +j1_y)); other corners are mirrored copies"""
    x0, y0 = P['j1_x'], P['j1_y']; R = 21.0
    up = _plate(12.5, 4.0, x0, y0, R, 14.0, 30.0); lo = _plate(-16.5, 4.0, x0, y0, R, 14.0, 30.0)
    pin = cq.Workplane("XY").workplane(offset=-16.5).center(x0, y0).circle(2.0).extrude(33.0)
    return up.val(), lo.val(), pin.val()

# ---------------- arm (variant 'A': J1 high -> wrist is lower than the knuckle by `stagger`; 'B': mirror in z)
def _ramp(x, xa, xb):
    t = min(max((x - xa)/(xb - xa), 0.0), 1.0); return 0.5 - 0.5*math.cos(math.pi*t)

def arm(variant='A'):
    L = P['arm_L']; xe = L - P['arm_end_gap']; sg = -1.0 if variant == 'A' else 1.0; dzw = sg*P['stagger']
    kr, kh = P['knuckle_r'], P['knuckle_h']
    knuckle = cq.Workplane("XY").workplane(offset=-kh/2).circle(kr).extrude(kh).edges().fillet(2.0)
    w0, h0, w1, h1 = P['arm_w0'], P['arm_h0'], P['arm_w1'], P['arm_h1']
    xs = [kr - 4, 30.0, 42.0, 54.0, xe - 18.0, xe - 8.0, xe - 0.5]
    wires = []
    for x in xs:
        t = min(max((x - (kr - 4))/((xe - 8) - (kr - 4)), 0.0), 1.0)
        w = w0 + (w1 - w0)*t; h = h0 + (h1 - h0)*t
        if x > xe - 8.5: w -= 1.0; h -= 1.0
        zc = dzw*_ramp(x, 22.0, xe - 18.0)
        wires.append(cq.Wire.makeEllipse(w/2, h/2, V(x, 0, zc), V(1, 0, 0), V(0, 1, 0)))
    body = cq.Workplane(obj=cq.Solid.makeLoft(wires, False))
    wrist = cq.Workplane("YZ").workplane(offset=xe - 12).center(0, dzw).circle(13.5).extrude(12.0).faces(">X").edges().fillet(1.5)
    arm_fair = cq.Workplane(obj=knuckle.val()).union(body).union(wrist)
    # straight CFRP spar from the knuckle to the start of the horizontal wrist section (tilted)
    p0 = V(kr - 2, 0, 0); p1 = V(xe - 18, 0, dzw); d = p1 - p0
    tube = cq.Solid.makeCylinder(5.0, d.Length, p0, d).cut(cq.Solid.makeCylinder(4.0, d.Length, p0, d))
    j1_servo = cq.Workplane("XY").box(23, 12, 22)
    j2_servo = cq.Workplane("XY").box(20, 11, 20).translate((xe - 16, 0, dzw))
    stops = cq.Workplane("XY").box(6, 4, 3.0).translate((kr + 3.0, 0, -13.5))
    return dict(arm_fairing=arm_fair.val(), cfrp_tube=tube, j1_servo_placeholder=j1_servo.val(), j2_servo_placeholder=j2_servo.val(), stop_lug=stops.val())
