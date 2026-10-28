"""Open the FCStd, set Params.cfg to 1/2/3, recompute, compare every Arm_/RotorWheelPod_ global placement with the numpy transforms in manifest.json"""
import json, os, numpy as np, FreeCAD as App
OUT = os.environ.get('CF2_OUT', '../build')
man = json.load(open(OUT + '/manifest.json'))
doc = App.openDocument(OUT + '/CF2_Chameleon-Ring.FCStd'); ss = doc.getObject('Params')
res = {}
for k, name in ((1, 'cfg_flight'), (2, 'cfg_ground'), (3, 'cfg_compact')):
    ss.set(ss.getCellFromAlias('cfg'), str(k)); doc.recompute()
    worst_t = worst_r = 0.0
    for c in ('FL', 'FR', 'RL', 'RR'):
        for obj, key in ((doc.getObject('Arm_' + c), 'arm_T'), (doc.getObject('RotorWheelPod_' + c), 'pod_T')):
            M = np.array(man['expected'][name][c][key]); G = obj.getGlobalPlacement().Matrix
            A = np.array([[G.A11, G.A12, G.A13, G.A14], [G.A21, G.A22, G.A23, G.A24], [G.A31, G.A32, G.A33, G.A34]])
            worst_t = max(worst_t, float(np.abs(A[:, 3] - M[:3, 3]).max())); worst_r = max(worst_r, float(np.abs(A[:, :3] - M[:3, :3]).max()))
    res[name] = dict(max_translation_err_mm=worst_t, max_rotation_matrix_err=worst_r); print(name, res[name])
json.dump(res, open(OUT + '/fc_validation.json', 'w'), indent=1)
