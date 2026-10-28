"""Export the CF-2 CAD: per-part STEP/STL (local frames), hierarchical coloured STEP assemblies per configuration, manifest for the FreeCAD builder.
usage: python3 export_all.py"""
import os, json, numpy as np, cadquery as cq
import library, assemble, kin, mass
from params import P, D
from render_scene import mat_for

OUT = '../build'

def rgb(name):
    c = mat_for(name)[1]; return cq.Color(c[0], c[1], c[2], 1.0)

def tmat(T):
    from OCP.gp import gp_Trsf
    M = np.asarray(T, float); t = gp_Trsf()
    t.SetValues(*[float(M[r, c]) for r in range(3) for c in range(4)])
    return cq.Location(t)

def part_files():
    os.makedirs(OUT + '/step_parts', exist_ok=True); L = library.lib(); files = {}
    for n, d in L.items():
        cq.exporters.export(cq.Workplane(obj=d['shape']), '%s/step_parts/%s.step' % (OUT, n)); files[n] = n + '.step'
    for c in kin.CORNERS:
        for nm in ('shoulder_plate_upper', 'shoulder_plate_lower', 'j1_hinge_pin'):
            sh = L[nm]['shape']
            if kin.SY[c] < 0: sh = sh.mirror('XZ')
            if kin.SX[c] < 0: sh = sh.mirror('YZ')
            cq.exporters.export(cq.Workplane(obj=sh), '%s/step_parts/%s_%s.step' % (OUT, nm, c)); files['%s_%s' % (nm, c)] = '%s_%s.step' % (nm, c)
    return files

def hierarchy():
    """subsystem tree (names) used in STEP assembly + FreeCAD + BOM"""
    return {
        '00_CF2_Chameleon-Ring_concept': {
            '10_Fuselage': ['fuselage_main_shell', 'panel_nose_cone', 'panel_dorsal_hatch', 'panel_belly_hatch', 'panel_service_left', 'panel_service_right',
                            'panel_tail_cap', 'antenna_fin', 'fasteners_M2'],
            '11_Internals_placeholders': ['battery_placeholder', 'fc_stack_placeholder', 'companion_computer_placeholder', 'camera_module_placeholder',
                                          'gps_puck_placeholder', 'nose_sensor_dome_placeholder'],
            '20_Shoulders_J1_fixed': ['shoulder_plate_upper', 'shoulder_plate_lower', 'j1_hinge_pin'],
            '30_Arm': ['arm_fairing', 'cfrp_arm_tube', 'j1_servo_placeholder', 'j2_servo_placeholder', 'j1_stop_lug'],
            '40_RotorWheelPod': {'41_Wheel_rolling': ['rolling_rim', 'tyre'],
                                 '42_Stator': ['stator_hub_spokes', 'support_roller_1', 'support_roller_2', 'support_roller_3', 'drive_pinion', 'wheel_gearmotor_placeholder'],
                                 '43_Rotor': ['rotor_motor_placeholder', 'rotor_prop_placeholder'],
                                 '44_Joint_J2': ['pylon_wrist_bridge']}}}

def build_assembly(cfg_name, cfg):
    """hierarchical cq.Assembly for one configuration (mirrored shoulder parts as separate shapes)"""
    L = library.lib(); root = cq.Assembly(name='CF2_%s' % cfg_name)
    fus = cq.Assembly(name='10_Fuselage'); intn = cq.Assembly(name='11_Internals_placeholders')
    for n in ('fuselage_main_shell', 'panel_nose_cone', 'panel_dorsal_hatch', 'panel_belly_hatch', 'panel_service_left', 'panel_service_right', 'panel_tail_cap', 'antenna_fin', 'fasteners_M2'):
        fus.add(L[n]['shape'], name=n, color=rgb(n))
    for n in ('battery_placeholder', 'fc_stack_placeholder', 'companion_computer_placeholder', 'camera_module_placeholder', 'gps_puck_placeholder', 'nose_sensor_dome_placeholder'):
        intn.add(L[n]['shape'], name=n, color=rgb(n))
    root.add(fus); root.add(intn)
    for c in kin.CORNERS:
        sh = cq.Assembly(name='20_Shoulder_%s' % c)
        for nm in ('shoulder_plate_upper', 'shoulder_plate_lower', 'j1_hinge_pin'):
            s = L[nm]['shape']
            if kin.SY[c] < 0: s = s.mirror('XZ')
            if kin.SX[c] < 0: s = s.mirror('YZ')
            sh.add(s, name='%s_%s' % (nm, c), color=rgb(nm))
        root.add(sh)
        ph, rho, TA, TP = kin.corner_state2(c, cfg)
        arm = cq.Assembly(name='30_Arm_%s' % c)
        for n in ('arm_fairing', 'cfrp_arm_tube', 'j1_servo_placeholder', 'j2_servo_placeholder', 'j1_stop_lug'):
            arm.add(L[n]['shape'], name='%s_%s' % (n, c), color=rgb(n))
        root.add(arm, name='30_Arm_%s' % c, loc=tmat(TA))
        pod = cq.Assembly(name='40_RotorWheelPod_%s' % c)
        for grp, names in (('41_Wheel_rolling', ['rolling_rim', 'tyre']), ('42_Stator', ['stator_hub_spokes', 'support_roller_1', 'support_roller_2', 'support_roller_3', 'drive_pinion', 'wheel_gearmotor_placeholder']),
                           ('43_Rotor', ['rotor_motor_placeholder', 'rotor_prop_placeholder']), ('44_Joint_J2', ['pylon_wrist_bridge'])):
            sub = cq.Assembly(name='%s_%s' % (grp, c))
            for n in names: sub.add(L[n]['shape'], name='%s_%s' % (n, c), color=rgb(n))
            pod.add(sub)
        root.add(pod, name='40_RotorWheelPod_%s' % c, loc=tmat(TP))
    return root

def main():
    files = part_files(); rows = mass.part_table()
    man = dict(params={k: v for k, v in P.items() if not isinstance(v, dict)}, derived=D, configs={k: P[k] for k in ('cfg_flight', 'cfg_ground', 'cfg_compact')},
               corners={c: dict(j1=list(kin.j1_pos(c)), side_sign=None) for c in kin.CORNERS}, files=files, hierarchy=hierarchy(), mass=rows, expected={})
    for name in ('cfg_flight', 'cfg_ground', 'cfg_compact'):
        cfg = P[name]; exp = {}
        for c in kin.CORNERS:
            ph, rho, TA, TP = kin.corner_state2(c, cfg); exp[c] = dict(phi=ph, rho=rho, arm_T=TA.tolist(), pod_T=TP.tolist())
        man['expected'][name] = exp
        a = build_assembly(name, cfg); a.save('%s/CF2_%s.step' % (OUT, name.replace('cfg_', '')), exportType='STEP'); print('saved assembly', name, flush=True)
    json.dump(man, open(OUT + '/manifest.json', 'w'), indent=1, default=float)

if __name__ == '__main__':
    main()
