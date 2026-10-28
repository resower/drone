"""Blender (bpy/Cycles) renderer.  usage: python3 render_scene.py spec.json
spec = dict(instances=[dict(stl, T(4x4 row-major), name)], out, res=[w,h], samples, cam=dict(loc, target, lens), ground=bool, ground_z, cutaway=None, mode='studio')"""
import sys, json, math, bpy, mathutils, os

def mat_for(name):
    n = name.lower()
    if n.startswith('fuselage_main'): return ('pearl', (0.86, 0.87, 0.86, 1), 0.0, 0.32)
    if n.startswith('panel_nose') or n.startswith('panel_tail'): return ('graphite', (0.045, 0.05, 0.055, 1), 0.0, 0.38)
    if n.startswith('panel_'): return ('panel', (0.70, 0.72, 0.72, 1), 0.0, 0.34)
    if n.startswith('fasteners') or 'pin' in n and 'pinion' not in n: return ('steel', (0.65, 0.66, 0.68, 1), 1.0, 0.28)
    if n.startswith('shoulder_plate'): return ('anodized', (0.90, 0.30, 0.04, 1), 0.85, 0.30)
    if n.startswith('arm_fairing'): return ('graphite', (0.05, 0.055, 0.06, 1), 0.0, 0.42)
    if n.startswith('cfrp'): return ('carbon', (0.02, 0.02, 0.022, 1), 0.2, 0.25)
    if n.startswith('rolling_rim'): return ('rim', (0.12, 0.125, 0.13, 1), 0.35, 0.33)
    if n.startswith('tyre'): return ('rubber', (0.012, 0.012, 0.014, 1), 0.0, 0.72)
    if n.startswith('support_roller'): return ('orange', (0.95, 0.33, 0.03, 1), 0.0, 0.40)
    if n.startswith('drive_pinion'): return ('steel', (0.65, 0.66, 0.68, 1), 1.0, 0.28)
    if n.startswith('stator'): return ('stator', (0.16, 0.17, 0.18, 1), 0.2, 0.40)
    if n.startswith('pylon'): return ('graphite2', (0.09, 0.095, 0.10, 1), 0.3, 0.38)
    if n.startswith('rotor_motor'): return ('motor', (0.10, 0.12, 0.18, 1), 0.9, 0.30)
    if n.startswith('rotor_prop'): return ('prop', (0.55, 0.57, 0.60, 1), 0.0, 0.35)
    if n.startswith('wheel_gearmotor'): return ('steel2', (0.5, 0.5, 0.52, 1), 1.0, 0.35)
    if 'servo' in n: return ('servo', (0.02, 0.02, 0.025, 1), 0.0, 0.5)
    if n.startswith('battery'): return ('battery', (0.15, 0.30, 0.55, 1), 0.0, 0.5)
    if n.startswith('fc_stack'): return ('pcb', (0.05, 0.35, 0.18, 1), 0.0, 0.45)
    if n.startswith('companion'): return ('pcb2', (0.10, 0.45, 0.25, 1), 0.0, 0.45)
    if n.startswith('camera'): return ('cam', (0.03, 0.03, 0.035, 1), 0.0, 0.3)
    if n.startswith('gps'): return ('gps', (0.7, 0.7, 0.72, 1), 0.0, 0.5)
    if n.startswith('j1_stop'): return ('orange', (0.95, 0.33, 0.03, 1), 0.0, 0.40)
    return ('misc', (0.5, 0.5, 0.5, 1), 0.0, 0.5)

_mats = {}
def get_mat(name, override=None):
    key, col, met, rough = mat_for(name)
    if override and key in override: col = override[key]
    if key in _mats and not override: return _mats[key]
    m = bpy.data.materials.new(key + ('_o' if override else '')); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = col; b.inputs['Metallic'].default_value = met; b.inputs['Roughness'].default_value = rough
    if key in ('pearl', 'panel', 'graphite', 'anodized', 'rim', 'graphite2'):
        try: b.inputs['Coat Weight'].default_value = 0.35; b.inputs['Coat Roughness'].default_value = 0.15
        except Exception: pass
    if key == 'prop':
        try: b.inputs['Alpha'].default_value = 0.55
        except Exception: pass
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    _mats[key] = m; return m

