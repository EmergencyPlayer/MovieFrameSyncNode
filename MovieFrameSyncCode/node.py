import os, re
import bpy
from bpy_extras.io_utils import ImportHelper
from . import tree_builder


def count_sequence(filepath):
    """Count files sharing the same prefix/extension, numbered >= the chosen file."""
    folder, name = os.path.split(filepath)
    stem, ext = os.path.splitext(name)
    m = re.search(r"(\d+)$", stem)
    if not m:
        return 1
    prefix, first = stem[:m.start()], int(m.group(1))
    pat = re.compile(re.escape(prefix) + r"(\d+)" + re.escape(ext) + "$")
    count = 0
    for f in os.listdir(folder):
        mm = pat.match(f)
        if mm and int(mm.group(1)) >= first:
            count += 1
    return max(count, 1)

def _update_projection(self, context):
    tree = self.node_tree
    if tree is None:
        return
    tex = tree.nodes["Tex"]
    coord = tree.nodes["Coord"]
    tex.projection = self.projection
    for link in list(tex.inputs["Vector"].links):
        tree.links.remove(link)
    out = "UV" if self.projection == 'FLAT' else "Object"
    tree.links.new(coord.outputs[out], tex.inputs["Vector"])


class ShaderNodeMovieFrameSync(bpy.types.ShaderNodeCustomGroup):
    bl_idname = "ShaderNodeMovieFrameSync"
    bl_label = "Movie Frame Sync"
    bl_width_default = 240
    bl_width_min = 200

    projection: bpy.props.EnumProperty(
        name="Projection",
        items=[
            ('FLAT',   "Flat",   "Use UV coordinates"),
            ('BOX',    "Box",    "Project from the object's axes"),
            ('SPHERE', "Sphere", "Wrap around the object"),
            ('TUBE',   "Tube",   "Wrap around a cylinder"),
        ],
        default='FLAT',
        update=_update_projection,
    )

    def init(self, context):
        self.node_tree = tree_builder.build()

    def copy(self, node):
        self.node_tree = node.node_tree.copy()
        tree_builder.retarget_drivers(self.node_tree)

    def free(self):
        bpy.data.node_groups.remove(self.node_tree)

    def draw_buttons(self, context, layout):
        if self.node_tree is None or "Tex" not in self.node_tree.nodes:
            layout.label(text="Tree missing, re-add node", icon='ERROR')
            return
        tex = self.node_tree.nodes["Tex"]
        img = tex.image

        layout.template_image(tex, "image", tex.image_user)

        layout.separator()
        if img and img.source == 'MOVIE':
            op = layout.operator("realtime_movie.detect_fps", icon='FILE_MOVIE')
            op.node_name = self.name
        else:
            op = layout.operator("movieframesync.load_sequence", icon='FILE_IMAGE')
            op.tree_name = self.node_tree.name
        label = "Sequence FPS" if (img and img.source == 'SEQUENCE') else "Source FPS"
        layout.prop(self.node_tree, '["movie_fps"]', text=label)
        layout.prop(self.node_tree, '["length"]', text="Length (frames)")
        layout.prop(self.node_tree, '["speed"]', text="Speed")
        layout.prop(self.node_tree, '["start"]', text="Start Frame")

        layout.separator()
        layout.prop(tex, "interpolation", text="")
        layout.prop(self, "projection", text="")
        if tex.projection == 'BOX':
            layout.prop(tex, "projection_blend", text="Blend")
        layout.prop(tex, "extension", text="")


class MOVIEFRAMESYNC_OT_detect_fps(bpy.types.Operator):
    bl_idname = "realtime_movie.detect_fps"
    bl_label = "Detect FPS"
    bl_description = "Read the frame rate from the movie file"
    bl_options = {'REGISTER', 'UNDO'}

    node_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        sd = context.space_data
        return sd and sd.type == 'NODE_EDITOR' and sd.edit_tree is not None

    def execute(self, context):
        from . import fps_probe

        node = context.space_data.edit_tree.nodes.get(self.node_name)
        if node is None or node.bl_idname != "ShaderNodeMovieFrameSync":
            self.report({'ERROR'}, "Node not found")
            return {'CANCELLED'}

        img = node.node_tree.nodes["Tex"].image
        if img is None or img.source != 'MOVIE':
            self.report({'WARNING'}, "Node needs a movie file")
            return {'CANCELLED'}

        fps = fps_probe.probe_movie_fps(img)
        if not fps:
            self.report({'WARNING'},
                        "Couldn't detect FPS. Enter it manually.")
            return {'CANCELLED'}

        node.node_tree["movie_fps"] = fps
        node.node_tree["length"] = max(img.frame_duration, 1)
        node.node_tree.update_tag()
        self.report({'INFO'}, f"Source FPS set to {fps:.3f}")
        return {'FINISHED'}


class MOVIEFRAMESYNC_OT_load_sequence(bpy.types.Operator, ImportHelper):
    bl_idname = "movieframesync.load_sequence"
    bl_label = "Load Image Sequence"
    bl_description = "Select the sequence frames; the frame count is set automatically"
    bl_options = {'REGISTER', 'UNDO'}

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    filter_image: bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    tree_name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        tree = bpy.data.node_groups.get(self.tree_name)
        if tree is None or "Tex" not in tree.nodes:
            self.report({'ERROR'}, "Node tree not found")
            return {'CANCELLED'}

        names = sorted(f.name for f in self.files)
        if not names:
            self.report({'WARNING'}, "No files selected")
            return {'CANCELLED'}

        first = os.path.join(self.directory, names[0])
        count = len(names) if len(names) > 1 else count_sequence(first)

        img = bpy.data.images.load(first, check_existing=True)
        img.source = 'SEQUENCE'

        tex = tree.nodes["Tex"]
        tex.image = img
        tree["length"] = count

        self.report({'INFO'}, f"Loaded {count} frames. Set Sequence FPS.")
        return {'FINISHED'}