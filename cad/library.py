"""Part library: every CF-2 part once, in its local frame, with role/material/placeholder metadata.
Local frames:  fuselage-frame parts: global;  arm parts: arm-local (origin J1 axis);  pod parts: pod-local (origin ring centre, blade plane)."""
import math, functools, cadquery as cq
from cadquery import Vector as V
import parts_pod as pp, parts_body as pb
from params import P, D

# material table: name -> (density g/cm3, fill factor = solid fraction of the CAD volume that is real material)
MAT = {
    'PA12-CF (SLS/FDM)':  (1.10, 0.55),   # printed structure, shell/infill factor assumed
    'PA12 (SLS)':         (1.01, 0.60),
    'TPU 95A':            (1.20, 0.90),
    'CFRP tube':          (1.55, 1.00),
    'PETG':               (1.27, 0.45),
    'Steel':              (7.80, 1.00),
    'Acetal (POM)':       (1.41, 1.00),
    'Placeholder block':  (0.0, 0.0),     # mass taken from catalogue assumption, not from volume
    'Electronics':        (0.0, 0.0),
}

@functools.lru_cache(maxsize=1)
def lib():
    L = {}
    def add(name, shape, group, material, role, placeholder=False, mass_g=None, note='', frame='pod'):
        L[name] = dict(shape=shape, group=group, material=material, role=role, placeholder=placeholder, mass_g=mass_g, note=note, frame=frame)
    # ---- pod ----
    rim, Zg = pp.ring_rim()
    add('rolling_rim', rim, 'rotor_wheel_pod/wheel', 'PA12-CF (SLS/FDM)', 'Annular duct wall + roller V-rail + internal ring gear. Rolls on tyre.', False, note='Ring-gear Z=%d, m=%.1f' % (Zg, P['gear_m']))
    add('tyre', pp.tire(), 'rotor_wheel_pod/wheel', 'TPU 95A', 'Tread: only part intended to touch ground.', False)
    add('stator_hub_spokes', pp.stator(), 'rotor_wheel_pod/stator', 'PA12-CF (SLS/FDM)', 'Hub plate + 4 spokes carrying motor, 3 rollers, drive pinion.', False)
    for i, r in enumerate(pp.rollers()):
        add('support_roller_%d' % (i + 1), r, 'rotor_wheel_pod/stator', 'Acetal (POM)', 'V-groove roller carrying the ring (unproven wear/noise).', False)
    pin, gm, pxy = pp.drive_pinion()
    add('drive_pinion', pin, 'rotor_wheel_pod/stator', 'Steel', 'Drives internal ring gear.', True, mass_g=2.0, note='placeholder geometry')
    add('wheel_gearmotor_placeholder', gm, 'rotor_wheel_pod/stator', 'Electronics', 'N20-class gearmotor, size only.', True, mass_g=10.0, note='torque/speed not selected')
    add('rotor_motor_placeholder', pp.motor(), 'rotor_wheel_pod/rotor', 'Electronics', '2306-class outrunner, size only.', True, mass_g=33.0, note='catalogue-class mass, unverified')
    add('rotor_prop_placeholder', pp.prop(), 'rotor_wheel_pod/rotor', 'Placeholder block', '127 mm 3-blade reference prop. NOT an aerodynamic design.', True, mass_g=5.0, note='placeholder geometry')
    add('pylon_wrist_bridge', pp.pylon_bridge(), 'rotor_wheel_pod/joint_J2', 'PA12-CF (SLS/FDM)', 'Hub -> J2 output flange. Carries ALL ground loads of the wheel (unproven).', False)
    # ---- arm ----
    a = pb.arm()
    add('arm_fairing', a['arm_fairing'], 'arm', 'PA12-CF (SLS/FDM)', 'Knuckle + faired arm + wrist housing (2 printed halves in production).', False, frame='arm')
    add('cfrp_arm_tube', a['cfrp_tube'], 'arm', 'CFRP tube', 'Ø10x1 carbon spar (reference).', False, frame='arm')
    add('j1_servo_placeholder', a['j1_servo_placeholder'], 'arm', 'Electronics', 'Hinge actuator, size only.', True, mass_g=12.0, frame='arm')
    add('j2_servo_placeholder', a['j2_servo_placeholder'], 'arm', 'Electronics', 'Pod-roll actuator, size only.', True, mass_g=12.0, frame='arm')
    add('j1_stop_lug', a['stop_lug'], 'arm', 'PA12-CF (SLS/FDM)', 'Mechanical stop on knuckle (positions unvalidated).', False, frame='arm')
    # ---- fuselage ----
    sp = pb.fuselage_split()
    names = {'fuselage_main': 'fuselage_main_shell', 'nose_cone': 'panel_nose_cone', 'dorsal_hatch': 'panel_dorsal_hatch', 'belly_hatch': 'panel_belly_hatch',
             'service_L': 'panel_service_left', 'service_R': 'panel_service_right', 'tail_cap': 'panel_tail_cap'}
    for k, nm in names.items():
        add(nm, sp[k], 'fuselage', 'PA12-CF (SLS/FDM)', ('Main shell, 2 mm wall.' if k == 'fuselage_main' else 'Removable access panel (screwed).'), False, frame='fus')
    add('antenna_fin', pb.antenna_fin(), 'fuselage', 'PA12-CF (SLS/FDM)', 'Dorsal antenna fin (non-structural fairing).', False, frame='fus')
    add('nose_sensor_dome_placeholder', pb.nose_dome(), 'fuselage', 'Placeholder block', 'Sensor window/dome (glazing placeholder).', True, mass_g=4.0, frame='fus')
    add('fasteners_M2', pb.fasteners(), 'fuselage', 'Steel', 'M2 pan-head screws (placeholder positions).', True, mass_g=6.0, frame='fus')
    for k, s in pb.internals().items():
        mg = dict(battery_placeholder=190.0, fc_stack_placeholder=14.0, companion_computer_placeholder=45.0, camera_module_placeholder=22.0, gps_puck_placeholder=15.0)[k]
        add(k, s, 'fuselage/internals', 'Electronics', 'Packaging envelope only.', True, mass_g=mg, note='catalogue-class mass, unverified', frame='fus')
    up, lo, pin_ = pb.shoulder_plates()
    add('shoulder_plate_upper', up, 'fuselage/shoulder', 'PA12-CF (SLS/FDM)', 'Upper clevis plate of J1 (x4 by symmetry).', False, frame='fus')
    add('shoulder_plate_lower', lo, 'fuselage/shoulder', 'PA12-CF (SLS/FDM)', 'Lower clevis plate of J1 (x4 by symmetry).', False, frame='fus')
    add('j1_hinge_pin', pin_, 'fuselage/shoulder', 'Steel', 'Ø4 pin (x4).', True, mass_g=3.0, frame='fus')
    return L
