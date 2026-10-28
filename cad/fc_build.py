"""Build the native FreeCAD document CF2_Chameleon-Ring.FCStd from out/manifest.json + out/step_parts/*.step.
Run with:  freecadcmd fc_build.py   (paths are read from environment CF2_OUT, default ../build)

Document structure
  Params (Spreadsheet)            : parameter table, config selector `cfg` (1 flight, 2 ground, 3 compact), joint angles per corner (aliases phi_FL, rho_FL, ...)
  CF2_Assembly (App::Part)
     Fuselage / Internals_placeholders / Shoulder_<corner> (fixed)
     Arm_<corner>   (App::Part, Placement = J1 position * Rz(phi))          <- J1 yaw joint, expression-driven
        RotorWheelPod_<corner> (App::Part, Placement = Tr(L,0,0) * Rx(-s*rho) * Tr(0,0,-A_z))   <- J2 roll joint, expression-driven
Change Params.cfg (or the individual joint cells) and recompute: the whole assembly moves.
Every part carries CF2_* properties (material, role, mass estimate, PLACEHOLDER flag)."""
import os, json, math
import FreeCAD as App, Part

OUT = os.environ.get('CF2_OUT', '../build')
man = json.load(open(OUT + '/manifest.json'))
P = man['params']; D = man['derived']; files = man['files']; cfgs = man['configs']; rows = man['mass']
doc = App.newDocument('CF2_Chameleon_Ring')

# ------------------------------------------------------------------------------------------ parameter spreadsheet
ss = doc.addObject('Spreadsheet::Sheet', 'Params')
r = 1
def put(label, value, alias=None, note=''):
    global r
    ss.set('A%d' % r, label); ss.set('B%d' % r, str(value))
    if alias: ss.setAlias('B%d' % r, alias)
    if note: ss.set('C%d' % r, note)
    r += 1
put('CF-2 Chameleon-Ring -- parameter + configuration sheet', '', note='CONCEPT model, geometry only. Nothing here is a verified performance or flight-worthiness value.')
put('Active configuration (1 flight, 2 ground, 3 compact, 4 sequence/manual)', 1, 'cfg', 'change this cell, then Recompute (Ctrl+R)')
put('Sequence/manual: front J1 yaw (deg), used when cfg = 4; rear mirrors (180 - this)', 50, 'seqPhiF', 'checked range 0..170 (front) -- see joint_range_map.png')
put('Sequence/manual: J2 roll (deg), all four pods, used when cfg = 4', 0, 'seqRho', 'only combinations inside the green region of joint_range_map.png are collision-free')
r += 1
put('CONFIGURATION TABLE (deg)', '', note='columns: B flight  C ground  D compact(placeholder)  -- see CF2_report for the status of each')
hdr = r; ss.set('B%d' % hdr, 'flight'); ss.set('C%d' % hdr, 'ground'); ss.set('D%d' % hdr, 'compact'); r += 1
cf = [cfgs['cfg_flight'], cfgs['cfg_ground'], cfgs['cfg_compact']]
def cfg_val(k, c):
    # per-corner override first, then F/R group
    ov = c.get(k)
    return ov
rowof = {}
for c in ('FL', 'FR', 'RL', 'RR'):
    front = c in ('FL', 'FR'); left = c in ('FL', 'RL')
    # yaw phi of arm (right side mirrored), roll rho
    vals_phi = []; vals_rho = []
    for q in cf:
        base = q['phi_F'] if front else q['phi_R']; vals_phi.append(base if left else -base)
        vals_rho.append(q['rho_F'] if front else q['rho_R'])
    ss.set('A%d' % r, 'phi_%s  (J1 arm yaw)' % c)
    for j, v in enumerate(vals_phi): ss.set('%s%d' % ('BCD'[j], r), str(v))
    seqphi = {'FL': 'seqPhiF', 'FR': '-seqPhiF', 'RL': '(180 - seqPhiF)', 'RR': '-(180 - seqPhiF)'}[c]
    ss.set('F%d' % r, '=' + seqphi)
    ss.set('E%d' % r, '=cfg == 1 ? B%d : (cfg == 2 ? C%d : (cfg == 3 ? D%d : F%d))' % (r, r, r, r)); ss.setAlias('E%d' % r, 'phi_%s' % c); r += 1
    ss.set('A%d' % r, 'rho_%s  (J2 pod roll, + = ring outboard)' % c)
    for j, v in enumerate(vals_rho): ss.set('%s%d' % ('BCD'[j], r), str(v))
    ss.set('F%d' % r, '=seqRho')
    ss.set('E%d' % r, '=cfg == 1 ? B%d : (cfg == 2 ? C%d : (cfg == 3 ? D%d : F%d))' % (r, r, r, r)); ss.setAlias('E%d' % r, 'rho_%s' % c); r += 1
ss.set('E%d' % hdr, 'ACTIVE'); ss.set('F%d' % hdr, 'sequence'); r += 1
put('GEOMETRY (mm)', '', note='informational; the part solids are imported (rebuild them with cad/build.py after changing cad/params.py)')
for k in ('prop_d', 'tip_gap', 'arm_L', 'j1_x', 'j1_y', 'j1_z', 'f_len', 'f_w', 'f_h', 'wall', 'tire_r_out'):
    put(k, P[k], k)
