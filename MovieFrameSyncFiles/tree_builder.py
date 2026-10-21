import bpy

def build():
    tree = bpy.data.node_groups.new("RTMovie", "ShaderNodeTree")

    iface = tree.interface
    iface.new_socket("Color", in_out='OUTPUT', socket_type='NodeSocketColor')
    iface.new_socket("Alpha", in_out='OUTPUT', socket_type='NodeSocketFloat')

    n_out = tree.nodes.new("NodeGroupOutput")
    coord = tree.nodes.new("ShaderNodeTexCoord")
    tex   = tree.nodes.new("ShaderNodeTexImage")
    tex.name = "Tex"
    tex.image_user.frame_start = 1
    tex.image_user.use_cyclic = True

    tree.links.new(coord.outputs["UV"], tex.inputs["Vector"])
    tree.links.new(tex.outputs["Color"], n_out.inputs["Color"])
    tree.links.new(tex.outputs["Alpha"], n_out.inputs["Alpha"])

    tree["movie_fps"] = 60.0
    tree["speed"] = 1.0
    tree["start"] = 1

    _add_driver(tree)
    return tree


def _add_driver(tree):
    fc = tree.driver_add('nodes["Tex"].image_user.frame_offset')
    d = fc.driver
    d.type = 'SCRIPTED'

    def var(name, id_type, id_, path):
        v = d.variables.new()
        v.name = name
        v.type = 'SINGLE_PROP'
        t = v.targets[0]
        t.id_type = id_type
        t.id = id_
        t.data_path = path

    scene = bpy.context.scene
    var("sfps",  'SCENE',    scene, "render.fps")
    var("base",  'SCENE',    scene, "render.fps_base")
    var("mfps",  'NODETREE', tree,  '["movie_fps"]')
    var("speed", 'NODETREE', tree,  '["speed"]')
    var("start", 'NODETREE', tree,  '["start"]')
    d.expression = "floor(max(frame - start, 0) * speed * mfps * base / sfps) + 1 - frame"


def retarget_drivers(tree):
    if not tree.animation_data:
        return
    for fc in tree.animation_data.drivers:
        for v in fc.driver.variables:
            for t in v.targets:
                if t.id_type == 'NODETREE':
                    t.id = tree