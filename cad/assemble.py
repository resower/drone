"""Instances of the whole assembly for a given configuration; STL export helpers."""
import os, numpy as np, cadquery as cq
import library, kin
from params import P, D

OUT = '../build'

def instances(cfg, dz=None):
    """list of dict(name, part, T(4x4), group, frame)"""
    L = library.lib(); inst = []
    for name, d in L.items():
        if d['frame'] == 'fus' and d['group'] != 'fuselage/shoulder':
            inst.append(dict(name=name, part=name, T=np.eye(4), group=d['group']))
    for c in kin.CORNERS:
        for nm, mir in (('shoulder_plate_upper', 0), ('shoulder_plate_lower', 0), ('j1_hinge_pin', 0)):
            inst.append(dict(name='%s_%s' % (nm, c), part=nm, T=np.eye(4), group='fuselage/shoulder', mirror=c))
        ph, rho, TA, TP = kin.corner_state(c, cfg, dz)
        for nm, d in L.items():
            if d['frame'] == 'arm': inst.append(dict(name='%s_%s' % (nm, c), part=nm, T=TA, group='arm_%s' % c))
            if d['frame'] == 'pod': inst.append(dict(name='%s_%s' % (nm, c), part=nm, T=TP, group='pod_%s' % c))
    return inst

def export_stls(dirn=OUT + '/stl_parts'):
    os.makedirs(dirn, exist_ok=True); L = library.lib()
    for name, d in L.items():
        cq.exporters.export(cq.Workplane(obj=d['shape']), '%s/%s.stl' % (dirn, name), tolerance=0.15, angularTolerance=0.12)
    # mirrored shoulder parts for the four corners
    for c in kin.CORNERS:
        for nm in ('shoulder_plate_upper', 'shoulder_plate_lower', 'j1_hinge_pin'):
            sh = L[nm]['shape']
            if kin.SY[c] < 0: sh = sh.mirror('XZ')
            if kin.SX[c] < 0: sh = sh.mirror('YZ')
            cq.exporters.export(cq.Workplane(obj=sh), '%s/%s_%s.stl' % (dirn, nm, c), tolerance=0.15, angularTolerance=0.12)

def instance_stl(i):
    if 'mirror' in i: return '%s_%s.stl' % (i['part'], i['mirror'])
    return '%s.stl' % i['part']
