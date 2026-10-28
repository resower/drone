"""CF-2 Chameleon-Ring: build and pose the concept assembly in Autodesk Fusion.

HOW TO RUN (Fusion desktop app):
  1. Utilities > Add-Ins > Scripts and Add-Ins > "+" next to My Scripts > select the folder CF2_Fusion_Build > Run.
  2. Keep the folder structure: this file and cf2_transforms.json must sit together; step_parts is read from this folder or from ../step_parts.
  3. First run: builds the whole assembly (about 46 STEP imports, give it a few minutes) and puts it in the flight pose.
     Next runs (same document): a prompt asks for a pose. Type 1 flight, 2 ground, 3 compact, 4 animate the transformation,
     or two numbers "J1_front_yaw,J2_roll" in degrees, for example 30,10.

WHAT THIS IS: a pose-driven model. Arms and pods are placed by transforms computed from the checked kinematics
(they match the FreeCAD/numpy transforms in the package). It is NOT a joint-constrained model: Fusion joints with limits
must be added by hand (see README_Fusion.md, which lists each axis and range).
STATUS: written without access to Fusion. The geometry math is tested against the package data with a mock of the Fusion API;
the Fusion API calls themselves have NOT been run in Fusion. Expect to fix small API errors; the error dialog shows the line.
CONCEPT ONLY: placeholders (motors, battery, electronics, propeller) are size stand-ins; nothing here is flight-worthy.
"""
import adsk.core, adsk.fusion, traceback, json, os, math, time

_app = adsk.core.Application.get()
_ui = _app.userInterface
HERE = os.path.dirname(os.path.realpath(__file__))
MM_TO_CM = 0.1                       # Fusion's internal length unit is centimetres
CORNERS = ['FL', 'FR', 'RL', 'RR']
SX = dict(FL=1, FR=1, RL=-1, RR=-1); SY = dict(FL=1, FR=-1, RL=1, RR=-1)

# ----------------------------------------------------------------------------- pure kinematics (same as cad/kin.py)
def _eye():
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]

def mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def Tr(x, y, z):
    M = _eye(); M[0][3], M[1][3], M[2][3] = x, y, z; return M

def Rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); M = _eye(); M[0][0], M[0][1], M[1][0], M[1][1] = c, -s, s, c; return M

def Rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); M = _eye(); M[1][1], M[1][2], M[2][1], M[2][2] = c, -s, s, c; return M

def side_sign(c, phi):
    cp = math.cos(math.radians(phi))
    if abs(cp) < 1e-9: return 1.0
    return (1.0 if cp > 0 else -1.0) * (1.0 if SY[c] > 0 else -1.0)

def corner_transforms(c, phi_front, rho, prm):
    """world transforms (mm) of the arm and pod of corner c for a lock-step pose: front arms at phi_front, rear arms at 180 - phi_front"""
    base = phi_front if c in ('FL', 'FR') else 180.0 - phi_front
    phi = base if SY[c] > 0 else -base
    j1 = (SX[c] * prm['j1_x'], SY[c] * prm['j1_y'], prm['j1_z'])
    arm = mul(Tr(*j1), Rz(phi))
    pod = mul(mul(mul(arm, Tr(prm['arm_L'], 0, 0)), Rx(-side_sign(c, phi) * rho)), Tr(0, 0, -prm['pod_A_z']))
    return arm, pod

# ----------------------------------------------------------------------------- Fusion helpers
def to_m3d(M):
    m = adsk.core.Matrix3D.create()
    for r in range(4):
        for c in range(4):
            v = M[r][c] * (MM_TO_CM if c == 3 and r < 3 else 1.0)
            m.setCell(r, c, v)
    return m

def import_step(target_comp, path):
    im = _app.importManager
    opts = im.createSTEPImportOptions(path)
    im.importToTarget(opts, target_comp)

def add_part(parent_comp, name, step_path):
    occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    import_step(occ.component, step_path)
    return occ

def flat_names(node):
    """list of part names in a hierarchy node (list or nested dict)"""
    if isinstance(node, list): return list(node)
    out = []
    for v in node.values(): out += flat_names(v)
    return out

# ----------------------------------------------------------------------------- build
def count_parts(data):
    h = data['hierarchy']['00_CF2_Chameleon-Ring_concept']
    return len(h['10_Fuselage']) + len(h['11_Internals_placeholders']) + 4 * len(h['20_Shoulders_J1_fixed']) + len(h['30_Arm']) + len(flat_names(h['40_RotorWheelPod']))

def build(design, data, progress):
    root = design.rootComponent; step = os.path.join(HERE, 'step_parts') if os.path.isdir(os.path.join(HERE, 'step_parts')) else os.path.join(HERE, '..', 'step_parts'); files = data['files']
    h = data['hierarchy']['00_CF2_Chameleon-Ring_concept']; I = adsk.core.Matrix3D.create(); n_done = 0
    def tick(msg):
        nonlocal n_done
        n_done += 1; progress.progressValue = n_done; progress.message = msg; adsk.doEvents()
    fus = root.occurrences.addNewComponent(I); fus.component.name = 'CF2_Fuselage'
    for n in h['10_Fuselage'] + h['11_Internals_placeholders']:
        add_part(fus.component, n, os.path.join(step, files[n])); tick(n)
    shoulders = {}
    for c in CORNERS:
        sh = root.occurrences.addNewComponent(I); sh.component.name = 'CF2_Shoulder_' + c
        for n in h['20_Shoulders_J1_fixed']:
            key = '%s_%s' % (n, c); add_part(sh.component, key, os.path.join(step, files[key])); tick(key)
        shoulders[c] = sh
    arm0 = root.occurrences.addNewComponent(I); arm0.component.name = 'CF2_ArmModule'
    for n in h['30_Arm']:
        add_part(arm0.component, n, os.path.join(step, files[n])); tick(n)
    pod0 = root.occurrences.addNewComponent(I); pod0.component.name = 'CF2_RotorWheelPod'
    for grp, names in h['40_RotorWheelPod'].items():
        g = pod0.component.occurrences.addNewComponent(I); g.component.name = grp
        for n in names:
            add_part(g.component, n, os.path.join(step, files[n])); tick(n)
    arms = {'FL': arm0}; pods = {'FL': pod0}
    for c in ('FR', 'RL', 'RR'):
        arms[c] = root.occurrences.addExistingComponent(arm0.component, I); pods[c] = root.occurrences.addExistingComponent(pod0.component, I)
    return arms, pods

