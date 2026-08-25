import bpy
import importlib.util
import math
import os
from mathutils import Vector


ROOT = os.path.dirname(os.path.abspath(__file__))
PREVIEW_DIR = os.path.join(ROOT, "预览")
BLEND_PATH = os.path.join(ROOT, "EP03_六机位空间图_v001.blend")
EP02_HELPER = os.path.abspath(os.path.join(ROOT, "..", "..", "EP02", "3D预演", "build_ep02_previs.py"))
os.makedirs(PREVIEW_DIR, exist_ok=True)


spec = importlib.util.spec_from_file_location("ep02_previs_helpers", EP02_HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


CAMERA_SPECS = [
    {
        "id": "SHOT-001", "lens": 35,
        "loc": (-1.0, -8.5, 1.60), "target": (0.15, 0.65, 1.12),
        "color": (0.12, 0.75, 1.0), "note": "BASELINE / 35mm",
    },
    {
        "id": "SHOT-002", "lens": 20,
        "loc": (-5.0, -2.0, 0.18), "target": (0.0, 0.6, 1.02),
        "color": (1.0, 0.25, 0.10), "note": "COURT-FLOOR / 20mm",
    },
    {
        "id": "SHOT-003", "lens": 85,
        "loc": (4.60, -1.20, 1.35), "target": (0.25, 2.15, 1.12),
        "color": (0.95, 0.18, 0.65), "note": "NET-EDGE / 85mm",
    },
    {
        "id": "SHOT-004", "lens": 28,
        "loc": (-5.5, -6.5, 7.0), "target": (0.0, 0.0, 0.75),
        "color": (0.75, 0.35, 1.0), "note": "HIGH CORNER / 28mm",
    },
    {
        "id": "SHOT-005", "lens": 50,
        "loc": (1.5, -4.8, 1.35), "target": (0.42, -3.55, 1.20),
        "color": (1.0, 0.76, 0.05), "note": "RIGHT-WRIST / 50mm",
    },
    {
        "id": "SHOT-006", "lens": 18,
        "loc": (4.50, -1.00, 0.45), "target": (0.0, 1.00, 1.02),
        "color": (0.20, 1.0, 0.45), "note": "NET-POST / 18mm",
    },
]


def label_material(name, color):
    return h.mat(name, color, roughness=0.35, emission=color)


def add_map_text(body, loc, material, col, size=0.32):
    bpy.ops.object.text_add(location=loc)
    obj = bpy.context.object
    obj.name = "MAP_LABEL_" + body.replace(" ", "_")
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.012
    obj.data.materials.append(material)
    h.move_to_collection(obj, col)
    return obj


def add_camera_marker(item, material, col):
    loc = Vector(item["loc"])
    target = Vector(item["target"])
    ground_loc = Vector((loc.x, loc.y, 0.12))
    ground_target = Vector((target.x, target.y, 0.12))
    h.uv_sphere("MAP_" + item["id"] + "_POSITION", ground_loc, (.22, .22, .12), material, col)
    h.cylinder_between("MAP_" + item["id"] + "_VIEWLINE", ground_loc, ground_target, .025, material, col, vertices=10)
    direction = (ground_target - ground_loc).normalized()
    side = Vector((-direction.y, direction.x, 0))
    tip = ground_loc + direction * .62
    left = ground_loc + direction * .30 + side * .20
    right = ground_loc + direction * .30 - side * .20
    h.cylinder_between("MAP_ARROW_L", left, tip, .035, material, col, vertices=8)
    h.cylinder_between("MAP_ARROW_R", right, tip, .035, material, col, vertices=8)
    label_pos = ground_loc - direction * .55
    add_map_text(item["id"] + "  " + str(item["lens"]) + "mm", (label_pos.x, label_pos.y, .16), material, col, .28)


def add_zone_marker(name, loc, color, col):
    material = label_material("ZONE_" + name, color)
    h.uv_sphere(name, loc, (.20, .20, .06), material, col)
    add_map_text(name, (loc[0], loc[1] + .38, .15), material, col, .24)


def add_legend(col):
    bg = h.cube("LEGEND_BG", (7.2, -4.5, .10), (5.0, 4.5, .08), h.M["floor"], col, bevel=.12)
    entries = [
        "EP03 / 30s / SIX HARD CUT CAMERAS",
        "35mm  baseline depth",
        "20mm  court-floor pressure",
        "85mm  net compression",
        "28mm  tactical high angle",
        "50mm  right-wrist detail",
        "18mm  net-post danger",
        "BGM: NONE / SFX ONLY",
    ]
    for i, entry in enumerate(entries):
        material = h.M["line"] if i in (0, 7) else h.M["moon"]
        add_map_text(entry, (7.2, -2.9 - i * .43, .16), material, col, .23 if i else .27)


def add_map_camera(name, loc, target, ortho_scale=None, lens=42):
    data = bpy.data.cameras.new(name)
    if ortho_scale:
        data.type = "ORTHO"
        data.ortho_scale = ortho_scale
    else:
        data.lens = lens
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    h.look_at(obj, target)
    return obj


def configure_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.002, 0.004, 0.012)
    scene.frame_start = 1
    scene.frame_end = 720
    scene.render.fps = 24
    return scene


