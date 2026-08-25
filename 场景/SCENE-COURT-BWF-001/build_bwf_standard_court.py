import bpy
import importlib.util
import os


ROOT = os.path.dirname(os.path.abspath(__file__))
PREVIEW = os.path.join(ROOT, "三视图")
BLEND_PATH = os.path.join(ROOT, "SCENE-COURT-BWF-001_v001.blend")
HELPER = os.path.abspath(os.path.join(ROOT, "..", "..", "制作", "EP02", "3D预演", "build_ep02_previs.py"))
os.makedirs(PREVIEW, exist_ok=True)

spec = importlib.util.spec_from_file_location("bwf_scene_helpers", HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def configure_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.002, 0.004, 0.012)
    return scene


def orthographic_camera(name, loc, target, scale):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    h.look_at(obj, target)
    return obj


def build():
    h.reset_scene()
    h.init_materials()
    scene = configure_scene()
    court_col = bpy.data.collections.new("SCENE-COURT-BWF-001_STANDARD_METRIC")
    bpy.context.scene.collection.children.link(court_col)
    h.add_court(court_col, 0, 0, indoor=False)

    # Metadata remains embedded in the .blend for downstream scripts.
    scene["court_standard"] = "BWF Laws of Badminton / Diagram A"
    scene["court_length_m"] = 13.40
    scene["court_doubles_width_m"] = 6.10
    scene["court_singles_width_m"] = 5.18
    scene["line_width_m"] = 0.04
    scene["short_service_from_net_m"] = 1.98
    scene["doubles_long_service_from_back_m"] = 0.76
    scene["net_post_height_m"] = 1.55
    scene["net_center_height_m"] = 1.524

    h.add_area_light("COURT_TOP_LIGHT", (0, 0, 12), 1800, (0.76, 0.88, 1.0), court_col, 10)
    # Landscape render needs extra orthographic margin on the long vertical axis.
    top = orthographic_camera("CAM_BWF_TOP", (0, 0, 22), (0, 0, 0), 18.5)
    front = orthographic_camera("CAM_BWF_FRONT", (0, -18, 2.6), (0, 0, .65), 7.4)
    side = orthographic_camera("CAM_BWF_SIDE", (12, 0, 3.2), (0, 0, .65), 15.2)

    for cam, filename in (
        (top, "SCENE-COURT-BWF-001_TOP_v001.png"),
        (front, "SCENE-COURT-BWF-001_FRONT_v001.png"),
        (side, "SCENE-COURT-BWF-001_SIDE_v001.png"),
    ):
        scene.camera = cam
        scene.render.filepath = os.path.join(PREVIEW, filename)
        bpy.ops.render.render(write_still=True)

    scene.camera = top
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("BWF_STANDARD_COURT_DONE", BLEND_PATH)


if __name__ == "__main__":
    build()
