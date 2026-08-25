import bpy
import importlib.util
import math
import os
from mathutils import Vector


ROOT = os.path.dirname(os.path.abspath(__file__))
KEYFRAME_DIR = os.path.join(ROOT, "动作关键帧_v002")
BLEND_PATH = os.path.join(ROOT, "EP03_骨骼IK动作预演_v002.blend")
EP02_HELPER = os.path.abspath(os.path.join(ROOT, "..", "..", "EP02", "3D预演", "build_ep02_previs.py"))
os.makedirs(KEYFRAME_DIR, exist_ok=True)


spec = importlib.util.spec_from_file_location("ep02_previs_helpers", EP02_HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


CAMERA_SPECS = [
    ("SHOT-001", 35, (-1.0, -8.5, 1.60), (0.15, 0.65, 1.12)),
    ("SHOT-002", 20, (-5.0, -2.0, 0.18), (0.0, 0.6, 1.02)),
    ("SHOT-003", 85, (4.60, -1.20, 1.35), (0.25, 2.15, 1.12)),
    ("SHOT-004", 28, (-5.5, -6.5, 7.0), (0.0, 0.0, 0.75)),
    ("SHOT-005", 50, (1.5, -4.8, 1.35), (0.42, -3.55, 1.20)),
    ("SHOT-006", 18, (4.50, -1.00, 0.45), (0.0, 1.00, 1.02)),
]


SHOT_FRAMES = {
    "SHOT-001": [(1, "READY"), (38, "CHASE"), (76, "CLEAR_CONTACT"), (112, "RECOVER")],
    "SHOT-002": [(121, "SMASH_LOAD"), (158, "LOW_JUMP"), (196, "SMASH_BLOCK"), (232, "NET_EXIT")],
    "SHOT-003": [(241, "BLOCK_NET"), (278, "ORANGE_APPROACH"), (316, "ORANGE_LUNGE_LIFT"), (352, "LIFT_EXIT")],
    "SHOT-004": [(361, "RETREAT"), (398, "OVERHEAD_LOAD"), (436, "TIEDAN_SMASH"), (472, "ORANGE_BLOCK")],
    "SHOT-005": [(481, "DRIVE_READY"), (518, "TIEDAN_DRIVE"), (556, "ORANGE_DRIVE"), (592, "TIEDAN_REDIRECT")],
    "SHOT-006": [(601, "ORANGE_DROP"), (638, "TIEDAN_LUNGE"), (676, "TIEDAN_SAVE"), (712, "UNRESOLVED_END")],
}


def create_bone(arm_data, name, head, tail, parent=None, connected=False, deform=True):
    b = arm_data.edit_bones.new(name)
    b.head = head
    b.tail = tail
    b.use_deform = deform
    if parent:
        b.parent = arm_data.edit_bones[parent]
        b.use_connect = connected
    return b


def create_rig(name, col):
    arm_data = bpy.data.armatures.new(name + "_ARMATURE_DATA")
    arm = bpy.data.objects.new(name + "_RIG", arm_data)
    col.objects.link(arm)
    arm.show_in_front = True
    arm.data.display_type = "BBONE"
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    # Control bones point along world +Y so their local X/Y/Z channels match
    # court right/forward/up. This prevents IK translation axes from swapping.
    create_bone(arm_data, "root", (0, 0, 0), (0, .30, 0), deform=False)
    create_bone(arm_data, "pelvis", (0, 0, .70), (0, 0, .90), "root")
    create_bone(arm_data, "spine", (0, 0, .90), (0, 0, 1.16), "pelvis", True)
    create_bone(arm_data, "chest", (0, 0, 1.16), (0, 0, 1.38), "spine", True)
    create_bone(arm_data, "neck", (0, 0, 1.38), (0, 0, 1.49), "chest", True)
    create_bone(arm_data, "head", (0, 0, 1.49), (0, 0, 1.78), "neck", True)

    for side, sx in (("L", -.24), ("R", .24)):
        sign = -1 if side == "L" else 1
        create_bone(arm_data, "upper_arm." + side, (sx, 0, 1.31), (sign * .49, .02, 1.08), "chest")
        create_bone(arm_data, "forearm." + side, (sign * .49, .02, 1.08), (sign * .72, .10, .82), "upper_arm." + side, True)
        create_bone(arm_data, "hand." + side, (sign * .72, .10, .82), (sign * .79, .15, .76), "forearm." + side, True)
        create_bone(arm_data, "thigh." + side, (sign * .15, 0, .70), (sign * .15, .02, .39), "pelvis")
        create_bone(arm_data, "shin." + side, (sign * .15, .02, .39), (sign * .15, .05, .10), "thigh." + side, True)
        create_bone(arm_data, "foot." + side, (sign * .15, .05, .10), (sign * .15, .28, .07), "shin." + side, True)

        create_bone(arm_data, "hand_ik." + side, (sign * .72, .10, .82), (sign * .72, .26, .82), "root", deform=False)
        create_bone(arm_data, "elbow_pole." + side, (sign * .62, -.48, 1.12), (sign * .62, -.32, 1.12), "root", deform=False)
        create_bone(arm_data, "foot_ik." + side, (sign * .15, .05, .10), (sign * .15, .22, .10), "root", deform=False)
        create_bone(arm_data, "knee_pole." + side, (sign * .15, -.48, .42), (sign * .15, -.32, .42), "root", deform=False)

    bpy.ops.object.mode_set(mode="POSE")
    for side in ("L", "R"):
        ik = arm.pose.bones["forearm." + side].constraints.new("IK")
        ik.name = "ARM_IK_" + side
        ik.target = arm
        ik.subtarget = "hand_ik." + side
        ik.pole_target = arm
        ik.pole_subtarget = "elbow_pole." + side
        ik.chain_count = 2
        ik.use_stretch = False

        leg_ik = arm.pose.bones["shin." + side].constraints.new("IK")
        leg_ik.name = "LEG_IK_" + side
        leg_ik.target = arm
        leg_ik.subtarget = "foot_ik." + side
        leg_ik.pole_target = arm
        leg_ik.pole_subtarget = "knee_pole." + side
        leg_ik.chain_count = 2
        leg_ik.use_stretch = False

    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.select_set(False)
    return arm


def bind_rigid_to_bone(obj, rig, bone_name):
    # Apply the primitive transform so all vertices share armature space, then
    # assign the complete rigid component to one deform bone.
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)
    group = obj.vertex_groups.new(name=bone_name)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new("ARMATURE_RIG", "ARMATURE")
    modifier.object = rig