def build():
    h.reset_scene()
    h.init_materials()
    scene = configure_scene()

    stage_col = bpy.data.collections.new("EP03_MASTER_COURT")
    guide_col = bpy.data.collections.new("EP03_CAMERA_MAP_GUIDES")
    bpy.context.scene.collection.children.link(stage_col)
    bpy.context.scene.collection.children.link(guide_col)

    h.add_court(stage_col, 0, 0, indoor=True)
    h.indoor_lighting(stage_col, 0, 0)
    tiedan = h.add_cat("TIEDAN_CHAR-001_v003", (0.0, -3.7, 0), 0,
                       h.M["skin_td"], h.M["white"], h.M["blue"], stage_col, "ready")
    h.add_cat("ORANGE_CHAR-002_v001", (0.45, 3.75, 0), math.pi,
              h.M["skin_oc"], h.M["yellow"], h.M["black"], stage_col, "ready")

    # One shuttle only, suspended at a neutral mid-rally point for spatial reference.
    h.shuttle("ONLY_SHUTTLE_EP03", (-0.35, 0.85, 2.25), stage_col)

    cameras = []
    for item in CAMERA_SPECS:
        cam = h.camera("CAM_EP03_" + item["id"], item["loc"], item["target"], item["lens"], stage_col)
        cam.data.display_size = .45
        cameras.append(cam)
        add_camera_marker(item, label_material("CAM_COLOR_" + item["id"], item["color"]), guide_col)

    add_zone_marker("TIEDAN_NEAR", (0.0, -3.7, .12), (0.12, .75, 1.0), guide_col)
    add_zone_marker("ORANGE_FAR", (.45, 3.75, .12), (1.0, .55, .04), guide_col)
    add_zone_marker("NET_PLANE", (0.0, 0.0, .12), (.95, .95, .95), guide_col)
    add_legend(guide_col)

    top_cam = add_map_camera("CAM_EP03_MAP_TOP", (0, 0, 24), (0, 0, 0), ortho_scale=22)
    perspective_cam = add_map_camera("CAM_EP03_MAP_PERSPECTIVE", (13, -15, 14), (0, 0, .8), lens=45)

    # Timeline markers document the six 5-second units without animating camera movement.
    for index, cam in enumerate(cameras):
        frame = 1 + index * 120
        scene.timeline_markers.new(CAMERA_SPECS[index]["id"] + " / " + cam.name, frame=frame)

    scene.camera = top_cam
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

    guide_col.hide_render = False
    scene.camera = top_cam
    scene.render.filepath = os.path.join(PREVIEW_DIR, "EP03_camera-map_TOP_v001.png")
    bpy.ops.render.render(write_still=True)
    scene.camera = perspective_cam
    scene.render.filepath = os.path.join(PREVIEW_DIR, "EP03_camera-map_PERSPECTIVE_v001.png")
    bpy.ops.render.render(write_still=True)

    guide_col.hide_render = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    for index, cam in enumerate(cameras, 1):
        scene.camera = cam
        scene.render.filepath = os.path.join(PREVIEW_DIR, f"EP03-SHOT-{index:03d}_camera-preview_v001.png")
        bpy.ops.render.render(write_still=True)

    guide_col.hide_render = False
    scene.camera = top_cam
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("EP03_CAMERA_MAP_DONE", BLEND_PATH)


if __name__ == "__main__":
    build()
