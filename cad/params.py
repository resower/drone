"""CF-2 'Chameleon-Ring' research demonstrator -- single source of truth (mm, degrees, grams).
Everything here is a CONCEPT parameter, not a verified design value. Frames: x fwd, y left, z up."""
import math

P = dict(
    # ---------------- rotor + rotor-wheel ring ("pod") : pod frame, z = rotor axis, z=0 = blade plane
    prop_d=127.0,            # 5-inch class reference prop (placeholder geometry)
    tip_gap=4.0,             # radial blade-tip to duct-wall clearance (print tolerance driven; unproven)
    z_top=10.0, z_bot=-29.0, # ring axial extent -> rim width 39
    lip_r=6.0,               # bellmouth lip radius
    gear_m=1.5,              # internal ring-gear module
    gear_band=7.0,           # axial height of ring-gear band
    rail_z=-17.0,            # axial position of roller V-rail
    wall_out=75.0,           # rim flange outer radius
    tire_r_out=77.5,         # tread outer radius (tire is the only part meant to touch ground)
    tire_z0=-21.0, tire_z1=1.0,
    n_lugs=36,
    # stator inside the ring
    spoke_z=-33.0, spoke_t=4.0, spoke_w=8.0, hub_r=18.0,
    roller_r=5.0, roller_h=6.0,
    pinion_Z=12,
    motor_d=28.0, motor_h=31.0, motor_base_z=-33.0,
    pylon_r=9.0, pylon_len=20.5,
    # pod -> arm joint (J2: roll about the arm axis)
    e_lat=42.0,              # distance arm axis -> ring mid-plane
    # ---------------- arm
    arm_L=100.0,              # J1 axis -> pod centre (horizontal distance along the arm)
    knuckle_r=17.0, knuckle_h=24.0,
    arm_end_gap=26.0,        # arm body ends this far inboard of the pod axis
    arm_w0=18.0, arm_h0=20.0, arm_w1=15.0, arm_h1=16.0,
    # ---------------- fuselage
    f_len=300.0, f_w=66.0, f_h=56.0, wall=2.0,
    j1_x=58.0, j1_y=46.0,    # J1 (arm hinge) axis position, |x|, |y|
    j1_z=0.0,
    stagger=0.0,            # checkerboard shoulder height: FL,RR at +stagger, FR,RL at -stagger; arms slope back to a common wrist height
    # ---------------- configurations (deg). phi = arm yaw from +x (left side, CCW); rho = pod roll (outboard +)
    cfg_flight=dict(phi_F=50.0, phi_R=130.0, rho_F=0.0, rho_R=0.0),
    cfg_ground=dict(phi_F=0.0,  phi_R=180.0, rho_F=90.0, rho_R=90.0),
    cfg_speed=dict(phi_F=75.0, phi_R=105.0, rho_F=-90.0, rho_R=90.0),   # SPEEDSTER (Rev-C): all four pods rolled so thrust points forward; arms swept toward lateral; wing carries weight
    cfg_compact=dict(phi_F=70.0, phi_R=110.0, rho_F=0.0, rho_R=0.0),   # best Rev-A pose with >=20 mm margin: modest (~10 %) volume reduction only
)
D = {}
D['R_in'] = P['prop_d']/2 + P['tip_gap']
D['gear_Rp'] = None
D['pod_A_z'] = P['spoke_z'] - 2.0 - P['pylon_len']          # arm axis in pod frame (z)
D['ring_mid'] = 0.5*(P['z_top'] + P['z_bot'])
D['e_check'] = D['ring_mid'] - D['pod_A_z']

DZ = {'FL': +P['stagger'], 'RR': +P['stagger'], 'FR': -P['stagger'], 'RL': -P['stagger']}
VAR = {c: ('A' if DZ[c] > 0 else 'B') for c in DZ}          # arm variant: A = J1 high (wrist slopes down), B = J1 low (wrist slopes up)
