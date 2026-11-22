import bpy, math, sys
from mathutils import Vector
out = sys.argv[sys.argv.index('--')+1]
args = sys.argv[sys.argv.index('--')+1:]
samples = int(args[1])
# optional: width height shift_x lens (banner framing)
width, height = (int(args[2]), int(args[3])) if len(args) > 3 else (1024, 1024)
shift_x = float(args[4]) if len(args) > 4 else 0.0
lens = float(args[5]) if len(args) > 5 else 88.0
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for t in ('OPTIX','CUDA'):
    try:
        prefs.compute_device_type = t; prefs.get_devices()
        if any(d.type == t for d in prefs.devices): break
    except Exception: pass
for d in prefs.devices: d.use = d.type != 'CPU'
sc.cycles.device = 'GPU'
sc.cycles.samples = samples
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = width, height
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.75

def hexrgb(h, a=1):
    h = h.lstrip('#'); c = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple((x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4) for x in c)+(a,)

def stone_mat(name, c_light, c_mid, c_dark, speck, seed, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord')
    # mottled base: large noise through a 3-stop ramp
    n1 = N.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 2.2; n1.inputs['Detail'].default_value = 8; n1.inputs['Roughness'].default_value = .6
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    r1 = N.new('ShaderNodeValToRGB'); e = r1.color_ramp.elements
    e[0].position, e[0].color = .3, hexrgb(c_dark); e[1].position, e[1].color = .7, hexrgb(c_light)
    mid = e.new(.5); mid.color = hexrgb(c_mid)
    L.new(n1.outputs['Fac'], r1.inputs['Fac'])
    # granite grains: two voronoi layers thresholded
    def grains(scale, pos, col, s):
        v = N.new('ShaderNodeTexVoronoi'); v.feature = 'F1'; v.inputs['Scale'].default_value = scale
        v.inputs['Randomness'].default_value = 1
        L.new(tc.outputs['Object'], v.inputs['Vector'])
        r = N.new('ShaderNodeValToRGB'); r.color_ramp.interpolation = 'EASE'
        r.color_ramp.elements[0].position = pos; r.color_ramp.elements[0].color = (1,1,1,1)
        r.color_ramp.elements[1].position = pos+.04; r.color_ramp.elements[1].color = (0,0,0,1)
        L.new(v.outputs['Distance'], r.inputs['Fac'])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MIX'
        mx.inputs[7].default_value = hexrgb(col)
        return r, mx
    cur = r1.outputs['Color']
    for scale, pos, col, strength in ((26, .11, speck, .9), (17, .07, '#fbf8f1', .55), (70, .13, speck, .7)):
        r, mx = grains(scale, pos, col, strength)
        mt = N.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = strength
        L.new(r.outputs['Color'], mt.inputs[0]); L.new(mt.outputs[0], mx.inputs['Factor'])
        L.new(cur, mx.inputs[6]); cur = mx.outputs[2]
    L.new(cur, bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    # fine bump
    n2 = N.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 90; n2.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], n2.inputs['Vector'])
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .25; bump.inputs['Distance'].default_value = .02
    L.new(n2.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m

def stone(name, size, loc, rot, mat, seed):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1, location=loc)
    o = bpy.context.object; o.name = name
    o.scale = size; o.rotation_euler = [math.radians(a) for a in rot]
    tex = bpy.data.textures.new(name+'_d', 'CLOUDS'); tex.noise_scale = 0.9; tex.noise_depth = 2
    d = o.modifiers.new('d', 'DISPLACE'); d.texture = tex; d.strength = 0.07; d.mid_level = .5; d.texture_coords = 'OBJECT'
    o.modifiers.new('s', 'SUBSURF').levels = 1
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o

mb = stone_mat('base', '#e6d9c1', '#d2c0a0', '#ad9a7a', '#4a4036', 1, .55)
mm = stone_mat('mid',  '#b4cbb9', '#8fac97', '#6a8672', '#2c3a30', 2, .42)
mt = stone_mat('top',  '#f1e9da', '#e2d6bd', '#c3b291', '#5c5244', 3, .5)
stone('base', (1.55, 1.2, .52), (0, 0, .5), (0, 0, 8), mb, 1)
stone('mid',  (1.08, .86, .4), (.04, .02, 1.36), (2, -3, -12), mm, 2)
stone('top',  (.68, .56, .32), (-.02, 0, 2.03), (-2, 2, 18), mt, 3)

# studio sweep backdrop in the app green
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 6, 0))
bd = bpy.context.object
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=40); bpy.ops.object.mode_set(mode='OBJECT')
for v in bd.data.vertices:
    y = v.co.y
    if y > 2: v.co.z = (y-2)**2 * .18
bd.modifiers.new('s', 'SUBSURF').levels = 2
bpy.ops.object.shade_smooth()
g = bpy.data.materials.new('green'); g.use_nodes = True
pb = g.node_tree.nodes['Principled BSDF']; pb.inputs['Base Color'].default_value = hexrgb('#2f5a47'); pb.inputs['Roughness'].default_value = .85
bd.data.materials.append(g)

def area(name, loc, size, power, color, target=(0,0,1.1)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object; l.data.size = size; l.data.energy = power; l.data.color = color; l.visible_camera = False; l.visible_glossy = name != 'backglow'
    l.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
area('key', (-4.5, -5, 6.5), 5, 2600, (1, .96, .9))
area('fill', (5, -4, 2.5), 6, 700, (.85, .93, 1))
area('rim', (1, 5, 5.5), 3, 1400, (1, 1, 1))
bpy.ops.object.light_add(type='POINT', location=(0, 4.5, 1.8)); bg = bpy.context.object; bg.data.energy = 2200; bg.data.shadow_soft_size = 2; bg.data.color = (.92, 1, .95); bg.visible_camera = False; bg.visible_glossy = False
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = hexrgb('#24493a'); w.node_tree.nodes['Background'].inputs['Strength'].default_value = .6

bpy.ops.object.camera_add(location=(0, -11.5, 3.1))
cam = bpy.context.object; sc.camera = cam; cam.data.lens = lens; cam.data.sensor_fit = 'VERTICAL'; cam.data.shift_x = shift_x
cam.rotation_euler = (Vector((0, 0, 1.25)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
