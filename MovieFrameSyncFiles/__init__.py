bl_info = {
    "name": "Movie Frame Sync",
    "author": "Emergency Player",
    "version": (1, 0, 0),
    "blender": (5, 2, 0),
    "location": "Shader Editor > Add > Texture",
    "description": "Image/movie texture that plays at real-time speed regardless of scene fps",
    "category": "Node",
}

import bpy
from . import node

classes = (
    node.ShaderNodeMovieFrameSync,
    node.MOVIEFRAMESYNC_OT_detect_fps,
)

def add_menu_entry(self, context):
    if context.space_data.tree_type != 'ShaderNodeTree':
        return
    layout = self.layout
    layout.separator()
    op = layout.operator("node.add_node", text="Movie Frame Sync")
    op.type = "ShaderNodeMovieFrameSync"
    op.use_transform = True

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_category_shader_texture.append(add_menu_entry)

def unregister():
    bpy.types.NODE_MT_category_shader_texture.remove(add_menu_entry)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)