def sphere_component(name, loc, scale, material, col, rig, bone):
    obj = h.uv_sphere(name, loc, scale, material, col)
    bind_rigid_to_bone(obj, rig, bone)
    return obj


def limb_component(name, a, b, radius, material, col, rig, bone):
    obj = h.cylinder_between(name, a, b, radius, material, col)
    bind_rigid_to_bone(obj, rig, bone)
    return obj


def create_watch_torus(name, loc, col, rig):
    forearm_direction = Vector((.72, .10, .82)) - Vector((.49, .02, 1.08))
    bpy.ops.mesh.primitive_torus_add(major_radius=.075, minor_radius=.018, major_segments=20,
                                    minor_segments=8, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(forearm_direction.normalized())
    obj.data.materials.append(h.M["black"])
    h.move_to_collection(obj, col)
    bind_rigid_to_bone(obj, rig, "hand.R")
    return obj


def build_rig_proxy(name, rig, skin, shirt, shorts, racket_color, col, tiedan=False):
    sphere_component(name + "_PELVIS", (0, 0, .77), (.27, .21, .20), shorts, col, rig, "pelvis")
    sphere_component(name + "_TORSO", (0, 0, 1.10), (.30, .23, .41), shirt, col, rig, "spine")
    sphere_component(name + "_CHEST", (0, 0, 1.28), (.31, .24, .23), shirt, col, rig, "chest")
    sphere_component(name + "_HEAD", (0, 0, 1.61), (.28, .25, .27), skin, col, rig, "head")
    sphere_component(name + "_MUZZLE", (0, .225, 1.54), (.17, .10, .105), h.M["white"] if tiedan else skin, col, rig, "head")
    ear_l = h.cone(name + "_EAR_L", (-.16, 0, 1.87), .13, .29, skin, col)
    ear_r = h.cone(name + "_EAR_R", (.16, 0, 1.87), .13, .29, skin, col)
    bind_rigid_to_bone(ear_l, rig, "head")
    bind_rigid_to_bone(ear_r, rig, "head")

    for side, sign in (("L", -1), ("R", 1)):
        limb_component(name + "_UPPER_ARM_" + side, (sign * .24, 0, 1.31), (sign * .49, .02, 1.08), .078, skin, col, rig, "upper_arm." + side)
        limb_component(name + "_FOREARM_" + side, (sign * .49, .02, 1.08), (sign * .72, .10, .82), .067, skin, col, rig, "forearm." + side)
        sphere_component(name + "_HAND_" + side, (sign * .75, .12, .79), (.08, .07, .08), skin, col, rig, "hand." + side)
        limb_component(name + "_THIGH_" + side, (sign * .15, 0, .70), (sign * .15, .02, .39), .10, skin, col, rig, "thigh." + side)
        limb_component(name + "_SHIN_" + side, (sign * .15, .02, .39), (sign * .15, .05, .10), .078, skin, col, rig, "shin." + side)
        shoe = h.cube(name + "_SHOE_" + side, (sign * .15, .17, .075), (.19, .32, .11), h.M["white"], col, bevel=.025)
        bind_rigid_to_bone(shoe, rig, "foot." + side)

    tail1 = limb_component(name + "_TAIL_1", (-.20, -.10, .76), (-.46, -.18, .58), .065, skin, col, rig, "pelvis")
    tail2 = limb_component(name + "_TAIL_2", (-.46, -.18, .58), (-.58, -.05, .86), .052, skin, col, rig, "pelvis")

    before = set(bpy.data.objects)
    h.add_racket(name + "_RACKET_675MM_RIGHT", (.75, .12, .79), (0, .05, 1), racket_color, col)
    racket_objects = list(set(bpy.data.objects) - before)
    for obj in racket_objects:
        if obj.type == "MESH":
            bind_rigid_to_bone(obj, rig, "hand.R")

    if tiedan:
        create_watch_torus("TIEDAN_RIGHT_WRIST_CLOSED_BLACK_WATCH", (.70, .095, .84), col, rig)


def base_pose(root=(0, 0, 0), yaw=0):
    return {
        "root": (root[0], root[1], root[2], 0, 0, yaw),
        "pelvis": (0, 0, 0, 0, 0, 0),
        "chest": (0, 0, 0, 0, 0, 0),
        "head": (0, 0, 0, 0, 0, 0),
        "hand_ik.R": (-.34, .34, .34, 0, 0, 0),
        "hand_ik.L": (.30, .23, .23, 0, 0, 0),
        "foot_ik.R": (.22, .03, 0, 0, 0, 0),
        "foot_ik.L": (-.22, -.03, 0, 0, 0, 0),
        "elbow_pole.R": (0, 0, 0, 0, 0, 0),
        "elbow_pole.L": (0, 0, 0, 0, 0, 0),
        "knee_pole.R": (0, 0, 0, 0, 0, 0),
        "knee_pole.L": (0, 0, 0, 0, 0, 0),
    }


def action_pose(action, root, yaw=0):
    p = base_pose(root, yaw)
    if action == "ready":
        p["pelvis"] = (0, 0, -.10, math.radians(8), 0, 0)
        p["hand_ik.R"] = (-.35, .40, .34, math.radians(-10), 0, 0)
        p["hand_ik.L"] = (.28, .28, .30, 0, 0, 0)
        p["foot_ik.R"] = (.26, .07, 0, 0, 0, 0)
        p["foot_ik.L"] = (-.26, -.07, 0, 0, 0, 0)
    elif action == "chase_right":
        p["root"] = (root[0], root[1], root[2], math.radians(4), math.radians(-8), yaw)
        p["pelvis"] = (0, 0, -.08, math.radians(10), 0, math.radians(-8))
        p["foot_ik.R"] = (.42, .18, 0, 0, 0, 0)
        p["foot_ik.L"] = (-.12, -.22, .03, 0, 0, 0)
        p["hand_ik.R"] = (-.28, .26, .48, 0, 0, 0)
    elif action == "overhead_load":
        p["pelvis"] = (0, 0, -.08, math.radians(6), 0, math.radians(-18))
        p["chest"] = (0, 0, 0, math.radians(-12), math.radians(8), math.radians(-28))
        p["hand_ik.R"] = (-.20, -.18, .88, math.radians(-35), 0, math.radians(-20))
        p["hand_ik.L"] = (.18, .48, .62, 0, 0, 0)
        p["foot_ik.R"] = (.25, -.10, 0, 0, 0, 0)
        p["foot_ik.L"] = (-.28, .16, 0, 0, 0, 0)
    elif action == "overhead_contact":
        p["root"] = (root[0], root[1], root[2], 0, math.radians(-4), yaw)
        p["pelvis"] = (0, 0, .02, math.radians(-5), 0, math.radians(18))
        p["chest"] = (0, 0, 0, math.radians(-8), math.radians(-6), math.radians(28))
        p["hand_ik.R"] = (-.28, .26, 1.04, math.radians(10), 0, math.radians(18))
        p["hand_ik.L"] = (.48, .10, .32, 0, 0, 0)
        p["foot_ik.R"] = (.18, -.02, .10, 0, 0, 0)
        p["foot_ik.L"] = (-.18, .03, .08, 0, 0, 0)
    elif action == "smash_follow":
        p["pelvis"] = (0, 0, -.12, math.radians(15), 0, math.radians(12))
        p["chest"] = (0, 0, 0, math.radians(18), 0, math.radians(35))
        p["hand_ik.R"] = (-.62, .42, .20, math.radians(25), 0, math.radians(35))
        p["hand_ik.L"] = (.25, .18, .18, 0, 0, 0)
    elif action == "block":
        p["pelvis"] = (0, 0, -.18, math.radians(12), 0, 0)
        p["chest"] = (0, 0, 0, math.radians(8), 0, 0)
        p["hand_ik.R"] = (-.45, .48, .36, math.radians(-15), 0, 0)
        p["hand_ik.L"] = (.24, .22, .18, 0, 0, 0)
        p["foot_ik.R"] = (.34, .12, 0, 0, 0, 0)
        p["foot_ik.L"] = (-.34, -.12, 0, 0, 0, 0)
    elif action == "net_lunge":
        p["root"] = (root[0], root[1], root[2], math.radians(12), 0, yaw)
        p["pelvis"] = (0, 0, -.22, math.radians(18), 0, 0)
        p["hand_ik.R"] = (-.42, .68, .22, math.radians(-25), 0, 0)
        p["hand_ik.L"] = (.20, .28, .10, 0, 0, 0)
        p["foot_ik.R"] = (.12, .70, 0, 0, 0, 0)
        p["foot_ik.L"] = (-.18, -.24, 0, 0, 0, 0)
    elif action == "lift":
        p["pelvis"] = (0, 0, -.18, math.radians(16), 0, 0)
        p["hand_ik.R"] = (-.42, .60, .10, math.radians(25), 0, math.radians(-5))
        p["hand_ik.L"] = (.18, .24, .16, 0, 0, 0)
        p["foot_ik.R"] = (.10, .62, 0, 0, 0, 0)
        p["foot_ik.L"] = (-.18, -.18, 0, 0, 0, 0)
    elif action == "drive_fh":
        p["pelvis"] = (0, 0, -.10, math.radians(7), 0, math.radians(-10))
        p["chest"] = (0, 0, 0, 0, 0, math.radians(-24))
        p["hand_ik.R"] = (-.30, .56, .40, 0, 0, math.radians(-20))
        p["hand_ik.L"] = (.22, .20, .20, 0, 0, 0)
    elif action == "drive_bh":
        p["pelvis"] = (0, 0, -.12, math.radians(8), 0, math.radians(12))
        p["chest"] = (0, 0, 0, 0, 0, math.radians(28))
        p["hand_ik.R"] = (-.68, .48, .34, 0, 0, math.radians(30))
        p["hand_ik.L"] = (.20, .18, .22, 0, 0, 0)
    elif action == "drop":
        p["pelvis"] = (0, 0, -.05, math.radians(5), 0, math.radians(-8))
        p["chest"] = (0, 0, 0, 0, 0, math.radians(-18))
        p["hand_ik.R"] = (-.24, .30, .82, math.radians(-20), 0, math.radians(-10))
        p["hand_ik.L"] = (.26, .32, .42, 0, 0, 0)
    elif action == "full_save":
        p["root"] = (root[0], root[1], root[2], math.radians(38), math.radians(-8), yaw)
        p["pelvis"] = (0, 0, -.34, math.radians(20), 0, 0)
        p["chest"] = (0, 0, 0, math.radians(18), 0, math.radians(-8))
        p["hand_ik.R"] = (-.48, .95, .12, math.radians(-30), 0, 0)
        p["hand_ik.L"] = (.20, .62, .05, 0, 0, 0)
        p["foot_ik.R"] = (.12, .86, 0, 0, 0, 0)
        p["foot_ik.L"] = (-.12, -.35, 0, 0, 0, 0)
    return p


def apply_pose(rig, frame, pose):
    for bone_name, values in pose.items():
        pb = rig.pose.bones[bone_name]
        pb.location = values[:3]
        pb.rotation_euler = values[3:6]
        pb.keyframe_insert("location", frame=frame, group=bone_name)
        pb.keyframe_insert("rotation_euler", frame=frame, group=bone_name)


def set_constant_interpolation(rig, action_name):
    if rig.animation_data and rig.animation_data.action:
        rig.animation_data.action.name = action_name
        for fc in rig.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def shuttle_key(shuttle, frame, loc):
    shuttle.location = loc
    shuttle.keyframe_insert("location", frame=frame)


def build_pose_schedule(tiedan, orange, shuttle):
    # 24 blocking poses: four per shot. Orange uses yaw pi, Tiedan yaw zero.
    schedule = [
        (1, "S1_READY", "ready", (0, -4.2, 0), "drive_fh", (0.3, 4.0, 0), (0.3, 2.8, 2.7)),
        (38, "S1_CHASE", "chase_right", (.55, -4.55, 0), "ready", (-.4, 4.1, 0), (.35, -2.8, 2.45)),
        (76, "S1_CLEAR_CONTACT", "overhead_contact", (.72, -4.7, 0), "ready", (-.65, 4.0, 0), (.70, -4.25, 2.45)),
        (112, "S1_RECOVER", "smash_follow", (.35, -4.35, 0), "overhead_load", (-1.0, 4.0, 0), (-1.0, 3.4, 3.8)),

        (121, "S2_SMASH_LOAD", "ready", (.2, -3.85, 0), "overhead_load", (-1.0, 4.0, 0), (-1.0, 3.6, 3.1)),
        (158, "S2_LOW_JUMP", "ready", (.15, -3.75, 0), "overhead_contact", (-1.0, 4.0, .10), (-1.0, 3.85, 2.55)),
        (196, "S2_BLOCK", "block", (.1, -3.55, 0), "smash_follow", (-.8, 3.9, 0), (.12, -3.10, 1.18)),
        (232, "S2_NET_EXIT", "block", (0, -3.15, 0), "ready", (-.6, 3.55, 0), (-.55, 1.15, 1.62)),

        (241, "S3_BLOCK_NET", "block", (0, -2.75, 0), "ready", (-.4, 3.2, 0), (-.5, .65, 1.65)),
        (278, "S3_APPROACH", "ready", (0, -2.8, 0), "chase_right", (-.25, 2.0, 0), (-.45, 1.25, 1.20)),
        (316, "S3_LUNGE_LIFT", "ready", (0, -3.0, 0), "lift", (-.15, 1.35, 0), (-.2, 1.20, .90)),
        (352, "S3_LIFT_EXIT", "chase_right", (.25, -3.5, 0), "net_lunge", (-.15, 1.5, 0), (.35, -2.8, 3.7)),

        (361, "S4_RETREAT", "chase_right", (.45, -4.0, 0), "ready", (-.1, 2.6, 0), (.42, -3.6, 3.35)),
        (398, "S4_LOAD", "overhead_load", (.75, -4.75, 0), "ready", (-.05, 3.05, 0), (.75, -4.2, 2.85)),
        (436, "S4_TIEDAN_SMASH", "overhead_contact", (.78, -4.75, .08), "block", (-.05, 3.25, 0), (.75, -4.35, 2.55)),
        (472, "S4_ORANGE_BLOCK", "smash_follow", (.55, -4.25, 0), "block", (-.05, 3.0, 0), (.1, 2.65, 1.15)),

        (481, "S5_DRIVE_READY", "ready", (.25, -2.9, 0), "ready", (-.1, 2.9, 0), (.05, 0.3, 1.35)),
        (518, "S5_TIEDAN_DRIVE", "drive_fh", (.25, -2.75, 0), "ready", (-.15, 2.75, 0), (.30, -2.35, 1.25)),
        (556, "S5_ORANGE_DRIVE", "ready", (.2, -2.75, 0), "drive_fh", (-.15, 2.7, 0), (-.1, 2.25, 1.25)),
        (592, "S5_REDIRECT", "drive_bh", (.2, -2.65, 0), "ready", (-.2, 2.6, 0), (.65, -.2, 1.30)),

        (601, "S6_ORANGE_DROP", "ready", (.25, -2.7, 0), "drop", (-.25, 2.35, 0), (-.25, 2.0, 1.75)),
        (638, "S6_TIEDAN_LUNGE", "net_lunge", (.45, -1.85, 0), "smash_follow", (-.25, 2.2, 0), (.35, -.25, 1.28)),
        (676, "S6_TIEDAN_SAVE", "full_save", (.55, -1.25, 0), "ready", (-.2, 2.25, 0), (2.8, -.45, .95)),
        (712, "S6_UNRESOLVED", "net_lunge", (.35, -1.45, 0), "overhead_load", (-.25, 2.4, 0), (-.2, 1.65, 2.65)),
    ]
    for frame, label, t_action, t_root, o_action, o_root, ball in schedule:
        apply_pose(tiedan, frame, action_pose(t_action, t_root, 0))
        apply_pose(orange, frame, action_pose(o_action, o_root, math.pi))
        shuttle_key(shuttle, frame, ball)
        bpy.context.scene.timeline_markers.new(label, frame=frame)
    set_constant_interpolation(tiedan, "ACT_EP03_TIEDAN_RALLY_BLOCKING_v001")
    set_constant_interpolation(orange, "ACT_EP03_ORANGE_RALLY_BLOCKING_v001")
    if shuttle.animation_data and shuttle.animation_data.action:
        shuttle.animation_data.action.name = "ACT_EP03_ONLY_SHUTTLE_PATH_v001"
        for fc in shuttle.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"


def create_shuttle(col):
    before = set(bpy.data.objects)
    h.shuttle("ONLY_SHUTTLE_EP03_ANIMATED", (0, 0, 2), col)
    new = list(set(bpy.data.objects) - before)
    empty = bpy.data.objects.new("ONLY_SHUTTLE_EP03_CONTROLLER", None)
    col.objects.link(empty)
    for obj in new:
        obj.parent = empty
    return empty


def configure_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 720
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.002, 0.004, 0.012)
    return scene