def main(spec):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spec.get('samples', 64)
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = spec.get('res', [1280, 720]); sc.render.resolution_percentage = 100
    sc.render.threads_mode = 'FIXED'; sc.render.threads = 2
    sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 4; sc.cycles.transmission_bounces = 4; sc.cycles.transparent_max_bounces = 8
    try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    # world: soft studio gradient
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord'); grad = nt.nodes.new('ShaderNodeTexGradient'); cr = nt.nodes.new('ShaderNodeValToRGB'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (math.radians(-90), 0, 0)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], grad.inputs['Vector']); nt.links.new(grad.outputs['Fac'], cr.inputs['Fac'])
    cr.color_ramp.elements[0].color = tuple(spec.get('bg0', (0.55, 0.58, 0.62, 1))); cr.color_ramp.elements[1].color = tuple(spec.get('bg1', (0.92, 0.93, 0.95, 1)))
    nt.links.new(cr.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = spec.get('world_strength', 0.9)
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    # objects
    for it in spec['instances']:
        bpy.ops.wm.stl_import(filepath=it['stl'])
        ob = bpy.context.selected_objects[0] if bpy.context.selected_objects else bpy.context.object
        T = it['T']; ob.matrix_world = mathutils.Matrix([T[0], T[1], T[2], T[3]])
        ob.data.materials.append(get_mat(it['name'], spec.get('override')))
        try:
            bpy.context.view_layer.objects.active = ob; ob.select_set(True)
            if it.get('smooth', True): bpy.ops.object.shade_smooth()
            ob.select_set(False)
        except Exception: pass
        if 'autosmooth' not in it:
            try:
                m = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); m.keep_sharp = True
                ob.data.polygons.foreach_set('use_smooth', [True]*len(ob.data.polygons)); 
            except Exception: pass
    # ground
    if spec.get('ground', True):
        bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, spec.get('ground_z', 0)))
        g = bpy.context.object; gm = bpy.data.materials.new('floor'); gm.use_nodes = True
        b = gm.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = tuple(spec.get('floor', (0.80, 0.81, 0.83, 1))); b.inputs['Roughness'].default_value = 0.55
        g.data.materials.append(gm)
    # lights
    def area(loc, target, size, energy, color=(1, 1, 1)):
        bpy.ops.object.light_add(type='AREA', location=loc); l = bpy.context.object; l.data.size = size; l.data.energy = energy; l.data.color = color
        d = mathutils.Vector(target) - mathutils.Vector(loc); l.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    tg = spec['cam']['target']
    area((tg[0] - 500, tg[1] - 450, tg[2] + 650), tg, 700, spec.get('key', 150000), (1.0, 0.97, 0.93))
    area((tg[0] + 600, tg[1] + 300, tg[2] + 300), tg, 600, spec.get('fill', 50000), (0.9, 0.95, 1.0))
    area((tg[0] + 100, tg[1] + 700, tg[2] + 500), tg, 500, spec.get('rim', 60000), (1, 1, 1))
    area((tg[0], tg[1], tg[2] + 900), tg, 900, spec.get('top', 70000), (1, 1, 1))
    # camera
    cd = bpy.data.cameras.new('c'); cd.lens = spec['cam'].get('lens', 60); cd.sensor_width = 36; cd.clip_start = 5.0; cd.clip_end = 20000.0
    co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
    co.location = spec['cam']['loc']
    d = mathutils.Vector(tg) - mathutils.Vector(spec['cam']['loc']); co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = spec['out']; sc.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)

if __name__ == '__main__':
    main(json.load(open(sys.argv[1])))
