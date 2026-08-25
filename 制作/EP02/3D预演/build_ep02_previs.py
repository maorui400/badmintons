import bpy
import math
import os
from mathutils import Vector


ROOT = os.path.dirname(os.path.abspath(__file__))
PREVIEW_DIR = os.path.join(ROOT, "预览")
BLEND_PATH = os.path.join(ROOT, "EP02_3D导演预演_v001.blend")
os.makedirs(PREVIEW_DIR, exist_ok=True)


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                  bpy.data.cameras, bpy.data.lights):
        pass


def mat(name, color, metallic=0.0, roughness=0.55, emission=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 3.0
    return m


M = {}


def init_materials():
    colors = {
        "court": (0.035, 0.36, 0.28), "line": (0.92, 0.95, 0.90),
        "net": (0.018, 0.022, 0.028), "wall": (0.035, 0.055, 0.11),
        "floor": (0.055, 0.07, 0.10), "skin_td": (0.62, 0.66, 0.70),
        "white": (0.93, 0.95, 0.96), "blue": (0.03, 0.19, 0.74),
        "black": (0.008, 0.010, 0.014), "skin_oc": (0.31, 0.33, 0.35),
        "yellow": (1.0, 0.67, 0.02), "red": (0.85, 0.02, 0.045),
        "navy": (0.018, 0.04, 0.16), "towel": (0.025, 0.19, 0.83),
        "phone": (0.025, 0.028, 0.035), "track": (0.38, 0.035, 0.035),
        "grass": (0.025, 0.20, 0.075), "tree": (0.025, 0.16, 0.07),
        "wood": (0.22, 0.09, 0.035), "glass": (0.20, 0.30, 0.42),
        "shuttle": (0.94, 0.94, 0.88), "moon": (0.65, 0.78, 1.0),
    }
    for key, value in colors.items():
        M[key] = mat(key, value, metallic=0.15 if key in {"phone", "black"} else 0.0)


def move_to_collection(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def cube(name, loc, scale, material, col, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("soft_edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    obj.data.materials.append(material)
    return move_to_collection(obj, col)


def uv_sphere(name, loc, scale, material, col):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return move_to_collection(obj, col)


def cylinder_between(name, a, b, radius, material, col, vertices=16):
    a, b = Vector(a), Vector(b)
    mid = (a + b) / 2
    direction = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                       depth=direction.length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction.normalized())
    obj.data.materials.append(material)
    return move_to_collection(obj, col)


def cone(name, loc, radius, depth, material, col, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=radius, radius2=0,
                                   depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return move_to_collection(obj, col)


def text_obj(label, loc, col, size=0.75, rot=(math.radians(72), 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = label
    obj.data.body = label
    obj.data.align_x = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.018
    obj.data.materials.append(M["line"])
    obj.hide_render = True
    return move_to_collection(obj, col)


def add_area_light(name, loc, energy, color, col, size=8.0):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    col.objects.link(obj)
    obj.rotation_euler = (0, 0, 0)
    return obj


def point_light(name, loc, energy, color, col, radius=1.0):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    col.objects.link(obj)
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera(name, loc, target, lens, col):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    col.objects.link(obj)
    look_at(obj, target)
    return obj


def add_court(col, ox=0, oy=0, indoor=True):
    # BWF nominal dimensions in metres. `cube()` receives final dimensions.
    # Boundary dimensions are measured to the outside edges of 40 mm lines.
    line_w = .04
    cube("BWF_COURT_SURFACE_6.10x13.40M", (ox, oy, 0), (6.10, 13.40, 0.08), M["court"], col)

    # Doubles outer sidelines: outside edge at x = +/-3.05 m.
    for x in (-3.03, 3.03):
        cube("BWF_DOUBLES_SIDELINE", (ox + x, oy, 0.06), (line_w, 13.40, 0.025), M["line"], col)
    # Singles sidelines: outside-to-outside width 5.18 m.
    for x in (-2.57, 2.57):
        cube("BWF_SINGLES_SIDELINE", (ox + x, oy, 0.06), (line_w, 13.40, 0.025), M["line"], col)

    # Baselines: outside edge at y = +/-6.70 m.
    for y in (-6.68, 6.68):
        cube("BWF_BASELINE", (ox, oy + y, 0.06), (6.10, line_w, 0.025), M["line"], col)
    # Short service lines: near edge is 1.98 m from the net plane.
    for y in (-2.00, 2.00):
        cube("BWF_SHORT_SERVICE_LINE", (ox, oy + y, 0.06), (6.10, line_w, 0.025), M["line"], col)
    # Doubles long-service lines: 0.76 m inside the back boundary.
    for y in (-5.92, 5.92):
        cube("BWF_DOUBLES_LONG_SERVICE_LINE", (ox, oy + y, 0.06), (6.10, line_w, 0.025), M["line"], col)

    # Centre service lines, from the outer edge of the short service line to
    # the inner edge of each baseline.
    centre_len = 6.66 - 2.02
    centre_mid = (6.66 + 2.02) / 2
    cube("BWF_CENTER_SERVICE_NEAR", (ox, oy - centre_mid, 0.06), (line_w, centre_len, 0.025), M["line"], col)
    cube("BWF_CENTER_SERVICE_FAR", (ox, oy + centre_mid, 0.06), (line_w, centre_len, 0.025), M["line"], col)
    add_net(col, ox, oy)
    if indoor:
        cube("hall_floor", (ox, oy, -0.12), (16, 22, 0.15), M["floor"], col)
        cube("back_wall", (ox, oy + 10.5, 3.3), (16, 0.25, 6.6), M["wall"], col)
        cube("side_wall", (ox + 7.8, oy, 3.3), (0.25, 21, 6.6), M["wall"], col)
        cube("side_wall", (ox - 7.8, oy, 3.3), (0.25, 21, 6.6), M["wall"], col)
    return (ox, oy)


def add_net(col, ox, oy):
    # BWF: posts stand on the doubles sidelines at 1.55 m; net centre is
    # 1.524 m high. Proxy mesh bottom is 0.76 m below its local top edge.
    z0, z1 = 0.764, 1.524
    cylinder_between("BWF_POST_L_1.55M", (ox - 3.05, oy, 0), (ox - 3.05, oy, 1.55), .025, M["black"], col)
    cylinder_between("BWF_POST_R_1.55M", (ox + 3.05, oy, 0), (ox + 3.05, oy, 1.55), .025, M["black"], col)
    for i in range(27):
        x = ox - 3.05 + i * (6.1 / 26)
        cylinder_between("net_v", (x, oy, z0), (x, oy, z1), .008, M["net"], col, vertices=8)
    for i in range(7):
        z = z0 + i * ((z1 - z0) / 6)
        cylinder_between("net_h", (ox - 3.05, oy, z), (ox + 3.05, oy, z), .008, M["net"], col, vertices=8)
    cube("BWF_NET_TOP_TAPE", (ox, oy, z1), (6.10, .045, .065), M["line"], col)


def local_point(origin, yaw, p):
    x, y, z = p
    c, s = math.cos(yaw), math.sin(yaw)
    return (origin[0] + x * c - y * s, origin[1] + x * s + y * c, origin[2] + z)


def add_racket(name, grip, direction, color, col):
    # Regulation adult proxy: total 0.675 m, fixed proportions.
    d = Vector(direction).normalized()
    grip = Vector(grip)
    shaft_end = grip + d * 0.50
    cylinder_between(name + "_shaft", grip, shaft_end, .010, M["black"], col, vertices=10)
    cylinder_between(name + "_grip", grip - d * .02, grip + d * .14, .022, M["white"], col, vertices=12)
    center = grip + d * .57
    # Hoop as 20 short segments in a plane chosen from the shaft direction.
    side = d.cross(Vector((0, 0, 1)))
    if side.length < .1:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d).normalized()
    pts = []
    for i in range(25):
        a = 2 * math.pi * i / 24
        pts.append(center + side * (.105 * math.cos(a)) + up * (.145 * math.sin(a)))
    for i in range(24):
        cylinder_between(name + "_head", pts[i], pts[i + 1], .009, color, col, vertices=8)
    return center


def add_watch(loc, col):
    # Highly visible closed black band marker, right wrist only.
    uv_sphere("RIGHT_WRIST_BLACK_WATCH", loc, (.075, .055, .045), M["black"], col)


def add_cat(name, pos, yaw, skin, shirt, shorts, col, pose="ready", racket=True):
    origin = (pos[0], pos[1], pos[2])
    p = lambda v: local_point(origin, yaw, v)
    # Body and identity markers.
    uv_sphere(name + "_torso", p((0, 0, 1.02)), (.29, .22, .43), shirt, col)
    uv_sphere(name + "_hips", p((0, 0, .73)), (.26, .20, .22), shorts, col)
    uv_sphere(name + "_head", p((0, 0, 1.55)), (.28, .25, .27), skin, col)
    uv_sphere(name + "_muzzle", p((0, .225, 1.49)), (.17, .10, .105), M["white"] if name.startswith("TIEDAN") else skin, col)
    cone(name + "_ear_L", p((-.16, 0, 1.83)), .13, .29, skin, col, rot=(0, 0, yaw))
    cone(name + "_ear_R", p((.16, 0, 1.83)), .13, .29, skin, col, rot=(0, 0, yaw))
    # Legs.
    for sx in (-.14, .14):
        hip = p((sx, 0, .68))
        knee = p((sx, .015, .39))
        ankle = p((sx, .04, .08))
        cylinder_between(name + "_thigh", hip, knee, .095, skin, col)
        cylinder_between(name + "_shin", knee, ankle, .075, skin, col)
        cube(name + "_shoe", p((sx, .10, .055)), (.18, .31, .10), M["white"], col, rot=(0, 0, yaw), bevel=.025)
    # Tail.
    tail_a, tail_b, tail_c = p((-.20, -.10, .74)), p((-.43, -.15, .56)), p((-.55, -.03, .83))
    cylinder_between(name + "_tail1", tail_a, tail_b, .065, skin, col)
    cylinder_between(name + "_tail2", tail_b, tail_c, .052, skin, col)
    # Pose-driven arms. Local +X is anatomical right.
    if pose == "smash":
        L_el, L_wr = (-.34, .18, 1.33), (-.52, .38, 1.55)
        R_el, R_wr = (.40, -.04, 1.57), (.48, .12, 1.83)
        racket_dir = (.08, .17, .98)
    elif pose == "yes":
        L_el, L_wr = (-.38, .12, 1.20), (-.45, .22, 1.42)
        R_el, R_wr = (.36, .08, 1.28), (.49, .18, 1.48)
        racket_dir = (.15, .12, .98)
    elif pose == "wave":
        L_el, L_wr = (-.38, .15, 1.35), (-.46, .20, 1.65)
        R_el, R_wr = (.38, .00, 1.18), (.50, .12, 1.34)
        racket_dir = (.25, .15, .95)
    elif pose == "phone":
        L_el, L_wr = (-.30, .20, 1.07), (-.19, .35, 1.17)
        R_el, R_wr = (.30, .20, 1.10), (.08, .38, 1.24)
        racket_dir = (.20, .10, .97)
    elif pose == "pack":
        L_el, L_wr = (-.35, .14, 1.04), (-.34, .35, .82)
        R_el, R_wr = (.35, .12, 1.03), (.30, .38, .82)
        racket_dir = (.18, .10, .98)
    else:
        L_el, L_wr = (-.35, .16, 1.21), (-.40, .34, 1.12)
        R_el, R_wr = (.35, .16, 1.21), (.40, .34, 1.12)
        racket_dir = (.08, .22, .97)
    for side, elbow, wrist in (("L", L_el, L_wr), ("R", R_el, R_wr)):
        shoulder = p((-.24 if side == "L" else .24, 0, 1.27))
        elbow_w, wrist_w = p(elbow), p(wrist)
        cylinder_between(name + "_upperarm_" + side, shoulder, elbow_w, .075, skin, col)
        cylinder_between(name + "_forearm_" + side, elbow_w, wrist_w, .063, skin, col)
        uv_sphere(name + "_hand_" + side, wrist_w, (.075, .065, .075), skin, col)
        if side == "R" and name.startswith("TIEDAN"):
            add_watch(wrist_w, col)
    right_wrist = p(R_wr)
    left_wrist = p(L_wr)
    if racket:
        world_dir = Vector(p(racket_dir)) - Vector(p((0, 0, 0)))
        add_racket(name + "_RACKET_675MM", right_wrist, world_dir, M["red"] if name.startswith("ORANGE") else M["blue"], col)
    if pose == "phone":
        cube(name + "_IPHONE16PRO", Vector(left_wrist) + Vector((0, 0, .03)), (.09, .018, .18), M["phone"], col, rot=(math.radians(72), 0, yaw), bevel=.012)
    return {"right_wrist": right_wrist, "left_wrist": left_wrist}


def shuttle(name, loc, col, rot=(0, 0, 0)):
    cone(name + "_skirt", loc, .07, .13, M["shuttle"], col, rot=rot)
    uv_sphere(name + "_cork", (loc[0], loc[1], loc[2] - .075), (.045, .045, .045), M["white"], col)


def bench(name, loc, col):
    x, y, z = loc
    cube(name + "_seat", (x, y, z + .45), (2.5, .55, .12), M["wood"], col, bevel=.05)
    for dx in (-1.0, 1.0):
        cube(name + "_leg", (x + dx, y, z + .22), (.12, .42, .45), M["black"], col)


def props_on_bench(loc, col):
    x, y, z = loc
    cube("NAVY_RACKET_BAG", (x + .65, y, z + .62), (1.1, .28, .32), M["navy"], col, rot=(0, .12, 0), bevel=.08)
    cube("COBALT_BLUE_TOWEL", (x - .72, y, z + .58), (.55, .34, .08), M["towel"], col, bevel=.03)
    cube("WHITE_TOP_FOLDED", (x, y, z + .57), (.44, .30, .07), M["white"], col, bevel=.03)


def indoor_lighting(col, ox, oy):
    for x in (-3.5, 0, 3.5):
        point_light("warm_hall_light", (ox + x, oy, 5.4), 780, (1.0, .56, .30), col, 1.2)
    point_light("cyan_fill", (ox - 5.5, oy - 3, 3.2), 520, (.12, .45, 1.0), col, 1.5)


def exterior_set(col, ox, oy):
    cube("red_track", (ox, oy, 0), (19, 12, .10), M["track"], col)
    cube("green_field", (ox, oy + 10, .03), (24, 10, .10), M["grass"], col)
    for i in range(6):
        y = oy + 5.5 + i * 1.5
        cube("track_line", (ox, y, .065), (19, .04, .02), M["line"], col)
    # Warm doorway on the hall facade.
    cube("hall_front", (ox, oy - 5.8, 3.0), (13, .35, 6.0), M["wall"], col)
    cube("warm_door", (ox, oy - 5.58, 1.4), (2.2, .18, 2.8), mat("door_glow", (1.0, .32, .04), emission=(1.0, .22, .03)), col)
    for i, dx in enumerate((-8, -5, 5, 8)):
        cube("tree_trunk", (ox + dx, oy + 14, .9), (.35, .35, 1.8), M["wood"], col)
        uv_sphere("tree_crown", (ox + dx, oy + 14, 2.5 + (i % 2) * .3), (1.1, 1.1, 1.7), M["tree"], col)
    # High-rise silhouette and window lights.
    cube("highrise", (ox + 8, oy + 20, 7.5), (6.0, 3.0, 15.0), M["wall"], col)
    for z in range(2, 14, 2):
        for x in (6.5, 8.0, 9.5):
            cube("window", (ox + x, oy + 18.48, z), (.62, .04, .35), M["moon"], col)
    for dx in (-7, 7):
        cylinder_between("flood_pole", (ox + dx, oy + 8, 0), (ox + dx, oy + 8, 6.5), .08, M["black"], col)
        point_light("cold_flood", (ox + dx, oy + 8, 6.5), 1100, (.50, .68, 1.0), col, .55)
    add_area_light("moon_fill", (ox - 7, oy + 3, 10), 650, (.30, .46, 1.0), col, 10)
    point_light("door_warmth", (ox, oy - 4.8, 2.0), 850, (1.0, .20, .04), col, 1.4)


def make_stage_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def build_shot_001():
    col = make_stage_collection("SHOT-001_对打与滚网")
    ox, oy = 0, 0
    add_court(col, ox, oy)
    indoor_lighting(col, ox, oy)
    add_cat("TIEDAN", (ox, oy - 4.55, 0), 0, M["skin_td"], M["white"], M["blue"], col, "ready")
    add_cat("ORANGE", (ox + 1.05, oy + 4.4, .10), math.pi, M["skin_oc"], M["yellow"], M["black"], col, "smash")
    # Exactly one shuttle, far court front service-line area, visually behind the black net.
    shuttle("ONLY_SHUTTLE_FAR_FRONT", (ox - .55, oy + 1.98, .16), col)
    text_obj("SHOT-001  BASELINE / NET DEPTH", (ox, oy + 8.8, 5.7), col)
    cam = camera("CAM_SHOT_001", (ox - 1.75, oy - 8.2, 1.90), (ox + .15, oy + .70, 1.15), 36, col)
    return col, cam


def build_shot_002():
    col = make_stage_collection("SHOT-002_YES与离场")
    ox, oy = 30, 0
    add_court(col, ox, oy)
    indoor_lighting(col, ox, oy)
    bench("REST_BENCH", (ox - 5.0, oy - 4.8, 0), col)
    add_cat("TIEDAN", (ox - 1.2, oy - 4.4, 0), -.32, M["skin_td"], M["white"], M["blue"], col, "yes")
    add_cat("ORANGE", (ox + .5, oy + 4.2, 0), math.pi, M["skin_oc"], M["yellow"], M["black"], col, "wave")
    text_obj("SHOT-002  YES / WAVE / BENCH", (ox, oy + 8.8, 5.7), col)
    cam = camera("CAM_SHOT_002", (ox - 7.2, oy - 8.0, 3.15), (ox - .25, oy + .10, 1.15), 34, col)
    return col, cam


def build_shot_003():
    col = make_stage_collection("SHOT-003_手机语音")
    ox, oy = 60, 0
    cube("rest_area_floor", (ox, oy, 0), (14, 12, .1), M["floor"], col)
    cube("rest_wall", (ox, oy + 5.5, 3), (14, .3, 6), M["wall"], col)
    bench("SAME_BENCH", (ox, oy, 0), col)
    props_on_bench((ox, oy, 0), col)
    add_cat("TIEDAN", (ox, oy - .05, .45), 0, M["skin_td"], M["white"], M["blue"], col, "phone", racket=False)
    indoor_lighting(col, ox, oy)
    text_obj("SHOT-003  PHONE / SAME BENCH", (ox, oy + 5.1, 5.2), col)
    cam = camera("CAM_SHOT_003", (ox + 2.35, oy - 3.15, 2.15), (ox, oy + .12, 1.35), 46, col)
    return col, cam


def build_shot_004():
    col = make_stage_collection("SHOT-004_收包出门")
    ox, oy = 0, 32
    cube("hall_floor", (ox, oy, 0), (15, 15, .12), M["floor"], col)
    cube("facade_L", (ox - 4.0, oy + 4.8, 3), (6.0, .3, 6), M["wall"], col)
    cube("facade_R", (ox + 4.0, oy + 4.8, 3), (6.0, .3, 6), M["wall"], col)
    # Door leaf rotated inward toward Tiedan; outside is beyond +Y.
    cube("DOOR_INWARD_OPEN", (ox + .8, oy + 4.15, 1.45), (1.7, .15, 2.9), M["wood"], col, rot=(0, 0, math.radians(-38)), bevel=.03)
    bench("PACKING_BENCH", (ox - 3.6, oy - .5, 0), col)
    props_on_bench((ox - 3.6, oy - .5, 0), col)
    add_cat("TIEDAN", (ox, oy + 2.5, 0), 0, M["skin_td"], M["white"], M["blue"], col, "pack", racket=False)
    indoor_lighting(col, ox, oy)
    point_light("outside_cool", (ox, oy + 7.2, 2.7), 800, (.24, .45, 1.0), col, 2)
    text_obj("SHOT-004  PACK / EXIT OUTWARD", (ox, oy + 7.7, 5.4), col)
    cam = camera("CAM_SHOT_004", (ox + 5.0, oy - 3.8, 2.45), (ox, oy + 2.4, 1.25), 44, col)
    return col, cam


def build_shot_005():
    col = make_stage_collection("SHOT-005_夜风毛发")
    ox, oy = 30, 32
    exterior_set(col, ox, oy)
    add_cat("TIEDAN", (ox, oy - 3.8, 0), 0, M["skin_td"], M["white"], M["blue"], col, "ready", racket=False)
    # Three subtle fur guide curves, a readable animation note rather than body vibration.
    for dx in (-.13, 0, .13):
        cylinder_between("FUR_WIND_GUIDE", (ox + dx, oy - 3.57, 1.56), (ox + dx + .10, oy - 3.48, 1.59), .008, M["moon"], col, vertices=8)
    text_obj("SHOT-005  HIGH 45 DEG / FUR INSERT", (ox, oy + 1.8, 6.4), col)
    cam = camera("CAM_SHOT_005", (ox + 6.4, oy + 1.4, 7.2), (ox, oy - 3.7, 1.25), 50, col)
    return col, cam


def build_shot_006():
    col = make_stage_collection("SHOT-006_夏夜远景")
    ox, oy = 60, 32
    exterior_set(col, ox, oy)
    add_cat("TIEDAN", (ox, oy - 3.8, 0), 0, M["skin_td"], M["white"], M["blue"], col, "ready", racket=False)
    text_obj("SHOT-006  HARD CUT WIDE / SMALL SUBJECT", (ox, oy + 1.8, 8.5), col)
    cam = camera("CAM_SHOT_006", (ox + 16.0, oy + .5, 12.5), (ox, oy + 2.0, 2.1), 32, col)
    return col, cam


def configure_render(scene):
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.003, 0.006, 0.018)


def main():
    reset_scene()
    init_materials()
    scene = bpy.context.scene
    configure_render(scene)
    stages = [build_shot_001(), build_shot_002(), build_shot_003(),
              build_shot_004(), build_shot_005(), build_shot_006()]
    # Save complete editable director board with all six dioramas visible.
    scene.camera = stages[0][1]
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    # Render isolated camera cards.
    for index, (col, cam) in enumerate(stages, 1):
        for other, _ in stages:
            other.hide_render = other != col
        scene.camera = cam
        scene.render.filepath = os.path.join(PREVIEW_DIR, f"EP02-SHOT-{index:03d}_camera-preview_v001.png")
        bpy.ops.render.render(write_still=True)
    for col, _ in stages:
        col.hide_render = False
    scene.camera = stages[0][1]
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("EP02_PREVIS_DONE", BLEND_PATH)


if __name__ == "__main__":
    main()