def build():
    h.reset_scene()
    h.init_materials()
    scene = configure_scene()
    stage = bpy.data.collections.new("EP03_RIGGED_STAGE")
    bpy.context.scene.collection.children.link(stage)
    h.add_court(stage, 0, 0, indoor=True)
    h.indoor_lighting(stage, 0, 0)

    tiedan = create_rig("TIEDAN_CHAR-001_v003", stage)
    orange = create_rig("ORANGE_CHAR-002_v001", stage)
    build_rig_proxy("TIEDAN", tiedan, h.M["skin_td"], h.M["white"], h.M["blue"], h.M["blue"], stage, tiedan=True)
    build_rig_proxy("ORANGE", orange, h.M["skin_oc"], h.M["yellow"], h.M["black"], h.M["red"], stage, tiedan=False)
    shuttle = create_shuttle(stage)

    cameras = []
    for shot_id, lens, loc, target in CAMERA_SPECS:
        cameras.append(h.camera("CAM_EP03_" + shot_id, loc, target, lens, stage))
    # Camera markers create actual single-frame hard cuts at each five-second boundary.
    for index, cam in enumerate(cameras):
        marker = scene.timeline_markers.new("CUT_" + CAMERA_SPECS[index][0], frame=1 + index * 120)
        marker.camera = cam

    build_pose_schedule(tiedan, orange, shuttle)
    scene.frame_set(1)
    scene.camera = cameras[0]
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

    # Render all 24 blocking candidates from their bound shot camera. v002 uses
    # the corrected 1:1-metre BWF court; v001 assets remain untouched.
    for shot_index, (shot_id, keyframes) in enumerate(SHOT_FRAMES.items(), 1):
        shot_dir = os.path.join(KEYFRAME_DIR, shot_id)
        os.makedirs(shot_dir, exist_ok=True)
        for key_index, (frame, pose_name) in enumerate(keyframes, 1):
            scene.frame_set(frame)
            scene.render.filepath = os.path.join(shot_dir, f"{shot_id}_KF{key_index:02d}_{pose_name}_v002.png")
            bpy.ops.render.render(write_still=True)

    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("EP03_RIGGED_PREVIS_DONE", BLEND_PATH)


if __name__ == "__main__":
    build()
