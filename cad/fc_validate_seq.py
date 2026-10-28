import json, os, numpy as np, FreeCAD as App, sys
import json
OUT = '../build'; doc = App.openDocument(OUT + '/CF2_Chameleon-Ring.FCStd'); ss = doc.getObject('Params')
def setv(a, v): ss.set(ss.getCellFromAlias(a), str(v))
setv('cfg', 4); worst = 0.0
for e in json.load(open(OUT + '/expected_seq.json')):
    ph, rh = e['phi'], e['rho']; setv('seqPhiF', ph); setv('seqRho', rh); doc.recompute()
    for c in ('FL', 'FR', 'RL', 'RR'):
        TA = np.array(e['T'][c]['arm']); TP = np.array(e['T'][c]['pod'])
        for obj, M in ((doc.getObject('Arm_' + c), TA), (doc.getObject('RotorWheelPod_' + c), TP)):
            G = obj.getGlobalPlacement().Matrix; A = np.array([[G.A11, G.A12, G.A13, G.A14], [G.A21, G.A22, G.A23, G.A24], [G.A31, G.A32, G.A33, G.A34]])
            worst = max(worst, float(np.abs(A - M[:3]).max()))
print('SEQ_MAX_ERR', worst)
open(OUT + '/fc_validation_sequence.txt', 'w').write('max abs placement error (mm / matrix element) over 6 sequence states x 4 corners: %g\n' % worst)
