import bpy
from . import tree_builder

class ShaderNodeMovieFrameSync(bpy.types.ShaderNodeCustomGroup):
    bl_idname = "ShaderNodeMovieFrameSync"
    bl_label = "Movie Frame Sync"
    bl_width_default = 240
    bl_width_min = 200

    def init(self, context):
        self.node_tree = tree_builder.build()

    def copy(self, node):
        self.node_tree = node.node_tree.copy()
        tree_builder.retarget_drivers(self.node_tree)

    def free(self):
        bpy.data.node_groups.remove(self.node_tree)

    def draw_buttons(self, context, layout):
        tex = self.node_tree.nodes["Tex"]
        layout.template_image(tex, "image", tex.image_user)
        img = tex.image
        if img and img.source == 'MOVIE':
            op = layout.operator("realtime_movie.detect_fps", icon='FILE_MOVIE')
            op.node_name = self.name        # tells the operator which node
        layout.prop(self.node_tree, '["movie_fps"]', text="Source FPS")
        layout.prop(self.node_tree, '["speed"]', text="Speed")
        layout.prop(self.node_tree, '["start"]', text="Start Frame")


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
        node.node_tree.update_tag()
        self.report({'INFO'}, f"Source FPS set to {fps:.3f}")
        return {'FINISHED'}