put('e_lat (arm axis -> ring mid-plane)', round(D['e_check'], 2), 'e_lat')
put('pod_A_z (arm axis in pod frame)', D['pod_A_z'], 'pod_A_z')
doc.recompute()

# ------------------------------------------------------------------------------------------ helpers
def load(name):
    s = Part.read(OUT + '/step_parts/' + files[name]); return s

def add_part(container, name, partname, label=None):
    shape = load(partname); o = doc.addObject('Part::Feature', name); o.Shape = shape
    row = rows.get(partname.split('_FL')[0].split('_FR')[0].split('_RL')[0].split('_RR')[0], rows.get(partname))
    if row is None and partname[-3:-2] == '_' : row = rows.get(partname[:-3])
    o.Label = label or name
    props = dict(CF2_Material=row['material'] if row else '', CF2_Group=row['group'] if row else '', CF2_MassEstimate_g=('%.1f' % row['mass_g']) if row else '',
                 CF2_MassBasis=row['basis'] if row else '')
    for k, v in props.items():
        o.addProperty('App::PropertyString', k, 'CF2'); setattr(o, k, v)
    o.addProperty('App::PropertyBool', 'CF2_Placeholder', 'CF2'); o.CF2_Placeholder = bool(row['placeholder']) if row else False
    o.Label2 = 'PLACEHOLDER - size/position only, not a flight-worthy part' if (row and row['placeholder']) else 'concept geometry - untested, not flight-worthy'
    # appearance (best effort)
    try:
        import json as _j
        m = App.Material(); col = COL.get(partname.split('_FL')[0].split('_FR')[0].split('_RL')[0].split('_RR')[0])
        if col: m.DiffuseColor = col; o.ShapeMaterial = m
    except Exception:
        pass
    container.addObject(o); return o

COL = {}
try:
    for n, rgb in json.load(open(OUT + '/colors.json')).items(): COL[n] = tuple(rgb)
except Exception:
    pass

root = doc.addObject('App::Part', 'CF2_Assembly'); root.Label = 'CF2_Assembly'
fus = doc.addObject('App::Part', 'Fuselage'); root.addObject(fus)
for n in man['hierarchy']['00_CF2_Chameleon-Ring_concept']['10_Fuselage']: add_part(fus, n, n)
intn = doc.addObject('App::Part', 'Internals_placeholders'); root.addObject(intn)
for n in man['hierarchy']['00_CF2_Chameleon-Ring_concept']['11_Internals_placeholders']: add_part(intn, n, n)

pod_groups = man['hierarchy']['00_CF2_Chameleon-Ring_concept']['40_RotorWheelPod']
side_sign = lambda c: None
for c in ('FL', 'FR', 'RL', 'RR'):
    sh = doc.addObject('App::Part', 'Shoulder_' + c); root.addObject(sh)
    for n in ('shoulder_plate_upper', 'shoulder_plate_lower', 'j1_hinge_pin'): add_part(sh, '%s_%s' % (n, c), '%s_%s' % (n, c))
    j1 = man['corners'][c]['j1']
    arm = doc.addObject('App::Part', 'Arm_' + c); root.addObject(arm)
    arm.setExpression('Placement', 'create(<<placement>>; create(<<vector>>; %.6f mm; %.6f mm; %.6f mm); create(<<rotation>>; create(<<vector>>; 0; 0; 1); Params.phi_%s * 1 deg / 1 deg))' % (j1[0], j1[1], j1[2], c))
    for n in man['hierarchy']['00_CF2_Chameleon-Ring_concept']['30_Arm']: add_part(arm, '%s_%s' % (n, c), n)
    pod = doc.addObject('App::Part', 'RotorWheelPod_' + c); arm.addObject(pod)
    # side sign of local-y pointing outboard depends on the current yaw: s = sign(cos(phi)) * (+1 left / -1 right)
    left = 1 if c in ('FL', 'RL') else -1
    sexpr = '(cos(Params.phi_%s * 1 deg) >= 0 ? %d : %d)' % (c, left, -left) if False else '((cos(Params.phi_%s * 1 deg / 1 deg) >= 0 ? 1 : -1) * %d)' % (c, left)
    L_arm = P['arm_L']; Az = D['pod_A_z']
    pod.setExpression('Placement', 'create(<<placement>>; create(<<vector>>; %.6f mm; 0 mm; 0 mm); create(<<rotation>>; create(<<vector>>; 1; 0; 0); -%s * Params.rho_%s * 1 deg / 1 deg)) * create(<<placement>>; create(<<vector>>; 0 mm; 0 mm; %.6f mm); create(<<rotation>>; create(<<vector>>; 0; 0; 1); 0))' % (L_arm, sexpr, c, -Az))
    for grp, names in pod_groups.items():
        g = doc.addObject('App::Part', '%s_%s' % (grp, c)); pod.addObject(g)
        for n in names: add_part(g, '%s_%s' % (n, c), n)
doc.recompute()
out = OUT + '/CF2_Chameleon-Ring.FCStd'
doc.saveAs(out); print('saved', out, 'objects', len(doc.Objects))