def find_modules(root):
    arms = {}; pods = {}; found = []
    for occ in root.occurrences:
        nm = occ.component.name
        if nm == 'CF2_ArmModule': found.append(('arm', occ))
        elif nm == 'CF2_RotorWheelPod': found.append(('pod', occ))
    a = [o for k, o in found if k == 'arm']; p = [o for k, o in found if k == 'pod']
    if len(a) != 4 or len(p) != 4: return None, None
    for c, o in zip(CORNERS, a): arms[c] = o
    for c, o in zip(CORNERS, p): pods[c] = o
    return arms, pods

def set_pose(arms, pods, corners):
    for c in CORNERS:
        arms[c].transform2 = to_m3d(corners[c]['arm']); pods[c].transform2 = to_m3d(corners[c]['pod'])
    adsk.doEvents(); _app.activeViewport.refresh()

def pose_from_angles(arms, pods, phi, rho, prm):
    corners = {}
    for c in CORNERS:
        a, p = corner_transforms(c, phi, rho, prm); corners[c] = dict(arm=a, pod=p)
    set_pose(arms, pods, corners)

def set_parameters(design, data):
    up = design.userParameters
    def put(name, expr, unit, comment):
        if up.itemByName(name) is None: up.add(name, adsk.core.ValueInput.createByString(expr), unit, comment)
    put('CF2_J1_front_yaw_deg', '50 deg', 'deg', 'front arm yaw J1 (rear mirrors: 180 - this). Checked range 0..170. Informational: run the script to apply')
    put('CF2_J2_roll_deg', '0 deg', 'deg', 'pod roll J2, all four pods. Only combinations inside joint_range_map.png are collision-free')
    put('CF2_arm_length', '100 mm', 'mm', 'J1 axis to J2 axis (from cad/params.py)')
    put('CF2_ring_outer_diameter', '157 mm', 'mm', 'tyre outer diameter')
    put('CF2_prop_diameter', '127 mm', 'mm', 'placeholder propeller diameter')

# ----------------------------------------------------------------------------- entry point
def run(context):
    try:
        data = json.load(open(os.path.join(HERE, 'cf2_transforms.json')))
        design = adsk.fusion.Design.cast(_app.activeProduct)
        if design is None:
            _ui.messageBox('Open or create a Fusion design first (File > New Design), then run the script again.'); return
        root = design.rootComponent; prm = data['params']
        arms, pods = find_modules(root)
        if arms is None:
            if root.occurrences.count > 0:
                _ui.messageBox('This design already contains other components. Run the script in an empty new design so the build is not mixed up.'); return
            pd = _ui.createProgressDialog(); pd.isBackgroundTranslucent = False; pd.show('CF-2 build', 'Importing parts...', 0, count_parts(data), 1)
            try:
                arms, pods = build(design, data, pd)
            finally:
                pd.hide()
            set_parameters(design, data)
            set_pose(arms, pods, data['configs']['flight']['corners'])
            _ui.messageBox('CF-2 assembly built in the flight pose.\n\nRun this script again to change pose (1 flight, 2 ground, 3 compact, 4 animate, 5 speedster, 6 animate flight-to-speedster, or "J1,J2" in degrees).\n\nConcept model: placeholders are size stand-ins; nothing here is flight-worthy.')
            return
        ok, cancelled = _ui.inputBox('Pose: 1 flight, 2 ground, 3 compact, 4 animate flight-ground, 5 speedster, 6 animate flight-to-speedster, or "J1_front_yaw,J2_roll" in degrees (e.g. 30,10)', 'CF-2 pose', '1')
        if cancelled: return
        s = ok.strip()
        if s in ('1', '2', '3', '5'):
            label = {'1': 'flight', '2': 'ground', '3': 'compact', '5': 'speed'}[s]; set_pose(arms, pods, data['configs'][label]['corners'])
        elif s == '6':
            for st in data['path_flight_to_speed']:
                set_pose(arms, pods, st['corners']); adsk.doEvents(); time.sleep(0.12)
        elif s == '4':
            for st in data['path']:
                set_pose(arms, pods, st['corners']); time.sleep(0.12)
        else:
            phi, rho = [float(x) for x in s.replace(';', ',').split(',')]
            pose_from_angles(arms, pods, phi, rho, prm)
            _ui.messageBox('Pose applied. Angles outside the checked region (see joint_range_map.png) may interpenetrate: this script does not check collisions.')
    except Exception:
        if _ui: _ui.messageBox('CF-2 script failed:\n%s' % traceback.format_exc())
